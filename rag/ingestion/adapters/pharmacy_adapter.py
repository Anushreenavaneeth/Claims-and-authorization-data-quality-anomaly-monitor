"""
Pharmacy ML -> RAG Adapter

Supports the new Pharmacy ML output schema.
"""

from typing import Any, Dict, List


class PharmacyAdapter:

    DATASET_TYPE = "pharmacy"

    # =========================================================
    # Public API
    # =========================================================

    def adapt_record(
        self,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not isinstance(
            record,
            dict
        ):
            raise TypeError(
                "Pharmacy record must be a dictionary."
            )

        record_id_data = record.get(
            "record_id",
            {}
        )

        entity = record.get(
            "entity",
            {}
        )

        final_assessment = record.get(
            "final_assessment",
            {}
        )

        bayesian = record.get(
            "bayesian",
            {}
        )

        rule_engine = record.get(
            "rule_engine",
            {}
        )

        ml_evidence = record.get(
            "ml_evidence",
            {}
        )

        context_for_rag = record.get(
            "context_for_rag"
        )

        if not isinstance(
            record_id_data,
            dict
        ):
            record_id_data = {}

        if not isinstance(
            entity,
            dict
        ):
            entity = {}

        if not isinstance(
            final_assessment,
            dict
        ):
            final_assessment = {}

        if not isinstance(
            bayesian,
            dict
        ):
            bayesian = {}

        if not isinstance(
            rule_engine,
            dict
        ):
            rule_engine = {}

        if not isinstance(
            ml_evidence,
            dict
        ):
            ml_evidence = {}

        return {

            "dataset_type":
                self.DATASET_TYPE,

            "record_id":
                self._build_record_id(
                    record_id_data
                ),

            "detection_summary":
                self._build_detection_summary(
                    final_assessment,
                    bayesian,
                    rule_engine,
                    ml_evidence
                ),

            "rule_based_evidence":
                self._build_rule_evidence(
                    rule_engine
                ),

            "ml_based_evidence":
                self._build_ml_evidence(
                    ml_evidence
                ),

            "bayesian_evidence":
                self._build_bayesian_evidence(
                    bayesian
                ),

            "behavioral_evidence":
                self._build_behavioral_evidence(
                    final_assessment,
                    context_for_rag
                ),

            "record_context":
                self._build_context(
                    record_id_data,
                    entity,
                    context_for_rag
                ),

            "source_explanation":
                self._build_source_explanation(
                    context_for_rag
                ),

            "sla": None,

            "raw_ml_record": record
        }

    # =========================================================
    # Multiple Records
    # =========================================================

    def adapt(
        self,
        ml_output: Any
    ) -> Dict[str, Any]:

        if isinstance(
            ml_output,
            dict
        ):

            records = ml_output.get(
                "records",
                []
            )

        elif isinstance(
            ml_output,
            list
        ):

            records = ml_output

        else:

            raise TypeError(
                "Pharmacy ML output must "
                "be a JSON object or list."
            )

        if not isinstance(
            records,
            list
        ):

            raise ValueError(
                "Pharmacy output does not "
                "contain a valid records list."
            )

        adapted_records = []

        for record in records:

            if not isinstance(
                record,
                dict
            ):
                continue

            adapted_records.append(
                self.adapt_record(
                    record
                )
            )

        return {
            "records": adapted_records,
            "record_count": len(
                adapted_records
            )
        }

    # =========================================================
    # Record ID
    # =========================================================

    def _build_record_id(
        self,
        record_id_data: Dict[str, Any]
    ) -> str:

        plan_id = record_id_data.get(
            "plan_id"
        )

        issuer_id = record_id_data.get(
            "issuer_id"
        )

        if plan_id and issuer_id:

            return (
                f"{plan_id}_{issuer_id}"
            )

        if plan_id:

            return str(plan_id)

        if issuer_id:

            return str(issuer_id)

        return "unknown"

    # =========================================================
    # Detection Summary
    # =========================================================

    def _build_detection_summary(
        self,
        final_assessment: Dict[str, Any],
        bayesian: Dict[str, Any],
        rule_engine: Dict[str, Any],
        ml_evidence: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {

            "final_anomaly":
                final_assessment.get(
                    "anomaly"
                ),

            "final_severity":
                final_assessment.get(
                    "severity"
                ),

            "final_risk_score":
                final_assessment.get(
                    "risk_score"
                ),

            "rule_risk_score":
                None,

            "ml_risk_score":
                None,

            "cluster_risk_score":
                None,

            "bayesian_probability":
                bayesian.get(
                    "probability"
                ),

            "bayesian_anomaly":
                bayesian.get(
                    "anomaly"
                ),

            "ml_anomaly_score":
                self._first_value(
                    ml_evidence,
                    [
                        "anomaly_score",
                        "score"
                    ]
                ),

            "rule_anomaly":
                rule_engine.get(
                    "anomaly"
                ),

            "ml_anomaly":
                self._ml_anomaly(
                    ml_evidence
                ),

            "anomaly_type":
                final_assessment.get(
                    "signals"
                )
        }

    # =========================================================
    # Rule Evidence
    # =========================================================

    def _build_rule_evidence(
        self,
        rule_engine: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        if not rule_engine.get(
            "anomaly",
            False
        ):
            return []

        rule_names = str(
            rule_engine.get(
                "rule_name",
                ""
            )
        )

        rules = []

        for rule_name in rule_names.split(
            ";"
        ):

            rule_name = rule_name.strip()

            if not rule_name:
                continue

            rules.append(
                {
                    "rule_name": rule_name,

                    "status": "ANOMALY",

                    "reason":
                        rule_engine.get(
                            "reason"
                        ),

                    "severity":
                        rule_engine.get(
                            "severity"
                        )
                }
            )

        return rules

    # =========================================================
    # ML Evidence
    # =========================================================

    def _build_ml_evidence(
        self,
        ml_evidence: Dict[str, Any]
    ) -> Dict[str, Any]:

        features = ml_evidence.get(
            "features",
            []
        )

        if not isinstance(
            features,
            list
        ):
            features = []

        return {

            "model":
                ml_evidence.get(
                    "model"
                ),

            "is_anomaly":
                self._ml_anomaly(
                    ml_evidence
                ),

            "anomaly_score":
                self._first_value(
                    ml_evidence,
                    [
                        "anomaly_score",
                        "score"
                    ]
                ),

            "prediction":
                ml_evidence.get(
                    "prediction"
                ),

            "contributing_features":
                features,

            "evidence_count":
                ml_evidence.get(
                    "evidence_count",
                    0
                ),

            "severity":
                ml_evidence.get(
                    "severity"
                ),

            "types":
                ml_evidence.get(
                    "types"
                ),

            "details":
                ml_evidence.get(
                    "details"
                ),

            "summary":
                ml_evidence.get(
                    "summary"
                )
        }

    # =========================================================
    # Bayesian
    # =========================================================

    def _build_bayesian_evidence(
        self,
        bayesian: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {

            "anomaly":
                bayesian.get(
                    "anomaly"
                ),

            "score":
                bayesian.get(
                    "score"
                ),

            "probability":
                bayesian.get(
                    "probability"
                ),

            "threshold":
                bayesian.get(
                    "threshold"
                )
        }

    # =========================================================
    # Behavioral Evidence
    # =========================================================

    def _build_behavioral_evidence(
        self,
        final_assessment: Dict[str, Any],
        context_for_rag: Any
    ) -> List[Dict[str, Any]]:

        signals = str(
            final_assessment.get(
                "signals",
                ""
            )
        )

        behavioral = (
            "Behavioral"
            in signals
        )

        if not behavioral:
            return []

        return [
            {
                "type": "behavioral",
                "detected": True,
                "description":
                    context_for_rag
                    or
                    "Behavioral anomaly detected."
            }
        ]

    # =========================================================
    # Context
    # =========================================================

    def _build_context(
        self,
        record_id_data: Dict[str, Any],
        entity: Dict[str, Any],
        context_for_rag: Any
    ) -> Dict[str, Any]:

        context = {}

        for key, value in record_id_data.items():

            if value is not None:

                context[key] = value

        for key, value in entity.items():

            if value is not None:

                context[key] = value

        if context_for_rag:

            context[
                "context_for_rag"
            ] = context_for_rag

        return context

    # =========================================================
    # Source Explanation
    # =========================================================

    def _build_source_explanation(
        self,
        context_for_rag: Any
    ) -> Dict[str, Any]:

        if not context_for_rag:

            return {}

        return {
            "explanation":
                str(
                    context_for_rag
                )
        }

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _first_value(
        data: Dict[str, Any],
        keys: List[str]
    ):

        for key in keys:

            value = data.get(
                key
            )

            if value is not None:

                return value

        return None

    @staticmethod
    def _ml_anomaly(
        ml_evidence: Dict[str, Any]
    ):

        value = ml_evidence.get(
            "anomaly"
        )

        if value is not None:

            return value

        return False