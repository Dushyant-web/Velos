from pydantic import BaseModel

class TelemetryCreate(BaseModel):
    vehicle_id: str
    speed: float
    engine_temp: float
    battery_level: float
    fuel: float
    rpm: float
    latitude: float
    longitude: float
    tire_pressure: float