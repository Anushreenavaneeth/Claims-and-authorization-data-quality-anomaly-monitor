"""
Test RAG retrieval using a small sample
of Authorization ML output.
"""

import json

from rag.retrieval.retriever import Retriever


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INPUT_FILE = "authorization_anomalies_for_rag.json"

TEST_RECORD_COUNT = 5


# ---------------------------------------------------------
# Load ML JSON
# ---------------------------------------------------------

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    rag_input = json.load(file)


print(
    f"Total ML anomaly records: {len(rag_input)}"
)


# ---------------------------------------------------------
# Use only a small sample for testing
# ---------------------------------------------------------

test_input = rag_input[
    :TEST_RECORD_COUNT
]


print(
    f"Testing retrieval on: "
    f"{len(test_input)} records"
)


# ---------------------------------------------------------
# Initialize Retriever
# ---------------------------------------------------------

retriever = Retriever(
    top_k=5,
    similarity_threshold=0.35
)


# ---------------------------------------------------------
# Retrieve
# ---------------------------------------------------------

result = retriever.retrieve(
    test_input
)


# ---------------------------------------------------------
# Display
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("RAG RETRIEVAL TEST")
print("=" * 70)


print(
    f"\nRecords processed: "
    f"{result.get('record_count', 0)}"
)


for record in result.get(
    "records",
    []
):

    print("\n" + "=" * 70)

    print(
        f"Record ID: "
        f"{record.get('record_id', 'unknown')}"
    )

    print(
        f"Dataset: "
        f"{record.get('dataset_type', 'unknown')}"
    )

    print("\nQuery:")

    print(
        record.get(
            "query",
            ""
        )
    )

    print(
        f"\nRetrieved chunks: "
        f"{record.get('result_count', 0)}"
    )

    print("\nRetrieved Knowledge:")

    for index, item in enumerate(
        record.get("results", []),
        start=1
    ):

        metadata = item.get(
            "metadata",
            {}
        )

        print(
            f"\n[{index}] "
            f"Similarity: "
            f"{item.get('similarity_score', 0.0):.4f}"
        )

        print(
            f"Source: "
            f"{metadata.get('source', 'unknown')}"
        )

        print(
            f"Category: "
            f"{metadata.get('category', 'unknown')}"
        )

        print("\nContent:")

        print(
            item.get(
                "text",
                ""
            )
        )

        print("-" * 70)