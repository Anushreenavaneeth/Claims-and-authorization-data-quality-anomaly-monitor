import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.auth_service import hash_password
from app.utils.enums import UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateWorkerRequest(BaseModel):
    name: str
    email: EmailStr
    # pyrefly: ignore [invalid-annotation]
    phone_number: Optional[str] = None
    password: Optional[str] = None  # If empty, generates invite link/token for worker email


class WorkerCreatedResponse(BaseModel):
    worker: UserResponse
    invite_token: Optional[str] = None
    invite_url: Optional[str] = None
    email_dispatched: bool = True
    message: str


@router.get("/workers", response_model=list[UserResponse])
def list_workers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return all worker accounts."""
    workers = db.query(User).filter(User.role == UserRole.WORKER).order_by(User.created_at.desc()).all()
    # Populate has_password boolean
    results = []
    for w in workers:
        res = UserResponse.model_validate(w)
        res.has_password = bool(w.password_hash)
        results.append(res)
    return results


from app.services.email_service import (
    load_notification_settings,
    save_notification_settings,
    send_test_email,
    send_worker_invitation,
)


@router.post("/workers", response_model=WorkerCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_worker(
    payload: CreateWorkerRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Create a new worker account and dispatch SMTP email invitation / set password link. Admin only."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    invite_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    worker = User(
        name=payload.name,
        email=payload.email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password) if payload.password else None,
        role=UserRole.WORKER,
        is_active=True,
        is_archived=False,
        invite_token=invite_token if not payload.password else None,
        invite_token_expires_at=expires_at if not payload.password else None,
    )
    db.add(worker)

    # Log worker creation in Audit Trail
    audit_entry = AuditLog(
        action="WORKER_CREATED",
        field_name="worker_account",
        new_value=f"{payload.name} ({payload.email})",
        performed_by=admin.name,
        notes=f"Worker account created. Phone: {payload.phone_number or 'N/A'}.",
    )
    db.add(audit_entry)

    # Dispatch SMTP Email Invitation if not creating with explicit password
    email_dispatched = False
    dispatch_msg = "Account created without email invitation."
    if not payload.password:
        sent, msg = send_worker_invitation(payload.email, payload.name, invite_token)
        email_dispatched = sent
        dispatch_msg = msg

        # Log email notification to Audit Trail
        email_audit = AuditLog(
            action="EMAIL_NOTIFICATION_SENT",
            field_name="worker_invitation",
            new_value=payload.email,
            performed_by="System (SMTP)",
            notes=f"Dispatched worker invitation email to {payload.email} (Status: {'Delivered' if sent else 'Pending SMTP config'}).",
        )
        db.add(email_audit)

    db.commit()
    db.refresh(worker)

    invite_url = f"/set-password?token={invite_token}" if not payload.password else None

    user_resp = UserResponse.model_validate(worker)
    user_resp.has_password = bool(worker.password_hash)

    return WorkerCreatedResponse(
        worker=user_resp,
        invite_token=invite_token if not payload.password else None,
        invite_url=invite_url,
        email_dispatched=email_dispatched,
        message=f"Worker created successfully. {dispatch_msg}",
    )


@router.post("/workers/{worker_id}/resend-invite", response_model=WorkerCreatedResponse)
def resend_invite(
    worker_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Regenerate and re-dispatch an SMTP invitation email for a worker."""
    worker = db.query(User).filter(User.id == worker_id, User.role == UserRole.WORKER).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")

    invite_token = secrets.token_urlsafe(32)
    worker.invite_token = invite_token
    worker.invite_token_expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Dispatch SMTP Email
    sent, msg = send_worker_invitation(worker.email, worker.name, invite_token)

    audit_entry = AuditLog(
        action="EMAIL_NOTIFICATION_SENT",
        field_name="invite_resent",
        new_value=worker.email,
        performed_by=admin.name,
        notes=f"Resent credential setup invitation email to {worker.email} ({msg})",
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(worker)

    invite_url = f"/set-password?token={invite_token}"

    user_resp = UserResponse.model_validate(worker)
    user_resp.has_password = bool(worker.password_hash)

    return WorkerCreatedResponse(
        worker=user_resp,
        invite_token=invite_token,
        invite_url=invite_url,
        email_dispatched=sent,
        message=f"Invitation link dispatched to {worker.email}. {msg}",
    )



@router.patch("/workers/{worker_id}/suspend", response_model=UserResponse)
def suspend_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Suspend a worker account. Prevents login and task assignment while retaining record. Admin only."""
    worker = db.query(User).filter(
        User.id == worker_id,
        User.role == UserRole.WORKER,
    ).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    worker.is_active = False

    audit_entry = AuditLog(
        action="WORKER_SUSPENDED",
        field_name="is_active",
        old_value="True",
        new_value="False",
        performed_by=admin.name,
        notes=f"Suspended worker account {worker.name} ({worker.email}). Claims access paused.",
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(worker)
    res = UserResponse.model_validate(worker)
    res.has_password = bool(worker.password_hash)
    return res


@router.patch("/workers/{worker_id}/reactivate", response_model=UserResponse)
def reactivate_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Reactivate a suspended worker account. Admin only."""
    worker = db.query(User).filter(
        User.id == worker_id,
        User.role == UserRole.WORKER,
    ).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    worker.is_active = True

    audit_entry = AuditLog(
        action="WORKER_REACTIVATED",
        field_name="is_active",
        old_value="False",
        new_value="True",
        performed_by=admin.name,
        notes=f"Reactivated worker account {worker.name} ({worker.email}). Claims access restored.",
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(worker)
    res = UserResponse.model_validate(worker)
    res.has_password = bool(worker.password_hash)
    return res


@router.patch("/workers/{worker_id}/archive", response_model=UserResponse)
def archive_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Archive a worker account. Retains all historical records, assigned tasks, and audit logs for insurance compliance. Admin only."""
    worker = db.query(User).filter(
        User.id == worker_id,
        User.role == UserRole.WORKER,
    ).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    worker.is_archived = True
    worker.is_active = False

    audit_entry = AuditLog(
        action="WORKER_ARCHIVED",
        field_name="is_archived",
        old_value="False",
        new_value="True",
        performed_by=admin.name,
        notes=f"Archived worker {worker.name} ({worker.email}) with full insurance compliance record retention.",
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(worker)
    res = UserResponse.model_validate(worker)
    res.has_password = bool(worker.password_hash)
    return res


@router.patch("/workers/{worker_id}/restore", response_model=UserResponse)
def restore_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Restore an archived worker back to active state. Admin only."""
    worker = db.query(User).filter(
        User.id == worker_id,
        User.role == UserRole.WORKER,
    ).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    worker.is_archived = False
    worker.is_active = True

    audit_entry = AuditLog(
        action="WORKER_RESTORED",
        field_name="is_archived",
        old_value="True",
        new_value="False",
        performed_by=admin.name,
        notes=f"Restored archived worker {worker.name} ({worker.email}) back to active status.",
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(worker)
    res = UserResponse.model_validate(worker)
    res.has_password = bool(worker.password_hash)
    return res


@router.patch("/workers/{worker_id}/deactivate", response_model=UserResponse)
def deactivate_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Legacy alias for suspend."""
    return suspend_worker(worker_id=worker_id, db=db, admin=admin)


# --- Notification & SMTP Settings Endpoints -----------------------------------

class NotificationSettingsPayload(BaseModel):
    email_notifications_enabled: bool = True
    worker_invitations: bool = True
    critical_anomalies: bool = True
    sla_at_risk: bool = True
    sla_breached: bool = True
    pipeline_failures: bool = True
    worker_assignments: bool = True
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = ""
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = "notifications@healthdata-ops.internal"
    smtp_from_name: Optional[str] = "Healthcare DQ Monitor"
    smtp_use_tls: Optional[bool] = True
    admin_alert_email: Optional[str] = "admin@healthdata-ops.internal"


class TestEmailPayload(BaseModel):
    recipient_email: EmailStr
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_use_tls: Optional[bool] = None


@router.get("/notifications/settings")
def get_notification_settings(_: User = Depends(require_admin)):
    """Retrieve operational notification preferences and masked SMTP server settings."""
    cfg = load_notification_settings()
    # Mask password for security
    resp = dict(cfg)
    if resp.get("smtp_password"):
        resp["smtp_password_configured"] = True
        resp["smtp_password"] = "••••••••••••"
    else:
        resp["smtp_password_configured"] = False
        resp["smtp_password"] = ""
    return resp


@router.post("/notifications/settings")
def update_notification_settings(
    payload: NotificationSettingsPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Save operational notification preferences and SMTP credentials. Admin only."""
    current = load_notification_settings()
    update_data = payload.model_dump(exclude_unset=True)

    # Don't overwrite existing password if payload password is empty/masked
    if not update_data.get("smtp_password") or update_data.get("smtp_password") == "••••••••••••":
        update_data["smtp_password"] = current.get("smtp_password", "")

    saved = save_notification_settings(update_data)

    audit_entry = AuditLog(
        action="NOTIFICATION_SETTINGS_UPDATED",
        field_name="smtp_notification_config",
        performed_by=admin.name,
        notes=f"Updated operational notification preferences. Master toggle: {saved.get('email_notifications_enabled')}.",
    )
    db.add(audit_entry)
    db.commit()

    resp = dict(saved)
    resp["smtp_password"] = "••••••••••••" if resp.get("smtp_password") else ""
    resp["smtp_password_configured"] = bool(saved.get("smtp_password"))
    return resp


@router.post("/notifications/test-email")
def test_smtp_connection(
    payload: TestEmailPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Dispatches a test verification email to validate SMTP server and credentials."""
    current = load_notification_settings()
    test_cfg = dict(current)

    if payload.smtp_host:
        test_cfg["smtp_host"] = payload.smtp_host
    if payload.smtp_port:
        test_cfg["smtp_port"] = payload.smtp_port
    if payload.smtp_username:
        test_cfg["smtp_username"] = payload.smtp_username
    if payload.smtp_password and payload.smtp_password != "••••••••••••":
        test_cfg["smtp_password"] = payload.smtp_password
    if payload.smtp_from_email:
        test_cfg["smtp_from_email"] = payload.smtp_from_email
    if payload.smtp_from_name:
        test_cfg["smtp_from_name"] = payload.smtp_from_name
    if payload.smtp_use_tls is not None:
        test_cfg["smtp_use_tls"] = payload.smtp_use_tls

    sent, msg = send_test_email(payload.recipient_email, test_cfg=test_cfg)

    audit_entry = AuditLog(
        action="SMTP_TEST_EXECUTED",
        field_name="smtp_test_email",
        new_value=payload.recipient_email,
        performed_by=admin.name,
        notes=f"Test email executed to {payload.recipient_email}. Result: {msg}",
    )
    db.add(audit_entry)
    db.commit()

    return {
        "success": sent,
        "recipient": payload.recipient_email,
        "message": msg,
    }


# --- Demo endpoints -----------------------------------------------------------

@router.post("/demo/authorization", status_code=201)
def demo_authorization(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Generate mock Authorization data, run the ML pipeline, and return a summary."""
    import pandas as pd
    from app.services.ml_service import run_dataframe_inference

    mock_data = {
        "authorization_id": ["MOCK001", "MOCK002"],
        "patient_id": ["PAT001", "PAT002"],
        "provider_id": ["PRV001", "PRV002"],
        "request_date": ["2026-08-01", "2026-08-02"],
        "approval_date": ["2026-08-03", "2026-08-04"],
        "valid_from_date": ["2026-08-01", "2026-08-02"],
        "valid_to_date": ["2026-12-31", "2026-12-31"],
        "requested_quantity": [10, 5],
        "charged_amount": [200.0, 120.0],
        "approval_status": ["approved", "rejected"],
    }
    df = pd.DataFrame(mock_data)
    _, anomalies = run_dataframe_inference(df, source_type="AUTHORIZATION")
    created = len(anomalies) if anomalies is not None else 0
    return {"message": "Mock authorization data processed.", "anomalies_created": created}


# ------------------------------------------------------------------------------
