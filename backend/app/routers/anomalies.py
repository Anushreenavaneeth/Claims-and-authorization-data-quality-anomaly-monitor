"""
Anomaly recommendation endpoint.

GET /anomalies/{anomaly_id}/recommend

Flow:
    Browser → GET /anomalies/{id}/recommend  (this backend, port 8000)
            → rag_service.is_available()     checks http://localhost:8001/health
            → If online:  POST /recommend    full RAG pipeline (Charan's service)
            → If offline: smart fallback     anomaly-specific text from DB fields
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import require_admin, require_worker
from app.models.user import User
from app.services import rag_service

router = APIRouter(tags=["Anomalies"])

# ─────────────────────────────────────────────────────────────────────────────
# Load the anomaly dataset once at import time.
# Adjust this path if the JSON file moves.
# ─────────────────────────────────────────────────────────────────────────────

_DATA_FILE = Path(__file__).resolve().parents[4] / "authorization_anomalies_for_rag.json"

_ANOMALY_MAP: Dict[str, Dict[str, Any]] = {}

try:
    with open(_DATA_FILE, "r", encoding="utf-8") as _f:
        _records: List[Dict[str, Any]] = json.load(_f)
    _ANOMALY_MAP = {r["record_id"]: r for r in _records}
except Exception as _exc:  # noqa: BLE001
    # Non-fatal — fallback will still produce generic text
    print(f"WARNING: could not load anomaly dataset: {_exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Response schema
# ─────────────────────────────────────────────────────────────────────────────


class RecommendationResponse(BaseModel):
    anomaly_id: str
    dataset_type: str
    admin_summary: str
    root_cause: Dict[str, Any]
    employee_action: str
    priority: str
    rag_available: bool


# ─────────────────────────────────────────────────────────────────────────────
# Fallback helpers
# ─────────────────────────────────────────────────────────────────────────────


def _severity_to_priority(severity: str) -> str:
    mapping = {
        "critical": "Critical",
        "error": "High",
        "warning": "Medium",
        "info": "Low",
    }
    return mapping.get(severity.lower(), "Medium")


def _build_fallback(
    anomaly_id: str,
    record: Optional[Dict[str, Any]],
) -> RecommendationResponse:
    """
    Produce an anomaly-specific recommendation without the RAG service.
    Uses detection_summary and record_context fields from the stored record.
    """

    if record is None:
        return RecommendationResponse(
            anomaly_id=anomaly_id,
            dataset_type="unknown",
            admin_summary=(
                f"Anomaly {anomaly_id} was flagged by automated detection. "
                "RAG service is offline — manual review recommended."
            ),
            root_cause={"primary": "Undetermined (RAG service offline)"},
            employee_action=(
                "Review the record in the source system, correct any data-quality "
                "issues, and revalidate before reprocessing."
            ),
            priority="Medium",
            rag_available=False,
        )

    detection = record.get("detection_summary", {})
    context = record.get("record_context", {})
    dataset_type = record.get("dataset_type", "unknown")
    severity = str(detection.get("final_severity", "Warning"))
    risk_score: Optional[float] = detection.get("final_risk_score")
    sla = record.get("sla", "")

    # Rules that were violated
    rule_violations: List[str] = [
        e["rule_name"]
        for e in record.get("rule_based_evidence", [])
        if e.get("status") == "violated"
    ]

    # ML contributing features
    ml_features: List[str] = [
        f["feature"]
        for f in record.get("ml_based_evidence", {}).get("contributing_features", [])
    ]

    # ── admin summary ──────────────────────────────────────────────────────
    risk_text = f" (risk score {risk_score:.4f})" if risk_score is not None else ""
    admin_summary = (
        f"Anomaly {anomaly_id} detected with {severity} severity{risk_text}. "
    )
    if rule_violations:
        admin_summary += f"Rule violations: {', '.join(rule_violations)}. "
    if ml_features:
        admin_summary += f"ML flagged features: {', '.join(ml_features[:3])}. "
    if sla:
        admin_summary += f"SLA: {sla}."

    # ── root cause ─────────────────────────────────────────────────────────
    root_cause: Dict[str, Any] = {
        "primary": rule_violations[0].replace("_", " ").title() if rule_violations else "ML statistical anomaly",
        "rule_violations": rule_violations,
        "ml_contributing_features": ml_features,
    }

    # ── employee action ────────────────────────────────────────────────────
    if rule_violations:
        action = (
            f"Correct the rule violation(s): {', '.join(rule_violations).replace('_', ' ')}. "
            "Verify dates, document counts, and field values against the source system, "
            "then resubmit for processing."
        )
    elif ml_features:
        action = (
            f"Review the following flagged fields: {', '.join(ml_features[:3]).replace('_', ' ')}. "
            "Compare observed values against expected ranges and correct any data-entry errors."
        )
    else:
        action = (
            "Review the flagged record in the source system, correct identified "
            "data-quality issues, and revalidate before reprocessing."
        )

    priority = _severity_to_priority(severity)
    if risk_score is not None and risk_score >= 0.85:
        priority = "Critical"
    elif risk_score is not None and risk_score >= 0.75 and priority != "Critical":
        priority = "High"

    return RecommendationResponse(
        anomaly_id=anomaly_id,
        dataset_type=dataset_type,
        admin_summary=admin_summary,
        root_cause=root_cause,
        employee_action=action,
        priority=priority,
        rag_available=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/anomalies/{anomaly_id}/recommend",
    response_model=RecommendationResponse,
    summary="Get AI recommendation for an anomaly",
)
def get_recommendation(
    anomaly_id: str,
    current_user: User = Depends(require_worker),
):
    """
    Returns an AI-generated recommendation for the given anomaly.

    - If the RAG microservice (port 8001) is online: full RAG pipeline.
    - If offline: anomaly-specific fallback from stored detection fields.
    """

    record = _ANOMALY_MAP.get(anomaly_id)

    # ── try RAG service ────────────────────────────────────────────────────
    if rag_service.is_available():
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Anomaly '{anomaly_id}' not found in dataset.",
            )

        rag_result = rag_service.get_recommendation(record)

        if rag_result is not None:
            return RecommendationResponse(
                anomaly_id=rag_result.get("record_id", anomaly_id),
                dataset_type=rag_result.get("dataset_type", record.get("dataset_type", "unknown")),
                admin_summary=rag_result.get("admin_summary", ""),
                root_cause=rag_result.get("root_cause", {}),
                employee_action=rag_result.get("employee_action", ""),
                priority=rag_result.get("priority", "Medium"),
                rag_available=True,
            )

    # ── fallback ───────────────────────────────────────────────────────────
    return _build_fallback(anomaly_id, record)
