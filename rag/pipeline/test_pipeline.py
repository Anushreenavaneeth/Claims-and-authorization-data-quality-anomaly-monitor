"""
End-to-end test for the unified RAG pipeline.

ML Output
    ↓
Ingestion
    ↓
Retrieval
    ↓
XAI
    ↓
Recommendation
"""

import json

from .pipeline import RAGPipeline


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = "authorization_anomalies_for_rag.json"

TARGET_RECORD_ID = "AUTH04414"


# =========================================================
# Header
# =========================================================

print("=" * 70)
print("UNIFIED RAG PIPELINE TEST")
print("=" * 70)


# =========================================================
# Load ML Output
# =========================================================

print("\n[1] Loading ML output...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    ml_output = json.load(file)


print(
    f"Total ML records loaded: "
    f"{len(ml_output)}"
)


# =========================================================
# Find Target Record
# =========================================================

print(
    f"\n[2] Selecting record: "
    f"{TARGET_RECORD_ID}"
)

target_record = None

for record in ml_output:

    if (
        isinstance(record, dict)
        and record.get("record_id")
        == TARGET_RECORD_ID
    ):

        target_record = record

        break


if target_record is None:

    raise ValueError(
        f"Record {TARGET_RECORD_ID} "
        "was not found in the ML output."
    )


print(
    f"Record ID: "
    f"{target_record.get('record_id')}"
)

print(
    f"Dataset: "
    f"{target_record.get('dataset_type')}"
)


# =========================================================
# Initialize Pipeline
# =========================================================

print(
    "\n[3] Initializing RAG pipeline..."
)

pipeline = RAGPipeline()


# =========================================================
# Run Complete Pipeline
# =========================================================

print(
    "\n[4] Running complete RAG pipeline..."
)

result = pipeline.process_single(
    target_record
)


# =========================================================
# Pipeline Status
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "PIPELINE COMPLETED"
)

print(
    "=" * 70
)


# =========================================================
# Retrieval Information
# =========================================================

retrieval = result.get(
    "retrieval",
    {}
)

print(
    "\nRETRIEVAL"
)

print(
    f"Queries generated: "
    f"{retrieval.get('query_count', 0)}"
)

print(
    f"Knowledge chunks retrieved: "
    f"{retrieval.get('knowledge_count', 0)}"
)


# =========================================================
# XAI Information
# =========================================================

xai_result = result.get(
    "xai",
    {}
)

xai_analysis = xai_result.get(
    "xai_analysis",
    {}
)

print(
    "\nXAI"
)

print(
    f"Anomaly: "
    f"{xai_analysis.get('matched_anomaly_pattern', 'Unknown')}"
)

print(
    f"Explanation: "
    f"{xai_analysis.get('explanation', 'N/A')}"
)


# =========================================================
# Recommendation
# =========================================================

recommendation = result.get(
    "recommendation",
    {}
)

print(
    "\n"
    + "=" * 70
)

print(
    "RECOMMENDATION"
)

print(
    "=" * 70
)

print(
    f"Severity: "
    f"{recommendation.get('severity', 'Unknown')}"
)

print(
    f"Priority: "
    f"{recommendation.get('priority', 'Unknown')}"
)

print(
    f"Anomaly: "
    f"{recommendation.get('anomaly', 'Unknown')}"
)


# =========================================================
# Admin Summary
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "ADMIN SUMMARY"
)

print(
    "=" * 70
)

print(
    recommendation.get(
        "admin_summary",
        "No admin summary generated."
    )
)


# =========================================================
# Employee Action
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "EMPLOYEE ACTION"
)

print(
    "=" * 70
)

print(
    recommendation.get(
        "employee_action",
        "No employee action generated."
    )
)


# =========================================================
# Final Recommendation
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "FINAL HUMAN-READABLE RECOMMENDATION"
)

print(
    "=" * 70
)

print(
    recommendation.get(
        "recommendation",
        "No recommendation generated."
    )
)


# =========================================================
# Complete JSON Result
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "COMPLETE PIPELINE JSON"
)

print(
    "=" * 70
)

print(
    json.dumps(
        result,
        indent=2,
        ensure_ascii=False
    )
)


# =========================================================
# Completion
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "UNIFIED RAG PIPELINE TEST COMPLETED"
)

print(
    "=" * 70
)