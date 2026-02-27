from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Telemetry


def calculate_health(db: Session, number_plate: str):
    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == number_plate)
        .order_by(desc(Telemetry.timestamp))
        .limit(200)
        .all()
    )

    if not records:
        return None

    avg_temp = sum(r.engine_temp for r in records) / len(records)
    avg_rpm = sum(r.rpm for r in records) / len(records)
    avg_speed = sum(r.speed for r in records) / len(records)

    fuel_start = records[-1].fuel
    fuel_end = records[0].fuel
    fuel_burn = fuel_start - fuel_end

    # ---------- HEALTH FORMULA ----------
    health = 100

    if avg_temp > 100:
        health -= (avg_temp - 100) * 0.5

    if avg_rpm > 4000:
        health -= (avg_rpm - 4000) * 0.01

    if avg_speed > 120:
        health -= 5

    if fuel_burn > 5:
        health -= 5

    health = max(0, min(100, health))

    # Predict life out of 20 years
    predicted_life = round(20 * (health / 100), 2)

    risk = "Low"
    if health < 70:
        risk = "Moderate"
    if health < 50:
        risk = "High"

    return {
        "health_score": round(health, 2),
        "predicted_life_years": predicted_life,
        "risk_level": risk,
        "avg_engine_temp": round(avg_temp, 2),
        "avg_rpm": round(avg_rpm, 2),
        "avg_speed": round(avg_speed, 2),
        "fuel_burn_last_cycle": round(fuel_burn, 2),
    }