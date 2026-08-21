"""
Normalize ML -> RAG records.

The normalizer preserves evidence supplied by the ML pipeline.

It does NOT:
- invent anomaly scores
- invent ML features
- invent root causes
- invent Bayesian values
"""

from typing import Any, Dict, List


class RAGInputNormalizer:

    # =========================================================
    # Normalize Complete Input
    # =========================================================

    def normalize(
        self,
        rag_input: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        if not isinstance(
            rag_input,
            list
        ):

            raise TypeError(
                "RAG input must be a list."
            )

        normalized_records = []

        for record in rag_input:

            normalized_records.append(
                self._normalize_record(
                    record
                )
            )

        return {
            "records": normalized_records,
            "record_count": len(
                normalized_records
            )
        }

    # =========================================================
    # Normalize One Record
    # =========================================================

    def _normalize_record(
        self,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:

        dataset_type = record.get(
            "dataset_type"
        )

        record_id = str(
            record.get(
                "record_id",
                "unknown"
            )
        )

        detection = record.get(
            "detection_summary",
            {}
        )

        rule_evidence = record.get(
            "rule_based_evidence",
            []
        )

        ml_evidence = record.get(
            "ml_based_evidence"
        )

        behavior_evidence = record.get(
            "behavior_based_evidence",
            {}
        )

        bayesian_evidence = record.get(
            "bayesian_evidence",
            {}
        )

        context = record.get(
            "record_context",
            {}
        )

        sla = record.get(
            "sla"
        )

        source_explanation = record.get(
            "source_explanation",
            {}
        )

        # -----------------------------------------------------
        # Preserve complete source evidence
        # -----------------------------------------------------

        source_evidence = record.get(
            "source_evidence",
            {}
        )

        return {

            "dataset_type":
                dataset_type,

            "record_id":
                record_id,

            "detection_summary":
                detection,

            "rule_based_evidence":
                rule_evidence,

            "ml_based_evidence":
                self._normalize_ml_evidence(
                    ml_evidence
                ),

            "behavior_based_evidence":
                behavior_evidence,

            "bayesian_evidence":
                bayesian_evidence,

            "record_context":
                context,

            "sla":
                sla,

            "source_explanation":
                source_explanation,

            "source_evidence":
                source_evidence
        }

    # =========================================================
    # Normalize ML Evidence
    # =========================================================

    def _normalize_ml_evidence(
        self,
        ml_evidence: Any
    ):

        if ml_evidence is None:

            return None

        if not isinstance(
            ml_evidence,
            dict
        ):

            raise TypeError(
                "ml_based_evidence must be "
                "an object or null."
            )

        return dict(
            ml_evidence
        )

    # =========================================================
    # Evidence Summary
    # =========================================================

    def extract_evidence_summary(
        self,
        normalized_record: Dict[str, Any]
    ) -> Dict[str, Any]:

        detection = normalized_record.get(
            "detection_summary",
            {}
        )

        rule_evidence = normalized_record.get(
            "rule_based_evidence",
            []
        )

        ml_evidence = normalized_record.get(
            "ml_based_evidence"
        )

        behavior_evidence = normalized_record.get(
            "behavior_based_evidence",
            {}
        )

        bayesian_evidence = normalized_record.get(
            "bayesian_evidence",
            {}
        )

        # -----------------------------------------------------
        # Rule names
        # -----------------------------------------------------

        rule_names = []

        for rule in rule_evidence:

            if not isinstance(
                rule,
                dict
            ):
                continue

            name = rule.get(
                "rule_name"
            )

            if name:

                rule_names.append(
                    str(name)
                )

        # -----------------------------------------------------
        # ML features
        # -----------------------------------------------------

        ml_features = []

        if isinstance(
            ml_evidence,
            dict
        ):

            features = ml_evidence.get(
                "contributing_features",
                []
            )

            if isinstance(
                features,
                list
            ):

                for feature in features:

                    if isinstance(
                        feature,
                        dict
                    ):

                        name = feature.get(
                            "feature"
                        )

                        if name:

                            ml_features.append(
                                str(name)
                            )

                    elif isinstance(
                        feature,
                        str
                    ):

                        ml_features.append(
                            feature
                        )

        return {

            "rule_anomaly":
                detection.get(
                    "rule_anomaly"
                ),

            "ml_anomaly":
                detection.get(
                    "ml_anomaly"
                ),

            "behavior_anomaly":
                detection.get(
                    "behavior_anomaly"
                ),

            "bayesian_anomaly":
                detection.get(
                    "bayesian_anomaly"
                ),

            "ml_evidence_available":
                ml_evidence is not None,

            "rule_names":
                rule_names,

            "ml_features":
                ml_features,

            "bayesian_probability":
                bayesian_evidence.get(
                    "probability"
                )
                if isinstance(
                    bayesian_evidence,
                    dict
                )
                else None,

            "bayesian_score":
                bayesian_evidence.get(
                    "score"
                )
                if isinstance(
                    bayesian_evidence,
                    dict
                )
                else None,

            "behavior_evidence":
                behavior_evidence
        }