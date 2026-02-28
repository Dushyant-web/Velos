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

@router.post("/vehicle/{vehicle_id}/compare")
def compare_scenario(
    vehicle_id: str,
    scenario: dict = Body(...),
    db: Session = Depends(get_db)
):

    # ---------- CURRENT BASELINE ----------
    current = calculate_health(db, vehicle_id)

    if not current:
        return {"error": "No telemetry data"}

    current_health = current["health_score"]
    current_life = current["predicted_life_years"]

    engine_current = current["engine_health"]
    battery_current = current["battery_health"]
    fuel_current = current["fuel_system_health"]
    drivetrain_current = current["drivetrain_health"]

    current_cost = (
        (100 - engine_current) * 50 +
        (100 - battery_current) * 30 +
        (100 - fuel_current) * 20 +
        (100 - drivetrain_current) * 40
    )

    # ---------- WHAT IF ----------
    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(150)
        .all()
    )

    max_temp = scenario.get("max_temp", 100)
    max_rpm = scenario.get("max_rpm", 3500)
    component = scenario.get("component", "all")

    engine_scenario = engine_current
    battery_scenario = battery_current
    fuel_scenario = fuel_current
    drivetrain_scenario = drivetrain_current

    for r in records:

        if component in ["engine", "all"] and r.engine_temp > max_temp:
            engine_scenario -= (r.engine_temp - max_temp) * 0.01

        if component in ["drivetrain", "all"] and r.rpm > max_rpm:
            drivetrain_scenario -= (r.rpm - max_rpm) * 0.002

        if component in ["battery", "all"] and r.battery_level < 50:
            battery_scenario -= (50 - r.battery_level) * 0.01

        if component in ["fuel", "all"] and r.fuel < 25:
            fuel_scenario -= (25 - r.fuel) * 0.01

    # Clamp
    engine_scenario = max(0, min(100, engine_scenario))
    battery_scenario = max(0, min(100, battery_scenario))
    fuel_scenario = max(0, min(100, fuel_scenario))
    drivetrain_scenario = max(0, min(100, drivetrain_scenario))

    what_if_overall = (
        engine_scenario * 0.35 +
        battery_scenario * 0.25 +
        fuel_scenario * 0.20 +
        drivetrain_scenario * 0.20
    )

    what_if_life = 20 * pow(what_if_overall / 100, 1.4)

    what_if_cost = (
        (100 - engine_scenario) * 50 +
        (100 - battery_scenario) * 30 +
        (100 - fuel_scenario) * 20 +
        (100 - drivetrain_scenario) * 40
    )

    # ---------- DELTA ----------
    return {
        "current": {
            "overall_health": round(current_health, 2),
            "life_years": round(current_life, 2),
            "maintenance_cost": round(current_cost, 2),
            "engine_health": round(engine_current, 2),
            "battery_health": round(battery_current, 2),
            "fuel_system_health": round(fuel_current, 2),
            "drivetrain_health": round(drivetrain_current, 2)
        },
        "what_if": {
            "overall_health": round(what_if_overall, 2),
            "life_years": round(what_if_life, 2),
            "maintenance_cost": round(what_if_cost, 2),
            "engine_health": round(engine_scenario, 2),
            "battery_health": round(battery_scenario, 2),
            "fuel_system_health": round(fuel_scenario, 2),
            "drivetrain_health": round(drivetrain_scenario, 2)
        },
        "delta": {
            "health_difference": round(what_if_overall - current_health, 2),
            "life_difference_years": round(what_if_life - current_life, 2),
            "cost_difference": round(current_cost - what_if_cost, 2),
            "engine_delta": round(engine_scenario - engine_current, 2),
            "battery_delta": round(battery_scenario - battery_current, 2),
            "fuel_system_delta": round(fuel_scenario - fuel_current, 2),
            "drivetrain_delta": round(drivetrain_scenario - drivetrain_current, 2)
        }
    }

@router.get("/fleet/overview")
def fleet_overview(db: Session = Depends(get_db)):

    vehicles = db.query(Vehicle).all()

    if not vehicles:
        return {"error": "No vehicles found"}

    total_health = 0
    total_life = 0
    total_cost = 0

    worst_vehicle = None
    best_vehicle = None

    worst_health = 101
    best_health = -1

    for v in vehicles:

        health_data = calculate_health(db, v.number_plate)

        if not health_data:
            continue

        health = health_data["health_score"]
        life = health_data["predicted_life_years"]

        engine = health_data["engine_health"]
        battery = health_data["battery_health"]
        fuel = health_data["fuel_system_health"]
        drivetrain = health_data["drivetrain_health"]

        cost = (
            (100 - engine) * 50 +
            (100 - battery) * 30 +
            (100 - fuel) * 20 +
            (100 - drivetrain) * 40
        )

        total_health += health
        total_life += life
        total_cost += cost

        if health < worst_health:
            worst_health = health
            worst_vehicle = v.number_plate

        if health > best_health:
            best_health = health
            best_vehicle = v.number_plate

    count = len(vehicles)

    return {
        "total_vehicles": count,
        "average_fleet_health": round(total_health / count, 2),
        "average_fleet_life_years": round(total_life / count, 2),
        "total_estimated_maintenance_cost": round(total_cost, 2),
        "worst_vehicle": worst_vehicle,
        "best_vehicle": best_vehicle
    }


@router.get("/fleet/risk-distribution")
def fleet_risk_distribution(db: Session = Depends(get_db)):

    vehicles = db.query(Vehicle).all()

    low = 0
    moderate = 0
    high = 0
    critical = 0

    for v in vehicles:

        health_data = calculate_health(db, v.number_plate)

        if not health_data:
            continue

        risk = health_data["risk_level"]

        if risk == "Low":
            low += 1
        elif risk == "Moderate":
            moderate += 1
        elif risk == "High":
            high += 1
        elif risk == "Critical":
            critical += 1

    total = low + moderate + high + critical

    return {
        "total_vehicles_evaluated": total,
        "low_risk": low,
        "moderate_risk": moderate,
        "high_risk": high,
        "critical_risk": critical
    }


@router.get("/fleet/ranking")
def fleet_ranking(db: Session = Depends(get_db)):

    vehicles = db.query(Vehicle).all()

    ranking = []

    for v in vehicles:

        health_data = calculate_health(db, v.number_plate)

        if not health_data:
            continue

        ranking.append({
            "vehicle_id": v.number_plate,
            "health_score": health_data["health_score"],
            "predicted_life_years": health_data["predicted_life_years"],
            "risk_level": health_data["risk_level"]
        })

    ranking.sort(key=lambda x: x["health_score"])

    return {
        "fleet_ranking_worst_to_best": ranking
    }