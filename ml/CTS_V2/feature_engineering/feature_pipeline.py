# feature_engineering/feature_pipeline.py

import pandas as pd

from feature_engineering.behavioral_features import (
    BehavioralFeatureEngineer
)

from feature_engineering.historical_features import (
    HistoricalFeatureEngineer
)


class FeatureEngineeringPipeline:
    """
    Main feature-engineering pipeline.

    Steps:
        1. Behavioral feature engineering
        2. Historical feature engineering (optional)

    The original dataframe is never modified directly.
    """

    def __init__(
        self,
        current_df: pd.DataFrame,
        historical_df: pd.DataFrame | None = None,
    ):
        self.current_df = current_df.copy()
        self.historical_df = (
            historical_df.copy()
            if historical_df is not None
            else None
        )

    def create_features(self) -> pd.DataFrame:
        """
        Execute the complete feature-engineering process.
        """

        # ---------------------------------------------
        # Step 1: Behavioral features
        # ---------------------------------------------

        behavioral_engineer = BehavioralFeatureEngineer(
            self.current_df
        )

        result = behavioral_engineer.create_features()

        # ---------------------------------------------
        # Step 2: Historical features
        # ---------------------------------------------

        if self.historical_df is not None:

            historical_engineer = HistoricalFeatureEngineer(
                current_df=result,
                historical_df=self.historical_df,
            )

            result = historical_engineer.create_features()

        return result

    def get_feature_names(self, dataframe: pd.DataFrame) -> list:
        """
        Return the names of the engineered features
        that are present in the resulting dataframe.
        """

        expected_features = [
            # Behavioral
            "cost_per_claim",
            "claims_per_beneficiary",
            "cost_per_beneficiary",
            "day_supply_per_claim",
            "fills_per_claim",
            "cost_per_day_supply",

            # Historical
            "claim_volume_change",
            "fill_volume_change",
            "days_supply_change",
            "drug_cost_change",
            "beneficiary_change",
            "cost_per_claim_change",
        ]

        return [
            feature
            for feature in expected_features
            if feature in dataframe.columns
        ]