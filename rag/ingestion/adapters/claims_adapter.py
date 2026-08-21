"""
Claims ML Output → RAG Input Adapter

Converts the Claims ML model output into the
common RAG-compatible anomaly structure.

Claims ML format:

{
    "record": {...},
    "anomaly": {...},
    "detection": {...},
    "explanation": {
        "explanation": "...",
        "likely_cause": "...",
        "recommended_fix": "..."
    }
}

RAG format:

{
    "dataset_type": "claims",
    "record_id": "...",
    "detection_summary": {...},
    "rule_based_evidence": [...],
    "ml_based_evidence": {...},
    "record_context": {...},
    "sla": null,
    "source_explanation": {...}
}
"""

from typing import Dict, Any, List


class ClaimsAdapter:
    """
    Adapter for converting Claims ML anomalies
    into the common RAG input structure.
    """

    # =====================================================
    # Public API
    # =====================================================

    def adapt_record(
        self,
        anomaly: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert one Claims ML anomaly into
        the common RAG-compatible structure.
        """

        if not isinstance(
            anomaly,
            dict
        ):
            raise TypeError(
                "Claims anomaly must be a dictionary."
            )

        # -------------------------------------------------
        # Original Claims sections
        # -------------------------------------------------

        record = anomaly.get(
            "record",
            {}
        )

        anomaly_info = anomaly.get(
            "anomaly",
            {}
        )

        detection = anomaly.get(
            "detection",
            {}
        )

        explanation = anomaly.get(
            "explanation",
            {}
        )

        if not isinstance(
            record,
            dict
        ):
            record = {}

        if not isinstance(
            anomaly_info,
            dict
        ):
            anomaly_info = {}

        if not isinstance(
            detection,
            dict
        ):
            detection = {}

        if not isinstance(
            explanation,
            dict
        ):
            explanation = {}

        # -------------------------------------------------
        # Detection sections
        # -------------------------------------------------

        rule_based = detection.get(
            "rule_based",
            {}
        )

        machine_learning = detection.get(
            "machine_learning",
            {}
        )

        if not isinstance(
            rule_based,
            dict
        ):
            rule_based = {}

        if not isinstance(
            machine_learning,
            dict
        ):
            machine_learning = {}

        # =================================================
        # Record ID
        # =================================================

        record_id = (
            record.get(
                "plan_id"
            )
            or record.get(
                "record_id"
            )
            or anomaly.get(
                "record_id"
            )
        )

        if record_id is None:

            record_id = "unknown"

        # =================================================
        # Anomaly Information
        # =================================================

        final_anomaly = anomaly_info.get(
            "final_anomaly",
            machine_learning.get(
                "detected",
                False
            )
        )

        final_severity = anomaly_info.get(
            "severity"
        )

        anomaly_type = anomaly_info.get(
            "anomaly_type"
        )

        # =================================================
        # Rule-Based Evidence
        # =================================================

        rule_anomaly = rule_based.get(
            "detected",
            False
        )

        rule_name = rule_based.get(
            "rule_name"
        )

        rule_reason = rule_based.get(
            "rule_reason"
        )

        rule_severity = rule_based.get(
            "severity"
        )

        rule_based_evidence = []

        if rule_anomaly:

            rule_entry = {
                "rule_name": (
                    rule_name
                    or "unknown_rule"
                ),
                "status": "violated"
            }

            if rule_reason:

                rule_entry[
                    "reason"
                ] = rule_reason

            if rule_severity is not None:

                rule_entry[
                    "severity"
                ] = rule_severity

            rule_based_evidence.append(
                rule_entry
            )

        # =================================================
        # ML Evidence
        # =================================================

        ml_anomaly = machine_learning.get(
            "detected",
            False
        )

        ml_prediction = machine_learning.get(
            "prediction"
        )

        ml_anomaly_score = machine_learning.get(
            "anomaly_score"
        )

        # -------------------------------------------------
        # Contributing Features
        #
        # Claims model currently provides the important
        # feature evidence inside the explanation text.
        #
        # We DO NOT invent structured feature values.
        # -------------------------------------------------

        contributing_features = []

        ml_based_evidence = {
            "model": "Isolation Forest",

            "is_anomaly": ml_anomaly,

            "anomaly_score": (
                ml_anomaly_score
            ),

            "contributing_features": (
                contributing_features
            )
        }

        if ml_prediction is not None:

            ml_based_evidence[
                "prediction"
            ] = ml_prediction

        # =================================================
        # Record Context
        # =================================================

        record_context = {}

        # Preserve all original Claims record fields.
        #
        # This is important because the Claims schema
        # can contain domain-specific fields that may
        # be useful to RAG/XAI later.

        for key, value in record.items():

            record_context[
                key
            ] = value

        # =================================================
        # Source Explanation
        # =================================================

        source_explanation = {
            "explanation": explanation.get(
                "explanation"
            ),

            "likely_cause": explanation.get(
                "likely_cause"
            ),

            "recommended_fix": explanation.get(
                "recommended_fix"
            )
        }

        # Remove completely missing values.

        source_explanation = {
            key: value
            for key, value
            in source_explanation.items()
            if value is not None
        }

        # =================================================
        # Detection Summary
        # =================================================

        detection_summary = {
            "final_anomaly": final_anomaly,

            "final_severity": final_severity,

            # Claims model does not currently provide
            # a combined risk score.
            "final_risk_score": None,

            "rule_risk_score": None,

            "ml_risk_score": None,

            "cluster_risk_score": None,

            "ml_anomaly_score": ml_anomaly_score,

            "rule_anomaly": rule_anomaly,

            "ml_anomaly": ml_anomaly,

            "anomaly_type": anomaly_type
        }

        # =================================================
        # Final RAG-Compatible Record
        # =================================================

        adapted_record = {
            "dataset_type": "claims",

            "record_id": record_id,

            "detection_summary": (
                detection_summary
            ),

            "rule_based_evidence": (
                rule_based_evidence
            ),

            "ml_based_evidence": (
                ml_based_evidence
            ),

            "record_context": (
                record_context
            ),

            "sla": None,

            # -------------------------------------------------
            # Preserve the original Claims ML explanation.
            # This is important for XAI.
            # -------------------------------------------------

            "source_explanation": (
                source_explanation
            )
        }

        return adapted_record

    # =====================================================
    # Adapt Multiple Records
    # =====================================================

    def adapt(
        self,
        claims_output: Any
    ) -> List[Dict[str, Any]]:
        """
        Adapt multiple Claims anomalies.

        Supports the original Claims ML structure:

        {
            "metadata": {...},
            "dataset_summary": {...},
            "anomalies": [...]
        }

        Also supports a direct list of anomalies.
        """

        # -------------------------------------------------
        # Claims output object
        # -------------------------------------------------

        if isinstance(
            claims_output,
            dict
        ):

            anomalies = claims_output.get(
                "anomalies",
                []
            )

            if not isinstance(
                anomalies,
                list
            ):
                raise ValueError(
                    "Claims output contains an "
                    "invalid 'anomalies' field."
                )

        # -------------------------------------------------
        # Direct list
        # -------------------------------------------------

        elif isinstance(
            claims_output,
            list
        ):

            anomalies = claims_output

        else:

            raise TypeError(
                "Claims ML output must be "
                "a dictionary or list."
            )

        # -------------------------------------------------
        # Adapt records
        # -------------------------------------------------

        adapted_records = []

        for anomaly in anomalies:

            if not isinstance(
                anomaly,
                dict
            ):
                continue

            adapted_records.append(
                self.adapt_record(
                    anomaly
                )
            )

        return adapted_records

    # =====================================================
    # Adapt Complete Output
    # =====================================================

    def adapt_output(
        self,
        claims_output: Any
    ) -> Dict[str, Any]:
        """
        Adapt complete Claims ML output and return
        a normalized RAG ingestion-style object.
        """

        records = self.adapt(
            claims_output
        )

        return {
            "records": records,

            "record_count": len(
                records
            )
        }