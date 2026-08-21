# models/bayesian_network.py

from pathlib import Path
from typing import Optional

import joblib
import pandas as pd

from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD


class BayesianAnomalyNetwork:
    """
    Bayesian Network for probabilistic anomaly reasoning.

    The network combines multiple evidence sources:

        Rule anomaly
        ML anomaly
        Behavior anomaly
        Cluster anomaly
        Data-quality issue
        SLA risk

    and estimates:

        P(overall_anomaly)

    This is a reasoning layer, not the primary anomaly detector.
    """

    def __init__(self):
        self.model = None
        self.inference = None
        self.is_fitted = False

    # --------------------------------------------------
    # Build network
    # --------------------------------------------------

    def build(self):
        """
        Build a small discrete Bayesian Network.

        All evidence variables have two states:

            0 = False / Low
            1 = True / High
        """

        model = DiscreteBayesianNetwork(
            [
                ("ML_Anomaly", "Overall_Anomaly"),
                ("Rule_Anomaly", "Overall_Anomaly"),
                ("Behavior_Anomaly", "Overall_Anomaly"),
                ("Cluster_Anomaly", "Overall_Anomaly"),
                ("Data_Quality_Issue", "Overall_Anomaly"),
                ("SLA_Risk", "Overall_Anomaly"),
            ]
        )

        # --------------------------------------------------
        # Prior probabilities
        # --------------------------------------------------

        ml_cpd = TabularCPD(
            variable="ML_Anomaly",
            variable_card=2,
            values=[
                [0.99],
                [0.01],
            ],
        )

        rule_cpd = TabularCPD(
            variable="Rule_Anomaly",
            variable_card=2,
            values=[
                [0.90],
                [0.10],
            ],
        )

        behavior_cpd = TabularCPD(
            variable="Behavior_Anomaly",
            variable_card=2,
            values=[
                [0.90],
                [0.10],
            ],
        )

        cluster_cpd = TabularCPD(
            variable="Cluster_Anomaly",
            variable_card=2,
            values=[
                [0.90],
                [0.10],
            ],
        )

        quality_cpd = TabularCPD(
            variable="Data_Quality_Issue",
            variable_card=2,
            values=[
                [0.85],
                [0.15],
            ],
        )

        sla_cpd = TabularCPD(
            variable="SLA_Risk",
            variable_card=2,
            values=[
                [0.90],
                [0.10],
            ],
        )

        # --------------------------------------------------
        # Overall anomaly CPD
        # --------------------------------------------------
        #
        # Six binary evidence variables produce:
        #
        # 2^6 = 64 evidence combinations.
        #
        # We generate the probabilities automatically
        # instead of manually writing all 64 combinations.
        #

        overall_cpd = self._build_overall_cpd()

        model.add_cpds(
            ml_cpd,
            rule_cpd,
            behavior_cpd,
            cluster_cpd,
            quality_cpd,
            sla_cpd,
            overall_cpd,
        )

        if not model.check_model():
            raise RuntimeError(
                "Bayesian Network failed validation."
            )

        self.model = model

        self.inference = VariableElimination(
            self.model
        )

        self.is_fitted = True

        return self

    # --------------------------------------------------
    # Overall anomaly CPD
    # --------------------------------------------------

    def _build_overall_cpd(self):
        """
        Build the conditional probability table for
        Overall_Anomaly.

        Evidence is converted into a weighted risk score.

        This is a development baseline. Later, these
        probabilities should be calibrated using validated
        historical/labelled evidence.
        """

        evidence_variables = [
            "ML_Anomaly",
            "Rule_Anomaly",
            "Behavior_Anomaly",
            "Cluster_Anomaly",
            "Data_Quality_Issue",
            "SLA_Risk",
        ]

        # Evidence weights.
        #
        # ML and behavioral evidence receive stronger
        # weights than SLA/data-quality indicators because
        # those are closer to anomaly behavior itself.
        weights = {
            "ML_Anomaly": 0.25,
            "Rule_Anomaly": 0.20,
            "Behavior_Anomaly": 0.25,
            "Cluster_Anomaly": 0.15,
            "Data_Quality_Issue": 0.05,
            "SLA_Risk": 0.10,
        }

        # Generate all 64 binary combinations.
        combinations = []

        for number in range(64):

            state = []

            for position in range(6):
                state.append(
                    (number >> position) & 1
                )

            combinations.append(state)

        probability_normal = []
        probability_anomaly = []

        for state in combinations:

            risk_score = 0.0

            for index, variable in enumerate(
                evidence_variables
            ):

                evidence_value = state[index]

                risk_score += (
                    weights[variable]
                    * evidence_value
                )

            # Convert weighted evidence into a
            # probability-like value.
            #
            # Baseline probability is kept small when
            # no evidence is present.
            anomaly_probability = min(
                0.99,
                0.01 + (0.98 * risk_score)
            )

            probability_anomaly.append(
                anomaly_probability
            )

            probability_normal.append(
                1.0 - anomaly_probability
            )

        return TabularCPD(
            variable="Overall_Anomaly",
            variable_card=2,
            values=[
                probability_normal,
                probability_anomaly,
            ],
            evidence=evidence_variables,
            evidence_card=[2, 2, 2, 2, 2, 2],
        )

    # --------------------------------------------------
    # Probability prediction
    # --------------------------------------------------

    def predict_probability(
        self,
        evidence: dict,
    ) -> float:
        """
        Calculate P(Overall_Anomaly = 1 | evidence).
        """

        self._check_fitted()

        clean_evidence = {
            key: int(bool(value))
            for key, value in evidence.items()
        }

        result = self.inference.query(
            variables=["Overall_Anomaly"],
            evidence=clean_evidence,
            show_progress=False,
        )

        return float(
            result.values[1]
        )

    # --------------------------------------------------
    # DataFrame prediction
    # --------------------------------------------------

    def predict_dataframe(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate Bayesian anomaly probability
        for every row.

        Required columns:
            ML_Anomaly
            Rule_Anomaly
            Behavior_Anomaly
            Cluster_Anomaly
            Data_Quality_Issue
            SLA_Risk
        """

        self._check_fitted()

        required_columns = [
            "ML_Anomaly",
            "Rule_Anomaly",
            "Behavior_Anomaly",
            "Cluster_Anomaly",
            "Data_Quality_Issue",
            "SLA_Risk",
        ]

        missing = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing:
            raise ValueError(
                f"Missing Bayesian evidence columns: {missing}"
            )

        probabilities = []

        for _, row in dataframe.iterrows():

            evidence = {
                column: row[column]
                for column in required_columns
            }

            probability = (
                self.predict_probability(
                    evidence
                )
            )

            probabilities.append(
                probability
            )

        result = dataframe.copy()

        result[
            "bayesian_anomaly_probability"
        ] = probabilities

        return result

    # --------------------------------------------------
    # Model information
    # --------------------------------------------------

    def get_model_info(self) -> dict:
        """Return model information."""

        return {
            "model": "Bayesian Network",
            "nodes": [
                "ML_Anomaly",
                "Rule_Anomaly",
                "Behavior_Anomaly",
                "Cluster_Anomaly",
                "Data_Quality_Issue",
                "SLA_Risk",
                "Overall_Anomaly",
            ],
            "is_fitted": self.is_fitted,
        }

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def save(
        self,
        path: str = (
            "models/artifacts/"
            "bayesian_network.joblib"
        ),
    ):
        """Save Bayesian Network."""

        self._check_fitted()

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            self,
            path,
        )

        return path

    # --------------------------------------------------
    # Load
    # --------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str = (
            "models/artifacts/"
            "bayesian_network.joblib"
        ),
    ):
        """Load a saved Bayesian Network."""

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found: {path}"
            )

        network = joblib.load(path)

        if not isinstance(
            network,
            cls,
        ):
            raise TypeError(
                "Loaded object is not "
                "BayesianAnomalyNetwork."
            )

        return network

    # --------------------------------------------------
    # Fitted check
    # --------------------------------------------------

    def _check_fitted(self):
        if not self.is_fitted:
            raise RuntimeError(
                "Bayesian Network has not been built. "
                "Call build() first."
            )