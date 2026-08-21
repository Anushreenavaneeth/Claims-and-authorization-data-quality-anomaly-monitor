# pipeline/root_cause_engine.py

from typing import Dict, List, Any


class RootCauseEngine:
    """
    Converts internal rule-engine evidence into
    human-readable pharmacy anomaly root causes.

    This component does not decide whether a record
    is anomalous. It explains the evidence that has
    already been detected.
    """

    # ==================================================
    # RULE → ROOT CAUSE MAPPING
    # ==================================================

    ROOT_CAUSE_MAP = {

        # ----------------------------------------------
        # Historical behavior
        # ----------------------------------------------

        "drug_cost_change_high": {
            "cause": "extreme_drug_cost_change",
            "description":
                "Drug cost changed significantly compared with historical behavior."
        },

        "drug_cost_change_medium": {
            "cause": "unusual_drug_cost_change",
            "description":
                "Drug cost changed unusually compared with historical behavior."
        },

        "claim_volume_change_high": {
            "cause": "extreme_claim_volume_change",
            "description":
                "Claim volume changed significantly compared with historical behavior."
        },

        "claim_volume_change_medium": {
            "cause": "unusual_claim_volume_change",
            "description":
                "Claim volume changed unusually compared with historical behavior."
        },

        "fill_volume_change_high": {
            "cause": "extreme_fill_volume_change",
            "description":
                "Fill volume changed significantly compared with historical behavior."
        },

        "fill_volume_change_medium": {
            "cause": "unusual_fill_volume_change",
            "description":
                "Fill volume changed unusually compared with historical behavior."
        },

        "days_supply_change_high": {
            "cause": "extreme_days_supply_change",
            "description":
                "Day supply changed significantly compared with historical behavior."
        },

        "days_supply_change_medium": {
            "cause": "unusual_days_supply_change",
            "description":
                "Day supply changed unusually compared with historical behavior."
        },

        "beneficiary_change_high": {
            "cause": "extreme_beneficiary_change",
            "description":
                "Beneficiary volume changed significantly compared with historical behavior."
        },

        "beneficiary_change_medium": {
            "cause": "unusual_beneficiary_change",
            "description":
                "Beneficiary volume changed unusually compared with historical behavior."
        },

        "cost_per_claim_change_high": {
            "cause": "extreme_cost_per_claim_change",
            "description":
                "Cost per claim changed significantly compared with historical behavior."
        },

        "cost_per_claim_change_medium": {
            "cause": "unusual_cost_per_claim_change",
            "description":
                "Cost per claim changed unusually compared with historical behavior."
        },

        "cost_per_claim_change": {
            "cause": "unusual_cost_per_claim_change",
            "description":
                "Cost per claim changed unusually compared with historical behavior."
        },

        # ----------------------------------------------
        # Ratio-based behavior
        # ----------------------------------------------

        "fills_per_claim_high": {
            "cause": "unusual_fills_per_claim",
            "description":
                "The number of fills per claim is unusually high."
        },

        "fills_per_claim_medium": {
            "cause": "unusual_fills_per_claim",
            "description":
                "The number of fills per claim is higher than expected."
        },

        "cost_per_claim_high": {
            "cause": "unusual_cost_per_claim",
            "description":
                "The cost per claim is statistically unusual."
        },

        "cost_per_claim_medium": {
            "cause": "unusual_cost_per_claim",
            "description":
                "The cost per claim is higher than expected."
        },

        "cost_per_beneficiary_high": {
            "cause": "unusual_cost_per_beneficiary",
            "description":
                "The drug cost per beneficiary is statistically unusual."
        },

        "cost_per_beneficiary_medium": {
            "cause": "unusual_cost_per_beneficiary",
            "description":
                "The drug cost per beneficiary is higher than expected."
        },

        "cost_per_day_supply_high": {
            "cause": "unusual_cost_per_day_supply",
            "description":
                "The drug cost per day of supply is statistically unusual."
        },

        "cost_per_day_supply_medium": {
            "cause": "unusual_cost_per_day_supply",
            "description":
                "The drug cost per day of supply is higher than expected."
        },

        "day_supply_per_claim_high": {
            "cause": "unusual_day_supply_per_claim",
            "description":
                "The day supply per claim is statistically unusual."
        },

        "day_supply_per_claim_medium": {
            "cause": "unusual_day_supply_per_claim",
            "description":
                "The day supply per claim is higher than expected."
        },

        "claims_per_beneficiary_high": {
            "cause": "unusual_claims_per_beneficiary",
            "description":
                "The number of claims per beneficiary is statistically unusual."
        },

        "claims_per_beneficiary_medium": {
            "cause": "unusual_claims_per_beneficiary",
            "description":
                "The number of claims per beneficiary is higher than expected."
        },

        # ----------------------------------------------
        # Data quality / structural rules
        # ----------------------------------------------

        "negative_value": {
            "cause": "invalid_negative_value",
            "description":
                "A numerical pharmacy value contains an invalid negative value."
        },

        "fills_without_claims": {
            "cause": "fills_without_claims",
            "description":
                "Fill activity exists without corresponding claims."
        },

        "cost_without_claims": {
            "cause": "cost_without_claims",
            "description":
                "Drug cost exists without corresponding claims."
        },

        "ge65_exceeds_total": {
            "cause": "ge65_total_inconsistency",
            "description":
                "GE65 values exceed the corresponding total pharmacy values."
        },

        "missing_critical_value": {
            "cause": "missing_critical_data",
            "description":
                "A critical pharmacy data field is missing."
        },

        # ----------------------------------------------
        # Context
        # ----------------------------------------------

        "suppression_context": {
            "cause": "suppressed_demographic_data",
            "description":
                "Some demographic values are suppressed and should be treated as context."
        },
    }

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(self):

        pass

    # ==================================================
    # SAFE SEVERITY
    # ==================================================

    @staticmethod
    def _get_severity(
        reason: Dict[str, Any],
    ) -> str:

        severity = reason.get(
            "severity",
            "MEDIUM",
        )

        if severity is None:
            return "MEDIUM"

        return str(
            severity
        ).upper()

    # ==================================================
    # CONVERT ONE RULE
    # ==================================================

    def convert_rule(
        self,
        reason: Dict[str, Any],
    ) -> Dict[str, Any]:

        rule_name = reason.get(
            "rule",
            "unknown",
        )

        mapping = self.ROOT_CAUSE_MAP.get(
            rule_name
        )

        # Unknown rules are preserved rather
        # than silently discarded.

        if mapping is None:

            return {
                "cause": rule_name,
                "description":
                    reason.get(
                        "description",
                        f"Anomaly rule '{rule_name}' was triggered."
                    ),
                "severity":
                    self._get_severity(
                        reason
                    ),
            }

        return {
            "cause":
                mapping["cause"],

            "description":
                mapping["description"],

            "severity":
                self._get_severity(
                    reason
                ),
        }

    # ==================================================
    # REMOVE DUPLICATES
    # ==================================================

    @staticmethod
    def _deduplicate(
        causes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        unique = {}

        for cause in causes:

            key = cause.get(
                "cause"
            )

            if key not in unique:

                unique[key] = cause

        return list(
            unique.values()
        )

    # ==================================================
    # BUILD RULE ROOT CAUSES
    # ==================================================

    def build_rule_root_causes(
        self,
        reasons: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        causes = []

        for reason in reasons:

            category = reason.get(
                "category",
                "",
            )

            # Context is not a root cause.
            if category == "CONTEXT":
                continue

            causes.append(
                self.convert_rule(
                    reason
                )
            )

        return self._deduplicate(
            causes
        )

    # ==================================================
    # BUILD RAG CONTEXT
    # ==================================================

    def build_rag_context(
        self,
        root_causes: List[Dict[str, Any]],
    ) -> str:

        if not root_causes:

            return ""

        descriptions = [
            cause["description"]
            for cause in root_causes
        ]

        return (
            "Rule-based pharmacy anomaly evidence detected: "
            + " ".join(descriptions)
        )

    # ==================================================
    # COMPLETE RESULT
    # ==================================================

    def build(
        self,
        classified_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        all_reasons = []

        all_reasons.extend(
            classified_result.get(
                "hard_anomalies",
                [],
            )
        )

        all_reasons.extend(
            classified_result.get(
                "behavior_evidence",
                [],
            )
        )

        all_reasons.extend(
            classified_result.get(
                "data_quality_evidence",
                [],
            )
        )

        root_causes = (
            self.build_rule_root_causes(
                all_reasons
            )
        )

        rag_context = (
            self.build_rag_context(
                root_causes
            )
        )

        return {
            "rule_based_root_causes":
                root_causes,

            "context_for_rag":
                rag_context,
        }