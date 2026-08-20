"""
Main RAG input ingestion pipeline.

Flow:

ML JSON
   ↓
Load
   ↓
Validate
   ↓
Normalize
   ↓
Clean RAG Input
"""

import json
from pathlib import Path
from typing import Any, Dict, Union

from .validator import RAGInputValidator
from .normalizer import RAGInputNormalizer


class RAGIngestion:
    """
    Main ingestion component for ML model output.
    """

    def __init__(self):

        self.validator = (
            RAGInputValidator()
        )

        self.normalizer = (
            RAGInputNormalizer()
        )

    # =====================================================
    # Load JSON
    # =====================================================

    def load_json(
        self,
        file_path: Union[str, Path]
    ) -> Any:
        """
        Load ML/RAG input JSON from disk.
        """

        file_path = Path(
            file_path
        )

        if not file_path.exists():

            raise FileNotFoundError(
                f"RAG input file not found: "
                f"{file_path}"
            )

        if file_path.suffix.lower() != ".json":

            raise ValueError(
                "RAG input file must be a JSON file."
            )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            try:

                data = json.load(
                    file
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    f"Invalid JSON file: "
                    f"{file_path}"
                ) from exc

        return data

    # =====================================================
    # Validate
    # =====================================================

    def validate(
        self,
        rag_input: Any
    ) -> Dict[str, Any]:
        """
        Validate raw ML output.
        """

        return self.validator.validate(
            rag_input
        )

    # =====================================================
    # Normalize
    # =====================================================

    def normalize(
        self,
        rag_input: Any
    ) -> Dict[str, Any]:
        """
        Normalize validated ML output.
        """

        return self.normalizer.normalize(
            rag_input
        )

    # =====================================================
    # Complete Ingestion
    # =====================================================

    def ingest(
        self,
        file_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Execute the complete ingestion pipeline.

        ML JSON
           ↓
        Load
           ↓
        Validate
           ↓
        Normalize
           ↓
        Return structured RAG input
        """

        print(
            "=" * 60
        )

        print(
            "RAG INPUT INGESTION"
        )

        print(
            "=" * 60
        )

        # -------------------------------------------------
        # Step 1: Load
        # -------------------------------------------------

        print(
            "\n[1/3] Loading ML output..."
        )

        raw_input = self.load_json(
            file_path
        )

        print(
            f"Records loaded: "
            f"{len(raw_input) if isinstance(raw_input, list) else 'unknown'}"
        )

        # -------------------------------------------------
        # Step 2: Validate
        # -------------------------------------------------

        print(
            "\n[2/3] Validating ML output..."
        )

        validation_result = (
            self.validate(
                raw_input
            )
        )

        if not validation_result[
            "valid"
        ]:

            print(
                "Validation failed."
            )

            for error in validation_result[
                "errors"
            ]:

                print(
                    f"  - {error}"
                )

            raise ValueError(
                "RAG input validation failed."
            )

        print(
            "Validation successful."
        )

        print(
            f"Validated records: "
            f"{validation_result['record_count']}"
        )

        # -------------------------------------------------
        # Step 3: Normalize
        # -------------------------------------------------

        print(
            "\n[3/3] Normalizing records..."
        )

        normalized = (
            self.normalize(
                raw_input
            )
        )

        print(
            f"Normalized records: "
            f"{normalized['record_count']}"
        )

        # -------------------------------------------------
        # Final result
        # -------------------------------------------------

        print(
            "\n"
            + "=" * 60
        )

        print(
            "RAG INGESTION COMPLETED"
        )

        print(
            "=" * 60
        )

        return normalized


# =========================================================
# Simple command-line test
# =========================================================

if __name__ == "__main__":

    input_file = (
        "authorization_anomalies_for_rag.json"
    )

    ingestion = RAGIngestion()

    result = ingestion.ingest(
        input_file
    )

    print(
        "\nFirst normalized record:"
    )

    print(
        json.dumps(
            result["records"][0],
            indent=2
        )
    )