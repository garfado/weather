from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import httpx
import sqlite3
from typing import List

from app.models import WeatherData
from app.database import DB_PATH

app = FastAPI()

# Função chamável para injeção de dependência
def get_http_client():
    return httpx.AsyncClient()

@app.on_event("startup")
def startup_event():
    WeatherData.create_table()

@app.post("/sync-weather")
async def sync_weather(client: httpx.AsyncClient = Depends(get_http_client)):
    try:
        data = await fetch_weather_data(client)
        save_weather_data(data["times"], data["temperatures"])
        return {"rows_upserted": len(data["times"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_weather_data(client: httpx.AsyncClient) -> dict:
    url = "https://api.open-meteo.com/v1/forecast" 
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "hourly": "temperature_2m"
    }
    response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Falha ao buscar dados climáticos")

    json_data = response.json()
    return {
        "times": json_data["hourly"]["time"],
        "temperatures": json_data["hourly"]["temperature_2m"]
    }

def save_weather_data(times: List[str], temps: List[float]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO weather_data (timestamp, temperature) VALUES (?, ?)",
        zip(times, temps)
    )
    conn.commit()
    conn.close()

@app.get("/week")
async def get_week_forecast(client: httpx.AsyncClient = Depends(get_http_client)):
    today = datetime.now().date()
    seven_days_later = today + timedelta(days=7)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, temperature FROM weather_data WHERE date(timestamp) >= date(?) AND date(timestamp) < date(?)",
        (today.isoformat(), seven_days_later.isoformat())
    )

    results = cursor.fetchall()
    conn.close()

    daily_temps = defaultdict(list)
    for row in results:
        dt = datetime.fromisoformat(row[0])
        if 6 <= dt.hour <= 18:
            daily_temps[dt.date()].append(row[1])

    avg_temps = {str(date): round(sum(temps)/len(temps), 2) for date, temps in daily_temps.items()}
    return avg_temps

@app.get("/weather")
async def get_weather(limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, temperature FROM weather_data ORDER BY timestamp DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    conn.close()
    return [{"timestamp": row[0], "temperature": row[1]} for row in results]