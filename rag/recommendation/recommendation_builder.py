"""
Healthcare Data Quality Recommendation Builder.

Combines:

XAI Analysis
    ↓
Evidence Matching
    ↓
Root Cause Analysis
    ↓
Resolution Procedure
    ↓
Priority
    ↓
Human-Readable Recommendation
"""

from typing import Any, Dict, List, Optional

from .config import (
    DEFAULT_PRIORITY,
    SEVERITY_PRIORITY_MAP
)

from .evidence_matcher import EvidenceMatcher
from .rca_engine import RCAEngine
from .resolution_engine import ResolutionEngine


class RecommendationBuilder:
    """
    Main recommendation engine.

    Converts XAI analysis and retrieved knowledge into
    an actionable recommendation for administrators
    and operational employees.
    """

    def __init__(self):

        self.evidence_matcher = (
            EvidenceMatcher()
        )

        self.rca_engine = (
            RCAEngine()
        )

        self.resolution_engine = (
            ResolutionEngine()
        )

    # =====================================================
    # Severity
    # =====================================================

    def _extract_severity(
        self,
        xai_result: Dict[str, Any]
    ) -> str:
        """
        Extract the original anomaly severity
        produced by the ML/anomaly-detection layer.
        """

        xai_analysis = (
            xai_result.get(
                "xai_analysis",
                {}
            )
        )

        observed = (
            xai_analysis.get(
                "observed_evidence",
                {}
            )
        )

        severity = observed.get(
            "final_severity"
        )

        if severity is None:

            return "Unknown"

        return str(
            severity
        )

    # =====================================================
    # Risk Score
    # =====================================================

    def _extract_risk_score(
        self,
        xai_result: Dict[str, Any]
    ) -> Optional[float]:
        """
        Extract the final platform risk score.

        Returns:
            float -> when a valid final risk score exists
            None  -> when the ML model did not provide one

        IMPORTANT:
        None must NOT be converted to 0.0.

        For example, the Claims Isolation Forest
        anomaly_score is a different metric from the
        platform final_risk_score.
        """

        xai_analysis = (
            xai_result.get(
                "xai_analysis",
                {}
            )
        )

        observed = (
            xai_analysis.get(
                "observed_evidence",
                {}
            )
        )

        risk_score = observed.get(
            "final_risk_score"
        )

        # -------------------------------------------------
        # No platform risk score supplied
        # -------------------------------------------------

        if risk_score is None:

            return None

        # -------------------------------------------------
        # Convert valid value
        # -------------------------------------------------

        try:

            return float(
                risk_score
            )

        except (
            TypeError,
            ValueError
        ):

            return None

    # =====================================================
    # Priority
    # =====================================================

    def _determine_priority(
        self,
        severity: str,
        risk_score: Optional[float]
    ) -> str:
        """
        Convert anomaly severity and risk into
        an operational priority.

        Severity remains unchanged.

        Priority is a separate operational value.

        If no platform risk score exists, priority is
        determined only from severity.
        """

        severity_lower = (
            str(
                severity
            )
            .strip()
            .lower()
        )

        # -------------------------------------------------
        # Severity mapping
        # -------------------------------------------------

        priority = (
            SEVERITY_PRIORITY_MAP.get(
                severity_lower,
                DEFAULT_PRIORITY
            )
        )

        # -------------------------------------------------
        # Risk escalation
        #
        # Only apply escalation when an actual platform
        # risk score exists.
        # -------------------------------------------------

        if risk_score is not None:

            if risk_score >= 0.85:

                return "Critical"

            if risk_score >= 0.75:

                if priority not in {
                    "Critical"
                }:

                    return "High"

        return priority

    # =====================================================
    # Recommendation Text
    # =====================================================

    def _build_recommendation_text(
        self,
        anomaly_pattern: str,
        rca_result: Dict[str, Any],
        resolution_result: Dict[str, Any],
        priority: str
    ) -> str:
        """
        Build a concise recommendation understandable
        by administrators and operational employees.
        """

        procedure = (
            resolution_result.get(
                "procedure",
                ""
            )
        )

        if not procedure:

            procedure = (
                "Review the affected record against "
                "the source system and applicable "
                "data-quality procedure."
            )

        if anomaly_pattern:

            introduction = (
                f"The record contains a "
                f"{anomaly_pattern} issue."
            )

        else:

            introduction = (
                "A healthcare data-quality issue "
                "was detected in this record."
            )

        return (
            f"{introduction} "
            f"{procedure} "
            f"This issue should be handled with "
            f"{priority} priority."
        )

    # =====================================================
    # Admin Summary
    # =====================================================

    def _build_admin_summary(
        self,
        anomaly_pattern: str,
        severity: str,
        priority: str,
        risk_score: Optional[float]
    ) -> str:
        """
        Short monitoring-oriented summary for
        an administrator/dashboard.

        If risk_score is unavailable, do not display
        a fake 0.0000 value.
        """

        anomaly_name = (
            anomaly_pattern
            if anomaly_pattern
            else "data-quality anomaly"
        )

        # -------------------------------------------------
        # Risk score available
        # -------------------------------------------------

        if risk_score is not None:

            return (
                f"{anomaly_name} detected with "
                f"{severity} severity and a risk score "
                f"of {risk_score:.4f}. "
                f"Operational priority: {priority}."
            )

        # -------------------------------------------------
        # Risk score unavailable
        # -------------------------------------------------

        return (
            f"{anomaly_name} detected with "
            f"{severity} severity. "
            f"Platform risk score unavailable. "
            f"Operational priority: {priority}."
        )

    # =====================================================
    # Employee Action
    # =====================================================

    def _build_employee_action(
        self,
        resolution_result: Dict[str, Any]
    ) -> str:
        """
        Action-oriented text for the employee
        responsible for resolving the anomaly.
        """

        procedure = (
            resolution_result.get(
                "procedure"
            )
        )

        if procedure:

            return str(
                procedure
            )

        return (
            "Verify the affected record against the "
            "source system, correct the identified "
            "data-quality issue, and revalidate the "
            "record before reprocessing."
        )

    # =====================================================
    # Main Builder
    # =====================================================

    def build(
        self,
        xai_result: Dict[str, Any],
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build the complete recommendation result.
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

        # =================================================
        # XAI Information
        # =================================================

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

        explanation = str(
            xai_analysis.get(
                "explanation",
                ""
            )
        )

        # =================================================
        # Evidence Matching
        # =================================================

        evidence_result = (
            self.evidence_matcher.match(
                xai_result=xai_result,
                retrieved_knowledge=(
                    retrieved_knowledge
                )
            )
        )

        matched_knowledge = (
            evidence_result.get(
                "matched_knowledge",
                []
            )
        )

        # =================================================
        # RCA
        # =================================================

        rca_result = (
            self.rca_engine.identify(
                xai_result=xai_result,
                matched_knowledge=(
                    matched_knowledge
                )
            )
        )

        # =================================================
        # Resolution
        # =================================================

        resolution_result = (
            self.resolution_engine.resolve(
                xai_result=xai_result,
                rca_result=rca_result,
                matched_knowledge=(
                    matched_knowledge
                )
            )
        )

        # =================================================
        # Severity / Risk / Priority
        # =================================================

        severity = (
            self._extract_severity(
                xai_result
            )
        )

        risk_score = (
            self._extract_risk_score(
                xai_result
            )
        )

        priority = (
            self._determine_priority(
                severity=severity,
                risk_score=risk_score
            )
        )

        # =================================================
        # Human-readable Recommendation
        # =================================================

        recommendation = (
            self._build_recommendation_text(
                anomaly_pattern=(
                    anomaly_pattern
                ),

                rca_result=(
                    rca_result
                ),

                resolution_result=(
                    resolution_result
                ),

                priority=priority
            )
        )

        # =================================================
        # Admin Summary
        # =================================================

        admin_summary = (
            self._build_admin_summary(
                anomaly_pattern=(
                    anomaly_pattern
                ),

                severity=severity,

                priority=priority,

                risk_score=risk_score
            )
        )

        # =================================================
        # Employee Action
        # =================================================

        employee_action = (
            self._build_employee_action(
                resolution_result
            )
        )

        # =================================================
        # Final Output
        # =================================================

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

            "anomaly":
                anomaly_pattern,

            "severity":
                severity,

            "risk_score":
                risk_score,

            "priority":
                priority,

            "explanation":
                explanation,

            "evidence_matching": {

                "evidence_terms":
                    evidence_result.get(
                        "evidence_terms",
                        []
                    ),

                "match_count":
                    evidence_result.get(
                        "match_count",
                        0
                    ),

                "matched_sources": [
                    item.get(
                        "source",
                        "unknown"
                    )
                    for item
                    in matched_knowledge
                ]
            },

            "root_cause":
                rca_result,

            "resolution":
                resolution_result,

            "admin_summary":
                admin_summary,

            "employee_action":
                employee_action,

            "recommendation":
                recommendation
        }