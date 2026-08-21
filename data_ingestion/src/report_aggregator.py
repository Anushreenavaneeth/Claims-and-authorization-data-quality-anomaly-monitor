"""
report_aggregator.py
---------------------
Runs the ingestion + validation pipeline across multiple files and produces
a single combined summary report — e.g. "2 files processed, 14 total
invalid rows" — instead of one report per run.

Sits downstream of format_loader.load_any() and validator.validate_dataframe().
Neither of those files change.

validate_dataframe(df, schema) returns (valid_df, invalid_df, report) where
report = {
    "total_records": int, "valid_records": int, "invalid_records": int,
    "missing_columns": [...], "unexpected_columns": [...],
    "issues": [{"type": str, "severity": "ERROR"|"WARNING", "column": str,
                "rows": int, "message": str}, ...],
    "status": "PASS" | "FAIL"
}

Usage (programmatic):
    from report_aggregator import run_batch, print_summary, save_summary
    from validator import validate_dataframe

    jobs = [
        {"label": "claims",   "input": "data/claims_batch.csv",   "schema": "config/claims_schema.json"},
        {"label": "pharmacy", "input": "data/pharmacy_batch.csv", "schema": "config/pharmacy_schema.json"},
    ]

    summary = run_batch(jobs, validate_fn=validate_dataframe)
    print_summary(summary)
    save_summary(summary, "output/combined_report.json")
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from format_loader import load_any
from schema_matcher import detect_schema

logger = logging.getLogger(__name__)

# Extensions format_loader.load_any() knows how to read. Anything else in
# an input directory (e.g. .txt notes, .DS_Store) is skipped rather than
# sent through and failed loudly.
DISCOVERABLE_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".yml", ".yaml", ".pdf", ".png", ".jpg", ".jpeg"}


# --------------------------------------------------------------------------
# Adapter: pulls the roll-up numbers out of validator.py's report dict.
# Kept as its own function so if validator.py's report shape ever changes,
# this is the only place to touch.
# --------------------------------------------------------------------------

def _extract_counts(validation_report: Dict[str, Any]) -> Dict[str, Any]:
    issues = validation_report.get("issues", [])

    # Breakdown by issue type (schema / completeness / type / domain / range /
    # duplicate / ingestion), counting affected rows where available so the
    # summary reflects row-level impact, not just number of rule violations.
    error_type_counts: Dict[str, int] = {}
    for issue in issues:
        if issue.get("severity") != "ERROR":
            continue
        category = issue.get("type", "unknown")
        weight = issue.get("rows", 1)
        error_type_counts[category] = error_type_counts.get(category, 0) + weight

    return {
        "total_rows": validation_report.get("total_records", 0),
        "valid_rows": validation_report.get("valid_records", 0),
        "invalid_rows": validation_report.get("invalid_records", 0),
        "error_type_counts": error_type_counts,
    }


# --------------------------------------------------------------------------
# Per-file pipeline run
# --------------------------------------------------------------------------

def run_single_file(label: str, input_path: str, schema_path: str, validate_fn) -> Dict[str, Any]:
    """
    Runs load_any -> validate_dataframe for one file and returns a per-file
    report. `validate_fn` is passed in (validator.validate_dataframe) rather
    than imported directly here, keeping this module decoupled/testable.
    """
    report: Dict[str, Any] = {
        "label": label,
        "input_file": input_path,
        "schema_file": schema_path,
        "ingestion_status": None,
        "detected_format": None,
        "extraction_confidence": None,
        "validation_status": "not_run",   # not_run | completed | error | skipped_ingestion_failed
        "validator_status": None,          # PASS | FAIL, mirrors validator.py's report["status"]
        "missing_columns": [],
        "unexpected_columns": [],
        "counts": {"total_rows": 0, "valid_rows": 0, "invalid_rows": 0, "error_type_counts": {}},
        "warning": None,
    }

    df, meta = load_any(input_path)
    report["ingestion_status"] = meta["status"]
    report["detected_format"] = meta["detected_format"]
    report["extraction_confidence"] = meta["confidence"]

    if meta["status"] != "ok":
        report["warning"] = meta["warning"]
        report["validation_status"] = "skipped_ingestion_failed"
        return report

    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))

    try:
        _valid_df, _invalid_df, validation_report = validate_fn(df, schema)
    except Exception as e:
        logger.error("Validation failed for %s: %s", input_path, e)
        report["validation_status"] = "error"
        report["warning"] = str(e)
        return report

    report["validation_status"] = "completed"
    report["validator_status"] = validation_report.get("status")
    report["missing_columns"] = validation_report.get("missing_columns", [])
    report["unexpected_columns"] = validation_report.get("unexpected_columns", [])
    report["counts"] = _extract_counts(validation_report)
    return report


# --------------------------------------------------------------------------
# Directory mode: mixed-format files, schema unknown ahead of time.
# Sits on top of the same load_any() / validate_fn() building blocks as
# run_single_file above — nothing about ingestion or validation rules
# changes here, only *which schema applies* is now inferred per file.
# --------------------------------------------------------------------------

def discover_input_files(input_dir: str) -> List[Path]:
    """Lists every file in input_dir (non-recursive) whose extension
    format_loader can read. Unsupported/hidden files are skipped, not
    errored, since a source drop-folder often has stray non-data files."""
    directory = Path(input_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in DISCOVERABLE_SUFFIXES
    )


def run_single_file_auto(
    input_path: str,
    schemas: Dict[str, Dict[str, Any]],
    validate_fn,
    min_confidence: float = 0.6,
) -> Tuple[Dict[str, Any], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Like run_single_file, but the schema isn't passed in — it's detected
    from the ingested file's own columns against the full schema registry
    (schema_matcher.detect_schema). If no schema clears min_confidence, the
    file is routed to "skipped_schema_unmatched" instead of being forced
    through the wrong schema or discarded silently.

    Returns (report, valid_df, invalid_df). valid_df/invalid_df are None
    whenever validation didn't actually run (ingestion failure or
    unmatched schema) — the caller decides whether/what to write to disk.
    """
    report: Dict[str, Any] = {
        "input_file": str(input_path),
        "ingestion_status": None,
        "detected_format": None,
        "extraction_confidence": None,
        "schema_detection": None,
        "matched_schema": None,
        "validation_status": "not_run",   # not_run | completed | error |
                                           # skipped_ingestion_failed | skipped_schema_unmatched
        "validator_status": None,
        "missing_columns": [],
        "unexpected_columns": [],
        "column_resolution": [],
        "counts": {"total_rows": 0, "valid_rows": 0, "invalid_rows": 0, "error_type_counts": {}},
        "warning": None,
    }

    df, meta = load_any(str(input_path))
    report["ingestion_status"] = meta["status"]
    report["detected_format"] = meta["detected_format"]
    report["extraction_confidence"] = meta["confidence"]

    if meta["status"] != "ok":
        report["warning"] = meta["warning"]
        report["validation_status"] = "skipped_ingestion_failed"
        return report, None, None

    detection = detect_schema(list(df.columns), schemas, min_confidence=min_confidence)
    report["schema_detection"] = {
        "matched_schema": detection["matched_schema"],
        "confidence": round(detection["confidence"], 3),
        "candidates": detection["candidates"],
    }

    if detection["matched_schema"] is None:
        report["validation_status"] = "skipped_schema_unmatched"
        best = detection["candidates"][0] if detection["candidates"] else None
        report["warning"] = (
            f"No schema matched with confidence >= {min_confidence} "
            f"(closest: {best}). Routed to manual review instead of "
            "guessing at a schema."
        )
        return report, None, None

    schema_name = detection["matched_schema"]
    schema = schemas[schema_name]
    report["matched_schema"] = schema_name

    try:
        valid_df, invalid_df, validation_report = validate_fn(df, schema)
    except Exception as e:
        logger.error("Validation failed for %s: %s", input_path, e)
        report["validation_status"] = "error"
        report["warning"] = str(e)
        return report, None, None

    report["validation_status"] = "completed"
    report["validator_status"] = validation_report.get("status")
    report["missing_columns"] = validation_report.get("missing_columns", [])
    report["unexpected_columns"] = validation_report.get("unexpected_columns", [])
    report["column_resolution"] = validation_report.get("column_resolution", [])
    report["counts"] = _extract_counts(validation_report)
    return report, valid_df, invalid_df


def summarize_directory_run(file_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Same roll-up shape as run_batch()'s summary, generalized for
    directory mode where files carry a detected schema instead of a
    caller-supplied label."""
    total_files = len(file_reports)
    files_ok = sum(1 for r in file_reports if r["validation_status"] == "completed")
    files_unmatched = sum(1 for r in file_reports if r["validation_status"] == "skipped_schema_unmatched")
    files_failed = total_files - files_ok - files_unmatched

    total_rows = sum(r["counts"]["total_rows"] for r in file_reports)
    total_valid = sum(r["counts"]["valid_rows"] for r in file_reports)
    total_invalid = sum(r["counts"]["invalid_rows"] for r in file_reports)

    combined_error_types: Dict[str, int] = {}
    for r in file_reports:
        for category, count in r["counts"]["error_type_counts"].items():
            combined_error_types[category] = combined_error_types.get(category, 0) + count

    any_validator_fail = any(r["validator_status"] == "FAIL" for r in file_reports)
    overall_status = (
        "pass" if (files_failed == 0 and files_unmatched == 0 and not any_validator_fail)
        else "issues_found"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files_processed": total_files,
        "files_completed": files_ok,
        "files_unmatched_schema": files_unmatched,
        "files_failed": files_failed,
        "total_rows_processed": total_rows,
        "total_valid_rows": total_valid,
        "total_invalid_rows": total_invalid,
        "combined_error_type_counts": combined_error_types,
        "overall_status": overall_status,
        "file_reports": file_reports,
    }


# --------------------------------------------------------------------------
# Batch runner + combined summary
# --------------------------------------------------------------------------

def run_batch(jobs: List[Dict[str, str]], validate_fn=None) -> Dict[str, Any]:
    """
    jobs: list of {"label": str, "input": path, "schema": path}
    validate_fn: validator.validate_dataframe — pass it explicitly (default
                 import below assumes validator.py sits on the same path).
    """
    if validate_fn is None:
        from validator import validate_dataframe as validate_fn  # adjust import path if needed

    file_reports = [
        run_single_file(job["label"], job["input"], job["schema"], validate_fn)
        for job in jobs
    ]

    total_files = len(file_reports)
    files_ok = sum(1 for r in file_reports if r["validation_status"] == "completed")
    files_failed = total_files - files_ok

    total_rows = sum(r["counts"]["total_rows"] for r in file_reports)
    total_valid = sum(r["counts"]["valid_rows"] for r in file_reports)
    total_invalid = sum(r["counts"]["invalid_rows"] for r in file_reports)

    combined_error_types: Dict[str, int] = {}
    for r in file_reports:
        for category, count in r["counts"]["error_type_counts"].items():
            combined_error_types[category] = combined_error_types.get(category, 0) + count

    any_validator_fail = any(r["validator_status"] == "FAIL" for r in file_reports)
    overall_status = "pass" if (files_failed == 0 and not any_validator_fail) else "issues_found"

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files_processed": total_files,
        "files_completed": files_ok,
        "files_failed": files_failed,
        "total_rows_processed": total_rows,
        "total_valid_rows": total_valid,
        "total_invalid_rows": total_invalid,
        "combined_error_type_counts": combined_error_types,
        "overall_status": overall_status,
        "file_reports": file_reports,
    }
    return summary


# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------

def print_summary(summary: Dict[str, Any]) -> None:
    print("=" * 60)
    print("COMBINED DATA-QUALITY SUMMARY")
    print("=" * 60)
    print(f"Files processed : {summary['files_processed']} "
          f"({summary['files_completed']} ok, {summary['files_failed']} failed)")
    print(f"Total rows      : {summary['total_rows_processed']}")
    print(f"Valid rows      : {summary['total_valid_rows']}")
    print(f"Invalid rows    : {summary['total_invalid_rows']}")
    print(f"Overall status  : {summary['overall_status'].upper()}")

    if summary["combined_error_type_counts"]:
        print("\nError breakdown (all files, by issue type):")
        for category, count in sorted(summary["combined_error_type_counts"].items(), key=lambda x: -x[1]):
            print(f"  - {category}: {count}")

    print("\nPer-file detail:")
    for r in summary["file_reports"]:
        print(f"  [{r['label']}] {r['input_file']}")
        print(f"      format={r['detected_format']} confidence={r['extraction_confidence']} "
              f"ingestion={r['ingestion_status']} validation={r['validation_status']} "
              f"({r['validator_status']})")
        if r["warning"]:
            print(f"      WARNING: {r['warning']}")
        else:
            c = r["counts"]
            print(f"      rows={c['total_rows']} valid={c['valid_rows']} invalid={c['invalid_rows']}")
    print("=" * 60)


def print_directory_summary(summary: Dict[str, Any]) -> None:
    """Directory-mode counterpart to print_summary(): file_reports here
    carry a detected schema per file instead of a caller-supplied label."""
    print("=" * 60)
    print("DIRECTORY INGESTION + AUTO-SCHEMA-DETECTION SUMMARY")
    print("=" * 60)
    print(f"Files processed : {summary['files_processed']} "
          f"({summary['files_completed']} ok, "
          f"{summary['files_unmatched_schema']} unmatched schema, "
          f"{summary['files_failed']} failed)")
    print(f"Total rows      : {summary['total_rows_processed']}")
    print(f"Valid rows      : {summary['total_valid_rows']}")
    print(f"Invalid rows    : {summary['total_invalid_rows']}")
    print(f"Overall status  : {summary['overall_status'].upper()}")

    if summary["combined_error_type_counts"]:
        print("\nError breakdown (all files, by issue type):")
        for category, count in sorted(summary["combined_error_type_counts"].items(), key=lambda x: -x[1]):
            print(f"  - {category}: {count}")

    print("\nPer-file detail:")
    for r in summary["file_reports"]:
        det = r.get("schema_detection") or {}
        print(f"  {r['input_file']}")
        print(f"      format={r['detected_format']} confidence={r['extraction_confidence']} "
              f"ingestion={r['ingestion_status']}")
        print(f"      matched_schema={r['matched_schema']} "
              f"schema_confidence={det.get('confidence')} "
              f"validation={r['validation_status']} ({r['validator_status']})")
        if r["column_resolution"]:
            renamed = ", ".join(f"{c['original_column']}->{c['matched_to']} ({c['method']})"
                                 for c in r["column_resolution"])
            print(f"      column_resolution: {renamed}")
        if r["warning"]:
            print(f"      WARNING: {r['warning']}")
        else:
            c = r["counts"]
            print(f"      rows={c['total_rows']} valid={c['valid_rows']} invalid={c['invalid_rows']}")
    print("=" * 60)


def save_summary(summary: Dict[str, Any], output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Combined summary written to %s", output_path)