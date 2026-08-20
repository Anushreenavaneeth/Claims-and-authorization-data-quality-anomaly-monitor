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
        anomaly: Dict[str, Any]
    ) -> List[str]:
        """
        Extract important evidence terms from
        the ML anomaly record.

        These terms receive an additional ranking
        signal during retrieval.
        """

        terms = []

        # -------------------------------------------------
        # Dataset
        # -------------------------------------------------

        dataset_type = anomaly.get(
            "dataset_type"
        )

        if dataset_type:
            terms.append(
                str(dataset_type)
            )

        # -------------------------------------------------
        # Rule-Based Evidence
        # -------------------------------------------------

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

                if rule_name:
                    terms.append(
                        str(rule_name)
                    )

        # -------------------------------------------------
        # ML Contributing Features
        # -------------------------------------------------

        ml_evidence = anomaly.get(
            "ml_based_evidence",
            {}
        )

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

                    if not isinstance(
                        feature,
                        dict
                    ):
                        continue

                    feature_name = feature.get(
                        "feature"
                    )

                    if feature_name:
                        terms.append(
                            str(feature_name)
                        )

        # -------------------------------------------------
        # Record Context
        # -------------------------------------------------

        record_context = anomaly.get(
            "record_context",
            {}
        )

        if isinstance(
            record_context,
            dict
        ):

            context_fields = [
                "service_type",
                "procedure_code",
                "authorization_status",
                "authorization_type",
                "urgency",
                "submission_channel"
            ]

            for field in context_fields:

                value = record_context.get(
                    field
                )

                if value is not None:

                    terms.append(
                        str(value)
                    )

        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        unique_terms = []

        seen = set()

        for term in terms:

            normalized = (
                term.strip().lower()
            )

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            unique_terms.append(
                term.strip()
            )

        return unique_terms

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
            len(evidence_terms)
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

        # -------------------------------------------------
        # First pass:
        # Prefer different sources
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Second pass:
        # Fill remaining slots
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Final ordering
        # -------------------------------------------------

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

        3. Normalized ingestion object containing:
           {
               "records": [...],
               "record_count": ...
           }
        """

        # -------------------------------------------------
        # Normalize Input
        # -------------------------------------------------

        if isinstance(
            rag_input,
            dict
        ):

            # Complete normalized ingestion result
            if (
                "records" in rag_input
                and isinstance(
                    rag_input["records"],
                    list
                )
            ):

                anomaly_records = (
                    rag_input["records"]
                )

            # Single anomaly record
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

        # -------------------------------------------------
        # Build Queries
        #
        # IMPORTANT:
        # Pass anomaly_records, not rag_input.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Process Each Anomaly
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Final Response
        # -------------------------------------------------

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