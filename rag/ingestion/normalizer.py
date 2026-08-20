"""
Normalize validated ML model output before it enters
the RAG retrieval and XAI pipeline.

Important:
- Does not invent ML evidence.
- Preserves null ML evidence.
- Preserves original rule and ML evidence.
- Creates a consistent internal structure.
"""

from typing import Any, Dict, List


class RAGInputNormalizer:
    """
    Normalize validated ML/RAG input into a consistent
    internal representation.
    """

    def normalize(
        self,
        rag_input: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Normalize all anomaly records.

        Returns:

        {
            "records": [...],
            "record_count": int
        }
        """

        if not isinstance(
            rag_input,
            list
        ):

            raise TypeError(
                "RAG input must be a list "
                "of anomaly records."
            )

        normalized_records = []

        for record in rag_input:

            normalized_record = (
                self._normalize_record(
                    record
                )
            )

            normalized_records.append(
                normalized_record
            )

        return {
            "records": normalized_records,
            "record_count": len(
                normalized_records
            )
        }

    # =====================================================
    # Normalize Individual Record
    # =====================================================

    def _normalize_record(
        self,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize one anomaly record.
        """

        # -------------------------------------------------
        # Basic identity
        # -------------------------------------------------

        dataset_type = record.get(
            "dataset_type"
        )

        record_id = record.get(
            "record_id"
        )

        # -------------------------------------------------
        # Detection summary
        # -------------------------------------------------

        detection_summary = record.get(
            "detection_summary",
            {}
        )

        # -------------------------------------------------
        # Rule evidence
        # -------------------------------------------------

        rule_evidence = record.get(
            "rule_based_evidence",
            []
        )

        if rule_evidence is None:

            rule_evidence = []

        # -------------------------------------------------
        # ML evidence
        #
        # IMPORTANT:
        # None means ML evidence was not provided.
        #
        # Do NOT convert None into:
        # is_anomaly = false
        # -------------------------------------------------

        ml_evidence = record.get(
            "ml_based_evidence"
        )

        normalized_ml_evidence = (
            self._normalize_ml_evidence(
                ml_evidence
            )
        )

        # -------------------------------------------------
        # Record context
        # -------------------------------------------------

        record_context = record.get(
            "record_context",
            {}
        )

        if record_context is None:

            record_context = {}

        # -------------------------------------------------
        # SLA
        # -------------------------------------------------

        sla = record.get(
            "sla"
        )

        # -------------------------------------------------
        # Build normalized record
        # -------------------------------------------------

        return {
            "dataset_type": dataset_type,

            "record_id": record_id,

            "detection_summary": (
                detection_summary
            ),

            "rule_based_evidence": (
                rule_evidence
            ),

            "ml_based_evidence": (
                normalized_ml_evidence
            ),

            "record_context": (
                record_context
            ),

            "sla": sla
        }

    # =====================================================
    # Normalize ML Evidence
    # =====================================================

    def _normalize_ml_evidence(
        self,
        ml_evidence: Any
    ):
        """
        Normalize ML evidence.

        Returns None when the ML model did not provide
        evidence.

        Does not fabricate missing values.
        """

        # -------------------------------------------------
        # No ML evidence
        # -------------------------------------------------

        if ml_evidence is None:

            return None

        # -------------------------------------------------
        # ML evidence available
        # -------------------------------------------------

        if not isinstance(
            ml_evidence,
            dict
        ):

            raise TypeError(
                "ml_based_evidence must be "
                "an object or null."
            )

        # -------------------------------------------------
        # Preserve ML evidence exactly
        # while ensuring expected optional structures
        # are represented consistently.
        # -------------------------------------------------

        normalized = {
            "model": ml_evidence.get(
                "model"
            ),

            "is_anomaly": ml_evidence.get(
                "is_anomaly"
            ),

            "anomaly_score": ml_evidence.get(
                "anomaly_score"
            ),

            "contributing_features": (
                ml_evidence.get(
                    "contributing_features",
                    []
                )
            )
        }

        return normalized

    # =====================================================
    # Extract Evidence Summary
    # =====================================================

    def extract_evidence_summary(
        self,
        normalized_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract the evidence that will be useful
        for Query Builder, XAI and Generation.

        This does not generate an RCA.
        """

        rule_evidence = (
            normalized_record.get(
                "rule_based_evidence",
                []
            )
        )

        ml_evidence = (
            normalized_record.get(
                "ml_based_evidence"
            )
        )

        # -------------------------------------------------
        # Rule names
        # -------------------------------------------------

        rule_names = []

        for rule in rule_evidence:

            if not isinstance(
                rule,
                dict
            ):
                continue

            rule_name = rule.get(
                "rule_name"
            )

            if rule_name:

                rule_names.append(
                    rule_name
                )

        # -------------------------------------------------
        # ML features
        # -------------------------------------------------

        ml_features = []

        if isinstance(
            ml_evidence,
            dict
        ):

            features = ml_evidence.get(
                "contributing_features",
                []
            )

            for feature in features:

                if not isinstance(
                    feature,
                    dict
                ):
                    continue

                feature_name = feature.get(
                    "feature"
                )

                if feature_name:

                    ml_features.append(
                        feature_name
                    )

        # -------------------------------------------------
        # Detection sources
        # -------------------------------------------------

        detection_summary = (
            normalized_record.get(
                "detection_summary",
                {}
            )
        )

        rule_anomaly = detection_summary.get(
            "rule_anomaly"
        )

        ml_anomaly = detection_summary.get(
            "ml_anomaly"
        )

        # -------------------------------------------------
        # Evidence availability
        # -------------------------------------------------

        ml_evidence_available = (
            ml_evidence is not None
        )

        return {
            "rule_anomaly": rule_anomaly,

            "ml_anomaly": ml_anomaly,

            "ml_evidence_available": (
                ml_evidence_available
            ),

            "rule_names": rule_names,

            "ml_features": ml_features
        }