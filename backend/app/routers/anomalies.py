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
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.anomaly import Anomaly
from app.models.user import User
from app.realtime.manager import anomaly_manager
from app.schemas.anomaly import (
    AnomalyCreate,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyStatusUpdate,
)
from app.utils.enums import AnomalySeverity, AnomalyStatus, SourceDataset

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


# ── List anomalies with filters + pagination ──────────────────────────────

@router.get("", response_model=AnomalyListResponse)
def list_anomalies(
    source:    Optional[SourceDataset]   = Query(None),
    severity:  Optional[AnomalySeverity] = Query(None),
    status_:   Optional[AnomalyStatus]   = Query(None, alias="status"),
    search:    Optional[str]             = Query(None, description="Search record_id, anomaly_type, or affected_field"),
    page:      int                       = Query(1, ge=1),
    page_size: int                       = Query(20, ge=1, le=100),
    db:        Session                   = Depends(get_db),
    _:         User                      = Depends(get_current_user),
):
    q = db.query(Anomaly)

    if source:
        q = q.filter(Anomaly.source_dataset == source)
    if severity:
        q = q.filter(Anomaly.severity == severity)
    if status_:
        q = q.filter(Anomaly.status == status_)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Anomaly.record_id.ilike(term)
            | Anomaly.anomaly_type.ilike(term)
            | Anomaly.affected_field.ilike(term)
        )

    total = q.count()
    items = (
        q.order_by(Anomaly.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AnomalyListResponse(total=total, page=page, page_size=page_size, items=items)


# ── Single anomaly ────────────────────────────────────────────────────────

@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly(
    anomaly_id: str,
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")
    return anomaly


# ── Update status ─────────────────────────────────────────────────────────

@router.patch("/{anomaly_id}/status", response_model=AnomalyResponse)
async def update_anomaly_status(
    anomaly_id: str,
    payload:    AnomalyStatusUpdate,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")

    anomaly.status = payload.status
    db.commit()
    db.refresh(anomaly)

    # Broadcast status change to all WebSocket clients
    await anomaly_manager.broadcast_status_change(anomaly_id, payload.status.value)

    return anomaly


# ── Trigger pipeline re-run (stub — ETL team implements the actual logic) ─

@router.post("/{anomaly_id}/rerun")
def trigger_rerun(
    anomaly_id: str,
    db:         Session = Depends(get_db),
    _:          User    = Depends(require_admin),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")

    # ETL team hooks into this endpoint to trigger reprocessing
    return {"message": f"Re-run triggered for anomaly {anomaly_id}", "anomaly_id": anomaly_id}


# ── Admin: create anomaly manually (for testing / ML ingestion) ───────────

@router.post("", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
async def create_anomaly(
    payload: AnomalyCreate,
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_admin),
):
    anomaly = Anomaly(**payload.model_dump())
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    # Broadcast to WebSocket clients immediately
    await anomaly_manager.broadcast_anomaly(
        AnomalyResponse.model_validate(anomaly).model_dump(mode="json")
    )

    return anomaly


# ── WebSocket endpoint ────────────────────────────────────────────────────

@router.websocket("/ws")
async def anomaly_websocket(websocket: WebSocket):
    """
    Frontend connects here to receive real-time anomaly events.
    Message types emitted:
      { "type": "NEW_ANOMALY",    "data": AnomalyResponse }
      { "type": "STATUS_CHANGED", "data": { "id": str, "status": str } }
      { "type": "PING" }
    """
    await anomaly_manager.connect(websocket)
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "CONNECTED",
            "data": {"connections": anomaly_manager.connection_count},
        })
        while True:
            # Keep alive — client can send "PING" to check connection
            msg = await websocket.receive_text()
            if msg == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        anomaly_manager.disconnect(websocket)
