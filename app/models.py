# app/models.py
import sqlite3
from app.config import DB_PATH

class WeatherData:
    @staticmethod
    def create_table():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    city_name TEXT NOT NULL DEFAULT 'unknown',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(timestamp, city_name)
                )
            ''')
            conn.commit()