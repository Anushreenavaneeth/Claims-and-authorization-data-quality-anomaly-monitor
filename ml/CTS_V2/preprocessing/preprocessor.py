# preprocessing/preprocessor.py

from typing import List, Optional

import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


class MLPreprocessor:
    """
    Prepares numerical ML features for anomaly-detection models.

    Steps:
        1. Select ML features
        2. Convert values to numeric
        3. Replace missing values using median imputation
        4. Standardize features

    The original dataframe is never modified.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame,
        feature_columns: List[str],
    ):
        self.dataframe = dataframe.copy()
        self.feature_columns = feature_columns

        self.imputer = SimpleImputer(
            strategy="median"
        )

        self.scaler = StandardScaler()

        self.is_fitted = False

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_features(self):
        """Check that all requested features exist."""

        missing_features = [
            feature
            for feature in self.feature_columns
            if feature not in self.dataframe.columns
        ]

        if missing_features:
            raise ValueError(
                f"Missing ML features: {missing_features}"
            )

        if not self.feature_columns:
            raise ValueError(
                "No ML features were provided."
            )

    # --------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------

    def convert_to_numeric(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Safely convert ML features to numeric."""

        result = dataframe.copy()

        for feature in self.feature_columns:

            result[feature] = pd.to_numeric(
                result[feature],
                errors="coerce",
            )

        return result

    # --------------------------------------------------
    # Fit
    # --------------------------------------------------

    def fit(
        self,
        dataframe: Optional[pd.DataFrame] = None,
    ):
        """
        Fit the imputer and scaler.

        In a real train/test setup, fit should only be
        performed on training data.
        """

        source = (
            dataframe.copy()
            if dataframe is not None
            else self.dataframe.copy()
        )

        self.validate_features()

        source = self.convert_to_numeric(source)

        values = source[
            self.feature_columns
        ]

        imputed_values = self.imputer.fit_transform(
            values
        )

        self.scaler.fit(
            imputed_values
        )

        self.is_fitted = True

        return self

    # --------------------------------------------------
    # Transform
    # --------------------------------------------------

    def transform(
        self,
        dataframe: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Transform data using the fitted imputer
        and scaler.
        """

        if not self.is_fitted:
            raise RuntimeError(
                "Preprocessor has not been fitted. "
                "Call fit() before transform()."
            )

        source = (
            dataframe.copy()
            if dataframe is not None
            else self.dataframe.copy()
        )

        source = self.convert_to_numeric(source)

        values = source[
            self.feature_columns
        ]

        imputed_values = self.imputer.transform(
            values
        )

        scaled_values = self.scaler.transform(
            imputed_values
        )

        result = pd.DataFrame(
            scaled_values,
            columns=self.feature_columns,
            index=source.index,
        )

        return result

    # --------------------------------------------------
    # Fit + Transform
    # --------------------------------------------------

    def fit_transform(self) -> pd.DataFrame:
        """
        Fit the preprocessing components and transform
        the current dataframe.
        """

        self.fit()

        return self.transform()

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def get_imputation_values(self) -> pd.Series:
        """
        Return the median values learned by the imputer.
        """

        if not self.is_fitted:
            raise RuntimeError(
                "Preprocessor has not been fitted."
            )

        return pd.Series(
            self.imputer.statistics_,
            index=self.feature_columns,
        )

    def get_feature_columns(self) -> List[str]:
        """Return the features used by the preprocessor."""

        return self.feature_columns.copy()