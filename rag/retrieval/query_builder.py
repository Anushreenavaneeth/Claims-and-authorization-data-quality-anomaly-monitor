"""
Universal Query Builder

Creates retrieval queries from the normalized RAG record.

Supported datasets:
- Claims
- Authorization
- Pharmacy
"""

from typing import Any, Dict, List


class QueryBuilder:

    # =====================================================
    # Build One Query
    # =====================================================

    def build_query(
        self,
        anomaly: Dict[str, Any]
    ) -> str:

        if not isinstance(anomaly, dict):
            return ""

        query_parts = []

        # -------------------------------------------------
        # Dataset
        # -------------------------------------------------

        dataset = anomaly.get(
            "dataset_type",
            "healthcare"
        )

        query_parts.append(
            f"Healthcare data quality anomaly in {dataset} dataset."
        )

        # -------------------------------------------------
        # Record ID
        # -------------------------------------------------

        record_id = anomaly.get(
            "record_id"
        )

        if record_id:
            query_parts.append(
                f"Record ID: {record_id}."
            )

        # -------------------------------------------------
        # Detection Summary
        # -------------------------------------------------

        detection = anomaly.get(
            "detection_summary",
            {}
        )

        if isinstance(detection, dict):

            if detection.get("final_anomaly") is not None:
                query_parts.append(
                    f"Final anomaly: {detection.get('final_anomaly')}."
                )

            if detection.get("final_severity"):
                query_parts.append(
                    f"Severity: {detection.get('final_severity')}."
                )

            if detection.get("final_risk_score") is not None:
                query_parts.append(
                    f"Risk score: {detection.get('final_risk_score')}."
                )

            if detection.get("anomaly_type"):
                query_parts.append(
                    f"Signal types: {detection.get('anomaly_type')}."
                )

        # -------------------------------------------------
        # Rule Evidence
        # -------------------------------------------------

        rules = anomaly.get(
            "rule_based_evidence",
            []
        )

        if isinstance(rules, list) and rules:

            rule_names = []
            rule_reasons = []

            for rule in rules:

                if not isinstance(rule, dict):
                    continue

                name = rule.get("rule_name")
                reason = rule.get("reason")

                if name:
                    rule_names.append(name)

                if reason:
                    rule_reasons.append(reason)

            if rule_names:
                query_parts.append(
                    "Rule violations: "
                    + ", ".join(rule_names)
                    + "."
                )

            if rule_reasons:
                query_parts.append(
                    "Rule reasons: "
                    + "; ".join(rule_reasons)
                    + "."
                )

        # -------------------------------------------------
        # ML Evidence
        # -------------------------------------------------

        ml = anomaly.get(
            "ml_based_evidence",
            {}
        )

        if isinstance(ml, dict):

            model = ml.get("model")

            if model:
                query_parts.append(
                    f"ML model: {model}."
                )

            if ml.get("is_anomaly") is not None:
                query_parts.append(
                    f"ML anomaly: {ml.get('is_anomaly')}."
                )

            score = ml.get("anomaly_score")

            if score is not None:
                query_parts.append(
                    f"ML anomaly score: {score}."
                )

            prediction = ml.get("prediction")

            if prediction is not None:
                query_parts.append(
                    f"ML prediction: {prediction}."
                )

            features = ml.get(
                "contributing_features",
                []
            )

            if isinstance(features, list) and features:

                query_parts.append(
                    "Contributing features: "
                    + ", ".join(map(str, features))
                    + "."
                )

            summary = ml.get("summary")

            if summary:
                query_parts.append(
                    f"ML summary: {summary}."
                )

        # -------------------------------------------------
        # Bayesian Evidence
        # -------------------------------------------------

        bayesian = anomaly.get(
            "bayesian_evidence",
            {}
        )

        if isinstance(bayesian, dict):

            if bayesian.get("anomaly") is not None:
                query_parts.append(
                    f"Bayesian anomaly: {bayesian.get('anomaly')}."
                )

            probability = bayesian.get("probability")

            if probability is not None:
                query_parts.append(
                    f"Bayesian probability: {probability}."
                )

            score = bayesian.get("score")

            if score is not None:
                query_parts.append(
                    f"Bayesian score: {score}."
                )

        # -------------------------------------------------
        # Behavioral Evidence
        # -------------------------------------------------

        behavioral = anomaly.get(
            "behavioral_evidence",
            []
        )

        if isinstance(behavioral, list) and behavioral:

            query_parts.append(
                "Behavioral anomaly detected."
            )

            descriptions = []

            for item in behavioral:

                if not isinstance(item, dict):
                    continue

                desc = item.get("description")

                if desc:
                    descriptions.append(desc)

            if descriptions:
                query_parts.append(
                    "Behavioral evidence: "
                    + "; ".join(descriptions)
                    + "."
                )

        # -------------------------------------------------
        # Record Context
        # -------------------------------------------------

        context = anomaly.get(
            "record_context",
            {}
        )

        if isinstance(context, dict):

            context_parts = []

            important_fields = [
                "plan_id",
                "authorization_id",
                "reference_number",
                "issuer_name",
                "state",
                "plan_type",
                "metal_level",
                "patient_id",
                "provider_id",
                "payer_id",
                "authorization_type",
                "service_code",
                "service_description"
            ]

            for field in important_fields:

                value = context.get(field)

                if value in [None, "", []]:
                    continue

                context_parts.append(
                    f"{field.replace('_',' ')}: {value}"
                )

            if context_parts:
                query_parts.append(
                    "Record context: "
                    + "; ".join(context_parts)
                    + "."
                )

        # -------------------------------------------------
        # Source Explanation
        # -------------------------------------------------

        explanation = anomaly.get(
            "source_explanation",
            {}
        )

        if isinstance(explanation, dict):

            text = explanation.get("explanation")

            if text:
                query_parts.append(
                    f"Detected pattern explanation: {text}"
                )

            cause = explanation.get("likely_cause")

            if cause:
                query_parts.append(
                    f"Likely cause: {cause}"
                )

            fix = explanation.get("recommended_fix")

            if fix:
                query_parts.append(
                    f"Recommended fix: {fix}"
                )

        # -------------------------------------------------
        # SLA
        # -------------------------------------------------

        sla = anomaly.get("sla")

        if sla:
            query_parts.append(
                f"SLA status: {sla}."
            )

        # -------------------------------------------------
        # Dataset-specific retrieval intent
        # -------------------------------------------------

        if dataset == "claims":

            query_parts.append(
                "Find healthcare claims data quality validation rules, missing data patterns, suppressed values, root causes, and remediation procedures."
            )

        elif dataset == "authorization":

            query_parts.append(
                "Find healthcare authorization validation rules, prior authorization anomalies, provider and payer data quality issues, and remediation procedures."
            )

        elif dataset == "pharmacy":

            query_parts.append(
                "Find pharmacy claims validation rules, cost-per-claim anomalies, behavioral pattern changes, Bayesian anomaly guidance, and remediation procedures."
            )

        # -------------------------------------------------
        # Final Query
        # -------------------------------------------------

        return " ".join(query_parts).strip()

    # =====================================================
    # Multiple Queries
    # =====================================================

    def build_queries(
        self,
        rag_input: Any
    ) -> List[str]:

        queries = []

        if isinstance(rag_input, dict):

            if (
                "records" in rag_input
                and isinstance(rag_input["records"], list)
            ):

                rag_input = rag_input["records"]

            else:

                query = self.build_query(rag_input)

                if query:
                    queries.append(query)

                return queries

        if isinstance(rag_input, list):

            for record in rag_input:

                if not isinstance(record, dict):
                    continue

                query = self.build_query(record)

                if query:
                    queries.append(query)

            return queries

        raise TypeError(
            "RAG input must be a list or dictionary."
        )