from pydantic import BaseModel


# =========================
# TELEMETRY SCHEMAS
# =========================
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


# =========================
# VEHICLE SCHEMAS
# =========================
class VehicleCreate(BaseModel):
    number_plate: str
    name: str
    model: str
    year: int
    image_url: str


class VehicleResponse(BaseModel):
    id: int
    number_plate: str
    name: str
    model: str
    year: int
    image_url: str

    class Config:
        orm_mode = True