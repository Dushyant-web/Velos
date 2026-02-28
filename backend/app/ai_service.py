from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Telemetry
from .health_service import calculate_health
import math
import statistics


FAILURE_THRESHOLD = 30
WINDOW_SIZE = 30


def compute_engine_failure_probability(db: Session, vehicle_id: str):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(WINDOW_SIZE)
        .all()
    )

    if len(records) < 5:
        return None

    # Get engine health history
    health_values = []

    for r in reversed(records):
        health = calculate_health(db, vehicle_id)
        health_values.append(health["engine_health"])

    # Linear regression slope approximation
    n = len(health_values)
    x = list(range(n))
    y = health_values

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0

    current_health = y[-1]

    if slope >= 0:
        return {
            "engine_failure_probability_90_days": 0.05,
            "trend": "stable_or_improving"
        }

    days_to_failure = (current_health - FAILURE_THRESHOLD) / abs(slope)

    # Sigmoid transform
    probability = 1 / (1 + math.exp(days_to_failure / 30))

    return {
        "engine_failure_probability_90_days": round(probability, 3),
        "trend": "degrading",
        "estimated_days_to_failure": round(days_to_failure, 1)
    }

def detect_anomalies(db: Session, vehicle_id: str):

    records = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .order_by(desc(Telemetry.timestamp))
        .limit(30)
        .all()
    )

    if len(records) < 10:
        return []

    anomalies = []

    def check_metric(metric_name):
        values = [getattr(r, metric_name) for r in records]
        current = values[0]
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0

        if std == 0:
            return

        z_score = (current - mean) / std

        if abs(z_score) > 3:
            anomalies.append({
                "metric": metric_name,
                "severity": "High",
                "z_score": round(z_score, 2)
            })
        elif abs(z_score) > 2.5:
            anomalies.append({
                "metric": metric_name,
                "severity": "Moderate",
                "z_score": round(z_score, 2)
            })

    check_metric("engine_temp")
    check_metric("rpm")
    check_metric("fuel")
    check_metric("speed")

    return anomalies