from __future__ import annotations


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def calculate_threat_score(
    artificial_urgency: float,
    social_coercion: float,
    institutional_deviation: float,
) -> float:
    score = (
        clamp_score(artificial_urgency) * 0.25
        + clamp_score(social_coercion) * 0.25
        + clamp_score(institutional_deviation) * 0.50
    )
    return round(clamp_score(score), 4)


def risk_level_from_score(score: float) -> str:
    value = clamp_score(score)
    if value <= 0.30:
        return "LOW"
    if value <= 0.60:
        return "MEDIUM"
    if value <= 0.80:
        return "HIGH"
    return "CRITICAL"

