"""
ML Anomaly Ingestion Script
============================
Reads the ML team's output CSV (tc_puf_explained.csv) and inserts
anomaly records into the database.

Usage:
    python ingest_ml_anomalies.py
    python ingest_ml_anomalies.py --file path/to/custom.csv
    python ingest_ml_anomalies.py --dry-run

Run after:
    1. alembic upgrade head
    2. ML team has produced: data/anomalies/tc_puf_explained.csv
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# Add backend/ to path so app imports work
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models.anomaly import Anomaly
from app.utils.enums import AnomalySeverity, AnomalyStatus, AnomalyType, SourceDataset

DEFAULT_CSV = Path(__file__).parent.parent / "ml" / "anomaly_detection" / "data" / "anomalies" / "tc_puf_explained.csv"


def map_severity(raw: str) -> AnomalySeverity:
    mapping = {
        "HIGH":     AnomalySeverity.HIGH,
        "MEDIUM":   AnomalySeverity.MEDIUM,
        "LOW":      AnomalySeverity.LOW,
        "CRITICAL": AnomalySeverity.CRITICAL,
        "NORMAL":   AnomalySeverity.LOW,
    }
    return mapping.get(str(raw).upper(), AnomalySeverity.MEDIUM)


def map_anomaly_type(anomaly_type_raw: str) -> AnomalyType:
    """Map ML anomaly_type column to our AnomalyType enum."""
    t = str(anomaly_type_raw).upper()
    if "RULE" in t and "ML" in t:
        return AnomalyType.INVALID_DOMAIN
    if "RULE" in t:
        return AnomalyType.NEGATIVE_VALUE
    if "ML" in t:
        return AnomalyType.SLA_PROCESSING_SPIKE
    return AnomalyType.MISSING_FIELD


def ingest(csv_path: Path, dry_run: bool = False) -> int:
    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}")
        print("Run the ML pipeline first: python ml/anomaly_detection/anomaly_explainer.py")
        return 0

    db = SessionLocal()
    inserted = 0
    skipped  = 0

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only ingest actual anomalies, skip NORMAL records
                if str(row.get("final_anomaly", "False")).lower() not in ("true", "1"):
                    skipped += 1
                    continue

                plan_id = str(row.get("Plan_ID", "UNKNOWN"))

                # Avoid duplicate ingestion on re-runs
                existing = db.query(Anomaly).filter(
                    Anomaly.record_id == plan_id,
                    Anomaly.source_dataset == SourceDataset.CLAIMS,
                ).first()
                if existing:
                    skipped += 1
                    continue

                # Build raw_record — include key numeric fields
                raw = {
                    k: row[k] for k in row
                    if k in (
                        "Plan_ID", "Issuer_Claims_Received_In_Network",
                        "Issuer_Claims_Denied_In_Network",
                        "Issuer_Claims_Resubmitted_In_Network",
                        "anomaly_type", "severity", "rule_name", "rule_reason",
                    )
                }

                anomaly = Anomaly(
                    source_dataset  = SourceDataset.CLAIMS,
                    record_id       = plan_id,
                    anomaly_type    = map_anomaly_type(row.get("anomaly_type", "")),
                    severity        = map_severity(row.get("severity", "")),
                    status          = AnomalyStatus.OPEN,
                    affected_field  = str(row.get("rule_name", "multiple_fields") or "multiple_fields"),
                    error_message   = str(row.get("explanation", "Anomaly detected"))[:500],
                    likely_cause    = str(row.get("likely_cause", ""))[:500] or None,
                    recommended_fix = str(row.get("recommended_fix", ""))[:500] or None,
                    raw_record      = raw,
                )

                if not dry_run:
                    db.add(anomaly)
                inserted += 1

        if not dry_run:
            db.commit()

    finally:
        db.close()

    print(f"{'[DRY RUN] ' if dry_run else ''}Ingested: {inserted}  |  Skipped: {skipped}")
    return inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest ML anomaly CSV into the database")
    parser.add_argument("--file",    default=str(DEFAULT_CSV), help="Path to ML output CSV")
    parser.add_argument("--dry-run", action="store_true", help="Parse without writing to DB")
    args = parser.parse_args()

    count = ingest(Path(args.file), dry_run=args.dry_run)
    print(f"Done. {'Would insert' if args.dry_run else 'Inserted'} {count} anomalies.")
