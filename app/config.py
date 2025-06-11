# app/config.py
import os

DB_PATH = os.getenv("DB_PATH", "/app/data/weather.db")