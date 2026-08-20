"""
End-to-end Recommendation Engine test.

Pipeline:

ML JSON
    ↓
Normalization
    ↓
Knowledge Retrieval
    ↓
XAI Analysis
    ↓
Recommendation Engine
    ↓
Human-readable recommendation
"""

import json

from rag.ingestion.normalizer import RAGInputNormalizer
from rag.retrieval.retriever import Retriever
from rag.xai.analyzer import XAIAnalyzer

from .recommendation_builder import RecommendationBuilder


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = (
    "authorization_anomalies_for_rag.json"
)

TARGET_RECORD_ID = "AUTH04414"


# =========================================================
# Load ML Output
# =========================================================

print(
    "=" * 70
)

print(
    "RETRIEVAL → XAI → RECOMMENDATION TEST"
)

print(
    "=" * 70
)

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    ml_data = json.load(
        file
    )


# =========================================================
# Find Target Record
# =========================================================

target_record = None

for record in ml_data:

    if record.get(
        "record_id"
    ) == TARGET_RECORD_ID:

        target_record = record

        break


if target_record is None:

    raise ValueError(
        f"{TARGET_RECORD_ID} was not found "
        f"in {INPUT_FILE}"
    )


print(
    f"\nRecord ID: "
    f"{target_record['record_id']}"
)

print(
    f"Dataset: "
    f"{target_record['dataset_type']}"
)


# =========================================================
# Normalize
# =========================================================

print(
    "\n[1] Normalizing ML output..."
)

normalizer = (
    RAGInputNormalizer()
)

normalized = (
    normalizer.normalize(
        [target_record]
    )
)

anomaly = normalized[
    "records"
][0]

print(
    "Normalization completed."
)


# =========================================================
# Retrieval
# =========================================================

print(
    "\n[2] Running knowledge retrieval..."
)

retriever = Retriever()

retrieval_result = (
    retriever.retrieve(
        anomaly
    )
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
    f"Knowledge chunks retrieved: "
    f"{len(retrieved_knowledge)}"
)


# =========================================================
# XAI
# =========================================================

print(
    "\n[3] Running XAI analysis..."
)

xai_analyzer = (
    XAIAnalyzer()
)

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
# Recommendation Engine
# =========================================================

print(
    "\n[4] Running recommendation engine..."
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
# Final Result
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "FINAL RECOMMENDATION RESULT"
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
# Human-readable Sections
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


print(
    "\n"
    + "=" * 70
)

print(
    "RECOMMENDATION TEST COMPLETED"
)

print(
    "=" * 70
)