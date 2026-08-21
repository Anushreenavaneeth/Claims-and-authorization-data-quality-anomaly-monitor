
"""
TC-PUF FINAL ANOMALY INTEGRATION
================================

Combines:

1. Bayesian unsupervised anomaly detection
2. Rule-based anomaly detection
3. ML anomaly/evidence output

Produces:

1. Final CSV
2. Final JSON
3. Integration validation summary

The JSON is designed to be consumed by the RAG/recommendation layer.

IMPORTANT:
- Bayesian + rule results contain all 4,956 records.
- Evidence contains only ML-anomalous records.
- Plan_ID + Issuer_ID are used as the record identity.
"""

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
ANOMALIES_DIR = BASE_DIR / "data" / "anomalies"

BAYESIAN_FILE = (
    PROCESSED_DIR / "tc_puf_bayesian_results.csv"
)

RULE_FILE = (
    ANOMALIES_DIR / "tc_puf_rule_results.csv"
)

EVIDENCE_FILE = (
    PROCESSED_DIR / "tc_puf_anomaly_evidence.csv"
)

OUTPUT_DIR = (
    PROCESSED_DIR / "final"
)

FINAL_CSV = (
    OUTPUT_DIR / "tc_puf_final_anomaly_results.csv"
)

FINAL_JSON = (
    OUTPUT_DIR / "tc_puf_final_anomaly_results.json"
)

VALIDATION_FILE = (
    OUTPUT_DIR / "tc_puf_integration_validation.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

KEY_COLUMNS = [
    "Plan_ID",
    "Issuer_ID",
]

REQUIRED_BAYESIAN_COLUMNS = [
    "Plan_ID",
    "Issuer_ID",
    "State",
    "Issuer_Name",
    "Bayesian_Anomaly",
    "Bayesian_Anomaly_Score",
    "Bayesian_Anomaly_Probability",
    "Bayesian_Threshold",
]

REQUIRED_RULE_COLUMNS = [
    "Plan_ID",
    "Issuer_ID",
    "rule_anomaly",
    "rule_count",
    "rule_name",
    "rule_reason",
    "rule_severity",
]

REQUIRED_EVIDENCE_COLUMNS = [
    "Plan_ID",
    "Issuer_ID",
    "Evidence_Count",
    "Evidence_Severity",
    "Evidence_Types",
    "Evidence_Features",
    "Evidence_Details",
    "Evidence_Summary",
]


# ============================================================
# HELPERS
# ============================================================

def print_section(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def fail(message):
    print()
    print("ERROR:")
    print(message)
    sys.exit(1)


def check_file(path):
    if not path.exists():
        fail(f"Required file not found:\n{path}")


def check_columns(df, required, name):
    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        fail(
            f"{name} is missing required columns:\n"
            + "\n".join(missing)
        )


def normalize_keys(df):
    """
    Normalize merge keys without changing their meaning.
    """

    result = df.copy()

    for column in KEY_COLUMNS:

        if column not in result.columns:
            fail(
                f"Missing merge key: {column}"
            )

        result[column] = (
            result[column]
            .astype(str)
            .str.strip()
        )

        result[column] = (
            result[column]
            .replace(
                {
                    "nan": "",
                    "None": "",
                    "NaN": "",
                }
            )
        )

    return result


def check_duplicate_keys(df, name):

    duplicates = (
        df.duplicated(
            subset=KEY_COLUMNS,
            keep=False
        )
    )

    count = int(duplicates.sum())

    if count > 0:

        duplicate_keys = (
            df.loc[
                duplicates,
                KEY_COLUMNS
            ]
            .drop_duplicates()
            .head(10)
            .to_dict("records")
        )

        fail(
            f"{name} contains duplicate "
            f"Plan_ID + Issuer_ID keys.\n"
            f"Duplicate rows: {count}\n"
            f"Examples: {duplicate_keys}"
        )


def numeric_bool(value):
    """
    Convert anomaly-like values to 0/1 safely.
    """

    if pd.isna(value):
        return 0

    if isinstance(value, bool):
        return int(value)

    text = str(value).strip().lower()

    if text in {
        "1",
        "true",
        "yes",
        "y",
        "anomaly",
    }:
        return 1

    return 0


def clean_json_value(value):

    if pd.isna(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    return value


def safe_text(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


def calculate_final_severity(row):

    """
    Severity is determined from independent signals.

    CRITICAL:
        Bayesian anomaly + rule anomaly + evidence

    HIGH:
        Two independent anomaly signals

    MEDIUM:
        One strong anomaly signal

    LOW:
        No anomaly
    """

    bayesian = int(
        row["Bayesian_Anomaly"]
    )

    rule = int(
        row["Rule_Anomaly"]
    )

    evidence_count = int(
        row["Evidence_Count"]
    )

    signal_count = (
        bayesian
        + rule
        + int(evidence_count > 0)
    )

    if signal_count >= 3:
        return "CRITICAL"

    if signal_count == 2:
        return "HIGH"

    if signal_count == 1:
        return "MEDIUM"

    return "LOW"


def calculate_final_anomaly(row):

    return int(
        (
            int(row["Bayesian_Anomaly"]) == 1
        )
        or
        (
            int(row["Rule_Anomaly"]) == 1
        )
        or
        (
            int(row["Evidence_Count"]) > 0
        )
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print_section("LOADING FINAL INTEGRATION INPUTS")

    check_file(BAYESIAN_FILE)
    check_file(RULE_FILE)
    check_file(EVIDENCE_FILE)

    print(f"Bayesian file : {BAYESIAN_FILE}")
    print(f"Rule file     : {RULE_FILE}")
    print(f"Evidence file : {EVIDENCE_FILE}")

    bayesian = pd.read_csv(
        BAYESIAN_FILE
    )

    rules = pd.read_csv(
        RULE_FILE
    )

    evidence = pd.read_csv(
        EVIDENCE_FILE
    )

    print()
    print("Bayesian shape:", bayesian.shape)
    print("Rule shape    :", rules.shape)
    print("Evidence shape:", evidence.shape)

    return bayesian, rules, evidence


# ============================================================
# VALIDATE INPUTS
# ============================================================

def validate_inputs(
    bayesian,
    rules,
    evidence,
):

    print_section("VALIDATING INPUT DATA")

    check_columns(
        bayesian,
        REQUIRED_BAYESIAN_COLUMNS,
        "Bayesian results"
    )

    check_columns(
        rules,
        REQUIRED_RULE_COLUMNS,
        "Rule results"
    )

    check_columns(
        evidence,
        REQUIRED_EVIDENCE_COLUMNS,
        "Evidence results"
    )

    bayesian = normalize_keys(
        bayesian
    )

    rules = normalize_keys(
        rules
    )

    evidence = normalize_keys(
        evidence
    )

    check_duplicate_keys(
        bayesian,
        "Bayesian results"
    )

    check_duplicate_keys(
        rules,
        "Rule results"
    )

    check_duplicate_keys(
        evidence,
        "Evidence results"
    )

    # --------------------------------------------------------
    # Check Bayesian and rule record coverage.
    # --------------------------------------------------------

    bayesian_keys = set(
        map(
            tuple,
            bayesian[KEY_COLUMNS].values
        )
    )

    rule_keys = set(
        map(
            tuple,
            rules[KEY_COLUMNS].values
        )
    )

    if bayesian_keys != rule_keys:

        only_bayesian = (
            bayesian_keys - rule_keys
        )

        only_rules = (
            rule_keys - bayesian_keys
        )

        fail(
            "Bayesian and rule datasets do not "
            "contain exactly the same records.\n"
            f"Only Bayesian: {len(only_bayesian)}\n"
            f"Only Rules   : {len(only_rules)}"
        )

    # --------------------------------------------------------
    # Normalize anomaly columns.
    # --------------------------------------------------------

    bayesian["Bayesian_Anomaly"] = (
        bayesian["Bayesian_Anomaly"]
        .apply(numeric_bool)
    )

    rules["rule_anomaly"] = (
        rules["rule_anomaly"]
        .apply(numeric_bool)
    )

    print("Input validation: PASSED")

    return bayesian, rules, evidence


# ============================================================
# PREPARE EVIDENCE
# ============================================================

def prepare_evidence(evidence):

    print_section("PREPARING ML EVIDENCE")

    evidence = evidence.copy()

    evidence["Evidence_Count"] = (
        pd.to_numeric(
            evidence["Evidence_Count"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    evidence["Evidence_Severity"] = (
        evidence["Evidence_Severity"]
        .apply(safe_text)
    )

    for column in [
        "Evidence_Types",
        "Evidence_Features",
        "Evidence_Details",
        "Evidence_Summary",
    ]:
        evidence[column] = (
            evidence[column]
            .apply(safe_text)
        )

    return evidence


# ============================================================
# MERGE
# ============================================================

def merge_results(
    bayesian,
    rules,
    evidence,
):

    print_section("MERGING ANOMALY SIGNALS")

    # --------------------------------------------------------
    # Select only required rule output columns.
    # --------------------------------------------------------

    rule_columns = [
        "Plan_ID",
        "Issuer_ID",
        "rule_anomaly",
        "rule_count",
        "rule_name",
        "rule_reason",
        "rule_severity",
    ]

    rules_small = rules[
        rule_columns
    ].copy()

    # --------------------------------------------------------
    # Select only required evidence columns.
    # --------------------------------------------------------

    evidence_columns = [
        "Plan_ID",
        "Issuer_ID",
        "Evidence_Count",
        "Evidence_Severity",
        "Evidence_Types",
        "Evidence_Features",
        "Evidence_Details",
        "Evidence_Summary",
    ]

    evidence_small = evidence[
        evidence_columns
    ].copy()

    # --------------------------------------------------------
    # Evidence is sparse by design.
    #
    # Left join means all 4,956 records remain.
    # --------------------------------------------------------

    result = bayesian.merge(
        rules_small,
        on=KEY_COLUMNS,
        how="left",
        validate="one_to_one",
        suffixes=("", "_rule")
    )

    result = result.merge(
        evidence_small,
        on=KEY_COLUMNS,
        how="left",
        validate="one_to_one",
        suffixes=("", "_evidence")
    )

    # --------------------------------------------------------
    # Fill missing evidence/rule fields.
    # --------------------------------------------------------

    result["Rule_Anomaly"] = (
        pd.to_numeric(
            result["rule_anomaly"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    result["Rule_Count"] = (
        pd.to_numeric(
            result["rule_count"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    result["Rule_Name"] = (
        result["rule_name"]
        .fillna("")
        .astype(str)
    )

    result["Rule_Reason"] = (
        result["rule_reason"]
        .fillna("")
        .astype(str)
    )

    result["Rule_Severity"] = (
        result["rule_severity"]
        .fillna("")
        .astype(str)
    )

    result["Evidence_Count"] = (
        pd.to_numeric(
            result["Evidence_Count"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    for column in [
        "Evidence_Severity",
        "Evidence_Types",
        "Evidence_Features",
        "Evidence_Details",
        "Evidence_Summary",
    ]:
        result[column] = (
            result[column]
            .fillna("")
            .astype(str)
        )

    # --------------------------------------------------------
    # Final anomaly decision.
    # --------------------------------------------------------

    result["Final_Anomaly"] = (
        result.apply(
            calculate_final_anomaly,
            axis=1
        )
    )

    result["Final_Severity"] = (
        result.apply(
            calculate_final_severity,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Signal count.
    # --------------------------------------------------------

    result["Anomaly_Signal_Count"] = (
        result["Bayesian_Anomaly"].astype(int)
        +
        result["Rule_Anomaly"].astype(int)
        +
        (
            result["Evidence_Count"] > 0
        ).astype(int)
    )

    # --------------------------------------------------------
    # Signal explanation.
    # --------------------------------------------------------

    def signal_text(row):

        signals = []

        if row["Bayesian_Anomaly"] == 1:
            signals.append("Bayesian")

        if row["Rule_Anomaly"] == 1:
            signals.append("Rule")

        if row["Evidence_Count"] > 0:
            signals.append("ML_Evidence")

        if not signals:
            return "None"

        return ", ".join(signals)

    result["Anomaly_Signals"] = (
        result.apply(
            signal_text,
            axis=1
        )
    )

    print(
        "Merged shape:",
        result.shape
    )

    return result


# ============================================================
# FINAL VALIDATION
# ============================================================

def validate_final(result):

    print_section("FINAL INTEGRATION VALIDATION")

    validation = {}

    validation["total_records"] = int(
        len(result)
    )

    validation["duplicate_keys"] = int(
        result.duplicated(
            subset=KEY_COLUMNS
        ).sum()
    )

    validation["bayesian_anomalies"] = int(
        result["Bayesian_Anomaly"].sum()
    )

    validation["rule_anomalies"] = int(
        result["Rule_Anomaly"].sum()
    )

    validation["ml_evidence_records"] = int(
        (result["Evidence_Count"] > 0).sum()
    )

    validation["final_anomalies"] = int(
        result["Final_Anomaly"].sum()
    )

    validation["final_anomaly_percentage"] = round(
        float(
            result["Final_Anomaly"].mean()
            * 100
        ),
        4
    )

    validation["critical_records"] = int(
        (
            result["Final_Severity"]
            == "CRITICAL"
        ).sum()
    )

    validation["high_records"] = int(
        (
            result["Final_Severity"]
            == "HIGH"
        ).sum()
    )

    validation["medium_records"] = int(
        (
            result["Final_Severity"]
            == "MEDIUM"
        ).sum()
    )

    validation["low_records"] = int(
        (
            result["Final_Severity"]
            == "LOW"
        ).sum()
    )

    # --------------------------------------------------------
    # Required consistency checks.
    # --------------------------------------------------------

    if validation["duplicate_keys"] != 0:
        fail(
            "FINAL VALIDATION FAILED: "
            "duplicate Plan_ID + Issuer_ID keys."
        )

    if validation["total_records"] != 4956:
        fail(
            "FINAL VALIDATION FAILED: "
            f"expected 4,956 records but got "
            f"{validation['total_records']}."
        )

    if validation["bayesian_anomalies"] != 248:
        fail(
            "FINAL VALIDATION FAILED: "
            f"expected 248 Bayesian anomalies but got "
            f"{validation['bayesian_anomalies']}."
        )

    # --------------------------------------------------------
    # Final anomaly cannot be less than an independent signal.
    # --------------------------------------------------------

    if (
        validation["final_anomalies"]
        < validation["bayesian_anomalies"]
    ):
        fail(
            "FINAL VALIDATION FAILED: "
            "final anomalies are fewer than Bayesian anomalies."
        )

    if (
        validation["final_anomalies"]
        < validation["rule_anomalies"]
    ):
        fail(
            "FINAL VALIDATION FAILED: "
            "final anomalies are fewer than rule anomalies."
        )

    validation["status"] = "PASSED"

    print(
        json.dumps(
            validation,
            indent=2
        )
    )

    return validation


# ============================================================
# JSON CONVERSION
# ============================================================

def build_json(result):

    print_section("BUILDING RAG JSON")

    records = []

    for _, row in result.iterrows():

        record = {
            "record_id": {
                "plan_id": safe_text(
                    row["Plan_ID"]
                ),
                "issuer_id": safe_text(
                    row["Issuer_ID"]
                ),
            },

            "entity": {
                "state": safe_text(
                    row["State"]
                ),
                "issuer_name": safe_text(
                    row["Issuer_Name"]
                ),
                "plan_type": safe_text(
                    row["Plan_Type"]
                ),
                "metal_level": safe_text(
                    row["Metal_Level"]
                ),
                "exchange_type": safe_text(
                    row["Exchange_Type"]
                ),
                "individual_or_shop": safe_text(
                    row["Individual/SHOP"]
                ),
            },

            "final_assessment": {
                "anomaly": bool(
                    row["Final_Anomaly"]
                ),
                "severity": safe_text(
                    row["Final_Severity"]
                ),
                "signal_count": int(
                    row["Anomaly_Signal_Count"]
                ),
                "signals": safe_text(
                    row["Anomaly_Signals"]
                ),
            },

            "bayesian": {
                "anomaly": bool(
                    row["Bayesian_Anomaly"]
                ),
                "score": clean_json_value(
                    row["Bayesian_Anomaly_Score"]
                ),
                "probability": clean_json_value(
                    row["Bayesian_Anomaly_Probability"]
                ),
                "threshold": clean_json_value(
                    row["Bayesian_Threshold"]
                ),
            },

            "rule_engine": {
                "anomaly": bool(
                    row["Rule_Anomaly"]
                ),
                "rule_count": int(
                    row["Rule_Count"]
                ),
                "rule_name": safe_text(
                    row["Rule_Name"]
                ),
                "reason": safe_text(
                    row["Rule_Reason"]
                ),
                "severity": safe_text(
                    row["Rule_Severity"]
                ),
            },

            "ml_evidence": {
                "evidence_count": int(
                    row["Evidence_Count"]
                ),
                "severity": safe_text(
                    row["Evidence_Severity"]
                ),
                "types": safe_text(
                    row["Evidence_Types"]
                ),
                "features": safe_text(
                    row["Evidence_Features"]
                ),
                "details": safe_text(
                    row["Evidence_Details"]
                ),
                "summary": safe_text(
                    row["Evidence_Summary"]
                ),
            },
        }

        records.append(record)

    payload = {
        "project": "TC-PUF Claims and Authorization Data Quality Anomaly Monitor",
        "schema_version": "1.0",
        "record_count": len(records),
        "records": records,
    }

    return payload


# ============================================================
# SAVE
# ============================================================

def save_outputs(
    result,
    payload,
    validation,
):

    print_section("SAVING FINAL OUTPUTS")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Remove internal duplicate columns before CSV output.
    # --------------------------------------------------------

    output_columns = [
        "Plan_ID",
        "Issuer_ID",
        "State",
        "Issuer_Name",
        "Plan_Type",
        "Metal_Level",
        "Exchange_Type",
        "Individual/SHOP",

        "Bayesian_Anomaly",
        "Bayesian_Anomaly_Score",
        "Bayesian_Anomaly_Probability",
        "Bayesian_Threshold",

        "Rule_Anomaly",
        "Rule_Count",
        "Rule_Name",
        "Rule_Reason",
        "Rule_Severity",

        "Evidence_Count",
        "Evidence_Severity",
        "Evidence_Types",
        "Evidence_Features",
        "Evidence_Details",
        "Evidence_Summary",

        "Anomaly_Signal_Count",
        "Anomaly_Signals",
        "Final_Anomaly",
        "Final_Severity",
    ]

    output_columns = [
        column
        for column in output_columns
        if column in result.columns
    ]

    final_df = result[
        output_columns
    ].copy()

    final_df.to_csv(
        FINAL_CSV,
        index=False
    )

    with open(
        FINAL_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False
        )

    with open(
        VALIDATION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            validation,
            file,
            indent=2
        )

    print(f"CSV       : {FINAL_CSV}")
    print(f"JSON      : {FINAL_JSON}")
    print(f"Validation: {VALIDATION_FILE}")

    print()
    print("Records:", len(final_df))
    print(
        "Final anomalies:",
        int(final_df["Final_Anomaly"].sum())
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print_section(
        "TC-PUF FINAL ANOMALY INTEGRATION"
    )

    bayesian, rules, evidence = (
        load_data()
    )

    bayesian, rules, evidence = (
        validate_inputs(
            bayesian,
            rules,
            evidence
        )
    )

    evidence = prepare_evidence(
        evidence
    )

    result = merge_results(
        bayesian,
        rules,
        evidence
    )

    validation = validate_final(
        result
    )

    payload = build_json(
        result
    )

    save_outputs(
        result,
        payload,
        validation
    )

    print_section(
        "INTEGRATION COMPLETED SUCCESSFULLY"
    )

    print(
        "The final JSON is ready for the RAG layer."
    )


if __name__ == "__main__":
    main()

