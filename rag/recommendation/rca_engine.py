"""
Root Cause Analysis engine.

Uses XAI evidence and matched knowledge to identify
the most likely root cause of a healthcare data-quality
anomaly.
"""

from typing import Any, Dict, List


class RCAEngine:
    """
    Converts XAI evidence into a clear,
    human-readable root-cause statement.
    """

    # =====================================================
    # Main RCA Analysis
    # =====================================================

    def identify(
        self,
        xai_result: Dict[str, Any],
        matched_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify the likely root cause from XAI evidence
        and supporting knowledge.
        """

        if not isinstance(
            xai_result,
            dict
        ):
            raise TypeError(
                "xai_result must be a dictionary."
            )

        if not isinstance(
            matched_knowledge,
            list
        ):
            raise TypeError(
                "matched_knowledge must be a list."
            )

        xai_analysis = (
            xai_result.get(
                "xai_analysis",
                {}
            )
        )

        # -------------------------------------------------
        # Extract existing XAI RCA
        # -------------------------------------------------

        existing_rca = (
            xai_analysis.get(
                "likely_root_cause",
                {}
            )
        )

        existing_cause = (
            existing_rca.get(
                "cause"
            )
        )

        existing_basis = (
            existing_rca.get(
                "basis",
                []
            )
        )

        # -------------------------------------------------
        # Extract anomaly pattern
        # -------------------------------------------------

        anomaly_pattern = (
            xai_analysis.get(
                "matched_anomaly_pattern",
                ""
            )
        )

        # -------------------------------------------------
        # Build supporting sources
        # -------------------------------------------------

        supporting_sources = []

        for knowledge in matched_knowledge:

            source = knowledge.get(
                "source"
            )

            if source:
                supporting_sources.append(
                    source
                )

        # Remove duplicate sources

        supporting_sources = list(
            dict.fromkeys(
                supporting_sources
            )
        )

        # =================================================
        # Known RCA from XAI
        # =================================================

        if existing_cause:

            cause = str(
                existing_cause
            )

            status = existing_rca.get(
                "status",
                "likely"
            )

            return {
                "status": status,

                "cause": cause,

                "basis": existing_basis,

                "supporting_sources":
                    supporting_sources,

                "confidence": self._calculate_confidence(
                    existing_cause,
                    matched_knowledge
                )
            }

        # =================================================
        # Pattern-based RCA
        # =================================================

        pattern_lower = str(
            anomaly_pattern
        ).lower()

        # -------------------------------------------------
        # Invalid date sequence
        # -------------------------------------------------

        if "invalid date" in pattern_lower:

            cause = (
                "The service date occurs before the "
                "authorization date, indicating an "
                "invalid date-sequence data-quality issue. "
                "This may be caused by incorrect source "
                "data, date transformation issues, or "
                "upstream transmission problems."
            )

            return {
                "status": "likely",

                "cause": cause,

                "basis": [
                    "invalid_date_sequence"
                ],

                "supporting_sources":
                    supporting_sources,

                "confidence": self._calculate_confidence(
                    cause,
                    matched_knowledge
                )
            }

        # -------------------------------------------------
        # Missing documentation
        # -------------------------------------------------

        if (
            "missing document" in pattern_lower
            or "documentation" in pattern_lower
        ):

            cause = (
                "Required supporting documentation is "
                "missing from the affected record, "
                "indicating incomplete source or "
                "submission data."
            )

            return {
                "status": "likely",

                "cause": cause,

                "basis": [
                    "missing_documentation"
                ],

                "supporting_sources":
                    supporting_sources,

                "confidence": self._calculate_confidence(
                    cause,
                    matched_knowledge
                )
            }

        # -------------------------------------------------
        # Duplicate records
        # -------------------------------------------------

        if "duplicate" in pattern_lower:

            cause = (
                "The record appears to have been "
                "transmitted or created more than once, "
                "indicating a possible duplicate "
                "transmission or upstream duplication issue."
            )

            return {
                "status": "likely",

                "cause": cause,

                "basis": [
                    "duplicate_record"
                ],

                "supporting_sources":
                    supporting_sources,

                "confidence": self._calculate_confidence(
                    cause,
                    matched_knowledge
                )
            }

        # -------------------------------------------------
        # Schema mismatch
        # -------------------------------------------------

        if "schema" in pattern_lower:

            cause = (
                "The affected record does not conform "
                "to the expected healthcare data schema, "
                "indicating a possible schema or source "
                "mapping issue."
            )

            return {
                "status": "likely",

                "cause": cause,

                "basis": [
                    "schema_mismatch"
                ],

                "supporting_sources":
                    supporting_sources,

                "confidence": self._calculate_confidence(
                    cause,
                    matched_knowledge
                )
            }

        # -------------------------------------------------
        # Reconciliation failure
        # -------------------------------------------------

        if "reconciliation" in pattern_lower:

            cause = (
                "The affected record does not reconcile "
                "with the corresponding source or "
                "downstream data, indicating a possible "
                "data synchronization or transformation issue."
            )

            return {
                "status": "likely",

                "cause": cause,

                "basis": [
                    "reconciliation_failure"
                ],

                "supporting_sources":
                    supporting_sources,

                "confidence": self._calculate_confidence(
                    cause,
                    matched_knowledge
                )
            }

        # =================================================
        # Knowledge-based RCA
        # =================================================

        for knowledge in matched_knowledge:

            content = str(
                knowledge.get(
                    "content",
                    ""
                )
            )

            score = float(
                knowledge.get(
                    "hybrid_score",
                    0.0
                ) or 0.0
            )

            if (
                score >= 0.50
                and content
            ):

                cause = (
                    "The available knowledge-base evidence "
                    "supports the identified anomaly as a "
                    "healthcare data-quality issue. The "
                    "specific root cause should be verified "
                    "against the source system before "
                    "remediation."
                )

                return {
                    "status": "possible",

                    "cause": cause,

                    "basis": [
                        anomaly_pattern
                    ] if anomaly_pattern else [],

                    "supporting_sources":
                        supporting_sources,

                    "confidence": self._calculate_confidence(
                        cause,
                        matched_knowledge
                    )
                }

        # =================================================
        # Insufficient Evidence
        # =================================================

        return {
            "status": "undetermined",

            "cause": (
                "The available evidence is insufficient "
                "to determine a specific root cause. "
                "The affected record should be verified "
                "against the source system."
            ),

            "basis": [],

            "supporting_sources":
                supporting_sources,

            "confidence": "Low"
        }

    # =====================================================
    # Confidence
    # =====================================================

    def _calculate_confidence(
        self,
        cause: str,
        matched_knowledge: List[Dict[str, Any]]
    ) -> str:
        """
        Estimate RCA confidence using the available
        supporting knowledge.

        This is a rule-based confidence indicator,
        not an ML probability.
        """

        if not matched_knowledge:

            return "Low"

        highest_score = 0.0

        for knowledge in matched_knowledge:

            score = float(
                knowledge.get(
                    "hybrid_score",
                    0.0
                ) or 0.0
            )

            highest_score = max(
                highest_score,
                score
            )

        if highest_score >= 0.70:

            return "High"

        if highest_score >= 0.50:

            return "Medium"

        return "Low"