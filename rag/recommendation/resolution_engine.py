"""
Resolution Procedure Engine.

Uses the detected anomaly, XAI evidence, RCA,
and retrieved knowledge to determine the appropriate
remediation procedure.
"""

from typing import Any, Dict, List


class ResolutionEngine:
    """
    Generates a clear, actionable resolution procedure
    for the detected healthcare data-quality issue.
    """

    # =====================================================
    # Main Resolution
    # =====================================================

    def resolve(
        self,
        xai_result: Dict[str, Any],
        rca_result: Dict[str, Any],
        matched_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Determine the appropriate resolution procedure.
        """

        if not isinstance(
            xai_result,
            dict
        ):
            raise TypeError(
                "xai_result must be a dictionary."
            )

        if not isinstance(
            rca_result,
            dict
        ):
            raise TypeError(
                "rca_result must be a dictionary."
            )

        if not isinstance(
            matched_knowledge,
            list
        ):
            raise TypeError(
                "matched_knowledge must be a list."
            )

        # -------------------------------------------------
        # Extract anomaly information
        # -------------------------------------------------

        xai_analysis = (
            xai_result.get(
                "xai_analysis",
                {}
            )
        )

        anomaly_pattern = str(
            xai_analysis.get(
                "matched_anomaly_pattern",
                ""
            )
        )

        anomaly_lower = (
            anomaly_pattern.lower()
        )

        # -------------------------------------------------
        # Try knowledge-grounded resolution first
        # -------------------------------------------------

        knowledge_resolution = (
            self._find_knowledge_resolution(
                matched_knowledge,
                anomaly_lower
            )
        )

        if knowledge_resolution:

            return {
                "status": "identified",

                "procedure":
                    knowledge_resolution,

                "basis": "knowledge_base",

                "anomaly_pattern":
                    anomaly_pattern,

                "verification_required":
                    True
            }

        # -------------------------------------------------
        # Rule-based resolution
        # -------------------------------------------------

        procedure = (
            self._rule_based_resolution(
                anomaly_lower
            )
        )

        if procedure:

            return {
                "status": "identified",

                "procedure":
                    procedure,

                "basis": "anomaly_pattern",

                "anomaly_pattern":
                    anomaly_pattern,

                "verification_required":
                    True
            }

        # -------------------------------------------------
        # Generic resolution
        # -------------------------------------------------

        return {
            "status": "review_required",

            "procedure": (
                "Review the affected record against "
                "the source system and the applicable "
                "healthcare data-quality procedure. "
                "Correct the underlying issue, "
                "revalidate the record, and reprocess "
                "it only after validation succeeds."
            ),

            "basis": "generic_data_quality_procedure",

            "anomaly_pattern":
                anomaly_pattern,

            "verification_required":
                True
        }

    # =====================================================
    # Knowledge-Based Resolution
    # =====================================================

    def _find_knowledge_resolution(
        self,
        matched_knowledge: List[Dict[str, Any]],
        anomaly_lower: str
    ) -> str:
        """
        Check whether retrieved KB content contains
        an explicit remediation instruction.
        """

        # Only use strongly relevant knowledge.

        for knowledge in matched_knowledge:

            score = float(
                knowledge.get(
                    "hybrid_score",
                    0.0
                ) or 0.0
            )

            if score < 0.50:
                continue

            content = str(
                knowledge.get(
                    "content",
                    ""
                )
            )

            if not content:
                continue

            content_lower = (
                content.lower()
            )

            # -------------------------------------------------
            # Invalid date sequence
            # -------------------------------------------------

            if (
                "invalid date" in anomaly_lower
                and (
                    "verify" in content_lower
                    or "correct" in content_lower
                    or "reprocess" in content_lower
                )
            ):

                return (
                    "Verify the authorization date and "
                    "service date against the source system. "
                    "Correct the invalid date sequence and "
                    "revalidate the record before "
                    "reprocessing."
                )

            # -------------------------------------------------
            # Missing documentation
            # -------------------------------------------------

            if (
                (
                    "missing document"
                    in anomaly_lower
                )
                or (
                    "documentation"
                    in anomaly_lower
                )
            ):

                if (
                    "missing" in content_lower
                    and (
                        "verify" in content_lower
                        or "obtain" in content_lower
                    )
                ):

                    return (
                        "Verify the required supporting "
                        "documentation. Obtain any missing "
                        "documents, update the record, and "
                        "revalidate it before continuing "
                        "processing."
                    )

            # -------------------------------------------------
            # Duplicate
            # -------------------------------------------------

            if "duplicate" in anomaly_lower:

                if (
                    "duplicate" in content_lower
                    and (
                        "verify" in content_lower
                        or "resolve" in content_lower
                    )
                ):

                    return (
                        "Verify whether the record is a "
                        "true duplicate against the source "
                        "system. Retain the valid record, "
                        "resolve the duplicate entry, and "
                        "revalidate the affected data."
                    )

        return ""

    # =====================================================
    # Rule-Based Resolution
    # =====================================================

    def _rule_based_resolution(
        self,
        anomaly_lower: str
    ) -> str:
        """
        Provide a specific resolution procedure for
        recognized anomaly types.
        """

        # -------------------------------------------------
        # Invalid Date Sequence
        # -------------------------------------------------

        if "invalid date" in anomaly_lower:

            return (
                "Verify the authorization date and "
                "service date against the source system. "
                "Correct the invalid date sequence, "
                "revalidate the record, and reprocess "
                "the authorization."
            )

        # -------------------------------------------------
        # Missing Fields
        # -------------------------------------------------

        if (
            "missing field" in anomaly_lower
            or "missing data" in anomaly_lower
        ):

            return (
                "Identify the missing required fields, "
                "verify the values against the source "
                "system, populate the missing information, "
                "and revalidate the record."
            )

        # -------------------------------------------------
        # Missing Documentation
        # -------------------------------------------------

        if (
            "missing document" in anomaly_lower
            or "documentation" in anomaly_lower
        ):

            return (
                "Verify the required supporting documents. "
                "Obtain the missing documentation, update "
                "the record, and revalidate it before "
                "continuing processing."
            )

        # -------------------------------------------------
        # Duplicate Records
        # -------------------------------------------------

        if "duplicate" in anomaly_lower:

            return (
                "Compare the affected record with existing "
                "records in the source system to confirm "
                "the duplication. Retain the valid record, "
                "resolve the duplicate entry according to "
                "the remediation procedure, and revalidate "
                "the data."
            )

        # -------------------------------------------------
        # Schema Mismatch
        # -------------------------------------------------

        if "schema" in anomaly_lower:

            return (
                "Compare the affected record with the "
                "expected schema. Correct the field or "
                "structure mismatch, validate the corrected "
                "record, and reprocess it."
            )

        # -------------------------------------------------
        # Reconciliation Failure
        # -------------------------------------------------

        if "reconciliation" in anomaly_lower:

            return (
                "Compare the affected record with the "
                "corresponding source or downstream record. "
                "Identify and correct the reconciliation "
                "difference, then rerun the reconciliation "
                "process."
            )

        # -------------------------------------------------
        # Delayed Processing
        # -------------------------------------------------

        if (
            "delayed processing" in anomaly_lower
            or "processing delay" in anomaly_lower
        ):

            return (
                "Check the processing status and identify "
                "the stage causing the delay. Verify "
                "upstream and downstream pipeline status, "
                "resolve the blocking issue, and resume "
                "processing."
            )

        # -------------------------------------------------
        # Upstream Data Issue
        # -------------------------------------------------

        if "upstream" in anomaly_lower:

            return (
                "Verify the affected data against the "
                "upstream source. Identify the source of "
                "the incorrect or incomplete data, correct "
                "the upstream issue, and reprocess the "
                "affected records."
            )

        # -------------------------------------------------
        # Provider Data Issue
        # -------------------------------------------------

        if "provider" in anomaly_lower:

            return (
                "Verify the affected provider data against "
                "the source system and applicable provider "
                "requirements. Correct the inaccurate or "
                "incomplete information and revalidate the "
                "record."
            )

        return ""

    # =====================================================
    # Human-Readable Summary
    # =====================================================

    def build_summary(
        self,
        resolution_result: Dict[str, Any]
    ) -> str:
        """
        Convert the resolution result into a concise
        human-readable statement.
        """

        procedure = resolution_result.get(
            "procedure"
        )

        if not procedure:

            return (
                "No specific resolution procedure "
                "was identified. Review the record "
                "against the applicable data-quality "
                "procedure."
            )

        return str(
            procedure
        )