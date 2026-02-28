from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .simulation_service import simulate_terrain
from fastapi import Body
from datetime import timedelta

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
def health_trend(vehicle_id: str, limit: int = 100, db: Session = Depends(get_db)):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.timestamp.asc())
        .limit(limit)
        .all()
    )

    life_remaining = 20.0  # 20 year total vehicle life

    trend = []

    for r in records:

        stress = 0

        # Temperature stress
        if r.engine_temp > 95:
            stress += 0.002

        # High RPM stress
        if r.rpm > 3500:
            stress += 0.001

        # Low battery stress
        if r.battery_level < 40:
            stress += 0.001

        # Low fuel stress
        if r.fuel < 20:
            stress += 0.001

        life_remaining -= stress
        life_remaining = max(0, life_remaining)

        health_score = (life_remaining / 20.0) * 100

        trend.append({
            "timestamp": r.timestamp,
            "health_score": round(health_score, 2),
            "life_remaining_years": round(life_remaining, 3)
        })

    return trend



@router.get("/vehicle/{vehicle_id}/project-life")
def project_life(
    vehicle_id: str,
    years: float = 0,
    months: float = 0,
    hours: float = 0,
    db: Session = Depends(get_db)
):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(100)
        .all()
    )

    if not records:
        return {"error": "No data"}

    # --- STEP 1: calculate average stress level ---
    total_stress = 0

    for r in records:
        stress = 0

        # Realistic stress model
        if r.engine_temp > 110:
            stress += (r.engine_temp - 110) / 500

        if r.rpm > 3000:
            stress += (r.rpm - 3000) / 8000

        if r.battery_level < 50:
            stress += (50 - r.battery_level) / 500

        if r.fuel < 25:
            stress += (25 - r.fuel) / 500

        total_stress += stress

    avg_stress = total_stress / len(records)

    # --- STEP 2: Convert stress to yearly degradation ---
    # Base yearly wear = 1 year consumed per 20 years lifespan
    base_yearly_wear = 1 / 20  

    # Stress multiplier
    yearly_degradation = base_yearly_wear * (1 + avg_stress)

    # --- STEP 3: Convert requested time to years ---
    total_years_requested = (
        years +
        (months / 12) +
        (hours / (24 * 365))
    )

    total_life = 20.0

    projected_life_remaining = max(
        0,
        total_life - (yearly_degradation * total_years_requested * 20)
    )

    projected_health = (projected_life_remaining / total_life) * 100

    return {
        "projected_health_percentage": round(projected_health, 2),
        "projected_life_remaining_years": round(projected_life_remaining, 2)
    }