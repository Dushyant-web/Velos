from .models import Alert, Vehicle
from .health_service import calculate_health
from datetime import datetime

def check_and_create_alert(db, vehicle_id):

    health = calculate_health(db, vehicle_id)

    print("HEALTH:", health)

    if not health:
        print("NO HEALTH")
        return

    vehicle = db.query(Vehicle).filter(
        Vehicle.number_plate == vehicle_id
    ).first()

    print("VEHICLE:", vehicle)

    if not vehicle:
        print("NO VEHICLE")
        return

    alerts = []

    if health["health_score"] < 50:
        print("LOW OVERALL")
        alerts.append(("Health Drop", "High", "Overall health below 50%"))

    if health["engine_health"] < 40:
        print("ENGINE ALERT TRIGGERED")
        alerts.append(("Engine Risk", "High", "Engine degradation critical"))

    print("ALERT LIST:", alerts)
    print("ALERT FUNCTION CALLED")
    print("HEALTH DICT KEYS:", health.keys())
    print("ENGINE VALUE:", health.get("engine_health"))