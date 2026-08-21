# feature_engineering/historical_features.py

import numpy as np
import pandas as pd


class HistoricalFeatureEngineer:
    """
    Creates historical behavior features by comparing
    current data against a historical/reference dataset.

    The class does not assume any specific year.
    """

    METRIC_COLUMNS = {
        "claim_volume_change": "Tot_Clms",
        "fill_volume_change": "Tot_30day_Fills",
        "days_supply_change": "Tot_Day_Suply",
        "drug_cost_change": "Tot_Drug_Cst",
        "beneficiary_change": "Tot_Benes",
    }

    REQUIRED_ID_COLUMN = "Prscrbr_NPI"

    def __init__(
        self,
        current_df: pd.DataFrame,
        historical_df: pd.DataFrame,
    ):
        self.current_df = current_df.copy()
        self.historical_df = historical_df.copy()

    def validate(self):
        """Validate required columns in both datasets."""

        required_columns = [
            self.REQUIRED_ID_COLUMN,
            *self.METRIC_COLUMNS.values(),
        ]

        current_missing = [
            column
            for column in required_columns
            if column not in self.current_df.columns
        ]

        historical_missing = [
            column
            for column in required_columns
            if column not in self.historical_df.columns
        ]

        if current_missing:
            raise ValueError(
                f"Current dataset is missing columns: {current_missing}"
            )

        if historical_missing:
            raise ValueError(
                f"Historical dataset is missing columns: {historical_missing}"
            )

    @staticmethod
    def _safe_percentage_change(current, historical):
        """
        Calculate relative change:

        (current - historical) / historical

        If the historical value is zero, the result is NaN
        rather than infinity.
        """

        current = pd.to_numeric(current, errors="coerce")
        historical = pd.to_numeric(historical, errors="coerce")

        result = (current - historical).div(historical)

        return result.replace([np.inf, -np.inf], np.nan)

    def _prepare_historical_data(self):
        """
        Aggregate historical data by prescriber.

        This is important because the same prescriber can appear
        multiple times in the historical dataset.
        """

        historical = self.historical_df.copy()

        numerical_columns = list(
            self.METRIC_COLUMNS.values()
        )

        for column in numerical_columns:
            historical[column] = pd.to_numeric(
                historical[column],
                errors="coerce",
            )

        historical = (
            historical
            .groupby(self.REQUIRED_ID_COLUMN, as_index=False)[
                numerical_columns
            ]
            .sum(min_count=1)
        )

        return historical

    def create_features(self) -> pd.DataFrame:
        """
        Compare current prescriber-level behavior with
        historical prescriber-level behavior.
        """

        self.validate()

        current = self.current_df.copy()
        historical = self._prepare_historical_data()

        # Convert current numerical columns.
        for column in self.METRIC_COLUMNS.values():
            current[column] = pd.to_numeric(
                current[column],
                errors="coerce",
            )

        # Rename historical columns so they don't conflict.
        rename_map = {
            column: f"historical_{column}"
            for column in self.METRIC_COLUMNS.values()
        }

        historical = historical.rename(
            columns=rename_map
        )

        # Merge historical behavior onto current records.
        current = current.merge(
            historical,
            on=self.REQUIRED_ID_COLUMN,
            how="left",
        )

        # --------------------------------------------------
        # Historical percentage changes
        # --------------------------------------------------

        current["claim_volume_change"] = (
            self._safe_percentage_change(
                current["Tot_Clms"],
                current["historical_Tot_Clms"],
            )
        )

        current["fill_volume_change"] = (
            self._safe_percentage_change(
                current["Tot_30day_Fills"],
                current["historical_Tot_30day_Fills"],
            )
        )

        current["days_supply_change"] = (
            self._safe_percentage_change(
                current["Tot_Day_Suply"],
                current["historical_Tot_Day_Suply"],
            )
        )

        current["drug_cost_change"] = (
            self._safe_percentage_change(
                current["Tot_Drug_Cst"],
                current["historical_Tot_Drug_Cst"],
            )
        )

        current["beneficiary_change"] = (
            self._safe_percentage_change(
                current["Tot_Benes"],
                current["historical_Tot_Benes"],
            )
        )

        # --------------------------------------------------
        # Historical cost-per-claim comparison
        # --------------------------------------------------

        current_cost_per_claim = (
            current["Tot_Drug_Cst"]
            / current["Tot_Clms"]
        )

        historical_cost_per_claim = (
            current["historical_Tot_Drug_Cst"]
            / current["historical_Tot_Clms"]
        )

        current["cost_per_claim_change"] = (
            self._safe_percentage_change(
                current_cost_per_claim,
                historical_cost_per_claim,
            )
        )

        return current

    def get_historical_features(self) -> list:
        """Return names of generated historical features."""

        return [
            "claim_volume_change",
            "fill_volume_change",
            "days_supply_change",
            "drug_cost_change",
            "beneficiary_change",
            "cost_per_claim_change",
        ]