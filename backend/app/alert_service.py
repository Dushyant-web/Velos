from .models import Alert, Vehicle
from .health_service import calculate_health
from datetime import datetime

def check_and_create_alert(db: Session, vehicle_id: str):

    vehicle = db.query(Vehicle).filter(Vehicle.number_plate == vehicle_id).first()

    if not vehicle:
        print("NO VEHICLE")
        return

    health = calculate_health(vehicle_id)

    alerts = []

    if health["health_score"] < 50:
        alerts.append(("Health Drop", "High", "Overall health below 50%"))

    if health["engine_health"] < 30:
        alerts.append(("Engine Risk", "High", "Engine degradation critical"))

    if health["battery_health"] < 30:
        alerts.append(("Battery Risk", "Medium", "Battery level critical"))

    # 🔥 THIS IS THE IMPORTANT PART
    for alert_type, severity, message in alerts:
        alert = Alert(
            vehicle_id=vehicle.number_plate,
            vehicle_name=vehicle.name,
            vehicle_model=vehicle.model,
            alert_type=alert_type,
            severity=severity,
            message=message
        )
        db.add(alert)

    db.commit()