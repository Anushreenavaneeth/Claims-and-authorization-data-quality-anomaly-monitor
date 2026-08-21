"""
Test Retrieval with the NEW Authorization ML JSON.
"""

import json

from rag.ingestion.adapters.authorization_adapter import AuthorizationAdapter
from rag.retrieval.retriever import Retriever


INPUT_FILE = "authorization.json"


print("=" * 70)
print("NEW AUTHORIZATION → ADAPTER → QUERY BUILDER → RETRIEVER TEST")
print("=" * 70)


# =========================================================
# 1. Load Authorization JSON
# =========================================================

print("\n[1] Loading Authorization ML output...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    authorization_output = json.load(file)


if not isinstance(authorization_output, dict):
    raise ValueError(
        "Authorization ML output must be a JSON object."
    )


records = authorization_output.get(
    "records",
    []
)


print(
    f"Total Authorization records: {len(records)}"
)


if not records:
    raise ValueError(
        "No Authorization records found."
    )


# =========================================================
# 2. Select first record
# =========================================================

target_record = records[0]

print("\nTarget record:")

print(
    target_record.get("record_id")
)


# =========================================================
# 3. Adapt
# =========================================================

print("\n[2] Adapting Authorization record...")

adapter = AuthorizationAdapter()

adapted_record = adapter.adapt_record(
    target_record
)


print(
    "Dataset:",
    adapted_record.get("dataset_type")
)

print(
    "Record ID:",
    adapted_record.get("record_id")
)


# =========================================================
# 4. Display evidence
# =========================================================

print("\n[3] Normalized Evidence...")

detection = adapted_record.get(
    "detection_summary",
    {}
)


print(
    "Final anomaly:",
    detection.get("final_anomaly")
)

print(
    "Severity:",
    detection.get("final_severity")
)

print(
    "Bayesian anomaly:",
    detection.get("bayesian_anomaly")
)

print(
    "Bayesian probability:",
    detection.get("bayesian_probability")
)


print("\nRule evidence:")

for rule in adapted_record.get(
    "rule_based_evidence",
    []
):

    print(
        "-",
        rule.get("rule_name")
    )


# =========================================================
# 5. Initialize Retriever
# =========================================================

print(
    "\n[4] Initializing Retriever..."
)

retriever = Retriever(
    top_k=5,
    similarity_threshold=0.35
)

print(
    "Retriever initialized successfully."
)


# =========================================================
# 6. Retrieval
# =========================================================

print(
    "\n[5] Running knowledge retrieval..."
)

result = retriever.retrieve(
    adapted_record
)


print(
    "\nRecords processed:",
    result.get("record_count", 0)
)


if not result.get("records"):
    raise ValueError(
        "Retriever returned zero records."
    )


retrieval_record = result[
    "records"
][0]


# =========================================================
# 7. Generated Query
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

print(
    retrieval_record.get(
        "query",
        ""
    )
)


# =========================================================
# 8. Evidence Terms
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

evidence_terms = retrieval_record.get(
    "evidence_terms",
    []
)


if evidence_terms:

    for term in evidence_terms:
        print(
            "-",
            term
        )

else:

    print(
        "NO EVIDENCE TERMS"
    )


# =========================================================
# 9. Retrieved Knowledge
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


results = retrieval_record.get(
    "results",
    []
)


print(
    "Knowledge chunks:",
    len(results)
)


for index, item in enumerate(
    results,
    start=1
):

    metadata = item.get(
        "metadata",
        {}
    )

    print(
        f"\n[Knowledge {index}]"
    )

    print(
        "Source:",
        metadata.get(
            "source",
            "unknown"
        )
    )

    print(
        "Category:",
        metadata.get(
            "category",
            "unknown"
        )
    )

    print(
        "Semantic score:",
        f"{item.get('semantic_score', 0.0):.4f}"
    )

    print(
        "Evidence score:",
        f"{item.get('evidence_score', 0.0):.4f}"
    )

    print(
        "Hybrid score:",
        f"{item.get('hybrid_score', 0.0):.4f}"
    )

    print(
        "Content:"
    )

    print(
        item.get(
            "text",
            ""
        )
    )


# =========================================================
# 10. Final Status
# =========================================================

print(
    "\n"
    + "=" * 70
)

if retrieval_record.get("query") and results:

    print(
        "NEW AUTHORIZATION RETRIEVAL TEST PASSED"
    )

elif retrieval_record.get("query"):

    print(
        "AUTHORIZATION QUERY GENERATED, "
        "BUT NO KNOWLEDGE RETRIEVED"
    )

else:

    print(
        "AUTHORIZATION RETRIEVAL TEST FAILED"
    )

print(
    "=" * 70
)