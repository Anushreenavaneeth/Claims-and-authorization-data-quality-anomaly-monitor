"""
Configuration for RAG ML-output ingestion.
"""

# ---------------------------------------------------------
# Supported datasets
# ---------------------------------------------------------

SUPPORTED_DATASETS = {
    "authorization",
    "pharmacy",
    "claims"
}


# ---------------------------------------------------------
# Required fields for every anomaly record
# ---------------------------------------------------------

REQUIRED_FIELDS = {
    "dataset_type",
    "record_id",
    "detection_summary",
    "rule_based_evidence",
    "ml_based_evidence",
    "record_context",
    "sla"
}


# ---------------------------------------------------------
# Required detection-summary fields
# ---------------------------------------------------------

REQUIRED_DETECTION_FIELDS = {
    "final_anomaly",
    "final_severity",
    "final_risk_score",
    "rule_risk_score",
    "ml_risk_score",
    "cluster_risk_score",
    "rule_anomaly",
    "ml_anomaly"
}


# ---------------------------------------------------------
# Required ML evidence fields
# ---------------------------------------------------------

REQUIRED_ML_FIELDS = {
    "model",
    "is_anomaly",
    "anomaly_score",
    "contributing_features"
}


# ---------------------------------------------------------
# Validation behaviour
# ---------------------------------------------------------

ALLOW_EMPTY_RULE_EVIDENCE = True

ALLOW_EMPTY_CONTRIBUTING_FEATURES = True

ALLOW_NULL_CONTEXT_VALUES = True


# ---------------------------------------------------------
# Maximum records allowed in one ingestion request
# ---------------------------------------------------------

MAX_RECORDS = 5000