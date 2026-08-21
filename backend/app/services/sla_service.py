"""
SLA Monitoring & Risk Assessment Service
=========================================
Calculates real-time SLA risk, target resolution windows, breach probability,
and priority rankings for anomalies across Claims, Pharmacy, and Authorization datasets.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

# Resolution target hours based on severity
SLA_TARGET_HOURS = {
    "CRITICAL": 4,      # 4 hours
    "HIGH": 24,         # 1 day
    "MEDIUM": 48,       # 2 days
    "LOW": 72,          # 3 days
}

SEVERITY_BASE_SCORES = {
    "CRITICAL": 85,
    "HIGH": 65,
    "MEDIUM": 40,
    "LOW": 15,
}


def calculate_sla_risk(
    anomaly_record: Dict[str, Any],
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Computes comprehensive SLA risk assessment for an anomaly.

    Returns:
        target_hours: int
        deadline: str (ISO format)
        elapsed_hours: float
        remaining_hours: float
        breach_probability: float (0.0 to 1.0)
        sla_status: ON_TRACK | AT_RISK | BREACHED | RESOLVED
        sla_risk_tier: LOW | MEDIUM | HIGH | CRITICAL
        sla_risk_score: int (0 to 100)
    """
    severity = str(anomaly_record.get("severity", "MEDIUM")).upper()
    status = str(anomaly_record.get("status", "OPEN")).upper()
    
    target_hours = SLA_TARGET_HOURS.get(severity, 48)
    base_score = SEVERITY_BASE_SCORES.get(severity, 40)

    now = datetime.now(timezone.utc)
    if created_at is None:
        created_at = now

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    deadline = created_at + timedelta(hours=target_hours)
    elapsed_seconds = max(0.0, (now - created_at).total_seconds())
    elapsed_hours = round(elapsed_seconds / 3600.0, 2)
    remaining_seconds = (deadline - now).total_seconds()
    remaining_hours = round(remaining_seconds / 3600.0, 2)

    # If already resolved or closed
    if status in ("RESOLVED", "CLOSED", "REJECTED"):
        return {
            "target_hours": target_hours,
            "deadline": deadline.isoformat(),
            "elapsed_hours": elapsed_hours,
            "remaining_hours": max(0.0, remaining_hours),
            "breach_probability": 0.0,
            "sla_status": "RESOLVED",
            "sla_risk_tier": "LOW",
            "sla_risk_score": 0,
            "recommendation": "Anomaly successfully addressed within operational SLA.",
        }

    # Time ratio used
    time_used_ratio = min(2.0, elapsed_hours / target_hours) if target_hours > 0 else 1.0
    
    # Calculate breach probability & SLA status
    if remaining_hours <= 0:
        sla_status = "BREACHED"
        breach_probability = 1.0
        risk_score = 100
        risk_tier = "CRITICAL"
    elif time_used_ratio >= 0.75:
        sla_status = "AT_RISK"
        breach_probability = round(min(0.95, 0.60 + (time_used_ratio - 0.75) * 1.4), 2)
        risk_score = min(99, int(base_score + (time_used_ratio * 25)))
        risk_tier = "CRITICAL" if risk_score >= 80 else "HIGH"
    elif time_used_ratio >= 0.50:
        sla_status = "ON_TRACK"
        breach_probability = round(0.20 + (time_used_ratio - 0.50) * 0.8, 2)
        risk_score = min(75, int(base_score + (time_used_ratio * 15)))
        risk_tier = "HIGH" if severity == "CRITICAL" else "MEDIUM"
    else:
        sla_status = "ON_TRACK"
        breach_probability = round(max(0.05, time_used_ratio * 0.3), 2)
        risk_score = base_score
        risk_tier = severity if severity in ("LOW", "MEDIUM", "HIGH") else "MEDIUM"

    return {
        "target_hours": target_hours,
        "deadline": deadline.isoformat(),
        "elapsed_hours": elapsed_hours,
        "remaining_hours": remaining_hours,
        "breach_probability": breach_probability,
        "sla_status": sla_status,
        "sla_risk_tier": risk_tier,
        "sla_risk_score": risk_score,
        "recommendation": (
            f"Expedite resolution! {abs(remaining_hours):.1f}h past SLA deadline."
            if sla_status == "BREACHED"
            else f"{remaining_hours:.1f}h remaining before {severity} SLA breach. Assign steward immediately."
            if sla_status == "AT_RISK"
            else f"On track with {remaining_hours:.1f}h remaining."
        ),
    }
