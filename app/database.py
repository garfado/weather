import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "/app/data/weather.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()