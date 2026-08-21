# Delayed Processing Troubleshooting SOP

## 1. Purpose

This document provides troubleshooting guidance for healthcare data that is received or processed later than expected.

---

## 2. Common Symptoms

Indicators include:

- Processing time exceeds expected range
- Data arrives after the expected ingestion window
- SLA deadline is approaching or exceeded
- Processing backlog increases
- Provider or source processing time is unusually high
- Batch remains pending for an extended period

---

## 3. Evidence to Check

Review:

- Event timestamp
- Source timestamp
- Ingestion timestamp
- Processing timestamp
- Expected processing time
- Applicable SLA
- Queue size
- Batch status
- Pipeline execution logs
- Retry history
- Provider/source performance

---

## 4. Investigation Procedure

### Step 1 — Calculate Processing Delay

Compare the relevant timestamps.

### Step 2 — Identify the Delayed Stage

Determine whether the delay occurred during:

- Source generation
- Transmission
- Ingestion
- Validation
- Transformation
- Processing
- Downstream delivery

### Step 3 — Check Pipeline Status

Review:

- Failed jobs
- Running jobs
- Queue backlog
- Retry activity
- Resource availability

### Step 4 — Check Upstream Status

Determine whether the source transmitted the data late.

### Step 5 — Check Historical Performance

Compare current processing time against the relevant baseline.

---

## 5. Possible Causes

Potential causes include:

- Upstream processing delay
- Pipeline backlog
- Failed job
- Excessive retry
- Infrastructure issue
- Network delay
- Large batch
- Missing documentation
- Provider workflow delay

---

## 6. Resolution

Depending on the confirmed cause:

- Resolve failed pipeline jobs.
- Clear processing backlog.
- Correct pipeline configuration.
- Recover delayed source data.
- Reprocess failed records.
- Investigate provider/source workflow.
- Escalate when SLA exposure is significant.

---

## 7. SLA Consideration

Check the applicable SLA before prioritizing remediation.

Important information includes:

- SLA requirement
- Current elapsed processing time
- Remaining SLA time
- Number of affected records
- Severity
- Business impact

Do not invent an SLA threshold.

Use the configured SLA policy or the SLA information provided by the upstream pipeline.

---

## 8. Validation After Resolution

Verify:

- Processing time
- Batch completion
- Record completeness
- Reconciliation
- Downstream availability
- SLA status

---

## 9. RAG Usage

RAG should use delayed-processing evidence together with:

- Anomaly patterns
- Pipeline SOPs
- SLA policies
- Troubleshooting procedures
- Domain-specific knowledge

The RAG response should distinguish between observed delay and the suspected reason for the delay.