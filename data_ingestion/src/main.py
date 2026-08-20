import argparse
import json
import sys
from pathlib import Path

from format_loader import load_any
from validator import load_schema, validate_dataframe
from schema_registry import load_schemas
from report_aggregator import (
    run_batch, print_summary, save_summary,
    discover_input_files, run_single_file_auto, summarize_directory_run,
    print_directory_summary,
)


def run_single(input_file, schema_file, output_dir):
    """
    Single-file mode. Format is auto-detected (csv, xlsx, json, yml, pdf,
    image) via format_loader — this replaces the old direct loader.load_csv
    call, so this mode now accepts any supported format, not just CSV.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(input_file).stem

    df, meta = load_any(input_file)

    if meta["status"] != "ok":
        # Ingestion itself failed (unreadable/unsupported/empty). Still write
        # a report so CI/orchestration and the dashboard have something to
        # key off of, and fail loudly rather than silently skipping the file.
        report = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "missing_columns": [],
            "unexpected_columns": [],
            "issues": [{
                "type": "ingestion",
                "severity": "ERROR",
                "column": None,
                "message": meta["warning"] or "Ingestion failed",
            }],
            "status": "FAIL",
            "detected_format": meta["detected_format"],
            "extraction_confidence": meta["confidence"],
        }
        (out / f"{stem}_validation_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return report

    schema = load_schema(schema_file)
    valid, invalid, report = validate_dataframe(df, schema)

    # Tag the report with ingestion metadata so a low-confidence PDF/image
    # extraction is visible downstream, not just a silent PASS/FAIL.
    report["detected_format"] = meta["detected_format"]
    report["extraction_confidence"] = meta["confidence"]

    valid.to_csv(out / f"{stem}_valid.csv", index=False)
    invalid.to_csv(out / f"{stem}_invalid.csv", index=False)
    (out / f"{stem}_validation_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


def run_combined(args):
    """
    Batch mode: run multiple files (e.g. claims + pharmacy) through the same
    ingestion + validation pipeline and produce one combined summary report,
    instead of separate unrelated per-file reports.
    """
    jobs = []
    if args.claims_input and args.claims_schema:
        jobs.append({"label": "claims", "input": args.claims_input, "schema": args.claims_schema})
    if args.pharmacy_input and args.pharmacy_schema:
        jobs.append({"label": "pharmacy", "input": args.pharmacy_input, "schema": args.pharmacy_schema})

    if not jobs:
        print("ERROR: --batch requires at least one of "
              "(--claims-input + --claims-schema) or (--pharmacy-input + --pharmacy-schema)")
        sys.exit(2)

    summary = run_batch(jobs, validate_fn=validate_dataframe)
    print_summary(summary)

    out = Path(args.output)
    save_summary(summary, str(out / "combined_report.json"))

    return summary


def run_directory(args):
    """
    Directory mode: point at a folder containing any mix of csv/xlsx/json/
    yml/pdf/image files with unknown schema per file. Each file is ingested
    via format_loader (format auto-detected), then matched against every
    schema in --schema-dir (schema auto-detected from its columns, with
    alias/fuzzy column-name tolerance — see schema_matcher.py), then
    validated against whichever schema it matched. Files that don't clear
    the confidence threshold are routed to manual review instead of being
    forced through the wrong schema.
    """
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    schemas = load_schemas(args.schema_dir)
    if not schemas:
        print(f"ERROR: no *_schema.json files found in --schema-dir '{args.schema_dir}'")
        sys.exit(2)

    files = discover_input_files(args.input_dir)
    if not files:
        print(f"ERROR: no readable files found in --input-dir '{args.input_dir}'")
        sys.exit(2)

    file_reports = []
    for f in files:
        stem = f.stem
        report, valid_df, invalid_df = run_single_file_auto(
            str(f), schemas, validate_dataframe, min_confidence=args.min_confidence
        )
        # Same per-file output convention as single-file mode: valid/invalid
        # CSVs + a report JSON, but only when validation actually ran.
        if valid_df is not None and invalid_df is not None:
            valid_df.to_csv(out / f"{stem}_valid.csv", index=False)
            invalid_df.to_csv(out / f"{stem}_invalid.csv", index=False)
        (out / f"{stem}_validation_report.json").write_text(json.dumps(report, indent=2))
        file_reports.append(report)

    summary = summarize_directory_run(file_reports)
    print_directory_summary(summary)
    save_summary(summary, str(out / "directory_combined_report.json"))
    return summary


def main():
    p = argparse.ArgumentParser(description="Claims/Pharmacy data ingestion & validation")

    # Single-file mode (existing behavior, now multi-format via format_loader)
    p.add_argument("--input", help="Path to a single input file (csv, xlsx, json, yml, pdf, image)")
    p.add_argument("--schema", help="Path to the schema JSON for --input")

    # Batch / combined-report mode (caller already knows file<->schema pairing)
    p.add_argument("--batch", action="store_true",
                    help="Run multiple files together and produce one combined summary report")
    p.add_argument("--claims-input")
    p.add_argument("--claims-schema")
    p.add_argument("--pharmacy-input")
    p.add_argument("--pharmacy-schema")

    # Directory mode: mixed formats, schema unknown ahead of time, auto-detected per file
    p.add_argument("--input-dir", help="Folder of mixed-format files to ingest, detect schema for, and validate")
    p.add_argument("--schema-dir", default="config",
                    help="Folder of *_schema.json files to detect against (default: config)")
    p.add_argument("--min-confidence", type=float, default=0.6,
                    help="Minimum fraction of a schema's required columns that must resolve "
                         "before a file is matched to it (default: 0.6)")

    p.add_argument("--output", default="output")

    args = p.parse_args()

    if args.input_dir:
        summary = run_directory(args)
        # 0 = every file ingested, schema-matched, and validated cleanly
        sys.exit(0 if summary["overall_status"] == "pass" else 1)
    elif args.batch:
        summary = run_combined(args)
        # 0 = every file ingested + validated cleanly, 1 = any failure/issue
        sys.exit(0 if summary["overall_status"] == "pass" else 1)
    else:
        if not args.input or not args.schema:
            p.error("--input and --schema are required unless --batch or --input-dir is used")
        result = run_single(args.input, args.schema, args.output)
        # Standard exit codes for orchestration (Airflow, CI, etc.):
        # 0 = clean pass, 1 = at least one ERROR-level validation issue found.
        sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()