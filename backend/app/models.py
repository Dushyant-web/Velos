from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
from datetime import datetime
import uuid


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
# ALERT TABLE
# =========================
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id = Column(String, index=True)
    vehicle_name = Column(String)
    vehicle_model = Column(String)

    alert_type = Column(String)
    severity = Column(String)
    message = Column(String)

    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)


# =========================
# USER TABLE (AUTH)
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="fleet_manager")  # admin / fleet_manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fleet = relationship("Fleet", back_populates="owner", uselist=False)


# =========================
# FLEET TABLE
# =========================
class Fleet(Base):
    __tablename__ = "fleets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="fleet")
    vehicles = relationship("Vehicle", back_populates="fleet")


# =========================
# VEHICLE TABLE (UPDATED)
# =========================
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    number_plate = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer)
    image_url = Column(String)

    fleet_id = Column(UUID(as_uuid=True), ForeignKey("fleets.id"))
    fleet = relationship("Fleet", back_populates="vehicles")