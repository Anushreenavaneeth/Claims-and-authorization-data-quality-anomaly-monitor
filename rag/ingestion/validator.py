"""
Validate ML model output before entering the RAG pipeline.

The validator supports:
- Rule-based anomalies
- ML-based anomalies
- Rule + ML anomalies
- Records where ML evidence is unavailable (null)
"""

from typing import Any, Dict, List

from .config import (
    SUPPORTED_DATASETS,
    REQUIRED_FIELDS,
    REQUIRED_DETECTION_FIELDS,
    REQUIRED_ML_FIELDS,
    MAX_RECORDS
)


class ValidationError(Exception):
    """
    Raised when the RAG input itself is structurally invalid.
    """
    pass


class RAGInputValidator:
    """
    Validates the ML → RAG JSON contract.

    Expected top-level structure:

    [
        {
            "dataset_type": "authorization",
            "record_id": "AUTH00001",
            "detection_summary": {},
            "rule_based_evidence": [],
            "ml_based_evidence": {},
            "record_context": {},
            "sla": "Review within 48 Hours"
        }
    ]

    ml_based_evidence is allowed to be null when
    ML evidence is unavailable for that record.
    """

    def validate(
        self,
        rag_input: Any
    ) -> Dict[str, Any]:
        """
        Validate the complete ML/RAG input.

        Returns:

        {
            "valid": True/False,
            "record_count": int,
            "errors": []
        }
        """

        errors: List[str] = []

        # =================================================
        # Top-level validation
        # =================================================

        if not isinstance(
            rag_input,
            list
        ):

            raise ValidationError(
                "RAG input must be a JSON list "
                "of anomaly records."
            )

        if not rag_input:

            raise ValidationError(
                "RAG input contains no anomaly records."
            )

        if len(rag_input) > MAX_RECORDS:

            raise ValidationError(
                f"RAG input contains {len(rag_input)} "
                f"records. Maximum allowed is "
                f"{MAX_RECORDS}."
            )

        # =================================================
        # Validate every record
        # =================================================

        for index, record in enumerate(
            rag_input
        ):

            record_errors = (
                self._validate_record(
                    record,
                    index
                )
            )

            errors.extend(
                record_errors
            )

        # =================================================
        # Final validation result
        # =================================================

        if errors:

            return {
                "valid": False,
                "record_count": len(
                    rag_input
                ),
                "errors": errors
            }

        return {
            "valid": True,
            "record_count": len(
                rag_input
            ),
            "errors": []
        }

    # =====================================================
    # Record Validation
    # =====================================================

    def _validate_record(
        self,
        record: Any,
        index: int
    ) -> List[str]:
        """
        Validate one anomaly record.
        """

        errors: List[str] = []

        prefix = (
            f"Record [{index}]"
        )

        # =================================================
        # Record must be an object
        # =================================================

        if not isinstance(
            record,
            dict
        ):

            errors.append(
                f"{prefix}: record must be an object."
            )

            return errors

        # =================================================
        # Required top-level fields
        # =================================================

        missing_fields = (
            REQUIRED_FIELDS
            -
            set(record.keys())
        )

        for field in sorted(
            missing_fields
        ):

            errors.append(
                f"{prefix}: missing required "
                f"field '{field}'."
            )

        # If required structure is missing,
        # stop deeper validation for this record.

        if missing_fields:

            return errors

        # =================================================
        # Dataset validation
        # =================================================

        dataset_type = record.get(
            "dataset_type"
        )

        if dataset_type not in (
            SUPPORTED_DATASETS
        ):

            errors.append(
                f"{prefix}: unsupported "
                f"dataset_type '{dataset_type}'. "
                f"Supported datasets: "
                f"{sorted(SUPPORTED_DATASETS)}."
            )

        # =================================================
        # Record ID validation
        # =================================================

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

        # =================================================
        # Detection Summary
        # =================================================

        detection_summary = record.get(
            "detection_summary"
        )

        if not isinstance(
            detection_summary,
            dict
        ):

            errors.append(
                f"{prefix}: detection_summary "
                f"must be an object."
            )

        else:

            missing_detection_fields = (
                REQUIRED_DETECTION_FIELDS
                -
                set(
                    detection_summary.keys()
                )
            )

            for field in sorted(
                missing_detection_fields
            ):

                errors.append(
                    f"{prefix}: detection_summary "
                    f"missing '{field}'."
                )

        # =================================================
        # Rule-Based Evidence
        # =================================================

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

        else:

            for rule_index, rule in enumerate(
                rule_evidence
            ):

                # -----------------------------------------
                # Rule must be an object
                # -----------------------------------------

                if not isinstance(
                    rule,
                    dict
                ):

                    errors.append(
                        f"{prefix}: rule_based_evidence "
                        f"[{rule_index}] must be an object."
                    )

                    continue

                # -----------------------------------------
                # Rule name
                # -----------------------------------------

                rule_name = rule.get(
                    "rule_name"
                )

                if not isinstance(
                    rule_name,
                    str
                ) or not rule_name.strip():

                    errors.append(
                        f"{prefix}: rule_based_evidence "
                        f"[{rule_index}] missing valid "
                        f"'rule_name'."
                    )

                # -----------------------------------------
                # Rule status
                # -----------------------------------------

                status = rule.get(
                    "status"
                )

                if not isinstance(
                    status,
                    str
                ) or not status.strip():

                    errors.append(
                        f"{prefix}: rule_based_evidence "
                        f"[{rule_index}] missing valid "
                        f"'status'."
                    )

        # =================================================
        # ML-Based Evidence
        # =================================================

        ml_evidence = record.get(
            "ml_based_evidence"
        )

        # -------------------------------------------------
        # Case 1:
        # ML evidence unavailable.
        #
        # This is VALID.
        #
        # We do NOT fabricate:
        # - model
        # - anomaly score
        # - features
        # -------------------------------------------------

        if ml_evidence is None:

            pass

        # -------------------------------------------------
        # Case 2:
        # ML evidence available.
        # -------------------------------------------------

        elif isinstance(
            ml_evidence,
            dict
        ):

            missing_ml_fields = (
                REQUIRED_ML_FIELDS
                -
                set(
                    ml_evidence.keys()
                )
            )

            for field in sorted(
                missing_ml_fields
            ):

                errors.append(
                    f"{prefix}: ml_based_evidence "
                    f"missing '{field}'."
                )

            # ---------------------------------------------
            # Contributing features
            # ---------------------------------------------

            if "contributing_features" in (
                ml_evidence
            ):

                features = ml_evidence.get(
                    "contributing_features"
                )

                if not isinstance(
                    features,
                    list
                ):

                    errors.append(
                        f"{prefix}: "
                        f"contributing_features "
                        f"must be an array."
                    )

                else:

                    for feature_index, feature in enumerate(
                        features
                    ):

                        if not isinstance(
                            feature,
                            dict
                        ):

                            errors.append(
                                f"{prefix}: "
                                f"contributing_features "
                                f"[{feature_index}] "
                                f"must be an object."
                            )

        # -------------------------------------------------
        # Case 3:
        # Invalid ML evidence type.
        # -------------------------------------------------

        else:

            errors.append(
                f"{prefix}: ml_based_evidence "
                f"must be an object or null."
            )

        # =================================================
        # Record Context
        # =================================================

        record_context = record.get(
            "record_context"
        )

        if not isinstance(
            record_context,
            dict
        ):

            errors.append(
                f"{prefix}: record_context "
                f"must be an object."
            )

        # =================================================
        # SLA
        # =================================================

        sla = record.get(
            "sla"
        )

        if sla is not None:

            if not isinstance(
                sla,
                str
            ):

                errors.append(
                    f"{prefix}: sla must be "
                    f"a string or null."
                )

        return errors