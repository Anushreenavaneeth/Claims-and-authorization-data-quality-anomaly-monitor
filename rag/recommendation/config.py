"""
Recommendation engine configuration.
"""

# Minimum hybrid retrieval score required
# for knowledge to be considered strongly relevant.

MIN_KNOWLEDGE_SCORE = 0.35


# Maximum number of supporting knowledge
# entries used by the recommendation engine.

MAX_SUPPORTING_KNOWLEDGE = 5


# Default priority when evidence is insufficient.

DEFAULT_PRIORITY = "Normal"


# Priority mapping from ML severity.

SEVERITY_PRIORITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "warning": "Medium",
    "medium": "Medium",
    "low": "Low"
}