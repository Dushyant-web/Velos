from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from math import pow

from .database import SessionLocal
from .models import Telemetry, Vehicle
from .schemas import TelemetryCreate, VehicleCreate, VehicleResponse
from .health_service import calculate_health
from .simulation_service import simulate_terrain

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


# =========================
# VEHICLE PATH
# =========================
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


# =========================
# HEALTH TREND (Improved Model)
# =========================
@router.get("/vehicle/{vehicle_id}/health-trend")
def health_trend(vehicle_id: str, limit: int = 100, db: Session = Depends(get_db)):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.timestamp.asc())
        .limit(limit)
        .all()
    )

    total_life = 20.0
    life_remaining = total_life
    trend = []

    for r in records:

        stress = 0

        if r.engine_temp > 95:
            stress += (r.engine_temp - 95) / 500

        if r.rpm > 3500:
            stress += (r.rpm - 3500) / 10000

        if r.battery_level < 40:
            stress += (40 - r.battery_level) / 800

        if r.fuel < 20:
            stress += (20 - r.fuel) / 800

        life_remaining -= stress
        life_remaining = max(0, life_remaining)

        health_score = (life_remaining / total_life) * 100

        trend.append({
            "timestamp": r.timestamp,
            "health_score": round(health_score, 2),
            "life_remaining_years": round(life_remaining, 3)
        })

    return trend


# =========================
# PROJECT LIFE (Phase 4 Non-Linear Engine)
# =========================
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
        .limit(150)
        .all()
    )

    if not records:
        return {"error": "No data"}

    # ---- STEP 1: Average stress ----
    total_stress = 0

    for r in records:
        stress = 0

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

    # ---- STEP 2: Non-Linear Degradation ----
    base_yearly_wear = 1 / 20
    stress_multiplier = 1 + pow(avg_stress, 1.4)

    yearly_degradation = base_yearly_wear * stress_multiplier

    # ---- STEP 3: Convert requested time ----
    total_years_requested = (
        years +
        (months / 12) +
        (hours / (24 * 365))
    )

    total_life = 20.0

    life_consumed = yearly_degradation * total_years_requested * 20
    projected_life_remaining = max(0, total_life - life_consumed)

    # Curve effect near failure
    projected_life_remaining = total_life * pow(
        projected_life_remaining / total_life, 1.2
    )

    projected_health = (projected_life_remaining / total_life) * 100

    # ---- STEP 4: Failure Date Prediction ----
    if projected_health <= 15:
        failure_years = total_years_requested
    else:
        failure_years = (projected_life_remaining / total_life) * 20

    failure_date = datetime.utcnow() + timedelta(days=failure_years * 365)

    return {
        "projected_health_percentage": round(projected_health, 2),
        "projected_life_remaining_years": round(projected_life_remaining, 2),
        "predicted_failure_date": failure_date.strftime("%Y-%m-%d"),
        "stress_index": round(avg_stress, 4)
    }

@router.post("/vehicle/{vehicle_id}/what-if")
def what_if_simulation(
    vehicle_id: str,
    scenario: dict = Body(...),
    db: Session = Depends(get_db)
):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(150)
        .all()
    )

    if not records:
        return {"error": "No telemetry data"}

    max_temp = scenario.get("max_temp", 100)
    max_rpm = scenario.get("max_rpm", 3500)
    component = scenario.get("component", "all")

    current_health = calculate_health(db, vehicle_id)

    engine_health = current_health["engine_health"]
    battery_health = current_health["battery_health"]
    fuel_system_health = current_health["fuel_system_health"]
    drivetrain_health = current_health["drivetrain_health"]

    for r in records:

        if component in ["engine", "all"]:
            if r.engine_temp > max_temp:
                engine_health -= (r.engine_temp - max_temp) * 0.01

        if component in ["drivetrain", "all"]:
            if r.rpm > max_rpm:
                drivetrain_health -= (r.rpm - max_rpm) * 0.002

        if component in ["battery", "all"]:
            if r.battery_level < 50:
                battery_health -= (50 - r.battery_level) * 0.01

        if component in ["fuel", "all"]:
            if r.fuel < 25:
                fuel_system_health -= (25 - r.fuel) * 0.01

    # Clamp values
    engine_health = max(0, min(100, engine_health))
    battery_health = max(0, min(100, battery_health))
    fuel_system_health = max(0, min(100, fuel_system_health))
    drivetrain_health = max(0, min(100, drivetrain_health))

    # Weighted overall health
    projected_overall = (
        engine_health * 0.35 +
        battery_health * 0.25 +
        fuel_system_health * 0.20 +
        drivetrain_health * 0.20
    )

    predicted_life = 20 * pow(projected_overall / 100, 1.4)

    return {
        "what_if_overall_health": round(projected_overall, 2),
        "engine_health": round(engine_health, 2),
        "battery_health": round(battery_health, 2),
        "fuel_system_health": round(fuel_system_health, 2),
        "drivetrain_health": round(drivetrain_health, 2),
        "what_if_life_years": round(predicted_life, 2)
    }

@router.get("/vehicle/{vehicle_id}/recommended-scenarios")
def recommended_scenarios(vehicle_id: str):

    return {
        "eco_mode": {
            "max_temp": 95,
            "max_rpm": 3000,
            "driving_style": "eco",
            "maintenance_factor": 0.9
        },
        "balanced_mode": {
            "max_temp": 100,
            "max_rpm": 3500,
            "driving_style": "normal",
            "maintenance_factor": 1.0
        },
        "performance_mode": {
            "max_temp": 110,
            "max_rpm": 4500,
            "driving_style": "aggressive",
            "maintenance_factor": 1.2
        }
    }

@router.get("/vehicle/{vehicle_id}/maintenance-cost")
def maintenance_cost(vehicle_id: str, db: Session = Depends(get_db)):

    current_health = calculate_health(db, vehicle_id)

    if not current_health:
        return {"error": "No telemetry data"}

    engine = current_health["engine_health"]
    battery = current_health["battery_health"]
    fuel = current_health["fuel_system_health"]
    drivetrain = current_health["drivetrain_health"]

    # Cost multipliers (can later move to config)
    engine_cost = (100 - engine) * 50
    battery_cost = (100 - battery) * 30
    fuel_cost = (100 - fuel) * 20
    drivetrain_cost = (100 - drivetrain) * 40

    total_cost = engine_cost + battery_cost + fuel_cost + drivetrain_cost

    return {
        "engine_repair_estimate": round(engine_cost, 2),
        "battery_repair_estimate": round(battery_cost, 2),
        "fuel_system_repair_estimate": round(fuel_cost, 2),
        "drivetrain_repair_estimate": round(drivetrain_cost, 2),
        "total_estimated_maintenance_cost": round(total_cost, 2)
    }