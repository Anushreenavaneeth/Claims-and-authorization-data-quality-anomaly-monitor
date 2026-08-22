"""
Human Review Router
===================
A recommendation must go through human review before any action is executed.

POST   /reviews                    — create a review for an anomaly
GET    /reviews                    — list reviews (filterable)
GET    /reviews/{id}               — get single review
PATCH  /reviews/{id}/approve       — approve the recommendation
PATCH  /reviews/{id}/reject        — reject with mandatory comment
PATCH  /reviews/{id}/modify        — modify recommendation text, then approve
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
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["Human Review"])


# ── Schemas ───────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    anomaly_record_id:       str
    dataset:                 str
    recommendation_snapshot: Optional[str] = None


class ReviewResponse(BaseModel):
    id:                      str
    anomaly_record_id:       str
    dataset:                 str
    recommendation_snapshot: Optional[str]
    status:                  str
    reviewed_by:             Optional[str]
    review_comments:         Optional[str]
    reviewed_at:             Optional[datetime]
    created_at:              datetime
    updated_at:              datetime

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    comments: Optional[str] = None


class RejectRequest(BaseModel):
    comments: str   # mandatory for rejection


class ModifyRequest(BaseModel):
    modified_recommendation: str
    comments:                Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_or_404(review_id: str, db: Session) -> Review:
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found.")
    return r


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    db:      Session = Depends(get_db),
    user:    User    = Depends(require_admin),
):
    """Create a review entry for an anomaly recommendation."""
    review = Review(
        id                      = str(uuid.uuid4()),
        anomaly_record_id       = payload.anomaly_record_id,
        dataset                 = payload.dataset,
        recommendation_snapshot = payload.recommendation_snapshot,
        status                  = "pending_review",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("", response_model=list[ReviewResponse])
def list_reviews(
    status_filter: Optional[str] = Query(None, alias="status",
                                         description="pending_review | approved | rejected | modified"),
    dataset:       Optional[str] = Query(None),
    page:          int           = Query(1, ge=1),
    page_size:     int           = Query(50, ge=1, le=200),
    db:            Session       = Depends(get_db),
    _:             User          = Depends(get_current_user),
):
    q = db.query(Review)
    if status_filter:
        q = q.filter(Review.status == status_filter)
    if dataset:
        q = q.filter(Review.dataset == dataset)
    return (
        q.order_by(Review.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: str,
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_user),
):
    return _get_or_404(review_id, db)


@router.patch("/{review_id}/approve", response_model=ReviewResponse)
def approve_review(
    review_id: str,
    payload:   ApproveRequest,
    db:        Session = Depends(get_db),
    user:      User    = Depends(get_current_user),   # admin OR worker can approve
):
    """Approve a recommendation. Triggers action creation."""
    review = _get_or_404(review_id, db)
    if review.status not in ("pending_review", "modified"):
        raise HTTPException(400, f"Cannot approve a review with status '{review.status}'.")

    review.status          = "approved"
    review.reviewed_by     = str(user.id)
    review.review_comments = payload.comments
    review.reviewed_at     = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return review


@router.patch("/{review_id}/reject", response_model=ReviewResponse)
def reject_review(
    review_id: str,
    payload:   RejectRequest,
    db:        Session = Depends(get_db),
    user:      User    = Depends(get_current_user),   # admin OR worker
):
    """Reject a recommendation. Comment is mandatory."""
    review = _get_or_404(review_id, db)
    if review.status not in ("pending_review",):
        raise HTTPException(400, f"Cannot reject a review with status '{review.status}'.")
    if not payload.comments.strip():
        raise HTTPException(400, "Rejection requires a comment explaining the reason.")

    review.status          = "rejected"
    review.reviewed_by     = str(user.id)
    review.review_comments = payload.comments
    review.reviewed_at     = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return review


@router.patch("/{review_id}/modify", response_model=ReviewResponse)
def modify_review(
    review_id: str,
    payload:   ModifyRequest,
    db:        Session = Depends(get_db),
    user:      User    = Depends(get_current_user),   # admin OR worker
):
    """Modify the recommendation text, then mark as modified (pending re-approval)."""
    review = _get_or_404(review_id, db)
    if review.status not in ("pending_review",):
        raise HTTPException(400, f"Cannot modify a review with status '{review.status}'.")

    review.recommendation_snapshot = payload.modified_recommendation
    review.status                  = "modified"
    review.reviewed_by             = str(user.id)
    review.review_comments         = payload.comments
    review.reviewed_at             = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return review
