from .models import Alert, Vehicle
from .health_service import calculate_health
from datetime import datetime
from sqlalchemy.orm import Session


def check_and_create_alert(db: Session, vehicle_id: str):

    health = calculate_health(db, vehicle_id)

    if not health:
        print("NO HEALTH")
        return

    vehicle = db.query(Vehicle).filter(
        Vehicle.number_plate == vehicle_id
    ).first()

    if not vehicle:
        print("NO VEHICLE")
        return

    alerts = []

    if health["health_score"] < 50:
        alerts.append(("Health Drop", "High", "Overall health below 50%"))

    if health["engine_health"] < 40:
        alerts.append(("Engine Risk", "High", "Engine degradation critical"))

    # 🔥 THIS WAS MISSING
    for alert_type, severity, message in alerts:
        alert = Alert(
            vehicle_id=vehicle.number_plate,
            vehicle_name=vehicle.name,
            vehicle_model=vehicle.model,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            resolved=False
        )
        db.add(alert)

    if alerts:
        db.commit()
        print("ALERTS SAVED:", len(alerts))