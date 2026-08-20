
---

# `anomaly_detection_pipeline.md`

```md
# Healthcare Anomaly Detection Pipeline SOP

## 1. Purpose

This document defines the anomaly detection stage of the Healthcare Data Quality and Anomaly Detection Platform.

The anomaly detection pipeline combines rule-based detection and ML-based detection to identify unusual, invalid, or unexpected healthcare data behavior.

The resulting evidence is passed to anomaly correlation, risk assessment, SLA evaluation, and finally the RAG system.

---

## 2. Pipeline Flow

Validated Data
    ↓
Rule-Based Detection
    +
ML-Based Detection
    ↓
Combined Anomaly Evidence
    ↓
Anomaly Correlation
    ↓
Risk / Severity
    ↓
SLA Risk
    ↓
RAG Input
    ↓
XAI / RAG Analysis
    ↓
RCA + Recommendation

---

## 3. Rule-Based Detection

Rule-based detection evaluates explicit healthcare data-quality and business rules.

Examples include:

- Invalid dates
- Invalid date sequences
- Missing required fields
- Invalid categorical values
- Duplicate records
- Invalid numeric values
- Schema violations
- Inconsistent fields
- SLA violations
- Domain-specific validation failures

Each violated rule should produce structured evidence.

Example:

```json
{
  "rule": "invalid_date_sequence",
  "status": "violated"
}