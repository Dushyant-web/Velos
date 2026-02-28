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

def compute_risk_confidence(db: Session, vehicle_id: str):

    from .ai_service import compute_engine_failure_probability, detect_anomalies
    from .health_service import calculate_health

    health = calculate_health(db, vehicle_id)
    failure = compute_engine_failure_probability(db, vehicle_id)
    anomalies = detect_anomalies(db, vehicle_id)

    if not health or not failure:
        return None

    failure_prob = failure["engine_failure_probability_90_days"]
    normalized_health = health["health_score"] / 100
    anomaly_factor = min(len(anomalies) / 3, 1)

    risk_score = (
        0.5 * failure_prob +
        0.3 * (1 - normalized_health) +
        0.2 * anomaly_factor
    )

    if risk_score > 0.7:
        risk_level = "High"
    elif risk_score > 0.4:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # Confidence based on telemetry depth
    record_count = (
        db.query(Telemetry)
        .filter(Telemetry.vehicle_id == vehicle_id)
        .count()
    )

    confidence_score = min(record_count / 30, 1)

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "confidence_score": round(confidence_score, 3)
    }

def generate_recommendations(failure, anomalies, risk):

    recommendations = []

    if failure and failure.get("engine_failure_probability_90_days", 0) > 0.6:
        recommendations.append(
            "Schedule engine inspection within 14 days"
        )

    for anomaly in anomalies:
        if anomaly["metric"] == "rpm":
            recommendations.append("Reduce aggressive acceleration")
        if anomaly["metric"] == "engine_temp":
            recommendations.append("Avoid high-load driving for next 7 days")
        if anomaly["metric"] == "fuel":
            recommendations.append("Inspect fuel system for irregular usage")

    if risk and risk.get("risk_level") == "High":
        recommendations.append("Prioritize preventive maintenance")

    return list(set(recommendations))

def unified_ai_analysis(db: Session, vehicle_id: str):

    failure = compute_engine_failure_probability(db, vehicle_id)
    anomalies = detect_anomalies(db, vehicle_id)
    risk = compute_risk_confidence(db, vehicle_id)

    recommendations = generate_recommendations(
        failure, anomalies, risk
    )

    return {
        "failure_probability": failure,
        "anomalies": anomalies,
        "risk_analysis": risk,
        "recommendations": recommendations
    }

def compute_component_failure_probabilities(db: Session, vehicle_id: str):

    from .health_service import calculate_health

    health = calculate_health(db, vehicle_id)

    if not health:
        return None

    def health_to_failure_prob(score):
        normalized = 1 - (score / 100)
        return min(1, normalized ** 1.8)

    engine_prob = health_to_failure_prob(health["engine_health"])
    battery_prob = health_to_failure_prob(health["battery_health"])
    drivetrain_prob = health_to_failure_prob(health["drivetrain_health"])
    fuel_prob = health_to_failure_prob(health["fuel_system_health"])

    overall_prob = (
        engine_prob * 0.4 +
        battery_prob * 0.2 +
        drivetrain_prob * 0.25 +
        fuel_prob * 0.15
    )

    return {
        "engine_failure_probability": round(engine_prob, 3),
        "battery_failure_probability": round(battery_prob, 3),
        "drivetrain_failure_probability": round(drivetrain_prob, 3),
        "fuel_system_failure_probability": round(fuel_prob, 3),
        "overall_vehicle_failure_probability": round(overall_prob, 3)
    }


def weibull_failure_probability(health_score, projected_days=90):

    # shape parameter (wear-out type failure)
    beta = 2.2  

    # scale parameter depends on health
    # healthier vehicle = larger eta
    eta = 180 * (health_score / 100)

    if eta <= 0:
        return 1

    survival = math.exp(-((projected_days / eta) ** beta))
    failure_probability = 1 - survival

    return round(min(1, failure_probability), 3)