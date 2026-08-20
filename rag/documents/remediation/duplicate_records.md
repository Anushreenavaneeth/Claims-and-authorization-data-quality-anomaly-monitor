# Duplicate Records Remediation SOP

## 1. Purpose

This document defines the standard remediation procedure for duplicate records identified in healthcare data.

Duplicate records may occur in Claims, Pharmacy, Authorization, or other healthcare datasets.

---

## 2. Problem Description

A duplicate record occurs when the same business event, transaction, or entity is represented more than once when only one valid record is expected.

Common examples include:

- Duplicate record IDs
- Duplicate transaction IDs
- Duplicate claim records
- Duplicate pharmacy transactions
- Duplicate authorization records
- Repeated records from the same upstream batch

---

## 3. Common Causes

Possible causes include:

- Duplicate upstream transmission
- Batch replay
- Pipeline retry
- Reprocessing of the same data
- Integration failure
- Incorrect deduplication logic
- Multiple source-system submissions
- Failed or repeated ingestion

These are possible causes and must be confirmed through investigation.

---

## 4. Evidence to Collect

Review:

- Record ID
- Transaction ID
- Batch ID
- Source system
- Ingestion timestamp
- Processing timestamp
- Duplicate count
- Duplicate rate
- Source batch history
- Previous processing history

---

## 5. Investigation Procedure

### Step 1 — Identify Duplicate Records

Identify records sharing the same applicable uniqueness key.

### Step 2 — Compare Record Contents

Compare duplicated records across relevant fields.

Determine whether they represent:

- The same business event
- Legitimate repeated transactions
- Duplicate transmission
- Partial or conflicting records

### Step 3 — Check Batch Information

Review:

- Batch ID
- Source
- File name
- Ingestion time
- Processing time

Determine whether the duplicates originated from the same batch or multiple transmissions.

### Step 4 — Check Processing History

Review whether the same records were previously processed or reprocessed.

### Step 5 — Verify Against Source

Where possible, compare the records with the authoritative upstream source.

---

## 6. Remediation Actions

If duplicates are confirmed:

1. Quarantine or identify the duplicate records.
2. Preserve the valid record.
3. Remove or suppress confirmed duplicate copies according to the operational policy.
4. Correct the upstream transmission or ingestion issue if identified.
5. Prevent duplicate records from being reintroduced.
6. Reprocess affected records when required.

Do not delete records solely because they appear similar without confirming that they represent the same business event.

---

## 7. Revalidation

After remediation, verify:

- Duplicate count
- Duplicate rate
- Record count
- Unique identifier count
- Source-to-target reconciliation
- Batch integrity

The duplicate condition should no longer be present.

---

## 8. Escalation

Escalate when:

- The source of duplication cannot be identified.
- Duplicate records affect a large number of transactions.
- Financial or operational impact is suspected.
- Duplicate transmission continues after remediation.
- Reprocessing creates additional duplicates.

---

## 9. RAG Usage

When RAG identifies a duplicate-record anomaly, it should use:

- ML/rule evidence
- Duplicate anomaly patterns
- Dataset-specific knowledge
- Reconciliation procedures
- Pipeline SOPs
- Troubleshooting information

RAG should recommend investigation and remediation based on the available evidence.

A duplicate anomaly alone does not prove duplicate upstream transmission.