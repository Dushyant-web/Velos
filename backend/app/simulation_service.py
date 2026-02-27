import os
import requests
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Telemetry
from .health_service import calculate_health


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def detect_terrain(db: Session, number_plate: str):
    """
    Hybrid terrain detection:
    1. Rule-based detection using speed patterns
    2. Optional Google Elevation API enhancement
    """

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == number_plate)
        .order_by(desc(Telemetry.timestamp))
        .limit(20)
        .all()
    )

    if not records:
        return "city"  # default fallback

    avg_speed = sum(r.speed for r in records) / len(records)

    # --- RULE BASED DETECTION ---
    if avg_speed > 85:
        terrain = "highway"
    elif avg_speed < 25:
        terrain = "city"
    else:
        terrain = "mixed"

    # --- GOOGLE ELEVATION ENHANCEMENT (optional) ---
    if GOOGLE_API_KEY:
        try:
            latest = records[0]
            elevation_url = (
                f"https://maps.googleapis.com/maps/api/elevation/json"
                f"?locations={latest.latitude},{latest.longitude}"
                f"&key={GOOGLE_API_KEY}"
            )

            response = requests.get(elevation_url, timeout=3)
            data = response.json()

            if data.get("results"):
                elevation = data["results"][0]["elevation"]

                # Elevation logic
                if elevation > 500:
                    terrain = "hilly"
                elif elevation < 50 and avg_speed < 40:
                    terrain = "offroad"

        except Exception:
            # If API fails, ignore and keep rule-based result
            pass

    return terrain


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