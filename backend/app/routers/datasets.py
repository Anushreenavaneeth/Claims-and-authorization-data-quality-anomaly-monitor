"""
Dataset Upload & Ingestion Router
==================================
POST /datasets/upload
  - Accepts a CSV file + source_type (CLAIMS | PHARMACY | AUTHORIZATION)
  - Runs ETL validation via data_ingestion/src/
  - If AUTHORIZATION source: runs ML scoring on valid records
  - Creates Anomaly DB records for flagged rows
  - Broadcasts new anomalies via WebSocket
  - Returns a validation report

GET /datasets
  - List past uploads (last 50)
"""
import csv
import io
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.anomaly import Anomaly
from app.models.audit_log import AuditLog
from app.models.user import User
from app.realtime.manager import anomaly_manager
from app.schemas.anomaly import AnomalyResponse
from app.services import ml_service
from app.utils.enums import AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset

# ── Path resolution ───────────────────────────────────────────────────────
_REPO_ROOT    = Path(__file__).resolve().parents[3]
_ETL_SRC      = _REPO_ROOT / "data_ingestion" / "src"
_ETL_CONFIG   = _REPO_ROOT / "data_ingestion" / "config"
_ETL_OUTPUT   = _REPO_ROOT / "data_ingestion" / "output"
_ETL_OUTPUT.mkdir(parents=True, exist_ok=True)

# Add ETL src to path so we can import loader / validator directly
if str(_ETL_SRC) not in sys.path:
    sys.path.insert(0, str(_ETL_SRC))

router = APIRouter(prefix="/datasets", tags=["Datasets"])

SCHEMA_MAP = {
    "CLAIMS":        _ETL_CONFIG / "claims_schema.json",
    "PHARMACY":      _ETL_CONFIG / "pharmacy_schema.json",
    "AUTHORIZATION": _ETL_CONFIG / "authorization_schema.json",
}

SEVERITY_MAP = {
    "CRITICAL": AnomalySeverity.CRITICAL,
    "HIGH":     AnomalySeverity.HIGH,
    "MEDIUM":   AnomalySeverity.MEDIUM,
    "LOW":      AnomalySeverity.LOW,
}

SOURCE_MAP = {
    "CLAIMS":        SourceDataset.CLAIMS,
    "PHARMACY":      SourceDataset.PHARMACY,
    "AUTHORIZATION": SourceDataset.AUTHORIZATION,
}


class ValidationReport(BaseModel):
    upload_id:       str
    filename:        str
    source_type:     str
    total_records:   int
    valid_records:   int
    invalid_records: int
    status:          str          # PASS | FAIL
    issues:          list[dict]
    anomalies_created: int
    timestamp:       str


@router.post("/upload", response_model=ValidationReport, status_code=status.HTTP_200_OK)
async def upload_dataset(
    file:        UploadFile = File(..., description="CSV file to ingest"),
    source_type: str        = Form(..., description="CLAIMS | PHARMACY | AUTHORIZATION"),
    db:          Session    = Depends(get_db),
    admin:       User       = Depends(require_admin),
):
    """
    Upload a CSV dataset, validate it, run ML scoring (for AUTHORIZATION),
    and create anomaly records for any flagged rows.
    """
    source_type = source_type.upper().strip()
    if source_type not in SCHEMA_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"source_type must be one of: {list(SCHEMA_MAP.keys())}",
        )

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only CSV files are accepted.")

    upload_id = str(uuid.uuid4())[:8]

    # ── Read uploaded file ────────────────────────────────────────────────
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # ── Save temporarily to disk for ETL module ──────────────────────────
    tmp_path = _ETL_OUTPUT / f"{upload_id}_{file.filename}"
    tmp_path.write_text(text, encoding="utf-8")

    # ── Run ETL validation ────────────────────────────────────────────────
    try:
        from loader import load_csv
        from validator import load_schema, validate_dataframe

        df           = load_csv(str(tmp_path))
        schema_path  = SCHEMA_MAP[source_type]
        schema       = load_schema(str(schema_path))
        valid_df, invalid_df, report = validate_dataframe(df, schema)
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"ETL module not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)   # clean up temp file

    # ── ML scoring for AUTHORIZATION records — full 3-tier pipeline ─────────
    anomalies_created = 0
    last_anomaly = None

    _RULE_TO_ANOMALY_TYPE: dict[str, AnomalyType] = {
        "MISSING_DATA":            AnomalyType.MISSING_FIELD,
        "INVALID_DATE":            AnomalyType.INVALID_DOMAIN,
        "FUTURE_REQUEST":          AnomalyType.INVALID_DOMAIN,
        "APPROVAL_BEFORE_REQUEST": AnomalyType.INVALID_DOMAIN,
        "INVALID_VALIDITY_RANGE":  AnomalyType.INVALID_DOMAIN,
        "NEGATIVE_QUANTITY":       AnomalyType.NEGATIVE_VALUE,
        "NEGATIVE_AMOUNT":         AnomalyType.NEGATIVE_VALUE,
        "UNUSUAL_QUANTITY":        AnomalyType.SLA_PROCESSING_SPIKE,
        "UNUSUAL_AMOUNT":          AnomalyType.SLA_PROCESSING_SPIKE,
        "DUPLICATE_RECORD":        AnomalyType.DUPLICATE_RECORD,
    }

    def _pick_anomaly_type(rule_names: list) -> AnomalyType:
        for name in rule_names:
            mapped = _RULE_TO_ANOMALY_TYPE.get(str(name).upper())
            if mapped:
                return mapped
        return AnomalyType.INVALID_DOMAIN

    if ml_service.is_available(source_type) and len(valid_df) > 0:
        try:
            _, all_results = ml_service.run_dataframe_inference(valid_df, source_type=source_type)
        except Exception as exc:
            all_results = []

        id_field_map = {
            "AUTHORIZATION": "authorization_id",
            "CLAIMS": "claim_id",
            "PHARMACY": "prescription_id",
        }
        id_field = id_field_map.get(source_type, "id")

        for row_idx, result in enumerate(all_results):
            if not result.get("is_anomaly", False):
                continue

            row = valid_df.iloc[row_idx].to_dict() if row_idx < len(valid_df) else {}

            rule_engine = result.get("rule_engine", {})
            rule_names   = rule_engine.get("rule_names", []) if isinstance(rule_engine, dict) else result.get("rule_names", [])
            rule_reasons = rule_engine.get("rule_reasons", []) if isinstance(rule_engine, dict) else result.get("rule_reasons", [])
            severity_str = result.get("severity", "MEDIUM")

            # Build human-readable error message
            if rule_names:
                error_msg = f"{source_type} rule violation: " + "; ".join(rule_names[:3])
                if rule_reasons:
                    error_msg += " | " + rule_reasons[0]
            elif result.get("ml_evidence", {}).get("evidence_count", 0) > 0:
                ml_ev     = result.get("ml_evidence", {})
                error_msg = f"ML model flagged {source_type} anomaly: {ml_ev.get('summary', 'Density deviation')}"
            else:
                prob      = result.get("bayesian", {}).get("probability", 0.0)
                error_msg = f"ML anomaly probability: {prob:.2%}"

            affected_field = rule_names[0] if rule_names else "multiple_fields"
            record_id      = str(row.get(id_field, row.get("record_id", f"{source_type}_{uuid.uuid4().hex[:6]}")))

            anomaly = Anomaly(
                source_dataset  = SOURCE_MAP.get(source_type, SourceDataset.AUTHORIZATION),
                record_id       = record_id,
                anomaly_type    = _pick_anomaly_type(rule_names),
                severity        = SEVERITY_MAP.get(severity_str, AnomalySeverity.MEDIUM),
                status          = AnomalyStatus.OPEN,
                affected_field  = affected_field[:255],
                error_message   = error_msg[:500],
                likely_cause    = (
                    "; ".join(rule_reasons[:2]) if rule_reasons
                    else f"{source_type} data quality anomaly detected by ML pipeline."
                )[:500],
                recommended_fix = f"Review the {source_type.lower()} record in the source system. Correct the identified violation and revalidate.",
                raw_record      = {
                    "record_id":            record_id,
                    "risk_score":           result.get("risk_score", 0),
                    "severity":             severity_str,
                    "signals":              result.get("signals", "None"),
                    "rule_count":           len(rule_names),
                    "rule_names":           rule_names,
                    "bayesian_probability": result.get("bayesian", {}).get("probability", 0.0),
                    "model":                result.get("model", f"{source_type}_Pipeline"),
                },
            )
            db.add(anomaly)
            anomalies_created += 1
            last_anomaly = anomaly

        if anomalies_created:
            db.commit()
            if last_anomaly:
                db.refresh(last_anomaly)
                await anomaly_manager.broadcast_anomaly(
                    AnomalyResponse.model_validate(last_anomaly).model_dump(mode="json")
                )

    # ── Rule-based anomalies for schema-invalid rows (all sources) ─────────
    if len(invalid_df) > 0:
        issue_map = {i["column"]: i["message"] for i in report.get("issues", []) if "column" in i}

        for _, row in invalid_df.head(100).iterrows():  # cap at 100 per upload
            affected = next(
                (col for col in issue_map if col in row.index and str(row.get(col, "")).strip() == ""),
                "multiple_fields",
            )
            id_field = "claim_id" if source_type == "CLAIMS" else ("prescription_id" if source_type == "PHARMACY" else "authorization_id")
            record_id = str(row.get(id_field, f"ROW_{uuid.uuid4().hex[:6]}"))

            anomaly = Anomaly(
                source_dataset  = SOURCE_MAP[source_type],
                record_id       = record_id,
                anomaly_type    = AnomalyType.MISSING_FIELD,
                severity        = AnomalySeverity.HIGH,
                status          = AnomalyStatus.OPEN,
                affected_field  = affected,
                error_message   = issue_map.get(affected, "Validation rule failed"),
                likely_cause    = "Data quality issue in source file.",
                recommended_fix = "Correct the field in the source system and re-upload.",
                raw_record      = {k: str(v) for k, v in row.items()},
            )
            db.add(anomaly)
            anomalies_created += 1

        if anomalies_created:
            db.commit()

    # Log ingestion action in Audit Trail
    audit_entry = AuditLog(
        action=f"DATASET_INGESTION_{source_type}",
        source_dataset=source_type,
        field_name="dataset_upload",
        new_value=file.filename,
        performed_by=admin.name,
        notes=f"Uploaded {file.filename} ({source_type}): {report['total_records']} total, {report['valid_records']} valid, {report['invalid_records']} invalid, {anomalies_created} anomalies flagged.",
        metadata_json={
            "upload_id": upload_id,
            "filename": file.filename,
            "source_type": source_type,
            "total_records": report["total_records"],
            "valid_records": report["valid_records"],
            "invalid_records": report["invalid_records"],
            "anomalies_created": anomalies_created,
        }
    )
    db.add(audit_entry)
    db.commit()

    return ValidationReport(
        upload_id       = upload_id,
        filename        = file.filename,
        source_type     = source_type,
        total_records   = report["total_records"],
        valid_records   = report["valid_records"],
        invalid_records = report["invalid_records"],
        status          = report["status"],
        issues          = report["issues"],
        anomalies_created = anomalies_created,
        timestamp       = datetime.now(timezone.utc).isoformat(),
    )


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None
