from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .database import Base


# =========================
# TELEMETRY TABLE
# =========================
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


# =========================
# VEHICLE METADATA TABLE
# =========================
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    number_plate = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer)
    image_url = Column(String)