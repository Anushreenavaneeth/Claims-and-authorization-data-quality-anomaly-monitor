import json
from pathlib import Path
import pandas as pd

def load_schema(path):
    return json.loads(Path(path).read_text())

def validate_dataframe(df, schema):
    issues = []
    bad_rows = set()

    required = schema["required_columns"]
    not_null = schema.get("not_null_columns", [c for c in required if c not in schema.get("conditional_required", {})])
    missing = [c for c in required if c not in df.columns]
    unexpected = [c for c in df.columns if c not in required]

    for c in missing:
        issues.append({"type":"schema","severity":"ERROR","column":c,"message":"Missing required column"})
    for c in unexpected:
        issues.append({"type":"schema","severity":"WARNING","column":c,"message":"Unexpected column"})

    conditional_required = schema.get("conditional_required", {})
    date_format = schema.get("date_format", "%Y-%m-%d")

    for col in required:
        if col not in df.columns:
            continue
        if col in not_null:
            nulls = df[col].isna() | (df[col].astype(str).str.strip() == "")
            if nulls.any():
                bad_rows.update(df.index[nulls])
                issues.append({"type":"completeness","severity":"ERROR","column":col,"rows":int(nulls.sum()),"message":"Missing/blank values"})
        else:
            nulls = pd.Series(False, index=df.index)

        expected = schema["types"].get(col)
        if expected == "date":
            bad = pd.to_datetime(df[col], format=date_format, errors="coerce").isna() & ~nulls
        elif expected in ("float","integer"):
            bad = pd.to_numeric(df[col], errors="coerce").isna() & ~nulls
        else:
            bad = pd.Series(False, index=df.index)
        if bad.any():
            bad_rows.update(df.index[bad])
            issues.append({"type":"type","severity":"ERROR","column":col,"rows":int(bad.sum()),"message":f"Invalid {expected} value"})

    for col, cond in conditional_required.items():
        trigger_col = cond.get("column")
        trigger_values = cond.get("equals", [])
        if col not in df.columns or trigger_col not in df.columns:
            continue
        applies = df[trigger_col].isin(trigger_values)
        blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        bad = applies & blank
        if bad.any():
            bad_rows.update(df.index[bad])
            issues.append({"type":"completeness","severity":"ERROR","column":col,"rows":int(bad.sum()),
                            "message":f"Missing/blank value required when {trigger_col} in {trigger_values}"})

    for col, allowed in schema.get("allowed_values",{}).items():
        if col in df.columns:
            bad = ~df[col].isin(allowed) & df[col].notna()
            if bad.any():
                bad_rows.update(df.index[bad])
                issues.append({"type":"domain","severity":"ERROR","column":col,"rows":int(bad.sum()),"message":f"Allowed values: {allowed}"})

    for col in schema.get("non_negative",[]):
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            bad = vals < 0
            if bad.any():
                bad_rows.update(df.index[bad])
                issues.append({"type":"range","severity":"ERROR","column":col,"rows":int(bad.sum()),"message":"Negative value not allowed"})

    for col in schema.get("unique_columns",[]):
        if col in df.columns:
            bad = df[col].duplicated(keep=False) & df[col].notna()
            if bad.any():
                bad_rows.update(df.index[bad])
                issues.append({"type":"duplicate","severity":"ERROR","column":col,"rows":int(bad.sum()),"message":"Duplicate value"})

    valid = df.loc[~df.index.isin(bad_rows)].copy()
    invalid = df.loc[df.index.isin(bad_rows)].copy()

    has_errors = any(i["severity"] == "ERROR" for i in issues)

    report = {
        "total_records": int(len(df)),
        "valid_records": int(len(valid)),
        "invalid_records": int(len(invalid)),
        "missing_columns": missing,
        "unexpected_columns": unexpected,
        "issues": issues,
        "status": "FAIL" if has_errors else "PASS"
    }
    return valid, invalid, report
