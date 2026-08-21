"""
ML Router — Multi-Dataset Anomaly Detection
============================================
Exposes anomaly detection pipelines for Authorization, Claims, and Pharmacy via REST API.

Endpoints:
  GET  /ml/health                — Check pipeline status & active tiers across all datasets
  POST /ml/predict               — Score a single record (Authorization, Claims, Pharmacy)
  POST /ml/predict/batch         — Score multiple records
  POST /ml/analyze-and-store     — Score + auto-persist Anomaly DB record if flagged + WebSocket broadcast
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.anomaly import Anomaly
from app.models.user import User
from app.realtime.manager import anomaly_manager
from app.schemas.anomaly import AnomalyResponse
from app.services import ml_service
from app.utils.enums import AnomalyStatus, AnomalyType, AnomalySeverity, SourceDataset

router = APIRouter(prefix="/ml", tags=["ML"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RuleViolation(BaseModel):
    anomaly:       bool
    rule_count:    int
    rule_names:    list[str]
    rule_reasons:  list[str]
    rule_severity: str


class BayesianResult(BaseModel):
    anomaly:        bool
    probability:    float


class MLEvidence(BaseModel):
    evidence_count: int
    severity:       str
    types:          str
    summary:        str


class GenericRecordRequest(BaseModel):
    model_config = {"extra": "allow"}
    source_type: Optional[str] = "AUTHORIZATION"
    record_id:   Optional[str] = None


class PredictionResult(BaseModel):
    authorization_id:    Optional[str] = None
    record_id:           Optional[str] = None
    source_type:         str           = "AUTHORIZATION"
    is_anomaly:          bool
    anomaly_score:       float
    severity:            str
    risk_score:          int
    signals:             str
    signal_count:        int
    rule_engine:         RuleViolation
    bayesian:            BayesianResult
    ml_evidence:         MLEvidence
    model:               str


class BatchPredictionResponse(BaseModel):
    total:     int
    anomalies: int
    results:   list[PredictionResult]


class AnalyzeAndStoreRequest(BaseModel):
    model_config = {"extra": "allow"}
    source_type: Optional[str] = "AUTHORIZATION"
    record:      Dict[str, Any]
    auto_store:  bool = True


# ── Helpers ───────────────────────────────────────────────────────────────────

_SEVERITY_MAP = {
    "CRITICAL": AnomalySeverity.CRITICAL,
    "HIGH":     AnomalySeverity.HIGH,
    "MEDIUM":   AnomalySeverity.MEDIUM,
    "LOW":      AnomalySeverity.LOW,
}

_RULE_TO_ANOMALY_TYPE: dict[str, AnomalyType] = {
    "MISSING_DATA":                    AnomalyType.MISSING_FIELD,
    "INVALID_DATE":                    AnomalyType.INVALID_DOMAIN,
    "FUTURE_REQUEST":                  AnomalyType.INVALID_DOMAIN,
    "APPROVAL_BEFORE_REQUEST":         AnomalyType.INVALID_DOMAIN,
    "INVALID_VALIDITY_RANGE":          AnomalyType.INVALID_DOMAIN,
    "NEGATIVE_QUANTITY":               AnomalyType.NEGATIVE_VALUE,
    "NEGATIVE_AMOUNT":                 AnomalyType.NEGATIVE_VALUE,
    "NEGATIVE_TOTAL_CLAIMS":           AnomalyType.NEGATIVE_VALUE,
    "NEGATIVE_TOTAL_FILLS":            AnomalyType.NEGATIVE_VALUE,
    "NEGATIVE_DRUG_COST":              AnomalyType.NEGATIVE_VALUE,
    "NEGATIVE_DAY_SUPPLY":             AnomalyType.NEGATIVE_VALUE,
    "DENIALS_EXCEED_RECEIVED_OON":     AnomalyType.INVALID_DOMAIN,
    "DENIALS_EXCEED_RECEIVED_INN":     AnomalyType.INVALID_DOMAIN,
    "OVERTURNED_EXCEEDS_FILED_APPEALS": AnomalyType.INVALID_DOMAIN,
    "UNUSUAL_QUANTITY":                AnomalyType.SLA_PROCESSING_SPIKE,
    "UNUSUAL_AMOUNT":                  AnomalyType.SLA_PROCESSING_SPIKE,
    "EXTREME_COST_PER_CLAIM":          AnomalyType.SLA_PROCESSING_SPIKE,
    "DUPLICATE_RECORD":                AnomalyType.DUPLICATE_RECORD,
}


def _map_anomaly_type(rule_names: list[str]) -> AnomalyType:
    for name in rule_names:
        mapped = _RULE_TO_ANOMALY_TYPE.get(name.upper())
        if mapped:
            return mapped
    return AnomalyType.INVALID_DOMAIN


def _to_prediction_result(rec_id: Optional[str], source_type: str, res: dict[str, Any]) -> PredictionResult:
    return PredictionResult(
        authorization_id = rec_id,
        record_id        = rec_id or res.get("record_id"),
        source_type      = source_type,
        is_anomaly       = res["is_anomaly"],
        anomaly_score    = res["anomaly_score"],
        severity         = res["severity"],
        risk_score       = res["risk_score"],
        signals          = res["signals"],
        signal_count     = res["signal_count"],
        rule_engine      = RuleViolation(
            anomaly       = res["rule_engine"]["anomaly"],
            rule_count    = res["rule_engine"]["rule_count"],
            rule_names    = res["rule_engine"]["rule_names"],
            rule_reasons  = res["rule_engine"]["rule_reasons"],
            rule_severity = res["rule_engine"]["rule_severity"],
        ),
        bayesian         = BayesianResult(
            anomaly     = res["bayesian"]["anomaly"],
            probability = res["bayesian"]["probability"],
        ),
        ml_evidence      = MLEvidence(
            evidence_count = res["ml_evidence"].get("evidence_count", 0),
            severity       = res["ml_evidence"].get("severity", ""),
            types          = res["ml_evidence"].get("types", ""),
            summary        = res["ml_evidence"].get("summary", ""),
        ),
        model            = res["model"],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health")
def ml_health():
    """Returns full pipeline load status across all datasets and detection tiers."""
    return ml_service.get_model_info()


@router.post("/predict", response_model=PredictionResult)
def predict_single(
    record: Dict[str, Any],
    source_type: Optional[str] = Query("AUTHORIZATION", description="AUTHORIZATION | CLAIMS | PHARMACY"),
):
    """Score a single record using the appropriate dataset ML pipeline."""
    src = record.get("source_type", source_type).upper().strip()
    if not ml_service.is_available(src):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{src} ML pipeline not available: {ml_service.get_load_error(src)}",
        )
    res = ml_service.predict(record, source_type=src)
    rec_id = str(record.get("record_id") or record.get("authorization_id") or record.get("claim_id") or record.get("prescription_id") or "ROW")
    return _to_prediction_result(rec_id, src, res)


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(
    records: List[Dict[str, Any]],
    source_type: Optional[str] = Query("AUTHORIZATION", description="AUTHORIZATION | CLAIMS | PHARMACY"),
):
    """Score multiple records across Authorization, Claims, or Pharmacy."""
    src = (source_type or "AUTHORIZATION").upper().strip()
    if not ml_service.is_available(src):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{src} ML pipeline not available: {ml_service.get_load_error(src)}",
        )

    results = ml_service.predict_batch(records, source_type=src)
    preds = []
    for i, r in enumerate(results):
        rec_id = str(records[i].get("record_id") or records[i].get("authorization_id") or records[i].get("claim_id") or records[i].get("prescription_id") or f"ROW_{i}")
        preds.append(_to_prediction_result(rec_id, src, r))

    return BatchPredictionResponse(
        total     = len(preds),
        anomalies = sum(1 for p in preds if p.is_anomaly),
        results   = preds,
    )


@router.post(
    "/analyze-and-store",
    response_model=AnomalyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_and_store(
    payload: AnalyzeAndStoreRequest,
    db: Session = Depends(get_db),
):
    """
    Run anomaly scoring on a record. If anomalous AND auto_store=True,
    persists it to the anomalies table and broadcasts via WebSocket.
    """
    src = (payload.source_type or "AUTHORIZATION").upper().strip()
    if not ml_service.is_available(src):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{src} ML pipeline not available: {ml_service.get_load_error(src)}",
        )

    res = ml_service.predict(payload.record, source_type=src)

    rec_id = str(payload.record.get("record_id") or payload.record.get("authorization_id") or payload.record.get("claim_id") or payload.record.get("prescription_id") or "UNKNOWN")

    if not res["is_anomaly"]:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message":          "Record is NORMAL — no anomaly detected.",
                "anomaly_score":    res["anomaly_score"],
                "risk_score":       res["risk_score"],
                "signals":          res["signals"],
                "model":            res["model"],
            },
        )

    if not payload.auto_store:
        pred = _to_prediction_result(rec_id, src, res)
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message":    "Anomaly detected (auto_store=False, not persisted).",
                "prediction": pred.model_dump(),
            },
        )

    rule_names   = res["rule_engine"]["rule_names"]
    rule_reasons = res["rule_engine"]["rule_reasons"]
    if rule_names:
        error_msg = "Rule violations: " + "; ".join(rule_names[:3])
        if rule_reasons:
            error_msg += " | " + rule_reasons[0]
    elif res["ml_evidence"]["evidence_count"] > 0:
        error_msg = f"ML model flagged multivariate anomaly: {res['ml_evidence'].get('summary', 'Density deviation')}"
    else:
        error_msg = f"Anomaly score: {res['anomaly_score']:.2f} flagged by {res['model']}"

    affected_field = rule_names[0] if rule_names else "multiple_fields"

    dataset_enum = SourceDataset.AUTHORIZATION
    if src in ("CLAIMS", "CLAIM"):
        dataset_enum = SourceDataset.CLAIMS
    elif src in ("PHARMACY", "PHARM", "RX"):
        dataset_enum = SourceDataset.PHARMACY

    anomaly = Anomaly(
        source_dataset  = dataset_enum,
        record_id       = rec_id,
        anomaly_type    = _map_anomaly_type(rule_names),
        severity        = _SEVERITY_MAP.get(res["severity"], AnomalySeverity.MEDIUM),
        status          = AnomalyStatus.OPEN,
        affected_field  = affected_field[:255],
        error_message   = error_msg[:500],
        likely_cause    = (
            "; ".join(rule_reasons[:2]) if rule_reasons
            else f"{src} data quality anomaly detected by ML pipeline."
        )[:500],
        recommended_fix = f"Review the {src.lower()} record in the source system. Correct the identified violation and revalidate.",
        raw_record      = {
            "record_id":            rec_id,
            "risk_score":           res["risk_score"],
            "severity":             res["severity"],
            "signals":              res["signals"],
            "rule_count":           res["rule_engine"]["rule_count"],
            "rule_names":           res["rule_engine"]["rule_names"],
            "bayesian_probability": res["bayesian"]["probability"],
            "model":                res["model"],
        },
    )

    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)

    await anomaly_manager.broadcast_anomaly(
        AnomalyResponse.model_validate(anomaly).model_dump(mode="json")
    )

    return AnomalyResponse.model_validate(anomaly)
