"""
Match XAI evidence with retrieved healthcare knowledge.
"""

from typing import Any, Dict, List

from .config import (
    MIN_KNOWLEDGE_SCORE,
    MAX_SUPPORTING_KNOWLEDGE
)


class EvidenceMatcher:
    """
    Identifies the most relevant knowledge supporting
    the detected anomaly and XAI analysis.
    """

    def __init__(
        self,
        min_score: float = MIN_KNOWLEDGE_SCORE,
        max_results: int = MAX_SUPPORTING_KNOWLEDGE
    ):
        self.min_score = min_score
        self.max_results = max_results

    # =====================================================
    # Extract XAI Terms
    # =====================================================

    def _extract_evidence_terms(
        self,
        xai_result: Dict[str, Any]
    ) -> List[str]:
        """
        Extract important terms from the XAI result.
        """

        terms = []

        xai_analysis = xai_result.get(
            "xai_analysis",
            {}
        )

        # -------------------------------------------------
        # Matched anomaly pattern
        # -------------------------------------------------

        pattern = xai_analysis.get(
            "matched_anomaly_pattern"
        )

        if pattern:
            terms.append(
                str(pattern).lower()
            )

        # -------------------------------------------------
        # Root-cause basis
        # -------------------------------------------------

        root_cause = xai_analysis.get(
            "likely_root_cause",
            {}
        )

        basis = root_cause.get(
            "basis",
            []
        )

        if isinstance(
            basis,
            list
        ):

            for item in basis:

                if item:
                    terms.append(
                        str(item).lower()
                    )

        # -------------------------------------------------
        # Observed evidence
        # -------------------------------------------------

        observed = xai_analysis.get(
            "observed_evidence",
            {}
        )

        rules = observed.get(
            "rules",
            []
        )

        if isinstance(
            rules,
            list
        ):

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
                    terms.append(
                        str(
                            rule_name
                        ).lower()
                    )

        # -------------------------------------------------
        # Dataset type
        # -------------------------------------------------

        dataset_type = xai_result.get(
            "dataset_type"
        )

        if dataset_type:
            terms.append(
                str(
                    dataset_type
                ).lower()
            )

        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        unique_terms = []

        seen = set()

        for term in terms:

            normalized = term.strip()

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            unique_terms.append(
                normalized
            )

        return unique_terms

    # =====================================================
    # Match Knowledge
    # =====================================================

    def match(
        self,
        xai_result: Dict[str, Any],
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match retrieved knowledge against XAI evidence.
        """

        if not isinstance(
            xai_result,
            dict
        ):
            raise TypeError(
                "xai_result must be a dictionary."
            )

        if not isinstance(
            retrieved_knowledge,
            list
        ):
            raise TypeError(
                "retrieved_knowledge must be a list."
            )

        # -------------------------------------------------
        # Extract evidence terms
        # -------------------------------------------------

        evidence_terms = (
            self._extract_evidence_terms(
                xai_result
            )
        )

        matched = []

        # -------------------------------------------------
        # Evaluate retrieved knowledge
        # -------------------------------------------------

        for knowledge in retrieved_knowledge:

            if not isinstance(
                knowledge,
                dict
            ):
                continue

            metadata = knowledge.get(
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

            content = str(
                knowledge.get(
                    "text",
                    ""
                )
            )

            semantic_score = float(
                knowledge.get(
                    "semantic_score",
                    0.0
                ) or 0.0
            )

            evidence_score = float(
                knowledge.get(
                    "evidence_score",
                    0.0
                ) or 0.0
            )

            hybrid_score = float(
                knowledge.get(
                    "hybrid_score",
                    0.0
                ) or 0.0
            )

            # -------------------------------------------------
            # Skip weak knowledge
            # -------------------------------------------------

            if hybrid_score < self.min_score:
                continue

            # -------------------------------------------------
            # Find matching evidence terms
            # -------------------------------------------------

            content_lower = content.lower()

            matched_terms = []

            for term in evidence_terms:

                if term in content_lower:

                    matched_terms.append(
                        term
                    )

            # -------------------------------------------------
            # Store matched knowledge
            # -------------------------------------------------

            matched.append(
                {
                    "source": source,

                    "category": category,

                    "content": content,

                    "semantic_score":
                        semantic_score,

                    "evidence_score":
                        evidence_score,

                    "hybrid_score":
                        hybrid_score,

                    "matched_terms":
                        matched_terms,

                    "evidence_match":
                        bool(
                            matched_terms
                        )
                }
            )

        # -------------------------------------------------
        # Rank:
        #
        # 1. Evidence match
        # 2. Hybrid score
        # -------------------------------------------------

        matched.sort(
            key=lambda item: (
                item[
                    "evidence_match"
                ],
                item[
                    "hybrid_score"
                ]
            ),
            reverse=True
        )

        # -------------------------------------------------
        # Limit results
        # -------------------------------------------------

        matched = matched[
            :self.max_results
        ]

        return {
            "evidence_terms":
                evidence_terms,

            "matched_knowledge":
                matched,

            "match_count":
                len(matched)
        }