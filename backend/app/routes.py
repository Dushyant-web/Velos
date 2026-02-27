from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Telemetry
from .schemas import TelemetryCreate
from sqlalchemy import desc

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/telemetry")
def create_telemetry(data: TelemetryCreate, db: Session = Depends(get_db)):
    telemetry = Telemetry(**data.dict())
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)
    return {"message": "Telemetry stored successfully"}


@router.get("/telemetry/{vehicle_id}")
def get_recent_telemetry(vehicle_id: str, limit: int = 10, db: Session = Depends(get_db)):
    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(limit)
        .all()
    )
    return records