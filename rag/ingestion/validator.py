"""
RAG Input Validator

Validates the NEW ML -> RAG JSON contract.

Supported ML output structure:

{
    "project": "...",
    "schema_version": 1.0,
    "record_count": 123,
    "records": [...]
}

Each record contains:

{
    "record_id": {...},
    "entity": {...},
    "final_assessment": {...},
    "bayesian": {...},
    "rule_engine": {...},
    "ml_evidence": {...}
}
"""

from typing import Any, Dict, List


class ValidationError(Exception):
    """Raised when the RAG input structure is invalid."""
    pass


class RAGInputValidator:

    SUPPORTED_DATASETS = {
        "claims",
        "authorization",
        "pharmacy"
    }

    def validate(
        self,
        rag_input: Any
    ) -> Dict[str, Any]:

        errors: List[str] = []

        # =====================================================
        # Top-level input
        # =====================================================

        if not isinstance(rag_input, list):

            raise ValidationError(
                "RAG input must be a list of normalized "
                "anomaly records."
            )

        if not rag_input:

            raise ValidationError(
                "RAG input contains no records."
            )

        # =====================================================
        # Validate records
        # =====================================================

        for index, record in enumerate(rag_input):

            record_errors = self._validate_record(
                record,
                index
            )

            errors.extend(
                record_errors
            )

        return {
            "valid": len(errors) == 0,
            "record_count": len(rag_input),
            "errors": errors
        }

    # =========================================================
    # Validate One Record
    # =========================================================

    def _validate_record(
        self,
        record: Any,
        index: int
    ) -> List[str]:

        errors = []

        prefix = f"Record [{index}]"

        # -----------------------------------------------------
        # Record object
        # -----------------------------------------------------

        if not isinstance(record, dict):

            return [
                f"{prefix}: record must be an object."
            ]

        # -----------------------------------------------------
        # Required normalized fields
        # -----------------------------------------------------

        required_fields = {
            "dataset_type",
            "record_id",
            "detection_summary",
            "rule_based_evidence",
            "ml_based_evidence",
            "record_context"
        }

        missing = (
            required_fields
            - set(record.keys())
        )

        for field in sorted(missing):

            errors.append(
                f"{prefix}: missing required field "
                f"'{field}'."
            )

        if missing:

            return errors

        # -----------------------------------------------------
        # Dataset
        # -----------------------------------------------------

        dataset_type = record.get(
            "dataset_type"
        )

        if dataset_type not in self.SUPPORTED_DATASETS:

            errors.append(
                f"{prefix}: unsupported dataset_type "
                f"'{dataset_type}'."
            )

        # -----------------------------------------------------
        # Record ID
        # -----------------------------------------------------

        record_id = record.get(
            "record_id"
        )

        if not isinstance(
            record_id,
            str
        ) or not record_id.strip():

            errors.append(
                f"{prefix}: record_id must be "
                f"a non-empty string."
            )

        # -----------------------------------------------------
        # Detection summary
        # -----------------------------------------------------

        detection = record.get(
            "detection_summary"
        )

        if not isinstance(
            detection,
            dict
        ):

            errors.append(
                f"{prefix}: detection_summary must "
                f"be an object."
            )

        else:

            required_detection = {
                "final_anomaly",
                "final_severity",
                "final_risk_score",
                "rule_anomaly",
                "ml_anomaly"
            }

            missing_detection = (
                required_detection
                - set(detection.keys())
            )

            for field in sorted(
                missing_detection
            ):

                errors.append(
                    f"{prefix}: detection_summary "
                    f"missing '{field}'."
                )

        # -----------------------------------------------------
        # Rule evidence
        # -----------------------------------------------------

        rule_evidence = record.get(
            "rule_based_evidence"
        )

        if not isinstance(
            rule_evidence,
            list
        ):

            errors.append(
                f"{prefix}: rule_based_evidence "
                f"must be an array."
            )

        # -----------------------------------------------------
        # ML evidence
        # -----------------------------------------------------

        ml_evidence = record.get(
            "ml_based_evidence"
        )

        if ml_evidence is not None:

            if not isinstance(
                ml_evidence,
                dict
            ):

                errors.append(
                    f"{prefix}: ml_based_evidence "
                    f"must be an object or null."
                )

        # -----------------------------------------------------
        # Record context
        # -----------------------------------------------------

        context = record.get(
            "record_context"
        )

        if not isinstance(
            context,
            dict
        ):

            errors.append(
                f"{prefix}: record_context "
                f"must be an object."
            )

        # -----------------------------------------------------
        # SLA
        # -----------------------------------------------------

        if "sla" in record:

            sla = record.get(
                "sla"
            )

            if (
                sla is not None
                and not isinstance(
                    sla,
                    dict
                )
            ):

                errors.append(
                    f"{prefix}: sla must be "
                    f"an object or null."
                )

        return errors