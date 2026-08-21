# Authorization Data Quality Pipeline SOP

## 1. Purpose

This document defines the standard processing flow for Authorization data within the Healthcare Data Quality and Anomaly Detection Platform.

The pipeline identifies Authorization data, validates the schema, applies Authorization-specific rules, evaluates anomalies using rule-based and ML-based detection, performs anomaly correlation and risk assessment, and prepares structured evidence for RAG.

---

## 2. Pipeline Flow

Authorization Data
    ↓
Input Identification
    ↓
Schema Validation
    ↓
Authorization-Specific Rules
    ↓
Authorization ML Model
    ↓
Anomaly Detection
    ├── Rule-Based Detection
    └── ML-Based Detection
    ↓
Anomaly Correlation
    ↓
Risk / Severity Assessment
    ↓
SLA Risk
    ↓
RAG Input
    ↓
RCA + Recommendation

---

## 3. Input Identification

The system identifies whether the incoming dataset belongs to the Authorization domain.

Identification may use:

- Source
- Dataset type
- File type
- Schema
- Field names
- Dataset metadata

The identified dataset is routed to the Authorization pipeline.

---

## 4. Schema Validation

The Authorization dataset is validated against the expected Authorization schema.

Validation may include:

- Required fields
- Data types
- Field names
- Date formats
- Nullability
- Allowed categorical values
- Numeric fields
- Duplicate identifiers
- Schema compatibility

Validation failures are captured as structured evidence.

---

## 5. Authorization-Specific Validation

Authorization-specific rules are applied after schema validation.

Examples include:

- Invalid authorization date
- Invalid service date
- Invalid date sequence
- Invalid urgency
- Invalid authorization status
- Invalid authorization type
- Missing required documentation
- Invalid provider information
- Invalid service information
- Excessive processing time
- Duplicate authorization records
- Invalid resubmission information
- Inconsistent authorization fields

Each violated rule should produce structured evidence.

---

## 6. Authorization ML Model

The Authorization ML model evaluates records for anomalous behavior.

Relevant evidence may include:

- Model name
- Anomaly score
- Contributing features
- Observed values
- Expected ranges
- Deviation scores
- Record identifier

For example, unusually high processing time may be detected as an ML anomaly.

The ML model provides evidence and does not independently determine the final root cause.

---

## 7. Anomaly Detection

Authorization anomalies are identified using two sources.

### Rule-Based Detection

Detects explicit violations of predefined Authorization rules.

### ML-Based Detection

Detects statistical or behavioral deviations.

The two outputs are combined into the anomaly representation.

---

## 8. Anomaly Correlation

Related Authorization anomalies are correlated.

Possible correlation factors include:

- Record
- Field
- Rule
- ML feature
- Provider
- Service type
- Time period
- Anomaly pattern

Correlation helps determine whether multiple anomaly signals may represent one underlying problem.

---

## 9. Risk and Severity

The correlated anomaly is evaluated for operational importance.

Potential factors include:

- Severity
- Risk score
- Number of affected records
- Processing impact
- Data-quality impact
- SLA exposure

The resulting risk information is passed to the SLA stage.

---

## 10. SLA Risk

The Authorization SLA is evaluated using the available processing and anomaly evidence.

Example:

Review within 48 Hours

If observed processing time exceeds the applicable SLA, this becomes important evidence for downstream analysis.

---

## 11. RAG Handoff

The Authorization pipeline produces the structured JSON required by RAG.

The JSON should remain aligned with the ML-to-RAG contract.

RAG receives observed evidence and combines it with:

- Authorization Knowledge Base
- Common Healthcare Knowledge Base
- Remediation procedures
- Troubleshooting knowledge
- Pipeline SOPs

---

## 12. Expected RAG Evidence

Important evidence includes:

- Dataset
- Record ID
- Rule-based evidence
- ML-based evidence
- Contributing features
- Record context
- Anomaly correlation
- Severity
- Risk
- SLA information

---

## 13. Example Evidence

Observed:

- `invalid_date_sequence` violated
- `invalid_urgency` violated
- Processing time significantly exceeds expected range
- Processing time exceeds the stated SLA

RAG should use these observations to identify the most likely cause.

The final RCA must be based on evidence and retrieved domain knowledge rather than being directly invented by the ML model.

---

## 14. Important Principle

Authorization ML output represents observed evidence.

Authorization Knowledge Base represents Authorization-specific knowledge.

Common Healthcare Knowledge Base represents generic healthcare data-quality knowledge.

RAG combines evidence and knowledge to produce:

- Summary
- Likely root cause
- Supporting evidence
- Recommended resolution
- SLA/Priority consideration