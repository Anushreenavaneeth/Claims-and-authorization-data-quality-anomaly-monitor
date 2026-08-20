"""
PHARMACY ML → RAG ADAPTER TEST
"""

import json

from rag.ingestion.adapters.pharmacy_adapter import (
    PharmacyAdapter
)


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = "final_output_2mb.json"

TARGET_RECORD_ID = "1003481680"


# =========================================================
# Header
# =========================================================

print("=" * 70)

print(
    "PHARMACY ML → RAG ADAPTER TEST"
)

print("=" * 70)


# =========================================================
# 1. Load Pharmacy ML Output
# =========================================================

print(
    "\n[1] Loading Pharmacy ML output..."
)

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    pharmacy_data = json.load(
        file
    )


# =========================================================
# 2. Detect Input Structure
# =========================================================

if isinstance(
    pharmacy_data,
    list
):

    anomalies = pharmacy_data

elif isinstance(
    pharmacy_data,
    dict
):

    anomalies = pharmacy_data.get(
        "anomalies",
        []
    )

else:

    raise TypeError(
        "Unsupported Pharmacy JSON structure."
    )


print(
    "Original anomaly count:",
    len(anomalies)
)


# =========================================================
# 3. Find Target Record
# =========================================================

target_record = None

for anomaly in anomalies:

    if str(
        anomaly.get(
            "record_id"
        )
    ) == TARGET_RECORD_ID:

        target_record = anomaly

        break


if target_record is None:

    raise ValueError(
        f"Pharmacy record "
        f"{TARGET_RECORD_ID} "
        "was not found."
    )


print(
    "Target record:",
    TARGET_RECORD_ID
)


# =========================================================
# 4. Adapt Record
# =========================================================

print(
    "\n[2] Adapting Pharmacy record..."
)

adapter = PharmacyAdapter()

adapted_record = (
    adapter.adapt_record(
        target_record
    )
)


print(
    "Dataset:",
    adapted_record.get(
        "dataset_type"
    )
)

print(
    "Record ID:",
    adapted_record.get(
        "record_id"
    )
)


# =========================================================
# 5. Check Required RAG Fields
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
    "behavior_based_evidence",
    "record_context",
    "sla",
    "source_explanation"
]


missing_fields = []

for field in required_fields:

    if field not in adapted_record:

        missing_fields.append(
            field
        )


if missing_fields:

    print(
        "Missing fields:",
        missing_fields
    )

    raise ValueError(
        "Pharmacy adapter output "
        "is missing required fields."
    )


print(
    "Required fields: PASS"
)


# =========================================================
# 6. Check Important Evidence
# =========================================================

print(
    "\n[4] Checking Pharmacy evidence..."
)


detection = adapted_record.get(
    "detection_summary",
    {}
)

ml_evidence = adapted_record.get(
    "ml_based_evidence",
    {}
)

behavior_evidence = adapted_record.get(
    "behavior_based_evidence",
    {})


print(
    "Final anomaly:",
    detection.get(
        "final_anomaly"
    )
)

print(
    "Final severity:",
    detection.get(
        "final_severity"
    )
)

print(
    "Final risk score:",
    detection.get(
        "final_risk_score"
    )
)

print(
    "Rule anomaly:",
    detection.get(
        "rule_anomaly"
    )
)

print(
    "ML anomaly:",
    detection.get(
        "ml_anomaly"
    )
)

print(
    "Behavior anomaly:",
    detection.get(
        "behavior_anomaly"
    )
)

print(
    "ML model:",
    ml_evidence.get(
        "model"
    )
)

print(
    "ML anomaly score:",
    ml_evidence.get(
        "anomaly_score"
    )
)

print(
    "Behavior evidence fields:",
    len(
        behavior_evidence
    )
)


# =========================================================
# 7. Display Adapted Record
# =========================================================

print(
    "\n[5] Adapted Pharmacy record:"
)

print(
    json.dumps(
        adapted_record,
        indent=2,
        ensure_ascii=False
    )
)


# =========================================================
# 8. Completion
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "PHARMACY ADAPTER TEST PASSED"
)

print(
    "=" * 70
)