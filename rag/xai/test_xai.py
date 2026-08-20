"""
Test the XAI analyzer using one Authorization anomaly.
"""

import json

from rag.ingestion.normalizer import RAGInputNormalizer
from rag.xai.analyzer import XAIAnalyzer


# =========================================================
# Load ML input
# =========================================================

with open(
    "authorization_anomalies_for_rag.json",
    "r",
    encoding="utf-8"
) as file:

    ml_data = json.load(file)


# =========================================================
# Select AUTH04414
# =========================================================

target_record = None

for record in ml_data:

    if record.get(
        "record_id"
    ) == "AUTH04414":

        target_record = record
        break


if target_record is None:

    raise ValueError(
        "AUTH04414 was not found."
    )


# =========================================================
# Normalize
# =========================================================

normalizer = RAGInputNormalizer()

normalized = normalizer.normalize(
    [target_record]
)

anomaly = normalized[
    "records"
][0]


# =========================================================
# Temporary retrieved knowledge
#
# We will replace this with the actual Retrieval
# output after confirming XAI works.
# =========================================================

retrieved_knowledge = [
    {
        "metadata": {
            "source": "anomaly_patterns.md",
            "category": "data_quality"
        },

        "semantic_score": 0.80,

        "evidence_score": 0.90,

        "hybrid_score": 0.85,

        "text": (
            "Invalid Date Sequence: "
            "The service date occurs before the "
            "authorization date. This can indicate "
            "incorrect source data, date transformation "
            "issues, or upstream transmission problems. "
            "Verify the source dates and correct the "
            "invalid sequence before reprocessing."
        )
    }
]


# =========================================================
# Run XAI
# =========================================================

analyzer = XAIAnalyzer()

result = analyzer.analyze(
    anomaly=anomaly,
    retrieved_knowledge=retrieved_knowledge
)


# =========================================================
# Display result
# =========================================================

print(
    "=" * 70
)

print(
    "XAI TEST - AUTH04414"
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