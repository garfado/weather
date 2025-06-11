# app/schema.py
from typing import List
from pydantic import BaseModel

class HourlyData(BaseModel):
    time: List[str]
    temperature_2m: List[float]

class WeatherResponse(BaseModel):
    hourly: HourlyData