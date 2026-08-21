# Healthcare Data Quality Metrics

## Purpose

This document defines common data quality dimensions and metrics used to evaluate healthcare datasets.

It provides supporting knowledge for the RAG system when interpreting data-quality anomalies, severity, risk, and recommended remediation.

This document contains generic healthcare data-quality concepts. Dataset-specific thresholds and business rules must be obtained from the appropriate domain knowledge base or configured policy.

---

## 1. Data Quality Dimensions

The primary data quality dimensions considered by the system are:

1. Completeness
2. Validity
3. Accuracy
4. Consistency
5. Uniqueness
6. Timeliness
7. Freshness
8. Conformity
9. Integrity
10. Reconciliation

---

## 2. Completeness

### Definition

Completeness measures whether required data fields are populated.

### Basic Metric

```text
Completeness % =
(number of non-null required values /
 total required values) × 100