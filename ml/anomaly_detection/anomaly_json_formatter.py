import json
import os
import pandas as pd


# ============================================================
# PATHS
# ============================================================

RULE_FILE = "data/anomalies/tc_puf_rule_results.csv"
EXPLAINED_FILE = "data/anomalies/tc_puf_explained.csv"
ANOMALY_FILE = "data/anomalies/tc_puf_anomalies.csv"

OUTPUT_FILE = "data/anomalies/tc_puf_anomaly_output.json"


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """Convert pandas/NumPy values into JSON-safe values."""

    if pd.isna(value):
        return None

    # Convert NumPy scalar types
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def get_value(row, column, default=None):
    """Safely get a column value from a pandas row."""

    if column not in row.index:
        return default

    value = row[column]

    if pd.isna(value):
        return default

    return clean_value(value)


def get_bool(value):
    """Convert values such as 0/1, True/False into bool."""

    if value is None:
        return False

    if isinstance(value, bool):
        return value

    try:
        return bool(int(value))
    except Exception:
        return str(value).lower() in ["true", "yes", "1"]


def split_text(value):
    """Convert a comma-separated field into a list."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    text = str(value).strip()

    if not text:
        return []

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 70)
    print("TC-PUF ANOMALY JSON FORMATTER")
    print("=" * 70)

    if not os.path.exists(ANOMALY_FILE):
        raise FileNotFoundError(
            f"Missing anomaly file: {ANOMALY_FILE}"
        )

    if not os.path.exists(EXPLAINED_FILE):
        raise FileNotFoundError(
            f"Missing explained file: {EXPLAINED_FILE}"
        )

    anomaly_df = pd.read_csv(ANOMALY_FILE)
    explained_df = pd.read_csv(EXPLAINED_FILE)

    print(f"Anomaly file shape   : {anomaly_df.shape}")
    print(f"Explained file shape : {explained_df.shape}")

    return anomaly_df, explained_df


# ============================================================
# DATASET SUMMARY
# ============================================================

def build_summary(anomaly_df):

    total_records = len(anomaly_df)

    final_anomaly = anomaly_df["final_anomaly"].fillna(0).astype(int)

    total_anomalies = int(final_anomaly.sum())

    ml_anomalies = int(
        anomaly_df["ml_anomaly"]
        .fillna(0)
        .astype(int)
        .sum()
    )

    rule_anomalies = int(
        anomaly_df["rule_anomaly"]
        .fillna(0)
        .astype(int)
        .sum()
    )

    anomaly_type_counts = (
        anomaly_df.loc[
            anomaly_df["final_anomaly"] == 1,
            "anomaly_type"
        ]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .to_dict()
    )

    severity_counts = (
        anomaly_df.loc[
            anomaly_df["final_anomaly"] == 1,
            "severity"
        ]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .to_dict()
    )

    return {
        "total_records": total_records,
        "normal_records": total_records - total_anomalies,
        "total_anomalies": total_anomalies,

        "ml_anomalies": ml_anomalies,
        "rule_anomalies": rule_anomalies,

        "anomaly_type_distribution": anomaly_type_counts,
        "severity_distribution": severity_counts
    }


# ============================================================
# BUILD ONE ANOMALY
# ============================================================

def build_anomaly(row):

    anomaly = {

        # ----------------------------------------------------
        # RECORD INFORMATION
        # ----------------------------------------------------

        "record": {
            "plan_id": get_value(row, "Plan_ID"),
            "issuer_id": get_value(row, "Issuer_ID"),
            "issuer_name": get_value(row, "Issuer_Name"),
            "state": get_value(row, "State"),
            "plan_type": get_value(row, "Plan_Type"),
            "qhp_or_sadp": get_value(row, "QHP or SADP?"),
            "metal_level": get_value(row, "Metal_Level"),
            "source_sheet": get_value(row, "source_sheet")
        },

        # ----------------------------------------------------
        # ANOMALY CLASSIFICATION
        # ----------------------------------------------------

        "anomaly": {
            "final_anomaly": get_bool(
                get_value(row, "final_anomaly")
            ),

            "anomaly_type": get_value(
                row,
                "anomaly_type"
            ),

            "severity": get_value(
                row,
                "severity"
            )
        },

        # ----------------------------------------------------
        # DETECTION
        # ----------------------------------------------------

        "detection": {

            "rule_based": {
                "detected": get_bool(
                    get_value(row, "rule_anomaly")
                ),

                "rule_name": get_value(
                    row,
                    "rule_name"
                ),

                "rule_reason": get_value(
                    row,
                    "rule_reason"
                ),

                "severity": get_value(
                    row,
                    "rule_severity"
                )
            },

            "machine_learning": {
                "detected": get_bool(
                    get_value(row, "ml_anomaly")
                ),

                "prediction": get_value(
                    row,
                    "ml_prediction"
                ),

                "anomaly_score": get_value(
                    row,
                    "ml_anomaly_score"
                )
            }
        },

        # ----------------------------------------------------
        # EXPLANATION
        # ----------------------------------------------------

        "explanation": {
            "explanation": get_value(
                row,
                "explanation"
            ),

            "likely_cause": get_value(
                row,
                "likely_cause"
            ),

            "recommended_fix": get_value(
                row,
                "recommended_fix"
            )
        }
    }

    return anomaly


# ============================================================
# MAIN
# ============================================================

def main():

    anomaly_df, explained_df = load_data()

    print()
    print("Building JSON output...")

    # --------------------------------------------------------
    # Use explained data as the main source when available.
    # --------------------------------------------------------

    if "final_anomaly" in explained_df.columns:

        anomaly_rows = explained_df[
            explained_df["final_anomaly"]
            .fillna(0)
            .astype(int)
            == 1
        ].copy()

    else:

        anomaly_rows = anomaly_df[
            anomaly_df["final_anomaly"]
            .fillna(0)
            .astype(int)
            == 1
        ].copy()

    # --------------------------------------------------------
    # Build anomaly list
    # --------------------------------------------------------

    anomalies = []

    for _, row in anomaly_rows.iterrows():

        anomaly = build_anomaly(row)

        anomalies.append(anomaly)

    # --------------------------------------------------------
    # Build complete JSON document
    # --------------------------------------------------------

    output = {

        "metadata": {
            "dataset": "TC-PUF",
            "source": "Healthcare.gov",
            "format_version": "1.0",
            "generated_by": "TC-PUF Anomaly Detection Pipeline"
        },

        "dataset_summary": build_summary(anomaly_df),

        "anomalies": anomalies
    }

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
            allow_nan=False
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        validated_json = json.load(f)

    print()
    print("=" * 70)
    print("JSON GENERATION COMPLETED")
    print("=" * 70)

    print(f"Output file       : {OUTPUT_FILE}")
    print(f"Total records     : {len(anomaly_df)}")
    print(
        f"Anomalies exported: "
        f"{len(validated_json['anomalies'])}"
    )

    print()
    print("JSON validation: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()