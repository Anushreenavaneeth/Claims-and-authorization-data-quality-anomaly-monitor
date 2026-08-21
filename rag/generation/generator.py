"""
Human-readable recommendation generator.

Responsibilities:

ML/XAI evidence
        ↓
Severity
        ↓
Operational Priority
        ↓
SLA
        ↓
Resolution Procedure
        ↓
Human-readable Recommendation
"""

from typing import Any, Dict, List

from .config import (
    DEFAULT_PRIORITY,
    DEFAULT_SLA,
    MIN_KNOWLEDGE_SCORE
)


class Generator:
    """
    Generates human-readable explanations,
    RCA, resolution procedures, SLA,
    priority and recommendations.
    """

    # =====================================================
    # Severity
    # =====================================================

    def _extract_severity(
        self,
        evidence: Dict[str, Any]
    ) -> str:

        severity = evidence.get(
            "final_severity"
        )

        if severity is None:

            return "Unknown"

        return str(
            severity
        )

    # =====================================================
    # Priority
    # =====================================================

    def _determine_priority(
        self,
        evidence: Dict[str, Any]
    ) -> str:
        """
        Convert ML severity/risk into an
        operational priority.

        Severity and priority are intentionally
        kept as separate fields.
        """

        severity = str(
            evidence.get(
                "final_severity",
                ""
            )
        ).lower()

        risk_score = float(
            evidence.get(
                "final_risk_score",
                0.0
            ) or 0.0
        )

        # Critical / High severity
        if severity in {
            "critical",
            "high"
        }:

            return "High"

        # Very high risk
        if risk_score >= 0.75:

            return "High"

        # Warning / Medium
        if severity in {
            "warning",
            "medium"
        }:

            return "Medium"

        return DEFAULT_PRIORITY

    # =====================================================
    # SLA
    # =====================================================

    def _extract_sla(
        self,
        evidence: Dict[str, Any],
        xai_result: Dict[str, Any]
    ) -> str:
        """
        Preserve the SLA supplied by ML.

        The generator must not invent an SLA when
        the ML input already provides one.
        """

        # -------------------------------------------------
        # Primary source:
        # observed ML evidence
        # -------------------------------------------------

        sla = evidence.get(
            "sla"
        )

        if sla:

            return str(
                sla
            )

        # -------------------------------------------------
        # Secondary source:
        # top-level XAI result
        # -------------------------------------------------

        sla = xai_result.get(
            "sla"
        )

        if sla:

            return str(
                sla
            )

        # -------------------------------------------------
        # Fallback
        # -------------------------------------------------

        return DEFAULT_SLA

    # =====================================================
    # Root Cause
    # =====================================================

    def _build_root_cause(
        self,
        xai_analysis: Dict[str, Any]
    ) -> str:
        """
        Use the RCA identified by XAI.
        """

        root_cause = (
            xai_analysis.get(
                "likely_root_cause",
                {}
            )
        )

        cause = root_cause.get(
            "cause"
        )

        if cause:

            return str(
                cause
            )

        pattern = xai_analysis.get(
            "matched_anomaly_pattern"
        )

        if pattern:

            return (
                "The available evidence indicates "
                f"a {pattern} data-quality issue."
            )

        return (
            "The root cause could not be "
            "determined from the available evidence."
        )

    # =====================================================
    # Resolution Procedure
    # =====================================================

    def _build_resolution(
        self,
        xai_analysis: Dict[str, Any],
        knowledge: List[Dict[str, Any]]
    ) -> str:
        """
        Build a human-readable resolution procedure
        grounded in the identified anomaly pattern
        and retrieved knowledge.
        """

        pattern = str(
            xai_analysis.get(
                "matched_anomaly_pattern",
                ""
            )
        ).lower()

        # -------------------------------------------------
        # Invalid date sequence
        # -------------------------------------------------

        if "invalid date" in pattern:

            return (
                "Verify the authorization date and service "
                "date against the source system. Correct "
                "the invalid date sequence and revalidate "
                "the record before reprocessing."
            )

        # -------------------------------------------------
        # Missing documentation
        # -------------------------------------------------

        if (
            "missing document" in pattern
            or "documentation" in pattern
        ):

            return (
                "Verify the required supporting documents. "
                "Obtain any missing documentation, update "
                "the record, and revalidate it before "
                "continuing processing."
            )

        # -------------------------------------------------
        # Duplicate records
        # -------------------------------------------------

        if "duplicate" in pattern:

            return (
                "Verify whether the record is a true "
                "duplicate against the source system. "
                "Retain the valid record, resolve the "
                "duplicate entry according to the "
                "documented procedure, and revalidate "
                "the data."
            )

        # -------------------------------------------------
        # Schema mismatch
        # -------------------------------------------------

        if "schema" in pattern:

            return (
                "Compare the affected record with the "
                "expected schema. Correct the field or "
                "structure mismatch and revalidate the "
                "record before reprocessing."
            )

        # -------------------------------------------------
        # Reconciliation failure
        # -------------------------------------------------

        if "reconciliation" in pattern:

            return (
                "Compare the affected records with the "
                "source system and identify the "
                "reconciliation difference. Correct the "
                "underlying data issue and rerun the "
                "reconciliation process."
            )

        # -------------------------------------------------
        # Generic knowledge-grounded procedure
        # -------------------------------------------------

        for item in knowledge:

            score = float(
                item.get(
                    "hybrid_score",
                    0.0
                )
            )

            content = item.get(
                "content",
                ""
            )

            if (
                score >= MIN_KNOWLEDGE_SCORE
                and content
            ):

                return (
                    "Review the affected record against "
                    "the retrieved knowledge-base "
                    "guidance. Correct the identified "
                    "data-quality issue, revalidate the "
                    "record, and reprocess it according "
                    "to the documented procedure."
                )

        # -------------------------------------------------
        # Final fallback
        # -------------------------------------------------

        return (
            "Review the affected record, verify the "
            "detected anomaly against the source data, "
            "correct the underlying data-quality issue, "
            "and revalidate the record before "
            "reprocessing."
        )

    # =====================================================
    # Recommendation
    # =====================================================

    def _build_recommendation(
        self,
        pattern: str,
        resolution: str,
        priority: str,
        sla: str
    ) -> str:
        """
        Create the final human-readable recommendation.
        """

        return (
            f"Review the record for the identified "
            f"{pattern} issue. "
            f"{resolution} "
            f"The recommended priority is {priority}. "
            f"{sla}."
        )

    # =====================================================
    # Main Generation
    # =====================================================

    def generate(
        self,
        xai_result: Dict[str, Any],
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate structured and human-readable output.
        """

        if not isinstance(
            xai_result,
            dict
        ):

            raise TypeError(
                "xai_result must be a dictionary."
            )

        if not isinstance(
            retrieved_knowledge,
            list
        ):

            raise TypeError(
                "retrieved_knowledge must be a list."
            )

        # -------------------------------------------------
        # XAI Analysis
        # -------------------------------------------------

        xai_analysis = (
            xai_result.get(
                "xai_analysis",
                {}
            )
        )

        # -------------------------------------------------
        # Observed ML Evidence
        # -------------------------------------------------

        evidence = (
            xai_analysis.get(
                "observed_evidence",
                {}
            )
        )

        # -------------------------------------------------
        # Severity
        # -------------------------------------------------

        severity = (
            self._extract_severity(
                evidence
            )
        )

        # -------------------------------------------------
        # Priority
        # -------------------------------------------------

        priority = (
            self._determine_priority(
                evidence
            )
        )

        # -------------------------------------------------
        # SLA
        # -------------------------------------------------

        sla = (
            self._extract_sla(
                evidence,
                xai_result
            )
        )

        # -------------------------------------------------
        # Anomaly Pattern
        # -------------------------------------------------

        anomaly = xai_analysis.get(
            "matched_anomaly_pattern",
            "Unknown anomaly"
        )

        # -------------------------------------------------
        # Root Cause
        # -------------------------------------------------

        root_cause = (
            self._build_root_cause(
                xai_analysis
            )
        )

        # -------------------------------------------------
        # Resolution
        # -------------------------------------------------

        resolution = (
            self._build_resolution(
                xai_analysis,
                retrieved_knowledge
            )
        )

        # -------------------------------------------------
        # Recommendation
        # -------------------------------------------------

        recommendation = (
            self._build_recommendation(
                anomaly,
                resolution,
                priority,
                sla
            )
        )

        # -------------------------------------------------
        # Final Result
        # -------------------------------------------------

        return {

            "record_id":
                xai_result.get(
                    "record_id",
                    "unknown"
                ),

            "dataset_type":
                xai_result.get(
                    "dataset_type",
                    "unknown"
                ),

            "severity":
                severity,

            "priority":
                priority,

            "anomaly":
                anomaly,

            "explanation":
                xai_analysis.get(
                    "explanation",
                    ""
                ),

            "root_cause":
                root_cause,

            "resolution_procedure":
                resolution,

            "sla":
                sla,

            "recommendation":
                recommendation
        }