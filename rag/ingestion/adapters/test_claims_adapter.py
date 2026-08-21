"""
Test Claims ML Output Adapter.
"""

import json

from .claims_adapter import ClaimsAdapter


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = (
    "tc_puf_anomaly_output.json"
)


# =========================================================
# Header
# =========================================================

print("=" * 70)
print("CLAIMS ML → RAG ADAPTER TEST")
print("=" * 70)


# =========================================================
# Load Claims Output
# =========================================================

print("\n[1] Loading Claims ML output...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    claims_output = json.load(
        file
    )


print(
    "Top-level type:",
    type(claims_output).__name__
)

print(
    "Original anomaly count:",
    len(
        claims_output.get(
            "anomalies",
            []
        )
    )
)


# =========================================================
# Adapt
# =========================================================

print(
    "\n[2] Converting Claims output..."
)

adapter = ClaimsAdapter()

records = adapter.adapt(
    claims_output
)


print(
    "Adapted records:",
    len(records)
)


# =========================================================
# Validate Basic Structure
# =========================================================

print(
    "\n[3] Checking RAG-compatible structure..."
)

required_fields = [
    "dataset_type",
    "record_id",
    "detection_summary",
    "rule_based_evidence",
    "ml_based_evidence",
    "record_context",
    "sla"
]


first_record = records[0]

missing_fields = [
    field
    for field in required_fields
    if field not in first_record
]


if missing_fields:

    raise ValueError(
        "Missing fields: "
        + ", ".join(
            missing_fields
        )
    )


print(
    "Required fields: PASS"
)


# =========================================================
# Display First Record
# =========================================================

print(
    "\n[4] First normalized Claims record:"
)

print(
    json.dumps(
        first_record,
        indent=2,
        ensure_ascii=False
    )
)


# =========================================================
# Summary
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "CLAIMS ADAPTER TEST COMPLETED"
)

print(
    "=" * 70
)