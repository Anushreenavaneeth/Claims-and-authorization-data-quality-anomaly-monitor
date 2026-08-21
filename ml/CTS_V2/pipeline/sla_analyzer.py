# pipeline/sla_analyzer.py

from typing import Dict, Any


class SLAAnalyzer:
    """
    Calculates SLA-related risk from pipeline evidence.

    SLA risk is treated as supporting evidence. It does not
    independently decide the final anomaly.

    The analyzer produces:
        - breach probability
        - workload risk
        - volume risk
        - ML risk
        - quality risk
        - overall SLA risk
    """

    def __init__(
        self,
        breach_threshold: float = 0.50,
    ):
        self.breach_threshold = breach_threshold

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
    # CLAMP
    # ==================================================

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:

        return min(
            max(value, 0.0),
            1.0,
        )

    # ==================================================
    # ANALYZE
    # ==================================================

    def analyze(
        self,
        evidence: Dict[str, Any],
        dataset_size: int = 0,
        processing_time_seconds: float = 0.0,
        batch_size: int = 100000,
    ) -> Dict[str, Any]:

        # ----------------------------------------------
        # Evidence
        # ----------------------------------------------

        rule = evidence.get(
            "rule_based",
            {},
        )

        isolation = evidence.get(
            "isolation_forest",
            {},
        )

        cluster = evidence.get(
            "clustering",
            {},
        )

        behavioral = evidence.get(
            "behavioral",
            {},
        )

        data_quality = evidence.get(
            "data_quality",
            {},
        )

        # ----------------------------------------------
        # Source scores
        # ----------------------------------------------

        rule_score = self._clamp(
            self._safe_float(
                rule.get(
                    "evidence_score",
                    0.0,
                )
            )
        )

        ml_score = self._clamp(
            self._safe_float(
                isolation.get(
                    "anomaly_score",
                    0.0,
                )
            )
        )

        cluster_score = self._clamp(
            self._safe_float(
                cluster.get(
                    "anomaly_score",
                    0.0,
                )
            )
        )

        behavior_score = self._clamp(
            self._safe_float(
                behavioral.get(
                    "score",
                    0.0,
                )
            )
        )

        quality_score = self._clamp(
            self._safe_float(
                data_quality.get(
                    "score",
                    0.0,
                )
            )
        )

        # ----------------------------------------------
        # Volume risk
        # ----------------------------------------------

        volume_risk = 0.0

        if dataset_size > 0:

            number_of_batches = (
                (dataset_size + batch_size - 1)
                // batch_size
            )

            if number_of_batches > 1:

                volume_risk = min(
                    1.0,
                    0.10
                    * (number_of_batches - 1),
                )

        # ----------------------------------------------
        # Workload risk
        # ----------------------------------------------

        workload_risk = 0.0

        if processing_time_seconds > 0:

            # This is deliberately a normalized
            # internal indicator rather than a claim
            # that an SLA was breached.

            workload_risk = min(
                processing_time_seconds
                / 3600.0,
                1.0,
            )

        # ----------------------------------------------
        # ML risk
        # ----------------------------------------------

        ml_risk = max(
            ml_score,
            cluster_score,
        )

        # ----------------------------------------------
        # Quality risk
        # ----------------------------------------------

        quality_risk = quality_score

        # ----------------------------------------------
        # Evidence risk
        # ----------------------------------------------

        evidence_risk = max(
            rule_score,
            behavior_score,
        )

        # ----------------------------------------------
        # Breach probability
        # ----------------------------------------------

        breach_probability = (
            0.25 * workload_risk
            + 0.20 * volume_risk
            + 0.20 * ml_risk
            + 0.20 * quality_risk
            + 0.15 * evidence_risk
        )

        breach_probability = self._clamp(
            breach_probability
        )

        # ----------------------------------------------
        # SLA status
        # ----------------------------------------------

        sla_risk = (
            breach_probability
            >= self.breach_threshold
        )

        return {

            "sla_risk": sla_risk,

            "breach_probability": round(
                breach_probability,
                4,
            ),

            "workload_risk": round(
                workload_risk,
                4,
            ),

            "volume_risk": round(
                volume_risk,
                4,
            ),

            "ml_risk": round(
                ml_risk,
                4,
            ),

            "quality_risk": round(
                quality_risk,
                4,
            ),

            "evidence_risk": round(
                evidence_risk,
                4,
            ),
        }