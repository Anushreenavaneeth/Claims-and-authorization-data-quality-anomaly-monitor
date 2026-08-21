"""
Build generation input from XAI analysis
and retrieved knowledge.
"""

from typing import Any, Dict, List


class PromptBuilder:
    """
    Converts XAI output and retrieved knowledge
    into structured generation context.
    """

    def build(
        self,
        xai_result: Dict[str, Any],
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

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

        xai_analysis = xai_result.get(
            "xai_analysis",
            {}
        )

        observed_evidence = (
            xai_analysis.get(
                "observed_evidence",
                {}
            )
        )

        root_cause = (
            xai_analysis.get(
                "likely_root_cause",
                {}
            )
        )

        matched_pattern = (
            xai_analysis.get(
                "matched_anomaly_pattern",
                "Unknown anomaly"
            )
        )

        explanation = (
            xai_analysis.get(
                "explanation",
                ""
            )
        )

        knowledge = []

        for item in retrieved_knowledge:

            metadata = item.get(
                "metadata",
                {}
            )

            knowledge.append(
                {
                    "source": metadata.get(
                        "source",
                        "unknown"
                    ),

                    "category": metadata.get(
                        "category",
                        "unknown"
                    ),

                    "semantic_score": item.get(
                        "semantic_score",
                        0.0
                    ),

                    "evidence_score": item.get(
                        "evidence_score",
                        0.0
                    ),

                    "hybrid_score": item.get(
                        "hybrid_score",
                        0.0
                    ),

                    "content": item.get(
                        "text",
                        ""
                    )
                }
            )

        return {
            "record_id": xai_result.get(
                "record_id",
                "unknown"
            ),

            "dataset_type": xai_result.get(
                "dataset_type",
                "unknown"
            ),

            "observed_evidence":
                observed_evidence,

            "matched_anomaly_pattern":
                matched_pattern,

            "xai_explanation":
                explanation,

            "likely_root_cause":
                root_cause,

            "supporting_knowledge":
                knowledge
        }