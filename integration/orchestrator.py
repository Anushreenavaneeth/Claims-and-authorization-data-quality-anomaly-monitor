"""
Integration Orchestrator
========================
Single entry point for the full end-to-end pipeline.

Usage:
    from integration.orchestrator import process_dataset, process_all

    results = process_dataset("claims")
    results = process_dataset("authorization")
    results = process_dataset("pharmacy")
    all_results = process_all()

Flow per record:
    Raw JSON record
        ↓ Dataset-specific adapter (Claims / Authorization / Pharmacy)
        ↓ Common Schema (StandardAnomalyRecord)
        ↓ Common SLA Engine
        ↓ RAG Connector
        ↓ Persist to SQLite
        ↓ Return final StandardAnomalyRecord

All three datasets use the SAME SLA engine and SAME RAG connector.
"""

from __future__ import annotations

# ── Path bootstrap (needed when run as a script) ──────────────────────────
# Ensures the project root is on sys.path so `from integration import ...`
# works whether this file is invoked as:
#   python integration/orchestrator.py   (script)
#   python -m integration.orchestrator   (module)
#   import integration.orchestrator      (library)
import sys as _sys
from pathlib import Path as _Path
_project_root = _Path(__file__).resolve().parent.parent
if str(_project_root) not in _sys.path:
    _sys.path.insert(0, str(_project_root))
# ──────────────────────────────────────────────────────────────────────────

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from integration import claims_adapter, authorization_adapter, pharmacy_adapter
from integration.sla_engine import apply_sla
from integration.rag_connector import apply_rag
from integration.common_schema import StandardAnomalyRecord, validate_standard_record

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Dataset JSON source file mapping
# ─────────────────────────────────────────────────────────────────────────────

_BASE = Path(__file__).resolve().parents[1]

_DATASET_SOURCES: Dict[str, Path] = {
    "claims":        _BASE / "sla risk" / "json files" / "claims.json",
    "authorization": _BASE / "authorization.json",
    "pharmacy":      _BASE / "anomaly_results.json",
}

_ADAPTERS = {
    "claims":        claims_adapter.adapt,
    "authorization": authorization_adapter.adapt,
    "pharmacy":      pharmacy_adapter.adapt,
}

# ─────────────────────────────────────────────────────────────────────────────
# SQLite persistence
# ─────────────────────────────────────────────────────────────────────────────

_DB_PATH = _BASE / "data" / "processed_results.db"


def _get_db() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_results (
            id              TEXT PRIMARY KEY,
            record_id       TEXT NOT NULL,
            dataset         TEXT NOT NULL,
            is_anomaly      INTEGER NOT NULL DEFAULT 0,
            severity        TEXT,
            risk_level      TEXT,
            risk_score      REAL,
            priority        TEXT,
            sla_status      TEXT,
            quality_score   REAL,
            processing_status TEXT,
            result_json     TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dataset   ON processed_results(dataset)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_severity  ON processed_results(severity)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_is_anomaly ON processed_results(is_anomaly)")
    conn.commit()
    conn.close()


def _upsert_result(record: StandardAnomalyRecord) -> None:
    conn = _get_db()
    now  = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO processed_results
            (id, record_id, dataset, is_anomaly, severity, risk_level,
             risk_score, priority, sla_status, quality_score,
             processing_status, result_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            is_anomaly        = excluded.is_anomaly,
            severity          = excluded.severity,
            risk_level        = excluded.risk_level,
            risk_score        = excluded.risk_score,
            priority          = excluded.priority,
            sla_status        = excluded.sla_status,
            quality_score     = excluded.quality_score,
            processing_status = excluded.processing_status,
            result_json       = excluded.result_json,
            updated_at        = excluded.updated_at
    """, (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, record.record_id)),
        record.record_id,
        record.dataset,
        1 if record.anomaly.is_anomaly else 0,
        record.anomaly.severity,
        record.sla.risk_level,
        record.sla.risk_score,
        record.sla.priority,
        record.sla.status,
        record.quality.quality_score,
        record.processing_status,
        json.dumps(record.to_dict(), ensure_ascii=False),
        now,
        now,
    ))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers (used by the API)
# ─────────────────────────────────────────────────────────────────────────────

def query_results(
    dataset:    Optional[str] = None,
    severity:   Optional[str] = None,
    sla_status: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    search:     Optional[str] = None,
    page:       int = 1,
    page_size:  int = 50,
) -> Dict[str, Any]:
    """Return paginated query results from the processed_results table."""
    conn  = _get_db()
    where = []
    args: list[Any] = []

    if dataset:
        where.append("dataset = ?")
        args.append(dataset.lower())
    if severity:
        where.append("severity = ?")
        args.append(severity.upper())
    if sla_status:
        where.append("sla_status = ?")
        args.append(sla_status.upper())
    if is_anomaly is not None:
        where.append("is_anomaly = ?")
        args.append(1 if is_anomaly else 0)
    if search:
        where.append("record_id LIKE ?")
        args.append(f"%{search}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total_row = conn.execute(
        f"SELECT COUNT(*) FROM processed_results {where_sql}", args
    ).fetchone()
    total = total_row[0] if total_row else 0

    offset = (page - 1) * page_size
    rows   = conn.execute(
        f"SELECT * FROM processed_results {where_sql} "
        f"ORDER BY risk_score DESC, created_at DESC "
        f"LIMIT ? OFFSET ?",
        args + [page_size, offset],
    ).fetchall()
    conn.close()

    items = [json.loads(r["result_json"]) for r in rows]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_result_by_record_id(record_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_db()
    row  = conn.execute(
        "SELECT result_json FROM processed_results WHERE record_id = ?",
        (record_id,),
    ).fetchone()
    conn.close()
    return json.loads(row["result_json"]) if row else None


def get_dashboard_summary() -> Dict[str, Any]:
    """Aggregate statistics for the dashboard overview."""
    conn = _get_db()

    total       = conn.execute("SELECT COUNT(*) FROM processed_results").fetchone()[0]
    total_anom  = conn.execute("SELECT COUNT(*) FROM processed_results WHERE is_anomaly=1").fetchone()[0]
    critical    = conn.execute("SELECT COUNT(*) FROM processed_results WHERE severity='CRITICAL' AND is_anomaly=1").fetchone()[0]
    high        = conn.execute("SELECT COUNT(*) FROM processed_results WHERE severity='HIGH' AND is_anomaly=1").fetchone()[0]
    medium      = conn.execute("SELECT COUNT(*) FROM processed_results WHERE severity='MEDIUM' AND is_anomaly=1").fetchone()[0]
    low         = conn.execute("SELECT COUNT(*) FROM processed_results WHERE severity='LOW' AND is_anomaly=1").fetchone()[0]
    sla_breach  = conn.execute("SELECT COUNT(*) FROM processed_results WHERE sla_status='BREACHED'").fetchone()[0]
    sla_at_risk = conn.execute("SELECT COUNT(*) FROM processed_results WHERE sla_status='AT_RISK'").fetchone()[0]

    avg_q = conn.execute("SELECT AVG(quality_score) FROM processed_results").fetchone()[0]

    # Per dataset
    datasets_raw = conn.execute(
        "SELECT dataset, COUNT(*) as cnt, SUM(is_anomaly) as anom "
        "FROM processed_results GROUP BY dataset"
    ).fetchall()
    datasets = [
        {"dataset": r["dataset"], "total": r["cnt"], "anomalies": r["anom"] or 0}
        for r in datasets_raw
    ]

    # Severity distribution
    sev_raw = conn.execute(
        "SELECT severity, COUNT(*) as cnt FROM processed_results WHERE is_anomaly=1 GROUP BY severity"
    ).fetchall()
    severity_dist = {r["severity"]: r["cnt"] for r in sev_raw}

    # SLA distribution
    sla_raw = conn.execute(
        "SELECT sla_status, COUNT(*) as cnt FROM processed_results GROUP BY sla_status"
    ).fetchall()
    sla_dist = {r["sla_status"]: r["cnt"] for r in sla_raw}

    conn.close()

    return {
        "total_records":        total,
        "total_anomalies":      total_anom,
        "normal_records":       total - total_anom,
        "anomaly_rate":         round((total_anom / total * 100) if total else 0, 2),
        "critical_issues":      critical,
        "high_issues":          high,
        "medium_issues":        medium,
        "low_issues":           low,
        "sla_breaches":         sla_breach,
        "sla_at_risk":          sla_at_risk,
        "average_quality_score": round(avg_q or 0, 2),
        "datasets":             datasets,
        "severity_distribution": severity_dist,
        "sla_distribution":     sla_dist,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline function
# ─────────────────────────────────────────────────────────────────────────────

def process_dataset(
    dataset_name: str,
    max_records: Optional[int] = None,
    anomalies_only: bool = False,
) -> Dict[str, Any]:
    """
    Run the full pipeline for one dataset.

    Args:
        dataset_name:  "claims" | "authorization" | "pharmacy"
        max_records:   Limit number of records processed (useful for testing)
        anomalies_only: Only persist anomalous records

    Returns:
        Summary dict with counts and status.
    """
    dataset_name = dataset_name.lower()
    if dataset_name not in _ADAPTERS:
        raise ValueError(
            f"Unknown dataset '{dataset_name}'. "
            f"Must be one of: {list(_ADAPTERS.keys())}"
        )

    _init_db()

    source_path = _DATASET_SOURCES[dataset_name]
    if not source_path.exists():
        raise FileNotFoundError(
            f"Dataset source file not found: {source_path}"
        )

    logger.info("Processing dataset: %s from %s", dataset_name, source_path)
    print(f"\n{'='*60}")
    print(f"PROCESSING: {dataset_name.upper()}")
    print(f"Source: {source_path.name}")
    print(f"{'='*60}")

    # Load JSON
    with open(source_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    records_raw: List[Dict[str, Any]] = data.get("records", [])
    if max_records:
        records_raw = records_raw[:max_records]

    adapt_fn   = _ADAPTERS[dataset_name]
    total      = len(records_raw)
    processed  = 0
    persisted  = 0
    errors     = 0
    anomalies  = 0

    print(f"Records to process: {total}")

    for i, raw in enumerate(records_raw):
        try:
            # 1. Adapt to common schema
            record = adapt_fn(raw)

            # 2. Validate
            validation_errors = validate_standard_record(record)
            if validation_errors:
                for ve in validation_errors:
                    record.processing_errors.append(f"Validation: {ve}")

            if record.anomaly.is_anomaly:
                # ── ANOMALOUS RECORDS: full Quality → SLA → RAG pipeline ──
                # 3. SLA engine (only for anomalies)
                apply_sla(record)

                # 4. RAG recommendation (only for anomalies)
                apply_rag(record)

                record.processing_status = "complete"
                anomalies += 1
            else:
                # ── NORMAL RECORDS: skip SLA + RAG, store minimal record ──
                record.processing_status = "normal"

            # 5. Persist
            if not anomalies_only or record.anomaly.is_anomaly:
                _upsert_result(record)
                persisted += 1

            processed += 1

            if (i + 1) % 500 == 0:
                print(f"  ... {i+1}/{total} records processed")

        except Exception as exc:
            errors += 1
            logger.error("Error processing record %d in %s: %s", i, dataset_name, exc)

    print(f"\n{'─'*60}")
    print(f"Dataset:    {dataset_name.upper()}")
    print(f"Total:      {total}")
    print(f"Processed:  {processed}")
    print(f"Anomalies:  {anomalies}")
    print(f"Persisted:  {persisted}")
    print(f"Errors:     {errors}")
    print(f"{'─'*60}\n")

    return {
        "dataset":   dataset_name,
        "total":     total,
        "processed": processed,
        "anomalies": anomalies,
        "persisted": persisted,
        "errors":    errors,
        "status":    "completed" if errors == 0 else "completed_with_errors",
    }


def process_all(max_records_per_dataset: Optional[int] = None) -> Dict[str, Any]:
    """Run the pipeline for all three datasets."""
    results = {}
    for dataset in ("claims", "authorization", "pharmacy"):
        try:
            results[dataset] = process_dataset(
                dataset,
                max_records=max_records_per_dataset,
            )
        except Exception as exc:
            logger.error("Failed to process %s: %s", dataset, exc)
            results[dataset] = {"dataset": dataset, "status": "failed", "error": str(exc)}
    return results


# ─────────────────────────────────────────────────────────────────────────────
# CLI runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    dataset_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    max_arg     = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if dataset_arg == "all":
        process_all(max_records_per_dataset=max_arg)
    else:
        process_dataset(dataset_arg, max_records=max_arg)
