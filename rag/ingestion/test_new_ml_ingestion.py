"""
Test the NEW ML -> RAG ingestion contract.

Tests:
- Claims
- Authorization
- Pharmacy
"""

import json
from pathlib import Path

from rag.ingestion.validator import (
    RAGInputValidator
)

from rag.ingestion.normalizer import (
    RAGInputNormalizer
)

from rag.ingestion.adapters.claims_adapter import (
    ClaimsAdapter
)

from rag.ingestion.adapters.authorization_adapter import (
    AuthorizationAdapter
)

from rag.ingestion.adapters.pharmacy_adapter import (
    PharmacyAdapter
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


FILES = {

    "claims":
        PROJECT_ROOT
        / "tc_puf_final_anomaly_results.json",

    "authorization":
        PROJECT_ROOT
        / "authorization.json",

    "pharmacy":
        PROJECT_ROOT
        / "anomaly_results.json"
}


ADAPTERS = {

    "claims":
        ClaimsAdapter(),

    "authorization":
        AuthorizationAdapter(),

    "pharmacy":
        PharmacyAdapter()
}


def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def main():

    print("=" * 70)

    print(
        "NEW ML → RAG INGESTION TEST"
    )

    print("=" * 70)

    validator = RAGInputValidator()

    normalizer = RAGInputNormalizer()

    for dataset_type, path in FILES.items():

        print()
        print("=" * 70)

        print(
            dataset_type.upper()
        )

        print("=" * 70)

        print(
            f"Input file: {path.name}"
        )

        # -----------------------------------------------------
        # Load
        # -----------------------------------------------------

        ml_output = load_json(
            path
        )

        print(
            "Top-level type:",
            type(ml_output).__name__
        )

        print(
            "Declared records:",
            ml_output.get(
                "record_count"
            )
        )

        print(
            "Actual records:",
            len(
                ml_output.get(
                    "records",
                    []
                )
            )
        )

        # -----------------------------------------------------
        # Adapter
        # -----------------------------------------------------

        adapter = ADAPTERS[
            dataset_type
        ]

        adapted = adapter.adapt_output(
            ml_output,
            anomalies_only=True
        )

        records = adapted[
            "records"
        ]

        print(
            "Anomaly records:",
            len(records)
        )

        if not records:

            print(
                "No anomalies to process."
            )

            continue

        # -----------------------------------------------------
        # Validation
        # -----------------------------------------------------

        validation = validator.validate(
            records
        )

        print(
            "Validation:",
            validation[
                "valid"
            ]
        )

        print(
            "Validated records:",
            validation[
                "record_count"
            ]
        )

        if not validation[
            "valid"
        ]:

            print()
            print(
                "VALIDATION ERRORS:"
            )

            for error in validation[
                "errors"
            ][:20]:

                print(
                    "-",
                    error
                )

            raise ValueError(
                f"{dataset_type} validation failed."
            )

        # -----------------------------------------------------
        # Normalize
        # -----------------------------------------------------

        normalized = normalizer.normalize(
            records
        )

        normalized_records = normalized[
            "records"
        ]

        print(
            "Normalized records:",
            len(
                normalized_records
            )
        )

        # -----------------------------------------------------
        # First Record
        # -----------------------------------------------------

        print()
        print(
            "FIRST NORMALIZED RECORD:"
        )

        print(
            json.dumps(
                normalized_records[0],
                indent=2,
                ensure_ascii=False
            )
        )

        print()
        print(
            f"{dataset_type.upper()} INGESTION PASSED"
        )

    print()
    print("=" * 70)

    print(
        "ALL NEW ML → RAG INGESTION TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()