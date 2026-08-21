"""
Build semantic retrieval queries from normalized ML anomaly records.

Supports:
- Authorization
- Claims
- Pharmacy
- Generic future datasets

Expected common structure:

{
    "dataset_type": "...",
    "record_id": "...",
    "detection_summary": {...},
    "rule_based_evidence": [...],
    "ml_based_evidence": {...},
    "record_context": {...},
    "sla": ...
}
"""

from typing import Any, Dict, List


class QueryBuilder:
    """
    Converts normalized ML anomaly records into
    evidence-rich semantic retrieval queries.
    """

    # =====================================================
    # Build One Query
    # =====================================================

    def build_query(
        self,
        anomaly: Dict[str, Any]
    ) -> str:

        if not isinstance(
            anomaly,
            dict
        ):
            return ""

        query_parts = []

        # =================================================
        # Dataset
        # =================================================

        dataset_type = anomaly.get(
            "dataset_type",
            "unknown"
        )

        record_id = anomaly.get(
            "record_id",
            "unknown"
        )

        query_parts.append(
            f"Healthcare data quality anomaly "
            f"in {dataset_type} dataset."
        )

        query_parts.append(
            f"Record ID: {record_id}."
        )

        # =================================================
        # Detection Summary
        # =================================================

        detection = anomaly.get(
            "detection_summary",
            {}
        )

        if not isinstance(
            detection,
            dict
        ):
            detection = {}

        final_anomaly = detection.get(
            "final_anomaly"
        )

        final_severity = detection.get(
            "final_severity"
        )

        final_risk_score = detection.get(
            "final_risk_score"
        )

        ml_anomaly_score = detection.get(
            "ml_anomaly_score"
        )

        anomaly_type = detection.get(
            "anomaly_type"
        )

        if final_anomaly is not None:

            query_parts.append(
                f"Final anomaly: "
                f"{final_anomaly}."
            )

        if final_severity:

            query_parts.append(
                f"Severity: "
                f"{final_severity}."
            )

        if final_risk_score is not None:

            query_parts.append(
                f"Final risk score: "
                f"{final_risk_score}."
            )

        if ml_anomaly_score is not None:

            query_parts.append(
                f"ML anomaly score: "
                f"{ml_anomaly_score}."
            )

        if anomaly_type:

            query_parts.append(
                f"Anomaly type: "
                f"{anomaly_type}."
            )

        # =================================================
        # Rule-Based Evidence
        # =================================================

        rule_evidence = anomaly.get(
            "rule_based_evidence",
            []
        )

        if not isinstance(
            rule_evidence,
            list
        ):
            rule_evidence = []

        rule_parts = []

        for rule in rule_evidence:

            if not isinstance(
                rule,
                dict
            ):
                continue

            rule_name = rule.get(
                "rule_name"
            )

            status = rule.get(
                "status"
            )

            reason = rule.get(
                "reason"
            )

            if not rule_name:
                continue

            rule_text = str(
                rule_name
            )

            if status:

                rule_text += (
                    f" ({status})"
                )

            if reason:

                rule_text += (
                    f": {reason}"
                )

            rule_parts.append(
                rule_text
            )

        if rule_parts:

            query_parts.append(
                "Rule-based anomalies: "
                + "; ".join(
                    rule_parts
                )
                + "."
            )

        # =================================================
        # ML-Based Evidence
        # =================================================

        ml_evidence = anomaly.get(
            "ml_based_evidence"
        )

        if not isinstance(
            ml_evidence,
            dict
        ):
            ml_evidence = {}

        model = ml_evidence.get(
            "model"
        )

        is_anomaly = ml_evidence.get(
            "is_anomaly"
        )

        anomaly_score = ml_evidence.get(
            "anomaly_score"
        )

        prediction = ml_evidence.get(
            "prediction"
        )

        if model:

            query_parts.append(
                f"ML model: "
                f"{model}."
            )

        if is_anomaly is not None:

            query_parts.append(
                f"ML anomaly: "
                f"{is_anomaly}."
            )

        if anomaly_score is not None:

            query_parts.append(
                f"ML anomaly score: "
                f"{anomaly_score}."
            )

        if prediction is not None:

            query_parts.append(
                f"ML prediction: "
                f"{prediction}."
            )

        # =================================================
        # Contributing Features
        # =================================================

        features = ml_evidence.get(
            "contributing_features",
            []
        )

        if not isinstance(
            features,
            list
        ):
            features = []

        for feature in features:

            if not isinstance(
                feature,
                dict
            ):
                continue

            feature_name = feature.get(
                "feature"
            )

            if not feature_name:
                continue

            observed_value = feature.get(
                "observed_value"
            )

            expected_lower = feature.get(
                "expected_lower"
            )

            expected_upper = feature.get(
                "expected_upper"
            )

            direction = feature.get(
                "direction"
            )

            deviation_score = feature.get(
                "deviation_score"
            )

            feature_parts = [
                f"ML feature "
                f"{feature_name}"
            ]

            if observed_value is not None:

                feature_parts.append(
                    f"observed value "
                    f"{observed_value}"
                )

            if expected_lower is not None:

                feature_parts.append(
                    f"expected lower "
                    f"{expected_lower}"
                )

            if expected_upper is not None:

                feature_parts.append(
                    f"expected upper "
                    f"{expected_upper}"
                )

            if direction:

                feature_parts.append(
                    f"direction "
                    f"{direction}"
                )

            if deviation_score is not None:

                feature_parts.append(
                    f"deviation score "
                    f"{deviation_score}"
                )

            query_parts.append(
                ", ".join(
                    feature_parts
                )
                + "."
            )

        # =================================================
        # Record Context
        #
        # Generic:
        # Do NOT hard-code authorization fields.
        # Every available Claims/Authorization/
        # Pharmacy context field can contribute
        # to semantic retrieval.
        # =================================================

        record_context = anomaly.get(
            "record_context",
            {}
        )

        if not isinstance(
            record_context,
            dict
        ):
            record_context = {}

        context_parts = []

        for field, value in record_context.items():

            if value is None:
                continue

            if isinstance(
                value,
                (dict, list)
            ):
                continue

            field_name = (
                str(field)
                .replace("_", " ")
            )

            context_parts.append(
                f"{field_name}: "
                f"{value}"
            )

        if context_parts:

            query_parts.append(
                "Record context: "
                + "; ".join(
                    context_parts
                )
                + "."
            )

        # =================================================
        # Source Explanation
        #
        # Claims adapter preserves:
        # explanation
        # likely_cause
        # recommended_fix
        #
        # These are useful retrieval signals.
        # =================================================

        source_explanation = anomaly.get(
            "source_explanation",
            {}
        )

        if not isinstance(
            source_explanation,
            dict
        ):
            source_explanation = {}

        explanation = source_explanation.get(
            "explanation"
        )

        likely_cause = source_explanation.get(
            "likely_cause"
        )

        recommended_fix = source_explanation.get(
            "recommended_fix"
        )

        if explanation:

            query_parts.append(
                f"Detected pattern explanation: "
                f"{explanation}"
            )

        if likely_cause:

            query_parts.append(
                f"Likely cause: "
                f"{likely_cause}"
            )

        if recommended_fix:

            query_parts.append(
                f"Recommended fix: "
                f"{recommended_fix}"
            )

        # =================================================
        # SLA
        # =================================================

        sla = anomaly.get(
            "sla"
        )

        if sla:

            query_parts.append(
                f"SLA: {sla}."
            )

        # =================================================
        # Final Query
        # =================================================

        return " ".join(
            query_parts
        ).strip()

    # =====================================================
    # Build Multiple Queries
    # =====================================================

    def build_queries(
        self,
        rag_input: Any
    ) -> List[str]:

        queries = []

        # -------------------------------------------------
        # Complete normalized ingestion result
        # -------------------------------------------------

        if isinstance(
            rag_input,
            dict
        ):

            if (
                "records" in rag_input
                and isinstance(
                    rag_input["records"],
                    list
                )
            ):

                rag_input = (
                    rag_input["records"]
                )

            else:

                query = self.build_query(
                    rag_input
                )

                if query:

                    queries.append(
                        query
                    )

                return queries

        # -------------------------------------------------
        # List of records
        # -------------------------------------------------

        if isinstance(
            rag_input,
            list
        ):

            for anomaly in rag_input:

                if not isinstance(
                    anomaly,
                    dict
                ):
                    continue

                query = self.build_query(
                    anomaly
                )

                if query:

                    queries.append(
                        query
                    )

            return queries

        # -------------------------------------------------
        # Invalid input
        # -------------------------------------------------

        raise TypeError(
            "RAG input must be either "
            "a JSON list or JSON object."
        )