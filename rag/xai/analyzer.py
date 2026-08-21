"""
Explainable AI analysis layer.

Flow:

ML Evidence
    +
Retrieved Knowledge
    ↓
Evidence Matching
    ↓
Explanation
    ↓
Likely Root Cause
    ↓
Recommendation Inputs

Supports:
- Authorization
- Claims
- Pharmacy
- Future datasets using the common RAG structure

Important:
This layer does NOT invent evidence.

ML output provides observed evidence.

Retrieved knowledge provides supporting domain knowledge.

The XAI layer combines both while preserving
the distinction between observed evidence and
supporting knowledge.
"""

from typing import Any, Dict, List

from .config import (
    EVIDENCE_SCORE_THRESHOLD,
    HYBRID_SCORE_THRESHOLD,
    MAX_SUPPORTING_SOURCES
)


class XAIAnalyzer:
    """
    Performs evidence-based analysis of an anomaly
    using ML output and retrieved knowledge.
    """

    # =====================================================
    # Main Analysis
    # =====================================================

    def analyze(
        self,
        anomaly: Dict[str, Any],
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze one normalized anomaly record.
        """

        record_id = anomaly.get(
            "record_id",
            "unknown"
        )

        dataset_type = anomaly.get(
            "dataset_type",
            "unknown"
        )

        # -------------------------------------------------
        # Extract observed ML evidence
        # -------------------------------------------------

        evidence = self._extract_evidence(
            anomaly
        )

        # -------------------------------------------------
        # Select relevant retrieved knowledge
        # -------------------------------------------------

        supporting_knowledge = (
            self._select_supporting_knowledge(
                retrieved_knowledge
            )
        )

        # -------------------------------------------------
        # Identify anomaly pattern
        # -------------------------------------------------

        anomaly_pattern = (
            self._identify_anomaly_pattern(
                anomaly,
                evidence,
                supporting_knowledge
            )
        )

        # -------------------------------------------------
        # Generate explanation
        # -------------------------------------------------

        explanation = (
            self._build_explanation(
                anomaly,
                evidence,
                anomaly_pattern
            )
        )

        # -------------------------------------------------
        # Identify likely root cause
        # -------------------------------------------------

        root_cause = (
            self._identify_root_cause(
                anomaly,
                evidence,
                supporting_knowledge,
                anomaly_pattern
            )
        )

        # -------------------------------------------------
        # Final result
        # -------------------------------------------------

        return {
            "record_id": record_id,

            "dataset_type": dataset_type,

            "xai_analysis": {
                "observed_evidence": evidence,

                "matched_anomaly_pattern": (
                    anomaly_pattern
                ),

                "explanation": explanation,

                "likely_root_cause": root_cause,

                "supporting_knowledge": (
                    supporting_knowledge
                )
            }
        }

    # =====================================================
    # Evidence Extraction
    # =====================================================

    def _extract_evidence(
        self,
        anomaly: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract factual observed evidence.

        Supports both:

        1. Structured ML evidence
        2. Source explanation supplied by ML model

        The source explanation is preserved as ML evidence.
        It is NOT treated as retrieved knowledge.
        """

        detection = anomaly.get(
            "detection_summary",
            {}
        )

        rule_evidence = anomaly.get(
            "rule_based_evidence",
            []
        )

        ml_evidence = anomaly.get(
            "ml_based_evidence"
        )

        record_context = anomaly.get(
            "record_context",
            {}
        )

        source_explanation = anomaly.get(
            "source_explanation",
            {}
        )

        # =================================================
        # Rule Evidence
        # =================================================

        rules = []

        if isinstance(
            rule_evidence,
            list
        ):

            for rule in rule_evidence:

                if not isinstance(
                    rule,
                    dict
                ):
                    continue

                rule_name = rule.get(
                    "rule_name"
                )

                status = rule.get(
                    "status"
                )

                if rule_name:

                    rules.append(
                        {
                            "rule_name": rule_name,
                            "status": status
                        }
                    )

        # =================================================
        # ML Evidence
        # =================================================

        ml_features = []

        ml_anomaly_score = None

        ml_model = None

        ml_prediction = None

        ml_is_anomaly = None

        if isinstance(
            ml_evidence,
            dict
        ):

            ml_model = ml_evidence.get(
                "model"
            )

            ml_anomaly_score = (
                ml_evidence.get(
                    "anomaly_score"
                )
            )

            ml_prediction = (
                ml_evidence.get(
                    "prediction"
                )
            )

            ml_is_anomaly = (
                ml_evidence.get(
                    "is_anomaly"
                )
            )

            features = (
                ml_evidence.get(
                    "contributing_features",
                    []
                )
            )

            if isinstance(
                features,
                list
            ):

                for feature in features:

                    if not isinstance(
                        feature,
                        dict
                    ):
                        continue

                    ml_features.append(
                        feature
                    )

        # =================================================
        # Source Explanation
        # =================================================

        source_explanation_data = {}

        if isinstance(
            source_explanation,
            dict
        ):

            source_explanation_data = {
                key: value
                for key, value
                in source_explanation.items()
                if value is not None
            }

        # =================================================
        # Return Observed Evidence
        # =================================================

        return {
            "final_anomaly": detection.get(
                "final_anomaly"
            ),

            "final_severity": detection.get(
                "final_severity"
            ),

            "final_risk_score": detection.get(
                "final_risk_score"
            ),

            "rule_anomaly": detection.get(
                "rule_anomaly"
            ),

            "ml_anomaly": detection.get(
                "ml_anomaly"
            ),

            "rules": rules,

            "ml_model": ml_model,

            "ml_anomaly_score": (
                ml_anomaly_score
            ),

            "ml_prediction": ml_prediction,

            "ml_features": ml_features,

            "record_context": record_context,

            # -------------------------------------------------
            # Claims / future ML explanation
            # -------------------------------------------------

            "source_explanation": (
                source_explanation_data
            )
        }

    # =====================================================
    # Supporting Knowledge Selection
    # =====================================================

    def _select_supporting_knowledge(
        self,
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Select knowledge chunks with sufficient relevance.
        """

        supporting = []

        seen_sources = set()

        if not isinstance(
            retrieved_knowledge,
            list
        ):
            return supporting

        for result in retrieved_knowledge:

            if not isinstance(
                result,
                dict
            ):
                continue

            hybrid_score = float(
                result.get(
                    "hybrid_score",
                    result.get(
                        "similarity_score",
                        0.0
                    )
                )
            )

            evidence_score = float(
                result.get(
                    "evidence_score",
                    0.0
                )
            )

            if (
                hybrid_score
                <
                HYBRID_SCORE_THRESHOLD
                and
                evidence_score
                <
                EVIDENCE_SCORE_THRESHOLD
            ):
                continue

            metadata = result.get(
                "metadata",
                {}
            )

            if not isinstance(
                metadata,
                dict
            ):
                metadata = {}

            source = metadata.get(
                "source",
                "unknown"
            )

            if source in seen_sources:
                continue

            seen_sources.add(
                source
            )

            supporting.append(
                {
                    "source": source,

                    "category": metadata.get(
                        "category",
                        "unknown"
                    ),

                    "semantic_score": result.get(
                        "semantic_score"
                    ),

                    "evidence_score": (
                        result.get(
                            "evidence_score"
                        )
                    ),

                    "hybrid_score": (
                        result.get(
                            "hybrid_score"
                        )
                    ),

                    "content": result.get(
                        "text",
                        ""
                    )
                }
            )

            if len(
                supporting
            ) >= MAX_SUPPORTING_SOURCES:

                break

        return supporting

    # =====================================================
    # Identify Anomaly Pattern
    # =====================================================

    def _identify_anomaly_pattern(
        self,
        anomaly: Dict[str, Any],
        evidence: Dict[str, Any],
        supporting_knowledge: List[Dict[str, Any]]
    ) -> str:
        """
        Identify the most meaningful anomaly pattern.

        Priority:

        1. Exact rule evidence
        2. ML source explanation
        3. Structured ML features
        4. Relevant knowledge
        5. Generic anomaly
        """

        # -------------------------------------------------
        # Exact rule match
        # -------------------------------------------------

        rules = evidence.get(
            "rules",
            []
        )

        if rules:

            for rule in rules:

                if not isinstance(
                    rule,
                    dict
                ):
                    continue

                rule_name = rule.get(
                    "rule_name"
                )

                if rule_name:

                    return self._format_rule_name(
                        rule_name
                    )

        # -------------------------------------------------
        # ML source explanation
        # -------------------------------------------------

        source_explanation = evidence.get(
            "source_explanation",
            {}
        )

        if isinstance(
            source_explanation,
            dict
        ):

            explanation_text = (
                source_explanation.get(
                    "explanation",
                    ""
                )
            )

            if explanation_text:

                return self._extract_source_pattern(
                    explanation_text,
                    anomaly
                )

        # -------------------------------------------------
        # Structured ML features
        # -------------------------------------------------

        ml_features = evidence.get(
            "ml_features",
            []
        )

        if ml_features:

            names = []

            for feature in ml_features:

                if not isinstance(
                    feature,
                    dict
                ):
                    continue

                name = feature.get(
                    "feature"
                )

                if name:

                    names.append(
                        name.replace(
                            "_",
                            " "
                        )
                    )

            if names:

                return (
                    "ML anomaly involving "
                    + ", ".join(names)
                )

        # -------------------------------------------------
        # Knowledge fallback
        # -------------------------------------------------

        if supporting_knowledge:

            first = supporting_knowledge[0]

            source = first.get(
                "source",
                "unknown"
            )

            return (
                f"Pattern supported by {source}"
            )

        return (
            "No specific known anomaly pattern "
            "could be established from the available evidence."
        )

    # =====================================================
    # Extract Source Pattern
    # =====================================================

    def _extract_source_pattern(
        self,
        explanation_text: str,
        anomaly: Dict[str, Any]
    ) -> str:
        """
        Create a readable anomaly pattern from the
        ML model's own explanation.

        This does not invent a domain pattern.
        """

        dataset_type = anomaly.get(
            "dataset_type",
            "unknown"
        )

        # -------------------------------------------------
        # Claims
        # -------------------------------------------------

        if dataset_type.lower() == "claims":

            return (
                "Claims ML anomaly: unusual field values"
            )

        # -------------------------------------------------
        # Other datasets
        # -------------------------------------------------

        return (
            "ML-detected anomaly supported by "
            "source model evidence"
        )

    # =====================================================
    # Format Rule Name
    # =====================================================

    def _format_rule_name(
        self,
        rule_name: str
    ) -> str:
        """
        Convert technical rule names into readable text.
        """

        text = rule_name.replace(
            "_",
            " "
        )

        return text.strip().capitalize()

    # =====================================================
    # Build Explanation
    # =====================================================

    def _build_explanation(
        self,
        anomaly: Dict[str, Any],
        evidence: Dict[str, Any],
        anomaly_pattern: str
    ) -> str:
        """
        Build human-readable explanation from observed
        ML/rule evidence.

        Claims source explanation is treated as
        first-party ML evidence.
        """

        parts = []

        rules = evidence.get(
            "rules",
            []
        )

        ml_features = evidence.get(
            "ml_features",
            []
        )

        source_explanation = evidence.get(
            "source_explanation",
            {}
        )

        final_severity = evidence.get(
            "final_severity"
        )

        # =================================================
        # Rule Explanation
        # =================================================

        if rules:

            rule_names = [
                self._format_rule_name(
                    rule["rule_name"]
                )
                for rule in rules
                if rule.get(
                    "rule_name"
                )
            ]

            if rule_names:

                parts.append(
                    "The record was flagged because "
                    + ", ".join(
                        rule_names
                    )
                    + " "
                    + (
                        "rule violation was detected."
                        if len(
                            rule_names
                        ) == 1
                        else
                        "rule violations were detected."
                    )
                )

        # =================================================
        # Source ML Explanation
        # =================================================

        source_text = ""

        if isinstance(
            source_explanation,
            dict
        ):

            source_text = (
                source_explanation.get(
                    "explanation",
                    ""
                )
            )

        if source_text:

            parts.append(
                source_text
            )

        # =================================================
        # Structured ML Features
        # =================================================

        elif ml_features:

            feature_names = []

            for feature in ml_features:

                name = feature.get(
                    "feature"
                )

                if name:

                    readable = name.replace(
                        "_",
                        " "
                    )

                    feature_names.append(
                        readable
                    )

            if feature_names:

                parts.append(
                    "The ML model identified "
                    + ", ".join(
                        feature_names
                    )
                    + " as contributing factors."
                )

        # =================================================
        # ML Anomaly Without Explanation
        # =================================================

        elif evidence.get(
            "ml_anomaly"
        ) is True:

            parts.append(
                "The ML model also classified "
                "the record as anomalous."
            )

        # =================================================
        # Severity
        # =================================================

        if final_severity:

            parts.append(
                f"The resulting anomaly severity "
                f"is {final_severity}."
            )

        # =================================================
        # Fallback
        # =================================================

        if not parts:

            return (
                "The record was identified as anomalous, "
                "but the available evidence is insufficient "
                "to provide a more specific explanation."
            )

        return " ".join(
            parts
        )

    # =====================================================
    # Root Cause Identification
    # =====================================================

    def _identify_root_cause(
        self,
        anomaly: Dict[str, Any],
        evidence: Dict[str, Any],
        supporting_knowledge: List[Dict[str, Any]],
        anomaly_pattern: str
    ) -> Dict[str, Any]:
        """
        Identify likely root cause.

        Priority:

        1. Rule evidence
        2. ML source explanation / likely cause
        3. Structured ML features
        4. Insufficient evidence
        """

        rules = evidence.get(
            "rules",
            []
        )

        ml_features = evidence.get(
            "ml_features",
            []
        )

        source_explanation = evidence.get(
            "source_explanation",
            {}
        )

        # =================================================
        # Rule-specific Root Cause
        # =================================================

        if rules:

            primary_rule = rules[0].get(
                "rule_name"
            )

            if primary_rule:

                readable_rule = (
                    self._format_rule_name(
                        primary_rule
                    )
                )

                return {
                    "status": "likely",

                    "cause": (
                        "The available evidence is "
                        "consistent with a "
                        f"{readable_rule.lower()} "
                        "data-quality issue."
                    ),

                    "basis": [
                        primary_rule
                    ]
                }

        # =================================================
        # ML Source Likely Cause
        # =================================================

        if isinstance(
            source_explanation,
            dict
        ):

            likely_cause = (
                source_explanation.get(
                    "likely_cause"
                )
            )

            if likely_cause:

                return {
                    "status": "likely",

                    "cause": likely_cause,

                    "basis": [
                        "source_ml_explanation"
                    ]
                }

        # =================================================
        # Structured ML Features
        # =================================================

        if ml_features:

            feature_names = []

            for feature in ml_features:

                if not isinstance(
                    feature,
                    dict
                ):
                    continue

                name = feature.get(
                    "feature"
                )

                if name:

                    feature_names.append(
                        name.replace(
                            "_",
                            " "
                        )
                    )

            if feature_names:

                return {
                    "status": "likely",

                    "cause": (
                        "The available ML evidence "
                        "indicates abnormal behavior "
                        "associated with "
                        + ", ".join(
                            feature_names
                        )
                        + "."
                    ),

                    "basis": feature_names
                }

        # =================================================
        # Insufficient Evidence
        # =================================================

        return {
            "status": "undetermined",

            "cause": (
                "The available evidence is insufficient "
                "to determine a specific root cause."
            ),

            "basis": []
        }