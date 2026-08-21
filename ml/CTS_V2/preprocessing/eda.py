# preprocessing/eda.py

from typing import Dict

import numpy as np
import pandas as pd


class EDAProfiler:
    """
    Lightweight automated EDA profiler for the pharmacy pipeline.

    This class analyzes the dataset without modifying it.

    It provides:
    - Dataset structure
    - Data types
    - Numerical statistics
    - Categorical statistics
    - Missing-value information
    - Unique-value counts
    - Zero-value counts
    - Skewness
    - Correlation information
    - Potential extreme-value information
    """

    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe.copy()

    # --------------------------------------------------
    # Dataset structure
    # --------------------------------------------------

    def dataset_info(self) -> Dict:
        """Return basic information about the dataset."""

        return {
            "rows": int(len(self.dataframe)),
            "columns": int(len(self.dataframe.columns)),
            "column_names": self.dataframe.columns.tolist(),
            "memory_usage_mb": round(
                self.dataframe.memory_usage(
                    deep=True
                ).sum() / (1024 ** 2),
                4
            ),
        }

    # --------------------------------------------------
    # Column classification
    # --------------------------------------------------

    def column_types(self) -> Dict:
        """
        Classify columns into numerical, categorical,
        boolean-like and object columns.
        """

        numerical_columns = (
            self.dataframe
            .select_dtypes(include=np.number)
            .columns
            .tolist()
        )

        categorical_columns = (
            self.dataframe
            .select_dtypes(include=["object", "category"])
            .columns
            .tolist()
        )

        return {
            "numerical_columns": numerical_columns,
            "categorical_columns": categorical_columns,
            "numerical_count": len(numerical_columns),
            "categorical_count": len(categorical_columns),
        }

    # --------------------------------------------------
    # Missing values
    # --------------------------------------------------

    def missing_value_profile(self) -> Dict:
        """Return missing count and percentage per column."""

        total_rows = len(self.dataframe)

        result = {}

        for column in self.dataframe.columns:

            missing_count = int(
                self.dataframe[column].isna().sum()
            )

            missing_percentage = (
                missing_count / total_rows * 100
                if total_rows > 0
                else 0
            )

            result[column] = {
                "missing_count": missing_count,
                "missing_percentage": round(
                    missing_percentage,
                    4
                ),
            }

        return result

    # --------------------------------------------------
    # Numerical profile
    # --------------------------------------------------

    def numerical_profile(self) -> Dict:
        """
        Generate statistical information for numerical columns.
        """

        numerical_columns = (
            self.dataframe
            .select_dtypes(include=np.number)
            .columns
        )

        result = {}

        for column in numerical_columns:

            series = self.dataframe[column]

            result[column] = {
                "count": int(series.count()),
                "missing": int(series.isna().sum()),
                "unique": int(series.nunique()),
                "mean": self._safe_float(
                    series.mean()
                ),
                "median": self._safe_float(
                    series.median()
                ),
                "std": self._safe_float(
                    series.std()
                ),
                "min": self._safe_float(
                    series.min()
                ),
                "max": self._safe_float(
                    series.max()
                ),
                "q1": self._safe_float(
                    series.quantile(0.25)
                ),
                "q3": self._safe_float(
                    series.quantile(0.75)
                ),
                "skewness": self._safe_float(
                    series.skew()
                ),
                "zero_count": int(
                    (series == 0).sum()
                ),
                "negative_count": int(
                    (series < 0).sum()
                ),
            }

        return result

    # --------------------------------------------------
    # Categorical profile
    # --------------------------------------------------

    def categorical_profile(
        self,
        top_n: int = 10
    ) -> Dict:
        """
        Generate statistics for categorical columns.

        top_n controls how many frequent categories
        are returned.
        """

        categorical_columns = (
            self.dataframe
            .select_dtypes(
                include=["object", "category"]
            )
            .columns
        )

        result = {}

        for column in categorical_columns:

            series = self.dataframe[column]

            value_counts = (
                series
                .value_counts(
                    dropna=False
                )
                .head(top_n)
            )

            top_values = {}

            for value, count in value_counts.items():

                if pd.isna(value):
                    key = "<NULL>"
                else:
                    key = str(value)

                top_values[key] = int(count)

            result[column] = {
                "unique_count": int(
                    series.nunique(
                        dropna=True
                    )
                ),
                "missing_count": int(
                    series.isna().sum()
                ),
                "top_values": top_values,
            }

        return result

    # --------------------------------------------------
    # Duplicate profile
    # --------------------------------------------------

    def duplicate_profile(self) -> Dict:
        """Return duplicate-row statistics."""

        duplicate_count = int(
            self.dataframe.duplicated(
                keep=False
            ).sum()
        )

        return {
            "duplicate_rows": duplicate_count,
            "duplicate_percentage": round(
                (
                    duplicate_count
                    / len(self.dataframe)
                    * 100
                )
                if len(self.dataframe) > 0
                else 0,
                4,
            ),
        }

    # --------------------------------------------------
    # Correlation profile
    # --------------------------------------------------

    def correlation_profile(
        self,
        threshold: float = 0.70
    ) -> Dict:
        """
        Find strongly correlated numerical feature pairs.

        Only absolute correlations >= threshold are returned.
        """

        numerical_df = (
            self.dataframe
            .select_dtypes(include=np.number)
        )

        if numerical_df.shape[1] < 2:
            return {
                "threshold": threshold,
                "strong_correlations": []
            }

        correlation_matrix = (
            numerical_df.corr()
        )

        strong_correlations = []

        columns = correlation_matrix.columns

        for i in range(len(columns)):

            for j in range(i + 1, len(columns)):

                correlation = (
                    correlation_matrix
                    .iloc[i, j]
                )

                if pd.isna(correlation):
                    continue

                if abs(correlation) >= threshold:

                    strong_correlations.append(
                        {
                            "feature_1": columns[i],
                            "feature_2": columns[j],
                            "correlation": round(
                                float(correlation),
                                6
                            ),
                        }
                    )

        strong_correlations.sort(
            key=lambda x: abs(
                x["correlation"]
            ),
            reverse=True,
        )

        return {
            "threshold": threshold,
            "strong_correlations":
                strong_correlations,
        }

    # --------------------------------------------------
    # Extreme-value profile
    # --------------------------------------------------

    def extreme_value_profile(self) -> Dict:
        """
        Identify potential extreme values using the IQR method.

        This does NOT label them as anomalies.
        It only reports potential extreme observations.
        """

        numerical_columns = (
            self.dataframe
            .select_dtypes(include=np.number)
            .columns
        )

        result = {}

        for column in numerical_columns:

            series = self.dataframe[column].dropna()

            if series.empty:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)

            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            extreme_mask = (
                (series < lower_bound)
                | (series > upper_bound)
            )

            result[column] = {
                "lower_bound": self._safe_float(
                    lower_bound
                ),
                "upper_bound": self._safe_float(
                    upper_bound
                ),
                "potential_extreme_count": int(
                    extreme_mask.sum()
                ),
            }

        return result

    # --------------------------------------------------
    # Complete EDA
    # --------------------------------------------------

    def profile(self) -> Dict:
        """
        Run the complete automated EDA profile.
        """

        return {
            "dataset_info":
                self.dataset_info(),

            "column_types":
                self.column_types(),

            "missing_values":
                self.missing_value_profile(),

            "numerical_profile":
                self.numerical_profile(),

            "categorical_profile":
                self.categorical_profile(),

            "duplicates":
                self.duplicate_profile(),

            "correlations":
                self.correlation_profile(),

            "extreme_values":
                self.extreme_value_profile(),
        }

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    @staticmethod
    def _safe_float(value):
        """
        Convert numerical values safely for JSON-compatible output.
        """

        if pd.isna(value):
            return None

        if np.isinf(value):
            return None

        return float(value)