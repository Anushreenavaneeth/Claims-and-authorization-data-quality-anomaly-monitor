# pipeline/bayesian_root_cause.py

from typing import Dict, List, Any


class BayesianRootCauseEngine:
    """
    Converts Bayesian Network probabilities into
    human-readable probable root causes.

    This component does not train the Bayesian Network.
    It only interprets its probability output.
    """

    # ==================================================
    # CAUSE MAPPING
    # ==================================================

    CAUSE_MAP = {

        "ML_Anomaly": {
            "cause": "multivariate_ml_anomaly",
            "description":
                "Multiple numerical features show unusual behavior."
        },

        "Rule_Anomaly": {
            "cause": "rule_based_anomaly",
            "description":
                "One or more pharmacy anomaly rules were triggered."
        },

        "Behavior_Anomaly": {
            "cause": "historical_behavior_anomaly",
            "description":
                "The record shows unusual behavior compared with historical patterns."
        },

        "Cluster_Anomaly": {
            "cause": "unusual_peer_group_behavior",
            "description":
                "The record differs significantly from its peer cluster."
        },

        "Data_Quality_Issue": {
            "cause": "data_quality_issue",
            "description":
                "The record contains a data-quality inconsistency."
        },

        "SLA_Risk": {
            "cause": "sla_processing_risk",
            "description":
                "The record contributes to increased processing or SLA risk."
        },

        "Overall_Anomaly": {
            "cause": "overall_anomaly",
            "description":
                "Multiple evidence sources indicate anomalous behavior."
        },
    }

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        probability_threshold: float = 0.50,
        minimum_lift: float = 1.0,
    ):

        self.probability_threshold = (
            probability_threshold
        )

        self.minimum_lift = (
            minimum_lift
        )

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
    # CALCULATE LIFT
    # ==================================================

    def calculate_lift(
        self,
        posterior: float,
        baseline: float,
    ) -> float:

        if baseline <= 0:

            return 0.0

        return (
            posterior
            / baseline
        )

    # ==================================================
    # BUILD ONE CAUSE
    # ==================================================

    def build_cause(
        self,
        variable: str,
        posterior: float,
        baseline: float,
    ) -> Dict[str, Any]:

        mapping = self.CAUSE_MAP.get(
            variable,
            {
                "cause": variable,
                "description":
                    f"Bayesian evidence indicates that {variable} contributes to the anomaly."
            },
        )

        lift = self.calculate_lift(
            posterior,
            baseline,
        )

        return {
            "cause":
                mapping["cause"],

            "probability_given_anomaly":
                round(
                    posterior,
                    4,
                ),

            "baseline_probability":
                round(
                    baseline,
                    4,
                ),

            "bayesian_lift":
                round(
                    lift,
                    4,
                ),
        }

    # ==================================================
    # BUILD FROM PROBABILITIES
    # ==================================================

    def build(
        self,
        probabilities: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Expected input:

        {
            "ML_Anomaly": {
                "posterior": 0.82,
                "baseline": 0.15
            },

            "Behavior_Anomaly": {
                "posterior": 0.75,
                "baseline": 0.20
            }
        }
        """

        causes = []

        for variable, values in (
            probabilities.items()
        ):

            if not isinstance(
                values,
                dict,
            ):
                continue

            posterior = self._safe_float(
                values.get(
                    "posterior",
                    0.0,
                )
            )

            baseline = self._safe_float(
                values.get(
                    "baseline",
                    0.0,
                )
            )

            lift = self.calculate_lift(
                posterior,
                baseline,
            )

            # ------------------------------------------
            # Probability threshold
            # ------------------------------------------

            if (
                posterior
                < self.probability_threshold
            ):
                continue

            # ------------------------------------------
            # Lift threshold
            # ------------------------------------------

            if (
                baseline > 0
                and lift < self.minimum_lift
            ):
                continue

            causes.append(
                self.build_cause(
                    variable,
                    posterior,
                    baseline,
                )
            )

        # Highest probability first
        causes.sort(
            key=lambda item:
                item[
                    "probability_given_anomaly"
                ],
            reverse=True,
        )

        return causes