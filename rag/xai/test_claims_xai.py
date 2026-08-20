"""
Claims → Retrieval → XAI Integration Test

Flow:

Claims ML Output
        ↓
Claims Adapter
        ↓
Normalized Claims Record
        ↓
Knowledge Retrieval
        ↓
XAI Analyzer
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

print("=" * 70)

print(
    "CLAIMS → RETRIEVAL → XAI TEST"
)

print("=" * 70)


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

    claims_output = json.load(
        file
    )


# =========================================================
# 2. Find Target Claims Anomaly
# =========================================================

target_anomaly = None

for anomaly in claims_output.get(
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
# 3. Claims Adapter
# =========================================================

print(
    "\n[2] Adapting Claims record..."
)

adapter = ClaimsAdapter()

normalized_anomaly = (
    adapter.adapt_record(
        target_anomaly
    )
)


print(
    "Dataset:",
    normalized_anomaly.get(
        "dataset_type"
    )
)

print(
    "Record ID:",
    normalized_anomaly.get(
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

retrieval_result = (
    retriever.retrieve(
        normalized_anomaly
    )
)


retrieval_records = (
    retrieval_result.get(
        "records",
        []
    )
)


if not retrieval_records:

    raise ValueError(
        "Retriever returned no records."
    )


retrieval_record = (
    retrieval_records[0]
)


retrieved_knowledge = (
    retrieval_record.get(
        "results",
        []
    )
)


print(
    "Knowledge chunks retrieved:",
    len(retrieved_knowledge)
)


if not retrieved_knowledge:

    raise ValueError(
        "No knowledge was retrieved. "
        "XAI cannot continue."
    )


# =========================================================
# 5. Run XAI
# =========================================================

print(
    "\n[4] Running XAI analysis..."
)

analyzer = XAIAnalyzer()

xai_result = analyzer.analyze(
    anomaly=normalized_anomaly,
    retrieved_knowledge=retrieved_knowledge
)


print(
    "XAI analysis completed."
)


# =========================================================
# 6. Display Complete XAI Result
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "CLAIMS XAI RESULT"
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
# 7. Extract XAI Analysis
# =========================================================

xai_analysis = xai_result.get(
    "xai_analysis",
    {}
)


# =========================================================
# 8. Human-Readable Matched Anomaly
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "MATCHED ANOMALY"
)

print(
    "=" * 70
)

print(
    xai_analysis.get(
        "matched_anomaly_pattern",
        "Unknown"
    )
)


# =========================================================
# 9. Explanation
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "EXPLANATION"
)

print(
    "=" * 70
)

print(
    xai_analysis.get(
        "explanation",
        "No explanation available."
    )
)


# =========================================================
# 10. Root Cause
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "LIKELY ROOT CAUSE"
)

print(
    "=" * 70
)

root_cause = xai_analysis.get(
    "likely_root_cause",
    {}
)


if isinstance(
    root_cause,
    dict
):

    print(
        root_cause.get(
            "cause",
            "No root cause identified."
        )
    )

else:

    print(
        root_cause
    )


# =========================================================
# 11. Supporting Knowledge
# =========================================================

supporting_knowledge = (
    xai_analysis.get(
        "supporting_knowledge",
        []
    )
)


print(
    "\n"
    + "=" * 70
)

print(
    "SUPPORTING KNOWLEDGE"
)

print(
    "=" * 70
)

print(
    "Knowledge chunks used:",
    len(supporting_knowledge)
)


for index, knowledge in enumerate(
    supporting_knowledge,
    start=1
):

    print(
        f"\n[Knowledge {index}]"
    )

    if isinstance(
        knowledge,
        dict
    ):

        print(
            "Source:",
            knowledge.get(
                "source",
                "unknown"
            )
        )

        print(
            "Category:",
            knowledge.get(
                "category",
                "unknown"
            )
        )

        print(
            "Semantic score:",
            knowledge.get(
                "semantic_score",
                0.0
            )
        )

        print(
            "Evidence score:",
            knowledge.get(
                "evidence_score",
                0.0
            )
        )

        print(
            "Hybrid score:",
            knowledge.get(
                "hybrid_score",
                0.0
            )
        )


# =========================================================
# 12. Final Status
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "CLAIMS → RETRIEVAL → XAI TEST PASSED"
)

print(
    "=" * 70
)