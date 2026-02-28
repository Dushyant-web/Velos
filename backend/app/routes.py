from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .simulation_service import simulate_terrain
from fastapi import Body

from .database import SessionLocal
from .models import Telemetry, Vehicle
from .schemas import TelemetryCreate, VehicleCreate, VehicleResponse
from .health_service import calculate_health

router = APIRouter()


# =========================
# DB DEPENDENCY
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# TELEMETRY ROUTES
# =========================
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


# =========================
# VEHICLE ROUTES
# =========================
@router.post("/vehicles", response_model=VehicleResponse)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = Vehicle(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.get("/vehicles", response_model=list[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).all()

@router.get("/vehicle/{number_plate}/health")
def get_vehicle_health(number_plate: str, db: Session = Depends(get_db)):
    result = calculate_health(db, number_plate)

    if not result:
        return {"message": "No telemetry data found"}

    return result

@router.post("/vehicle/{number_plate}/simulate-terrain")
def simulate_vehicle_terrain(
    number_plate: str,
    terrain: str = Body(...),
    db: Session = Depends(get_db)
):
    result = simulate_terrain(db, number_plate, terrain)

    if not result:
        return {"message": "No telemetry data found"}

    return result

@router.get("/vehicle/{vehicle_id}/path")
def get_vehicle_path(vehicle_id: str, limit: int = 100, db: Session = Depends(get_db)):
    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(limit)
        .all()
    )

    return [
        {
            "latitude": r.latitude,
            "longitude": r.longitude,
            "timestamp": r.timestamp
        }
        for r in records
    ]


@router.get("/vehicle/{vehicle_id}/health-trend")
def health_trend(vehicle_id: str, limit: int = 50, db: Session = Depends(get_db)):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.timestamp.asc())
        .limit(limit)
        .all()
    )

    trend = []

    for r in records:
        health_score = 100

        # Same logic as calculate_health
        if r.engine_temp > 110:
            health_score -= 20
        if r.battery_level < 30:
            health_score -= 15
        if r.fuel < 10:
            health_score -= 10

        trend.append({
            "timestamp": r.timestamp,
            "health_score": max(0, health_score),
            "engine_temp": r.engine_temp,
            "speed": r.speed
        })

    return trend