"""
ML Router
=========
Exposes the authorization anomaly detection model via REST API.

Endpoints:
  GET  /ml/health             — check if model is loaded
  POST /ml/predict            — score a single authorization record
  POST /ml/predict/batch      — score multiple records
  POST /ml/analyze-and-store  — predict + auto-create Anomaly DB record if flagged
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.anomaly import Anomaly
from app.models.user import User
from app.realtime.manager import anomaly_manager
from app.schemas.anomaly import AnomalyResponse
from app.services import ml_service
from app.utils.enums import AnomalyStatus, AnomalyType, SourceDataset

router = APIRouter(prefix="/ml", tags=["ML"])


# ── Schemas ───────────────────────────────────────────────────────────────

class AuthorizationRecord(BaseModel):
    """Input features for authorization anomaly scoring."""
    authorization_id:                   Optional[str]   = None
    processing_time_hours:              Optional[float] = None
    missing_document_count:             Optional[int]   = None
    resubmission_count:                 Optional[int]   = None
    authorization_to_service_days:      Optional[float] = None
    provider_avg_processing_time:       Optional[float] = None
    provider_avg_resubmission:          Optional[float] = None
    provider_avg_missing_docs:          Optional[float] = None
    processing_time_provider_deviation: Optional[float] = None
    # Extra context fields (not fed to model, used for DB storage)
    member_id:             Optional[str] = None
    provider_id:           Optional[str] = None
    service_type:          Optional[str] = None
    authorization_status:  Optional[str] = None


class PredictionResult(BaseModel):
    authorization_id: Optional[str]
    is_anomaly:       bool
    anomaly_score:    float
    severity:         str
    contributing_features: list[dict[str, Any]]
    model:            str


class BatchPredictionResponse(BaseModel):
    total:     int
    anomalies: int
    results:   list[PredictionResult]


class AnalyzeAndStoreRequest(BaseModel):
    record: AuthorizationRecord
    auto_store: bool = True   # if False, predict only without writing to DB


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.get("/health")
def ml_health(_: User = Depends(get_current_user)):
    """Returns model load status."""
    if ml_service.is_available():
        return {
            "status": "ready",
            "model": "IsolationForest_v1",
            "features": ml_service._feature_names,
        }
    return {
        "status": "unavailable",
        "error": ml_service.get_load_error(),
    }


@router.post("/predict", response_model=PredictionResult)
def predict_single(
    record: AuthorizationRecord,
    _: User = Depends(get_current_user),
):
    """Score a single authorization record."""
    if not ml_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML model not available: {ml_service.get_load_error()}",
        )
    result = ml_service.predict(record.model_dump(exclude={"member_id", "provider_id", "service_type", "authorization_status"}))
    return PredictionResult(authorization_id=record.authorization_id, **result)


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(
    records: list[AuthorizationRecord],
    _: User = Depends(get_current_user),
):
    """Score multiple authorization records at once."""
    if not ml_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML model not available: {ml_service.get_load_error()}",
        )
    exclude_keys = {"member_id", "provider_id", "service_type", "authorization_status"}
    results = []
    for rec in records:
        r = ml_service.predict(rec.model_dump(exclude=exclude_keys))
        results.append(PredictionResult(authorization_id=rec.authorization_id, **r))

    anomaly_count = sum(1 for r in results if r.is_anomaly)
    return BatchPredictionResponse(
        total=len(results),
        anomalies=anomaly_count,
        results=results,
    )


@router.post("/analyze-and-store", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
async def analyze_and_store(
    payload: AnalyzeAndStoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Score a record AND automatically create an Anomaly DB entry if flagged.
    Broadcasts via WebSocket so the frontend receives it in real time.
    """
    if not ml_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML model not available: {ml_service.get_load_error()}",
        )

    rec = payload.record
    exclude_keys = {"member_id", "provider_id", "service_type", "authorization_status"}
    result = ml_service.predict(rec.model_dump(exclude=exclude_keys))

    if not result["is_anomaly"]:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "Record is NORMAL — no anomaly detected.",
                "anomaly_score": result["anomaly_score"],
                "model": result["model"],
            },
        )

    # Build error message from top contributing feature
    top = result["contributing_features"]
    if top:
        f = top[0]
        error_msg = (
            f"{f['feature']} is {f['direction'].replace('_', ' ')} "
            f"(value={f['value']}, deviation={f['deviation_score']}σ)"
        )
    else:
        error_msg = "Unusual authorization pattern detected by Isolation Forest"

    likely_cause = (
        "Provider behaviour deviates from peer baseline. "
        "Possible causes: excessive resubmissions, abnormal processing time, "
        "missing documentation pattern."
    )
    recommended_fix = (
        "Review authorization record against provider history. "
        "Check for duplicate submissions, incomplete documentation, "
        "or SLA breach risk."
    )

    if not payload.auto_store:
        # Predict-only response — return a fake AnomalyResponse shape
        from datetime import datetime, timezone
        import uuid
        dummy = Anomaly(
            id=str(uuid.uuid4()),
            source_dataset=SourceDataset.AUTHORIZATION,
            record_id=rec.authorization_id or "UNKNOWN",
            anomaly_type=AnomalyType.SLA_PROCESSING_SPIKE,
            severity=result["severity"],
            status=AnomalyStatus.OPEN,
            affected_field=top[0]["feature"] if top else "unknown",
            error_message=error_msg,
            likely_cause=likely_cause,
            recommended_fix=recommended_fix,
            raw_record=rec.model_dump(),
            timestamp=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return dummy

    # Map severity
    from app.utils.enums import AnomalySeverity
    sev_map = {
        "CRITICAL": AnomalySeverity.CRITICAL,
        "HIGH":     AnomalySeverity.HIGH,
        "MEDIUM":   AnomalySeverity.MEDIUM,
        "LOW":      AnomalySeverity.LOW,
    }

    anomaly = Anomaly(
        source_dataset  = SourceDataset.AUTHORIZATION,
        record_id       = rec.authorization_id or "UNKNOWN",
        anomaly_type    = AnomalyType.SLA_PROCESSING_SPIKE,
        severity        = sev_map.get(result["severity"], AnomalySeverity.MEDIUM),
        status          = AnomalyStatus.OPEN,
        affected_field  = top[0]["feature"] if top else "multiple_fields",
        error_message   = error_msg,
        likely_cause    = likely_cause,
        recommended_fix = recommended_fix,
        raw_record      = {
            **rec.model_dump(exclude_none=True),
            "ml_score":    result["anomaly_score"],
            "ml_features": result["contributing_features"],
        },
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    # Real-time broadcast to frontend WebSocket clients
    await anomaly_manager.broadcast_anomaly(
        AnomalyResponse.model_validate(anomaly).model_dump(mode="json")
    )

    return anomaly
