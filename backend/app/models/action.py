"""
Action model
============
An action is created ONLY when a Review is approved.
It is a separate tracked entity — not the same as a recommendation.

Lifecycle:
  created → assigned → in_progress → completed | failed
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.types import JSON

from app.database import Base


class Action(Base):
    __tablename__ = "actions"

    id           = Column(String(36), primary_key=True,
                          default=lambda: str(uuid.uuid4()))
    review_id    = Column(String(36),  nullable=False, index=True)  # FK to reviews.id
    anomaly_record_id = Column(String(200), nullable=False, index=True)
    dataset      = Column(String(20),  nullable=False)

    action_type  = Column(String(50),  nullable=False)   # Fix Data / Reprocess / Escalate / Contact Team
    description  = Column(Text,        nullable=True)

    # Lifecycle
    status       = Column(String(20),  nullable=False, default="created", index=True)
    # created | assigned | in_progress | completed | failed

    assigned_to  = Column(String(36),  nullable=True, index=True)  # user id (worker)
    assigned_by  = Column(String(36),  nullable=True)              # user id (admin)
    assigned_at  = Column(DateTime(timezone=True), nullable=True)

    started_at   = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    notes        = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at   = Column(DateTime(timezone=True), nullable=False,
                          default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime(timezone=True), nullable=False,
                          default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
