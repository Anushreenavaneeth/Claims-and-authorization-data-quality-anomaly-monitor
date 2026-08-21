"""
TC-PUF Bayesian Anomaly Detection
=================================

Unsupervised Bayesian-style anomaly detection using a
multivariate Gaussian model.

IMPORTANT:
- Does NOT use Statistical_Anomaly.
- Does NOT use Actual_Anomaly.
- Does NOT use ML predictions.
- Does NOT use rule-engine outputs.
- Does NOT train on the test/evaluation labels.

Input:
    data/processed/tc_puf_feature_engineered.csv

Outputs:
    data/processed/tc_puf_bayesian_results.csv
    data/processed/tc_puf_bayesian_evaluation_summary.csv
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import LedoitWolf
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

INPUT_FILE = PROCESSED_DIR / "tc_puf_feature_engineered.csv"

OUTPUT_FILE = (
    PROCESSED_DIR /
    "tc_puf_bayesian_results.csv"
)

EVALUATION_FILE = (
    PROCESSED_DIR /
    "tc_puf_bayesian_evaluation_summary.csv"
)

RANDOM_STATE = 42

# Percentage of observations treated as anomalies.
# 5% is a reasonable starting point for a data-quality
# anomaly monitoring system.
ANOMALY_PERCENTILE = 95.0

# Remove features with >=98% missing values.
SPARSE_THRESHOLD = 0.98

# Remove highly correlated duplicate-information features.
CORRELATION_THRESHOLD = 0.95

# Small regularization value for numerical stability.
COVARIANCE_REGULARIZATION = 1e-6


# ============================================================
# LOGGING
# ============================================================

def print_section(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print_section("LOADING FEATURE-ENGINEERED DATA")

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"""
Feature-engineered input file not found:

{INPUT_FILE}

Please run feature engineering first.
"""
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Input file : {INPUT_FILE}")
    print(f"Shape      : {df.shape}")

    if df.empty:

        raise ValueError(
            "Input dataset is empty."
        )

    return df


# ============================================================
# SELECT NUMERIC FEATURES
# ============================================================

def select_numeric_features(df):

    print_section("SELECTING NUMERIC FEATURES")

    # Columns that must NEVER be predictors.
    forbidden_columns = {

        # Target/anomaly columns
        "Actual_Anomaly",
        "Statistical_Anomaly",
        "Predicted_Anomaly",
        "Anomaly_Probability",

        "Bayesian_Anomaly",
        "Bayesian_Anomaly_Probability",

        # Rule-engine outputs
        "rule_anomaly",
        "rule_count",
        "rule_name",
        "rule_reason",
        "rule_severity",

        # Identifiers / metadata
        "Plan_ID",
        "Issuer_ID",
    }

    numeric_columns = df.select_dtypes(
        include=[np.number]
    ).columns.tolist()

    candidate_columns = []

    for col in numeric_columns:

        if col in forbidden_columns:
            continue

        col_lower = col.lower()

        # Prevent accidental target leakage.
        forbidden_keywords = [
            "actual_anomaly",
            "statistical_anomaly",
            "predicted_anomaly",
            "anomaly_probability",
            "bayesian_anomaly",
            "rule_anomaly",
            "rule_count",
            "rule_severity",
        ]

        if any(
            keyword in col_lower
            for keyword in forbidden_keywords
        ):
            continue

        candidate_columns.append(col)

    if not candidate_columns:

        raise ValueError(
            "No usable numeric predictor features were found."
        )

    print(
        f"Numeric candidate features: "
        f"{len(candidate_columns)}"
    )

    return candidate_columns


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

def clean_numeric_data(df, columns):

    print_section("CLEANING NUMERIC FEATURES")

    X = df[columns].copy()

    for col in X.columns:

        X[col] = pd.to_numeric(
            X[col],
            errors="coerce"
        )

    # Replace infinite values.
    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # Remove extremely sparse columns.
    missing_rate = X.isna().mean()

    keep_columns = missing_rate[
        missing_rate < SPARSE_THRESHOLD
    ].index.tolist()

    removed_sparse = (
        len(X.columns) -
        len(keep_columns)
    )

    X = X[keep_columns]

    print(
        f"Removed sparse features: "
        f"{removed_sparse}"
    )

    # Remove columns with no variance.
    non_constant = [
        col
        for col in X.columns
        if X[col].nunique(dropna=True) > 1
    ]

    removed_constant = (
        len(X.columns) -
        len(non_constant)
    )

    X = X[non_constant]

    print(
        f"Removed constant features: "
        f"{removed_constant}"
    )

    if X.shape[1] == 0:

        raise ValueError(
            "No usable numeric features remain."
        )

    print(
        f"Features before correlation filtering: "
        f"{X.shape[1]}"
    )

    return X


# ============================================================
# IMPUTE AND SCALE
# ============================================================

def impute_and_scale(X):

    print_section("IMPUTATION AND STANDARDIZATION")

    imputer = SimpleImputer(
        strategy="median",
        add_indicator=False
    )

    X_imputed = imputer.fit_transform(X)

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X_imputed
    )

    X_scaled = pd.DataFrame(
        X_scaled,
        columns=X.columns,
        index=X.index
    )

    print(
        f"Imputed matrix shape: "
        f"{X_scaled.shape}"
    )

    return X_scaled, imputer, scaler


# ============================================================
# CORRELATION REDUCTION
# ============================================================

def remove_highly_correlated_features(X):

    print_section(
        "CORRELATION-BASED FEATURE REDUCTION"
    )

    if X.shape[1] <= 1:

        return X, list(X.columns)

    correlation_matrix = X.corr().abs()

    upper_triangle = correlation_matrix.where(
        np.triu(
            np.ones(
                correlation_matrix.shape
            ),
            k=1
        ).astype(bool)
    )

    columns_to_drop = [
        column
        for column in upper_triangle.columns
        if any(
            upper_triangle[column] >
            CORRELATION_THRESHOLD
        )
    ]

    X_reduced = X.drop(
        columns=columns_to_drop
    )

    print(
        f"Correlation threshold: "
        f"{CORRELATION_THRESHOLD}"
    )

    print(
        f"Removed highly correlated features: "
        f"{len(columns_to_drop)}"
    )

    print(
        f"Final Bayesian feature count: "
        f"{X_reduced.shape[1]}"
    )

    if X_reduced.shape[1] == 0:

        raise ValueError(
            "Correlation filtering removed all features."
        )

    return (
        X_reduced,
        list(X_reduced.columns)
    )


# ============================================================
# FIT GAUSSIAN MODEL
# ============================================================

def fit_gaussian_model(X):

    print_section(
        "FITTING BAYESIAN GAUSSIAN MODEL"
    )

    X_values = X.values

    # Ledoit-Wolf covariance shrinkage gives a
    # numerically stable covariance estimate.
    covariance_estimator = LedoitWolf(
        assume_centered=False
    )

    covariance_estimator.fit(
        X_values
    )

    mean_vector = (
        covariance_estimator.location_
    )

    covariance_matrix = (
        covariance_estimator.covariance_
    )

    # Additional numerical regularization.
    covariance_matrix = (
        covariance_matrix +
        np.eye(
            covariance_matrix.shape[0]
        ) *
        COVARIANCE_REGULARIZATION
    )

    print(
        f"Gaussian dimensions: "
        f"{len(mean_vector)}"
    )

    print(
        "Covariance estimator: "
        "Ledoit-Wolf shrinkage"
    )

    return (
        mean_vector,
        covariance_matrix
    )


# ============================================================
# MAHALANOBIS / GAUSSIAN ANOMALY SCORE
# ============================================================

def calculate_anomaly_scores(
    X,
    mean_vector,
    covariance_matrix
):

    print_section(
        "CALCULATING BAYESIAN ANOMALY SCORES"
    )

    X_values = X.values

    centered = (
        X_values -
        mean_vector
    )

    # Solve:
    #
    # covariance * solution = centered.T
    #
    # This is more numerically stable than
    # explicitly calculating covariance inverse.

    try:

        solved = np.linalg.solve(
            covariance_matrix,
            centered.T
        )

    except np.linalg.LinAlgError:

        covariance_matrix = (
            covariance_matrix +
            np.eye(
                covariance_matrix.shape[0]
            ) * 1e-4
        )

        solved = np.linalg.solve(
            covariance_matrix,
            centered.T
        )

    mahalanobis_squared = np.sum(
        centered.T * solved,
        axis=0
    )

    # Larger Mahalanobis distance =
    # lower Gaussian probability =
    # stronger anomaly evidence.
    anomaly_score = np.asarray(
        mahalanobis_squared,
        dtype=float
    )

    # Guard against numerical problems.
    anomaly_score = np.nan_to_num(
        anomaly_score,
        nan=0.0,
        posinf=np.finfo(float).max,
        neginf=0.0
    )

    return anomaly_score


# ============================================================
# CONVERT SCORE TO PROBABILITY-LIKE VALUE
# ============================================================

def score_to_probability(scores):

    """
    Convert anomaly score into a bounded
    anomaly probability-like score.

    This is NOT a supervised class probability.

    It is a normalized anomaly confidence score.
    """

    scores = np.asarray(
        scores,
        dtype=float
    )

    minimum = np.min(scores)
    maximum = np.max(scores)

    if maximum <= minimum:

        return np.zeros_like(
            scores,
            dtype=float
        )

    normalized = (
        (scores - minimum) /
        (maximum - minimum)
    )

    return np.clip(
        normalized,
        0.0,
        1.0
    )


# ============================================================
# DETERMINE THRESHOLD
# ============================================================

def determine_threshold(scores):

    print_section(
        "DETERMINING BAYESIAN ANOMALY THRESHOLD"
    )

    threshold = np.percentile(
        scores,
        ANOMALY_PERCENTILE
    )

    print(
        f"Anomaly percentile: "
        f"{ANOMALY_PERCENTILE}"
    )

    print(
        f"Anomaly score threshold: "
        f"{threshold:.6f}"
    )

    return float(threshold)


# ============================================================
# CREATE OUTPUT
# ============================================================

def create_output(
    df,
    scores,
    probabilities,
    threshold,
    feature_columns
):

    result = df.copy()

    result[
        "Bayesian_Anomaly_Score"
    ] = scores

    result[
        "Bayesian_Anomaly_Probability"
    ] = probabilities

    result[
        "Bayesian_Threshold"
    ] = threshold

    result[
        "Bayesian_Anomaly"
    ] = (
        result[
            "Bayesian_Anomaly_Score"
        ] >= threshold
    ).astype(int)

    result[
        "Bayesian_Model"
    ] = (
        "Multivariate_Gaussian_"
        "Ledoit_Wolf"
    )

    result[
        "Bayesian_Feature_Count"
    ] = len(feature_columns)

    return result


# ============================================================
# OPTIONAL EVALUATION
# ============================================================

def evaluate_if_ground_truth_exists(result):

    print_section(
        "OPTIONAL BAYESIAN EVALUATION"
    )

    if "Actual_Anomaly" not in result.columns:

        print(
            "No Actual_Anomaly column found."
        )

        print(
            "Bayesian model remains fully "
            "unsupervised."
        )

        return None

    y_true = pd.to_numeric(
        result["Actual_Anomaly"],
        errors="coerce"
    )

    valid = y_true.notna()

    y_true = y_true[
        valid
    ].astype(int)

    y_pred = result.loc[
        valid,
        "Bayesian_Anomaly"
    ].astype(int)

    y_score = result.loc[
        valid,
        "Bayesian_Anomaly_Probability"
    ].astype(float)

    if not set(
        y_true.unique()
    ).issubset({0, 1}):

        print(
            "Actual_Anomaly is not binary. "
            "Skipping evaluation."
        )

        return None

    print(
        classification_report(
            y_true,
            y_pred,
            digits=4,
            zero_division=0
        )
    )

    print(
        "Confusion matrix:"
    )

    print(
        confusion_matrix(
            y_true,
            y_pred
        )
    )

    if len(
        np.unique(y_true)
    ) == 2:

        auc = roc_auc_score(
            y_true,
            y_score
        )

        print(
            f"ROC-AUC: {auc:.4f}"
        )

    else:

        auc = np.nan

        print(
            "ROC-AUC unavailable because "
            "only one class is present."
        )

    summary = pd.DataFrame(
        {
            "Metric": [
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
                "ROC_AUC",
            ],
            "Value": [
                np.mean(
                    y_true.values ==
                    y_pred.values
                ),
                precision_score(
                    y_true,
                    y_pred,
                    zero_division=0
                ),
                recall_score(
                    y_true,
                    y_pred,
                    zero_division=0
                ),
                f1_score(
                    y_true,
                    y_pred,
                    zero_division=0
                ),
                auc,
            ],
        }
    )

    return summary


# ============================================================
# MAIN
# ============================================================

def main():

    print_section(
        "TC-PUF FINAL BAYESIAN ANOMALY DETECTION"
    )

    # --------------------------------------------------------
    # 1. Load feature-engineered data
    # --------------------------------------------------------

    df = load_data()

    # --------------------------------------------------------
    # 2. Select safe numeric predictors
    # --------------------------------------------------------

    candidate_columns = (
        select_numeric_features(df)
    )

    X = clean_numeric_data(
        df,
        candidate_columns
    )

    # --------------------------------------------------------
    # 3. Impute and scale
    # --------------------------------------------------------

    X_scaled, imputer, scaler = (
        impute_and_scale(X)
    )

    # --------------------------------------------------------
    # 4. Remove highly correlated features
    # --------------------------------------------------------

    X_final, feature_columns = (
        remove_highly_correlated_features(
            X_scaled
        )
    )

    # --------------------------------------------------------
    # 5. Fit Gaussian model
    # --------------------------------------------------------

    (
        mean_vector,
        covariance_matrix
    ) = fit_gaussian_model(
        X_final
    )

    # --------------------------------------------------------
    # 6. Calculate anomaly scores
    # --------------------------------------------------------

    anomaly_scores = (
        calculate_anomaly_scores(
            X_final,
            mean_vector,
            covariance_matrix
        )
    )

    # --------------------------------------------------------
    # 7. Convert scores to probability-like confidence
    # --------------------------------------------------------

    anomaly_probabilities = (
        score_to_probability(
            anomaly_scores
        )
    )

    # --------------------------------------------------------
    # 8. Determine threshold
    # --------------------------------------------------------

    threshold = determine_threshold(
        anomaly_scores
    )

    # --------------------------------------------------------
    # 9. Create output
    # --------------------------------------------------------

    result_df = create_output(
        df=df,
        scores=anomaly_scores,
        probabilities=anomaly_probabilities,
        threshold=threshold,
        feature_columns=feature_columns
    )

    # --------------------------------------------------------
    # 10. Print prediction distribution
    # --------------------------------------------------------

    print_section(
        "BAYESIAN PREDICTION SUMMARY"
    )

    print(
        result_df[
            "Bayesian_Anomaly"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    anomaly_count = int(
        result_df[
            "Bayesian_Anomaly"
        ].sum()
    )

    anomaly_percentage = (
        anomaly_count /
        len(result_df) *
        100
    )

    print()
    print(
        f"Total records: {len(result_df)}"
    )

    print(
        f"Bayesian anomalies: "
        f"{anomaly_count}"
    )

    print(
        f"Bayesian anomaly percentage: "
        f"{anomaly_percentage:.2f}%"
    )

    print()

    print(
        "Bayesian probability-like score:"
    )

    print(
        result_df[
            "Bayesian_Anomaly_Probability"
        ].describe().to_string()
    )

    # --------------------------------------------------------
    # 11. Optional evaluation
    # --------------------------------------------------------

    evaluation_summary = (
        evaluate_if_ground_truth_exists(
            result_df
        )
    )

    # --------------------------------------------------------
    # 12. Save Bayesian output
    # --------------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print_section(
        "BAYESIAN OUTPUT SAVED"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print(
        f"Records saved: "
        f"{len(result_df)}"
    )

    print(
        f"Columns saved: "
        f"{len(result_df.columns)}"
    )

    # --------------------------------------------------------
    # 13. Save evaluation summary
    # --------------------------------------------------------

    if evaluation_summary is not None:

        evaluation_summary.to_csv(
            EVALUATION_FILE,
            index=False
        )

        print(
            f"Evaluation summary: "
            f"{EVALUATION_FILE}"
        )

    print_section(
        "BAYESIAN ENGINE FINISHED"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()