from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Telemetry
from .health_service import calculate_health


def detect_terrain(db: Session, number_plate: str):
    """
    Intelligent terrain detection using vehicle behavior patterns.
    No external APIs required.
    """

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == number_plate)
        .order_by(desc(Telemetry.timestamp))
        .limit(30)
        .all()
    )

    if not records:
        return "city"

    speeds = [r.speed for r in records]
    rpms = [r.rpm for r in records]
    temps = [r.engine_temp for r in records]

    avg_speed = sum(speeds) / len(speeds)
    speed_variation = max(speeds) - min(speeds)
    avg_rpm = sum(rpms) / len(rpms)
    avg_temp = sum(temps) / len(temps)

    # Highway detection
    if avg_speed > 85 and speed_variation < 20:
        return "highway"

    # City detection
    if avg_speed < 35 and speed_variation > 25:
        return "city"

    # Hilly detection
    if avg_rpm > 3500 and avg_speed < 70 and avg_temp > 100:
        return "hilly"

    # Offroad detection
    if speed_variation > 40 and avg_speed < 50:
        return "offroad"

    return "mixed"


def simulate_terrain(db: Session, number_plate: str):
    """
    Simulate health impact based on auto-detected terrain
    """

    base_data = calculate_health(db, number_plate)

    if not base_data:
        return None

    terrain = detect_terrain(db, number_plate)
    health = base_data["health_score"]

    # Terrain penalty logic
    terrain_penalty = 0

    if terrain == "city":
        terrain_penalty = 5
    elif terrain == "highway":
        terrain_penalty = 3
    elif terrain == "hilly":
        terrain_penalty = 10
    elif terrain == "offroad":
        terrain_penalty = 15
    elif terrain == "mixed":
        terrain_penalty = 6

    new_health = max(0, health - terrain_penalty)
    new_predicted_life = round(20 * (new_health / 100), 2)

    return {
        "original_health": health,
        "terrain": terrain,
        "new_health_score": round(new_health, 2),
        "new_predicted_life_years": new_predicted_life,
        "life_reduction_years": round(
            base_data["predicted_life_years"] - new_predicted_life, 2
        )
    }