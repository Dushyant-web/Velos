from .models import Alert, Vehicle
from .health_service import calculate_health
from datetime import datetime

def check_and_create_alert(db, vehicle_id):

    health = calculate_health(db, vehicle_id)

    if not health:
        return

    vehicle = db.query(Vehicle).filter(Vehicle.number_plate == vehicle_id).first()

    if not vehicle:
        return

    alerts = []

    if health["health_score"] < 50:
        alerts.append(("Health Drop", "High", "Overall health below 50%"))

    if health["engine_health"] < 40:
        alerts.append(("Engine Risk", "High", "Engine degradation critical"))

    if health["battery_health"] < 35:
        alerts.append(("Battery Risk", "Moderate", "Battery health dropping"))

    if health["predicted_life_years"] < 5:
        alerts.append(("Low Life Remaining", "Critical", "Vehicle near failure"))

    for alert_type, severity, message in alerts:
        alert = Alert(
            vehicle_id=vehicle_id,
            vehicle_name=vehicle.name,
            vehicle_model=vehicle.model,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.add(alert)

    db.commit()