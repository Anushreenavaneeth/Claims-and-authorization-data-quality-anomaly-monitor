# Provider Data Issues Troubleshooting SOP

## 1. Purpose

This document provides troubleshooting guidance for data-quality issues associated with healthcare provider information.

---

## 2. Common Symptoms

Possible indicators include:

- Invalid provider identifier
- Missing provider information
- Unexpected provider values
- Provider-specific processing delay
- Provider-level anomaly
- Provider-specific deviation from expected behavior
- Invalid provider-to-service relationship
- Repeated provider-related validation failures

---

## 3. Evidence to Check

Review:

- Provider ID
- Provider type
- Provider location
- Provider status
- Service type
- Source system
- Record ID
- Historical provider activity
- Provider-specific baseline
- Processing time
- Rule violations
- ML contributing features

---

## 4. Investigation Procedure

### Step 1 — Validate Provider Identifier

Check whether the provider identifier follows the expected format and is available in the applicable reference data.

### Step 2 — Validate Provider Context

Review whether the provider is associated with the relevant:

- Service
- Transaction
- Authorization
- Claim
- Pharmacy activity

### Step 3 — Compare Historical Behavior

Compare current provider activity against an appropriate historical baseline.

### Step 4 — Check Provider-Specific Anomalies

Review:

- Processing time
- Volume
- Error rate
- Duplicate rate
- Missing-field rate
- Rule violations

### Step 5 — Check Source Data

Determine whether the provider issue originated from the upstream source or downstream processing.

---

## 5. Possible Causes

Potential causes include:

- Incorrect provider identifier
- Provider reference-data issue
- Mapping error
- Source-system error
- Provider submission issue
- Provider workflow delay
- Unexpected provider behavior
- Reference-data synchronization issue

These are possible causes and require supporting evidence.

---

## 6. Resolution

Depending on the confirmed cause:

- Correct provider information using an authoritative source.
- Correct provider mapping.
- Update approved reference data.
- Correct source data.
- Contact the appropriate provider/data owner.
- Reprocess affected records.
- Revalidate provider relationships.

Do not modify provider information without an authoritative reference.

---

## 7. Validation After Resolution

Verify:

- Provider identifier
- Provider reference data
- Provider-to-service relationship
- Affected records
- Rule violations
- Processing status
- Reconciliation

---

## 8. Escalation

Escalate when:

- Provider information cannot be verified.
- Provider reference data is inconsistent.
- A large number of provider records are affected.
- Provider-related anomalies continue.
- Significant SLA or operational impact exists.

---

## 9. RAG Usage

RAG should combine:

- Provider-related ML evidence
- Rule violations
- Provider context
- Domain Knowledge Base
- Provider troubleshooting information
- Pipeline SOPs
- Relevant remediation procedures

A provider-related anomaly does not automatically establish provider fault.

RAG should distinguish between:

Observed provider-related evidence
and
Possible provider-related root cause.