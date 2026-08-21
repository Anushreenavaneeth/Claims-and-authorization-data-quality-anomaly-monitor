# feature_engineering/behavioral_features.py

import numpy as np
import pandas as pd


class BehavioralFeatureEngineer:
    """
    Creates behavioral features from pharmacy-level numerical data.

    The original columns are preserved.
    New derived features are added to a copy of the dataframe.
    """

    REQUIRED_COLUMNS = [
        "Tot_Clms",
        "Tot_30day_Fills",
        "Tot_Day_Suply",
        "Tot_Drug_Cst",
        "Tot_Benes",
    ]

    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe.copy()

    def _safe_divide(self, numerator, denominator):
        """
        Safely divide two pandas Series.

        Division by zero or invalid values returns NaN
        instead of infinity.
        """
        numerator = pd.to_numeric(numerator, errors="coerce")
        denominator = pd.to_numeric(denominator, errors="coerce")

        result = numerator.div(denominator)

        return result.replace([np.inf, -np.inf], np.nan)

    def validate_columns(self):
        """Check whether required columns are available."""

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in self.dataframe.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns for behavioral "
                f"feature engineering: {missing_columns}"
            )

    def create_features(self) -> pd.DataFrame:
        """
        Create behavioral features and return the transformed dataframe.
        """

        self.validate_columns()

        df = self.dataframe

        # Convert source numerical columns safely.
        for column in self.REQUIRED_COLUMNS:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        # --------------------------------------------------
        # 1. Average drug cost per claim
        # --------------------------------------------------
        df["cost_per_claim"] = self._safe_divide(
            df["Tot_Drug_Cst"],
            df["Tot_Clms"]
        )

        # --------------------------------------------------
        # 2. Claims per beneficiary
        # --------------------------------------------------
        df["claims_per_beneficiary"] = self._safe_divide(
            df["Tot_Clms"],
            df["Tot_Benes"]
        )

        # --------------------------------------------------
        # 3. Drug cost per beneficiary
        # --------------------------------------------------
        df["cost_per_beneficiary"] = self._safe_divide(
            df["Tot_Drug_Cst"],
            df["Tot_Benes"]
        )

        # --------------------------------------------------
        # 4. Day supply per claim
        # --------------------------------------------------
        df["day_supply_per_claim"] = self._safe_divide(
            df["Tot_Day_Suply"],
            df["Tot_Clms"]
        )

        # --------------------------------------------------
        # 5. 30-day fills per claim
        # --------------------------------------------------
        df["fills_per_claim"] = self._safe_divide(
            df["Tot_30day_Fills"],
            df["Tot_Clms"]
        )

        # --------------------------------------------------
        # 6. Drug cost per day of supply
        # --------------------------------------------------
        df["cost_per_day_supply"] = self._safe_divide(
            df["Tot_Drug_Cst"],
            df["Tot_Day_Suply"]
        )

        return df

    def get_behavioral_features(self) -> list:
        """
        Return the names of the behavioral features created by this class.
        """

        return [
            "cost_per_claim",
            "claims_per_beneficiary",
            "cost_per_beneficiary",
            "day_supply_per_claim",
            "fills_per_claim",
            "cost_per_day_supply",
        ]