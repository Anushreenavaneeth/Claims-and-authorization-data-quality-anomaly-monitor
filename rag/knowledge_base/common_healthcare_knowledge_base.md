# Common Healthcare Data Quality Knowledge Base

## Scope

This knowledge base contains **generic healthcare data quality concepts**
that apply across multiple datasets — authorization, pharmacy, claims, and
others — unless a domain-specific KB overrides or extends a rule.

It does **not** contain authorization-specific, pharmacy-specific, or
claims-specific rules. Those rules belong in their respective domain KBs.

**KB Architecture:**

```
Common Healthcare Data Quality KB  ← This file
  └── Generic healthcare data quality concepts applicable across datasets

Authorization KB
  └── Authorization-specific knowledge

Pharmacy KB
  └── Pharmacy-specific knowledge

Claims KB
  └── Claims-specific knowledge
```

RAG should first retrieve domain-specific KB content, then supplement with
this common KB when domain-specific coverage is insufficient.

------------------------------------------------------------------------

# 1. Schema Validation

## 1.1 Expected Schema Check

Every dataset must conform to its expected schema before processing.

**What to check:**

- All required columns are present
- No unexpectedly missing columns
- No unexpected extra columns that may indicate a schema drift

**Anomaly signal:** If required columns are absent, schema validation fails
and downstream processing is unreliable.

## 1.2 Required Field Definition

A required field is one that must be present and non-null for every record.
Datasets must define their own required fields, but the following generic
categories apply across all healthcare datasets:

| Category | Examples |
|---|---|
| Record identifier | Claim ID, Authorization ID, Pharmacy claim ID |
| Member identifier | Member ID, subscriber ID |
| Provider identifier | Provider ID, NPI |
| Date fields | Service date, submission date, processing date |
| Status fields | Authorization status, claim status |

------------------------------------------------------------------------

# 2. Completeness Rules

## 2.1 Missing Value Detection

A record is incomplete when a required field contains a null, empty, or
placeholder value.

**General rule:**

```
field IS NULL
OR field = ''
OR field = 'N/A'
OR field = 'UNKNOWN'  (when used as a placeholder for missing data)
```

**Impact:** Missing required fields contribute to the rule score and mark
the record as a rule-based anomaly.

## 2.2 Partial Record

A record is considered a partial record when multiple required fields are
missing. Partial records should be routed for correction before further
processing.

------------------------------------------------------------------------

# 3. Uniqueness Rules

## 3.1 Duplicate Record Detection

A duplicate exists when two or more records share the same business key —
the combination of fields that uniquely identifies a transaction.

Each dataset defines its own business key. The general pattern is:

```
member_id + provider_id + service_date + transaction_type_identifier
```

**Anomaly signal:** Duplicate records inflate metrics, cause double
processing, and distort analytical outputs.

## 3.2 Deduplication Approach

When duplicates are detected:

1. Compare all fields across duplicate records.
2. Determine whether the duplication resulted from:
   - Repeated ingestion of the same source file
   - Resubmission of the same transaction
   - Legitimate repeated transactions (same member, same provider, same date)
3. Retain the authoritative record and remove or flag unintended duplicates
   according to operational deduplication policy.

------------------------------------------------------------------------

# 4. Validity Rules

## 4.1 Categorical Value Validation

Every categorical field must contain a value from its defined allowed set.

**General approach:**

```
IF observed_value NOT IN allowed_values
THEN flag as invalid_category_value
```

The allowed value sets are defined per field in each domain KB.

## 4.2 Identifier Format Validation

Identifiers must conform to the expected format pattern for the dataset.

**General approach:**

```
IF identifier does not match expected pattern
THEN flag as invalid_identifier_format
```

Format patterns (e.g., regex) are defined per identifier in each domain KB.

## 4.3 Numeric Validity

Numeric fields must satisfy:

- Non-negative where negative values are not meaningful (e.g., count fields,
  duration fields, amount fields)
- Within a plausible operational range

**General rules:**

```
count_field >= 0
duration_field >= 0
amount_field >= 0
amount_field <= defined_upper_limit   (where applicable)
```

------------------------------------------------------------------------

# 5. Consistency Rules

## 5.1 Cross-Field Logical Consistency

Related fields within a record must be logically consistent with each other.

**Common patterns:**

- End date must not precede start date
- Approval decision must be consistent with supporting documentation status
- Calculated fields must match their source components

## 5.2 Cross-Record Consistency

Records that reference shared entities (members, providers, drugs) must be
consistent across datasets. Referential integrity failures indicate:

- A missing or corrupted lookup table
- An entity that exists in one system but not another
- A mapping or synchronization failure between systems

------------------------------------------------------------------------

# 6. Date and Time Validation

## 6.1 Future Date Rule

**General rule:**

```
date_field > current_date → flag as future_date
```

Future dates on transaction records (service date, submission date, etc.)
are typically data-entry or transformation errors.

**Exceptions:** Some fields such as planned future service dates or
appointment dates may legitimately be in the future. Each domain KB defines
which date fields permit future values.

## 6.2 Date Sequence Rule

Dates in a transaction must follow a logical sequence.

**General pattern:**

```
event_start_date <= event_end_date
originating_event_date <= dependent_event_date
```

For example: service must occur before or at claim submission; authorization
must precede service (unless retrospective).

Each domain KB defines the specific date fields and their required sequence.

## 6.3 Date Format Validation

All dates must conform to the expected format:

```
YYYY-MM-DD
```

Dates in non-standard formats should be rejected or normalized during
ingestion.

## 6.4 Implausible Date

Dates that are technically valid but implausible should be flagged:

- Dates far in the past (e.g., before the system's operational start date)
- Dates in a calendar year that is unlikely for the transaction type

------------------------------------------------------------------------

# 7. Numeric Validation

## 7.1 Non-Negative Fields

Count fields, duration fields, and amount fields must be non-negative:

```
field_value >= 0
```

Negative values in these fields indicate data corruption, transformation
errors, or incorrect sign handling.

## 7.2 Plausible Range

Numeric fields must fall within a plausible operational range.

**General approach:**

```
lower_bound <= field_value <= upper_bound
```

Upper and lower bounds are defined per field in each domain KB based on
business knowledge and historical distribution.

## 7.3 Outlier Detection

Records where numeric field values deviate significantly from the expected
distribution should be flagged as potential outliers.

The ML pipeline uses Isolation Forest and cluster analysis for outlier
detection. Rule-based outlier detection uses defined upper/lower bounds.

------------------------------------------------------------------------

# 8. Data Freshness

## 8.1 Freshness Definition

A dataset is considered fresh when it has been updated within the expected
refresh cycle for that dataset type.

**General freshness indicators:**

- Processing date / ingestion timestamp is within the expected window
- Record count is consistent with expected volume for the period

## 8.2 Stale Data Signal

A dataset may be stale when:

```
current_date - last_ingestion_date > expected_refresh_interval
```

Stale data can cause downstream ML models and RAG systems to operate on
outdated information.

------------------------------------------------------------------------

# 9. Volume and Record Count Checks

## 9.1 Expected Volume Range

Every dataset ingestion should be compared against the expected volume
for the period (daily, weekly, monthly).

**Anomaly signals:**

- Actual record count significantly below expected count → possible data
  loss, pipeline failure, or source system issue
- Actual record count significantly above expected count → possible
  duplicate ingestion, processing loop, or unexpected volume spike

## 9.2 Volume Deviation Threshold

A volume deviation is flagged when:

```
|actual_count - expected_count| / expected_count > volume_threshold
```

The specific volume threshold is defined by operational configuration per
dataset. A common starting point is a 5–10% deviation threshold, but the
correct value depends on historical variability for the dataset.

------------------------------------------------------------------------

# 10. Generic Data Reconciliation

## 10.1 Schema Reconciliation

1. Compare incoming columns against the expected schema definition.
2. Investigate missing columns, unexpected columns, and type mismatches.
3. Escalate schema changes to the data engineering team.

## 10.2 Record Count Reconciliation

1. Compare actual ingested record count against the expected count from
   the source system.
2. If counts differ, investigate:
   - Pipeline failures or partial loads
   - Source system extraction issues
   - Deduplication removing more records than expected

## 10.3 Completeness Reconciliation

1. For each required field, calculate the null/missing rate.
2. Compare against the acceptable missing rate threshold.
3. If missing rates exceed the threshold, investigate:
   - Source system data entry gaps
   - ETL transformation errors
   - Field mapping issues

## 10.4 Distribution Reconciliation

1. For key numeric fields, compare the current distribution (mean, median,
   standard deviation, min, max) against the historical baseline.
2. Significant shifts may indicate:
   - Data quality degradation
   - Source system changes
   - Seasonal effects (if not accounted for)

------------------------------------------------------------------------

# 11. Generic Root Cause Patterns

These root cause patterns apply across all healthcare datasets. Domain-
specific root cause mappings in each domain KB take precedence.

| Pattern | Common Cause | Investigation |
|---|---|---|
| Missing required field | Source system gap, ETL mapping error | Verify source and mapping |
| Invalid identifier format | Source formatting change, mapping table out of date | Check source and mapping table |
| Future date | Data entry error, system clock issue, transformation bug | Verify source value |
| Date sequence violation | ETL reorder, retrospective transaction not flagged | Check transaction type and date fields |
| Invalid categorical value | Source system added new value, mapping table not updated | Check allowed values and mapping |
| Duplicate records | Re-ingestion, resubmission, deduplication failure | Check ingestion log and dedup logic |
| Volume drop | Pipeline failure, source system issue, extraction error | Check pipeline logs |
| Volume spike | Duplicate ingestion, source system error, load repeat | Check ingestion log |
| Numeric out of range | Data entry error, transformation error, unit mismatch | Verify source and transformation |

------------------------------------------------------------------------

# 12. Generic SLA Framework

Domain-specific SLA policies are defined in each domain KB. The following
generic framework applies when no domain-specific SLA is defined.

| Severity | Generic SLA |
|---|---|
| Normal | No action required |
| Warning | Review within 48 Hours |
| High | Review within 24 Hours |
| Critical | Immediate Review within 4 Hours |

Severity is determined by the final_risk_score produced by the ML pipeline.
Refer to the domain KB for the specific severity thresholds applicable to
each dataset.

------------------------------------------------------------------------

# 13. ML / KB / RAG Responsibility Boundary

This boundary applies to all datasets using the hybrid anomaly detection
and RAG pipeline.

```
ML OUTPUT        → What happened? (observed evidence)
KNOWLEDGE BASE   → What does this pattern mean, what are the possible
                   causes, and what procedures apply? (domain knowledge)
RAG              → Based on the observed evidence and retrieved knowledge,
                   what is the likely root cause and what should be done?
                   (grounded reasoning)
```

### RAG Principles Across All Datasets

- ML evidence (rule_based_evidence, ml_based_evidence, model_summary) must
  not be discarded or overridden by RAG.
- RAG must treat ML evidence as observed facts, not reinterpret them.
- RAG must retrieve domain KB knowledge to explain the observed facts.
- RAG must not claim a definitive root cause unless supported by evidence.
- Use wording: **Likely root cause**, **Possible root cause**,
  **Supporting evidence**, **Recommended investigation**.

### ML JSON Fields — Common Treatment

| Field | Treatment |
|---|---|
| `dataset` | Identifies which domain KB to retrieve |
| `final_anomaly` | Anomaly confirmation flag — do not discard |
| `final_severity` | Operational severity — drives SLA |
| `final_risk_score` | Overall risk — do not discard |
| `rule_risk_score` | Deterministic rule risk component |
| `ml_risk_score` | Statistical/ML risk component |
| `cluster_risk_score` | Behavioral cluster risk component |
| `rule_anomaly` | Rule-based anomaly flag — do not discard |
| `ml_anomaly` | ML-based anomaly flag — do not discard |
| `rule_based_evidence` | Specific violated rules |
| `ml_based_evidence` | Feature deviations from Isolation Forest |
| `record_context` | Actual record field values |
| `sla` | Operational review deadline |

------------------------------------------------------------------------

# 14. Historical Resolutions (Common)

This section is a placeholder for future cross-dataset resolved cases that
do not belong to a single domain. **Do not populate with fabricated examples.**

Recommended future structure:

```
case_id
record_id
dataset
issue_type
evidence
confirmed_root_cause
resolution_action
resolution_status
resolved_by
resolved_date
time_to_resolution
```

### Future Population Flow

```
ML detects anomaly
  → RAG recommends resolution
    → Worker resolves issue
      → Resolution is confirmed
        → Case is stored in Historical Resolution KB
          → Future RAG retrieval uses confirmed cases
```

This section will be populated only after real anomalies are resolved
through the operational workflow.
