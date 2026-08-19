# Claims + Pharmacy Data Ingestion and Validation

Starter prototype using the team's current Claims and Pharmacy schemas.

## Install
pip install -r requirements.txt

## Run Claims
python src/main.py --input data/mock_claims.csv --schema config/claims_schema.json --output output

## Run Pharmacy
python src/main.py --input data/mock_pharmacy.csv --schema config/pharmacy_schema.json --output output

The mock data intentionally contains errors so validation can be demonstrated.

## Run tests
python -m pytest tests/ -v

Outputs:
- *_valid.csv
- *_invalid.csv
- *_validation_report.json

The JSON schema files are provisional and should be updated if the team changes the expected schema or business rules.

## Validation checks performed
- **Schema**: required columns present / unexpected columns (unexpected = WARNING only, does not fail a row)
- **Completeness**: fields listed in `not_null_columns` (or, if that key is omitted, all `required_columns` minus any listed in `conditional_required`) must not be null/blank. The schema files currently omit `not_null_columns` and rely on the default — add it explicitly to a schema only if a column needs to diverge from that default (required as a header, but nullable without a formal conditional rule).
- **Conditional completeness**: e.g. `denial_code` is only required when `claim_status == DENIED` (a PAID/PENDING claim with no denial code is valid; a DENIED claim missing one is flagged)
- **Type**: dates parsed with a strict format (`date_format` in schema, default `%Y-%m-%d`) so ambiguous/loose date strings are rejected rather than silently coerced; numerics parsed via `pd.to_numeric`
- **Domain**: `claim_status` restricted to PAID / PENDING / DENIED
- **Range**: no negative amounts / costs / processing times
- **Uniqueness**: no duplicate `claim_id`

A row is marked invalid if it trips any ERROR-level check. The overall report `status` is FAIL only if at least one ERROR-level issue exists (WARNING-only issues, like an unexpected column, do not fail the run).

## Ingestion notes
- All CSV columns are read as raw strings (`dtype=str`) so pandas never silently reinterprets identifiers (e.g. dropping leading zeros from a code like `00123`). Numeric/date coercion happens explicitly in the validator, per the schema.
- The loader resets the DataFrame index after load, so row alignment stays consistent even if the loader is later extended to pre-filter rows.

## Exit codes (for CI / Airflow orchestration)
`main.py` exits `0` on a clean pass and `1` if the report status is `FAIL`, so automated pipelines can halt on bad data.