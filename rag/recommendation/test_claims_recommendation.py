"""
Claims → Retrieval → XAI → Recommendation Test

Pipeline:

Claims ML JSON
    ↓
Claims Adapter
    ↓
RAG-compatible anomaly
    ↓
Knowledge Retrieval
    ↓
XAI Analysis
    ↓
Recommendation Builder
    ↓
Human-readable recommendation
"""

import json

from rag.ingestion.adapters.claims_adapter import (
    ClaimsAdapter
)

from rag.retrieval.retriever import (
    Retriever
)

from rag.xai.analyzer import (
    XAIAnalyzer
)

from .recommendation_builder import (
    RecommendationBuilder
)


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = (
    "tc_puf_anomaly_output.json"
)

TARGET_RECORD_ID = (
    "11512NC0060002"
)


# =========================================================
# Header
# =========================================================

print(
    "=" * 70
)

print(
    "CLAIMS → RETRIEVAL → XAI → RECOMMENDATION TEST"
)

print(
    "=" * 70
)


# =========================================================
# 1. Load Claims ML Output
# =========================================================

print(
    "\n[1] Loading Claims ML output..."
)

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    claims_data = json.load(
        file
    )


# =========================================================
# 2. Find Target Claims Anomaly
# =========================================================

target_anomaly = None

for anomaly in claims_data.get(
    "anomalies",
    []
):

    record = anomaly.get(
        "record",
        {}
    )

    if str(
        record.get("plan_id")
    ) == TARGET_RECORD_ID:

        target_anomaly = anomaly

        break


if target_anomaly is None:

    raise ValueError(
        f"Claims record "
        f"{TARGET_RECORD_ID} "
        "was not found."
    )


print(
    f"Target record: "
    f"{TARGET_RECORD_ID}"
)


# =========================================================
# 3. Adapt Claims ML Output
# =========================================================

print(
    "\n[2] Adapting Claims record..."
)

adapter = ClaimsAdapter()

anomaly = adapter.adapt_record(
    target_anomaly
)


print(
    "Dataset:",
    anomaly.get(
        "dataset_type"
    )
)

print(
    "Record ID:",
    anomaly.get(
        "record_id"
    )
)


# =========================================================
# 4. Knowledge Retrieval
# =========================================================

print(
    "\n[3] Running knowledge retrieval..."
)

retriever = Retriever()

retrieval_result = retriever.retrieve(
    anomaly
)


retrieval_records = (
    retrieval_result.get(
        "records",
        []
    )
)


if not retrieval_records:

    raise RuntimeError(
        "Retriever returned no records."
    )


record_result = (
    retrieval_records[0]
)


retrieved_knowledge = (
    record_result.get(
        "results",
        []
    )
)


print(
    "Knowledge chunks retrieved:",
    len(
        retrieved_knowledge
    )
)


if not retrieved_knowledge:

    raise RuntimeError(
        "No knowledge chunks were retrieved."
    )


# =========================================================
# 5. XAI Analysis
# =========================================================

print(
    "\n[4] Running XAI analysis..."
)

xai_analyzer = XAIAnalyzer()

xai_result = (
    xai_analyzer.analyze(
        anomaly=anomaly,

        retrieved_knowledge=(
            retrieved_knowledge
        )
    )
)


print(
    "XAI analysis completed."
)


# =========================================================
# 6. Recommendation Builder
# =========================================================

print(
    "\n[5] Running recommendation builder..."
)

recommendation_builder = (
    RecommendationBuilder()
)


recommendation_result = (
    recommendation_builder.build(
        xai_result=xai_result,

        retrieved_knowledge=(
            retrieved_knowledge
        )
    )
)


print(
    "Recommendation generation completed."
)


# =========================================================
# 7. Final Recommendation Result
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "FINAL CLAIMS RECOMMENDATION RESULT"
)

print(
    "=" * 70
)

print(
    json.dumps(
        recommendation_result,
        indent=2,
        ensure_ascii=False
    )
)


# =========================================================
# 8. Admin Summary
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
    recommendation_result.get(
        "admin_summary",
        ""
    )
)


# =========================================================
# 9. Employee Action
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
    recommendation_result.get(
        "employee_action",
        ""
    )
)


# =========================================================
# 10. Final Recommendation
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "FINAL RECOMMENDATION"
)

print(
    "=" * 70
)

print(
    recommendation_result.get(
        "recommendation",
        ""
    )
)


# =========================================================
# 11. Completion
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "CLAIMS → RETRIEVAL → XAI → "
    "RECOMMENDATION TEST COMPLETED"
)

print(
    "=" * 70
)