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

    total_stress = 0

    for r in records:
        stress = 0

        if r.engine_temp > 100:
            stress += (r.engine_temp - 100) / 400

        if r.rpm > 3500:
            stress += (r.rpm - 3500) / 10000

        if r.battery_level < 50:
            stress += (50 - r.battery_level) / 800

        if r.fuel < 25:
            stress += (25 - r.fuel) / 800

        total_stress += stress

    avg_stress = total_stress / len(records)

    # 🔥 Non-linear aging factor
    aging_factor = 1 + pow(avg_stress, 1.3)

    base_health = 100 - (avg_stress * 50)

    health = base_health / aging_factor

    health = max(0, min(100, health))

    # Non-linear life curve (accelerates after mid-life)
    predicted_life = round(20 * pow(health / 100, 1.4), 2)

    risk = "Low"
    if health < 70:
        risk = "Moderate"
    if health < 50:
        risk = "High"
    if health < 30:
        risk = "Critical"

    return {
        "health_score": round(health, 2),
        "predicted_life_years": predicted_life,
        "risk_level": risk,
        "avg_stress_index": round(avg_stress, 4)
    }