"""
ML Service — Authorization Anomaly Detection
=============================================
Wraps the trained authorization Isolation Forest model.

The scaler was fit on 16 columns:
  8 base features + 8 corresponding _missing_flag columns.
We reconstruct those flags here before scaling.
"""
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np

warnings.filterwarnings("ignore")

_REPO_ROOT  = Path(__file__).resolve().parents[3]
_MODEL_DIR  = _REPO_ROOT / "ml" / "authorization" / "auth_models"

_model = None
_scaler = None
_feature_names: list[str] = []   # 8 base feature names
_load_error: str = ""

# Medians from the training data (used to impute missing values)
_MEDIANS: dict[str, float] = {
    "processing_time_hours":              23.94,
    "missing_document_count":             0.0,
    "resubmission_count":                 0.0,
    "authorization_to_service_days":      3.0,
    "provider_avg_processing_time":       29.78,
    "provider_avg_resubmission":          0.66,
    "provider_avg_missing_docs":          0.67,
    "processing_time_provider_deviation": 12.56,
}


def _load_models() -> None:
    global _model, _scaler, _feature_names, _load_error
    try:
        _model         = joblib.load(_MODEL_DIR / "isolation_forest_v1.pkl")
        _scaler        = joblib.load(_MODEL_DIR / "scaler_v1.pkl")
        _feature_names = list(joblib.load(_MODEL_DIR / "features_v1.pkl"))
    except Exception as e:
        _load_error = str(e)


_load_models()


def is_available() -> bool:
    return _model is not None and _scaler is not None


def get_load_error() -> str:
    return _load_error


def _build_feature_vector(record: dict[str, Any]) -> tuple[np.ndarray, list[float]]:
    """
    Build the 16-column feature vector the scaler expects:
      [feat_0, feat_1, ..., feat_7,
       feat_0_missing_flag, ..., feat_7_missing_flag]
    """
    base_values: list[float] = []
    missing_flags: list[float] = []

    for feat in _feature_names:
        raw = record.get(feat)
        if raw is None or (isinstance(raw, float) and np.isnan(raw)):
            # missing — use median, flag = 1
            base_values.append(_MEDIANS.get(feat, 0.0))
            missing_flags.append(1.0)
        else:
            base_values.append(float(raw))
            missing_flags.append(0.0)

    # 16 columns: 8 base + 8 flags
    combined = base_values + missing_flags
    return np.array([combined]), base_values


def predict(record: dict[str, Any]) -> dict[str, Any]:
    """
    Score a single authorization record.

    Accepts any subset of the 8 base features — missing values are
    median-imputed and flagged automatically.

    Returns:
        is_anomaly        bool
        anomaly_score     float  0-1 (higher = more anomalous)
        severity          CRITICAL | HIGH | MEDIUM | LOW
        contributing_features  list of top deviating fields
        model             str
    """
    if not is_available():
        raise RuntimeError(f"ML model not loaded: {_load_error}")

    X, base_values = _build_feature_vector(record)

    # Scale (16 features)
    X_scaled = _scaler.transform(X)

    # Predict
    raw_pred  = _model.predict(X_scaled)[0]        # -1 anomaly, 1 normal
    raw_score = float(_model.decision_function(X_scaled)[0])

    # Convert to 0-1 risk score (lower decision_function = more anomalous)
    risk_score = float(np.clip(0.5 - raw_score, 0.0, 1.0))
    is_anomaly = raw_pred == -1

    # Severity
    if risk_score >= 0.75:
        severity = "CRITICAL"
    elif risk_score >= 0.55:
        severity = "HIGH"
    elif risk_score >= 0.40:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Contributing features — use the first 8 scaled columns (base features only)
    contributing = []
    for i, feat in enumerate(_feature_names):
        scaled_val = float(X_scaled[0][i])
        if abs(scaled_val) >= 1.0:
            contributing.append({
                "feature":         feat,
                "value":           round(base_values[i], 4),
                "direction":       "above_normal" if scaled_val > 0 else "below_normal",
                "deviation_score": round(abs(scaled_val), 3),
            })

    contributing.sort(key=lambda x: x["deviation_score"], reverse=True)

    return {
        "is_anomaly":           bool(is_anomaly),
        "anomaly_score":        round(risk_score, 4),
        "severity":             severity,
        "contributing_features": contributing[:5],
        "model":                "IsolationForest_v1",
    }


def predict_batch(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [predict(r) for r in records]
