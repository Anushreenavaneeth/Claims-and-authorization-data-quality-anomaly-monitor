# Authorization Data Quality Knowledge Base

## Scope

This knowledge base covers **Authorization-specific** data quality rules,
anomaly patterns, root cause mappings, resolution procedures, SLA policies,
reconciliation procedures, historical resolutions, and business/operational
rules for the Authorization Data Quality and Anomaly Detection pipeline.

It does **not** include general healthcare, claims, or pharmacy rules.

**KB Architecture:**

```
Common Healthcare Data Quality KB
  └── Generic healthcare data quality concepts

Authorization KB  ← This file
  └── Authorization-specific knowledge

Pharmacy KB
  └── Pharmacy-specific knowledge

Claims KB
  └── Claims-specific knowledge
```

For generic healthcare data quality concepts (schema validation, completeness,
uniqueness, freshness, volume checks, etc.) see the
**Common Healthcare Data Quality KB**.

------------------------------------------------------------------------

# 1. Authorization Data Quality Rules

## 1.1 Schema / Required Columns

The authorization dataset is expected to contain:

  Field                    Requirement
  ------------------------ -----------------------
  authorization_id         Required
  member_id                Required
  provider_id              Required
  authorization_date       Required
  service_date             Required
  service_type             Required
  procedure_code           Required
  place_of_service         Expected schema field
  urgency                  Required schema field
  authorization_status     Required
  submission_channel       Required schema field
  authorization_type       Required schema field
  processing_time_hours    Required schema field
  missing_document_count   Required schema field
  resubmission_count       Required schema field

If required schema columns are missing, schema validation fails.

------------------------------------------------------------------------

## 1.2 Missing Required Field Rules

The following fields are checked for missing values:

  Rule                           Condition
  ------------------------------ ---------------------------------
  missing_authorization_id       authorization_id is missing
  missing_member_id              member_id is missing
  missing_provider_id            provider_id is missing
  missing_authorization_date     authorization_date is missing
  missing_service_date           service_date is missing
  missing_service_type           service_type is missing
  missing_procedure_code         procedure_code is missing
  missing_authorization_status   authorization_status is missing

A violation contributes to the rule score and marks the record as a
rule-based anomaly.

------------------------------------------------------------------------

## 1.3 Identifier Format Rules

  -----------------------------------------------------------------------
  Rule                                Expected Format
  ----------------------------------- -----------------------------------
  invalid_authorization_id            `AUTH` followed by one or more
                                      digits, e.g. `AUTH123`

  invalid_member_id                   `MEM` followed by one or more
                                      digits, e.g. `MEM123`

  invalid_provider_id                 `PRV` followed by one or more
                                      digits, e.g. `PRV123`
  -----------------------------------------------------------------------

Any value not matching the expected pattern is flagged.

------------------------------------------------------------------------

## 1.4 Date Validation Rules

### Future Authorization Date

**Rule:** `future_authorization_date`

Flag when:

``` text
authorization_date > current date
```

### Future Service Date

**Rule:** `future_service_date`

Flag when:

``` text
service_date > current date
```

### Invalid Date Sequence

**Rule:** `invalid_date_sequence`

Flag when:

``` text
service_date < authorization_date
AND authorization_type is not Retrospective
```

Retrospective authorizations are excluded from this rule.

------------------------------------------------------------------------

## 1.5 Valid Category Rules

### Valid Urgency Values

``` text
Routine
Urgent
Emergency
```

Any other value is flagged as `invalid_urgency`.

### Valid Authorization Status Values

``` text
Approved
Denied
Pending
```

Any other value is flagged as `invalid_status`.

### Valid Submission Channel Values

``` text
Portal
EDI
Fax
Phone
```

Any other value is flagged as `invalid_submission_channel`.

### Valid Authorization Type Values

``` text
Initial
Extension
Concurrent
Retrospective
```

Any other value is flagged as `invalid_authorization_type`.

------------------------------------------------------------------------

## 1.6 Numeric Validation Rules

  Rule                         Condition
  ---------------------------- ------------------------------
  negative_processing_time     processing_time_hours \< 0
  excessive_processing_time    processing_time_hours \> 720
  negative_missing_documents   missing_document_count \< 0
  negative_resubmissions       resubmission_count \< 0

------------------------------------------------------------------------

## 1.7 Business Consistency Rule

### Approved Authorization with High Missing Documents

**Rule:** `approved_high_missing_docs`

Flag when:

``` text
authorization_status = Approved
AND missing_document_count >= 5
```

This identifies a potentially inconsistent approval record where a high
number of required documents is recorded as missing.

------------------------------------------------------------------------

## 1.8 Duplicate Record Rule

**Rule:** `duplicate_record`

A record is flagged when another record has the same combination of:

``` text
member_id
provider_id
authorization_date
service_date
procedure_code
```

Duplicates are detected using this business key combination.

------------------------------------------------------------------------

## 1.9 Rule Score and Rule Severity

Each violated rule contributes `1` to the record's `rule_score`.

``` text
rule_score = total number of violated rules
```

### Rule Severity

  Rule Score   Severity
  ------------ ----------
  0            Normal
  1            Low
  2--3         Medium
  4 or more    Critical

A record with `rule_score > 0` is marked as a `rule_anomaly`.

------------------------------------------------------------------------

# 2. Known Anomaly Patterns

The system recognizes the following anomaly patterns.

## 2.1 Data Completeness Patterns

-   Missing authorization ID
-   Missing member ID
-   Missing provider ID
-   Missing authorization date
-   Missing service date
-   Missing service type
-   Missing procedure code
-   Missing authorization status

## 2.2 Identifier Quality Patterns

-   Authorization ID does not match the expected `AUTH<number>` format
-   Member ID does not match the expected `MEM<number>` format
-   Provider ID does not match the expected `PRV<number>` format

## 2.3 Date Anomaly Patterns

-   Authorization date is in the future
-   Service date is in the future
-   Service occurs before authorization for a non-retrospective
    authorization

## 2.4 Categorical Value Patterns

-   Unknown urgency value
-   Unknown authorization status
-   Unknown submission channel
-   Unknown authorization type

## 2.5 Numeric Patterns

-   Negative processing time
-   Processing time greater than 720 hours
-   Negative missing document count
-   Negative resubmission count

## 2.6 Business Consistency Pattern

-   Authorization marked Approved while missing_document_count is 5 or
    greater

## 2.7 Duplicate Pattern

-   Repeated authorization business-key combination:
    `member_id + provider_id + authorization_date + service_date + procedure_code`

## 2.8 ML-Based Unusual Pattern

Isolation Forest identifies records that deviate from the normal
authorization population using:

``` text
processing_time_hours
missing_document_count
resubmission_count
authorization_to_service_days
provider_avg_processing_time
provider_avg_resubmission
provider_avg_missing_docs
processing_time_provider_deviation
```

For each ML anomaly, the system can provide the top contributing
features that fall outside the calculated normal range.

## 2.9 Cluster-Based Behavioral Pattern

K-Means groups records into behavioral clusters.

A high distance between a record and its assigned cluster center
produces a higher `cluster_risk_score`.

A high `cluster_risk_score` indicates unusual behavior relative to the
assigned cluster. The operational threshold is defined by the ML model
configuration.

> **Note:** No ML implementation or configuration file was found in this
> workspace that defines a specific numeric threshold for
> `cluster_risk_score`. Therefore, a hard-coded threshold value is not
> stated here. When the ML pipeline configuration is finalized, this
> section should be updated to reflect the configured threshold.

------------------------------------------------------------------------

# 3. Root Cause → Evidence Mappings

These mappings should be used as guidance for RAG/GenAI explanations.
The evidence identifies what was observed; it does not always prove a
definitive operational root cause.

  -----------------------------------------------------------------------------
  Possible Root Cause /   Evidence from System          Suggested Investigation
  Issue                                                 
  ----------------------- ----------------------------- -----------------------
  Required identifier not Missing ID rule violated      Check source extract
  supplied                                              and request/correct the
                                                        missing identifier

  Identifier formatting   Invalid ID rule violated      Validate source
  issue                                                 formatting or
                                                        identifier mapping

  Incorrect or corrupted  Future date rule violated     Verify source date and
  date                                                  correct invalid value

  Authorization/service   Invalid date sequence         Verify whether the
  timing inconsistency                                  record should be
                                                        Retrospective or
                                                        correct the dates

  Invalid category        Invalid                       Check source system
  mapping                 urgency/status/channel/type   values and mapping
                                                        table

  Invalid numeric value   Negative numeric rule         Verify source
                                                        calculation or
                                                        transformation

  Excessive processing    processing_time_hours \> 720  Investigate workflow
  duration                or ML evidence above normal   delay, backlog, or
                          range                         incorrect duration
                                                        calculation

  Documentation           Approved + high missing       Review documentation
  inconsistency           document count                status and approval
                                                        record

  Duplicate ingestion or  Duplicate record rule         Check ingestion,
  repeated submission                                   resubmission, or
                                                        deduplication process

  Unusual authorization   Isolation Forest anomaly +    Investigate the
  behavior                contributing features         features with the
                                                        largest deviation

  Unusual cluster         High cluster risk score       Compare with normal
  behavior                                              records in the assigned
                                                        behavioral cluster
  -----------------------------------------------------------------------------

------------------------------------------------------------------------

# 4. Resolution Procedures

## 4.1 Missing Required Field

1.  Identify the missing field.
2.  Check whether the source record contains the value.
3.  If absent at source, request the required value or route for
    correction.
4.  If present at source but absent after ingestion, investigate
    mapping/transformation.
5.  Reprocess the corrected record.

## 4.2 Invalid Identifier Format

1.  Compare the observed ID with the expected format.
2.  Check source-system formatting.
3.  Correct the value or mapping.
4.  Revalidate the record.

## 4.3 Future Date

1.  Verify the date against the source system.
2.  Determine whether the value is a data-entry or transformation error.
3.  Correct the date.
4.  Re-run validation.

## 4.4 Invalid Date Sequence

1.  Check authorization type.
2.  If the authorization is truly retrospective, verify that it is
    correctly labelled `Retrospective`.
3.  Otherwise correct the authorization/service dates.
4.  Re-run validation.

## 4.5 Invalid Category Value

1.  Compare the observed value with the allowed values.
2.  Check source-to-target mapping.
3.  Correct the value or mapping.
4.  Revalidate.

## 4.6 Numeric Value Issue

1.  Verify source value.
2.  Check calculation/transformation logic.
3.  Correct invalid negative or excessive values.
4.  Reprocess the record.

## 4.7 Duplicate Record

1.  Compare duplicate records using the duplicate business key.
2.  Determine whether the duplicate is a legitimate repeated event or
    ingestion duplication.
3.  Remove/merge the unintended duplicate according to operational
    policy.
4.  Re-run the pipeline.

## 4.8 ML / Cluster Anomaly

1.  Review `ml_risk_score`, `cluster_risk_score`, and
    `final_risk_score`.
2.  Review ML contributing features.
3.  Compare observed values with expected lower/upper ranges.
4.  Investigate the largest deviations first.
5.  Confirm whether the record is a true anomaly or an acceptable
    exception.
6.  Apply operational correction if a data issue is confirmed.

------------------------------------------------------------------------

# 5. SLA Policies

The current implementation maps final severity to the following SLA:

  Final Severity   SLA
  ---------------- ---------------------------------
  Normal           No Action
  Warning          Review within 48 Hours
  High             Review within 24 Hours
  Critical         Immediate Review within 4 Hours

## Final Severity Thresholds

  Final Risk Score   Severity
  ------------------ ----------
  \< 0.30            Normal
  0.30 to \< 0.55    Warning
  0.55 to \< 0.75    High
  \>= 0.75           Critical

The final anomaly threshold may also be selected from evaluation data by
choosing the threshold with the best F1 score when ground-truth anomaly
labels are available.

------------------------------------------------------------------------

# 6. Data Reconciliation Procedures

The implemented authorization pipeline supports the following
reconciliation approach.

## 6.1 Schema Reconciliation

Compare incoming columns against the expected authorization schema.

Investigate:

-   Missing expected columns
-   Unexpected columns
-   Missing required values

## 6.2 Identifier Reconciliation

Validate:

-   Authorization ID format
-   Member ID format
-   Provider ID format

Records failing validation should be compared with the upstream source
or mapping logic.

## 6.3 Date Reconciliation

Verify:

-   Authorization date
-   Service date
-   Date sequence
-   Future dates

For retrospective authorizations, confirm that the authorization type is
correctly represented.

## 6.4 Duplicate Reconciliation

Compare records using:

``` text
member_id
provider_id
authorization_date
service_date
procedure_code
```

Investigate whether repeated records resulted from duplicate ingestion
or represent legitimate repeated transactions.

## 6.5 Risk Reconciliation

For high-risk records, reconcile:

``` text
rule_based_evidence
ml_based_evidence
rule_risk_score
ml_risk_score
cluster_risk_score
final_risk_score
```

This allows the downstream reviewer or RAG system to understand whether
the risk originated from deterministic rule violations, statistical
deviation, unusual cluster behavior, or a combination.

------------------------------------------------------------------------

# 7. Historical Resolutions

The current implementation does not contain a separate historical
resolution dataset or a record of previously confirmed resolutions.

Therefore, the knowledge base should treat this section as a placeholder
for future resolved cases. **Do not populate this section with
fabricated examples.**

Recommended future structure:

``` text
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

------------------------------------------------------------------------

# 8. Business / Operational Rules

## 8.1 Rule-Based Anomaly Definition

A record is a rule-based anomaly when:

``` text
rule_score > 0
```

## 8.2 Hybrid Risk Scoring

The current implementation calculates:

``` text
final_risk_score =
    0.35 × rule_risk_score
  + 0.45 × ml_risk_score
  + 0.20 × cluster_risk_score
```

### Score Meaning

-   `rule_risk_score`: normalized severity based on number of violated
    rules
-   `ml_risk_score`: normalized Isolation Forest anomaly risk
-   `cluster_risk_score`: normalized distance from the assigned K-Means
    cluster center
-   `final_risk_score`: combined overall risk

## 8.3 Final Anomaly Decision

A record is marked as a final anomaly when:

``` text
final_risk_score >= selected anomaly threshold
```

When ground-truth labels are available, the implementation evaluates
thresholds and can select the threshold with the highest F1 score.

## 8.4 Evidence Output Rules

For rule-based anomalies, the output contains the violated rule names.

For ML anomalies, the output contains:

-   Model name: Isolation Forest
-   ML anomaly status
-   ML risk/anomaly score
-   Top contributing abnormal features
-   Observed value
-   Expected lower range
-   Expected upper range
-   Direction of deviation

## 8.5 RAG Handoff

The ML pipeline exports each anomalous authorization record with the
following JSON structure:

``` json
{
  "dataset": "authorization",
  "anomalies": [
    {
      "record_id": "AUTH01859",
      "model_summary": {
        "final_anomaly": true,
        "final_severity": "Warning",
        "final_risk_score": 0.4181,
        "risk_components": {
          "rule_risk_score": 0.5,
          "ml_risk_score": 0.5132,
          "cluster_risk_score": 0.0943
        },
        "detection_sources": {
          "rule_anomaly": true,
          "ml_anomaly": true
        }
      },
      "rule_based_evidence": [
        { "rule": "invalid_date_sequence", "status": "violated" },
        { "rule": "invalid_urgency",        "status": "violated" }
      ],
      "ml_based_evidence": {
        "model": "Isolation Forest",
        "contributing_features": [
          {
            "feature": "processing_time_hours",
            "observed": 235.17,
            "expected_upper": 65.37,
            "deviation_score": 4.098
          },
          {
            "feature": "processing_time_provider_deviation",
            "observed": 201.98,
            "expected_upper": 44.32,
            "deviation_score": 4.962
          }
        ]
      },
      "record_context": {
        "authorization_date": "2026-06-21",
        "service_date": "2026-06-19",
        "service_type": "Physical Therapy",
        "authorization_status": "Approved",
        "authorization_type": "Initial",
        "urgency": null,
        "submission_channel": "Portal",
        "processing_time_hours": 235.17,
        "missing_document_count": 1,
        "resubmission_count": 1
      },
      "sla": "Review within 48 Hours"
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
| `record_context` | Actual record values — use for contextual investigation |
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
    → Identify dataset (authorization)
      → Retrieve relevant domain KB
        → Retrieve matching anomaly patterns
          → Retrieve Root Cause → Evidence mappings
            → Compare ML evidence against KB evidence
              → Determine likely root cause
                → Retrieve resolution procedure
                  → Apply SLA / business rules
                    → Generate RAG response
```

### RAG Output Structure

The RAG response for each anomaly should contain:

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
