"""
NEW PHARMACY → ADAPTER → QUERY BUILDER → RETRIEVER TEST

Flow:

Pharmacy ML Output
        ↓
Pharmacy Adapter
        ↓
Normalized Pharmacy Record
        ↓
Query Builder
        ↓
Retriever
        ↓
Pharmacy Knowledge Base
"""

import json

from rag.ingestion.adapters.pharmacy_adapter import PharmacyAdapter
from rag.retrieval.retriever import Retriever


# =========================================================
# Configuration
# =========================================================

INPUT_FILE = "anomaly_results.json"

# First Pharmacy record is already known to be anomalous.
TARGET_INDEX = 0


# =========================================================
# Header
# =========================================================

print("=" * 70)
print(
    "NEW PHARMACY → ADAPTER → QUERY BUILDER → RETRIEVER TEST"
)
print("=" * 70)


# =========================================================
# 1. Load Pharmacy ML Output
# =========================================================

print("\n[1] Loading Pharmacy ML output...")


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    pharmacy_output = json.load(file)


# =========================================================
# Validate Root Structure
# =========================================================

if not isinstance(
    pharmacy_output,
    dict
):

    raise ValueError(
        "Pharmacy ML output must be a JSON object."
    )


records = pharmacy_output.get(
    "records",
    []
)


if not isinstance(
    records,
    list
):

    raise ValueError(
        "Pharmacy ML output does not contain "
        "a valid 'records' list."
    )


print(
    f"Total Pharmacy records: {len(records)}"
)


if not records:

    raise ValueError(
        "No Pharmacy records found."
    )


# =========================================================
# 2. Select Target Record
# =========================================================

if TARGET_INDEX >= len(records):

    raise IndexError(
        f"TARGET_INDEX {TARGET_INDEX} is outside "
        f"the available record range."
    )


target_record = records[
    TARGET_INDEX
]


print(
    "\nTarget record:"
)

print(
    target_record.get(
        "record_id"
    )
)


# =========================================================
# 3. Adapt Pharmacy Record
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
# 4. Display Normalized Detection Summary
# =========================================================

print(
    "\n[3] Normalized Evidence..."
)


detection = adapted_record.get(
    "detection_summary",
    {}
)


print(
    "Final anomaly:",
    detection.get(
        "final_anomaly"
    )
)


print(
    "Severity:",
    detection.get(
        "final_severity"
    )
)


print(
    "Anomaly type:",
    detection.get(
        "anomaly_type"
    )
)


print(
    "Bayesian anomaly:",
    detection.get(
        "bayesian_anomaly"
    )
)


print(
    "Bayesian probability:",
    detection.get(
        "bayesian_probability"
    )
)


# =========================================================
# 5. Rule Evidence
# =========================================================

print(
    "\nRule evidence:"
)


rule_evidence = adapted_record.get(
    "rule_based_evidence",
    []
)


if rule_evidence:

    for rule in rule_evidence:

        if not isinstance(
            rule,
            dict
        ):
            continue

        print(
            "- Rule:",
            rule.get(
                "rule_name",
                "unknown"
            )
        )

        print(
            "  Status:",
            rule.get(
                "status",
                "unknown"
            )
        )

        print(
            "  Reason:",
            rule.get(
                "reason",
                ""
            )
        )

        print(
            "  Severity:",
            rule.get(
                "severity",
                ""
            )
        )

else:

    print(
        "No rule evidence."
    )


# =========================================================
# 6. Behavioral Evidence
# =========================================================

print(
    "\nBehavioral evidence:"
)


behavioral_evidence = adapted_record.get(
    "behavioral_evidence",
    []
)


if behavioral_evidence:

    for item in behavioral_evidence:

        if not isinstance(
            item,
            dict
        ):
            continue

        print(
            "- Type:",
            item.get(
                "type",
                "unknown"
            )
        )

        print(
            "  Detected:",
            item.get(
                "detected",
                False
            )
        )

        print(
            "  Description:",
            item.get(
                "description",
                ""
            )
        )

else:

    print(
        "No behavioral evidence."
    )


# =========================================================
# 7. Bayesian Evidence
# =========================================================

print(
    "\nBayesian evidence:"
)


bayesian_evidence = adapted_record.get(
    "bayesian_evidence",
    {}
)


if isinstance(
    bayesian_evidence,
    dict
):

    print(
        "- Anomaly:",
        bayesian_evidence.get(
            "anomaly"
        )
    )

    print(
        "- Score:",
        bayesian_evidence.get(
            "score"
        )
    )

    print(
        "- Probability:",
        bayesian_evidence.get(
            "probability"
        )
    )

    print(
        "- Threshold:",
        bayesian_evidence.get(
            "threshold"
        )
    )


# =========================================================
# 8. Source Explanation
# =========================================================

print(
    "\nSource explanation:"
)


source_explanation = adapted_record.get(
    "source_explanation",
    {}
)


if isinstance(
    source_explanation,
    dict
):

    print(
        source_explanation.get(
            "explanation",
            "No source explanation."
        )
    )


# =========================================================
# 9. Initialize Retriever
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
# 10. Run Retrieval
# =========================================================

print(
    "\n[5] Running knowledge retrieval..."
)


retrieval_result = retriever.retrieve(
    adapted_record
)


# =========================================================
# 11. Validate Retrieval Result
# =========================================================

record_count = retrieval_result.get(
    "record_count",
    0
)


print(
    "\nRecords processed:",
    record_count
)


retrieval_records = retrieval_result.get(
    "records",
    []
)


if not retrieval_records:

    raise ValueError(
        "Retriever returned zero records."
    )


retrieval_record = retrieval_records[
    0
]


# =========================================================
# 12. Generated Query
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


query = retrieval_record.get(
    "query",
    ""
)


if query:

    print(
        query
    )

else:

    print(
        "NO QUERY GENERATED"
    )


# =========================================================
# 13. Evidence Terms
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
# 14. Retrieved Knowledge
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


result_count = retrieval_record.get(
    "result_count",
    len(results)
)


print(
    "Knowledge chunks:",
    result_count
)


if not results:

    print(
        "\nNo knowledge chunks retrieved."
    )


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


    text = result.get(
        "text",
        ""
    )


    print(
        f"\n[Knowledge {index}]"
    )


    print(
        "Source:",
        source
    )


    print(
        "Category:",
        category
    )


    print(
        "Semantic score:",
        f"{semantic_score:.4f}"
    )


    print(
        "Evidence score:",
        f"{evidence_score:.4f}"
    )


    print(
        "Hybrid score:",
        f"{hybrid_score:.4f}"
    )


    print(
        "Content:"
    )


    print(
        text
    )


# =========================================================
# 15. Final Validation
# =========================================================

print(
    "\n"
    + "=" * 70
)


if query and results:

    print(
        "NEW PHARMACY RETRIEVAL TEST PASSED"
    )

elif query and not results:

    print(
        "PHARMACY QUERY GENERATION PASSED"
    )

    print(
        "BUT KNOWLEDGE RETRIEVAL RETURNED ZERO MATCHES."
    )

else:

    print(
        "PHARMACY RETRIEVAL TEST FAILED"
    )


print(
    "=" * 70
)