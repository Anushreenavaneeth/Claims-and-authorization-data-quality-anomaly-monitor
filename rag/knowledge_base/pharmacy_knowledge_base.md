# Pharmacy Data Quality Knowledge Base

## Scope

This knowledge base covers **Pharmacy-specific** data quality rules,
anomaly patterns, root cause mappings, resolution procedures, SLA policies,
reconciliation procedures, historical resolutions, and business/operational
rules for the Pharmacy Data Quality and Anomaly Detection pipeline.

It does **not** include authorization-specific, claims-specific, or generic
healthcare rules. For generic concepts (schema validation, completeness,
uniqueness, freshness, volume checks, etc.) see the
**Common Healthcare Data Quality KB**.

**KB Architecture:**

```
Common Healthcare Data Quality KB
  └── Generic healthcare data quality concepts

Authorization KB
  └── Authorization-specific knowledge

Pharmacy KB  ← This file
  └── Pharmacy-specific knowledge

Claims KB
  └── Claims-specific knowledge
```

------------------------------------------------------------------------

# 1. Pharmacy Data Quality Rules

## 1.1 Schema / Required Columns

The pharmacy dataset is expected to contain:

| Field | Requirement |
|---|---|
| pharmacy_claim_id | Required |
| member_id | Required |
| prescriber_npi | Required |
| pharmacy_npi | Required |
| ndc_code | Required |
| drug_name | Required schema field |
| fill_date | Required |
| days_supply | Required schema field |
| quantity_dispensed | Required schema field |
| ingredient_cost | Required schema field |
| dispensing_fee | Required schema field |
| copay_amount | Required schema field |
| plan_paid_amount | Required schema field |
| prescription_number | Required schema field |
| refill_number | Required schema field |
| claim_status | Required |
| submission_channel | Required schema field |
| formulary_tier | Required schema field |
| generic_indicator | Required schema field |
| controlled_substance_schedule | Required schema field |

If required schema columns are missing, schema validation fails.

------------------------------------------------------------------------

## 1.2 Missing Required Field Rules

The following fields are checked for missing values:

| Rule | Condition |
|---|---|
| missing_pharmacy_claim_id | pharmacy_claim_id is missing |
| missing_member_id | member_id is missing |
| missing_prescriber_npi | prescriber_npi is missing |
| missing_pharmacy_npi | pharmacy_npi is missing |
| missing_ndc_code | ndc_code is missing |
| missing_fill_date | fill_date is missing |
| missing_claim_status | claim_status is missing |

A violation contributes to the rule score and marks the record as a
rule-based anomaly.

------------------------------------------------------------------------

## 1.3 Identifier Format Rules

| Rule | Expected Format |
|---|---|
| invalid_pharmacy_claim_id | `RX` followed by one or more digits, e.g. `RX123456` |
| invalid_member_id | `MEM` followed by one or more digits, e.g. `MEM123` |
| invalid_prescriber_npi | 10-digit numeric NPI, e.g. `1234567890` |
| invalid_pharmacy_npi | 10-digit numeric NPI, e.g. `1234567890` |
| invalid_ndc_code | 11-digit numeric NDC in `NNNNNNNNNNN` format or `NNNNN-NNNN-NN` format |

Any value not matching the expected pattern is flagged.

------------------------------------------------------------------------

## 1.4 Date Validation Rules

### Future Fill Date

**Rule:** `future_fill_date`

Flag when:

```
fill_date > current_date
```

### Fill Date Before Member Enrollment

**Rule:** `fill_date_before_enrollment`

Flag when:

```
fill_date < member_enrollment_date
```

A prescription cannot be filled before a member is enrolled.

### Early Refill

**Rule:** `early_refill`

Flag when:

```
fill_date < (previous_fill_date + days_supply × early_refill_threshold)
```

An early refill occurs when a refill is dispensed before the previous
supply is reasonably exhausted. The early_refill_threshold is an
operational parameter (commonly 0.75, meaning before 75% of the previous
days_supply is consumed).

------------------------------------------------------------------------

## 1.5 Valid Category Rules

### Valid Claim Status Values

```
Paid
Rejected
Reversed
Pending
```

Any other value is flagged as `invalid_claim_status`.

### Valid Submission Channel Values

```
POS       (Point of Sale)
Mail Order
Specialty
```

Any other value is flagged as `invalid_submission_channel`.

### Valid Generic Indicator Values

```
Y    (Generic dispensed)
N    (Brand dispensed)
```

Any other value is flagged as `invalid_generic_indicator`.

### Valid Controlled Substance Schedule Values

```
II
III
IV
V
Non-Controlled
```

Any other value is flagged as `invalid_controlled_substance_schedule`.

### Valid Formulary Tier Values

```
Tier 1    (Generic)
Tier 2    (Preferred Brand)
Tier 3    (Non-Preferred Brand)
Tier 4    (Specialty)
Non-Formulary
```

Any other value is flagged as `invalid_formulary_tier`.

------------------------------------------------------------------------

## 1.6 Numeric Validation Rules

| Rule | Condition |
|---|---|
| negative_days_supply | days_supply < 0 |
| excessive_days_supply | days_supply > 365 |
| negative_quantity_dispensed | quantity_dispensed < 0 |
| negative_ingredient_cost | ingredient_cost < 0 |
| negative_dispensing_fee | dispensing_fee < 0 |
| negative_copay | copay_amount < 0 |
| negative_plan_paid | plan_paid_amount < 0 |

------------------------------------------------------------------------

## 1.7 NDC Code Validation Rule

**Rule:** `invalid_ndc_not_in_formulary`

Flag when:

```
ndc_code is not found in the active drug reference/formulary database
```

An NDC code that does not exist in the FDA drug database or the plan
formulary is a data quality issue.

**Rule:** `ndc_drug_name_mismatch`

Flag when:

```
drug_name does not correspond to the expected drug name for ndc_code
```

------------------------------------------------------------------------

## 1.8 Business Consistency Rules

### Controlled Substance with Excessive Days Supply

**Rule:** `controlled_substance_excessive_days_supply`

Flag when:

```
controlled_substance_schedule IN ('II', 'III')
AND days_supply > 30
```

Schedule II and III controlled substances are typically limited to a
30-day supply under standard clinical guidelines.

### Brand Dispensed Against Generic Available

**Rule:** `brand_dispensed_generic_available`

Flag when:

```
generic_indicator = 'N'
AND a generic equivalent exists in the formulary
AND no DAW (Dispense As Written) override code is present
```

This identifies potential formulary compliance issues.

### Paid Claim with Rejected NDC

**Rule:** `paid_claim_rejected_ndc`

Flag when:

```
claim_status = 'Paid'
AND ndc_code is in the rejected/excluded drug list
```

------------------------------------------------------------------------

## 1.9 Duplicate Record Rule

**Rule:** `duplicate_pharmacy_claim`

A record is flagged when another record has the same combination of:

```
member_id
prescriber_npi
pharmacy_npi
ndc_code
fill_date
```

Duplicates are detected using this business key combination.

------------------------------------------------------------------------

## 1.10 Rule Score and Rule Severity

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

- Missing pharmacy claim ID
- Missing member ID
- Missing prescriber NPI
- Missing pharmacy NPI
- Missing NDC code
- Missing fill date
- Missing claim status

## 2.2 Identifier Quality Patterns

- Pharmacy claim ID does not match `RX<number>` format
- Member ID does not match `MEM<number>` format
- Prescriber NPI is not a valid 10-digit number
- Pharmacy NPI is not a valid 10-digit number
- NDC code does not match 11-digit format

## 2.3 Date Anomaly Patterns

- Fill date is in the future
- Fill date precedes member enrollment date
- Early refill before previous supply is exhausted

## 2.4 Categorical Value Patterns

- Unknown claim status
- Unknown submission channel
- Unknown generic indicator
- Unknown controlled substance schedule
- Unknown formulary tier

## 2.5 Numeric Patterns

- Negative days supply
- Days supply greater than 365
- Negative quantity dispensed
- Negative ingredient cost
- Negative dispensing fee
- Negative copay or plan paid amount

## 2.6 Drug Identifier Patterns

- NDC code not found in formulary or drug reference database
- Drug name does not match NDC code

## 2.7 Business Consistency Patterns

- Controlled substance (Schedule II/III) with days supply exceeding 30
- Brand dispensed when a generic equivalent is available without a DAW override
- Paid claim where the NDC is on the excluded/rejected drug list

## 2.8 Duplicate Pattern

- Repeated pharmacy claim business key:
  `member_id + prescriber_npi + pharmacy_npi + ndc_code + fill_date`

## 2.9 ML-Based Unusual Pattern

Isolation Forest identifies records that deviate from the normal pharmacy
population. Key features used for pharmacy anomaly detection include:

```
days_supply
quantity_dispensed
ingredient_cost
refill_number
controlled_substance_schedule (encoded)
early_refill_rate
prescriber_avg_controlled_rate
prescriber_avg_claim_count
pharmacy_avg_ingredient_cost
brand_rate
```

For each ML anomaly, the system provides the top contributing features
with observed values, expected ranges, and deviation scores.

## 2.10 Cluster-Based Behavioral Pattern

K-Means groups pharmacy records into behavioral clusters.

A high distance between a record and its assigned cluster center produces
a higher `cluster_risk_score`.

A high `cluster_risk_score` indicates unusual pharmacy dispensing behavior
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
| NPI not valid or not registered | Invalid NPI format or NPI not in provider registry | Verify NPI in NPPES registry |
| NDC code invalid or not in formulary | invalid_ndc_code or not_in_formulary rule | Check FDA NDC database and plan formulary |
| Drug name / NDC mismatch | ndc_drug_name_mismatch rule | Verify NDC-to-drug mapping in reference table |
| Fill date error | Future date or pre-enrollment date rule | Verify source date in POS system |
| Early refill — possible diversion | early_refill rule | Review refill history and compare with days supply |
| Controlled substance compliance issue | controlled_substance_excessive_days_supply | Review prescriber order and clinical guidelines |
| Formulary compliance issue | brand_dispensed_generic_available | Review DAW code and formulary policy |
| Paid claim for excluded drug | paid_claim_rejected_ndc | Check excluded drug list and adjudication logic |
| Invalid category mapping | Invalid status/channel/tier/indicator rule | Check source values and mapping table |
| Numeric data error | Negative or excessive numeric rule | Verify source calculation or transformation |
| Duplicate dispensing | Duplicate pharmacy claim rule | Check POS system, re-submission, or dedup process |
| Unusual dispensing behavior | Isolation Forest anomaly + contributing features | Investigate features with largest deviation |
| Unusual cluster behavior | High cluster risk score | Compare with normal records in the assigned cluster |

------------------------------------------------------------------------

# 4. Resolution Procedures

## 4.1 Missing Required Field

1. Identify the missing field.
2. Check whether the source POS or adjudication system contains the value.
3. If absent at source, request the required value or route for correction.
4. If present at source but absent after ingestion, investigate ETL mapping.
5. Reprocess the corrected record.

## 4.2 Invalid Identifier Format

1. Compare the observed ID/NPI/NDC with the expected format.
2. Check source system formatting or NPI registry.
3. Correct the value or mapping.
4. Revalidate the record.

## 4.3 Invalid NDC Code

1. Look up the NDC code in the FDA drug database.
2. If invalid: investigate source system drug reference.
3. If valid but not in formulary: check formulary update schedule and drug
   exception process.
4. Correct or flag for formulary review.

## 4.4 Fill Date Issues

1. Verify the fill date against the POS dispensing record.
2. Determine whether the value is a data-entry or system clock error.
3. Correct the date.
4. Re-run validation.

## 4.5 Early Refill

1. Retrieve the refill history for the member and drug.
2. Calculate the expected earliest refill date based on previous days supply.
3. Determine whether the early refill is a true early dispense or a date
   entry error.
4. If confirmed early, route to clinical review per controlled substance policy.

## 4.6 Controlled Substance Compliance

1. Verify the prescription order for days supply.
2. Check applicable state and federal guidelines for the scheduled substance.
3. If the days supply exceeds the allowed limit, route to clinical/compliance
   review.

## 4.7 Formulary Issue

1. Confirm generic equivalent availability in the current formulary.
2. Check for a valid DAW (Dispense As Written) override code.
3. If no valid override, route for formulary compliance review.

## 4.8 Invalid Category Value

1. Compare the observed value with the allowed values list.
2. Check source-to-target mapping.
3. Correct the value or mapping.
4. Revalidate.

## 4.9 Numeric Value Issue

1. Verify source value from POS or adjudication system.
2. Check calculation/transformation logic.
3. Correct invalid negative or excessive values.
4. Reprocess the record.

## 4.10 Duplicate Record

1. Compare duplicate records using the pharmacy duplicate business key.
2. Determine whether the duplication resulted from:
   - Repeated POS submission
   - Ingestion re-load
   - Legitimate separate fill events
3. Remove/merge the unintended duplicate according to operational policy.
4. Re-run the pipeline.

## 4.11 ML / Cluster Anomaly

1. Review `ml_risk_score`, `cluster_risk_score`, and `final_risk_score`.
2. Review ML contributing features.
3. Compare observed values with expected lower/upper ranges.
4. Investigate features with the largest deviation scores first.
5. Confirm whether the record is a true anomaly or an acceptable exception.
6. Apply operational correction if a data issue is confirmed.

------------------------------------------------------------------------

# 5. SLA Policies

The pharmacy pipeline maps final severity to the following SLA:

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

- Controlled substance anomaly is detected and clinical safety may be
  impacted
- Evidence suggests potential drug diversion (high early refill rate +
  high controlled substance rate + high cash payment rate)
- Paid claim for an excluded or recalled drug is detected

------------------------------------------------------------------------

# 6. Data Reconciliation Procedures

## 6.1 Schema Reconciliation

Compare incoming columns against the expected pharmacy schema.

Investigate:

- Missing expected columns
- Unexpected columns
- Missing required values

## 6.2 Identifier Reconciliation

Validate:

- Pharmacy claim ID format
- Member ID format
- Prescriber NPI (10-digit, valid in NPPES)
- Pharmacy NPI (10-digit, valid in NPPES)
- NDC code format and presence in drug reference

## 6.3 Date Reconciliation

Verify:

- Fill date
- Fill date vs. enrollment date
- Refill date vs. previous fill + days supply

## 6.4 Drug Reference Reconciliation

Verify:

- NDC code is active in the FDA drug database
- Drug name matches the NDC code
- NDC code is on the current formulary (or has a valid non-formulary override)

## 6.5 Duplicate Reconciliation

Compare records using:

```
member_id + prescriber_npi + pharmacy_npi + ndc_code + fill_date
```

Investigate whether repeated records resulted from duplicate POS submission,
ingestion re-load, or legitimate separate dispensing events.

## 6.6 Risk Reconciliation

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
for pharmacy anomalies. This section is a placeholder for future resolved
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

This section will be populated only after real pharmacy anomalies are
resolved through the operational workflow.

------------------------------------------------------------------------

# 8. Business / Operational Rules

## 8.1 Rule-Based Anomaly Definition

A pharmacy record is a rule-based anomaly when:

```
rule_score > 0
```

## 8.2 Hybrid Risk Scoring

The pharmacy pipeline uses the same hybrid scoring framework as
authorization:

```
final_risk_score =
    w1 × rule_risk_score
  + w2 × ml_risk_score
  + w3 × cluster_risk_score
```

The specific weights (w1, w2, w3) are defined by the ML model configuration
for the pharmacy pipeline. Refer to the ML configuration when implemented.

### Score Meaning

- `rule_risk_score`: normalized severity based on number of violated rules
- `ml_risk_score`: normalized Isolation Forest anomaly risk
- `cluster_risk_score`: normalized distance from the assigned K-Means cluster
- `final_risk_score`: combined overall risk

## 8.3 Final Anomaly Decision

A pharmacy record is marked as a final anomaly when:

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

The ML pipeline exports each anomalous pharmacy record with the same
JSON structure used across all datasets:

```json
{
  "dataset": "pharmacy",
  "anomalies": [
    {
      "record_id": "<pharmacy_claim_id>",
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
        "fill_date": "<date>",
        "ndc_code": "<ndc>",
        "drug_name": "<name>",
        "days_supply": <value>,
        "quantity_dispensed": <value>,
        "controlled_substance_schedule": "<schedule>",
        "claim_status": "<status>",
        "refill_number": <value>
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
    → Identify dataset (pharmacy)
      → Retrieve relevant domain KB (Pharmacy KB)
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
