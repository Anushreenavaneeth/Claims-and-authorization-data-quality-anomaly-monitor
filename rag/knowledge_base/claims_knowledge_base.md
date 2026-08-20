# Claims Data Quality Knowledge Base

## Scope

This knowledge base covers **Claims-specific** data quality rules,
anomaly patterns, root cause mappings, resolution procedures, SLA policies,
reconciliation procedures, historical resolutions, and business/operational
rules for the Claims Data Quality and Anomaly Detection pipeline.

It does **not** include authorization-specific, pharmacy-specific, or generic
healthcare rules. For generic concepts (schema validation, completeness,
uniqueness, freshness, volume checks, etc.) see the
**Common Healthcare Data Quality KB**.

**KB Architecture:**

```
Common Healthcare Data Quality KB
  └── Generic healthcare data quality concepts

Authorization KB
  └── Authorization-specific knowledge

Pharmacy KB
  └── Pharmacy-specific knowledge

Claims KB  ← This file
  └── Claims-specific knowledge
```

------------------------------------------------------------------------

# 1. Claims Data Quality Rules

## 1.1 Schema / Required Columns

The claims dataset is expected to contain:

| Field | Requirement |
|---|---|
| claim_id | Required |
| member_id | Required |
| provider_id | Required |
| billing_npi | Required schema field |
| rendering_npi | Required schema field |
| service_date | Required |
| claim_submission_date | Required |
| adjudication_date | Required schema field |
| procedure_code | Required |
| diagnosis_code | Required |
| place_of_service | Required schema field |
| revenue_code | Required schema field (facility claims) |
| claim_type | Required |
| claim_status | Required |
| billed_amount | Required schema field |
| allowed_amount | Required schema field |
| paid_amount | Required schema field |
| member_liability | Required schema field |
| service_line_count | Required schema field |

If required schema columns are missing, schema validation fails.

------------------------------------------------------------------------

## 1.2 Missing Required Field Rules

The following fields are checked for missing values:

| Rule | Condition |
|---|---|
| missing_claim_id | claim_id is missing |
| missing_member_id | member_id is missing |
| missing_provider_id | provider_id is missing |
| missing_service_date | service_date is missing |
| missing_claim_submission_date | claim_submission_date is missing |
| missing_procedure_code | procedure_code is missing |
| missing_diagnosis_code | diagnosis_code is missing |
| missing_claim_type | claim_type is missing |
| missing_claim_status | claim_status is missing |

A violation contributes to the rule score and marks the record as a
rule-based anomaly.

------------------------------------------------------------------------

## 1.3 Identifier Format Rules

| Rule | Expected Format |
|---|---|
| invalid_claim_id | `CLM` followed by one or more digits, e.g. `CLM123456` |
| invalid_member_id | `MEM` followed by one or more digits, e.g. `MEM123` |
| invalid_provider_id | `PRV` followed by one or more digits, e.g. `PRV123` |
| invalid_billing_npi | 10-digit numeric NPI |
| invalid_rendering_npi | 10-digit numeric NPI |
| invalid_procedure_code | Valid CPT (5-digit) or HCPCS code format |
| invalid_diagnosis_code | Valid ICD-10-CM format (letter followed by alphanumerics, e.g. `A01.1`) |

Any value not matching the expected pattern is flagged.

------------------------------------------------------------------------

## 1.4 Date Validation Rules

### Future Service Date

**Rule:** `future_service_date`

Flag when:

```
service_date > current_date
```

### Future Claim Submission Date

**Rule:** `future_claim_submission_date`

Flag when:

```
claim_submission_date > current_date
```

### Service Before Submission

**Rule:** `service_after_submission`

Flag when:

```
service_date > claim_submission_date
```

A claim cannot be submitted before the service occurs.

### Submission Before Adjudication

**Rule:** `submission_after_adjudication`

Flag when:

```
claim_submission_date > adjudication_date
AND adjudication_date IS NOT NULL
```

Adjudication cannot precede submission.

### Timely Filing Violation

**Rule:** `timely_filing_violation`

Flag when:

```
claim_submission_date - service_date > timely_filing_limit_days
```

The timely filing limit is an operational/contractual parameter (commonly
90–365 days depending on the payer agreement).

------------------------------------------------------------------------

## 1.5 Valid Category Rules

### Valid Claim Status Values

```
Paid
Denied
Pending
Adjusted
Voided
```

Any other value is flagged as `invalid_claim_status`.

### Valid Claim Type Values

```
Professional    (CMS-1500 / physician services)
Institutional   (UB-04 / facility/hospital)
Dental          (ADA claim form)
```

Any other value is flagged as `invalid_claim_type`.

### Valid Place of Service Codes

Standard CMS Place of Service codes, e.g.:

```
11    (Office)
21    (Inpatient Hospital)
22    (Outpatient Hospital)
23    (Emergency Room - Hospital)
31    (Skilled Nursing Facility)
```

Non-standard POS codes are flagged as `invalid_place_of_service`.

### Valid Diagnosis Code

**Rule:** `invalid_diagnosis_code`

Diagnosis codes must be valid, active ICD-10-CM codes. Deprecated or
retired codes are flagged.

### Valid Procedure Code

**Rule:** `invalid_procedure_code`

Procedure codes must be valid CPT or HCPCS Level II codes. Inactive or
invalid codes are flagged.

------------------------------------------------------------------------

## 1.6 Numeric Validation Rules

| Rule | Condition |
|---|---|
| negative_billed_amount | billed_amount < 0 |
| negative_allowed_amount | allowed_amount < 0 |
| negative_paid_amount | paid_amount < 0 |
| negative_member_liability | member_liability < 0 |
| paid_exceeds_billed | paid_amount > billed_amount |
| allowed_exceeds_billed | allowed_amount > billed_amount |
| negative_service_line_count | service_line_count < 0 |
| zero_service_lines | service_line_count = 0 AND claim has no detail lines |

------------------------------------------------------------------------

## 1.7 Business Consistency Rules

### Paid Claim with Denied Status on Resubmission

**Rule:** `paid_on_previously_denied`

Flag when:

```
claim_status = 'Paid'
AND a previous claim exists for the same business key with status = 'Denied'
AND no appeal record exists
```

Identifies claims paid without a documented appeal after denial.

### Zero Paid Amount on Paid Claim

**Rule:** `paid_claim_zero_amount`

Flag when:

```
claim_status = 'Paid'
AND paid_amount = 0
```

A claim with Paid status should have a non-zero paid amount.

### Diagnosis / Procedure Mismatch

**Rule:** `diagnosis_procedure_mismatch`

Flag when:

```
procedure_code is clinically inconsistent with primary diagnosis_code
```

The specific diagnosis-procedure compatibility rules are defined in the
clinical coding reference used by the organization.

### Inpatient Claim Without Revenue Code

**Rule:** `institutional_missing_revenue_code`

Flag when:

```
claim_type = 'Institutional'
AND revenue_code IS NULL
```

Institutional (facility) claims require revenue codes.

------------------------------------------------------------------------

## 1.8 Duplicate Record Rule

**Rule:** `duplicate_claim`

A record is flagged when another record has the same combination of:

```
member_id
provider_id
service_date
procedure_code
diagnosis_code
claim_type
```

Duplicates are detected using this business key combination.

------------------------------------------------------------------------

## 1.9 Rule Score and Rule Severity

Each violated rule contributes `1` to the record's `rule_score`.

```
rule_score = total number of violated rules
```

### Rule Severity

| Rule Score | Severity |
|---|---|
| 0 | Normal |
| 1 | Low |
| 2–3 | Medium |
| 4 or more | Critical |

A record with `rule_score > 0` is marked as a `rule_anomaly`.

------------------------------------------------------------------------

# 2. Known Anomaly Patterns

## 2.1 Data Completeness Patterns

- Missing claim ID
- Missing member ID
- Missing provider ID
- Missing service date
- Missing claim submission date
- Missing procedure code
- Missing diagnosis code
- Missing claim type
- Missing claim status

## 2.2 Identifier Quality Patterns

- Claim ID does not match `CLM<number>` format
- Member ID does not match `MEM<number>` format
- Provider ID does not match `PRV<number>` format
- Billing NPI or Rendering NPI is not a valid 10-digit number
- Procedure code does not match CPT/HCPCS format
- Diagnosis code does not match ICD-10-CM format

## 2.3 Date Anomaly Patterns

- Service date is in the future
- Claim submitted before service occurred
- Adjudication recorded before claim submission
- Timely filing window exceeded

## 2.4 Categorical Value Patterns

- Unknown claim status
- Unknown claim type
- Invalid place of service code
- Invalid or deprecated ICD-10-CM diagnosis code
- Invalid or inactive CPT/HCPCS procedure code

## 2.5 Numeric Patterns

- Negative billed, allowed, or paid amount
- Negative member liability
- Paid amount exceeds billed amount
- Allowed amount exceeds billed amount
- Zero service lines on a claim

## 2.6 Business Consistency Patterns

- Paid claim with zero paid amount
- Paid claim following denial with no appeal record
- Institutional claim missing revenue code
- Diagnosis / procedure code clinical mismatch

## 2.7 Duplicate Pattern

- Repeated claim business key:
  `member_id + provider_id + service_date + procedure_code + diagnosis_code + claim_type`

## 2.8 ML-Based Unusual Pattern

Isolation Forest identifies records that deviate from the normal claims
population. Key features used for claims anomaly detection include:

```
billed_amount
paid_amount
allowed_amount
service_line_count
claim_submission_lag_days
provider_avg_billed_amount
provider_avg_paid_amount
member_claim_frequency
paid_to_billed_ratio
diagnosis_procedure_diversity
```

For each ML anomaly, the system provides the top contributing features
with observed values, expected ranges, and deviation scores.

## 2.9 Cluster-Based Behavioral Pattern

K-Means groups claims records into behavioral clusters.

A high distance between a record and its assigned cluster center produces
a higher `cluster_risk_score`.

A high `cluster_risk_score` indicates unusual claims billing behavior
relative to the assigned cluster. The operational threshold is defined by
the ML model configuration.

> **Note:** The specific numeric threshold for `cluster_risk_score` is
> defined by the ML model configuration. This KB does not hard-code a
> threshold value. When the ML pipeline configuration is finalized, this
> section should be updated to reflect the configured threshold.

------------------------------------------------------------------------

# 3. Root Cause → Evidence Mappings

These mappings should be used as guidance for RAG explanations. The
evidence identifies what was observed; it does not always prove a
definitive operational root cause.

| Possible Root Cause / Issue | Evidence from System | Suggested Investigation |
|---|---|---|
| Required identifier not supplied | Missing ID rule violated | Check source extract and request/correct the missing identifier |
| NPI not valid or not registered | Invalid NPI format | Verify NPI in NPPES registry |
| Invalid procedure code | invalid_procedure_code rule | Check CPT/HCPCS reference for the service date period |
| Invalid or deprecated diagnosis code | invalid_diagnosis_code rule | Verify ICD-10-CM code for the service date period |
| Date entry or transformation error | Future date rule violated | Verify source date in the adjudication system |
| Claim submitted before service | service_after_submission rule | Verify service and submission dates in the source system |
| Timely filing issue | timely_filing_violation rule | Check original service date and contractual filing window |
| Payment inconsistency | paid_claim_zero_amount or paid_exceeds_billed | Review adjudication logic and fee schedule |
| Denial bypassed without appeal | paid_on_previously_denied rule | Review claim history and appeal records |
| Missing revenue code on facility claim | institutional_missing_revenue_code | Check UB-04 claim form and revenue code mapping |
| Invalid category mapping | Invalid status/type/POS rule | Check source values and mapping table |
| Numeric data error | Negative or excessive amount rule | Verify source calculation or fee schedule |
| Duplicate billing | Duplicate claim rule | Check claim history, resubmission, and dedup process |
| Unusual billing behavior | Isolation Forest anomaly + contributing features | Investigate features with largest deviation |
| Unusual cluster behavior | High cluster risk score | Compare with normal records in the assigned cluster |

------------------------------------------------------------------------

# 4. Resolution Procedures

## 4.1 Missing Required Field

1. Identify the missing field.
2. Check whether the source adjudication or billing system contains the value.
3. If absent at source, request the required value or route for correction.
4. If present at source but absent after ingestion, investigate ETL mapping.
5. Reprocess the corrected record.

## 4.2 Invalid Identifier Format

1. Compare the observed ID/NPI/code with the expected format.
2. Check source system formatting or provider registry.
3. Correct the value or mapping.
4. Revalidate the record.

## 4.3 Invalid Procedure or Diagnosis Code

1. Verify the code against the applicable CPT/HCPCS or ICD-10-CM reference
   for the service date year.
2. If the code is deprecated, identify the replacement code.
3. If the code is a transcription error, correct from the source claim.
4. Reprocess the corrected record.

## 4.4 Date Issues

1. Verify all dates against the source adjudication system.
2. Correct data-entry or transformation errors.
3. If timely filing is violated, check contractual filing window and route
   for exception handling if applicable.
4. Re-run validation.

## 4.5 Adjudication Amount Issues

1. Verify billed, allowed, and paid amounts against the fee schedule and
   adjudication rules.
2. Investigate paid_amount > billed_amount or paid_amount = 0 on a Paid claim.
3. Correct or re-adjudicate as appropriate.

## 4.6 Institutional Claim Missing Revenue Code

1. Retrieve the original UB-04 claim form.
2. Add the appropriate revenue code.
3. Re-adjudicate the claim.

## 4.7 Paid After Denial Without Appeal

1. Retrieve the claim history for the business key.
2. Confirm whether an appeal was filed.
3. If no appeal exists, route to claims audit for review.

## 4.8 Invalid Category Value

1. Compare the observed value with the allowed values list.
2. Check source-to-target mapping.
3. Correct the value or mapping.
4. Revalidate.

## 4.9 Duplicate Record

1. Compare duplicate records using the claims duplicate business key.
2. Determine whether the duplication resulted from:
   - Duplicate billing from the provider
   - Ingestion re-load
   - Legitimate resubmission after correction
3. Remove/merge the unintended duplicate according to operational policy.
4. Re-run the pipeline.

## 4.10 ML / Cluster Anomaly

1. Review `ml_risk_score`, `cluster_risk_score`, and `final_risk_score`.
2. Review ML contributing features.
3. Compare observed values with expected lower/upper ranges.
4. Investigate features with the largest deviation scores first.
5. Confirm whether the record is a true anomaly or an acceptable exception.
6. Apply operational correction if a data issue is confirmed.

------------------------------------------------------------------------

# 5. SLA Policies

The claims pipeline maps final severity to the following SLA:

| Final Severity | SLA |
|---|---|
| Normal | No Action |
| Warning | Review within 48 Hours |
| High | Review within 24 Hours |
| Critical | Immediate Review within 4 Hours |

## Final Severity Thresholds

| Final Risk Score | Severity |
|---|---|
| < 0.30 | Normal |
| 0.30 to < 0.55 | Warning |
| 0.55 to < 0.75 | High |
| >= 0.75 | Critical |

The final anomaly threshold may also be selected from evaluation data by
choosing the threshold with the best F1 score when ground-truth anomaly
labels are available.

### Escalation Conditions

Escalate immediately (bypassing normal SLA) when:

- Evidence of systematic duplicate billing across multiple claims for the
  same provider
- High-value claims (billed_amount significantly above expected range for
  procedure) combined with other anomaly signals
- Diagnosis / procedure mismatch on a high-cost claim
- Paid claim with no supporting authorization record where authorization is
  required

------------------------------------------------------------------------

# 6. Data Reconciliation Procedures

## 6.1 Schema Reconciliation

Compare incoming columns against the expected claims schema.

Investigate:

- Missing expected columns
- Unexpected columns
- Missing required values

## 6.2 Identifier Reconciliation

Validate:

- Claim ID format
- Member ID format
- Provider ID format
- Billing NPI and Rendering NPI (10-digit, valid in NPPES)

## 6.3 Date Reconciliation

Verify:

- Service date
- Claim submission date
- Adjudication date
- Date sequence (service → submission → adjudication)
- Timely filing window

## 6.4 Code Reconciliation

Verify:

- Procedure codes against CPT/HCPCS reference for the applicable service year
- Diagnosis codes against ICD-10-CM reference for the applicable service year
- Place of service codes against CMS POS code list

## 6.5 Amount Reconciliation

For high-risk records, reconcile:

```
billed_amount
allowed_amount
paid_amount
member_liability
```

Verify:

- paid_amount <= allowed_amount <= billed_amount (in typical scenarios)
- Paid amount is consistent with the applicable fee schedule
- Member liability + plan paid amount = allowed_amount

## 6.6 Duplicate Reconciliation

Compare records using:

```
member_id + provider_id + service_date + procedure_code + diagnosis_code + claim_type
```

Investigate whether repeated records resulted from duplicate billing,
ingestion re-load, or legitimate resubmissions.

## 6.7 Risk Reconciliation

For high-risk records, reconcile:

```
rule_based_evidence
ml_based_evidence
rule_risk_score
ml_risk_score
cluster_risk_score
final_risk_score
```

This allows the reviewer or RAG system to understand whether the risk
originated from deterministic rule violations, statistical deviation,
unusual cluster behavior, or a combination.

------------------------------------------------------------------------

# 7. Historical Resolutions

The current implementation does not contain a historical resolution dataset
for claims anomalies. This section is a placeholder for future resolved
cases. **Do not populate this section with fabricated examples.**

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

This section will be populated only after real claims anomalies are
resolved through the operational workflow.

------------------------------------------------------------------------

# 8. Business / Operational Rules

## 8.1 Rule-Based Anomaly Definition

A claims record is a rule-based anomaly when:

```
rule_score > 0
```

## 8.2 Hybrid Risk Scoring

The claims pipeline uses the same hybrid scoring framework as authorization:

```
final_risk_score =
    w1 × rule_risk_score
  + w2 × ml_risk_score
  + w3 × cluster_risk_score
```

The specific weights (w1, w2, w3) are defined by the ML model configuration
for the claims pipeline. Refer to the ML configuration when implemented.

### Score Meaning

- `rule_risk_score`: normalized severity based on number of violated rules
- `ml_risk_score`: normalized Isolation Forest anomaly risk
- `cluster_risk_score`: normalized distance from the assigned K-Means cluster
- `final_risk_score`: combined overall risk

## 8.3 Final Anomaly Decision

A claims record is marked as a final anomaly when:

```
final_risk_score >= selected anomaly threshold
```

When ground-truth labels are available, the threshold with the highest
F1 score is selected.

## 8.4 Evidence Output Rules

For rule-based anomalies, the output contains the violated rule names.

For ML anomalies, the output contains:

- Model name: Isolation Forest
- ML anomaly status
- ML risk/anomaly score
- Top contributing abnormal features
- Observed value
- Expected lower range
- Expected upper range
- Direction of deviation

## 8.5 RAG Handoff

The ML pipeline exports each anomalous claims record with the same
JSON structure used across all datasets:

```json
{
  "dataset": "claims",
  "anomalies": [
    {
      "record_id": "<claim_id>",
      "model_summary": {
        "final_anomaly": true,
        "final_severity": "<severity>",
        "final_risk_score": <score>,
        "risk_components": {
          "rule_risk_score": <score>,
          "ml_risk_score": <score>,
          "cluster_risk_score": <score>
        },
        "detection_sources": {
          "rule_anomaly": true,
          "ml_anomaly": true
        }
      },
      "rule_based_evidence": [
        { "rule": "<rule_name>", "status": "violated" }
      ],
      "ml_based_evidence": {
        "model": "Isolation Forest",
        "contributing_features": [
          {
            "feature": "<feature_name>",
            "observed": <value>,
            "expected_upper": <value>,
            "deviation_score": <score>
          }
        ]
      },
      "record_context": {
        "service_date": "<date>",
        "claim_submission_date": "<date>",
        "claim_type": "<type>",
        "claim_status": "<status>",
        "procedure_code": "<code>",
        "diagnosis_code": "<code>",
        "billed_amount": <value>,
        "paid_amount": <value>,
        "place_of_service": "<code>"
      },
      "sla": "<sla_string>"
    }
  ]
}
```

### How RAG Should Treat Each Field

| Field | RAG Treatment |
|---|---|
| `model_summary` | ML decision and combined evidence — treat as the overall anomaly signal |
| `final_anomaly` | Confirmed anomaly flag — do not discard |
| `final_severity` | Operational severity tier — drives SLA |
| `final_risk_score` | Overall risk signal — do not discard |
| `rule_risk_score` | Deterministic rule component of risk |
| `ml_risk_score` | Statistical/ML component of risk |
| `cluster_risk_score` | Behavioral/cluster component of risk |
| `rule_anomaly` | Whether deterministic rules were violated — do not discard |
| `ml_anomaly` | Whether ML model flagged the record — do not discard |
| `rule_based_evidence` | Specific rules violated — use to identify deterministic root cause indicators |
| `ml_based_evidence` | Statistical deviations — use to identify behavioral root cause indicators |
| `record_context` | Actual record field values — use for contextual investigation |
| `sla` | Operational priority and review deadline |

### ML / KB / RAG Responsibility Boundary

```
ML OUTPUT        → What happened? (observed evidence)
KNOWLEDGE BASE   → What does this pattern mean, what are the possible
                   causes, and what procedures apply? (domain knowledge)
RAG              → Based on the observed evidence and retrieved knowledge,
                   what is the likely root cause and what should be done?
                   (grounded reasoning)
```

RAG must **not** claim a definitive root cause unless the evidence
supports it. Use wording such as:

- **Likely root cause**
- **Possible root cause**
- **Supporting evidence**
- **Recommended investigation**

### RAG Workflow

```
ML JSON
  → Extract anomaly evidence
    → Identify dataset (claims)
      → Retrieve relevant domain KB (Claims KB)
        → Retrieve matching anomaly patterns
          → Retrieve Root Cause → Evidence mappings
            → Compare ML evidence against KB evidence
              → Determine likely root cause
                → Retrieve resolution procedure
                  → Apply SLA / business rules
                    → Generate RAG response
```

### RAG Output Structure

| Output Field | Description |
|---|---|
| Anomaly Summary | Brief description of what was detected |
| Severity | Final severity from model_summary |
| Risk | Final risk score and component breakdown |
| Key Evidence | Most significant rule and ML evidence |
| Likely Root Cause | Best-supported cause based on evidence + KB |
| Root Cause Confidence | Qualitative confidence level |
| Supporting Evidence | Evidence backing the likely root cause |
| Recommended Action | Steps from KB resolution procedures |
| SLA / Priority | Review deadline from SLA field |
| Validation Steps | Steps to confirm resolution |
