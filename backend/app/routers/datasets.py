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
    # Authorization uses claims schema until auth-specific schema is added
    "AUTHORIZATION": _ETL_CONFIG / "claims_schema.json",
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

    # ── ML scoring for AUTHORIZATION records ─────────────────────────────
    anomalies_created = 0

    if source_type == "AUTHORIZATION" and ml_service.is_available() and len(valid_df) > 0:
        records = valid_df.to_dict(orient="records")

        for row in records:
            try:
                result = ml_service.predict({
                    "processing_time_hours":              _safe_float(row.get("processing_time_hours")),
                    "missing_document_count":             _safe_float(row.get("missing_document_count")),
                    "resubmission_count":                 _safe_float(row.get("resubmission_count")),
                    "authorization_to_service_days":      _safe_float(row.get("authorization_to_service_days")),
                    "provider_avg_processing_time":       _safe_float(row.get("provider_avg_processing_time")),
                    "provider_avg_resubmission":          _safe_float(row.get("provider_avg_resubmission")),
                    "provider_avg_missing_docs":          _safe_float(row.get("provider_avg_missing_docs")),
                    "processing_time_provider_deviation": _safe_float(row.get("processing_time_provider_deviation")),
                })
            except Exception:
                continue

            if not result["is_anomaly"]:
                continue

            top    = result["contributing_features"]
            field  = top[0]["feature"] if top else "multiple_fields"
            errmsg = (
                f"{field} is {top[0]['direction'].replace('_', ' ')} "
                f"(value={top[0]['value']}, deviation={top[0]['deviation_score']}σ)"
                if top else "Unusual authorization pattern"
            )

            anomaly = Anomaly(
                source_dataset  = SourceDataset.AUTHORIZATION,
                record_id       = str(row.get("authorization_id", f"ROW_{uuid.uuid4()[:6]}")),
                anomaly_type    = AnomalyType.SLA_PROCESSING_SPIKE,
                severity        = SEVERITY_MAP.get(result["severity"], AnomalySeverity.MEDIUM),
                status          = AnomalyStatus.OPEN,
                affected_field  = field,
                error_message   = errmsg,
                likely_cause    = "Provider behaviour deviates from peer baseline.",
                recommended_fix = "Review record against provider history.",
                raw_record      = {k: str(v) for k, v in row.items()},
            )
            db.add(anomaly)
            anomalies_created += 1

        if anomalies_created:
            db.commit()
            # Broadcast last anomaly (frontend will refetch count)
            db.refresh(anomaly)
            await anomaly_manager.broadcast_anomaly(
                AnomalyResponse.model_validate(anomaly).model_dump(mode="json")
            )

    # ── Rule-based anomalies for CLAIMS / PHARMACY invalid rows ──────────
    elif source_type in ("CLAIMS", "PHARMACY") and len(invalid_df) > 0:
        issue_map = {i["column"]: i["message"] for i in report["issues"] if "column" in i}

        for _, row in invalid_df.head(100).iterrows():  # cap at 100 per upload
            affected = next(
                (col for col in issue_map if col in row.index and str(row.get(col, "")).strip() == ""),
                "multiple_fields",
            )
            id_field = "claim_id" if source_type == "CLAIMS" else "prescription_id"
            record_id = str(row.get(id_field, f"ROW_{uuid.uuid4()[:6]}"))

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
