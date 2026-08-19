import argparse, json, sys
from pathlib import Path
from loader import load_csv
from validator import load_schema, validate_dataframe

def run(input_file, schema_file, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = load_csv(input_file)
    schema = load_schema(schema_file)
    valid, invalid, report = validate_dataframe(df, schema)
    stem = Path(input_file).stem
    valid.to_csv(out/f"{stem}_valid.csv", index=False)
    invalid.to_csv(out/f"{stem}_invalid.csv", index=False)
    (out/f"{stem}_validation_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--output", default="output")
    a = p.parse_args()
    result = run(a.input, a.schema, a.output)
    # Standard exit codes for orchestration (Airflow, CI, etc.):
    # 0 = clean pass, 1 = at least one ERROR-level validation issue found.
    sys.exit(0 if result["status"] == "PASS" else 1)
