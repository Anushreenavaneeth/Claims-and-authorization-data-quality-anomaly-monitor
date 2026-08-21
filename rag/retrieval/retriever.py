"""
Main RAG retrieval component.

Hybrid retrieval:

ML anomaly JSON
      ↓
Query Builder
      ↓
Semantic Vector Search
      +
Evidence Matching
      ↓
Hybrid Ranking
      ↓
Source Diversification
      ↓
Top-K Knowledge
"""

import re

from typing import Any, Dict, List, Set

from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_MODEL_NAME,
    TOP_K,
    SIMILARITY_THRESHOLD
)

from .vector_store import VectorStore
from .query_builder import QueryBuilder


class Retriever:
    """
    Retrieves relevant knowledge for each anomaly record.

    Ranking combines:

    1. Semantic similarity
    2. Exact evidence matching
    3. Source diversification
    """

    def __init__(
        self,
        top_k: int = TOP_K,
        similarity_threshold: float = SIMILARITY_THRESHOLD
    ):

        self.top_k = top_k

        self.similarity_threshold = (
            similarity_threshold
        )

        print(
            f"Loading retrieval embedding model: "
            f"{EMBEDDING_MODEL_NAME}"
        )

        self.embedding_model = (
            SentenceTransformer(
                EMBEDDING_MODEL_NAME
            )
        )

        self.vector_store = VectorStore()

        self.query_builder = QueryBuilder()

        print(
            "Retriever initialized successfully."
        )

    # =====================================================
    # Evidence Extraction
    # =====================================================

    def _extract_evidence_terms(
        self,
        anomaly
    ):

        """
        Extract retrieval evidence terms from the
        normalized anomaly record.

        Supports:

        - Dataset
        - Detection type
        - Rule-based evidence
        - ML evidence
        - Bayesian evidence
        - Behavioral evidence
        - Source explanation
        """

        terms = []

        # =================================================
        # Helper
        # =================================================

        def add_term(value):

            if value is None:
                return

            if isinstance(
                value,
                bool
            ):

                if value:
                    value = str(
                        value
                    ).lower()

                else:
                    return

            value = str(
                value
            ).strip()

            if not value:
                return

            if value.lower() in {
                "none",
                "null",
                "false",
                "unknown",
                "nan"
            }:
                return

            if value not in terms:

                terms.append(
                    value
                )

        # =================================================
        # Dataset
        # =================================================

        add_term(
            anomaly.get(
                "dataset_type"
            )
        )

        # =================================================
        # Detection Summary
        # =================================================

        detection = anomaly.get(
            "detection_summary",
            {}
        )

        if isinstance(
            detection,
            dict
        ):

            anomaly_type = detection.get(
                "anomaly_type"
            )

            if anomaly_type:

                for value in str(
                    anomaly_type
                ).split(","):

                    add_term(
                        value.strip()
                    )

        # =================================================
        # Rule-Based Evidence
        # =================================================

        rule_evidence = anomaly.get(
            "rule_based_evidence",
            []
        )

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

                add_term(
                    rule_name
                )

        # =================================================
        # ML Evidence
        # =================================================

        ml_evidence = anomaly.get(
            "ml_based_evidence",
            {}
        )

        if isinstance(
            ml_evidence,
            dict
        ):

            # ML model name

            add_term(
                ml_evidence.get(
                    "model"
                )
            )

            # Contributing features

            features = ml_evidence.get(
                "contributing_features",
                []
            )

            if isinstance(
                features,
                list
            ):

                for feature in features:

                    add_term(
                        feature
                    )

            # ML evidence types

            types = ml_evidence.get(
                "types"
            )

            if types:

                for value in str(
                    types
                ).split(","):

                    add_term(
                        value.strip()
                    )

            # ML summary

            summary = ml_evidence.get(
                "summary"
            )

            if summary:

                summary_lower = str(
                    summary
                ).lower()

                if "isolation forest" in summary_lower:

                    add_term(
                        "Isolation Forest"
                    )

                if "xgboost" in summary_lower:

                    add_term(
                        "XGBoost"
                    )

                if "random forest" in summary_lower:

                    add_term(
                        "Random Forest"
                    )

                if "outlier" in summary_lower:

                    add_term(
                        "outlier"
                    )

        # =================================================
        # Bayesian Evidence
        # =================================================

        bayesian_evidence = anomaly.get(
            "bayesian_evidence",
            {}
        )

        if isinstance(
            bayesian_evidence,
            dict
        ):

            if bayesian_evidence.get(
                "anomaly"
            ) is True:

                add_term(
                    "bayesian"
                )

        # =================================================
        # Behavioral Evidence
        # =================================================

        behavioral_evidence = anomaly.get(
            "behavioral_evidence",
            []
        )

        if isinstance(
            behavioral_evidence,
            list
        ):

            behavioral_detected = False

            for item in behavioral_evidence:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if item.get(
                    "detected"
                ) is True:

                    behavioral_detected = True

                evidence_type = item.get(
                    "type"
                )

                if evidence_type:

                    add_term(
                        evidence_type
                    )

                description = item.get(
                    "description"
                )

                if description:

                    description_lower = (
                        str(
                            description
                        ).lower()
                    )

                    if "cost per claim" in description_lower:

                        add_term(
                            "cost_per_claim"
                        )

                    if "historical" in description_lower:

                        add_term(
                            "historical_behavior"
                        )

                    if "behavior" in description_lower:

                        add_term(
                            "behavior"
                        )

            if behavioral_detected:

                add_term(
                    "behavioral"
                )

        # =================================================
        # Source Explanation
        # =================================================

        source_explanation = anomaly.get(
            "source_explanation",
            {}
        )

        if isinstance(
            source_explanation,
            dict
        ):

            explanation = source_explanation.get(
                "explanation"
            )

            if explanation:

                explanation_lower = str(
                    explanation
                ).lower()

                # -----------------------------
                # Missing data
                # -----------------------------

                if "missing" in explanation_lower:

                    add_term(
                        "missing"
                    )

                    add_term(
                        "completeness"
                    )

                # -----------------------------
                # Suppressed values
                # -----------------------------

                if "suppressed" in explanation_lower:

                    add_term(
                        "suppressed"
                    )

                # -----------------------------
                # Cost per claim
                # -----------------------------

                if "cost per claim" in explanation_lower:

                    add_term(
                        "cost_per_claim"
                    )

                # -----------------------------
                # Behavioral change
                # -----------------------------

                if "behavior" in explanation_lower:

                    add_term(
                        "behavior"
                    )

                    add_term(
                        "historical_behavior"
                    )

                # -----------------------------
                # Provider
                # -----------------------------

                if "provider" in explanation_lower:

                    add_term(
                        "provider"
                    )

                # -----------------------------
                # Authorization
                # -----------------------------

                if "authorization" in explanation_lower:

                    add_term(
                        "authorization"
                    )

                # -----------------------------
                # Claims
                # -----------------------------

                if "claim" in explanation_lower:

                    add_term(
                        "claims"
                    )

                # -----------------------------
                # Pharmacy
                # -----------------------------

                if "pharmacy" in explanation_lower:

                    add_term(
                        "pharmacy"
                    )

        # =================================================
        # Context For RAG
        # =================================================

        context_for_rag = anomaly.get(
            "record_context",
            {}
        )

        if isinstance(
            context_for_rag,
            dict
        ):

            rag_context = context_for_rag.get(
                "context_for_rag"
            )

            if rag_context:

                context_lower = str(
                    rag_context
                ).lower()

                if "cost per claim" in context_lower:

                    add_term(
                        "cost_per_claim"
                    )

                if "behavior" in context_lower:

                    add_term(
                        "behavior"
                    )

                if "historical" in context_lower:

                    add_term(
                        "historical_behavior"
                    )

                if "missing" in context_lower:

                    add_term(
                        "missing"
                    )

                if "suppressed" in context_lower:

                    add_term(
                        "suppressed"
                    )

        # =================================================
        # Remove duplicates
        # =================================================

        normalized_terms = []

        for term in terms:

            term = str(
                term
            ).strip()

            if not term:
                continue

            if term not in normalized_terms:

                normalized_terms.append(
                    term
                )

        return normalized_terms

    # =====================================================
    # Normalize Text
    # =====================================================

    def _normalize_text(
        self,
        text: str
    ) -> str:

        """
        Normalize text for evidence matching.
        """

        text = str(
            text
        ).lower()

        text = re.sub(
            r"[^a-z0-9_]+",
            " ",
            text
        )

        return text

    # =====================================================
    # Evidence Matching Score
    # =====================================================

    def _evidence_score(
        self,
        result: Dict[str, Any],
        evidence_terms: List[str]
    ) -> float:

        """
        Calculate evidence matching score.

        Exact evidence terms receive an additional
        ranking signal.
        """

        if not evidence_terms:

            return 0.0

        text = result.get(
            "text",
            ""
        )

        normalized_text = (
            self._normalize_text(
                text
            )
        )

        if not normalized_text:

            return 0.0

        matched = 0

        for term in evidence_terms:

            normalized_term = (
                self._normalize_text(
                    term
                )
            )

            if not normalized_term:

                continue

            if normalized_term in normalized_text:

                matched += 1

        if matched == 0:

            return 0.0

        return (
            matched /
            len(
                evidence_terms
            )
        )

    # =====================================================
    # Hybrid Score
    # =====================================================

    def _calculate_hybrid_score(
        self,
        result: Dict[str, Any],
        evidence_terms: List[str]
    ) -> Dict[str, float]:

        """
        Combine:

        Semantic similarity = 70%
        Evidence matching   = 30%
        """

        semantic_score = float(
            result.get(
                "similarity_score",
                0.0
            )
        )

        evidence_score = (
            self._evidence_score(
                result,
                evidence_terms
            )
        )

        hybrid_score = (
            0.70 * semantic_score
            +
            0.30 * evidence_score
        )

        return {
            "semantic_score": semantic_score,
            "evidence_score": evidence_score,
            "hybrid_score": hybrid_score
        }

    # =====================================================
    # Source Diversification
    # =====================================================

    def _diversify_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        """
        Prefer different knowledge sources while
        preserving high-relevance results.
        """

        if not results:

            return []

        sorted_results = sorted(
            results,
            key=lambda x: x.get(
                "hybrid_score",
                0.0
            ),
            reverse=True
        )

        selected = []

        selected_keys: Set = set()

        selected_sources: Set = set()

        # =================================================
        # First pass
        # Prefer different sources
        # =================================================

        for result in sorted_results:

            metadata = result.get(
                "metadata",
                {}
            )

            source = metadata.get(
                "source",
                "unknown"
            )

            chunk_id = metadata.get(
                "chunk_id"
            )

            text = result.get(
                "text",
                ""
            )

            key = (
                source,
                chunk_id,
                text
            )

            if key in selected_keys:

                continue

            if source in selected_sources:

                continue

            selected.append(
                result
            )

            selected_keys.add(
                key
            )

            selected_sources.add(
                source
            )

            if len(selected) >= self.top_k:

                break

        # =================================================
        # Second pass
        # Fill remaining slots
        # =================================================

        if len(selected) < self.top_k:

            for result in sorted_results:

                metadata = result.get(
                    "metadata",
                    {}
                )

                source = metadata.get(
                    "source",
                    "unknown"
                )

                chunk_id = metadata.get(
                    "chunk_id"
                )

                text = result.get(
                    "text",
                    ""
                )

                key = (
                    source,
                    chunk_id,
                    text
                )

                if key in selected_keys:

                    continue

                selected.append(
                    result
                )

                selected_keys.add(
                    key
                )

                if len(selected) >= self.top_k:

                    break

        # =================================================
        # Final ordering
        # =================================================

        selected.sort(
            key=lambda x: x.get(
                "hybrid_score",
                0.0
            ),
            reverse=True
        )

        return selected

    # =====================================================
    # Main Retrieval
    # =====================================================

    def retrieve(
        self,
        rag_input: Any
    ) -> Dict[str, Any]:

        """
        Retrieve knowledge separately for every
        ML anomaly record.

        Supports:

        1. Single anomaly dictionary

        2. List of anomaly dictionaries

        3. Normalized ingestion object:

           {
               "records": [...],
               "record_count": ...
           }
        """

        # =================================================
        # Normalize Input
        # =================================================

        if isinstance(
            rag_input,
            dict
        ):

            if (
                "records" in rag_input
                and isinstance(
                    rag_input[
                        "records"
                    ],
                    list
                )
            ):

                anomaly_records = (
                    rag_input[
                        "records"
                    ]
                )

            else:

                anomaly_records = [
                    rag_input
                ]

        elif isinstance(
            rag_input,
            list
        ):

            anomaly_records = rag_input

        else:

            raise TypeError(
                "RAG input must be a JSON "
                "list or dictionary."
            )

        # =================================================
        # Build Queries
        # =================================================

        queries = (
            self.query_builder.build_queries(
                anomaly_records
            )
        )

        if len(queries) != len(
            anomaly_records
        ):

            raise ValueError(
                "Number of generated queries "
                "does not match number of "
                "anomaly records."
            )

        anomaly_results = []

        # =================================================
        # Process Each Anomaly
        # =================================================

        for anomaly, query in zip(
            anomaly_records,
            queries
        ):

            if not isinstance(
                anomaly,
                dict
            ):

                continue

            if not query.strip():

                continue

            # ---------------------------------------------
            # Extract Evidence
            # ---------------------------------------------

            evidence_terms = (
                self._extract_evidence_terms(
                    anomaly
                )
            )

            # ---------------------------------------------
            # Query Embedding
            # ---------------------------------------------

            query_embedding = (
                self.embedding_model.encode(
                    query,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
            )

            # ---------------------------------------------
            # Candidate Retrieval
            # ---------------------------------------------

            candidate_k = max(
                self.top_k * 4,
                20
            )

            results = (
                self.vector_store.search(
                    query_embedding=query_embedding,
                    top_k=candidate_k,
                    similarity_threshold=(
                        self.similarity_threshold
                    )
                )
            )

            # ---------------------------------------------
            # Remove Duplicates
            # ---------------------------------------------

            unique_results = []

            seen = set()

            for result in results:

                metadata = result.get(
                    "metadata",
                    {}
                )

                key = (
                    metadata.get(
                        "source"
                    ),
                    metadata.get(
                        "chunk_id"
                    ),
                    result.get(
                        "text",
                        ""
                    )
                )

                if key in seen:

                    continue

                seen.add(
                    key
                )

                unique_results.append(
                    result
                )

            # ---------------------------------------------
            # Calculate Hybrid Scores
            # ---------------------------------------------

            for result in unique_results:

                scores = (
                    self._calculate_hybrid_score(
                        result,
                        evidence_terms
                    )
                )

                result[
                    "semantic_score"
                ] = scores[
                    "semantic_score"
                ]

                result[
                    "evidence_score"
                ] = scores[
                    "evidence_score"
                ]

                result[
                    "hybrid_score"
                ] = scores[
                    "hybrid_score"
                ]

            # ---------------------------------------------
            # Sort by Hybrid Score
            # ---------------------------------------------

            unique_results.sort(
                key=lambda x: x.get(
                    "hybrid_score",
                    0.0
                ),
                reverse=True
            )

            # ---------------------------------------------
            # Source Diversification
            # ---------------------------------------------

            final_results = (
                self._diversify_results(
                    unique_results
                )
            )

            # ---------------------------------------------
            # Record-Level Result
            # ---------------------------------------------

            anomaly_results.append(
                {
                    "record_id": anomaly.get(
                        "record_id",
                        "unknown"
                    ),

                    "dataset_type": anomaly.get(
                        "dataset_type",
                        "unknown"
                    ),

                    "query": query,

                    "evidence_terms": (
                        evidence_terms
                    ),

                    "results": final_results,

                    "result_count": len(
                        final_results
                    )
                }
            )

        # =================================================
        # Final Response
        # =================================================

        return {
            "records": anomaly_results,

            "record_count": len(
                anomaly_results
            )
        }

    # =====================================================
    # Generation / XAI Context
    # =====================================================

    def retrieve_text(
        self,
        rag_input: Any
    ) -> str:

        """
        Convert retrieval results into structured
        context for XAI and Generation.
        """

        retrieval_result = (
            self.retrieve(
                rag_input
            )
        )

        records = retrieval_result.get(
            "records",
            []
        )

        if not records:

            return (
                "No relevant knowledge was "
                "retrieved from the knowledge base."
            )

        context_parts = []

        for record in records:

            record_id = record.get(
                "record_id",
                "unknown"
            )

            dataset_type = record.get(
                "dataset_type",
                "unknown"
            )

            evidence_terms = record.get(
                "evidence_terms",
                []
            )

            context_parts.append(
                f"===== RECORD: {record_id} =====\n"
                f"Dataset: {dataset_type}\n"
                f"Evidence terms: "
                f"{', '.join(evidence_terms)}"
            )

            results = record.get(
                "results",
                []
            )

            if not results:

                context_parts.append(
                    "No relevant knowledge retrieved."
                )

                continue

            for index, result in enumerate(
                results,
                start=1
            ):

                metadata = result.get(
                    "metadata",
                    {}
                )

                source = metadata.get(
                    "source",
                    "unknown"
                )

                category = metadata.get(
                    "category",
                    "unknown"
                )

                semantic_score = result.get(
                    "semantic_score",
                    0.0
                )

                evidence_score = result.get(
                    "evidence_score",
                    0.0
                )

                hybrid_score = result.get(
                    "hybrid_score",
                    0.0
                )

                text = result.get(
                    "text",
                    ""
                )

                context_parts.append(
                    f"\n[Knowledge {index}]\n"
                    f"Source: {source}\n"
                    f"Category: {category}\n"
                    f"Semantic Score: "
                    f"{semantic_score:.4f}\n"
                    f"Evidence Score: "
                    f"{evidence_score:.4f}\n"
                    f"Hybrid Score: "
                    f"{hybrid_score:.4f}\n"
                    f"Content:\n{text}"
                )

        return "\n\n".join(
            context_parts
        )