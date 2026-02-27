from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)

    speed = Column(Float)
    engine_temp = Column(Float)
    battery_level = Column(Float)
    fuel = Column(Float)
    rpm = Column(Float)

    latitude = Column(Float)
    longitude = Column(Float)
    tire_pressure = Column(Float)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())