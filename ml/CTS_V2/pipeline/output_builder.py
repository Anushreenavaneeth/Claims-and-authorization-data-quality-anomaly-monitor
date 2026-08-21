# pipeline/output_builder.py

from typing import Dict, List, Any


class OutputBuilder:
    """
    Builds the final anomaly JSON output.

    Internal pipeline results are converted into the
    compact output contract required by the project.
    """

    def __init__(
        self,
        anomaly_threshold: float = 0.50,
    ):
        self.anomaly_threshold = anomaly_threshold

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
    # CLEAN RULE CAUSES
    # ==================================================

    @staticmethod
    def _clean_rule_causes(
        causes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        cleaned = []

        for cause in causes or []:

            cleaned.append(
                {
                    "cause": cause.get(
                        "cause",
                        "unknown",
                    ),

                    "description": cause.get(
                        "description",
                        "",
                    ),
                }
            )

        return cleaned

    # ==================================================
    # CLEAN BAYESIAN CAUSES
    # ==================================================

    @staticmethod
    def _clean_bayesian_causes(
        causes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        cleaned = []

        for cause in causes or []:

            cleaned.append(
                {
                    "cause": cause.get(
                        "cause",
                        "unknown",
                    ),

                    "probability_given_anomaly":
                        round(
                            OutputBuilder._safe_float(
                                cause.get(
                                    "probability_given_anomaly",
                                    0.0,
                                )
                            ),
                            4,
                        ),

                    "baseline_probability":
                        round(
                            OutputBuilder._safe_float(
                                cause.get(
                                    "baseline_probability",
                                    0.0,
                                )
                            ),
                            4,
                        ),

                    "bayesian_lift":
                        round(
                            OutputBuilder._safe_float(
                                cause.get(
                                    "bayesian_lift",
                                    0.0,
                                )
                            ),
                            4,
                        ),
                }
            )

        return cleaned

    # ==================================================
    # BUILD ONE RECORD
    # ==================================================

    def build_record(
        self,
        record_id: Any,
        evidence: Dict[str, Any],
        rule_root_causes: List[Dict[str, Any]],
        bayesian_root_causes: List[Dict[str, Any]],
        sla_result: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        sla_result = sla_result or {}

        # ----------------------------------------------
        # Detection sources
        # ----------------------------------------------

        rule_based = self._safe_bool(
            evidence.get(
                "rule_based",
                {}
            ).get(
                "anomaly",
                False,
            )
        )

        isolation_forest = self._safe_bool(
            evidence.get(
                "isolation_forest",
                {}
            ).get(
                "anomaly",
                False,
            )
        )

        clustering = self._safe_bool(
            evidence.get(
                "clustering",
                {}
            ).get(
                "anomaly",
                False,
            )
        )

        behavioral = self._safe_bool(
            evidence.get(
                "behavioral",
                {}
            ).get(
                "anomaly",
                False,
            )
        )

        # ----------------------------------------------
        # Bayesian evidence
        # ----------------------------------------------

        bayesian = (
            len(
                bayesian_root_causes or []
            )
            > 0
        )

        # ----------------------------------------------
        # ML anomaly score
        # ----------------------------------------------

        ml_anomaly_score = self._safe_float(
            evidence.get(
                "isolation_forest",
                {}
            ).get(
                "anomaly_score",
                0.0,
            )
        )

        # ----------------------------------------------
        # Fusion
        # ----------------------------------------------

        fusion = evidence.get(
            "fusion",
            {}
        )

        fusion_score = self._safe_float(
            fusion.get(
                "fusion_score",
                0.0,
            )
        )

        multi_source = self._safe_bool(
            fusion.get(
                "multi_source_anomaly",
                False,
            )
        )

        # ----------------------------------------------
        # SLA
        # ----------------------------------------------

        sla_risk = self._safe_bool(
            sla_result.get(
                "sla_risk",
                False,
            )
        )

        # ----------------------------------------------
        # Final anomaly decision
        # ----------------------------------------------

        anomaly_detected = (
            rule_based
            or isolation_forest
            or clustering
            or behavioral
            or bayesian
        )

        # SLA alone should not create an anomaly.
        #
        # It is supporting pipeline-risk information.

        if not anomaly_detected:

            anomaly_detected = (
                multi_source
                or fusion_score
                >= self.anomaly_threshold
            )

        # ----------------------------------------------
        # Clean causes
        # ----------------------------------------------

        cleaned_rule_causes = (
            self._clean_rule_causes(
                rule_root_causes
            )
        )

        cleaned_bayesian_causes = (
            self._clean_bayesian_causes(
                bayesian_root_causes
            )
        )

        # ----------------------------------------------
        # RAG context
        # ----------------------------------------------

        context_parts = []

        for cause in cleaned_rule_causes:

            description = cause.get(
                "description",
                "",
            )

            if description:
                context_parts.append(
                    description
                )

        for cause in cleaned_bayesian_causes:

            context_parts.append(
                "Bayesian evidence indicates "
                f"{cause['cause']} with probability "
                f"{cause['probability_given_anomaly']:.4f}."
            )

        if sla_risk:

            breach_probability = (
                self._safe_float(
                    sla_result.get(
                        "breach_probability",
                        0.0,
                    )
                )
            )

            context_parts.append(
                "SLA processing risk is elevated "
                f"with estimated breach probability "
                f"{breach_probability:.4f}."
            )

        context_for_rag = " ".join(
            context_parts
        )

        # ----------------------------------------------
        # Final output
        # ----------------------------------------------

        return {

            "record_id":
                record_id,

            "anomaly_detected":
                anomaly_detected,

            "detection_sources": {

                "rule_based":
                    rule_based,

                "isolation_forest":
                    isolation_forest,

                "clustering":
                    clustering,

                "behavioral":
                    behavioral,

                "bayesian":
                    bayesian,
            },

            "ml_anomaly_score":
                round(
                    ml_anomaly_score,
                    6,
                ),

            "rule_based_root_causes":
                cleaned_rule_causes,

            "bayesian_probable_root_causes":
                cleaned_bayesian_causes,

            "context_for_rag":
                context_for_rag,
        }

    # ==================================================
    # BUILD MULTIPLE RECORDS
    # ==================================================

    def build_batch(
        self,
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        return records