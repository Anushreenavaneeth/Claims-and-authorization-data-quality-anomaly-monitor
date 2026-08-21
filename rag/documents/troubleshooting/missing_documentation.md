# Missing Documentation Troubleshooting SOP

## 1. Purpose

This document provides troubleshooting guidance for healthcare records where required supporting documentation is missing or incomplete.

---

## 2. Common Symptoms

Possible indicators include:

- Missing document count greater than zero
- Required document field is missing
- Authorization cannot be completed
- Processing is delayed
- Record requires resubmission
- Documentation-related rule violation

---

## 3. Evidence to Check

Review:

- Record ID
- Document type
- Missing document count
- Required document status
- Submission history
- Resubmission count
- Processing timestamps
- Authorization or transaction status
- Source system
- Available attachments or references

---

## 4. Investigation Procedure

### Step 1 — Identify the Missing Document

Determine which document or documentation requirement is affected.

### Step 2 — Check the Applicable Requirement

Verify whether the document is:

- Required
- Conditionally required
- Optional

Use the applicable domain rule or policy.

### Step 3 — Check Submission History

Review whether the document was:

- Never submitted
- Submitted but not received
- Rejected
- Attached incorrectly
- Lost during transmission

### Step 4 — Check Resubmission History

Determine whether the record was previously resubmitted.

### Step 5 — Check Upstream Source

Verify whether the document exists in the authoritative source.

---

## 5. Possible Causes

Potential causes include:

- Incomplete submission
- Missing provider documentation
- Upload failure
- Transmission failure
- Incorrect document mapping
- Document rejection
- Upstream processing issue

---

## 6. Resolution

Depending on the confirmed cause:

- Request the required documentation.
- Recover the document from the authoritative source.
- Correct document mapping.
- Correct transmission failure.
- Attach the valid document.
- Reprocess the affected record.
- Update the processing status according to the applicable procedure.

Do not fabricate missing documentation or infer its contents without authoritative evidence.

---

## 7. Validation After Resolution

Verify:

- Required document is available
- Document is associated with the correct record
- Document status is valid
- Missing document count is corrected
- Record can proceed through processing
- SLA status is updated when applicable

---

## 8. Escalation

Escalate when:

- Required documentation cannot be obtained.
- Documentation is repeatedly lost.
- Provider submission repeatedly fails.
- The issue affects a large number of records.
- Processing or SLA impact is significant.

---

## 9. RAG Usage

RAG should use:

- Missing-document evidence
- Domain-specific documentation requirements
- Pipeline SOPs
- Troubleshooting procedures
- SLA policies

RAG should not assume that missing documentation is the root cause of a processing delay unless the available evidence supports that conclusion.