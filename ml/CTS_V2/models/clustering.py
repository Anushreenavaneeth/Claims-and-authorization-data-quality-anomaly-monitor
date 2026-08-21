# models/clustering.py

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans


class KMeansClusterDetector:
    """
    K-Means clustering component for the pharmacy
    anomaly-detection pipeline.

    Purpose:
        Identify groups of records with similar behavior.

    Clustering is NOT treated as the final anomaly detector.
    It provides peer-group/context evidence that can later
    be combined with Isolation Forest, rules, historical
    behavior, and Bayesian reasoning.
    """

    def __init__(
        self,
        n_clusters: int = 5,
        n_init: int = 10,
        max_iter: int = 300,
        random_state: int = 42,
    ):
        if n_clusters < 2:
            raise ValueError(
                "n_clusters must be at least 2."
            )

        self.n_clusters = n_clusters

        self.model = KMeans(
            n_clusters=n_clusters,
            n_init=n_init,
            max_iter=max_iter,
            random_state=random_state,
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
                "Run ML preprocessing first."
            )

        values = X.to_numpy(dtype=float)

        if not np.isfinite(values).all():
            raise ValueError(
                "Input contains infinite values."
            )

    # --------------------------------------------------
    # Fit
    # --------------------------------------------------

    def fit(
        self,
        X: pd.DataFrame,
    ):
        """
        Train K-Means and identify peer clusters.
        """

        self._validate_input(X)

        self.feature_columns = list(
            X.columns
        )

        self.model.fit(X)

        self.is_fitted = True

        return self

    # --------------------------------------------------
    # Cluster prediction
    # --------------------------------------------------

    def predict(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Assign each record to a cluster.
        """

        self._check_fitted()

        self._validate_features(X)

        return self.model.predict(X)

    # --------------------------------------------------
    # Distance from cluster center
    # --------------------------------------------------

    def distance_to_cluster(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Calculate each record's distance from its
        assigned cluster center.

        A larger distance means the record is less
        representative of its peer group.

        This is contextual evidence, not a final anomaly score.
        """

        self._check_fitted()

        self._validate_features(X)

        cluster_labels = self.model.predict(X)

        centers = self.model.cluster_centers_

        distances = np.linalg.norm(
            X.to_numpy(dtype=float)
            - centers[cluster_labels],
            axis=1,
        )

        return distances

    # --------------------------------------------------
    # Normalized cluster-distance score
    # --------------------------------------------------

    def cluster_anomaly_score(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Convert distance from cluster center into
        a 0-1 contextual anomaly score.

        Higher value = farther from peer-group center.
        """

        distances = self.distance_to_cluster(X)

        min_distance = distances.min()
        max_distance = distances.max()

        if max_distance == min_distance:
            return np.zeros(
                len(distances),
                dtype=float,
            )

        scores = (
            (distances - min_distance)
            / (max_distance - min_distance)
        )

        return scores

    # --------------------------------------------------
    # Complete prediction
    # --------------------------------------------------

    def predict_with_evidence(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Return cluster assignment and peer-group evidence.
        """

        self._check_fitted()

        self._validate_features(X)

        cluster_labels = self.predict(X)

        distances = self.distance_to_cluster(X)

        scores = self.cluster_anomaly_score(X)

        result = pd.DataFrame(
            {
                "cluster_id": cluster_labels,
                "cluster_distance": distances,
                "cluster_anomaly_score": scores,
            },
            index=X.index,
        )

        return result

    # --------------------------------------------------
    # Cluster summary
    # --------------------------------------------------

    def get_cluster_summary(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Return the number of records in each cluster.
        """

        self._check_fitted()

        labels = self.predict(X)

        summary = (
            pd.Series(
                labels,
                name="cluster_id",
            )
            .value_counts()
            .sort_index()
            .rename("record_count")
            .reset_index()
        )

        return summary

    # --------------------------------------------------
    # Fit + predict
    # --------------------------------------------------

    def fit_predict(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Train K-Means and return cluster evidence.
        """

        self.fit(X)

        return self.predict_with_evidence(X)

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
                "K-Means has not been fitted. "
                "Call fit() first."
            )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def save(
        self,
        path: str = "models/artifacts/kmeans.joblib",
    ):
        """
        Save the trained clustering model.
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
    # Load
    # --------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str = "models/artifacts/kmeans.joblib",
    ):
        """
        Load a previously trained K-Means detector.
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
                "Loaded object is not a "
                "KMeansClusterDetector."
            )

        return detector

    # --------------------------------------------------
    # Model information
    # --------------------------------------------------

    def get_model_info(self) -> dict:
        """Return model metadata."""

        return {
            "model": "K-Means",
            "n_clusters": self.n_clusters,
            "n_init": self.model.n_init,
            "max_iter": self.model.max_iter,
            "random_state":
                self.model.random_state,
            "feature_count":
                len(self.feature_columns)
                if self.feature_columns
                else 0,
            "feature_columns":
                self.feature_columns,
            "is_fitted": self.is_fitted,
        }