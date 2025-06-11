import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", os.path.join(os.getcwd(), "/app/data/", "weather.db"))

class WeatherData:
    @staticmethod
    def create_table():
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

    @staticmethod
    def insert(timestamp: str, temperature: float):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO weather_data (timestamp, temperature) VALUES (?, ?)",
            (timestamp, temperature)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all(limit: int = 10):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, temperature FROM weather_data ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        results = cursor.fetchall()
        conn.close()
        return [{"timestamp": row[0], "temperature": row[1]} for row in results]

    @staticmethod
    def bulk_insert(times: list, temps: list):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO weather_data (timestamp, temperature) VALUES (?, ?)",
            zip(times, temps)
        )
        conn.commit()
        conn.close()