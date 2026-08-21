"""
TC-PUF CLAIMS - ISOLATION FOREST ANOMALY DETECTION

Input:
    data/processed/tc_puf_feature_engineered.csv

Output:
    data/processed/tc_puf_anomaly_results.csv
    ml/anomaly_detection/models/tc_puf_isolation_forest.joblib
    ml/anomaly_detection/models/tc_puf_scaler.joblib
    ml/anomaly_detection/models/tc_puf_features.json

Purpose:
    Detect data-quality anomalies using Isolation Forest.

Important:
    - Do not modify the feature-engineered source file.
    - Missingness is preserved through missing-value indicators.
    - IDs and non-ML fields are excluded.
    - Raw ratio features are retained as data-quality signals.
"""

from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "tc_puf_feature_engineered.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "anomaly_detection"
    / "models"
)

OUTPUT_FILE = OUTPUT_DIR / "tc_puf_anomaly_results.csv"
MODEL_FILE = MODEL_DIR / "tc_puf_isolation_forest.joblib"
SCALER_FILE = MODEL_DIR / "tc_puf_scaler.joblib"
FEATURE_FILE = MODEL_DIR / "tc_puf_features.json"


# ============================================================
# CONFIGURATION
# ============================================================

CONTAMINATION = 0.05
RANDOM_STATE = 42
N_ESTIMATORS = 500

# We do not want identifiers or descriptive fields in Isolation Forest.
EXCLUDED_EXACT = {
    "Issuer_ID",
    "Plan_ID",
    "source_sheet",
}

EXCLUDED_PATTERNS = [
    "URL",
    "Name",
    "State",
    "Type",
    "Metal_Level",
    "Individual/SHOP",
    "QHP or SADP",
    "Exchange_Type",
    "Rate_Review",
    "Financial_Information",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def is_excluded_column(column_name):
    """
    Decide whether a column should be excluded from ML.
    """

    if column_name in EXCLUDED_EXACT:
        return True

    for pattern in EXCLUDED_PATTERNS:
        if pattern.lower() in column_name.lower():
            return True

    return False


def clean_numeric_columns(df):
    """
    Convert numeric-looking columns to numeric.

    Handles:
        *, **, blank strings, and other non-numeric values.

    Values that cannot be converted become NaN.
    """

    result = df.copy()

    for col in result.columns:

        if result[col].dtype == "object":

            cleaned = (
                result[col]
                .astype(str)
                .str.strip()
                .replace(
                    {
                        "": np.nan,
                        "nan": np.nan,
                        "None": np.nan,
                        "*": np.nan,
                        "**": np.nan,
                        "N/A": np.nan,
                        "NA": np.nan,
                    }
                )
            )

            numeric = pd.to_numeric(cleaned, errors="coerce")

            # Convert only if the majority of non-null values
            # can reasonably be interpreted as numeric.
            original_non_null = cleaned.notna().sum()

            if original_non_null > 0:
                numeric_non_null = numeric.notna().sum()

                if numeric_non_null / original_non_null >= 0.80:
                    result[col] = numeric

    return result


def select_ml_features(df):
    """
    Select numeric engineered/original features for Isolation Forest.
    """

    excluded = []
    selected = []

    for col in df.columns:

        if is_excluded_column(col):
            excluded.append(col)
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            selected.append(col)

    return selected, excluded


def remove_constant_features(df):
    """
    Remove features having zero variance.
    """

    nunique = df.nunique(dropna=True)

    constant_columns = nunique[nunique <= 1].index.tolist()

    return df.drop(columns=constant_columns), constant_columns


def add_missingness_features(df):
    """
    Add explicit missingness indicators.

    Missingness itself can be a data-quality anomaly.
    """

    result = df.copy()

    missing_columns = []

    for col in df.columns:

        if df[col].isna().any():
            indicator_name = f"{col}__missing"

            result[indicator_name] = df[col].isna().astype(np.int8)

            missing_columns.append(indicator_name)

    return result, missing_columns


def classify_severity(score, lower_q, upper_q):
    """
    Convert Isolation Forest score into human-readable severity.

    Lower decision scores are more anomalous.
    """

    if score <= lower_q:
        return "HIGH"

    if score <= upper_q:
        return "MEDIUM"

    return "LOW"


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print_section("TC-PUF ISOLATION FOREST ANOMALY DETECTION")

    # --------------------------------------------------------
    # 1. Check input
    # --------------------------------------------------------

    print(f"\nInput file:\n{INPUT_FILE}")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"\nInput file not found:\n{INPUT_FILE}\n"
            "Run feature engineering first."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # 2. Load dataset
    # --------------------------------------------------------

    df_original = pd.read_csv(INPUT_FILE)

    print(f"\nDataset shape: {df_original.shape}")

    # Keep original data for final output.
    df = df_original.copy()

    # --------------------------------------------------------
    # 3. Convert numeric-looking fields
    # --------------------------------------------------------

    print_section("NUMERIC CLEANING")

    df = clean_numeric_columns(df)

    print("Numeric conversion completed.")

    # --------------------------------------------------------
    # 4. Select ML features
    # --------------------------------------------------------

    print_section("ML FEATURE SELECTION")

    feature_columns, excluded_columns = select_ml_features(df)

    print(f"Selected numeric features : {len(feature_columns)}")
    print(f"Excluded columns          : {len(excluded_columns)}")

    if len(feature_columns) == 0:
        raise ValueError(
            "No numeric ML features were found."
        )

    X = df[feature_columns].copy()

    # --------------------------------------------------------
    # 5. Remove constant features
    # --------------------------------------------------------

    X, constant_columns = remove_constant_features(X)

    feature_columns = X.columns.tolist()

    print(f"Constant features removed : {len(constant_columns)}")
    print(f"Features after filtering  : {len(feature_columns)}")

    # --------------------------------------------------------
    # 6. Add missingness indicators
    # --------------------------------------------------------

    print_section("MISSINGNESS ENGINEERING")

    X, missing_indicator_columns = add_missingness_features(X)

    print(
        f"Missingness indicators added: "
        f"{len(missing_indicator_columns)}"
    )

    # --------------------------------------------------------
    # 7. Replace infinite values
    # --------------------------------------------------------

    X = X.replace([np.inf, -np.inf], np.nan)

    infinite_count = int(
        np.isinf(X.select_dtypes(include=[np.number])).sum().sum()
    )

    print(f"Infinite values remaining: {infinite_count}")

    # --------------------------------------------------------
    # 8. Median imputation
    # --------------------------------------------------------

    print_section("MISSING VALUE IMPUTATION")

    imputer = SimpleImputer(
        strategy="median"
    )

    X_imputed = imputer.fit_transform(X)

    print(
        f"Original ML matrix shape : {X.shape}"
    )

    print(
        f"Imputed ML matrix shape  : {X_imputed.shape}"
    )

    # --------------------------------------------------------
    # 9. Robust scaling
    # --------------------------------------------------------

    print_section("ROBUST SCALING")

    scaler = RobustScaler()

    X_scaled = scaler.fit_transform(X_imputed)

    print("Robust scaling completed.")

    # --------------------------------------------------------
    # 10. Isolation Forest
    # --------------------------------------------------------

    print_section("ISOLATION FOREST")

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        bootstrap=False,
    )

    model.fit(X_scaled)

    # --------------------------------------------------------
    # 11. Predictions
    # --------------------------------------------------------

    predictions = model.predict(X_scaled)

    # sklearn:
    #  1  = normal
    # -1  = anomaly

    anomaly_label = np.where(
        predictions == -1,
        1,
        0
    )

    # Decision function:
    # larger = more normal
    # smaller = more anomalous

    decision_scores = model.decision_function(X_scaled)

    # Convert to anomaly score where:
    # larger = more anomalous

    anomaly_score = -decision_scores

    # --------------------------------------------------------
    # 12. Severity
    # --------------------------------------------------------

    low_threshold = np.quantile(
        anomaly_score,
        0.90
    )

    high_threshold = np.quantile(
        anomaly_score,
        0.95
    )

    severity = []

    for score in anomaly_score:

        if score >= high_threshold:
            severity.append("HIGH")

        elif score >= low_threshold:
            severity.append("MEDIUM")

        else:
            severity.append("LOW")

    # --------------------------------------------------------
    # 13. Build output
    # --------------------------------------------------------

    results = df_original.copy()

    results["ML_Anomaly_Label"] = anomaly_label

    results["ML_Anomaly_Score"] = anomaly_score

    results["ML_Anomaly_Severity"] = severity

    results["ML_Is_Anomaly"] = (
        results["ML_Anomaly_Label"] == 1
    )

    # --------------------------------------------------------
    # 14. Save model artifacts
    # --------------------------------------------------------

    joblib.dump(
        model,
        MODEL_FILE
    )

    joblib.dump(
        scaler,
        SCALER_FILE
    )

    joblib.dump(
        imputer,
        MODEL_DIR / "tc_puf_imputer.joblib"
    )

    feature_metadata = {
        "input_file": str(INPUT_FILE),
        "original_columns": int(df_original.shape[1]),
        "original_rows": int(df_original.shape[0]),
        "selected_features": feature_columns,
        "missing_indicator_features": missing_indicator_columns,
        "constant_features_removed": constant_columns,
        "excluded_columns": excluded_columns,
        "contamination": CONTAMINATION,
        "n_estimators": N_ESTIMATORS,
        "random_state": RANDOM_STATE,
    }

    with open(
        FEATURE_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            feature_metadata,
            f,
            indent=2
        )

    # --------------------------------------------------------
    # 15. Save results
    # --------------------------------------------------------

    results.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # 16. Validation report
    # --------------------------------------------------------

    print_section("ANOMALY DETECTION REPORT")

    total = len(results)

    anomalies = int(
        results["ML_Is_Anomaly"].sum()
    )

    anomaly_percentage = (
        anomalies / total * 100
    )

    print(f"Total records          : {total:,}")
    print(f"Anomalies              : {anomalies:,}")
    print(
        f"Anomaly percentage     : "
        f"{anomaly_percentage:.2f}%"
    )

    print(
        f"\nAnomaly threshold "
        f"(90th percentile): {low_threshold:.6f}"
    )

    print(
        f"High severity threshold "
        f"(95th percentile): {high_threshold:.6f}"
    )

    print("\nSeverity distribution:")

    print(
        results["ML_Anomaly_Severity"]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # 17. Show top anomalies
    # --------------------------------------------------------

    print_section("TOP 20 ANOMALIES")

    top_anomalies = (
        results[
            results["ML_Is_Anomaly"]
        ]
        .sort_values(
            "ML_Anomaly_Score",
            ascending=False
        )
        .head(20)
    )

    display_columns = [
        c for c in [
            "Plan_ID",
            "Issuer_ID",
            "State",
            "ML_Anomaly_Score",
            "ML_Anomaly_Severity",
        ]
        if c in top_anomalies.columns
    ]

    if len(top_anomalies) > 0:

        print(
            top_anomalies[
                display_columns
            ].to_string(index=False)
        )

    else:

        print("No anomalies detected.")

    # --------------------------------------------------------
    # 18. Save metadata
    # --------------------------------------------------------

    print_section("OUTPUT FILES")

    print(
        f"Anomaly results:\n{OUTPUT_FILE}"
    )

    print(
        f"Isolation Forest model:\n{MODEL_FILE}"
    )

    print(
        f"Scaler:\n{SCALER_FILE}"
    )

    print(
        f"Imputer:\n"
        f"{MODEL_DIR / 'tc_puf_imputer.joblib'}"
    )

    print(
        f"Feature metadata:\n{FEATURE_FILE}"
    )

    print_section("ISOLATION FOREST COMPLETED")


if __name__ == "__main__":
    main()