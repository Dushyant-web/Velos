from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Telemetry
from math import pow

def calculate_health(db: Session, number_plate: str):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == number_plate)
        .order_by(desc(Telemetry.timestamp))
        .limit(300)
        .all()
    )

    if not records:
        return None

    # --- Initial Component Health ---
    engine_health = 100.0
    battery_health = 100.0
    fuel_system_health = 100.0
    drivetrain_health = 100.0

    for r in records:

        # Engine wear
        if r.engine_temp > 100:
            engine_health -= (r.engine_temp - 100) * 0.01

        # Drivetrain wear (RPM stress)
        if r.rpm > 3500:
            drivetrain_health -= (r.rpm - 3500) * 0.002

        # Battery degradation
        if r.battery_level < 50:
            battery_health -= (50 - r.battery_level) * 0.01

        # Fuel system wear
        if r.fuel < 25:
            fuel_system_health -= (25 - r.fuel) * 0.01 

    # Clamp all
    engine_health = max(0, min(100, engine_health))
    battery_health = max(0, min(100, battery_health))
    fuel_system_health = max(0, min(100, fuel_system_health))
    drivetrain_health = max(0, min(100, drivetrain_health))

    # Weighted overall health
    health_score = (
        engine_health * 0.35 +
        battery_health * 0.25 +
        fuel_system_health * 0.20 +
        drivetrain_health * 0.20
    )

    health_score = max(0, min(100, health_score))

    predicted_life = round(20 * pow(health_score / 100, 1.4), 2)

    risk = "Low"
    if health_score < 70:
        risk = "Moderate"
    if health_score < 50:
        risk = "High"
    if health_score < 30:
        risk = "Critical"

    return {
        "health_score": round(health_score, 2),
        "predicted_life_years": predicted_life,
        "risk_level": risk,
        "engine_health": round(engine_health, 2),
        "battery_health": round(battery_health, 2),
        "fuel_system_health": round(fuel_system_health, 2),
        "drivetrain_health": round(drivetrain_health, 2)
    }