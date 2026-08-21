# Claims Data Quality Pipeline SOP

## 1. Purpose

This document defines the standard processing flow for Claims data within the Healthcare Data Quality and Anomaly Detection Platform.

The pipeline identifies the Claims dataset, validates its structure, applies Claims-specific validation rules, performs anomaly detection, and produces structured evidence for downstream risk assessment and RAG-based root cause analysis.

---

## 2. Pipeline Flow

Claims Data
    ↓
Input Identification
    ↓
Schema Validation
    ↓
Claims-Specific Rules
    ↓
Claims ML Model
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

The system identifies whether the incoming dataset belongs to the Claims domain.

Expected identification information may include:

- Source
- Dataset type
- File type
- Schema
- Field names
- Dataset metadata

The identified source should be passed to the appropriate Claims processing pipeline.

---

## 4. Schema Validation

The Claims dataset is validated against the expected Claims schema.

Validation may include:

- Required fields
- Field names
- Data types
- Date formats
- Numeric fields
- Allowed categorical values
- Nullability
- Duplicate identifiers
- Schema compatibility

Schema validation failures should be recorded as structured evidence.

---

## 5. Claims-Specific Validation

Claims-specific rules are applied after schema validation.

Examples include:

- Invalid claim dates
- Invalid service dates
- Invalid claim status
- Invalid procedure codes
- Invalid diagnosis codes
- Invalid provider identifiers
- Invalid billed amounts
- Invalid allowed amounts
- Invalid paid amounts
- Duplicate claims
- Timely filing violations
- Inconsistent claim amounts
- Missing required claim information

Each violated rule should produce evidence describing:

- Rule name
- Rule status
- Affected record
- Observed value
- Expected condition

---

## 6. Claims ML Model

The Claims ML model evaluates the dataset or individual records for statistical or behavioral anomalies.

The ML output should contain only information required by downstream anomaly detection, risk assessment, and RAG.

Important evidence may include:

- Model name
- Anomaly score
- Contributing features
- Observed values
- Expected values or ranges
- Deviation information
- Record identifier

The ML model is responsible for identifying anomalous behavior.

It is not responsible for final root cause explanation or remediation recommendation.

---

## 7. Anomaly Detection

Claims anomalies are detected using two complementary approaches:

### Rule-Based Detection

Detects violations of predefined Claims data-quality rules.

### ML-Based Detection

Detects statistical or behavioral deviations learned by the ML model.

The outputs are combined into a unified anomaly representation.

---

## 8. Anomaly Correlation

Multiple anomalies may represent the same underlying data-quality problem.

The correlation stage groups related evidence based on factors such as:

- Record
- Field
- Rule
- Feature
- Anomaly pattern
- Dataset
- Time period

The objective is to avoid treating related symptoms as completely independent problems.

---

## 9. Risk and Severity

The correlated anomaly information is passed to the risk/severity stage.

The system determines the operational importance of the anomaly based on available evidence.

Possible factors include:

- Severity
- Anomaly frequency
- Business impact
- SLA exposure
- Data-quality impact
- Number of affected records

---

## 10. SLA Risk

The system evaluates whether the anomaly may affect the applicable Claims processing SLA.

The resulting SLA information is included in the downstream RAG input.

---

## 11. RAG Handoff

The Claims pipeline should produce structured JSON containing the relevant observed evidence.

The RAG system uses this information as evidence.

RAG does not modify the original ML evidence.

The responsibility boundary is:

ML / Rules
    → Observed evidence

RAG
    → Evidence interpretation
    → Root cause analysis
    → Resolution recommendation

---

## 12. Expected RAG Evidence

Relevant Claims evidence may include:

- Dataset
- Record ID
- Violated rules
- ML anomaly information
- Contributing features
- Record context
- Severity
- Risk
- SLA information
- Correlated anomaly information

---

## 13. Important Principle

Claims-specific knowledge should primarily come from the Claims Knowledge Base.

Generic data-quality concepts should come from the Common Healthcare Data Quality Knowledge Base.

RAG combines the observed Claims evidence with these knowledge sources to determine the most likely root cause and recommended resolution.