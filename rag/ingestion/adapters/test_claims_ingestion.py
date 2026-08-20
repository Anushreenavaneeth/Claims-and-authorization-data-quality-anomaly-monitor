"""
Claims Adapter → Validator → Normalizer Test
"""

import json

from .claims_adapter import ClaimsAdapter

from rag.ingestion.validator import (
    RAGInputValidator
)

from rag.ingestion.normalizer import (
    RAGInputNormalizer
)


INPUT_FILE = "tc_puf_anomaly_output.json"


print("=" * 70)
print("CLAIMS → RAG INGESTION TEST")
print("=" * 70)


# =========================================================
# 1. Load Claims ML output
# =========================================================

print("\n[1] Loading Claims ML output...")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    claims_output = json.load(file)


print(
    "Original anomalies:",
    len(
        claims_output.get(
            "anomalies",
            []
        )
    )
)


# =========================================================
# 2. Claims Adapter
# =========================================================

print(
    "\n[2] Adapting Claims output..."
)

adapter = ClaimsAdapter()

rag_records = adapter.adapt(
    claims_output
)

print(
    "Adapted records:",
    len(rag_records)
)


# =========================================================
# 3. Existing Validator
# =========================================================

print(
    "\n[3] Validating adapted records..."
)

validator = RAGInputValidator()

validation = validator.validate(
    rag_records
)

print(
    "Validation:",
    validation["valid"]
)

print(
    "Validated records:",
    validation["record_count"]
)

if not validation["valid"]:

    print(
        "\nValidation errors:"
    )

    for error in validation["errors"][:20]:

        print(
            "-",
            error
        )

    raise ValueError(
        "Claims validation failed."
    )


print(
    "Validation successful."
)


# =========================================================
# 4. Existing Normalizer
# =========================================================

print(
    "\n[4] Normalizing adapted records..."
)

normalizer = RAGInputNormalizer()

normalized = normalizer.normalize(
    rag_records
)

print(
    "Normalized records:",
    normalized["record_count"]
)


# =========================================================
# 5. Inspect First Record
# =========================================================

print(
    "\n[5] First normalized Claims record:"
)

print(
    json.dumps(
        normalized["records"][0],
        indent=2,
        ensure_ascii=False
    )
)


# =========================================================
# Final
# =========================================================

print(
    "\n"
    + "=" * 70
)

print(
    "CLAIMS → VALIDATOR → NORMALIZER TEST PASSED"
)

print(
    "=" * 70
)