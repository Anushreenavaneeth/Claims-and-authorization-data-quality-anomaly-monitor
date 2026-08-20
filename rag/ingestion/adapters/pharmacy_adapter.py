"""
Pharmacy ML → RAG Adapter

Converts Pharmacy ML anomaly output into the
common RAG-compatible anomaly structure.

Supported Pharmacy input:

{
    "dataset_type": "pharmacy",
    "record_id": "...",
    "detection_summary": {...},
    "rule_based_evidence": {...},
    "ml_based_evidence": {...},
    "behavior_based_evidence": {...},
    "record_context": {...},
    "sla": {...},
    "explanation": {...}
}
"""

from typing import Dict, Any, List


class PharmacyAdapter:
    """
    Converts Pharmacy ML anomaly records into the
    normalized structure expected by the RAG pipeline.
    """

    # =====================================================
    # Public: Adapt One Record
    # =====================================================

    def adapt_record(
        self,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not isinstance(
            record,
            dict
        ):
            raise TypeError(
                "Pharmacy anomaly must be a dictionary."
            )

        detection = record.get(
            "detection_summary",
            {}
        )

        rule_evidence = record.get(
            "rule_based_evidence",
            {}
        )

        ml_evidence = record.get(
            "ml_based_evidence",
            {}
        )

        behavior_evidence = record.get(
            "behavior_based_evidence",
            {}
        )

        record_context = record.get(
            "record_context",
            {}
        )

        sla = record.get(
            "sla"
        )

        explanation = record.get(
            "explanation",
            {}
        )

        # =================================================
        # Detection Summary
        # =================================================

        normalized_detection = {
            "final_anomaly":
                detection.get(
                    "final_anomaly"
                ),

            "final_severity":
                detection.get(
                    "final_severity"
                ),

            "final_risk_score":
                detection.get(
                    "final_risk_score"
                ),

            "rule_risk_score":
                detection.get(
                    "rule_risk_score"
                ),

            "ml_risk_score":
                detection.get(
                    "ml_risk_score"
                ),

            "cluster_risk_score":
                detection.get(
                    "cluster_risk_score"
                ),

            "ml_anomaly_score":
                ml_evidence.get(
                    "anomaly_score"
                ),

            "rule_anomaly":
                detection.get(
                    "rule_anomaly"
                ),

            "ml_anomaly":
                detection.get(
                    "ml_anomaly"
                ),

            "behavior_anomaly":
                detection.get(
                    "behavior_anomaly"
                )
        }

        # =================================================
        # Rule-Based Evidence
        # =================================================

        normalized_rule_evidence = []

        if isinstance(
            rule_evidence,
            dict
        ):

            rule_anomaly = (
                rule_evidence.get(
                    "rule_anomaly"
                )
            )

            severity = (
                rule_evidence.get(
                    "severity"
                )
            )

            reason = (
                rule_evidence.get(
                    "reason"
                )
            )

            if (
                rule_anomaly
                or reason
            ):

                normalized_rule_evidence.append(
                    {
                        "rule_name": (
                            reason
                            if reason
                            else "pharmacy_rule_anomaly"
                        ),

                        "status": (
                            "violated"
                            if rule_anomaly
                            else "detected"
                        ),

                        "severity": severity,

                        "reason": reason
                    }
                )

        elif isinstance(
            rule_evidence,
            list
        ):

            for rule in rule_evidence:

                if not isinstance(
                    rule,
                    dict
                ):
                    continue

                normalized_rule_evidence.append(
                    {
                        "rule_name":
                            rule.get(
                                "rule_name",
                                rule.get(
                                    "rule",
                                    "unknown"
                                )
                            ),

                        "status":
                            rule.get(
                                "status",
                                "detected"
                            )
                    }
                )

        # =================================================
        # ML-Based Evidence
        # =================================================

        normalized_ml_evidence = {
            "model":
                ml_evidence.get(
                    "model",
                    "Isolation Forest"
                ),

            "is_anomaly":
                ml_evidence.get(
                    "is_anomaly"
                ),

            "anomaly_score":
                ml_evidence.get(
                    "anomaly_score"
                ),

            "contributing_features":
                ml_evidence.get(
                    "contributing_features",
                    []
                )
        }

        # =================================================
        # Behavior-Based Evidence
        # =================================================

        normalized_behavior_evidence = {}

        if isinstance(
            behavior_evidence,
            dict
        ):

            behavior_fields = [
                "claim_volume_change",
                "fill_volume_change",
                "days_supply_change",
                "drug_cost_change",
                "beneficiary_change",
                "cost_per_claim_change"
            ]

            for field in behavior_fields:

                if field in behavior_evidence:

                    normalized_behavior_evidence[
                        field
                    ] = behavior_evidence.get(
                        field
                    )

        # =================================================
        # Record Context
        # =================================================

        normalized_context = {}

        if isinstance(
            record_context,
            dict
        ):

            normalized_context = dict(
                record_context
            )

        # =================================================
        # SLA
        # =================================================

        normalized_sla = sla

        # =================================================
        # Final RAG Record
        # =================================================

        return {
            "dataset_type":
                record.get(
                    "dataset_type",
                    "pharmacy"
                ),

            "record_id":
                str(
                    record.get(
                        "record_id",
                        "unknown"
                    )
                ),

            "detection_summary":
                normalized_detection,

            "rule_based_evidence":
                normalized_rule_evidence,

            "ml_based_evidence":
                normalized_ml_evidence,

            "behavior_based_evidence":
                normalized_behavior_evidence,

            "record_context":
                normalized_context,

            "sla":
                normalized_sla,

            "source_explanation":
                explanation
        }

    # =====================================================
    # Public: Adapt Multiple Records
    # =====================================================

    def adapt(
        self,
        records: Any
    ) -> List[Dict[str, Any]]:
        """
        Adapt a list of Pharmacy anomaly records.
        """

        if not isinstance(
            records,
            list
        ):

            raise TypeError(
                "Pharmacy records must be a list."
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

        return adapted_records