from .health_service import calculate_health


def simulate_terrain(db, number_plate: str, terrain: str):
    base_data = calculate_health(db, number_plate)

    if not base_data:
        return None

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

    new_health = max(0, health - terrain_penalty)
    new_predicted_life = round(20 * (new_health / 100), 2)

    return {
        "original_health": health,
        "terrain": terrain,
        "new_health_score": round(new_health, 2),
        "new_predicted_life_years": new_predicted_life,
        "life_reduction_years": round(base_data["predicted_life_years"] - new_predicted_life, 2)
    }