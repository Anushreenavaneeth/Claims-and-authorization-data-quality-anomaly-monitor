"""
Generation integration test.
"""

import json

from rag.ingestion.normalizer import RAGInputNormalizer
from rag.retrieval.retriever import Retriever
from rag.xai.analyzer import XAIAnalyzer

from .generator import Generator


INPUT_FILE = (
    "authorization_anomalies_for_rag.json"
)

TARGET_RECORD_ID = "AUTH04414"


# =========================================================
# Load ML output
# =========================================================

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    ml_data = json.load(
        file
    )


# =========================================================
# Find record
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
        f"{TARGET_RECORD_ID} not found."
    )


# =========================================================
# Normalize
# =========================================================

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


# =========================================================
# Retrieval
# =========================================================

print(
    "=" * 70
)

print(
    "RETRIEVAL → XAI → GENERATION TEST"
)

print(
    "=" * 70
)

print(
    f"\nRecord ID: "
    f"{anomaly['record_id']}"
)

print(
    f"Dataset: "
    f"{anomaly['dataset_type']}"
)


retriever = Retriever()

retrieval_result = (
    retriever.retrieve(
        anomaly
    )
)

record_result = (
    retrieval_result[
        "records"
    ][0]
)

retrieved_knowledge = (
    record_result.get(
        "results",
        []
    )
)


print(
    f"\nKnowledge chunks retrieved: "
    f"{len(retrieved_knowledge)}"
)


# =========================================================
# XAI
# =========================================================

print(
    "\nRunning XAI..."
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


# =========================================================
# Generation
# =========================================================

print(
    "\nRunning Generation..."
)

generator = Generator()

generation_result = (
    generator.generate(
        xai_result=xai_result,
        retrieved_knowledge=(
            retrieved_knowledge
        )
    )
)


# =========================================================
# Display
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "FINAL HUMAN-READABLE RESULT"
)

print(
    "=" * 70
)

print(
    json.dumps(
        generation_result,
        indent=2,
        ensure_ascii=False
    )
)


print(
    "\n"
    + "=" * 70
)

print(
    "GENERATION TEST COMPLETED"
)

print(
    "=" * 70
)