# feature_engineering/feature_selector.py

from typing import Dict, List

import pandas as pd


class FeatureSelector:
    """
    Organizes pharmacy dataset columns and determines
    which engineered features are suitable for ML models.

    This class does not modify the input dataframe.
    """

    # --------------------------------------------------
    # Identifier columns
    # --------------------------------------------------

    IDENTIFIER_COLUMNS = [
        "Prscrbr_NPI",
    ]

    # --------------------------------------------------
    # Descriptive columns
    # --------------------------------------------------

    DESCRIPTIVE_COLUMNS = [
        "Prscrbr_Last_Org_Name",
        "Prscrbr_First_Name",
    ]

    # --------------------------------------------------
    # Location columns
    # --------------------------------------------------

    LOCATION_COLUMNS = [
        "Prscrbr_City",
        "Prscrbr_State_Abrvtn",
        "Prscrbr_State_FIPS",
    ]

    # --------------------------------------------------
    # Prescriber categorical columns
    # --------------------------------------------------

    PRESCRIBER_CATEGORICAL_COLUMNS = [
        "Prscrbr_Type",
        "Prscrbr_Type_Src",
    ]

    # --------------------------------------------------
    # Drug categorical columns
    # --------------------------------------------------

    DRUG_CATEGORICAL_COLUMNS = [
        "Brnd_Name",
        "Gnrc_Name",
    ]

    # --------------------------------------------------
    # Original numerical features
    # --------------------------------------------------

    NUMERICAL_COLUMNS = [
        "Tot_Clms",
        "Tot_30day_Fills",
        "Tot_Day_Suply",
        "Tot_Drug_Cst",
        "Tot_Benes",
    ]

    GE65_NUMERICAL_COLUMNS = [
        "GE65_Tot_Clms",
        "GE65_Tot_30day_Fills",
        "GE65_Tot_Drug_Cst",
        "GE65_Tot_Day_Suply",
        "GE65_Tot_Benes",
    ]

    # --------------------------------------------------
    # Suppression columns
    # --------------------------------------------------

    SUPPRESSION_COLUMNS = [
        "GE65_Sprsn_Flag",
        "GE65_Bene_Sprsn_Flag",
    ]

    # --------------------------------------------------
    # Engineered behavioral features
    # --------------------------------------------------

    BEHAVIORAL_FEATURES = [
        "cost_per_claim",
        "claims_per_beneficiary",
        "cost_per_beneficiary",
        "day_supply_per_claim",
        "fills_per_claim",
        "cost_per_day_supply",
    ]

    # --------------------------------------------------
    # Historical behavioral features
    # --------------------------------------------------

    HISTORICAL_FEATURES = [
        "claim_volume_change",
        "fill_volume_change",
        "days_supply_change",
        "drug_cost_change",
        "beneficiary_change",
        "cost_per_claim_change",
    ]

    # --------------------------------------------------
    # Intermediate historical columns
    #
    # These are useful for analysis but should not
    # automatically become ML features.
    # --------------------------------------------------

    HISTORICAL_INTERMEDIATE_COLUMNS = [
        "historical_Tot_Clms",
        "historical_Tot_30day_Fills",
        "historical_Tot_Day_Suply",
        "historical_Tot_Drug_Cst",
        "historical_Tot_Benes",
    ]

    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe

    # ==================================================
    # BASIC COLUMN INFORMATION
    # ==================================================

    def get_available_columns(self) -> List[str]:
        """Return columns available in the input dataframe."""

        return list(self.dataframe.columns)

    def get_missing_expected_columns(self) -> List[str]:
        """Return expected columns missing from the dataset."""

        expected_columns = (
            self.IDENTIFIER_COLUMNS
            + self.DESCRIPTIVE_COLUMNS
            + self.LOCATION_COLUMNS
            + self.PRESCRIBER_CATEGORICAL_COLUMNS
            + self.DRUG_CATEGORICAL_COLUMNS
            + self.NUMERICAL_COLUMNS
            + self.GE65_NUMERICAL_COLUMNS
            + self.SUPPRESSION_COLUMNS
        )

        return [
            column
            for column in expected_columns
            if column not in self.dataframe.columns
        ]

    def get_extra_columns(self) -> List[str]:
        """
        Return columns that are not part of the original
        known pharmacy schema.
        """

        known_columns = set(
            self.IDENTIFIER_COLUMNS
            + self.DESCRIPTIVE_COLUMNS
            + self.LOCATION_COLUMNS
            + self.PRESCRIBER_CATEGORICAL_COLUMNS
            + self.DRUG_CATEGORICAL_COLUMNS
            + self.NUMERICAL_COLUMNS
            + self.GE65_NUMERICAL_COLUMNS
            + self.SUPPRESSION_COLUMNS
            + self.BEHAVIORAL_FEATURES
            + self.HISTORICAL_FEATURES
            + self.HISTORICAL_INTERMEDIATE_COLUMNS
        )

        return [
            column
            for column in self.dataframe.columns
            if column not in known_columns
        ]

    # ==================================================
    # FEATURE GROUPS
    # ==================================================

    def get_feature_groups(self) -> Dict[str, List[str]]:
        """Return columns grouped according to their purpose."""

        groups = {
            "identifier": self.IDENTIFIER_COLUMNS,
            "descriptive": self.DESCRIPTIVE_COLUMNS,
            "location": self.LOCATION_COLUMNS,
            "prescriber_categorical":
                self.PRESCRIBER_CATEGORICAL_COLUMNS,
            "drug_categorical":
                self.DRUG_CATEGORICAL_COLUMNS,
            "numerical": self.NUMERICAL_COLUMNS,
            "ge65_numerical":
                self.GE65_NUMERICAL_COLUMNS,
            "suppression": self.SUPPRESSION_COLUMNS,
            "behavioral":
                self.BEHAVIORAL_FEATURES,
            "historical":
                self.HISTORICAL_FEATURES,
            "historical_intermediate":
                self.HISTORICAL_INTERMEDIATE_COLUMNS,
        }

        return {
            group_name: [
                column
                for column in columns
                if column in self.dataframe.columns
            ]
            for group_name, columns in groups.items()
        }

    # ==================================================
    # ML FEATURES
    # ==================================================

    def get_ml_features(
        self,
        include_original: bool = True,
        include_behavioral: bool = True,
        include_historical: bool = True,
    ) -> List[str]:
        """
        Return the final candidate numerical features for ML.

        Identifier, text, location, categorical and suppression
        columns are intentionally excluded.
        """

        features = []

        if include_original:
            features.extend(self.NUMERICAL_COLUMNS)
            features.extend(self.GE65_NUMERICAL_COLUMNS)

        if include_behavioral:
            features.extend(self.BEHAVIORAL_FEATURES)

        if include_historical:
            features.extend(self.HISTORICAL_FEATURES)

        # Keep only columns actually present in the dataframe.
        features = [
            column
            for column in features
            if column in self.dataframe.columns
        ]

        # Remove duplicates while preserving order.
        return list(dict.fromkeys(features))

    def get_context_features(self) -> List[str]:
        """
        Return fields that should normally be preserved
        for explanation and final JSON output.
        """

        context_columns = (
            self.IDENTIFIER_COLUMNS
            + self.DESCRIPTIVE_COLUMNS
            + self.LOCATION_COLUMNS
            + self.PRESCRIBER_CATEGORICAL_COLUMNS
            + self.DRUG_CATEGORICAL_COLUMNS
            + self.SUPPRESSION_COLUMNS
        )

        return [
            column
            for column in context_columns
            if column in self.dataframe.columns
        ]

    def get_historical_intermediate_features(self) -> List[str]:
        """Return historical reference columns."""

        return [
            column
            for column in self.HISTORICAL_INTERMEDIATE_COLUMNS
            if column in self.dataframe.columns
        ]

    # ==================================================
    # ML DATAFRAME
    # ==================================================

    def get_ml_dataframe(
        self,
        include_original: bool = True,
        include_behavioral: bool = True,
        include_historical: bool = True,
    ) -> pd.DataFrame:
        """
        Return a dataframe containing only ML candidate features.
        """

        features = self.get_ml_features(
            include_original=include_original,
            include_behavioral=include_behavioral,
            include_historical=include_historical,
        )

        return self.dataframe[features].copy()

    # ==================================================
    # SUMMARY
    # ==================================================

    def summary(self) -> Dict:
        """Return a complete feature-selection summary."""

        return {
            "total_input_columns": len(
                self.dataframe.columns
            ),
            "feature_groups": self.get_feature_groups(),
            "ml_features": self.get_ml_features(),
            "ml_feature_count": len(
                self.get_ml_features()
            ),
            "context_features": self.get_context_features(),
            "historical_intermediate_features":
                self.get_historical_intermediate_features(),
            "missing_expected_columns":
                self.get_missing_expected_columns(),
            "extra_columns":
                self.get_extra_columns(),
        }