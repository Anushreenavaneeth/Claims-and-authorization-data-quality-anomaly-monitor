from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogCreate, AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit-trail", tags=["Audit Trail"])


@router.get("", response_model=AuditLogListResponse)
def get_audit_trail(
    anomaly_id:     Optional[str] = Query(None, description="Filter by anomaly ID"),
    record_id:      Optional[str] = Query(None, description="Filter by record ID"),
    action:         Optional[str] = Query(None, description="Filter by action"),
    source_dataset: Optional[str] = Query(None, description="Filter by dataset"),
    performed_by:   Optional[str] = Query(None, description="Filter by user or agent"),
    search:         Optional[str] = Query(None, description="Search notes or field name"),
    page:           int           = Query(1, ge=1),
    page_size:      int           = Query(20, ge=1, le=100),
    db:             Session       = Depends(get_db),
    _:              User          = Depends(get_current_user),
):
    """Retrieve filtered, paginated audit trail logs for data steward history and monitoring."""
    q = db.query(AuditLog)

    if anomaly_id:
        q = q.filter(AuditLog.anomaly_id == anomaly_id)
    if record_id:
        q = q.filter(AuditLog.record_id.ilike(f"%{record_id}%"))
    if action:
        q = q.filter(AuditLog.action == action)
    if source_dataset:
        q = q.filter(AuditLog.source_dataset == source_dataset)
    if performed_by:
        q = q.filter(AuditLog.performed_by.ilike(f"%{performed_by}%"))
    if search:
        term = f"%{search}%"
        q = q.filter(
            AuditLog.notes.ilike(term)
            | AuditLog.field_name.ilike(term)
            | AuditLog.action.ilike(term)
            | AuditLog.record_id.ilike(term)
        )

    total = q.count()
    items = (
        q.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AuditLogResponse.model_validate(item) for item in items],
    )


@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
def create_audit_entry(
    payload: AuditLogCreate,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    """Manually or agentically log a data correction or change action."""
    entry = AuditLog(
        anomaly_id=payload.anomaly_id,
        record_id=payload.record_id,
        source_dataset=payload.source_dataset,
        action=payload.action,
        field_name=payload.field_name,
        old_value=payload.old_value,
        new_value=payload.new_value,
        performed_by=payload.performed_by or user.name,
        notes=payload.notes,
        metadata_json=payload.metadata_json,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return AuditLogResponse.model_validate(entry)
