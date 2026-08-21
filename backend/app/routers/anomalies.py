from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session


from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.anomaly import Anomaly
from app.models.audit_log import AuditLog
from app.models.user import User
from app.realtime.manager import anomaly_manager
from app.schemas.anomaly import (
    AnomalyCreate,
    AnomalyFeedbackRequest,
    AnomalyFeedbackResponse,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyStatusUpdate,
    SLARiskResponse,
)
from app.services import rag_service
from app.services.email_service import (
    load_notification_settings,
    send_assignment_notification,
    send_critical_anomaly_alert,
    send_sla_breach_alert,
)
from app.services.sla_service import calculate_sla_risk
from app.utils.enums import AnomalySeverity, AnomalyStatus, SourceDataset

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])



# ── Smart fallback recommendation ─────────────────────────────────────────

_RULE_ACTIONS: dict[str, tuple[str, str]] = {
    "invalid_date_sequence":    (
        "Authorization date is after service date.",
        "Verify the authorization_date and service_date against the source system. "
        "Correct the date sequence so authorization_date precedes service_date, then revalidate and reprocess.",
    ),
    "missing_service_date":     (
        "Service date is missing from the authorization record.",
        "Locate the service date from the original authorization request or source system. "
        "Update the record and revalidate before processing.",
    ),
    "missing_procedure_code":   (
        "Procedure code is absent from the authorization record.",
        "Retrieve the procedure code from the provider or source system. "
        "Update the authorization record and revalidate.",
    ),
    "missing_member_id":        (
        "Member ID is missing — cannot link to a health plan member.",
        "Verify the member ID against the enrollment database. "
        "Update the record with the correct member ID and resubmit.",
    ),
    "invalid_member_id":        (
        "Member ID format is invalid or does not match known members.",
        "Cross-reference the member ID with the enrollment system. "
        "Correct the member ID or escalate to data steward if the member cannot be identified.",
    ),
    "invalid_provider_id":      (
        "Provider ID is invalid or not found in the provider network.",
        "Verify the provider NPI against the provider directory. "
        "Correct the provider ID or flag for provider credentialing review.",
    ),
    "future_authorization_date":(
        "Authorization date is set in the future, which is invalid.",
        "Correct the authorization date to reflect the actual submission date. Revalidate the record.",
    ),
    "future_service_date":      (
        "Service date is in the future — potential data entry error.",
        "Confirm the service date with the provider. If incorrect, update and revalidate.",
    ),
    "approved_high_missing_docs":(
        "Authorization was approved despite a high number of missing documents.",
        "Review the missing documentation requirements. Collect outstanding documents "
        "and attach them to the authorization record before final approval.",
    ),
    "duplicate_record":         (
        "This authorization record appears to be a duplicate of an existing record.",
        "Search for the original authorization record. Retain the valid record and "
        "remove or flag the duplicate. Confirm with the submitting provider.",
    ),
    "excessive_processing_time":(
        "Processing time exceeds acceptable thresholds — SLA breach risk.",
        "Escalate to the authorization team lead. Check for workflow bottlenecks "
        "or system delays and prioritize this record for immediate processing.",
    ),
}

_FEATURE_ACTIONS: dict[str, str] = {
    "processing_time_hours":              "Processing time is unusually high. Check for workflow delays or system issues.",
    "resubmission_count":                 "High resubmission count. Review prior rejection reasons and resolve the root cause.",
    "missing_document_count":             "High number of missing documents. Contact provider to collect outstanding documentation.",
    "provider_avg_processing_time":       "Provider's average processing time is abnormal. Review provider submission patterns.",
    "provider_avg_resubmission":          "Provider has an unusually high resubmission rate. Consider provider education outreach.",
    "processing_time_provider_deviation": "This record deviates significantly from the provider's normal processing time.",
    "authorization_to_service_days":      "Gap between authorization and service date is outside normal range. Verify dates.",
}


def _smart_fallback(anomaly: "Anomaly") -> dict[str, Any]:
    """
    Build an anomaly-specific recommendation from the raw_record JSON.
    Each anomaly has different rules/features so the text is unique.
    """
    raw      = anomaly.raw_record or {}
    rules    = raw.get("rules", [])
    features = raw.get("ml_features", [])
    severity = str(anomaly.severity)
    priority = "High" if severity in ("CRITICAL", "HIGH") else "Medium" if severity == "MEDIUM" else "Normal"

    # --- Root cause from rules ---
    root_cause_parts = []
    action_parts     = []

    for rule in rules:
        name = str(rule.get("rule_name", "")).lower()
        if name in _RULE_ACTIONS:
            cause, action = _RULE_ACTIONS[name]
            root_cause_parts.append(cause)
            action_parts.append(action)
        else:
            root_cause_parts.append(f"{name.replace('_', ' ').capitalize()} rule violation detected.")

    # --- Contributing ML features ---
    ml_parts = []
    for feat in features[:3]:
        fname = str(feat.get("feature", "")).lower()
        direction = feat.get("direction", "")
        deviation = feat.get("deviation_score", "")
        if fname in _FEATURE_ACTIONS:
            ml_parts.append(_FEATURE_ACTIONS[fname])
        elif fname:
            ml_parts.append(
                f"{fname.replace('_', ' ').capitalize()} is {direction.replace('_', ' ')} "
                f"(deviation: {deviation}σ)."
            )

    # Build final text
    if root_cause_parts:
        root_cause_text = " ".join(root_cause_parts)
    elif ml_parts:
        root_cause_text = ml_parts[0]
    else:
        root_cause_text = str(anomaly.likely_cause or "Data quality issue detected by ML pipeline.")

    if action_parts:
        employee_action = " ".join(action_parts[:2])  # top 2 specific actions
    elif ml_parts:
        employee_action = " ".join(ml_parts[:2])
    else:
        employee_action = str(anomaly.recommended_fix or "Review the record against the source system.")

    context = raw.get("context", {})
    service_type = context.get("service_type", "")
    sla          = raw.get("sla", "")

    admin_summary = (
        f"{severity.capitalize()} {str(anomaly.anomaly_type).replace('_', ' ').lower()} "
        f"on authorization record {anomaly.record_id}"
        + (f" ({service_type})" if service_type else "")
        + f". {root_cause_text}"
        + (f" SLA: {sla}." if sla else "")
    )

    return {
        "record_id":       anomaly.id,
        "dataset_type":    str(anomaly.source_dataset),
        "severity":        severity,
        "priority":        priority,
        "anomaly":         str(anomaly.anomaly_type).replace("_", " ").title(),
        "explanation":     str(anomaly.error_message),
        "root_cause":      {"status": "likely", "cause": root_cause_text, "basis": [r.get("rule_name") for r in rules]},
        "admin_summary":   admin_summary,
        "employee_action": employee_action,
        "recommendation":  f"{root_cause_text} {employee_action}",
        "resolution":      {"procedure": employee_action},
        "rag_available":   False,
        "rag_error":       "RAG engine unavailable — Python 3.9 / TensorFlow incompatibility",
    }


# ── Aggregate Stats (dashboard) ───────────────────────────────────────────

@router.get("/stats")
def get_anomaly_stats(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Aggregate anomaly counts grouped by source_dataset, severity, and status.
    Used by the dashboard to render overview charts without N+1 queries.
    """
    total = db.query(func.count(Anomaly.id)).scalar() or 0

    by_source = {
        row[0]: row[1]
        for row in db.query(
            Anomaly.source_dataset, func.count(Anomaly.id)
        ).group_by(Anomaly.source_dataset).all()
    }

    by_severity = {
        row[0]: row[1]
        for row in db.query(
            Anomaly.severity, func.count(Anomaly.id)
        ).group_by(Anomaly.severity).all()
    }

    by_status = {
        row[0]: row[1]
        for row in db.query(
            Anomaly.status, func.count(Anomaly.id)
        ).group_by(Anomaly.status).all()
    }

    # Normalize enum keys to strings
    def _to_str_keys(d: dict) -> dict:
        return {(k.value if hasattr(k, "value") else str(k)): v for k, v in d.items()}

    return {
        "total": total,
        "by_source": _to_str_keys(by_source),
        "by_severity": _to_str_keys(by_severity),
        "by_status": _to_str_keys(by_status),
    }


# ── List anomalies with filters + pagination ──────────────────────────────

@router.get("", response_model=AnomalyListResponse)
def list_anomalies(
    source:    Optional[SourceDataset]   = Query(None),
    severity:  Optional[AnomalySeverity] = Query(None),
    status_:   Optional[AnomalyStatus]   = Query(None, alias="status"),
    search:    Optional[str]             = Query(None),
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
        raise HTTPException(status_code=404, detail="Anomaly not found.")
    return anomaly


# ── RAG recommendation ────────────────────────────────────────────────────

@router.get("/{anomaly_id}/recommend")
def get_recommendation(
    anomaly_id: str,
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Generate an AI recommendation for this anomaly using the RAG pipeline.
    Returns admin_summary, root_cause, resolution, employee_action, priority.
    Falls back gracefully if RAG is unavailable.
    """
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found.")

    if not rag_service.is_available():
        return _smart_fallback(anomaly)

    try:
        row = {
            "record_id":       anomaly.record_id or anomaly.id,
            "dataset_type":    str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
            "anomaly_type":    str(anomaly.anomaly_type.value if hasattr(anomaly.anomaly_type, "value") else anomaly.anomaly_type),
            "severity":        str(anomaly.severity.value if hasattr(anomaly.severity, "value") else anomaly.severity),
            "status":          str(anomaly.status.value if hasattr(anomaly.status, "value") else anomaly.status),
            "affected_field":  anomaly.affected_field or "",
            "error_message":   anomaly.error_message or "",
            "likely_cause":    anomaly.likely_cause or "",
            "recommended_fix": anomaly.recommended_fix or "",
            "raw_record":      anomaly.raw_record or {},
        }
        result = rag_service.get_recommendation(row)
        if result:
            result["rag_available"] = True
            return result
        return _smart_fallback(anomaly)
    except Exception as exc:
        fallback = _smart_fallback(anomaly)
        fallback["rag_error"] = str(exc)
        return fallback


# ── SLA Risk Assessment ───────────────────────────────────────────────────

@router.get("/{anomaly_id}/sla", response_model=SLARiskResponse)
def get_anomaly_sla_risk(
    anomaly_id: str,
    db:         Session = Depends(get_db),
    _:          User    = Depends(get_current_user),
):
    """
    Computes real-time operational SLA metrics and breach risk for an anomaly record.
    """
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found.")

    record_dict = {
        "severity": anomaly.severity.value if hasattr(anomaly.severity, "value") else str(anomaly.severity),
        "status": anomaly.status.value if hasattr(anomaly.status, "value") else str(anomaly.status),
        "anomaly_type": anomaly.anomaly_type.value if hasattr(anomaly.anomaly_type, "value") else str(anomaly.anomaly_type),
    }

    result = calculate_sla_risk(record_dict, created_at=anomaly.timestamp)
    return SLARiskResponse(**result)


# ── Bulk SLA Assessment ───────────────────────────────────────────────────

@router.post("/sla-bulk")
def get_bulk_sla_risk(
    anomaly_ids: List[str],
    db:          Session = Depends(get_db),
    _:           User    = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Batch SLA risk assessment for a list of anomaly IDs.
    Returns a map { anomaly_id: SLARiskResponse } for efficient frontend rendering.
    """
    results: dict[str, Any] = {}
    anomalies = (
        db.query(Anomaly)
        .filter(Anomaly.id.in_(anomaly_ids))
        .all()
    )
    for anomaly in anomalies:
        record_dict = {
            "severity":     anomaly.severity.value if hasattr(anomaly.severity, "value") else str(anomaly.severity),
            "status":       anomaly.status.value if hasattr(anomaly.status, "value") else str(anomaly.status),
            "anomaly_type": anomaly.anomaly_type.value if hasattr(anomaly.anomaly_type, "value") else str(anomaly.anomaly_type),
        }
        sla = calculate_sla_risk(record_dict, created_at=anomaly.timestamp)
        results[anomaly.id] = SLARiskResponse(**sla).model_dump()
    # Mark any requested IDs that weren't found
    for aid in anomaly_ids:
        if aid not in results:
            results[aid] = {"error": "not_found"}
    return {"sla_assessments": results, "count": len(anomalies)}


# ── Steward Feedback & Human-in-the-Loop Loop ─────────────────────────────

@router.post("/{anomaly_id}/feedback", response_model=AnomalyFeedbackResponse)
def submit_anomaly_feedback(
    anomaly_id: str,
    payload:    AnomalyFeedbackRequest,
    db:         Session = Depends(get_db),
    user:       User    = Depends(get_current_user),
):
    """
    Records data steward verdict, ratings, and corrections on AI-flagged anomalies.
    Saves feedback directly into the Audit Trail for future model retraining & RAG reinforcement.
    """
    from datetime import datetime, timezone

    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found.")

    action_norm = payload.action.upper().strip()

    # Automatically synchronize status if accepted or marked false positive
    if action_norm in ("ACCEPTED", "RESOLVED"):
        anomaly.status = AnomalyStatus.RESOLVED
    elif action_norm == "FALSE_POSITIVE":
        anomaly.status = AnomalyStatus.REJECTED

    audit_entry = AuditLog(
        anomaly_id=anomaly.id,
        record_id=anomaly.record_id,
        source_dataset=str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
        action=f"AI_FEEDBACK_{action_norm}",
        field_name="recommendation_feedback",
        new_value=f"Rating: {payload.rating}/5 | Action: {action_norm}",
        performed_by=user.name,
        notes=payload.notes or f"Steward {user.name} submitted AI feedback: {action_norm}",
        metadata_json={
            "feedback_action": action_norm,
            "rating": payload.rating,
            "corrected_fields": payload.corrected_fields,
            "notes": payload.notes,
        },
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(anomaly)

    return AnomalyFeedbackResponse(
        anomaly_id=anomaly.id,
        action=action_norm,
        rating=payload.rating,
        status=anomaly.status.value if hasattr(anomaly.status, "value") else str(anomaly.status),
        recorded_by=user.name,
        timestamp=datetime.now(timezone.utc),
    )



# ── Update status ─────────────────────────────────────────────────────────

@router.patch("/{anomaly_id}/status", response_model=AnomalyResponse)
async def update_anomaly_status(
    anomaly_id: str,
    payload:    AnomalyStatusUpdate,
    db:         Session = Depends(get_db),
    user:       User    = Depends(get_current_user),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found.")
    
    old_status = str(anomaly.status.value if hasattr(anomaly.status, "value") else anomaly.status)
    new_status = str(payload.status.value if hasattr(payload.status, "value") else payload.status)
    
    anomaly.status = payload.status

    audit_entry = AuditLog(
        anomaly_id=anomaly.id,
        record_id=anomaly.record_id,
        source_dataset=str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
        action=f"STATUS_UPDATE_{new_status.upper()}",
        field_name="status",
        old_value=old_status,
        new_value=new_status,
        performed_by=user.name,
        notes=f"Anomaly status changed from {old_status} to {new_status} by {user.name} ({user.role.value if hasattr(user.role, 'value') else user.role}).",
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(anomaly)
    await anomaly_manager.broadcast_status_change(anomaly_id, payload.status.value)
    return anomaly


# ── Assign anomaly to a worker ────────────────────────────────────────────

class AnomalyAssignRequest(BaseModel):
    worker_id: Optional[str] = None  # None = unassign
    worker_name: Optional[str] = None  # For display / audit


@router.patch("/{anomaly_id}/assign", response_model=AnomalyResponse)
def assign_anomaly_to_worker(
    anomaly_id: str,
    payload:    "AnomalyAssignRequest",
    db:         Session = Depends(get_db),
    admin:      User    = Depends(require_admin),
):
    """
    Assign (or unassign) an anomaly to a worker by worker_id.
    Stores the worker's UUID in anomaly.assigned_to and creates an AuditLog entry.
    Admin-only endpoint.
    """
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found.")

    # Validate worker exists if assigning
    worker_name_display = "Unassigned"
    if payload.worker_id:
        worker = db.query(User).filter(User.id == payload.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found.")
        worker_name_display = worker.name

    old_assigned = anomaly.assigned_to or "Unassigned"
    anomaly.assigned_to = payload.worker_id  # None = unassign

    # Also move status to IN_REVIEW if currently OPEN and assigning someone
    if payload.worker_id and str(anomaly.status) in ("OPEN", "open"):
        anomaly.status = AnomalyStatus.IN_REVIEW

    audit_entry = AuditLog(
        anomaly_id=anomaly.id,
        record_id=anomaly.record_id,
        source_dataset=str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
        action="ANOMALY_ASSIGNED" if payload.worker_id else "ANOMALY_UNASSIGNED",
        field_name="assigned_to",
        old_value=old_assigned,
        new_value=payload.worker_id or "Unassigned",
        performed_by=admin.name,
        notes=f"Anomaly {anomaly.record_id} assigned to worker '{worker_name_display}' by admin {admin.name}.",
    )
    db.add(audit_entry)

    # Dispatch SMTP Notification to assigned worker
    if payload.worker_id and worker and worker.email:
        anomaly_dict = {
            "record_id": anomaly.record_id,
            "source_dataset": str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
            "anomaly_type": str(anomaly.anomaly_type.value if hasattr(anomaly.anomaly_type, "value") else anomaly.anomaly_type),
            "severity": str(anomaly.severity.value if hasattr(anomaly.severity, "value") else anomaly.severity),
        }
        sent, msg = send_assignment_notification(worker.email, worker.name, anomaly_dict, assigned_by=admin.name)
        email_audit = AuditLog(
            anomaly_id=anomaly.id,
            record_id=anomaly.record_id,
            source_dataset=str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
            action="EMAIL_NOTIFICATION_SENT",
            field_name="worker_assignment",
            new_value=worker.email,
            performed_by="System (SMTP)",
            notes=f"Dispatched task assignment email to {worker.email} ({msg}).",
        )
        db.add(email_audit)

    db.commit()
    db.refresh(anomaly)
    return anomaly




# ── Trigger pipeline re-run ───────────────────────────────────────────────

@router.post("/{anomaly_id}/rerun")
def trigger_rerun(
    anomaly_id: str,
    db:         Session = Depends(get_db),
    admin:      User    = Depends(require_admin),
):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found.")
    
    audit_entry = AuditLog(
        anomaly_id=anomaly.id,
        record_id=anomaly.record_id,
        source_dataset=str(anomaly.source_dataset.value if hasattr(anomaly.source_dataset, "value") else anomaly.source_dataset),
        action="PIPELINE_RERUN_TRIGGERED",
        performed_by=admin.name,
        notes=f"Re-run verification triggered for anomaly {anomaly.record_id}",
    )
    db.add(audit_entry)
    db.commit()

    return {"message": f"Re-run triggered for anomaly {anomaly_id}", "anomaly_id": anomaly_id}


# ── Create anomaly (admin / ML ingestion) ─────────────────────────────────

@router.post("", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
async def create_anomaly(
    payload: AnomalyCreate,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(require_admin),
):
    anomaly = Anomaly(**payload.model_dump())
    db.add(anomaly)
    
    audit_entry = AuditLog(
        record_id=payload.record_id,
        source_dataset=str(payload.source_dataset.value if hasattr(payload.source_dataset, "value") else payload.source_dataset),
        action="ANOMALY_CREATED",
        field_name=payload.affected_field,
        performed_by=admin.name,
        notes=f"Manual anomaly registered: {payload.error_message}",
    )
    db.add(audit_entry)

    # Dispatch Critical Alert if severity is Critical or High
    severity_str = str(payload.severity.value if hasattr(payload.severity, "value") else payload.severity).upper()
    if severity_str in ("CRITICAL", "HIGH"):
        cfg = load_notification_settings()
        admin_email = cfg.get("admin_alert_email") or "admin@healthdata-ops.internal"
        sent, msg = send_critical_anomaly_alert(admin_email, payload.model_dump())
        email_audit = AuditLog(
            record_id=payload.record_id,
            source_dataset=str(payload.source_dataset.value if hasattr(payload.source_dataset, "value") else payload.source_dataset),
            action="EMAIL_NOTIFICATION_SENT",
            field_name="critical_anomaly_alert",
            new_value=admin_email,
            performed_by="System (SMTP)",
            notes=f"Critical anomaly alert email dispatched to {admin_email} ({msg}).",
        )
        db.add(email_audit)
    
    db.commit()
    db.refresh(anomaly)
    await anomaly_manager.broadcast_anomaly(
        AnomalyResponse.model_validate(anomaly).model_dump(mode="json")
    )
    return anomaly



# ── WebSocket ─────────────────────────────────────────────────────────────

@router.websocket("/ws")
async def anomaly_websocket(websocket: WebSocket):
    """
    WS events:
      { "type": "NEW_ANOMALY",    "data": AnomalyResponse }
      { "type": "STATUS_CHANGED", "data": { "id", "status" } }
      { "type": "CONNECTED",      "data": { "connections" } }
    """
    await anomaly_manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "CONNECTED",
            "data": {"connections": anomaly_manager.connection_count},
        })
        while True:
            msg = await websocket.receive_text()
            if msg == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        anomaly_manager.disconnect(websocket)
