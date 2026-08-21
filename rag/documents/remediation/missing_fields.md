
```md
# Missing Fields Remediation SOP

## 1. Purpose

This document defines the standard remediation procedure for missing, null, or empty fields in healthcare datasets.

---

## 2. Problem Description

A missing-field anomaly occurs when a required or conditionally required field is absent, null, or empty when a valid value is expected.

Field requirements must be determined from the applicable schema and domain rules.

---

## 3. Common Causes

Possible causes include:

- Incomplete upstream transmission
- Source-system issue
- Mapping failure
- Schema change
- Extraction failure
- Missing documentation
- Incorrect required-field configuration
- Data transformation issue

---

## 4. Evidence to Collect

Review:

- Dataset
- Record ID
- Field name
- Null count
- Missing-value percentage
- Source system
- Source batch
- Schema definition
- Field mapping
- Historical completeness
- Related fields

---

## 5. Investigation Procedure

### Step 1 — Identify the Missing Field

Determine the affected field and number of impacted records.

### Step 2 — Determine Field Requirement

Check whether the field is:

- Universally required
- Conditionally required
- Optional

Use the applicable schema and domain knowledge.

### Step 3 — Check the Source

Determine whether the value exists in the authoritative upstream source.

### Step 4 — Check Mapping

If the source contains the value but the processed dataset does not, investigate field mapping and transformation logic.

### Step 5 — Check Historical Data

Determine whether the missing-value pattern is new or recurring.

---

## 6. Remediation Actions

If the correct value is available:

1. Recover the value from the authoritative source.
2. Correct the affected record.
3. Reprocess the record when required.
4. Validate downstream consistency.

If the source does not contain the value:

- Do not invent a value.
- Follow the applicable business or operational rule.
- Quarantine or escalate the record when required.

---

## 7. Revalidation

Verify:

- Required-field completeness
- Record validity
- Schema compliance
- Related-field consistency
- Downstream processing

---

## 8. Escalation

Escalate when:

- Missing values affect a significant number of records.
- Required source information is unavailable.
- The issue is caused by an upstream system.
- The missing field affects financial, regulatory, or operational processing.
- The problem continues after remediation.

---

## 9. RAG Usage

RAG should determine field requirements using:

- Applicable schema
- Domain Knowledge Base
- Common Healthcare Knowledge Base
- Pipeline SOP
- Troubleshooting documentation

RAG must not assume that every missing field is an error because some fields may be conditionally required or optional.