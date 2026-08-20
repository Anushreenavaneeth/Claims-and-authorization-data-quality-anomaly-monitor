# Invalid Dates Remediation SOP

## 1. Purpose

This document defines the standard remediation procedure for invalid, inconsistent, or incorrectly ordered dates in healthcare data.

---

## 2. Problem Description

An invalid date condition occurs when a date:

- Does not follow the expected format.
- Contains an impossible value.
- Violates an expected chronological sequence.
- Conflicts with related dates.
- Falls outside an applicable business condition.

---

## 3. Common Causes

Possible causes include:

- Incorrect source data
- Manual data-entry error
- Date transformation failure
- Field mapping error
- Time-zone conversion issue
- Incorrect date format
- Source-system defect
- Incorrect business-rule implementation

---

## 4. Evidence to Collect

Review:

- Affected record ID
- Date field
- Observed date
- Related date fields
- Expected date relationship
- Source system
- Source timestamp
- Transformation logic
- Time-zone information
- Historical records

---

## 5. Investigation Procedure

### Step 1 — Identify the Invalid Date

Determine which field contains the invalid or inconsistent date.

### Step 2 — Validate the Format

Check whether the value follows the expected date format.

### Step 3 — Validate the Value

Check whether the date is a valid calendar date.

### Step 4 — Check Date Relationships

Compare the affected date with related dates.

Examples:

```text
Start Date <= End Date
Service Date <= Submission Date
Authorization Date <= Applicable Processing Date