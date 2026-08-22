# Unified JSON Schema (v2.0)

## StandardAnomalyRecord

All three datasets produce this schema after processing.

```json
{
  "schema_version": "2.0",
  "record_id":      "CLAIMS-10091OR0770001",
  "dataset":        "claims",
  "timestamp":      "2026-08-22T10:00:00+00:00",

  "anomaly": {
    "is_anomaly":    true,
    "anomaly_score": 0.0125,
    "severity":      "MEDIUM",
    "signal_count":  1,
    "signals":       ["Rule"]
  },

  "quality": {
    "quality_score": 75.0,
    "issues":        ["At least 50% of important fields are missing"]
  },

  "ml": {
    "model":      "Isolation Forest (CTS_V2)",
    "prediction": "anomaly",
    "score":      0.0125,
    "reasons":    []
  },

  "rules": {
    "violations":      ["At least 50% of important fields are missing"],
    "violation_count": 2,
    "rule_names":      ["EXCESSIVE_IMPORTANT_MISSINGNESS", "EXCESSIVE_SUPPRESSED_VALUES"],
    "severity":        "MEDIUM"
  },

  "bayesian": {
    "is_anomaly":  false,
    "score":       73.95,
    "probability": 0.0124,
    "threshold":   292.33,
    "root_causes": [],
    "confidence":  0.0124
  },

  "evidence": [
    "At least 50% of important fields are missing",
    "Record contains 10 or more suppressed or non-numeric values"
  ],

  "sla": {
    "risk_score":          66.67,
    "risk_level":          "HIGH",
    "priority":            "P2",
    "status":              "AT_RISK",
    "response_time":       "4 hours",
    "escalation_required": true,
    "action":              "Immediate Prioritization",
    "recommendation":      "Prioritize records to avoid SLA breach."
  },

  "rag": {
    "recommendation":      "Anomaly detected in claims record ... Root cause: ...",
    "explanation":         "This claims record was flagged because ...",
    "root_cause":          "EXCESSIVE IMPORTANT MISSINGNESS: critical fields missing",
    "recommended_actions": ["Identify and populate the missing required fields..."],
    "priority":            "P2",
    "confidence":          0.7,
    "evidence":            ["At least 50% of important fields are missing"]
  },

  "metadata": {
    "plan_id":    "10091OR0770001",
    "issuer_id":  "10091",
    "state":      "OR",
    "issuer_name": "PacificSource Health Plans",
    "plan_type":  "EPO",
    "metal_level": "Bronze"
  },

  "processing_status": "complete",
  "processing_errors": []
}
```

## Dataset-specific record_id prefixes

| Dataset | Prefix |
|---------|--------|
| Claims | `CLAIMS-` |
| Authorization | `AUTH-` |
| Pharmacy | `PHARM-` |

## SLA Status Values

| Status | Meaning |
|--------|---------|
| NORMAL | Risk score 0–30 |
| ELEVATED | Risk score 30–60 |
| AT_RISK | Risk score 60–80 |
| BREACHED | Risk score 80–100 |
