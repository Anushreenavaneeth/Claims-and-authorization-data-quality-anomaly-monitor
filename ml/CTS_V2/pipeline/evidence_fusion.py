# pipeline/evidence_fusion.py

from typing import Dict, Any


class EvidenceFusion:
    """
    Combines evidence from:

    - Rule engine
    - Isolation Forest
    - K-Means
    - Historical behavior
    - Data quality

    This class does NOT make the final anomaly decision.

    It creates a unified evidence structure that will later
    be passed to the Bayesian Network and final output builder.
    """

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(self):

        pass

    # ==================================================
    # SAFE FLOAT
    # ==================================================

    @staticmethod
    def _safe_float(
        value,
        default=0.0,
    ):

        try:

            if value is None:
                return default

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ==================================================
    # SAFE BOOL
    # ==================================================

    @staticmethod
    def _safe_bool(
        value,
        default=False,
    ):

        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):

            return value.strip().lower() in {
                "true",
                "1",
                "yes",
                "y",
            }

        return bool(value)

    # ==================================================
    # FUSE ONE RECORD
    # ==================================================

    def fuse_record(
        self,
        rule_result: Dict[str, Any],
        isolation_result: Dict[str, Any],
        cluster_result: Dict[str, Any],
        behavioral_result: Dict[str, Any] = None,
        data_quality_result: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        behavioral_result = (
            behavioral_result or {}
        )

        data_quality_result = (
            data_quality_result or {}
        )

        # ----------------------------------------------
        # Rule evidence
        # ----------------------------------------------

        rule_anomaly = self._safe_bool(
            rule_result.get(
                "rule_anomaly",
                False,
            )
        )

        rule_severity = (
            rule_result.get(
                "severity",
                "NONE",
            )
        )

        rule_evidence_score = (
            self._safe_float(
                rule_result.get(
                    "rule_evidence_score",
                    0.0,
                )
            )
        )

        # ----------------------------------------------
        # Isolation Forest
        # ----------------------------------------------

        isolation_anomaly = (
            self._safe_bool(
                isolation_result.get(
                    "is_anomaly",
                    False,
                )
            )
        )

        isolation_score = (
            self._safe_float(
                isolation_result.get(
                    "anomaly_score",
                    0.0,
                )
            )
        )

        # ----------------------------------------------
        # K-Means
        # ----------------------------------------------

        cluster_anomaly = (
            self._safe_bool(
                cluster_result.get(
                    "is_anomaly",
                    False,
                )
            )
        )

        cluster_score = (
            self._safe_float(
                cluster_result.get(
                    "cluster_anomaly_score",
                    0.0,
                )
            )
        )

        cluster_id = cluster_result.get(
            "cluster_id"
        )

        cluster_distance = (
            self._safe_float(
                cluster_result.get(
                    "cluster_distance",
                    0.0,
                )
            )
        )

        # ----------------------------------------------
        # Behavioral evidence
        # ----------------------------------------------

        behavior_anomaly = (
            self._safe_bool(
                behavioral_result.get(
                    "behavior_anomaly",
                    False,
                )
            )
        )

        behavior_score = (
            self._safe_float(
                behavioral_result.get(
                    "behavior_score",
                    0.0,
                )
            )
        )

        # ----------------------------------------------
        # Data quality
        # ----------------------------------------------

        data_quality_issue = (
            self._safe_bool(
                data_quality_result.get(
                    "data_quality_issue",
                    False,
                )
            )
        )

        data_quality_score = (
            self._safe_float(
                data_quality_result.get(
                    "data_quality_score",
                    0.0,
                )
            )
        )

        # ----------------------------------------------
        # Combined evidence
        # ----------------------------------------------

        evidence_sources = {

            "rule_based": rule_anomaly,

            "isolation_forest":
                isolation_anomaly,

            "clustering":
                cluster_anomaly,

            "behavioral":
                behavior_anomaly,

            "data_quality":
                data_quality_issue,
        }

        # ----------------------------------------------
        # Evidence count
        # ----------------------------------------------

        active_sources = sum(
            1
            for value in evidence_sources.values()
            if value
        )

        # ----------------------------------------------
        # Multi-source agreement
        # ----------------------------------------------

        multi_source_anomaly = (
            active_sources >= 2
        )

        # ----------------------------------------------
        # Fusion score
        # ----------------------------------------------

        # Only ACTIVE anomaly sources contribute
        # to the fusion score.
        #
        # A normal Isolation Forest result, for example,
        # must not contribute its small normal score.
        #
        # The fusion score is NOT the final anomaly
        # probability. The Bayesian Network will later
        # interpret the combined evidence.

        active_scores = []

        if rule_anomaly:

            active_scores.append(
                rule_evidence_score
            )

        if isolation_anomaly:

            active_scores.append(
                isolation_score
            )

        if cluster_anomaly:

            active_scores.append(
                cluster_score
            )

        if behavior_anomaly:

            active_scores.append(
                behavior_score
            )

        if data_quality_issue:

            active_scores.append(
                data_quality_score
            )

        # ----------------------------------------------
        # Calculate fusion score
        # ----------------------------------------------

        if active_scores:

            fusion_score = (
                sum(active_scores)
                / len(active_scores)
            )

        else:

            fusion_score = 0.0

        fusion_score = min(
            max(fusion_score, 0.0),
            1.0,
        )

        # ----------------------------------------------
        # Final unified evidence object
        # ----------------------------------------------

        return {

            "rule_based": {

                "anomaly":
                    rule_anomaly,

                "severity":
                    rule_severity,

                "evidence_score":
                    rule_evidence_score,
            },

            "isolation_forest": {

                "anomaly":
                    isolation_anomaly,

                "anomaly_score":
                    isolation_score,
            },

            "clustering": {

                "anomaly":
                    cluster_anomaly,

                "cluster_id":
                    cluster_id,

                "cluster_distance":
                    cluster_distance,

                "anomaly_score":
                    cluster_score,
            },

            "behavioral": {

                "anomaly":
                    behavior_anomaly,

                "score":
                    behavior_score,
            },

            "data_quality": {

                "issue":
                    data_quality_issue,

                "score":
                    data_quality_score,
            },

            "fusion": {

                "active_sources":
                    active_sources,

                "multi_source_anomaly":
                    multi_source_anomaly,

                "fusion_score":
                    round(
                        fusion_score,
                        4,
                    ),
            },
        }