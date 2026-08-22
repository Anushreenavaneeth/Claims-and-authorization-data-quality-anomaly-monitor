# models/isolation_forest.py

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    """
    Isolation Forest based anomaly detector.

    Output:
        prediction:
            1  -> normal
           -1  -> anomaly

        anomaly_score:
            Higher value -> more anomalous

    The model can be:
        - trained
        - used for prediction
        - saved
        - loaded
    """

    def __init__(
        self,
        contamination: float = 0.01,
        n_estimators: int = 200,
        max_samples: str | int = "auto",
        random_state: int = 42,
        n_jobs: int = -1,
    ):
        if not 0 < contamination <= 0.5:
            raise ValueError(
                "contamination must be between "
                "0 and 0.5"
            )

        self.contamination = contamination

        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            random_state=random_state,
            n_jobs=n_jobs,
        )

        self.feature_columns: Optional[list[str]] = None
        self.is_fitted = False

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def _validate_input(
        self,
        X: pd.DataFrame,
    ):
        if not isinstance(X, pd.DataFrame):
            raise TypeError(
                "X must be a pandas DataFrame."
            )

        if X.empty:
            raise ValueError(
                "Input dataframe is empty."
            )

        if X.isna().any().any():
            raise ValueError(
                "Input contains missing values. "
                "Run ML preprocessing before "
                "Isolation Forest."
            )

        if not np.isfinite(
            X.to_numpy(dtype=float)
        ).all():
            raise ValueError(
                "Input contains infinite values."
            )

    # --------------------------------------------------
    # Training
    # --------------------------------------------------

    def fit(
        self,
        X: pd.DataFrame,
    ):
        """
        Train Isolation Forest on the supplied
        ML feature dataframe.
        """

        self._validate_input(X)

        self.feature_columns = list(
            X.columns
        )

        self.model.fit(X)

        self.is_fitted = True

        return self

    # --------------------------------------------------
    # Raw model score
    # --------------------------------------------------

    def decision_function(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Return sklearn's decision function.

        Higher values generally indicate more normal
        observations.

        Lower values indicate more anomalous
        observations.
        """

        self._check_fitted()

        self._validate_features(X)

        return self.model.decision_function(X)

    # --------------------------------------------------
    # Anomaly score
    # --------------------------------------------------

    def anomaly_score(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Convert Isolation Forest's decision function
        into an anomaly-oriented score.

        Higher score = more anomalous.

        This score is mainly useful for ranking and
        combining evidence with other detectors.
        """

        decision_scores = self.decision_function(X)

        # Reverse the direction so that:
        #
        # normal      -> lower score
        # anomalous   -> higher score
        #
        raw_scores = -decision_scores

        # Normalize within the current prediction batch.
        min_score = raw_scores.min()
        max_score = raw_scores.max()

        if max_score == min_score:
            return np.zeros(
                len(raw_scores),
                dtype=float,
            )

        normalized_scores = (
            (raw_scores - min_score)
            / (max_score - min_score)
        )

        return normalized_scores

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    def predict(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Predict anomalies and return a dataframe
        containing the model results.
        """

        self._check_fitted()

        self._validate_features(X)

        predictions = self.model.predict(X)

        scores = self.anomaly_score(X)

        result = pd.DataFrame(
            {
                "is_anomaly": predictions == -1,
                "prediction": predictions,
                "anomaly_score": scores,
            },
            index=X.index,
        )

        return result

    # --------------------------------------------------
    # Combined fit + prediction
    # --------------------------------------------------

    def fit_predict(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Train the model and predict anomalies
        on the same dataset.

        This is useful for initial development/testing.
        """

        self.fit(X)

        return self.predict(X)

    # --------------------------------------------------
    # Feature validation
    # --------------------------------------------------

    def _validate_features(
        self,
        X: pd.DataFrame,
    ):
        if list(X.columns) != self.feature_columns:
            raise ValueError(
                "Input features do not match the "
                "features used during training.\n"
                f"Expected: {self.feature_columns}\n"
                f"Received: {list(X.columns)}"
            )

        self._validate_input(X)

    # --------------------------------------------------
    # Fitted check
    # --------------------------------------------------

    def _check_fitted(self):
        if not self.is_fitted:
            raise RuntimeError(
                "Isolation Forest has not been fitted. "
                "Call fit() first."
            )

    # --------------------------------------------------
    # Save model
    # --------------------------------------------------

    def save(
        self,
        path: str = "models/artifacts/isolation_forest.pkl",
    ):
        """
        Save the trained detector.

        The model is serialized using joblib,
        but stored with a .pkl extension.
        """

        self._check_fitted()

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            self,
            path,
        )

        return path

    # --------------------------------------------------
    # Load model
    # --------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str = "models/artifacts/isolation_forest.pkl",
    ):
        """
        Load a previously trained detector.

        The file is expected to be a joblib-serialized
        object stored with a .pkl extension.
        """

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found: {path}"
            )

        detector = joblib.load(path)

        if not isinstance(
            detector,
            cls,
        ):
            raise TypeError(
                "Loaded object is not an "
                "IsolationForestDetector."
            )

        return detector

    # --------------------------------------------------
    # Model information
    # --------------------------------------------------

    def get_model_info(self) -> dict:
        """
        Return useful model metadata.
        """

        return {
            "model": "Isolation Forest",
            "contamination":
                self.contamination,
            "n_estimators":
                self.model.n_estimators,
            "max_samples":
                self.model.max_samples,
            "random_state":
                self.model.random_state,
            "feature_count":
                len(self.feature_columns)
                if self.feature_columns
                else 0,
            "feature_columns":
                self.feature_columns,
            "is_fitted":
                self.is_fitted,
        }