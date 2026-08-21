# preprocessing/cleaner.py

import numpy as np
import pandas as pd


class DataCleaner:
    """
    Basic data cleaning for the pharmacy anomaly pipeline.

    Responsibilities:
    - Normalize column names
    - Convert numerical columns safely
    - Handle infinite values
    - Preserve categorical/context columns
    - Report basic cleaning statistics

    This class does NOT perform ML preprocessing such as scaling
    or imputation. Those will be handled separately.
    """

    NUMERICAL_COLUMNS = [
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
        "cost_per_claim",
        "claims_per_beneficiary",
        "cost_per_beneficiary",
        "day_supply_per_claim",
        "fills_per_claim",
        "cost_per_day_supply",
        "claim_volume_change",
        "fill_volume_change",
        "days_supply_change",
        "drug_cost_change",
        "beneficiary_change",
        "cost_per_claim_change",
    ]

    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe.copy()

        self.stats = {
            "rows_before": len(self.dataframe),
            "columns_before": len(self.dataframe.columns),
            "infinite_values_replaced": 0,
        }

    def clean_column_names(self):
        """
        Remove accidental spaces around column names.
        """

        self.dataframe.columns = (
            self.dataframe.columns
            .astype(str)
            .str.strip()
        )

    def convert_numerical_columns(self):
        """
        Safely convert known numerical columns to numeric types.

        Invalid values become NaN instead of crashing the pipeline.
        """

        for column in self.NUMERICAL_COLUMNS:

            if column in self.dataframe.columns:

                self.dataframe[column] = pd.to_numeric(
                    self.dataframe[column],
                    errors="coerce"
                )

    def replace_infinite_values(self):
        """
        Replace positive/negative infinity with NaN.
        """

        numerical_data = self.dataframe.select_dtypes(
            include=[np.number]
        )

        infinite_count = np.isinf(
            numerical_data.to_numpy()
        ).sum()

        self.stats["infinite_values_replaced"] = int(
            infinite_count
        )

        self.dataframe.replace(
            [np.inf, -np.inf],
            np.nan,
            inplace=True
        )

    def clean(self) -> pd.DataFrame:
        """
        Execute the cleaning process.
        """

        self.clean_column_names()

        self.convert_numerical_columns()

        self.replace_infinite_values()

        self.stats["rows_after"] = len(
            self.dataframe
        )

        self.stats["columns_after"] = len(
            self.dataframe.columns
        )

        return self.dataframe

    def get_statistics(self):
        """
        Return cleaning statistics.
        """

        return self.stats.copy()