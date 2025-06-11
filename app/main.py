from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import httpx
import sqlite3
import os
from typing import List, Dict
from collections import defaultdict

app = FastAPI()

# Configuração do banco
DB_PATH = os.getenv("DB_PATH", "weather.db")


@app.on_event("startup")
async def startup_event():
    init_db()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")


def parse_iso_time(time_str: str) -> datetime:
    return datetime.fromisoformat(time_str)


async def fetch_weather_data() -> Dict[str, List]:
    url = "https://api.open-meteo.com/v1/forecast" 
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "hourly": "temperature_2m"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Falha ao buscar dados climáticos")

    data = response.json()
    return {
        "times": data["hourly"]["time"],
        "temperatures": data["hourly"]["temperature_2m"]
    }


def save_weather_data(times: List[str], temps: List[float]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for timestamp, temp in zip(times, temps):
        cursor.execute(
            "INSERT INTO weather_data (timestamp, temperature) VALUES (?, ?)",
            (timestamp, temp)
        )

    conn.commit()
    conn.close()


@app.post("/sync-weather")
async def sync_weather():
    try:
        data = await fetch_weather_data()
        save_weather_data(data["times"], data["temperatures"])
        return {"rows_upserted": len(data["times"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/week")
async def get_week_forecast():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().date()
    seven_days_later = today + timedelta(days=7)

    cursor.execute(
        "SELECT timestamp, temperature FROM weather_data WHERE date(timestamp) >= date(?) AND date(timestamp) < date(?)",
        (today.isoformat(), seven_days_later.isoformat())
    )

    results = cursor.fetchall()
    conn.close()

    daily_temps = defaultdict(list)

    for row in results:
        timestamp = parse_iso_time(row[0])
        hour = timestamp.hour
        # Considera apenas horários diurnos (6h - 18h)
        if 6 <= hour <= 18:
            daily_temps[timestamp.date()].append(row[1])

    avg_temps = {
        str(date): round(sum(temps) / len(temps), 2)
        for date, temps in daily_temps.items()
    }

    return avg_temps


@app.get("/weather")
async def get_weather(limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT timestamp, temperature FROM weather_data ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )

    results = cursor.fetchall()
    conn.close()

    return [
        {"timestamp": row[0], "temperature": row[1]}
        for row in results
    ]