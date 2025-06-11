# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from datetime import datetime, timedelta
from collections import defaultdict
import httpx
import sqlite3
from typing import List
import logging

# Importações locais
from app.models import WeatherData
from app.config import DB_PATH
from app.schema import WeatherResponse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Weather Ingestor API", version="1.0.0")

# Função chamável para injeção de dependência
def get_http_client():
    return httpx.AsyncClient(timeout=10.0)

@app.on_event("startup")
def startup_event():
    logger.info("Iniciando aplicação...")
    try:
        WeatherData.create_table()
        logger.info("Tabela weather_data criada ou já existe.")
    except Exception as e:
        logger.error(f"Falha ao inicializar tabela: {e}", exc_info=True)
        raise

def get_city_name(latitude: float, longitude: float) -> str:
    # Mapeamento simples baseado em coordenadas conhecidas
    locations = {
        (52.52, 13.41): "Berlin",
        (-23.55, -46.63): "Sao Paulo",
        (-22.91, -43.17): "Rio de Janeiro",
        (40.71, -74.01): "New York",
        (51.51, -0.13): "London",
        (48.85, 2.35): "Paris"
    }

    return locations.get((round(latitude, 2), round(longitude, 2)), f"{latitude:.2f},{longitude:.2f}")

@app.post("/sync-weather")
async def sync_weather(
    latitude: float = Query(52.52, description="Latitude da localização"),
    longitude: float = Query(13.41, description="Longitude da localização"),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Busca dados horários de temperatura para uma localização específica e salva no SQLite.
    Retorna número de linhas inseridas.
    """
    logger.info(f"Iniciando sincronização de dados climáticos para ({latitude}, {longitude})...")

    try:
        data = await fetch_weather_data(client, latitude, longitude)
        city_name = get_city_name(latitude, longitude)
        save_weather_data(data["times"], data["temperatures"], city_name)
        logger.info(f"{len(data['times'])} linhas inseridas com sucesso para {city_name}.")
        return {"rows_upserted": len(data["times"]), "city": city_name}
    except HTTPException as he:
        logger.warning(f"Erro HTTP durante sincronização: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Erro interno durante sincronização: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_weather_data(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float
) -> dict:
    """
    Faz requisição à Open-Meteo API e retorna dados validados.
    """
    url = "https://api.open-meteo.com/v1/forecast" 
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m"
    }

    logger.info(f"Buscando dados da API: {url}?{httpx.QueryParams(params)}")

    try:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Falha ao buscar dados climáticos")
        json_data = response.json()
        validated = WeatherResponse(**json_data)
        return {
            "times": validated.hourly.time,
            "temperatures": validated.hourly.temperature_2m
        }
    except Exception as e:
        logger.error(f"Erro ao validar resposta da API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na resposta da API: {e}")

def save_weather_data(times: List[str], temps: List[float], city_name: str):
    """
    Salva dados de temperatura com nome da cidade.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO weather_data (timestamp, temperature, city_name) VALUES (?, ?, ?)",
            zip(times, temps, [city_name] * len(times))
        )
        conn.commit()

@app.get("/week")
async def get_week_forecast(
    latitude: float = Query(52.52, description="Latitude da localização"),
    longitude: float = Query(13.41, description="Longitude da localização")
):
    today = datetime.now().date()
    seven_days_later = today + timedelta(days=7)

    city_name = get_city_name(latitude, longitude)
    logger.info(f"Buscando dados entre {today} e {seven_days_later} para {city_name}.")

    daily_temps = defaultdict(list)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, temperature FROM weather_data
            WHERE date(timestamp) >= date(?)
              AND date(timestamp) < date(?)
              AND city_name = ?
            """,
            (today.isoformat(), seven_days_later.isoformat(), city_name)
        )
        results = cursor.fetchall()

    for row in results:
        dt = datetime.fromisoformat(row[0])
        if 6 <= dt.hour <= 18:
            daily_temps[dt.date()].append(row[1])

    avg_temps = {
        str(date): round(sum(temps) / len(temps), 2)
        for date, temps in daily_temps.items()
        if temps
    }

    return {city_name: avg_temps}

@app.get("/locations")
async def get_locations():
    """
    Retorna lista de cidades cujos dados já foram sincronizados.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT city_name FROM weather_data ORDER BY city_name")
        results = cursor.fetchall()

    return {"locations": [row[0] for row in results]}

@app.get("/weather")
async def get_weather(limit: int = 10):
    """
    Retorna as últimas N temperaturas armazenadas.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, temperature, city_name FROM weather_data ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        results = cursor.fetchall()

    return [{"timestamp": row[0], "temperature": row[1], "city": row[2]} for row in results]