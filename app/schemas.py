from pydantic import BaseModel

class WeatherCreate(BaseModel):
    timestamp: str
    temperature: float