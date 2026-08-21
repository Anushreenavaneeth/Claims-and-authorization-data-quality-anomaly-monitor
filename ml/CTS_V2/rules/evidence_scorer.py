# rules/evidence_scorer.py

from typing import Dict, List, Any


class EvidenceScorer:
    """
    Converts classified rule evidence into a normalized
    rule evidence score between 0 and 1.

    This is NOT the final anomaly score.

    It only measures how strongly the rule engine
    supports the possibility of an anomaly.
    """

    # ==================================================
    # BASE WEIGHTS
    # ==================================================

    SEVERITY_WEIGHTS = {
        "HIGH": 0.75,
        "MEDIUM": 0.45,
        "LOW": 0.20,
        "INFO": 0.00,
    }

    CATEGORY_MULTIPLIERS = {
        "HARD_ANOMALY": 1.00,
        "DATA_QUALITY": 0.85,
        "BEHAVIOR_EVIDENCE": 0.65,
        "CONTEXT": 0.00,
        "UNKNOWN": 0.25,
    }

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        severity_weights: Dict[str, float] = None,
        category_multipliers: Dict[str, float] = None,
    ):

        self.severity_weights = (
            severity_weights
            if severity_weights is not None
            else self.SEVERITY_WEIGHTS.copy()
        )

        self.category_multipliers = (
            category_multipliers
            if category_multipliers is not None
            else self.CATEGORY_MULTIPLIERS.copy()
        )

    # ==================================================
    # SINGLE EVIDENCE SCORE
    # ==================================================

    def score_evidence(
        self,
        evidence: Dict[str, Any],
    ) -> float:
        """
        Calculate score for one evidence item.
        """

        severity = evidence.get(
            "severity",
            "INFO",
        )

        category = evidence.get(
            "category",
            "UNKNOWN",
        )

        severity_weight = self.severity_weights.get(
            severity,
            0.0,
        )

        category_multiplier = (
            self.category_multipliers.get(
                category,
                0.25,
            )
        )

        score = (
            severity_weight
            * category_multiplier
        )

        return min(
            max(score, 0.0),
            1.0,
        )

    # ==================================================
    # SCORE ALL EVIDENCE
    # ==================================================

    def score_evidence_list(
        self,
        evidence_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Add an evidence_score field to every
        evidence item.
        """

        scored = []

        for evidence in evidence_list:

            item = evidence.copy()

            item["evidence_score"] = round(
                self.score_evidence(
                    evidence
                ),
                4,
            )

            scored.append(item)

        return scored

    # ==================================================
    # COMBINE EVIDENCE
    # ==================================================

    def combine_scores(
        self,
        scored_evidence: List[Dict[str, Any]],
    ) -> float:
        """
        Combine multiple evidence scores.

        We do NOT simply sum them because that could
        exceed 1.0.

        Instead we use:

            1 - product(1 - score)

        This means multiple independent pieces of
        evidence strengthen the overall score while
        keeping it between 0 and 1.
        """

        if not scored_evidence:

            return 0.0

        combined = 0.0

        for evidence in scored_evidence:

            score = float(
                evidence.get(
                    "evidence_score",
                    0.0,
                )
            )

            score = min(
                max(score, 0.0),
                1.0,
            )

            combined = (
                1.0
                - (
                    (1.0 - combined)
                    * (1.0 - score)
                )
            )

        return min(
            max(combined, 0.0),
            1.0,
        )

    # ==================================================
    # CATEGORY SCORES
    # ==================================================

    def category_scores(
        self,
        scored_evidence: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Calculate separate scores for each
        evidence category.
        """

        categories = {
            "HARD_ANOMALY": [],
            "DATA_QUALITY": [],
            "BEHAVIOR_EVIDENCE": [],
            "CONTEXT": [],
            "UNKNOWN": [],
        }

        for evidence in scored_evidence:

            category = evidence.get(
                "category",
                "UNKNOWN",
            )

            score = float(
                evidence.get(
                    "evidence_score",
                    0.0,
                )
            )

            if category not in categories:
                category = "UNKNOWN"

            categories[category].append(
                score
            )

        result = {}

        for category, scores in categories.items():

            if not scores:

                result[category] = 0.0

            else:

                result[category] = round(
                    max(scores),
                    4,
                )

        return result

    # ==================================================
    # COMPLETE RESULT
    # ==================================================

    def calculate(
        self,
        classified_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate the complete rule evidence result.
        """

        all_evidence = []

        all_evidence.extend(
            classified_result.get(
                "hard_anomalies",
                [],
            )
        )

        all_evidence.extend(
            classified_result.get(
                "behavior_evidence",
                [],
            )
        )

        all_evidence.extend(
            classified_result.get(
                "data_quality_evidence",
                [],
            )
        )

        all_evidence.extend(
            classified_result.get(
                "context_evidence",
                [],
            )
        )

        all_evidence.extend(
            classified_result.get(
                "unknown_rules",
                [],
            )
        )

        # ----------------------------------------------
        # Score evidence
        # ----------------------------------------------

        scored = self.score_evidence_list(
            all_evidence
        )

        # ----------------------------------------------
        # Context does not contribute to anomaly score
        # ----------------------------------------------

        anomaly_evidence = [
            evidence
            for evidence in scored
            if evidence.get(
                "category"
            ) != "CONTEXT"
        ]

        # ----------------------------------------------
        # Combined score
        # ----------------------------------------------

        rule_evidence_score = (
            self.combine_scores(
                anomaly_evidence
            )
        )

        # ----------------------------------------------
        # Category scores
        # ----------------------------------------------

        category_score = (
            self.category_scores(
                scored
            )
        )

        # ----------------------------------------------
        # Count evidence
        # ----------------------------------------------

        return {
            "rule_evidence_score": round(
                rule_evidence_score,
                4,
            ),

            "hard_anomaly_score":
                category_score[
                    "HARD_ANOMALY"
                ],

            "data_quality_score":
                category_score[
                    "DATA_QUALITY"
                ],

            "behavior_evidence_score":
                category_score[
                    "BEHAVIOR_EVIDENCE"
                ],

            "context_score":
                category_score[
                    "CONTEXT"
                ],

            "evidence_count":
                len(anomaly_evidence),

            "context_count":
                len(
                    classified_result.get(
                        "context_evidence",
                        [],
                    )
                ),

            "scored_evidence":
                scored,
        }