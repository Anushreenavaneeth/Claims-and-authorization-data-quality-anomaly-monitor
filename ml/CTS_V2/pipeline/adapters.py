# pipeline/adapters.py

from typing import Dict, Any, List

import pandas as pd


class PipelineAdapters:
    """
    Converts outputs from the individual pipeline components
    into a common per-record format.

    This layer does NOT perform anomaly detection.
    It only normalizes existing outputs.
    """

    # ==================================================
    # RULE ENGINE
    # ==================================================

    @staticmethod
    def normalize_rule_results(
        rule_results: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        """
        Convert RuleEngine.evaluate_dataframe() output
        into a list of per-record dictionaries.
        """

        normalized = []

        for _, row in rule_results.iterrows():

            reasons = row.get(
                "rule_reasons",
                [],
            )

            context_reasons = row.get(
                "context_reasons",
                [],
            )

            # ------------------------------------------
            # Normalize rule reasons
            # ------------------------------------------

            normalized_reasons = []

            if isinstance(
                reasons,
                list,
            ):

                for reason in reasons:

                    if not isinstance(
                        reason,
                        dict,
                    ):
                        continue

                    normalized_reasons.append(
                        {
                            "rule":
                                reason.get(
                                    "rule",
                                    "unknown",
                                ),

                            "severity":
                                reason.get(
                                    "severity",
                                    "MEDIUM",
                                ),

                            "reason":
                                reason.get(
                                    "reason",
                                    "",
                                ),

                            "value":
                                reason.get(
                                    "value",
                                ),

                            "threshold":
                                reason.get(
                                    "threshold",
                                ),

                            "category":
                                PipelineAdapters
                                ._infer_rule_category(
                                    reason.get(
                                        "rule",
                                        ""
                                    )
                                ),
                        }
                    )

            # ------------------------------------------
            # Normalize context
            # ------------------------------------------

            normalized_context = []

            if isinstance(
                context_reasons,
                list,
            ):

                for reason in context_reasons:

                    if not isinstance(
                        reason,
                        dict,
                    ):
                        continue

                    normalized_context.append(
                        {
                            "rule":
                                reason.get(
                                    "rule",
                                    "context",
                                ),

                            "severity":
                                reason.get(
                                    "severity",
                                    "INFO",
                                ),

                            "reason":
                                reason.get(
                                    "reason",
                                    "",
                                ),

                            "category":
                                "CONTEXT",
                        }
                    )

            normalized.append(
                {
                    "row_index":
                        int(
                            row.get(
                                "row_index",
                                0,
                            )
                        ),

                    "rule_anomaly":
                        bool(
                            row.get(
                                "rule_anomaly",
                                False,
                            )
                        ),

                    "severity":
                        row.get(
                            "rule_severity",
                            "NONE",
                        ),

                    "reason_count":
                        int(
                            row.get(
                                "rule_reason_count",
                                0,
                            )
                        ),

                    "reasons":
                        normalized_reasons,

                    "context_reasons":
                        normalized_context,
                }
            )

        return normalized

    # ==================================================
    # RULE CATEGORY
    # ==================================================

    @staticmethod
    def _infer_rule_category(
        rule_name: str,
    ) -> str:

        if not rule_name:

            return "UNKNOWN"

        rule_name = str(
            rule_name
        ).lower()

        # ------------------------------------------
        # Historical behavior
        # ------------------------------------------

        historical_keywords = [
            "drug_cost_change",
            "claim_volume_change",
            "fill_volume_change",
            "days_supply_change",
            "beneficiary_change",
            "cost_per_claim_change",
        ]

        if any(
            keyword in rule_name
            for keyword in historical_keywords
        ):

            return "BEHAVIOR_EVIDENCE"

        # ------------------------------------------
        # Data quality
        # ------------------------------------------

        quality_keywords = [
            "missing",
            "negative",
            "without_claims",
            "without_day_supply",
            "without_beneficiaries",
            "ge65_exceeds_total",
        ]

        if any(
            keyword in rule_name
            for keyword in quality_keywords
        ):

            return "DATA_QUALITY"

        # ------------------------------------------
        # Ratio / statistical behavior
        # ------------------------------------------

        ratio_keywords = [
            "cost_per_claim",
            "cost_per_beneficiary",
            "cost_per_day_supply",
            "day_supply_per_claim",
            "fills_per_claim",
            "claims_per_beneficiary",
        ]

        if any(
            keyword in rule_name
            for keyword in ratio_keywords
        ):

            return "BEHAVIOR_EVIDENCE"

        return "UNKNOWN"

    # ==================================================
    # SINGLE RULE RECORD
    # ==================================================

    @staticmethod
    def rule_record_to_dict(
        rule_results: pd.DataFrame,
        row_index: int,
    ) -> Dict[str, Any]:

        if row_index < 0:

            raise ValueError(
                "row_index cannot be negative"
            )

        if row_index >= len(
            rule_results
        ):

            raise IndexError(
                "row_index is outside rule result range"
            )

        row = rule_results.iloc[
            row_index
        ]

        normalized = (
            PipelineAdapters
            .normalize_rule_results(
                pd.DataFrame(
                    [row]
                )
            )
        )

        return normalized[0]