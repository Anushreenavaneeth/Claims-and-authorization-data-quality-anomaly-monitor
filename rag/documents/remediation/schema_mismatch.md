# Schema Mismatch Remediation SOP

## 1. Purpose

This document defines the standard remediation procedure for schema mismatches between incoming healthcare data and the expected dataset schema.

---

## 2. Problem Description

A schema mismatch occurs when incoming data differs from the expected structure.

Examples include:

- Missing fields
- Unexpected fields
- Incorrect data types
- Incorrect field formats
- Changed field names
- Unexpected nested structures
- Incompatible schema versions

---

## 3. Common Causes

Possible causes include:

- Upstream schema change
- Version mismatch
- Mapping failure
- Incorrect file generation
- Pipeline configuration issue
- Source-system update
- Undocumented field changes

---

## 4. Evidence to Collect

Compare:

- Expected schema
- Actual schema
- Schema version
- Field names
- Data types
- Required fields
- Unexpected fields
- Missing fields
- Source system
- File version
- Pipeline configuration

---

## 5. Investigation Procedure

### Step 1 — Load Expected Schema

Retrieve the schema associated with the dataset and version.

### Step 2 — Inspect Actual Schema

Identify differences between incoming and expected structures.

### Step 3 — Classify Differences

Classify each difference as:

- Missing field
- Unexpected field
- Type mismatch
- Format mismatch
- Name mismatch
- Structural mismatch

### Step 4 — Check Source Changes

Determine whether the upstream source recently changed its schema.

### Step 5 — Check Mapping

Verify whether the transformation or mapping layer expects the correct schema.

---

## 6. Remediation Actions

Depending on the confirmed cause:

- Correct the upstream data generation.
- Update field mapping.
- Update compatible schema configuration.
- Correct data types.
- Restore missing fields.
- Handle newly introduced fields according to the approved schema policy.
- Reprocess affected data.

Do not modify the expected schema solely to make invalid input pass validation without confirming that the schema change is legitimate.

---

## 7. Revalidation

After remediation:

1. Validate the incoming schema again.
2. Validate data types.
3. Validate required fields.
4. Validate field formats.
5. Run domain-specific data-quality rules.
6. Confirm successful downstream processing.

---

## 8. Escalation

Escalate when:

- The upstream schema changed without notification.
- The correct schema version cannot be determined.
- A large number of records are affected.
- The mismatch may cause data loss.
- Financial or operational processing is affected.

---

## 9. RAG Usage

RAG should compare the observed schema evidence against:

- Relevant schema document
- Domain Knowledge Base
- Common Healthcare Knowledge Base
- Pipeline SOP
- Troubleshooting procedures

The recommendation should distinguish between a legitimate schema evolution and an unexpected schema mismatch.  