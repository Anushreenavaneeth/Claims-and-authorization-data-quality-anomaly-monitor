from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime

class AuditLogCreate(BaseModel):
    anomaly_id: Optional[str] = None
    record_id: Optional[str] = None
    source_dataset: Optional[str] = None
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None

class AuditLogResponse(BaseModel):
    id: str
    anomaly_id: Optional[str] = None
    record_id: Optional[str] = None
    source_dataset: Optional[str] = None
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AuditLogResponse]

