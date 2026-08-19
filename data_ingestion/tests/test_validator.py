import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from validator import validate_dataframe  # noqa: E402


CLAIMS_SCHEMA = {
    "required_columns": [
        "claim_id", "member_id", "provider_id", "claim_date",
        "service_type", "procedure_code", "diagnosis_code",
        "claim_amount", "claim_status", "denial_code",
        "processing_time_minutes"
    ],
    "types": {
        "claim_id": "string", "member_id": "string", "provider_id": "string",
        "claim_date": "date", "service_type": "string", "procedure_code": "string",
        "diagnosis_code": "string", "claim_amount": "float", "claim_status": "string",
        "denial_code": "string", "processing_time_minutes": "float"
    },
    "conditional_required": {
        "denial_code": {"column": "claim_status", "equals": ["DENIED"]}
    },
    "allowed_values": {"claim_status": ["PAID", "PENDING", "DENIED"]},
    "non_negative": ["claim_amount", "processing_time_minutes"],
    "unique_columns": ["claim_id"]
}


def make_claims_df(**overrides):
    base = {
        "claim_id": "C001", "member_id": "M001", "provider_id": "P001",
        "claim_date": "2026-08-01", "service_type": "Consultation",
        "procedure_code": "PROC001", "diagnosis_code": "DIA001",
        "claim_amount": 100.0, "claim_status": "PAID", "denial_code": "",
        "processing_time_minutes": 30
    }
    base.update(overrides)
    return pd.DataFrame([base])


def test_clean_row_is_valid():
    df = make_claims_df()
    valid, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(valid) == 1
    assert len(invalid) == 0
    assert report["status"] == "PASS"


def test_paid_claim_without_denial_code_is_valid():
    # Regression test: denial_code must NOT be required for non-DENIED claims.
    df = make_claims_df(claim_status="PAID", denial_code="")
    valid, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 0
    assert report["status"] == "PASS"


def test_denied_claim_without_denial_code_is_invalid():
    df = make_claims_df(claim_status="DENIED", denial_code="")
    valid, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 1
    assert any(i["column"] == "denial_code" for i in report["issues"])


def test_missing_required_column_flagged():
    df = make_claims_df().drop(columns=["provider_id"])
    _, _, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert "provider_id" in report["missing_columns"]
    assert report["status"] == "FAIL"


def test_invalid_date_flagged():
    df = make_claims_df(claim_date="NOT_A_DATE")
    _, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 1
    assert any(i["column"] == "claim_date" and i["type"] == "type" for i in report["issues"])


def test_negative_amount_flagged():
    df = make_claims_df(claim_amount=-50.0)
    _, invalid, _ = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 1


def test_unknown_status_flagged():
    df = make_claims_df(claim_status="UNKNOWN")
    _, invalid, _ = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 1


def test_duplicate_claim_id_flagged():
    df = pd.concat([make_claims_df(), make_claims_df()], ignore_index=True)
    _, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 2
    assert any(i["type"] == "duplicate" for i in report["issues"])


def test_unexpected_column_is_warning_not_failure():
    df = make_claims_df()
    df["extra_col"] = "x"
    _, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 0
    assert report["status"] == "PASS"
    assert "extra_col" in report["unexpected_columns"]


def test_loader_preserves_leading_zeros_and_reindexes(tmp_path):
    # Regression test for dtype=str + reset_index in loader.py
    from loader import load_csv
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("claim_id,member_id\nC001,00123\nC002,00456\n")
    df = load_csv(str(csv_path))
    assert df["member_id"].tolist() == ["00123", "00456"]
    assert list(df.index) == [0, 1]


def test_strict_date_format_rejects_ambiguous_dates():
    # Only ISO YYYY-MM-DD should be accepted per schema's date_format.
    df = make_claims_df(claim_date="08/01/2026")
    _, invalid, report = validate_dataframe(df, CLAIMS_SCHEMA)
    assert len(invalid) == 1
    assert any(i["column"] == "claim_date" for i in report["issues"])
