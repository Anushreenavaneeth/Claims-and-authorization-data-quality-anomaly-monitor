# rules/rule_classifier.py

from typing import Dict, List, Any


class RuleClassifier:
    """
    Classifies rule-engine evidence into three categories:

    HARD_ANOMALY
        Strong structural/data-quality violation.

    BEHAVIOR_EVIDENCE
        Unusual numerical or historical behavior.
        This should support anomaly detection but should
        not independently determine the final anomaly.

    CONTEXT
        Informational evidence that provides context but
        should not create an anomaly.
    """

    # ==================================================
    # HARD ANOMALY RULES
    # ==================================================

    HARD_RULES = {
        "negative_value",
        "fills_without_claims",
        "cost_without_claims",
        "ge65_exceeds_total",
    }

    # ==================================================
    # BEHAVIOR EVIDENCE RULES
    # ==================================================

    BEHAVIOR_RULES = {
        "fills_per_claim_medium",
        "fills_per_claim_high",

        "cost_per_claim_medium",
        "cost_per_claim_high",

        "cost_per_beneficiary_medium",
        "cost_per_beneficiary_high",

        "cost_per_day_supply_medium",
        "cost_per_day_supply_high",

        "day_supply_per_claim_medium",
        "day_supply_per_claim_high",

        "claims_per_beneficiary_medium",
        "claims_per_beneficiary_high",

        "drug_cost_change",
        "claim_volume_change",
        "fill_volume_change",
        "days_supply_change",
        "beneficiary_change",
        "cost_per_claim_change",
    }

    # ==================================================
    # DATA QUALITY RULES
    # ==================================================

    DATA_QUALITY_RULES = {
        "missing_critical_value",
        "claims_without_day_supply",
        "claims_without_beneficiaries",
        "zero_cost_positive_claims",
        "zero_beneficiaries_positive_claims",
        "zero_day_supply_positive_claims",
        "zero_fills_positive_claims",
    }

    # ==================================================
    # CONTEXT RULES
    # ==================================================

    CONTEXT_RULES = {
        "suppression_context",
    }

    # ==================================================
    # CLASSIFY ONE RULE
    # ==================================================

    def classify_rule(
        self,
        rule_name: str,
    ) -> str:

        if rule_name in self.HARD_RULES:

            return "HARD_ANOMALY"

        if rule_name in self.BEHAVIOR_RULES:

            return "BEHAVIOR_EVIDENCE"

        if rule_name in self.DATA_QUALITY_RULES:

            return "DATA_QUALITY"

        if rule_name in self.CONTEXT_RULES:

            return "CONTEXT"

        # Unknown rules should not silently become
        # anomalies.
        return "UNKNOWN"

    # ==================================================
    # CLASSIFY ONE REASON
    # ==================================================

    def classify_reason(
        self,
        reason: Dict[str, Any],
    ) -> Dict[str, Any]:

        rule_name = reason.get(
            "rule",
            "unknown",
        )

        category = self.classify_rule(
            rule_name
        )

        classified = reason.copy()

        classified["category"] = category

        return classified

    # ==================================================
    # CLASSIFY MULTIPLE REASONS
    # ==================================================

    def classify_reasons(
        self,
        reasons: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        return [
            self.classify_reason(reason)
            for reason in reasons
        ]

    # ==================================================
    # SUMMARIZE EVIDENCE
    # ==================================================

    def summarize(
        self,
        reasons: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        classified = self.classify_reasons(
            reasons
        )

        hard_anomalies = []
        behavior_evidence = []
        data_quality = []
        context = []
        unknown = []

        for reason in classified:

            category = reason["category"]

            if category == "HARD_ANOMALY":

                hard_anomalies.append(reason)

            elif category == "BEHAVIOR_EVIDENCE":

                behavior_evidence.append(reason)

            elif category == "DATA_QUALITY":

                data_quality.append(reason)

            elif category == "CONTEXT":

                context.append(reason)

            else:

                unknown.append(reason)

        # ----------------------------------------------
        # Hard anomaly
        # ----------------------------------------------

        hard_anomaly = (
            len(hard_anomalies) > 0
        )

        # ----------------------------------------------
        # Behavioral anomaly
        # ----------------------------------------------

        behavior_anomaly = (
            len(behavior_evidence) > 0
        )

        # ----------------------------------------------
        # Data-quality issue
        # ----------------------------------------------

        data_quality_issue = (
            len(data_quality) > 0
        )

        return {
            "hard_anomaly": hard_anomaly,

            "behavior_anomaly":
                behavior_anomaly,

            "data_quality_issue":
                data_quality_issue,

            "context_present":
                len(context) > 0,

            "hard_anomalies":
                hard_anomalies,

            "behavior_evidence":
                behavior_evidence,

            "data_quality_evidence":
                data_quality,

            "context_evidence":
                context,

            "unknown_rules":
                unknown,

            "total_evidence":
                len(classified),
        }

    # ==================================================
    # CLASSIFY COMPLETE RULE RESULT
    # ==================================================

    def classify_result(
        self,
        rule_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        reasons = rule_result.get(
            "reasons",
            [],
        )

        context_reasons = (
            rule_result.get(
                "context_reasons",
                [],
            )
        )

        # Combine only for classification.
        all_reasons = (
            reasons + context_reasons
        )

        summary = self.summarize(
            all_reasons
        )

        return {
            "original_rule_anomaly":
                rule_result.get(
                    "rule_anomaly",
                    False,
                ),

            "original_severity":
                rule_result.get(
                    "severity",
                    "NONE",
                ),

            **summary,
        }