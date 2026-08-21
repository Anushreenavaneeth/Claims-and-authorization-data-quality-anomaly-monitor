from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from app.utils.enums import AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset


class AnomalyResponse(BaseModel):
    id:              str
    source_dataset:  SourceDataset
    record_id:       str
    anomaly_type:    AnomalyType
    severity:        AnomalySeverity
    status:          AnomalyStatus
    affected_field:  str
    error_message:   str
    likely_cause:    Optional[str]
    recommended_fix: Optional[str]
    raw_record:      Optional[dict[str, Any]]
    timestamp:       datetime
    updated_at:      datetime
    assigned_to:     Optional[str]

    model_config = {"from_attributes": True}


class AnomalyStatusUpdate(BaseModel):
    status: AnomalyStatus


class AnomalyCreate(BaseModel):
    source_dataset:  SourceDataset
    record_id:       str
    anomaly_type:    AnomalyType
    severity:        AnomalySeverity
    affected_field:  str
    error_message:   str
    likely_cause:    Optional[str] = None
    recommended_fix: Optional[str] = None
    raw_record:      Optional[dict[str, Any]] = None


class AnomalyListResponse(BaseModel):
    total:     int
    page:      int
    page_size: int
    items:     list[AnomalyResponse]


class AnomalyFeedbackRequest(BaseModel):
    action:           str  # "ACCEPTED" | "REJECTED" | "MODIFIED" | "FALSE_POSITIVE"
    rating:           Optional[int] = 5  # 1-5 scale
    notes:            Optional[str] = None
    corrected_fields: Optional[dict[str, Any]] = None


class AnomalyFeedbackResponse(BaseModel):
    anomaly_id:  str
    action:      str
    rating:      Optional[int]
    status:      str
    recorded_by: str
    timestamp:   datetime


class SLARiskResponse(BaseModel):
    target_hours:       int
    deadline:           str
    elapsed_hours:      float
    remaining_hours:    float
    breach_probability: float
    sla_status:         str
    sla_risk_tier:      str
    sla_risk_score:     int
    recommendation:     str

