# models/ml_adapters.py

from typing import Dict, Any, List

import pandas as pd


class MLAdapters:
    """
    Normalizes Isolation Forest and K-Means outputs
    into a common per-record structure.

    This class does NOT perform anomaly detection.
    It only converts model outputs into a standard format.
    """

    # ==================================================
    # ISOLATION FOREST
    # ==================================================

    @staticmethod
    def normalize_isolation_results(
        results,
        expected_records: int,
    ) -> List[Dict[str, Any]]:
        """
        Normalize Isolation Forest output.

        IsolationForestDetector.predict() returns:

            is_anomaly
            prediction
            anomaly_score

        as dataframe columns.
        """

        # ----------------------------------------------
        # DataFrame output
        # ----------------------------------------------

        if isinstance(results, pd.DataFrame):

            required_columns = [
                "is_anomaly",
                "prediction",
                "anomaly_score",
            ]

            missing = [
                column
                for column in required_columns
                if column not in results.columns
            ]

            if missing:

                raise ValueError(
                    "Isolation Forest result is missing "
                    f"columns: {missing}"
                )

            if len(results) != expected_records:

                raise ValueError(
                    "Isolation Forest result count "
                    "does not match dataset size."
                )

            normalized = []

            for row_index, row in results.iterrows():

                normalized.append(
                    {
                        "row_index":
                            int(row_index),

                        "is_anomaly":
                            bool(
                                row["is_anomaly"]
                            ),

                        "prediction":
                            int(
                                row["prediction"]
                            ),

                        "anomaly_score":
                            float(
                                row["anomaly_score"]
                            ),
                    }
                )

            return normalized

        # ----------------------------------------------
        # Dictionary output
        # ----------------------------------------------

        if isinstance(results, dict):

            is_anomaly = results.get(
                "is_anomaly",
                [],
            )

            predictions = results.get(
                "prediction",
                [],
            )

            scores = results.get(
                "anomaly_score",
                [],
            )

            if len(is_anomaly) != expected_records:

                raise ValueError(
                    "Isolation Forest result count "
                    "does not match dataset size."
                )

            normalized = []

            for i in range(
                expected_records
            ):

                normalized.append(
                    {
                        "row_index": i,

                        "is_anomaly":
                            bool(
                                is_anomaly[i]
                            ),

                        "prediction":
                            int(
                                predictions[i]
                            ),

                        "anomaly_score":
                            float(
                                scores[i]
                            ),
                    }
                )

            return normalized

        raise TypeError(
            "Unsupported Isolation Forest "
            "result type: "
            f"{type(results)}"
        )

    # ==================================================
    # K-MEANS
    # ==================================================

    @staticmethod
    def normalize_cluster_results(
        results,
        expected_records: int,
    ) -> List[Dict[str, Any]]:
        """
        Normalize K-Means output.

        Supports both DataFrame and dictionary outputs.
        """

        # ----------------------------------------------
        # DataFrame output
        # ----------------------------------------------

        if isinstance(results, pd.DataFrame):

            required_columns = [
                "cluster_id",
                "cluster_distance",
                "cluster_anomaly_score",
            ]

            missing = [
                column
                for column in required_columns
                if column not in results.columns
            ]

            if missing:

                raise ValueError(
                    "K-Means result is missing "
                    f"columns: {missing}"
                )

            if len(results) != expected_records:

                raise ValueError(
                    "K-Means result count "
                    "does not match dataset size."
                )

            normalized = []

            for row_index, row in results.iterrows():

                cluster_score = float(
                    row[
                        "cluster_anomaly_score"
                    ]
                )

                # If the model already provides
                # is_anomaly, use it.
                if "is_anomaly" in results.columns:

                    is_anomaly = bool(
                        row["is_anomaly"]
                    )

                else:

                    # We don't invent a new threshold here.
                    # The model's own anomaly score is
                    # preserved.
                    is_anomaly = False

                normalized.append(
                    {
                        "row_index":
                            int(row_index),

                        "is_anomaly":
                            is_anomaly,

                        "cluster_id":
                            int(row["cluster_id"]),

                        "cluster_distance":
                            float(
                                row[
                                    "cluster_distance"
                                ]
                            ),

                        "cluster_anomaly_score":
                            cluster_score,
                    }
                )

            return normalized

        # ----------------------------------------------
        # Dictionary output
        # ----------------------------------------------

        if isinstance(results, dict):

            cluster_ids = results.get(
                "cluster_id",
                [],
            )

            distances = results.get(
                "cluster_distance",
                [],
            )

            anomaly_scores = results.get(
                "cluster_anomaly_score",
                [],
            )

            is_anomaly = results.get(
                "is_anomaly",
                [],
            )

            if len(cluster_ids) != expected_records:

                raise ValueError(
                    "K-Means result count "
                    "does not match dataset size."
                )

            normalized = []

            for i in range(
                expected_records
            ):

                normalized.append(
                    {
                        "row_index": i,

                        "is_anomaly":
                            bool(
                                is_anomaly[i]
                            )
                            if len(
                                is_anomaly
                            ) > i
                            else False,

                        "cluster_id":
                            cluster_ids[i],

                        "cluster_distance":
                            float(
                                distances[i]
                            ),

                        "cluster_anomaly_score":
                            float(
                                anomaly_scores[i]
                            ),
                    }
                )

            return normalized

        raise TypeError(
            "Unsupported K-Means "
            f"result type: {type(results)}"
        )

    # ==================================================
    # MERGE ML RESULTS
    # ==================================================

    @staticmethod
    def merge_ml_results(
        isolation_results: List[Dict[str, Any]],
        cluster_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge Isolation Forest and K-Means
        results by row index.
        """

        if len(isolation_results) != len(
            cluster_results
        ):

            raise ValueError(
                "Isolation Forest and K-Means "
                "result counts do not match."
            )

        merged = []

        for i in range(
            len(isolation_results)
        ):

            isolation = (
                isolation_results[i]
            )

            cluster = (
                cluster_results[i]
            )

            merged.append(
                {
                    "row_index": i,

                    "isolation_forest": {

                        "is_anomaly":
                            isolation[
                                "is_anomaly"
                            ],

                        "prediction":
                            isolation[
                                "prediction"
                            ],

                        "anomaly_score":
                            isolation[
                                "anomaly_score"
                            ],
                    },

                    "clustering": {

                        "is_anomaly":
                            cluster[
                                "is_anomaly"
                            ],

                        "cluster_id":
                            cluster[
                                "cluster_id"
                            ],

                        "cluster_distance":
                            cluster[
                                "cluster_distance"
                            ],

                        "anomaly_score":
                            cluster[
                                "cluster_anomaly_score"
                            ],
                    },
                }
            )

        return merged