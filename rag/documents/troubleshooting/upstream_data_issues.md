# Upstream Data Issues Troubleshooting SOP

## 1. Purpose

This document provides troubleshooting guidance for data-quality issues originating from upstream source systems.

---

## 2. Common Symptoms

Upstream data issues may appear as:

- Missing records
- Missing required fields
- Unexpected field values
- Invalid dates
- Invalid codes
- Duplicate records
- Unexpected data volume
- Schema mismatch
- Delayed data
- Sudden distribution changes

---

## 3. Evidence to Check

Review:

- Source system
- Dataset
- Batch ID
- File name
- Record ID
- Ingestion timestamp
- Source timestamp
- Processing timestamp
- Schema version
- Record count
- Historical data quality
- Upstream processing status

---

## 4. Investigation Procedure

### Step 1 — Identify the Source

Determine which upstream system generated the affected data.

### Step 2 — Compare With Historical Data

Check whether the issue is new or recurring.

### Step 3 — Check the Current Batch

Review:

- Batch ID
- Record count
- File structure
- Field completeness
- Data distribution

### Step 4 — Compare Source and Processed Data

Determine whether the issue existed in the source or was introduced during downstream processing.

### Step 5 — Check Recent Changes

Review recent:

- Source-system releases
- Schema changes
- Mapping changes
- Configuration changes
- Data extraction changes

---

## 5. Possible Causes

Potential causes include:

- Upstream application issue
- Source extraction failure
- Schema change
- Incorrect source mapping
- Incomplete transmission
- Duplicate transmission
- Source data-entry issue
- Upstream processing delay

These are hypotheses until confirmed by evidence.

---

## 6. Resolution

Depending on the confirmed cause:

- Correct the source data.
- Correct source extraction.
- Restore the expected schema.
- Correct field mappings.
- Retransmit the affected batch.
- Reconcile the retransmitted data.
- Reprocess affected records.

---

## 7. Validation After Resolution

Verify:

- Record count
- Required fields
- Schema
- Duplicate rate
- Data validity
- Reconciliation
- Processing status

---

## 8. Escalation

Escalate to the upstream data owner when:

- The issue originates from the source system.
- Data cannot be corrected downstream.
- The issue affects a large number of records.
- Repeated batches contain the same problem.
- Business or SLA impact is significant.

---

## 9. RAG Usage

RAG should use this document when the observed evidence indicates a possible upstream-originated issue.

RAG should distinguish between:

Observed upstream evidence
and
Possible upstream root cause.

An upstream issue should not be presented as confirmed without supporting evidence.