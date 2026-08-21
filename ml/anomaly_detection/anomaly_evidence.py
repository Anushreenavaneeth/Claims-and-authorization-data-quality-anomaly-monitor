"""
TC-PUF ANOMALY EVIDENCE GENERATOR
----------------------------------

Purpose:
    Generate human-readable evidence for ML-detected anomalies.

Input:
    data/processed/tc_puf_feature_engineered.csv
    data/processed/tc_puf_anomaly_results.csv

Output:
    data/processed/tc_puf_anomaly_evidence.csv
    data/processed/tc_puf_anomaly_evidence.json

Important:
    - Does NOT modify the ML anomaly scores.
    - Does NOT change which records are anomalies.
    - Only improves evidence generation and explanation.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "tc_puf_feature_engineered.csv"
)

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "tc_puf_anomaly_results.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "data"
    / "processed"
    / "tc_puf_anomaly_evidence.csv"
)

OUTPUT_JSON = (
    BASE_DIR
    / "data"
    / "processed"
    / "tc_puf_anomaly_evidence.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

ID_COLUMNS = [
    "Plan_ID",
    "Issuer_ID",
    "State",
    "Issuer_Name",
    "Plan_Type",
    "Metal_Level",
    "Exchange_Type",
    "Individual/SHOP",
]

RATE_COLUMNS = [
    "Issuer_In_Network_Denial_Rate",
    "Issuer_Out_of_Network_Denial_Rate",
    "Issuer_Overall_Denial_Rate",
    "Plan_In_Network_Denial_Rate",
    "Plan_Out_of_Network_Denial_Rate",
    "Plan_Overall_Denial_Rate",
    "Issuer_In_Network_Resubmission_Rate",
    "Issuer_Out_of_Network_Resubmission_Rate",
    "Issuer_Overall_Resubmission_Rate",
    "Plan_In_Network_Resubmission_Rate",
    "Plan_Out_of_Network_Resubmission_Rate",
    "Plan_Overall_Resubmission_Rate",
    "Internal_Appeal_Overturn_Rate",
    "External_Appeal_Overturn_Rate",
    "Overall_Appeal_Overturn_Rate",
    "Referral_Required_Denial_Rate",
    "Out_of_Network_Denial_Rate",
    "Services_Excluded_Denial_Rate",
    "Medical_Necessity_Denial_Rate",
    "Behavioral_Health_Medical_Necessity_Denial_Rate",
    "Benefit_Limit_Denial_Rate",
    "Member_Not_Covered_Denial_Rate",
    "Investigational_Experimental_Cosmetic_Denial_Rate",
    "Administrative_Denial_Rate",
    "Other_Denial_Rate",
    "Disenrollment_Rate",
]

IMPORTANT_MISSINGNESS_COLUMNS = [
    "Total_Important_Missing_Count",
    "Important_Missing_Rate",
    "Issuer_Claims_Missing_Count",
    "Plan_Claims_Missing_Count",
    "Appeal_Data_Missing_Count",
    "Enrollment_Data_Missing_Count",
]

QUALITY_FLAG_COLUMNS = [
    "Plan_Denied_Exceeds_Received",
    "Issuer_Denied_Exceeds_Received",
    "Plan_Resubmitted_Exceeds_Received",
    "Issuer_Resubmitted_Exceeds_Received",
    "Internal_Overturned_Exceeds_Appeals",
    "External_Overturned_Exceeds_Appeals",
]

INVALID_FLAG_COLUMNS = [
    c
    for c in RATE_COLUMNS
]

# ============================================================
# HELPERS
# ============================================================


def is_valid_number(value):
    return (
        value is not None
        and not pd.isna(value)
        and np.isfinite(value)
    )


def safe_float(value):
    try:
        value = float(value)

        if np.isfinite(value):
            return value

    except Exception:
        pass

    return None


def format_value(value):
    numeric = safe_float(value)

    if numeric is not None:

        if abs(numeric) >= 1000:
            return f"{numeric:,.2f}"

        if abs(numeric) >= 1:
            return f"{numeric:.3f}"

        return f"{numeric:.4f}"

    return str(value)


def clean_text(value):
    if value is None or pd.isna(value):
        return ""

    return str(value).strip()


def percentile_rank(series, value):

    numeric = pd.to_numeric(series, errors="coerce").dropna()

    if numeric.empty or not is_valid_number(value):
        return None

    return float((numeric <= value).mean() * 100)


def feature_label(feature):

    replacements = {
        "_": " ",
        "Rate": "Rate",
        "Denial": "Denial",
        "Resubmission": "Resubmission",
        "Appeal": "Appeal",
        "Claims": "Claims",
        "Enrollee": "Enrollee",
    }

    text = feature

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ============================================================
# LOAD DATA
# ============================================================


def load_data():

    print("=" * 70)
    print("TC-PUF ANOMALY EVIDENCE GENERATOR")
    print("=" * 70)

    print("\nFeature file:")
    print(FEATURE_FILE)

    print("\nAnomaly file:")
    print(ANOMALY_FILE)

    if not FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Feature file not found:\n{FEATURE_FILE}"
        )

    if not ANOMALY_FILE.exists():
        raise FileNotFoundError(
            f"Anomaly file not found:\n{ANOMALY_FILE}"
        )

    feature_df = pd.read_csv(FEATURE_FILE, low_memory=False)
    anomaly_df = pd.read_csv(ANOMALY_FILE, low_memory=False)

    print("\nFeature dataset shape :", feature_df.shape)
    print("Anomaly dataset shape :", anomaly_df.shape)

    return feature_df, anomaly_df


# ============================================================
# IDENTIFY ANOMALIES
# ============================================================


def identify_anomalies(anomaly_df):

    print("\n" + "=" * 70)
    print("IDENTIFYING ANOMALIES")
    print("=" * 70)

    flag_candidates = [
        "ML_Is_Anomaly",
        "is_anomaly",
        "Anomaly",
        "anomaly",
        "ML_Anomaly",
    ]

    score_candidates = [
        "ML_Anomaly_Score",
        "anomaly_score",
        "Anomaly_Score",
    ]

    severity_candidates = [
        "ML_Anomaly_Severity",
        "anomaly_severity",
        "Severity",
    ]

    flag_column = next(
        (c for c in flag_candidates if c in anomaly_df.columns),
        None,
    )

    score_column = next(
        (c for c in score_candidates if c in anomaly_df.columns),
        None,
    )

    severity_column = next(
        (c for c in severity_candidates if c in anomaly_df.columns),
        None,
    )

    if flag_column is None:
        raise ValueError(
            "Could not find anomaly flag column.\n"
            f"Available columns: {list(anomaly_df.columns)}"
        )

    if score_column is None:
        raise ValueError(
            "Could not find anomaly score column."
        )

    if severity_column is None:
        raise ValueError(
            "Could not find anomaly severity column."
        )

    print("Anomaly flag column :", flag_column)
    print("Score column        :", score_column)
    print("Severity column     :", severity_column)

    anomaly_flag = (
        anomaly_df[flag_column]
        .astype(str)
        .str.lower()
        .isin(["1", "true", "yes", "anomaly"])
    )

    result = anomaly_df.loc[anomaly_flag].copy()

    print("Anomalies found     :", len(result))
    print("Normal records      :", len(anomaly_df) - len(result))

    return result, flag_column, score_column, severity_column


# ============================================================
# GENERATE EVIDENCE
# ============================================================


def generate_evidence(feature_df, anomaly_df):

    print("\nGenerating evidence...")

    evidence_rows = []

    # --------------------------------------------------------
    # Dataset-wide percentile statistics
    # --------------------------------------------------------

    percentile_cache = {}

    for column in RATE_COLUMNS:

        if column not in feature_df.columns:
            continue

        numeric = pd.to_numeric(
            feature_df[column],
            errors="coerce",
        )

        percentile_cache[column] = {
            "p01": numeric.quantile(0.01),
            "p05": numeric.quantile(0.05),
            "p95": numeric.quantile(0.95),
            "p99": numeric.quantile(0.99),
        }

    # --------------------------------------------------------
    # Process every anomaly
    # --------------------------------------------------------

    for idx, row in anomaly_df.iterrows():

        evidence = []

        # ====================================================
        # 1. DATA QUALITY FLAGS
        # ====================================================

        for column in QUALITY_FLAG_COLUMNS:

            if column not in feature_df.columns:
                continue

            value = row.get(column)

            if safe_float(value) == 1:

                evidence.append({
                    "type": "DATA_QUALITY_FLAG",
                    "feature": column,
                    "message": (
                        f"{feature_label(column)} is triggered."
                    ),
                    "value": 1,
                })

        # ====================================================
        # 2. MISSINGNESS
        # ====================================================

        missing_count = safe_float(
            row.get("Total_Important_Missing_Count")
        )

        missing_rate = safe_float(
            row.get("Important_Missing_Rate")
        )

        if (
            missing_count is not None
            and missing_count > 0
        ):

            evidence.append({
                "type": "MISSINGNESS",
                "feature": "Total_Important_Missing_Count",
                "message": (
                    f"{int(round(missing_count))} important "
                    f"data fields are missing or unavailable."
                ),
                "value": missing_count,
            })

        if (
            missing_rate is not None
            and missing_rate >= 0.25
        ):

            evidence.append({
                "type": "MISSINGNESS",
                "feature": "Important_Missing_Rate",
                "message": (
                    f"Important missingness rate is "
                    f"{missing_rate:.1%}."
                ),
                "value": missing_rate,
            })

        # ====================================================
        # 3. EXTREME VALUES
        # ====================================================

        for column in RATE_COLUMNS:

            if column not in feature_df.columns:
                continue

            value = safe_float(row.get(column))

            if value is None:
                continue

            stats = percentile_cache.get(column)

            if not stats:
                continue

            p01 = safe_float(stats["p01"])
            p05 = safe_float(stats["p05"])
            p95 = safe_float(stats["p95"])
            p99 = safe_float(stats["p99"])

            # ----------------------------------------------
            # Extreme HIGH
            # ----------------------------------------------

            if (
                p99 is not None
                and value > p99
            ):

                evidence.append({
                    "type": "EXTREME_HIGH",
                    "feature": column,
                    "message": (
                        f"{feature_label(column)} = "
                        f"{format_value(value)}, "
                        f"above the dataset 99th percentile "
                        f"({format_value(p99)})."
                    ),
                    "value": value,
                    "threshold": p99,
                })

            # ----------------------------------------------
            # Extreme LOW
            # ----------------------------------------------

            elif (
                p01 is not None
                and value < p01
            ):

                evidence.append({
                    "type": "EXTREME_LOW",
                    "feature": column,
                    "message": (
                        f"{feature_label(column)} = "
                        f"{format_value(value)}, "
                        f"below the dataset 1st percentile "
                        f"({format_value(p01)})."
                    ),
                    "value": value,
                    "threshold": p01,
                })

        # ====================================================
        # 4. INVALID / NON-NORMAL RATE FLAGS
        # ====================================================

        for column in RATE_COLUMNS:

            flag_column = column + "_Invalid_Flag"

            if flag_column not in feature_df.columns:
                continue

            flag = safe_float(row.get(flag_column))

            if flag == 1:

                evidence.append({
                    "type": "DATA_QUALITY_FLAG",
                    "feature": flag_column,
                    "message": (
                        f"{feature_label(column)} contains "
                        f"an invalid raw value."
                    ),
                    "value": 1,
                })

        # ====================================================
        # 5. DEDUPLICATE EVIDENCE
        # ====================================================

        unique_evidence = []

        seen = set()

        for item in evidence:

            key = (
                item["type"],
                item["feature"],
                item["message"],
            )

            if key not in seen:

                seen.add(key)
                unique_evidence.append(item)

        evidence = unique_evidence

        # ====================================================
        # 6. EVIDENCE SEVERITY
        # ====================================================

        evidence_types = {
            item["type"]
            for item in evidence
        }

        if "DATA_QUALITY_FLAG" in evidence_types:

            evidence_severity = "HIGH"

        elif "EXTREME_HIGH" in evidence_types:

            evidence_severity = "HIGH"

        elif "EXTREME_LOW" in evidence_types:

            evidence_severity = "MEDIUM"

        elif "MISSINGNESS" in evidence_types:

            evidence_severity = "MEDIUM"

        else:

            evidence_severity = "LOW"

        # ====================================================
        # 7. BUILD CLEAN SUMMARY
        # ====================================================

        messages = [
            item["message"]
            for item in evidence
        ]

        # Keep summary concise.
        max_summary_items = 5

        summary_items = messages[:max_summary_items]

        if len(messages) > max_summary_items:

            summary_items.append(
                f"{len(messages) - max_summary_items} additional "
                f"evidence item(s)."
            )

        summary = " ".join(summary_items)

        # ====================================================
        # 8. EVIDENCE TYPE COUNTS
        # ====================================================

        type_counts = {}

        for item in evidence:

            evidence_type = item["type"]

            type_counts[evidence_type] = (
                type_counts.get(evidence_type, 0) + 1
            )

        # ====================================================
        # 9. EVIDENCE FEATURE LIST
        # ====================================================

        evidence_features = [
            item["feature"]
            for item in evidence
        ]

        # ====================================================
        # 10. OUTPUT RECORD
        # ====================================================

        output = {}

        for column in ID_COLUMNS:

            if column in row.index:
                output[column] = row[column]

        output["ML_Anomaly_Score"] = row.get(
            "ML_Anomaly_Score"
        )

        output["ML_Anomaly_Severity"] = row.get(
            "ML_Anomaly_Severity"
        )

        output["Evidence_Count"] = len(evidence)

        output["Evidence_Severity"] = evidence_severity

        output["Evidence_Types"] = json.dumps(
            type_counts,
            ensure_ascii=False,
        )

        output["Evidence_Features"] = json.dumps(
            evidence_features,
            ensure_ascii=False,
        )

        output["Evidence_Details"] = json.dumps(
            evidence,
            ensure_ascii=False,
        )

        output["Evidence_Summary"] = summary

        evidence_rows.append(output)

    return evidence_rows


# ============================================================
# SAVE OUTPUT
# ============================================================


def save_outputs(evidence_rows):

    result_df = pd.DataFrame(evidence_rows)

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    json_records = []

    for record in evidence_rows:

        cleaned = {}

        for key, value in record.items():

            if pd.isna(value):

                cleaned[key] = None

            elif isinstance(value, np.generic):

                cleaned[key] = value.item()

            else:

                cleaned[key] = value

        json_records.append(cleaned)

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            json_records,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return result_df


# ============================================================
# REPORT
# ============================================================


def print_report(result_df):

    print("\n" + "=" * 70)
    print("EVIDENCE REPORT")
    print("=" * 70)

    print(
        f"\nAnomalies analyzed : {len(result_df):,}"
    )

    if result_df.empty:

        print("\nNo anomalies found.")
        return

    print("\nEvidence severity:")

    print(
        result_df["Evidence_Severity"]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # Evidence type frequency
    # --------------------------------------------------------

    type_counter = {}

    for value in result_df["Evidence_Types"]:

        try:

            parsed = json.loads(value)

            for evidence_type, count in parsed.items():

                type_counter[evidence_type] = (
                    type_counter.get(evidence_type, 0)
                    + int(count)
                )

        except Exception:
            pass

    if type_counter:

        print("\nEvidence type frequency:")

        for evidence_type, count in sorted(
            type_counter.items(),
            key=lambda x: x[1],
            reverse=True,
        ):

            print(
                f"{evidence_type:<25} {count}"
            )

    # --------------------------------------------------------
    # Top anomalies
    # --------------------------------------------------------

    print("\nTop anomalies with evidence:")

    display_columns = [
        "Plan_ID",
        "Issuer_ID",
        "State",
        "ML_Anomaly_Score",
        "ML_Anomaly_Severity",
        "Evidence_Severity",
        "Evidence_Count",
        "Evidence_Summary",
    ]

    display_columns = [
        c for c in display_columns
        if c in result_df.columns
    ]

    top = (
        result_df
        .sort_values(
            by=[
                "Evidence_Count",
                "ML_Anomaly_Score",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(20)
    )

    print(
        top[display_columns]
        .to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================


def main():

    feature_df, anomaly_results = load_data()

    anomaly_df, _, _, _ = identify_anomalies(
        anomaly_results
    )

    evidence_rows = generate_evidence(
        feature_df,
        anomaly_df,
    )

    result_df = save_outputs(
        evidence_rows
    )

    print_report(result_df)

    print("\n" + "=" * 70)
    print("OUTPUT FILES")
    print("=" * 70)

    print("\nCSV:")
    print(OUTPUT_CSV)

    print("\nJSON:")
    print(OUTPUT_JSON)

    print("\n" + "=" * 70)
    print("ANOMALY EVIDENCE GENERATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()