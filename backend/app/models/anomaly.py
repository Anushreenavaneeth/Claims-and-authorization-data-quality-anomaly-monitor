import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.database import Base
from app.utils.enums import AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset

# Use JSONB on PostgreSQL, fall back to JSON for SQLite (tests)
_JSON = JSONB().with_variant(JSON(), "sqlite")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()), index=True)

    # Source info
    source_dataset = Column(String(20), nullable=False,
                            default=SourceDataset.CLAIMS)
    record_id      = Column(String(100), nullable=False, index=True)

    # Classification
    anomaly_type   = Column(String(50), nullable=False,
                            default=AnomalyType.MISSING_FIELD)
    severity       = Column(String(20), nullable=False,
                            default=AnomalySeverity.MEDIUM, index=True)
    status         = Column(String(20), nullable=False,
                            default=AnomalyStatus.OPEN, index=True)

    # Detail
    affected_field   = Column(String(255), nullable=False)
    error_message    = Column(Text, nullable=False)
    likely_cause     = Column(Text, nullable=True)
    recommended_fix  = Column(Text, nullable=True)

    # Raw failing record — JSONB on Postgres, JSON on SQLite (tests)
    raw_record = Column(_JSON, nullable=True)

    # Timestamps
    timestamp  = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)

    # Optional: which worker is handling it
    assigned_to = Column(String(36), nullable=True)
