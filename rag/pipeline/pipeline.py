"""
Unified Healthcare Data Quality RAG Pipeline.

Flow:

ML Output
    ↓
Validation
    ↓
Normalization
    ↓
Knowledge Retrieval
    ↓
XAI Analysis
    ↓
Recommendation
    ↓
Human-readable Result
"""

from typing import Any, Dict, List

from rag.ingestion.validator import RAGInputValidator
from rag.ingestion.normalizer import RAGInputNormalizer

from rag.retrieval.retriever import Retriever

from rag.xai.analyzer import XAIAnalyzer

from rag.recommendation.recommendation_builder import (
    RecommendationBuilder
)


class RAGPipeline:
    """
    Main orchestration layer for the healthcare
    data-quality RAG system.

    Supports:
    - Complete ML output containing multiple records
    - Single ML anomaly record
    """

    # =====================================================
    # Initialization
    # =====================================================

    def __init__(self):

        print("=" * 70)
        print(
            "INITIALIZING HEALTHCARE DATA QUALITY RAG PIPELINE"
        )
        print("=" * 70)

        # -------------------------------------------------
        # Ingestion
        # -------------------------------------------------

        self.validator = RAGInputValidator()

        self.normalizer = RAGInputNormalizer()

        # -------------------------------------------------
        # Retrieval
        # -------------------------------------------------

        self.retriever = Retriever()

        # -------------------------------------------------
        # XAI
        # -------------------------------------------------

        self.xai_analyzer = XAIAnalyzer()

        # -------------------------------------------------
        # Recommendation
        # -------------------------------------------------

        self.recommendation_builder = (
            RecommendationBuilder()
        )

        print(
            "RAG Pipeline initialized successfully."
        )

    # =====================================================
    # Prepare / Validate / Normalize ML Input
    # =====================================================

    def _prepare_records(
        self,
        ml_output: Any
    ) -> List[Dict[str, Any]]:
        """
        Validate and normalize ML output.

        The validator expects a LIST of anomaly records.

        Supported input to this internal method:
            [
                {...},
                {...}
            ]
        """

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        validation_result = (
            self.validator.validate(
                ml_output
            )
        )

        if not validation_result.get(
            "valid",
            False
        ):

            errors = validation_result.get(
                "errors",
                []
            )

            error_text = "\n".join(
                str(error)
                for error in errors[:20]
            )

            if len(errors) > 20:

                error_text += (
                    f"\n... and "
                    f"{len(errors) - 20} "
                    f"more errors."
                )

            raise ValueError(
                "ML output validation failed:\n"
                + error_text
            )

        # -------------------------------------------------
        # Normalization
        # -------------------------------------------------

        normalized = (
            self.normalizer.normalize(
                ml_output
            )
        )

        records = normalized.get(
            "records",
            []
        )

        if not isinstance(
            records,
            list
        ):

            raise ValueError(
                "Normalizer did not return "
                "a records list."
            )

        return records

    # =====================================================
    # Process One Normalized Record
    # =====================================================

    def process_record(
        self,
        anomaly: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process one normalized anomaly record.

        Flow:

        Record
            ↓
        Retrieval
            ↓
        XAI
            ↓
        Recommendation
        """

        if not isinstance(
            anomaly,
            dict
        ):

            raise TypeError(
                "Anomaly must be a dictionary."
            )

        record_id = anomaly.get(
            "record_id",
            "unknown"
        )

        dataset_type = anomaly.get(
            "dataset_type",
            "unknown"
        )

        # =================================================
        # 1. Knowledge Retrieval
        # =================================================

        retrieval_result = (
            self.retriever.retrieve(
                anomaly
            )
        )

        # -------------------------------------------------
        # Current Retriever format:
        #
        # {
        #     "record_count": 1,
        #     "records": [
        #         {
        #             "record_id": "...",
        #             "query": "...",
        #             "results": [...]
        #         }
        #     ]
        # }
        # -------------------------------------------------

        retrieval_records = (
            retrieval_result.get(
                "records",
                []
            )
        )

        retrieved_knowledge = []

        if retrieval_records:

            first_record = (
                retrieval_records[0]
            )

            retrieved_knowledge = (
                first_record.get(
                    "results",
                    []
                )
            )

        # =================================================
        # 2. XAI Analysis
        # =================================================

        xai_result = (
            self.xai_analyzer.analyze(
                anomaly=anomaly,
                retrieved_knowledge=(
                    retrieved_knowledge
                )
            )
        )

        # =================================================
        # 3. Recommendation
        # =================================================

        recommendation_result = (
            self.recommendation_builder.build(
                xai_result=xai_result,
                retrieved_knowledge=(
                    retrieved_knowledge
                )
            )
        )

        # =================================================
        # 4. Final Result
        # =================================================

        return {
            "record_id": record_id,

            "dataset_type": dataset_type,

            "retrieval": {
                "query_count": len(
                    retrieval_result.get(
                        "queries",
                        []
                    )
                ),

                "knowledge_count": len(
                    retrieved_knowledge
                ),

                "knowledge": (
                    retrieved_knowledge
                )
            },

            "xai": xai_result,

            "recommendation": (
                recommendation_result
            )
        }

    # =====================================================
    # Process Complete ML Output
    # =====================================================

    def process(
        self,
        ml_output: Any
    ) -> Dict[str, Any]:
        """
        Process complete ML output.

        Expected format:

        [
            {
                "dataset_type": "authorization",
                "record_id": "...",
                ...
            },
            {
                "dataset_type": "authorization",
                "record_id": "...",
                ...
            }
        ]
        """

        # -------------------------------------------------
        # Validation + Normalization
        # -------------------------------------------------

        records = (
            self._prepare_records(
                ml_output
            )
        )

        # -------------------------------------------------
        # Process Every Record
        # -------------------------------------------------

        results = []

        for anomaly in records:

            result = (
                self.process_record(
                    anomaly
                )
            )

            results.append(
                result
            )

        # -------------------------------------------------
        # Final Pipeline Result
        # -------------------------------------------------

        return {
            "pipeline_status": "completed",

            "record_count": len(
                records
            ),

            "results": results
        }

    # =====================================================
    # Process Single Record
    # =====================================================

    def process_single(
        self,
        ml_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process exactly one anomaly record.

        IMPORTANT:
        RAGInputValidator expects a LIST.

        Therefore the single dictionary is wrapped
        into a list before validation.
        """

        # -------------------------------------------------
        # Validate input type
        # -------------------------------------------------

        if not isinstance(
            ml_output,
            dict
        ):

            raise TypeError(
                "process_single() expects "
                "one anomaly record as a dictionary."
            )

        # -------------------------------------------------
        # IMPORTANT FIX
        #
        # Convert:
        #
        # {
        #     "record_id": "AUTH04414",
        #     ...
        # }
        #
        # into:
        #
        # [
        #     {
        #         "record_id": "AUTH04414",
        #         ...
        #     }
        # ]
        #
        # because the validator expects a list.
        # -------------------------------------------------

        records = (
            self._prepare_records(
                [ml_output]
            )
        )

        # -------------------------------------------------
        # Validate result
        # -------------------------------------------------

        if not records:

            raise ValueError(
                "No anomaly records found."
            )

        if len(records) != 1:

            raise ValueError(
                "process_single() expected exactly "
                "one anomaly record."
            )

        # -------------------------------------------------
        # Process normalized record
        # -------------------------------------------------

        return (
            self.process_record(
                records[0]
            )
        )