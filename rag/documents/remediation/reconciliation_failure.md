# Reconciliation Failure Remediation SOP

## 1. Purpose

This document defines the standard remediation procedure for reconciliation failures between related healthcare datasets, pipeline stages, batches, or control totals.

---

## 2. Problem Description

A reconciliation failure occurs when expected values do not agree between two related processing stages or data sources.

Examples include:

- Input count differs from output count.
- Source count differs from target count.
- Record identifiers are missing.
- Duplicate records appear after processing.
- Financial/control totals do not match.
- Batch-level totals do not reconcile.

---

## 3. Common Causes

Possible causes include:

- Dropped records
- Duplicate records
- Partial processing
- Failed batch
- Incorrect filtering
- Transformation error
- Mapping failure
- Incomplete transmission
- Pipeline interruption

---

## 4. Evidence to Collect

Review:

- Source record count
- Target record count
- Difference count
- Source identifiers
- Target identifiers
- Batch ID
- Control totals
- Amount totals
- Processing logs
- Error logs
- Processing status

---

## 5. Investigation Procedure

### Step 1 — Compare Record Counts

Compare source and target record counts.

Example:

```text
Source Records  = 10,000
Target Records  = 9,850
Difference      = 150