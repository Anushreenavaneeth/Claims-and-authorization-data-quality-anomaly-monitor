"""
DatasetVersion model
====================
Each time a dataset (Claims / Authorization / Pharmacy) is uploaded,
a new version row is created.  The previous version is preserved;
only the latest has is_current=True.

This satisfies the versioning requirement:
  - Old data is never overwritten.
  - is_current flag identifies the latest version.
  - Full audit trail of every upload.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id           = Column(String(36), primary_key=True,
                          default=lambda: str(uuid.uuid4()))
    dataset_type = Column(String(20), nullable=False, index=True)  # CLAIMS / AUTHORIZATION / PHARMACY
    version      = Column(Integer,    nullable=False, default=1)
    upload_time  = Column(DateTime(timezone=True), nullable=False,
                          default=lambda: datetime.now(timezone.utc))
    filename     = Column(String(255), nullable=True)
    source_file  = Column(Text,        nullable=True)
    record_count = Column(Integer,     nullable=True)
    valid_count  = Column(Integer,     nullable=True)
    anomaly_count= Column(Integer,     nullable=True)
    # pending | processing | complete | failed
    status       = Column(String(20),  nullable=False, default="pending")
    is_current   = Column(Boolean,     nullable=False, default=False, index=True)
    uploaded_by  = Column(String(36),  nullable=True)   # user id
    notes        = Column(Text,        nullable=True)
