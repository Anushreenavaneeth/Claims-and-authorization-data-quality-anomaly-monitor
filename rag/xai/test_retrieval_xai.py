"""
Integration test:

ML JSON
    ↓
Ingestion / Normalization
    ↓
Query Builder
    ↓
Retriever
    ↓
Actual Knowledge Base
    ↓
XAI Analyzer
"""

import json

from rag.ingestion.normalizer import RAGInputNormalizer
from rag.retrieval.retriever import Retriever
from rag.xai.analyzer import XAIAnalyzer


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = "authorization_anomalies_for_rag.json"

TARGET_RECORD_ID = "AUTH04414"


# =========================================================
# Load ML output
# =========================================================

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    ml_data = json.load(file)


# =========================================================
# Find target anomaly
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
# Header
# =========================================================

print(
    "=" * 70
)

print(
    "RETRIEVAL → XAI INTEGRATION TEST"
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


# =========================================================
# Initialize Retriever
# =========================================================

retriever = Retriever()


# =========================================================
# Run actual Retrieval
# =========================================================

print(
    "\n[1] Running actual knowledge retrieval..."
)

retrieval_result = retriever.retrieve(
    anomaly
)


# =========================================================
# Extract record-level retrieval result
# =========================================================

records = retrieval_result.get(
    "records",
    []
)

print(
    f"Records processed: "
    f"{retrieval_result.get('record_count', 0)}"
)


if not records:

    print(
        "No retrieval record was produced."
    )

    raise RuntimeError(
        "Retriever returned zero records."
    )


record_result = records[0]


query = record_result.get(
    "query",
    ""
)

retrieved_knowledge = record_result.get(
    "results",
    []
)

evidence_terms = record_result.get(
    "evidence_terms",
    []    
)


# =========================================================
# Display Query
# =========================================================

print(
    "\nGenerated Query:"
)

print(
    query
)


# =========================================================
# Display Evidence Terms
# =========================================================

print(
    "\nEvidence Terms:"
)

for term in evidence_terms:

    print(
        f"  - {term}"
    )


# =========================================================
# Display Retrieved Knowledge
# =========================================================

print(
    "\nRetrieved Knowledge:"
)

print(
    f"Knowledge chunks retrieved: "
    f"{len(retrieved_knowledge)}"
)


if not retrieved_knowledge:

    print(
        "No knowledge chunks passed "
        "the retrieval threshold."
    )

else:

    for index, result in enumerate(
        retrieved_knowledge,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        source = metadata.get(
            "source",
            "unknown"
        )

        category = metadata.get(
            "category",
            "unknown"
        )

        semantic_score = result.get(
            "semantic_score",
            0.0
        )

        evidence_score = result.get(
            "evidence_score",
            0.0
        )

        hybrid_score = result.get(
            "hybrid_score",
            0.0
        )

        print(
            f"\n[{index}] {source}"
        )

        print(
            f"Category: {category}"
        )

        print(
            f"Semantic Score: "
            f"{semantic_score:.4f}"
        )

        print(
            f"Evidence Score: "
            f"{evidence_score:.4f}"
        )

        print(
            f"Hybrid Score: "
            f"{hybrid_score:.4f}"
        )

        print(
            "Content:"
        )

        print(
            result.get(
                "text",
                ""
            )
        )


# =========================================================
# Run XAI
# =========================================================

print(
    "\n[2] Running XAI analysis..."
)

analyzer = XAIAnalyzer()

xai_result = analyzer.analyze(
    anomaly=anomaly,
    retrieved_knowledge=retrieved_knowledge
)


# =========================================================
# Display XAI Result
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "XAI RESULT"
)

print(
    "=" * 70
)

print(
    json.dumps(
        xai_result,
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
    "INTEGRATION TEST COMPLETED"
)

print(
    "=" * 70
)