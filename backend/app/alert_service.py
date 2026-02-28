from .models import Alert, Vehicle
from .health_service import calculate_health
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


COOLDOWN_MINUTES = 5


def check_and_create_alert(db: Session, vehicle_id: str):

    health = calculate_health(db, vehicle_id)

    if not health:
        return

    vehicle = db.query(Vehicle).filter(
        Vehicle.number_plate == vehicle_id
    ).first()

    if not vehicle:
        return

    alerts_to_create = []

    # -------------------------
    # ENGINE RISK TRIGGER
    # -------------------------
    if health["engine_health"] < 40:
        alerts_to_create.append(
            ("Engine Risk", "High", "Engine degradation critical")
        )

    # -------------------------
    # HEALTH DROP TRIGGER
    # -------------------------
    if health["health_score"] < 50:
        alerts_to_create.append(
            ("Health Drop", "High", "Overall health below 50%")
        )

    # -------------------------
    # AUTO RESOLVE ENGINE RISK
    # -------------------------
    if health["engine_health"] >= 40:
        existing_engine_alert = db.query(Alert).filter(
            Alert.vehicle_id == vehicle.number_plate,
            Alert.alert_type == "Engine Risk",
            Alert.resolved == False
        ).first()

        if existing_engine_alert:
            existing_engine_alert.resolved = True

    # -------------------------
    # CREATE ALERTS (DEDUP + COOLDOWN)
    # -------------------------
    for alert_type, severity, message in alerts_to_create:

        last_alert = db.query(Alert).filter(
            Alert.vehicle_id == vehicle.number_plate,
            Alert.alert_type == alert_type
        ).order_by(Alert.timestamp.desc()).first()

        # Cooldown check
        if last_alert:
            time_diff = datetime.utcnow() - last_alert.timestamp
            if time_diff < timedelta(minutes=COOLDOWN_MINUTES):
                continue

        # Avoid duplicate unresolved alerts
        existing_unresolved = db.query(Alert).filter(
            Alert.vehicle_id == vehicle.number_plate,
            Alert.alert_type == alert_type,
            Alert.resolved == False
        ).first()

        if existing_unresolved:
            continue

        new_alert = Alert(
            vehicle_id=vehicle.number_plate,
            vehicle_name=vehicle.name,
            vehicle_model=vehicle.model,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            resolved=False
        )

        db.add(new_alert)

    db.commit()