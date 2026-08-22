"""
Actions Router
==============
An action is created ONLY when a review is approved.
Admin assigns the action to a worker; worker executes and resolves it.

POST   /actions                          — create action from approved review
GET    /actions                          — list actions
GET    /actions/{id}                     — get single action
PATCH  /actions/{id}/assign              — admin assigns to worker
PATCH  /actions/{id}/status              — worker updates progress
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin, require_worker
from app.models.action import Action
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/actions", tags=["Execute Actions"])


# ── Schemas ───────────────────────────────────────────────────────────────

class ActionCreate(BaseModel):
    review_id:   str
    action_type: str   # Fix Data | Reprocess | Escalate | Contact Team
    description: Optional[str] = None


class ActionResponse(BaseModel):
    id:               str
    review_id:        str
    anomaly_record_id: str
    dataset:          str
    action_type:      str
    description:      Optional[str]
    status:           str
    assigned_to:      Optional[str]
    assigned_by:      Optional[str]
    assigned_at:      Optional[datetime]
    started_at:       Optional[datetime]
    completed_at:     Optional[datetime]
    notes:            Optional[str]
    resolution_notes: Optional[str]
    created_at:       datetime
    updated_at:       datetime

    model_config = {"from_attributes": True}


class AssignRequest(BaseModel):
    worker_id: str


class StatusUpdateRequest(BaseModel):
    status:           str   # in_progress | completed | failed
    notes:            Optional[str] = None
    resolution_notes: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────

VALID_TRANSITIONS = {
    "created":     {"assigned", "in_progress"},
    "assigned":    {"in_progress"},
    "in_progress": {"completed", "failed"},
}


def _get_or_404(action_id: str, db: Session) -> Action:
    a = db.query(Action).filter(Action.id == action_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Action not found.")
    return a


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
def create_action(
    payload: ActionCreate,
    db:      Session = Depends(get_db),
    user:    User    = Depends(require_admin),
):
    """
    Create an action from an approved review.
    Only reviews with status='approved' can spawn actions.
    """
    review = db.query(Review).filter(Review.id == payload.review_id).first()
    if not review:
        raise HTTPException(404, "Review not found.")
    if review.status != "approved":
        raise HTTPException(400,
            f"Actions can only be created from approved reviews. "
            f"Current review status: '{review.status}'.")

    action = Action(
        id                = str(uuid.uuid4()),
        review_id         = payload.review_id,
        anomaly_record_id = review.anomaly_record_id,
        dataset           = review.dataset,
        action_type       = payload.action_type,
        description       = payload.description,
        status            = "created",
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


@router.get("", response_model=list[ActionResponse])
def list_actions(
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_to:   Optional[str] = Query(None),
    dataset:       Optional[str] = Query(None),
    page:          int           = Query(1, ge=1),
    page_size:     int           = Query(50, ge=1, le=200),
    db:            Session       = Depends(get_db),
    _:             User          = Depends(get_current_user),
):
    q = db.query(Action)
    if status_filter:
        q = q.filter(Action.status == status_filter)
    if assigned_to:
        q = q.filter(Action.assigned_to == assigned_to)
    if dataset:
        q = q.filter(Action.dataset == dataset)
    return (
        q.order_by(Action.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: str,
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    return _get_or_404(action_id, db)


@router.patch("/{action_id}/assign", response_model=ActionResponse)
def assign_action(
    action_id: str,
    payload:   AssignRequest,
    db:        Session = Depends(get_db),
    user:      User    = Depends(require_admin),
):
    """Admin assigns the action to a specific worker."""
    action = _get_or_404(action_id, db)

    # Verify the worker exists and is active
    worker = db.query(User).filter(
        User.id == payload.worker_id,
        User.is_active == True,          # noqa: E712
    ).first()
    if not worker:
        raise HTTPException(404, "Worker not found or is inactive.")

    action.assigned_to  = payload.worker_id
    action.assigned_by  = str(user.id)
    action.assigned_at  = datetime.now(timezone.utc)
    action.status       = "assigned"
    db.commit()
    db.refresh(action)
    return action


@router.patch("/{action_id}/status", response_model=ActionResponse)
def update_action_status(
    action_id: str,
    payload:   StatusUpdateRequest,
    db:        Session = Depends(get_db),
    user:      User    = Depends(get_current_user),   # admin OR worker
):
    """Worker updates the action progress status."""
    action = _get_or_404(action_id, db)

    allowed = VALID_TRANSITIONS.get(action.status, set())
    if payload.status not in allowed:
        raise HTTPException(400,
            f"Cannot transition from '{action.status}' to '{payload.status}'. "
            f"Allowed transitions: {allowed}")

    action.status = payload.status
    if payload.notes:
        action.notes = (action.notes or "") + f"\n[{datetime.now(timezone.utc).isoformat()}] {payload.notes}"
    if payload.resolution_notes:
        action.resolution_notes = payload.resolution_notes

    now = datetime.now(timezone.utc)
    if payload.status == "in_progress" and not action.started_at:
        action.started_at = now
    if payload.status in ("completed", "failed"):
        action.completed_at = now

    db.commit()
    db.refresh(action)
    return action
