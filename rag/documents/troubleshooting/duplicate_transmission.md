# Duplicate Transmission Troubleshooting SOP

## 1. Purpose

This document provides troubleshooting guidance for duplicate records caused by repeated or duplicate transmission from an upstream source.

---

## 2. Common Symptoms

Possible indicators include:

- Duplicate record IDs
- Duplicate transaction IDs
- Sudden increase in duplicate rate
- Same batch received multiple times
- Same file received repeatedly
- Identical records with different ingestion timestamps
- Record volume significantly above expected levels

---

## 3. Evidence to Check

Review:

- Record ID
- Transaction ID
- Batch ID
- File name
- Source system
- Source timestamp
- Ingestion timestamp
- Processing timestamp
- Batch count
- Duplicate rate
- Previous transmission history

---

## 4. Investigation Procedure

### Step 1 — Identify Duplicate Records

Identify records with identical or conflicting uniqueness keys.

### Step 2 — Compare Record Contents

Determine whether the records represent the same business event.

### Step 3 — Compare Batch Information

Check whether duplicate records originated from:

- Same batch
- Multiple batches
- Same source file
- Multiple source files

### Step 4 — Compare Timestamps

Check whether the same records were received or processed multiple times.

### Step 5 — Check Transmission History

Determine whether the source retransmitted a previously delivered batch.

### Step 6 — Check Pipeline Retry Behavior

Review whether automatic retries or reprocessing generated duplicate records.

---

## 5. Possible Causes

Potential causes include:

- Upstream batch replay
- Duplicate file transmission
- Network retry
- Integration retry
- Pipeline retry
- Source-system reprocessing
- Missing deduplication control

---

## 6. Resolution

If duplicate transmission is confirmed:

1. Identify the original valid transmission.
2. Identify duplicate transmissions.
3. Prevent duplicate data from entering downstream processing.
4. Quarantine or suppress confirmed duplicates according to policy.
5. Correct the transmission or retry mechanism.
6. Reconcile the affected batch.
7. Reprocess only the required valid records.

---

## 7. Validation After Resolution

Verify:

- Duplicate rate
- Record count
- Unique record count
- Batch count
- Source-to-target reconciliation
- Processing status

---

## 8. Escalation

Escalate when:

- Duplicate transmission continues.
- The source system cannot identify the original batch.
- Duplicate data has already affected downstream systems.
- Financial or operational impact is suspected.
- Automatic retries continue generating duplicates.

---

## 9. RAG Usage

RAG should match duplicate evidence against:

- Duplicate anomaly patterns
- Domain-specific rules
- Reconciliation procedures
- Pipeline SOPs

RAG should describe duplicate upstream transmission as a likely cause only when the available evidence supports it.