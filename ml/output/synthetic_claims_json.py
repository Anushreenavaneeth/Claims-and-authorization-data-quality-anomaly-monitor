
"""
Synthetic Claims - PUF-Compatible JSON Output Generator

Purpose
-------
Convert the final ML + rule-based fusion results into a JSON structure
compatible with the existing PUF anomaly-monitor output.

Pipeline position
-----------------
Preprocessing
    ->
Feature Engineering
    ->
ML Anomaly Detection
    ->
Rule-Based Detection
    ->
ML + Rule Fusion
    ->
PUF-Compatible JSON

Input files
-----------
data/processed/synthetic/fusion/synthetic_claims_fusion_results.csv
data/processed/synthetic/feature_engineering/synthetic_claims_features.csv

Output file
-----------
data/processed/synthetic/json/synthetic_claims_final_anomaly_results.json

Important
---------
This script does NOT perform anomaly detection.

It only converts the already-generated fusion results into the
standard JSON structure used by the project.

SLA monitoring is intentionally NOT included here.
"""


import json
import os
from typing import Any, Dict, List

import numpy as np
import pandas as pd


# ============================================================================
# CONFIGURATION
# ============================================================================

FUSION_FILE = (
    r".\data\processed\synthetic\fusion"
    r"\synthetic_claims_fusion_results.csv"
)

FEATURE_FILE = (
    r".\data\processed\synthetic\feature_engineering"
    r"\synthetic_claims_features.csv"
)

OUTPUT_DIR = r".\data\processed\synthetic\json"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "synthetic_claims_final_anomaly_results.json"
)


PROJECT_NAME = "TC-PUF Claims and Authorization Data Quality Anomaly Monitor"
SCHEMA_VERSION = "1.0"


# ============================================================================
# GENERAL HELPERS
# ============================================================================

def is_null(value: Any) -> bool:
    """Safely determine whether a value is null."""
    if value is None:
        return True

    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def clean_value(value: Any) -> Any:
    """
    Convert pandas/numpy values into JSON-safe Python values.
    """
    if is_null(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def get_value(
    row: pd.Series,
    column: str,
    default: Any = None
) -> Any:
    """Safely get a value from a dataframe row."""
    if column not in row.index:
        return default

    value = row[column]

    if is_null(value):
        return default

    return clean_value(value)


def get_string(
    row: pd.Series,
    column: str,
    default: str = ""
) -> str:
    """Safely return a string value."""
    value = get_value(row, column, default)

    if value is None:
        return default

    return str(value).strip()


def get_bool(
    row: pd.Series,
    column: str,
    default: bool = False
) -> bool:
    """Safely convert a value into boolean."""
    value = get_value(row, column, default)

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value == 1

    value = str(value).strip().lower()

    return value in {
        "1",
        "true",
        "yes",
        "y",
        "anomaly",
        "detected"
    }


def get_int(
    row: pd.Series,
    column: str,
    default: int = 0
) -> int:
    """Safely convert a value into integer."""
    value = get_value(row, column, default)

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def get_float(
    row: pd.Series,
    column: str,
    default: float = 0.0
) -> float:
    """Safely convert a value into float."""
    value = get_value(row, column, default)

    try:
        value = float(value)

        if np.isnan(value) or np.isinf(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


# ============================================================================
# SEVERITY
# ============================================================================

VALID_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL"
}


def normalize_severity(
    value: Any,
    anomaly: bool
) -> str:
    """
    Normalize severity.

    Critical rule:
        anomaly=False -> NORMAL

    This prevents normal records from incorrectly receiving LOW,
    MEDIUM, HIGH, or CRITICAL severity.
    """

    if not anomaly:
        return "NORMAL"

    if value is None:
        return "LOW"

    severity = str(value).strip().upper()

    if severity in VALID_SEVERITIES:
        return severity

    return "LOW"


# ============================================================================
# ANOMALY SIGNALS
# ============================================================================

def build_signal_list(row: pd.Series) -> List[str]:
    """
    Build a compact list of meaningful anomaly signals.

    Only actual ML/rule anomaly signals are included.
    Risk indicators that were intentionally excluded from the
    hard-rule anomaly decision are not independently treated as
    anomalies.
    """

    signals = []

    final_anomaly = get_bool(
        row,
        "Final_Anomaly_Flag"
    )

    if not final_anomaly:
        return signals

    detection_source = get_string(
        row,
        "Detection_Source",
        "NONE"
    ).upper()

    final_type = get_string(
        row,
        "Final_Anomaly_Type",
        "Normal"
    )

    if detection_source in {
        "ML_ONLY",
        "ML_AND_RULE"
    }:
        signals.append("ML_ANOMALY")

    if detection_source in {
        "RULE_ONLY",
        "ML_AND_RULE"
    }:
        signals.append("RULE_ANOMALY")

    if final_type and final_type != "Normal":
        if final_type not in signals:
            signals.append(final_type)

    return signals


# ============================================================================
# RULE ENGINE INFORMATION
# ============================================================================

def get_triggered_rules(row: pd.Series) -> List[str]:
    """
    Return triggered rules as a JSON list.
    """

    raw = get_string(
        row,
        "Triggered_Rules",
        ""
    )

    if not raw:
        return []

    rules = [
        item.strip()
        for item in raw.split("|")
        if item.strip()
    ]

    return rules


def get_hard_rule_names(
    triggered_rules: List[str]
) -> List[str]:
    """
    Identify the hard-rule violations.

    Risk indicators used by the rule engine are intentionally
    excluded from hard-rule counting.
    """

    risk_rules = {
        "RULE_015_PRIOR_AUTH_MISMATCH",
        "RULE_016_MEMBER_PROVIDER_STATE_MISMATCH",
        "RULE_017_PROVIDER_NOT_VERIFIED",
        "RULE_018_OUT_OF_NETWORK",
        "RULE_020_HIGH_PROCESSING_TIME",
        "RULE_021_PREPROCESSING_ANOMALY",
        "RULE_019_HIGH_SERVICE_INTENSITY"
    }

    return [
        rule
        for rule in triggered_rules
        if rule not in risk_rules
    ]


def get_rule_name(
    row: pd.Series,
    triggered_rules: List[str]
) -> str:
    """
    Return the first meaningful hard-rule name.
    """

    hard_rules = get_hard_rule_names(
        triggered_rules
    )

    if not hard_rules:
        return "NONE"

    return hard_rules[0]


def build_rule_reason(
    row: pd.Series,
    triggered_rules: List[str]
) -> str:
    """Build human-readable rule explanation."""

    hard_rules = get_hard_rule_names(
        triggered_rules
    )

    if not hard_rules:
        return "No rule violation detected"

    return "; ".join(hard_rules)


# ============================================================================
# ML EVIDENCE
# ============================================================================

def build_ml_evidence(
    row: pd.Series,
    anomaly: bool
) -> Dict[str, Any]:
    """
    Build ML evidence section.

    ML evidence is populated only when the ML model contributes
    to the final detection.
    """

    ml_flag = get_bool(
        row,
        "ML_Anomaly_Flag"
    )

    if not ml_flag:
        return {
            "evidence_count": 0,
            "severity": "",
            "types": "",
            "features": "",
            "details": "",
            "summary": ""
        }

    final_type = get_string(
        row,
        "Final_Anomaly_Type",
        "ML_Detected_Anomaly"
    )

    severity = normalize_severity(
        get_string(
            row,
            "Final_Severity",
            "LOW"
        ),
        anomaly=True
    )

    score = get_float(
        row,
        "ML_Anomaly_Score",
        0.0
    )

    normalized_score = get_float(
        row,
        "ML_Normalized_Score",
        0.0
    )

    return {
        "evidence_count": 1,
        "severity": severity,
        "types": final_type,
        "features": "",
        "details": (
            f"ML anomaly score: {score:.6f}; "
            f"normalized score: {normalized_score:.6f}"
        ),
        "summary": (
            "Machine-learning anomaly detection "
            "identified this claim as anomalous."
        )
    }


# ============================================================================
# ENTITY INFORMATION
# ============================================================================

def build_record_id(row: pd.Series) -> Dict[str, Any]:
    """Build PUF-compatible record identifier section."""

    return {
        "claim_id": get_string(
            row,
            "Claim_ID"
        ),
        "member_id": get_value(
            row,
            "Member_ID"
        ),
        "provider_id": get_value(
            row,
            "Provider_ID"
        ),
        "plan_id": get_value(
            row,
            "Plan_ID"
        ),
        "issuer_id": get_value(
            row,
            "Issuer_ID"
        )
    }


def build_entity(row: pd.Series) -> Dict[str, Any]:
    """Build PUF-compatible entity section."""

    return {
        "state": get_string(
            row,
            "State"
        ),
        "issuer_name": get_string(
            row,
            "Issuer_Name"
        ),
        "plan_type": get_string(
            row,
            "Plan_Type"
        ),
        "metal_level": get_string(
            row,
            "Metal_Level"
        ),
        "exchange_type": get_string(
            row,
            "Exchange_Type"
        ),
        "individual_or_shop": get_string(
            row,
            "Individual/SHOP"
        ),
        "provider_state": get_string(
            row,
            "Provider_State"
        ),
        "provider_network_status": get_string(
            row,
            "Provider_Network_Status"
        )
    }


# ============================================================================
# FINAL ASSESSMENT
# ============================================================================

def build_final_assessment(
    row: pd.Series
) -> Dict[str, Any]:
    """
    Build the final PUF-compatible assessment.

    Important:
        Final_Anomaly_Flag is the authoritative anomaly decision.

    Normal records ALWAYS receive:
        severity = NORMAL
        signal_count = 0
        signals = None
    """

    anomaly = get_bool(
        row,
        "Final_Anomaly_Flag"
    )

    final_severity = normalize_severity(
        get_string(
            row,
            "Final_Severity",
            "LOW"
        ),
        anomaly=anomaly
    )

    signals = build_signal_list(
        row
    )

    if not anomaly:
        return {
            "anomaly": False,
            "severity": "NORMAL",
            "signal_count": 0,
            "signals": "None"
        }

    signal_text = "|".join(
        signals
    ) if signals else "Anomaly detected"

    return {
        "anomaly": True,
        "severity": final_severity,
        "signal_count": len(signals),
        "signals": signal_text
    }


# ============================================================================
# BAYESIAN / ML SECTION
# ============================================================================

def build_bayesian(
    row: pd.Series
) -> Dict[str, Any]:
    """
    Build the Bayesian-compatible ML section.

    The existing synthetic ML model provides:
        ML_Anomaly_Score
        ML_Anomaly_Flag
        ML_Normalized_Score

    These are mapped to the same conceptual structure used by
    the PUF output.
    """

    anomaly = get_bool(
        row,
        "ML_Anomaly_Flag"
    )

    score = get_float(
        row,
        "ML_Anomaly_Score",
        0.0
    )

    probability = get_float(
        row,
        "ML_Normalized_Score",
        0.0
    )

    return {
        "anomaly": anomaly,
        "score": score,
        "probability": probability,
        "threshold": 0.0
    }


# ============================================================================
# RULE ENGINE SECTION
# ============================================================================

def build_rule_engine(
    row: pd.Series
) -> Dict[str, Any]:
    """
    Build PUF-compatible rule engine information.

    Hard_Rule_Violation_Count is used as the actual rule anomaly
    count because risk indicators are not standalone anomalies.
    """

    triggered_rules = get_triggered_rules(
        row
    )

    hard_rules = get_hard_rule_names(
        triggered_rules
    )

    hard_rule_count = len(
        hard_rules
    )

    anomaly = hard_rule_count > 0

    rule_severity = (
        normalize_severity(
            get_string(
                row,
                "Rule_Severity",
                "LOW"
            ),
            anomaly=anomaly
        )
        if anomaly
        else "NONE"
    )

    return {
        "anomaly": anomaly,
        "rule_count": hard_rule_count,
        "rule_name": get_rule_name(
            row,
            triggered_rules
        ),
        "reason": build_rule_reason(
            row,
            triggered_rules
        ),
        "severity": rule_severity
    }


# ============================================================================
# COMPLETE RECORD
# ============================================================================

def build_record(
    row: pd.Series
) -> Dict[str, Any]:
    """
    Build one complete PUF-compatible JSON record.
    """

    final_anomaly = get_bool(
        row,
        "Final_Anomaly_Flag"
    )

    return {
        "record_id": build_record_id(
            row
        ),
        "entity": build_entity(
            row
        ),
        "final_assessment": build_final_assessment(
            row
        ),
        "bayesian": build_bayesian(
            row
        ),
        "rule_engine": build_rule_engine(
            row
        ),
        "ml_evidence": build_ml_evidence(
            row,
            anomaly=final_anomaly
        )
    }


# ============================================================================
# VALIDATION
# ============================================================================

def validate_records(
    records: List[Dict[str, Any]],
    expected_count: int
) -> None:
    """
    Validate generated JSON records.
    """

    if len(records) != expected_count:
        raise ValueError(
            "Record count mismatch: "
            f"expected {expected_count}, "
            f"generated {len(records)}"
        )

    required_top_level = {
        "record_id",
        "entity",
        "final_assessment",
        "bayesian",
        "rule_engine",
        "ml_evidence"
    }

    for index, record in enumerate(records):

        missing = (
            required_top_level
            - set(record.keys())
        )

        if missing:
            raise ValueError(
                f"Record {index} is missing fields: "
                f"{sorted(missing)}"
            )

        final_assessment = record[
            "final_assessment"
        ]

        anomaly = final_assessment[
            "anomaly"
        ]

        severity = final_assessment[
            "severity"
        ]

        # Critical consistency check:
        if not anomaly and severity != "NORMAL":
            raise ValueError(
                f"Record {index} is normal but has "
                f"severity={severity}"
            )

        if anomaly and severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Record {index} is anomalous but has "
                f"invalid severity={severity}"
            )

        # Signal count consistency
        signal_count = final_assessment[
            "signal_count"
        ]

        if not anomaly and signal_count != 0:
            raise ValueError(
                f"Record {index} is normal but "
                f"signal_count={signal_count}"
            )

    # JSON serialization test
    json.dumps(
        records,
        ensure_ascii=False,
        allow_nan=False
    )


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:

    print("=" * 70)
    print(
        "SYNTHETIC CLAIMS - "
        "PUF-COMPATIBLE JSON GENERATOR"
    )
    print("=" * 70)

    # ------------------------------------------------------------------------
    # 1. Check input files
    # ------------------------------------------------------------------------

    print("\nChecking input files...")

    if not os.path.exists(FUSION_FILE):
        raise FileNotFoundError(
            f"\nFusion file not found:\n{FUSION_FILE}"
        )

    if not os.path.exists(FEATURE_FILE):
        raise FileNotFoundError(
            f"\nFeature-engineered file not found:\n{FEATURE_FILE}"
        )

    print("Fusion file       : FOUND")
    print("Feature file      : FOUND")

    # ------------------------------------------------------------------------
    # 2. Load fusion results
    # ------------------------------------------------------------------------

    print("\nLoading final fusion results...")

    fusion_df = pd.read_csv(
        FUSION_FILE
    )

    print("Fusion results loaded successfully.")
    print(
        f"Rows    : {len(fusion_df)}"
    )
    print(
        f"Columns : {len(fusion_df.columns)}"
    )

    # ------------------------------------------------------------------------
    # 3. Load feature-engineered data
    # ------------------------------------------------------------------------

    print("\nLoading feature-engineered data...")

    feature_df = pd.read_csv(
        FEATURE_FILE
    )

    print("Feature-engineered data loaded.")
    print(
        f"Rows    : {len(feature_df)}"
    )

    # ------------------------------------------------------------------------
    # 4. Validate Claim_ID
    # ------------------------------------------------------------------------

    if "Claim_ID" not in fusion_df.columns:
        raise KeyError(
            "Claim_ID is missing from fusion results."
        )

    if "Claim_ID" not in feature_df.columns:
        raise KeyError(
            "Claim_ID is missing from feature-engineered data."
        )

    # ------------------------------------------------------------------------
    # 5. Remove duplicate entity columns before merge
    # ------------------------------------------------------------------------

    entity_columns = [
        "Claim_ID",
        "Member_ID",
        "Provider_ID",
        "Plan_ID",
        "Issuer_ID",
        "State",
        "Issuer_Name",
        "Plan_Type",
        "Metal_Level",
        "Exchange_Type",
        "Individual/SHOP",
        "Provider_State",
        "Provider_Network_Status"
    ]

    available_entity_columns = [
        column
        for column in entity_columns
        if column in feature_df.columns
    ]

    entity_df = feature_df[
        available_entity_columns
    ].copy()

    # ------------------------------------------------------------------------
    # 6. Ensure one entity record per Claim_ID
    # ------------------------------------------------------------------------

    entity_df = entity_df.drop_duplicates(
        subset=["Claim_ID"],
        keep="first"
    )

    # ------------------------------------------------------------------------
    # 7. Merge entity information
    # ------------------------------------------------------------------------

    print("\nMerging entity information...")

    merged_df = fusion_df.merge(
        entity_df,
        on="Claim_ID",
        how="left",
        suffixes=("", "_entity")
    )

    if len(merged_df) != len(fusion_df):
        raise ValueError(
            "Merge changed the number of fusion records."
        )

    print(
        "Entity information merged successfully."
    )

    # ------------------------------------------------------------------------
    # 8. Generate records
    # ------------------------------------------------------------------------

    print(
        "\nGenerating PUF-compatible JSON records..."
    )

    records = []

    for _, row in merged_df.iterrows():

        record = build_record(
            row
        )

        records.append(
            record
        )

    # ------------------------------------------------------------------------
    # 9. Validate records
    # ------------------------------------------------------------------------

    print(
        "\n" + "=" * 70
    )
    print(
        "JSON VALIDATION"
    )
    print(
        "=" * 70
    )

    validate_records(
        records,
        expected_count=len(merged_df)
    )

    # ------------------------------------------------------------------------
    # 10. Calculate statistics
    # ------------------------------------------------------------------------

    anomaly_count = sum(
        1
        for record in records
        if record[
            "final_assessment"
        ][
            "anomaly"
        ]
    )

    normal_count = (
        len(records)
        - anomaly_count
    )

    anomaly_rate = (
        anomaly_count
        / len(records)
        * 100
        if records
        else 0
    )

    # ------------------------------------------------------------------------
    # 11. Build final JSON document
    # ------------------------------------------------------------------------

    output_data = {
        "project": PROJECT_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_count": len(records),
        "records": records
    }

    # ------------------------------------------------------------------------
    # 12. Create output directory
    # ------------------------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # ------------------------------------------------------------------------
    # 13. Save JSON
    # ------------------------------------------------------------------------

    print("\nSaving JSON...")

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output_data,
            file,
            indent=2,
            ensure_ascii=False,
            allow_nan=False
        )

    # ------------------------------------------------------------------------
    # 14. Reload and validate saved JSON
    # ------------------------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        validated_data = json.load(
            file
        )

    if (
        validated_data[
            "record_count"
        ]
        != len(
            validated_data[
                "records"
            ]
        )
    ):
        raise ValueError(
            "Saved JSON record_count does not "
            "match actual record count."
        )

    # ------------------------------------------------------------------------
    # 15. Print validation summary
    # ------------------------------------------------------------------------

    print(
        "\nJSON records generated : "
        f"{len(records)}"
    )

    print(
        "Final anomalies        : "
        f"{anomaly_count}"
    )

    print(
        "Final normal           : "
        f"{normal_count}"
    )

    print(
        "Anomaly rate           : "
        f"{anomaly_rate:.2f}%"
    )

    print(
        "\nJSON syntax validation : PASSED"
    )

    print(
        "PUF-compatible schema  : PASSED"
    )

    # ------------------------------------------------------------------------
    # 16. Print sample record
    # ------------------------------------------------------------------------

    print(
        "\n" + "=" * 70
    )
    print(
        "SAMPLE PUF-COMPATIBLE RECORD"
    )
    print(
        "=" * 70
    )

    if records:
        print(
            json.dumps(
                records[0],
                indent=2,
                ensure_ascii=False
            )
        )

    # ------------------------------------------------------------------------
    # 17. Final output
    # ------------------------------------------------------------------------

    print(
        "\n" + "=" * 70
    )
    print(
        "SYNTHETIC CLAIMS JSON GENERATION COMPLETED"
    )
    print(
        "=" * 70
    )

    print(
        "\nGenerated file:"
    )

    print(
        os.path.abspath(
            OUTPUT_FILE
        )
    )

    print(
        f"\nRecords written: {len(records)}"
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
