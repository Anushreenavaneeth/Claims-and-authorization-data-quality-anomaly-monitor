# Healthcare Data Quality Anomaly Patterns

## Purpose

This document defines known healthcare data-quality anomaly patterns used by the RAG system.

It provides supporting knowledge for mapping observed rule-based and ML-based evidence to:

- Known anomaly patterns
- Likely causes
- Evidence to investigate
- Relevant remediation procedures

This document is a supporting knowledge source.

It does not replace:

- Authorization Knowledge Base
- Pharmacy Knowledge Base
- Claims Knowledge Base
- Common Healthcare Data Quality Rules
- Dataset-specific business rules

The ML model provides observed evidence.

The Knowledge Base provides domain knowledge.

RAG uses both to identify the most likely root cause and recommendation.


---

# 1. Invalid Date Sequence

## Pattern

A date relationship violates the expected chronological sequence between related healthcare events.

Examples include:

- Service date occurring before an allowed authorization date
- Authorization date and service date violating the configured business sequence
- Start date occurring after end date
- Related healthcare event dates occurring in an invalid order

## Common Indicators

- `invalid_date_sequence`
- Date fields are present but occur in an invalid order
- Related dates conflict with expected workflow
- Multiple records show the same date-ordering problem
- Date-related rule violation

## Evidence to Check

Review:

- Record ID
- Authorization date
- Service date
- Start date
- End date
- Submission date
- Processing timestamps
- Dataset-specific date rules
- Source-system timestamps

## Likely Causes

Possible causes include:

- Incorrect source data
- Manual data-entry error
- Date transformation failure
- Field mapping error
- Time-zone conversion issue
- Incorrect date format
- Source-system defect
- Incorrect business-rule implementation

## Recommended Knowledge Sources

Prioritize:

1. Domain-specific date rules
2. Invalid-date remediation procedures
3. Dataset schema
4. Date validation procedures
5. Relevant pipeline SOP

## Remediation Direction

Verify the affected date fields against the applicable domain rule.

Correct the source or transformation logic when the date relationship is invalid.

Do not automatically modify the record without validating the expected business sequence.


---

# 2. Missing Required Field

## Pattern

A required field is missing, null, or empty when a valid value is expected.

## Common Indicators

- Missing required field
- Null required field
- Empty required field
- `missing_service_date`
- Missing-value rule violation
- Completeness degradation

## Evidence to Check

Review:

- Dataset
- Record ID
- Field name
- Field value
- Required/optional status
- Null count
- Missing-value percentage
- Domain schema
- Source-system output

## Likely Causes

Possible causes include:

- Incomplete upstream transmission
- Source-system issue
- Mapping failure
- Schema change
- Extraction failure
- Missing documentation
- Incorrect required-field configuration
- Data transformation issue

## Important Distinction

A missing field is not automatically a missing document.

For example:

`missing_service_date`

means the service-date field is absent or invalid.

It should not automatically be interpreted as:

`missing_documentation`.

The RAG system must use the specific evidence before determining the root cause.

## Remediation Direction

Identify the missing field.

Verify whether the field is required according to the applicable schema and domain rules.

Trace the field to the upstream source and transformation stage.

Correct the source, mapping, or transformation issue before reprocessing.


---

# 3. Invalid Urgency

## Pattern

The urgency value is missing, invalid, inconsistent, or outside the permitted domain values.

## Common Indicators

- `invalid_urgency`
- Unexpected urgency value
- Null urgency where required
- Urgency value outside configured values
- Urgency inconsistent with the applicable business rule

## Evidence to Check

Review:

- Record ID
- Urgency value
- Authorization type
- Service type
- Procedure
- Source system
- Allowed urgency values
- Related business rules

## Likely Causes

Possible causes include:

- Invalid source value
- Mapping error
- Incorrect transformation
- Unsupported urgency value
- Missing business-rule validation
- Source-system configuration issue

## Remediation Direction

Validate the urgency value against the Authorization-specific rule.

Correct the source or mapping issue.

Revalidate the record before downstream processing.


---

# 4. Processing Time Anomaly

## Pattern

A record requires significantly more or less processing time than expected.

## Common Indicators

- High processing time
- Processing time above expected upper threshold
- Processing time below expected lower threshold
- High ML anomaly score
- Provider processing-time deviation
- SLA breach or near-breach

Relevant ML features may include:

- `processing_time_hours`
- `provider_avg_processing_time`
- `processing_time_provider_deviation`

## Evidence to Check

Review:

- Processing start timestamp
- Processing completion timestamp
- Processing time
- Expected processing range
- Provider baseline
- Historical processing time
- Submission channel
- Authorization status
- SLA
- Resubmission count
- Missing documentation

## Likely Causes

Possible causes include:

- Processing backlog
- Upstream delay
- Provider-specific delay
- Missing documentation
- Repeated resubmission
- Workflow bottleneck
- Source-system delay
- Operational issue

## Remediation Direction

Compare observed processing time with:

- Expected processing range
- Provider baseline
- SLA threshold

Determine whether the delay is isolated or systemic.

Investigate missing documentation, resubmissions, provider behavior, and upstream processing before reprocessing.


---

# 5. Provider Processing Deviation

## Pattern

A provider's processing behavior significantly deviates from the expected provider baseline.

## Common Indicators

Relevant ML features may include:

- `provider_avg_processing_time`
- `processing_time_provider_deviation`
- Provider-specific anomaly
- Provider processing time above expected range

## Evidence to Check

Review:

- Provider ID
- Provider baseline
- Provider average processing time
- Current processing time
- Deviation from baseline
- Service type
- Historical provider activity
- Rule violations
- Submission channel

## Likely Causes

Possible causes include:

- Provider workflow issue
- Provider-specific operational delay
- Provider data-quality issue
- Increased processing complexity
- Repeated resubmission
- Upstream provider transmission issue

## Remediation Direction

Compare the record with the provider's historical baseline.

Determine whether the deviation is isolated or repeated.

If repeated, investigate the provider/source process rather than treating the individual record as an isolated anomaly.


---

# 6. Excessive Resubmission

## Pattern

A record or provider has significantly more resubmissions than expected.

## Common Indicators

Relevant ML features may include:

- `resubmission_count`
- `provider_avg_resubmission`
- High resubmission deviation
- Repeated submission attempts

## Evidence to Check

Review:

- Record ID
- Resubmission count
- Provider average resubmission
- Submission history
- Rejection reasons
- Missing fields
- Missing documentation
- Validation failures

## Likely Causes

Possible causes include:

- Missing information
- Incorrect documentation
- Validation failure
- Provider submission error
- Mapping issue
- Repeated correction/rejection cycle

## Remediation Direction

Review the submission history and rejection/validation reasons.

Identify the original cause of the resubmission.

Correct the underlying data or documentation issue rather than repeatedly resubmitting the same invalid record.


---

# 7. Missing Documentation

## Pattern

Required supporting documentation is missing or incomplete.

## Common Indicators

- `missing_document_count > 0`
- Required document unavailable
- Documentation-related rule violation
- Authorization cannot be completed
- Record requires resubmission

## Evidence to Check

Review:

- Record ID
- Document type
- Missing document count
- Required document status
- Submission history
- Resubmission count
- Processing timestamps
- Authorization status
- Available attachments

## Likely Causes

Possible causes include:

- Incomplete upstream transmission
- Missing provider documentation
- Source-system issue
- Attachment failure
- Submission workflow issue
- Documentation mapping issue

## Remediation Direction

Identify the missing required document.

Verify whether the document was expected for the specific service or authorization type.

Obtain or retransmit the required documentation before reprocessing.


---

# 8. Duplicate Records

## Pattern

Multiple records represent the same business event or transaction when only one valid record is expected.

## Common Indicators

- Duplicate record identifiers
- Same entity and service combination appearing multiple times
- Duplicate transaction identifiers
- Duplicate batch identifiers
- Sudden increase in duplicate rate
- Repeated records received from upstream

## Evidence to Check

Review:

- Record ID
- Transaction ID
- Batch ID
- Entity identifiers
- Service date
- Submission timestamp
- Source system
- Transmission history

## Likely Causes

Possible causes include:

- Duplicate upstream transmission
- Retry without idempotency
- Batch replay
- Integration failure
- Incorrect deduplication logic

## Remediation Direction

Verify the duplicate records against the upstream transmission.

Identify the valid record.

Reconcile the duplicate transmission before reprocessing.


---

# 9. Schema or Field Validity Anomaly

## Pattern

A field or record does not conform to the expected schema, datatype, structure, or allowed values.

## Common Indicators

- Invalid datatype
- Invalid field format
- Unexpected field
- Missing required field
- Invalid enumeration value
- Schema validation failure

## Evidence to Check

Review:

- Dataset schema
- Field name
- Expected datatype
- Observed datatype
- Required/optional status
- Allowed values
- Source payload
- Transformation mapping

## Likely Causes

Possible causes include:

- Schema change
- Source-system change
- Mapping failure
- Transformation error
- Incorrect field configuration
- Version mismatch

## Remediation Direction

Compare the observed structure with the applicable schema.

Identify whether the issue originates from the source, mapping, transformation, or schema version.

Correct the responsible component before reprocessing.


---

# 10. Reconciliation Failure

## Pattern

Records or aggregates fail to reconcile between source and downstream systems.

## Common Indicators

- Record count mismatch
- Amount mismatch
- Transaction mismatch
- Batch mismatch
- Source-to-target discrepancy

## Evidence to Check

Review:

- Source record count
- Target record count
- Batch ID
- Transaction ID
- Aggregate amounts
- Processing status
- Reconciliation logs
- Transmission history

## Likely Causes

Possible causes include:

- Missing transmission
- Duplicate transmission
- Partial batch processing
- Transformation failure
- Failed records
- Timing mismatch
- Integration issue

## Remediation Direction

Identify the reconciliation boundary.

Compare source and target records.

Determine whether the discrepancy is caused by missing, duplicated, failed, or delayed records.

Reconcile the affected records before downstream reprocessing.


---

# 11. Multi-Signal Anomaly

## Pattern

Multiple independent anomaly signals identify the same record as abnormal.

For example:

- Rule anomaly + ML anomaly
- Multiple rule violations
- ML anomaly + SLA risk
- ML anomaly + provider deviation
- Missing documentation + processing delay

## Evidence to Check

Review:

- Rule-based evidence
- ML-based evidence
- Contributing features
- Anomaly score
- Risk score
- Correlation results
- SLA risk
- Record context

## Likely Causes

The root cause should not be inferred solely from the presence of multiple anomaly signals.

The evidence should be correlated to determine whether the signals represent:

- One underlying issue
- Multiple related issues
- Independent issues occurring in the same record

## Remediation Direction

Prioritize the strongest evidence-supported root cause.

Avoid treating every detected anomaly as a separate root cause when multiple signals can be explained by one upstream issue.


---

# 12. Evidence-to-Pattern Matching Rules

The RAG system should use observed evidence to identify the most relevant known anomaly pattern.

Examples:

| Observed Evidence | Preferred Pattern |
|---|---|
| `invalid_date_sequence` | Invalid Date Sequence |
| `missing_service_date` | Missing Required Field |
| `invalid_urgency` | Invalid Urgency |
| `processing_time_hours` above expected range | Processing Time Anomaly |
| `provider_avg_processing_time` above expected range | Provider Processing Deviation |
| `processing_time_provider_deviation` above expected range | Provider Processing Deviation |
| `provider_avg_resubmission` above expected range | Excessive Resubmission |
| `missing_document_count > 0` | Missing Documentation |
| Duplicate record identifiers | Duplicate Records |
| Schema validation failure | Schema or Field Validity Anomaly |
| Source/target count mismatch | Reconciliation Failure |

Exact rule names and feature names should receive stronger retrieval relevance than generic words such as:

- anomaly
- healthcare
- data quality
- processing
- validation


---

# 13. RAG Usage Principle

The ML model provides observed evidence.

This document provides known anomaly-pattern knowledge.

The RAG system should combine:

ML Evidence
+
Domain Knowledge
+
Common Healthcare Knowledge
+
Remediation Knowledge
+
Troubleshooting Knowledge
+
SLA / Operational Knowledge

to identify the most likely explanation and recommended action.

The RAG system must not invent a root cause that is unsupported by the observed evidence or retrieved knowledge.


---

# 14. Historical Resolutions

Historical resolutions are reserved for future use.

No fabricated historical cases should be added.

Once real resolved cases become available, they can be incorporated as additional evidence for similar future anomalies.


---

# 15. Retrieval Priority

When multiple knowledge sources are available, retrieval should prioritize:

1. Exact rule or feature match
2. Domain-specific knowledge
3. Known anomaly pattern
4. Root-cause/evidence mapping
5. Remediation procedure
6. Troubleshooting procedure
7. SLA / operational procedure
8. Generic healthcare data-quality concepts

Generic pipeline documentation should support the explanation but should not dominate retrieval when more specific evidence exists.