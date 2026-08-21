# rules/rule_engine.py

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class RuleEngine:
    """
    Rule-based anomaly detection engine for pharmacy data.

    Rules are divided into:

    1. Data-quality rules
    2. Value consistency rules
    3. Ratio rules
    4. Historical behavior rules
    5. GE65 consistency rules
    6. Suppression context

    IMPORTANT:
    Suppression flags are CONTEXT.
    They do NOT automatically create an anomaly.

    Rules provide evidence.
    They do NOT make the final anomaly decision.
    """

    # ==================================================
    # THRESHOLDS
    # ==================================================

    DEFAULT_THRESHOLDS = {

        # ----------------------------------------------
        # Historical changes
        # ----------------------------------------------

        "drug_cost_change_high": 3.0,
        "drug_cost_change_medium": 1.5,

        "claim_volume_change_high": 2.0,
        "claim_volume_change_medium": 1.0,

        "fill_volume_change_high": 2.0,
        "fill_volume_change_medium": 1.0,

        "days_supply_change_high": 2.0,
        "days_supply_change_medium": 1.0,

        "beneficiary_change_high": 2.0,
        "beneficiary_change_medium": 1.0,

        "cost_per_claim_change_high": 2.0,
        "cost_per_claim_change_medium": 1.0,

        # ----------------------------------------------
        # Cost ratios
        # ----------------------------------------------

        "cost_per_claim_high": 1000.0,
        "cost_per_claim_medium": 500.0,

        "cost_per_beneficiary_high": 5000.0,
        "cost_per_beneficiary_medium": 2500.0,

        "cost_per_day_supply_high": 100.0,
        "cost_per_day_supply_medium": 50.0,

        # ----------------------------------------------
        # Utilization ratios
        # ----------------------------------------------

        "day_supply_per_claim_high": 365.0,
        "day_supply_per_claim_medium": 180.0,

        "fills_per_claim_high": 5.0,
        "fills_per_claim_medium": 3.0,

        "claims_per_beneficiary_high": 20.0,
        "claims_per_beneficiary_medium": 10.0,

        # ----------------------------------------------
        # Minimum activity required before ratio rules
        # ----------------------------------------------

        "minimum_claims_for_ratio": 5.0,
        "minimum_beneficiaries_for_ratio": 2.0,

    }

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
    ):

        self.thresholds = (
            self.DEFAULT_THRESHOLDS.copy()
        )

        if thresholds:
            self.thresholds.update(
                thresholds
            )

    # ==================================================
    # UTILITY
    # ==================================================

    @staticmethod
    def _is_valid_number(value) -> bool:

        if pd.isna(value):
            return False

        try:
            return bool(
                np.isfinite(float(value))
            )

        except (TypeError, ValueError):
            return False

    @staticmethod
    def _absolute_change(value):

        if pd.isna(value):
            return None

        try:

            value = float(value)

            if not np.isfinite(value):
                return None

            return abs(value)

        except (TypeError, ValueError):

            return None

    @staticmethod
    def _add_reason(
        reasons: List[Dict],
        rule: str,
        severity: str,
        reason: str,
        value=None,
        threshold=None,
        column=None,
    ):

        evidence = {
            "rule": rule,
            "severity": severity,
            "reason": reason,
        }

        if value is not None:
            evidence["value"] = value

        if threshold is not None:
            evidence["threshold"] = threshold

        if column is not None:
            evidence["column"] = column

        reasons.append(evidence)

    # ==================================================
    # 1. MISSING CRITICAL VALUES
    # ==================================================

    def _check_missing_critical_values(
        self,
        row,
        reasons,
    ):

        critical_columns = [
            "Prscrbr_NPI",
            "Prscrbr_City",
            "Prscrbr_State_Abrvtn",
            "Prscrbr_Type",
            "Brnd_Name",
            "Gnrc_Name",
        ]

        missing = []

        for column in critical_columns:

            if column in row.index:

                if pd.isna(row[column]):

                    missing.append(column)

        if missing:

            self._add_reason(
                reasons,
                "missing_critical_value",
                "MEDIUM",
                "Critical field(s) are missing",
                value=missing,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 2. NEGATIVE VALUES
    # ==================================================

    def _check_negative_values(
        self,
        row,
        reasons,
    ):

        columns = [
            "Tot_Clms",
            "Tot_30day_Fills",
            "Tot_Day_Suply",
            "Tot_Drug_Cst",
            "Tot_Benes",
            "GE65_Tot_Clms",
            "GE65_Tot_30day_Fills",
            "GE65_Tot_Drug_Cst",
            "GE65_Tot_Day_Suply",
            "GE65_Tot_Benes",
        ]

        found = False

        for column in columns:

            if column not in row.index:
                continue

            value = row[column]

            if self._is_valid_number(value):

                if float(value) < 0:

                    found = True

                    self._add_reason(
                        reasons,
                        "negative_value",
                        "HIGH",
                        f"Negative value detected in {column}",
                        value=float(value),
                        column=column,
                    )

        return "HIGH" if found else None

    # ==================================================
    # 3. FILLS WITHOUT CLAIMS
    # ==================================================

    def _check_claim_fill_consistency(
        self,
        row,
        reasons,
    ):

        claims = row.get("Tot_Clms")
        fills = row.get("Tot_30day_Fills")

        if not (
            self._is_valid_number(claims)
            and self._is_valid_number(fills)
        ):
            return None

        claims = float(claims)
        fills = float(fills)

        if claims == 0 and fills > 0:

            self._add_reason(
                reasons,
                "fills_without_claims",
                "HIGH",
                "30-day fills exist while total claims are zero",
                value=fills,
            )

            return "HIGH"

        return None

    # ==================================================
    # 4. CLAIMS WITHOUT DAY SUPPLY
    # ==================================================

    def _check_claim_day_supply(
        self,
        row,
        reasons,
    ):

        claims = row.get("Tot_Clms")
        supply = row.get("Tot_Day_Suply")

        if not (
            self._is_valid_number(claims)
            and self._is_valid_number(supply)
        ):
            return None

        claims = float(claims)
        supply = float(supply)

        if claims > 0 and supply == 0:

            self._add_reason(
                reasons,
                "claims_without_day_supply",
                "MEDIUM",
                "Claims exist but total day supply is zero",
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 5. COST WITHOUT CLAIMS
    # ==================================================

    def _check_cost_claim_consistency(
        self,
        row,
        reasons,
    ):

        claims = row.get("Tot_Clms")
        cost = row.get("Tot_Drug_Cst")

        if not (
            self._is_valid_number(claims)
            and self._is_valid_number(cost)
        ):
            return None

        claims = float(claims)
        cost = float(cost)

        if claims == 0 and cost > 0:

            self._add_reason(
                reasons,
                "cost_without_claims",
                "HIGH",
                "Drug cost exists while claims are zero",
                value=cost,
            )

            return "HIGH"

        return None

    # ==================================================
    # 6. CLAIMS WITHOUT BENEFICIARIES
    # ==================================================

    def _check_beneficiary_consistency(
        self,
        row,
        reasons,
    ):

        claims = row.get("Tot_Clms")
        beneficiaries = row.get("Tot_Benes")

        if not (
            self._is_valid_number(claims)
            and self._is_valid_number(beneficiaries)
        ):
            return None

        claims = float(claims)
        beneficiaries = float(beneficiaries)

        if claims > 0 and beneficiaries == 0:

            self._add_reason(
                reasons,
                "claims_without_beneficiaries",
                "MEDIUM",
                "Claims exist but beneficiary count is zero",
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 7. COST PER CLAIM
    # ==================================================

    def _check_cost_per_claim(
        self,
        row,
        reasons,
    ):

        value = row.get("cost_per_claim")

        claims = row.get("Tot_Clms")

        if not self._is_valid_number(value):
            return None

        if not self._is_valid_number(claims):
            return None

        claims = float(claims)
        value = float(value)

        # Require enough activity before applying
        # the ratio-based anomaly rule.
        if claims < self.thresholds[
            "minimum_claims_for_ratio"
        ]:
            return None

        high = self.thresholds[
            "cost_per_claim_high"
        ]

        medium = self.thresholds[
            "cost_per_claim_medium"
        ]

        if value >= high:

            self._add_reason(
                reasons,
                "cost_per_claim_high",
                "HIGH",
                "Extremely high cost per claim",
                value=value,
                threshold=high,
            )

            return "HIGH"

        if value >= medium:

            self._add_reason(
                reasons,
                "cost_per_claim_medium",
                "MEDIUM",
                "Unusually high cost per claim",
                value=value,
                threshold=medium,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 8. COST PER BENEFICIARY
    # ==================================================

    def _check_cost_per_beneficiary(
        self,
        row,
        reasons,
    ):

        value = row.get(
            "cost_per_beneficiary"
        )

        beneficiaries = row.get(
            "Tot_Benes"
        )

        if not self._is_valid_number(value):
            return None

        if not self._is_valid_number(
            beneficiaries
        ):
            return None

        beneficiaries = float(
            beneficiaries
        )

        value = float(value)

        if beneficiaries < self.thresholds[
            "minimum_beneficiaries_for_ratio"
        ]:
            return None

        high = self.thresholds[
            "cost_per_beneficiary_high"
        ]

        medium = self.thresholds[
            "cost_per_beneficiary_medium"
        ]

        if value >= high:

            self._add_reason(
                reasons,
                "cost_per_beneficiary_high",
                "HIGH",
                "Extremely high cost per beneficiary",
                value=value,
                threshold=high,
            )

            return "HIGH"

        if value >= medium:

            self._add_reason(
                reasons,
                "cost_per_beneficiary_medium",
                "MEDIUM",
                "Unusually high cost per beneficiary",
                value=value,
                threshold=medium,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 9. COST PER DAY SUPPLY
    # ==================================================

    def _check_cost_per_day_supply(
        self,
        row,
        reasons,
    ):

        value = row.get(
            "cost_per_day_supply"
        )

        supply = row.get(
            "Tot_Day_Suply"
        )

        if not self._is_valid_number(value):
            return None

        if not self._is_valid_number(supply):
            return None

        supply = float(supply)
        value = float(value)

        if supply <= 0:
            return None

        high = self.thresholds[
            "cost_per_day_supply_high"
        ]

        medium = self.thresholds[
            "cost_per_day_supply_medium"
        ]

        if value >= high:

            self._add_reason(
                reasons,
                "cost_per_day_supply_high",
                "HIGH",
                "Extremely high drug cost per day supply",
                value=value,
                threshold=high,
            )

            return "HIGH"

        if value >= medium:

            self._add_reason(
                reasons,
                "cost_per_day_supply_medium",
                "MEDIUM",
                "Unusually high drug cost per day supply",
                value=value,
                threshold=medium,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 10. DAY SUPPLY PER CLAIM
    # ==================================================

    def _check_day_supply_per_claim(
        self,
        row,
        reasons,
    ):

        value = row.get(
            "day_supply_per_claim"
        )

        claims = row.get(
            "Tot_Clms"
        )

        if not self._is_valid_number(value):
            return None

        if not self._is_valid_number(claims):
            return None

        claims = float(claims)
        value = float(value)

        if claims < self.thresholds[
            "minimum_claims_for_ratio"
        ]:
            return None

        high = self.thresholds[
            "day_supply_per_claim_high"
        ]

        medium = self.thresholds[
            "day_supply_per_claim_medium"
        ]

        if value >= high:

            self._add_reason(
                reasons,
                "day_supply_per_claim_high",
                "HIGH",
                "Extremely high day supply per claim",
                value=value,
                threshold=high,
            )

            return "HIGH"

        if value >= medium:

            self._add_reason(
                reasons,
                "day_supply_per_claim_medium",
                "MEDIUM",
                "Unusually high day supply per claim",
                value=value,
                threshold=medium,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 11. FILLS PER CLAIM
    # ==================================================

    def _check_fills_per_claim(
        self,
        row,
        reasons,
    ):

        value = row.get(
            "fills_per_claim"
        )

        claims = row.get(
            "Tot_Clms"
        )

        if not self._is_valid_number(value):
            return None

        if not self._is_valid_number(claims):
            return None

        claims = float(claims)
        value = float(value)

        if claims < self.thresholds[
            "minimum_claims_for_ratio"
        ]:
            return None

        high = self.thresholds[
            "fills_per_claim_high"
        ]

        medium = self.thresholds[
            "fills_per_claim_medium"
        ]

        if value >= high:

            self._add_reason(
                reasons,
                "fills_per_claim_high",
                "HIGH",
                "Extremely high fills per claim",
                value=value,
                threshold=high,
            )

            return "HIGH"

        if value >= medium:

            self._add_reason(
                reasons,
                "fills_per_claim_medium",
                "MEDIUM",
                "Unusually high fills per claim",
                value=value,
                threshold=medium,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 12. CLAIMS PER BENEFICIARY
    # ==================================================

    def _check_claims_per_beneficiary(
        self,
        row,
        reasons,
    ):

        value = row.get(
            "claims_per_beneficiary"
        )

        beneficiaries = row.get(
            "Tot_Benes"
        )

        if not self._is_valid_number(value):
            return None

        if not self._is_valid_number(
            beneficiaries
        ):
            return None

        beneficiaries = float(
            beneficiaries
        )

        value = float(value)

        if beneficiaries < self.thresholds[
            "minimum_beneficiaries_for_ratio"
        ]:
            return None

        high = self.thresholds[
            "claims_per_beneficiary_high"
        ]

        medium = self.thresholds[
            "claims_per_beneficiary_medium"
        ]

        if value >= high:

            self._add_reason(
                reasons,
                "claims_per_beneficiary_high",
                "HIGH",
                "Extremely high claims per beneficiary",
                value=value,
                threshold=high,
            )

            return "HIGH"

        if value >= medium:

            self._add_reason(
                reasons,
                "claims_per_beneficiary_medium",
                "MEDIUM",
                "Unusually high claims per beneficiary",
                value=value,
                threshold=medium,
            )

            return "MEDIUM"

        return None

    # ==================================================
    # 13-18. HISTORICAL RULES
    # ==================================================

    def _check_change_rule(
        self,
        row,
        column,
        high_threshold,
        medium_threshold,
        description,
        reasons,
    ):

        if column not in row.index:
            return None

        change = self._absolute_change(
            row[column]
        )

        if change is None:
            return None

        if change >= high_threshold:

            self._add_reason(
                reasons,
                column,
                "HIGH",
                description,
                value=change,
                threshold=high_threshold,
            )

            return "HIGH"

        if change >= medium_threshold:

            self._add_reason(
                reasons,
                column,
                "MEDIUM",
                description,
                value=change,
                threshold=medium_threshold,
            )

            return "MEDIUM"

        return None

    def _check_historical_rules(
        self,
        row,
        reasons,
    ):

        rules = [
            (
                "drug_cost_change",
                "drug_cost_change_high",
                "drug_cost_change_medium",
                "Extreme year-over-year drug cost change",
            ),
            (
                "claim_volume_change",
                "claim_volume_change_high",
                "claim_volume_change_medium",
                "Extreme year-over-year claim volume change",
            ),
            (
                "fill_volume_change",
                "fill_volume_change_high",
                "fill_volume_change_medium",
                "Extreme year-over-year fill volume change",
            ),
            (
                "days_supply_change",
                "days_supply_change_high",
                "days_supply_change_medium",
                "Extreme year-over-year day supply change",
            ),
            (
                "beneficiary_change",
                "beneficiary_change_high",
                "beneficiary_change_medium",
                "Extreme year-over-year beneficiary change",
            ),
            (
                "cost_per_claim_change",
                "cost_per_claim_change_high",
                "cost_per_claim_change_medium",
                "Extreme year-over-year cost per claim change",
            ),
        ]

        severities = []

        for (
            column,
            high_key,
            medium_key,
            description,
        ) in rules:

            result = self._check_change_rule(
                row,
                column,
                self.thresholds[high_key],
                self.thresholds[medium_key],
                description,
                reasons,
            )

            if result:
                severities.append(result)

        return severities

    # ==================================================
    # 19. GE65 CONSISTENCY
    # ==================================================

    def _check_ge65_consistency(
        self,
        row,
        reasons,
    ):

        comparisons = [
            (
                "GE65_Tot_Clms",
                "Tot_Clms",
                "GE65 claims exceed total claims",
            ),
            (
                "GE65_Tot_30day_Fills",
                "Tot_30day_Fills",
                "GE65 fills exceed total fills",
            ),
            (
                "GE65_Tot_Drug_Cst",
                "Tot_Drug_Cst",
                "GE65 drug cost exceeds total drug cost",
            ),
            (
                "GE65_Tot_Day_Suply",
                "Tot_Day_Suply",
                "GE65 day supply exceeds total day supply",
            ),
            (
                "GE65_Tot_Benes",
                "Tot_Benes",
                "GE65 beneficiaries exceed total beneficiaries",
            ),
        ]

        severities = []

        for (
            ge65_column,
            total_column,
            description,
        ) in comparisons:

            if (
                ge65_column not in row.index
                or total_column not in row.index
            ):
                continue

            ge65 = row[ge65_column]
            total = row[total_column]

            if not (
                self._is_valid_number(ge65)
                and self._is_valid_number(total)
            ):
                continue

            ge65 = float(ge65)
            total = float(total)

            if ge65 >= 0 and total >= 0:

                if ge65 > total:

                    self._add_reason(
                        reasons,
                        "ge65_exceeds_total",
                        "HIGH",
                        description,
                        value=ge65,
                    )

                    severities.append(
                        "HIGH"
                    )

        return severities

    # ==================================================
    # 20. SUPPRESSION CONTEXT
    # ==================================================

    def _check_suppression_context(
        self,
        row,
    ):
        """
        Suppression flags are recorded as CONTEXT.

        They do NOT enter the anomaly reasons list.
        They do NOT increase anomaly severity.
        """

        context_reasons = []

        flag_columns = [
            "GE65_Sprsn_Flag",
            "GE65_Bene_Sprsn_Flag",
        ]

        for column in flag_columns:

            if column not in row.index:
                continue

            value = row[column]

            if pd.isna(value):
                continue

            value_string = (
                str(value)
                .strip()
                .upper()
            )

            if value_string not in {
                "",
                "N",
                "NO",
                "0",
                "FALSE",
                "NONE",
                "NAN",
            }:

                context_reasons.append(
                    {
                        "rule": "suppression_context",
                        "severity": "INFO",
                        "reason": (
                            f"Suppression flag present "
                            f"in {column}"
                        ),
                        "value": value_string,
                        "column": column,
                    }
                )

        return context_reasons

    # ==================================================
    # EVALUATE ONE ROW
    # ==================================================

    def evaluate_row(
        self,
        row: pd.Series,
    ):

        reasons = []

        severities = []

        # ----------------------------------------------
        # Context information
        # ----------------------------------------------

        context_reasons = (
            self._check_suppression_context(
                row
            )
        )

        # ----------------------------------------------
        # Data-quality rules
        # ----------------------------------------------

        checks = [
            self._check_missing_critical_values,
            self._check_negative_values,
        ]

        for check in checks:

            severity = check(
                row,
                reasons,
            )

            if severity:
                severities.append(
                    severity
                )

        # ----------------------------------------------
        # Consistency rules
        # ----------------------------------------------

        consistency_checks = [
            self._check_claim_fill_consistency,
            self._check_claim_day_supply,
            self._check_cost_claim_consistency,
            self._check_beneficiary_consistency,
        ]

        for check in consistency_checks:

            severity = check(
                row,
                reasons,
            )

            if severity:
                severities.append(
                    severity
                )

        # ----------------------------------------------
        # Ratio rules
        # ----------------------------------------------

        ratio_checks = [
            self._check_cost_per_claim,
            self._check_cost_per_beneficiary,
            self._check_cost_per_day_supply,
            self._check_day_supply_per_claim,
            self._check_fills_per_claim,
            self._check_claims_per_beneficiary,
        ]

        for check in ratio_checks:

            severity = check(
                row,
                reasons,
            )

            if severity:
                severities.append(
                    severity
                )

        # ----------------------------------------------
        # Historical behavior
        # ----------------------------------------------

        severities.extend(
            self._check_historical_rules(
                row,
                reasons,
            )
        )

        # ----------------------------------------------
        # GE65 consistency
        # ----------------------------------------------

        severities.extend(
            self._check_ge65_consistency(
                row,
                reasons,
            )
        )

        # ----------------------------------------------
        # Final severity
        # ----------------------------------------------

        if "HIGH" in severities:

            final_severity = "HIGH"

        elif "MEDIUM" in severities:

            final_severity = "MEDIUM"

        elif "LOW" in severities:

            final_severity = "LOW"

        else:

            final_severity = "NONE"

        # ----------------------------------------------
        # Final result
        # ----------------------------------------------

        return {
            "rule_anomaly": (
                len(reasons) > 0
            ),
            "severity": final_severity,
            "reason_count": len(reasons),
            "reasons": reasons,
            "context_reasons": context_reasons,
        }

    # ==================================================
    # EVALUATE COMPLETE DATAFRAME
    # ==================================================

    def evaluate_dataframe(
        self,
        dataframe: pd.DataFrame,
    ):

        results = []

        for index, row in dataframe.iterrows():

            result = self.evaluate_row(
                row
            )

            results.append(
                {
                    "row_index": index,

                    "rule_anomaly":
                        result[
                            "rule_anomaly"
                        ],

                    "rule_severity":
                        result[
                            "severity"
                        ],

                    "rule_reason_count":
                        result[
                            "reason_count"
                        ],

                    "rule_reasons":
                        result[
                            "reasons"
                        ],

                    "context_reasons":
                        result[
                            "context_reasons"
                        ],
                }
            )

        return pd.DataFrame(
            results
        )

    # ==================================================
    # THRESHOLDS
    # ==================================================

    def get_thresholds(self):

        return self.thresholds.copy()