"""
Claims → RAG Retrieval Integration Test

Flow:

Claims ML Output
    ↓
Claims Adapter
    ↓
Normalized Claims Record
    ↓
Query Builder
    ↓
Retriever
    ↓
Knowledge Base
"""

import json

from rag.ingestion.adapters.claims_adapter import ClaimsAdapter
from rag.retrieval.retriever import Retriever


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = "tc_puf_anomaly_output.json"

TARGET_RECORD_ID = "11512NC0060002"


# =========================================================
# Header
# =========================================================

print("=" * 70)
print("CLAIMS → RETRIEVAL TEST")
print("=" * 70)


# =========================================================
# 1. Load Claims ML Output
# =========================================================

print("\n[1] Loading Claims ML output...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    claims_output = json.load(file)


if not isinstance(
    claims_output,
    dict
):

    raise ValueError(
        "Claims ML output must be a JSON object."
    )


anomalies = claims_output.get(
    "anomalies",
    []
)


if not isinstance(
    anomalies,
    list
):

    raise ValueError(
        "Claims output does not contain "
        "a valid 'anomalies' list."
    )


target_anomaly = None

for anomaly in anomalies:

    if not isinstance(
        anomaly,
        dict
    ):
        continue

    record = anomaly.get(
        "record",
        {}
    )

    if record.get(
        "plan_id"
    ) == TARGET_RECORD_ID:

        target_anomaly = anomaly

        break


if target_anomaly is None:

    raise ValueError(
        f"Claims record "
        f"{TARGET_RECORD_ID} "
        f"was not found."
    )


print(
    f"Target record: "
    f"{TARGET_RECORD_ID}"
)


# =========================================================
# 2. Adapt Claims Record
# =========================================================

print(
    "\n[2] Adapting Claims record..."
)

adapter = ClaimsAdapter()

adapted_record = (
    adapter.adapt_record(
        target_anomaly
    )
)


print(
    f"Dataset: "
    f"{adapted_record.get('dataset_type')}"
)

print(
    f"Record ID: "
    f"{adapted_record.get('record_id')}"
)


# =========================================================
# 3. Initialize Retriever
# =========================================================

print(
    "\n[3] Initializing Retriever..."
)

retriever = Retriever()


# =========================================================
# 4. Run Retrieval
# =========================================================

print(
    "\n[4] Running knowledge retrieval..."
)

retrieval_result = (
    retriever.retrieve(
        adapted_record
    )
)


# =========================================================
# 5. Read Current Retriever Structure
# =========================================================

records = retrieval_result.get(
    "records",
    []
)

record_count = retrieval_result.get(
    "record_count",
    0
)


print(
    f"\nRecords processed: "
    f"{record_count}"
)


if not records:

    print(
        "\nWARNING: No retrieval record "
        "was generated."
    )

    print(
        "\nThis means the problem is before "
        "vector-store retrieval."
    )

    raise ValueError(
        "Retriever returned zero records."
    )


retrieval_record = records[0]


query = retrieval_record.get(
    "query",
    ""
)

results = retrieval_record.get(
    "results",
    []
)

evidence_terms = retrieval_record.get(
    "evidence_terms",
    []
)

result_count = retrieval_record.get(
    "result_count",
    0
)


# =========================================================
# 6. Query Result
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "GENERATED QUERY"
)

print(
    "=" * 70
)

if query:

    print(query)

else:

    print(
        "NO QUERY GENERATED"
    )


# =========================================================
# 7. Evidence Terms
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "EVIDENCE TERMS"
)

print(
    "=" * 70
)

if evidence_terms:

    for term in evidence_terms:

        print(
            f"- {term}"
        )

else:

    print(
        "No evidence terms extracted."
    )


# =========================================================
# 8. Retrieved Knowledge
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "RETRIEVED KNOWLEDGE"
)

print(
    "=" * 70
)


print(
    f"Knowledge chunks retrieved: "
    f"{result_count}"
)


if not results:

    print(
        "\nNo knowledge chunks were retrieved."
    )

else:

    for index, result in enumerate(
        results,
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

        text = result.get(
            "text",
            ""
        )

        semantic_score = result.get(
            "semantic_score",
            result.get(
                "similarity_score",
                0.0
            )
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
            f"\n[Knowledge {index}]"
        )

        print(
            f"Source: {source}"
        )

        print(
            f"Category: {category}"
        )

        print(
            f"Semantic score: "
            f"{semantic_score:.4f}"
        )

        print(
            f"Evidence score: "
            f"{evidence_score:.4f}"
        )

        print(
            f"Hybrid score: "
            f"{hybrid_score:.4f}"
        )

        print(
            "Content:"
        )

        print(
            text
        )


# =========================================================
# 9. Final Status
# =========================================================

print(
    "\n"
    + "=" * 70
)

if query and results:

    print(
        "CLAIMS RETRIEVAL TEST PASSED"
    )

elif query and not results:

    print(
        "CLAIMS QUERY GENERATION PASSED"
    )

    print(
        "BUT KNOWLEDGE RETRIEVAL RETURNED "
        "ZERO MATCHES."
    )

else:

    print(
        "CLAIMS RETRIEVAL TEST FAILED"
    )

print(
    "=" * 70
)