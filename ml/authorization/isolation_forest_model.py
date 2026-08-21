import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


# ============================================================
# TRAIN ISOLATION FOREST
# ============================================================

def train_isolation_forest(
    ml_df,
    contamination=0.05,
    n_estimators=300,
    random_state=42
):

    # --------------------------------------------------------
    # SCALE DATA
    # --------------------------------------------------------

    scaler = RobustScaler()

    X_scaled = scaler.fit_transform(
        ml_df
    )


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    iso_model = IsolationForest(

        n_estimators=n_estimators,

        contamination=contamination,

        random_state=random_state,

        n_jobs=-1
    )


    iso_model.fit(
        X_scaled
    )


    # --------------------------------------------------------
    # TRAINING PREDICTIONS
    # --------------------------------------------------------

    predictions = iso_model.predict(
        X_scaled
    )


    anomaly_flag = np.where(
        predictions == -1,
        1,
        0
    )


    # Higher score = more anomalous

    anomaly_score = (
        -iso_model.decision_function(
            X_scaled
        )
    )


    # --------------------------------------------------------
    # SEVERITY THRESHOLDS
    # --------------------------------------------------------

    medium_threshold = float(
        np.quantile(
            anomaly_score,
            0.90
        )
    )

    high_threshold = float(
        np.quantile(
            anomaly_score,
            0.95
        )
    )


    return {

        "isolation_forest_model":
            iso_model,

        "scaler":
            scaler,

        "ml_feature_columns":
            ml_df.columns.tolist(),

        "medium_threshold":
            medium_threshold,

        "high_threshold":
            high_threshold
    }


# ============================================================
# ML SEVERITY
# ============================================================

def get_ml_severity(
    score,
    medium_threshold,
    high_threshold
):

    if score >= high_threshold:
        return "HIGH"

    elif score >= medium_threshold:
        return "MEDIUM"

    return "LOW"


# ============================================================
# DETECT ANOMALIES
# ============================================================

def detect_ml_anomalies(
    ml_df,
    isolation_artifacts
):

    expected_features = isolation_artifacts[
        "ml_feature_columns"
    ]


    X = ml_df[
        expected_features
    ].copy()


    scaler = isolation_artifacts[
        "scaler"
    ]

    iso_model = isolation_artifacts[
        "isolation_forest_model"
    ]


    X_scaled = scaler.transform(
        X
    )


    predictions = iso_model.predict(
        X_scaled
    )


    anomaly_flag = np.where(
        predictions == -1,
        1,
        0
    )


    anomaly_score = (
        -iso_model.decision_function(
            X_scaled
        )
    )


    severity = []

    for score in anomaly_score:

        severity.append(
            get_ml_severity(
                score,
                isolation_artifacts[
                    "medium_threshold"
                ],
                isolation_artifacts[
                    "high_threshold"
                ]
            )
        )


    return {

        "ml_anomaly_flag":
            anomaly_flag,

        "ml_anomaly_score":
            anomaly_score,

        "ml_anomaly_severity":
            severity
    }