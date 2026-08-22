"""
Review model
============
A recommendation must be reviewed by a human before any action is executed.

Statuses:
  pending_review  — awaiting reviewer
  approved        — reviewer accepted the recommendation
  rejected        — reviewer rejected; must provide comment
  modified        — reviewer changed the recommendation text before approving
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.types import JSON

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id                      = Column(String(36), primary_key=True,
                                     default=lambda: str(uuid.uuid4()))
    anomaly_record_id       = Column(String(200), nullable=False, index=True)
    dataset                 = Column(String(20),  nullable=False)   # claims / authorization / pharmacy

    # Snapshot of the recommendation at review time
    recommendation_snapshot = Column(Text, nullable=True)

    # Review decision
    status           = Column(String(30), nullable=False,
                               default="pending_review", index=True)
    # pending_review | approved | rejected | modified

    reviewed_by      = Column(String(36),  nullable=True)   # user id
    review_comments  = Column(Text,        nullable=True)
    reviewed_at      = Column(DateTime(timezone=True), nullable=True)

    created_at       = Column(DateTime(timezone=True), nullable=False,
                               default=lambda: datetime.now(timezone.utc))
    updated_at       = Column(DateTime(timezone=True), nullable=False,
                               default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))
