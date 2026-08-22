"""
Common SLA Engine
=================
ONE SLA engine for all three datasets (Claims, Authorization, Pharmacy).

Input:  StandardAnomalyRecord  (from any adapter)
Output: SLABlock attached to the record in-place; record returned.

All thresholds are read from config/sla_config.json — nothing is hardcoded.

SLA Score formula (record level):
    score = w_anomaly  * anomaly_contribution
           + w_severity * severity_contribution
           + w_signal   * signal_contribution

Wraps the logic proven in `sla risk/sla monitoring.py` and adapts it to
work with StandardAnomalyRecord objects.
"""

from __future__ import annotations

# ── Path bootstrap — keeps imports working when run as a script ───────────
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
# ─────────────────────────────────────────────────────────────────────────

import json
import logging
from pathlib import Path
from typing import Any, Dict

from integration.common_schema import SLABlock, StandardAnomalyRecord

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Load config once at import time
# ─────────────────────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "sla_config.json"


def _load_config() -> Dict[str, Any]:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.error("Could not load sla_config.json: %s — using defaults", exc)
        return _default_config()


def _default_config() -> Dict[str, Any]:
    return {
        "severity_weights":       {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4},
        "risk_level_thresholds":  {
            "LOW":      {"min": 0,  "max": 30},
            "MEDIUM":   {"min": 30, "max": 60},
            "HIGH":     {"min": 60, "max": 80},
            "CRITICAL": {"min": 80, "max": 100},
        },
        "record_scoring_weights": {"anomaly_existence": 0.50, "severity": 0.30, "signal_count": 0.20},
        "signal_cap": 3,
        "priority_map": {
            "CRITICAL": {"priority": "P1", "response_time": "1 hour",   "escalation_required": True},
            "HIGH":     {"priority": "P2", "response_time": "4 hours",  "escalation_required": True},
            "MEDIUM":   {"priority": "P3", "response_time": "24 hours", "escalation_required": False},
            "LOW":      {"priority": "P4", "response_time": "72 hours", "escalation_required": False},
        },
        "sla_status_thresholds": {"BREACHED": 80, "AT_RISK": 60, "ELEVATED": 30, "NORMAL": 0},
        "recommendations": {
            "LOW":      {"action": "Continue Normal Monitoring",  "text": "No immediate SLA intervention required."},
            "MEDIUM":   {"action": "Prioritized Review",          "text": "Review and prioritize unresolved anomalies."},
            "HIGH":     {"action": "Immediate Prioritization",    "text": "Prioritize records to avoid SLA breach."},
            "CRITICAL": {"action": "Escalation Required",         "text": "Escalate immediately. Allocate additional resources."},
        },
    }


_CFG = _load_config()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def apply_sla(record: StandardAnomalyRecord) -> StandardAnomalyRecord:
    """Calculate and attach SLA info to a StandardAnomalyRecord (in-place)."""
    try:
        record.sla = _calculate_sla(record)
        if record.processing_status == "adapted":
            record.processing_status = "sla_done"
    except Exception as exc:
        logger.exception("SLA engine error for record %s", record.record_id)
        record.processing_errors.append(f"SLAEngine: {exc}")
    return record


# ─────────────────────────────────────────────────────────────────────────────
# Internal calculation
# ─────────────────────────────────────────────────────────────────────────────

def _calculate_sla(record: StandardAnomalyRecord) -> SLABlock:
    is_anomaly   = record.anomaly.is_anomaly
    severity     = record.anomaly.severity.upper()
    signal_count = record.anomaly.signal_count

    if not is_anomaly:
        return SLABlock(
            risk_score=0.0, risk_level="LOW", priority="P4", status="NORMAL",
            response_time="72 hours", escalation_required=False,
            action="Continue Normal Monitoring",
            recommendation="No anomaly detected. Routine monitoring sufficient.",
        )

    weights     = _CFG.get("record_scoring_weights", {})
    sev_weights = _CFG.get("severity_weights", {})
    signal_cap  = int(_CFG.get("signal_cap", 3))

    w_anomaly  = float(weights.get("anomaly_existence", 0.50))
    w_severity = float(weights.get("severity",          0.30))
    w_signal   = float(weights.get("signal_count",      0.20))

    max_weight            = max(sev_weights.values()) or 4
    sev_weight            = sev_weights.get(severity, 0)
    severity_contribution = (sev_weight / max_weight) * 100.0
    signal_contribution   = (min(signal_count, signal_cap) / signal_cap) * 100.0

    raw_score  = w_anomaly * 100.0 + w_severity * severity_contribution + w_signal * signal_contribution
    risk_score = round(max(0.0, min(raw_score, 100.0)), 2)
    risk_level = _get_risk_level(risk_score)

    priority_info = _CFG.get("priority_map", {}).get(risk_level, {})
    priority      = priority_info.get("priority", "P4")
    response_time = priority_info.get("response_time", "72 hours")
    escalation    = bool(priority_info.get("escalation_required", False))
    sla_status    = _get_sla_status(risk_score)

    rec_cfg  = _CFG.get("recommendations", {}).get(risk_level, {})
    action   = rec_cfg.get("action", "Continue Normal Monitoring")
    rec_text = rec_cfg.get("text",   "Review the flagged record.")

    return SLABlock(
        risk_score=risk_score, risk_level=risk_level, priority=priority,
        status=sla_status, response_time=response_time,
        escalation_required=escalation, action=action, recommendation=rec_text,
    )


def _get_risk_level(score: float) -> str:
    thresholds = _CFG.get("risk_level_thresholds", {})
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        t = thresholds.get(level, {})
        if score >= float(t.get("min", 0)):
            return level
    return "LOW"


def _get_sla_status(score: float) -> str:
    t = _CFG.get("sla_status_thresholds", {})
    if score >= float(t.get("BREACHED", 80)): return "BREACHED"
    if score >= float(t.get("AT_RISK",  60)): return "AT_RISK"
    if score >= float(t.get("ELEVATED", 30)): return "ELEVATED"
    return "NORMAL"
