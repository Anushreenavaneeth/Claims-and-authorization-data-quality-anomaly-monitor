"""
RAG Connector
=============
Bridges the StandardAnomalyRecord → RAG pipeline → RAGBlock.

Strategy:
  1. Try calling the RAG microservice (port 8001) if available.
  2. If unavailable, use the local RAGPipeline directly (imports rag/).
  3. If both fail, produce a grounded rule-based fallback recommendation.

The connector converts a StandardAnomalyRecord into the dict format
expected by the RAG pipeline and maps the result back into a RAGBlock.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from integration.common_schema import RAGBlock, StandardAnomalyRecord

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def apply_rag(record: StandardAnomalyRecord) -> StandardAnomalyRecord:
    """
    Generate and attach a RAG recommendation to the record.
    Modifies in place and returns the record.
    """
    try:
        if not record.anomaly.is_anomaly:
            record.rag = _no_anomaly_rag()
            if record.processing_status == "sla_done":
                record.processing_status = "rag_done"
            return record

        # Build the RAG-compatible input dict from the standard record
        rag_input = _build_rag_input(record)

        # Try RAG pipeline (local import)
        rag_result = _call_local_rag(rag_input)

        if rag_result:
            record.rag = _map_rag_result(rag_result, record)
        else:
            record.rag = _fallback_recommendation(record)

        if record.processing_status == "sla_done":
            record.processing_status = "rag_done"

    except Exception as exc:
        logger.exception("RAG connector error for record %s", record.record_id)
        record.processing_errors.append(f"RAGConnector: {exc}")
        record.rag = _fallback_recommendation(record)

    return record


# ─────────────────────────────────────────────────────────────────────────────
# Build RAG input
# ─────────────────────────────────────────────────────────────────────────────

def _build_rag_input(record: StandardAnomalyRecord) -> Dict[str, Any]:
    """Convert StandardAnomalyRecord to the dict the RAGPipeline expects."""
    return {
        "record_id":    record.record_id,
        "dataset_type": record.dataset,
        "anomaly": {
            "is_anomaly":    record.anomaly.is_anomaly,
            "anomaly_score": record.anomaly.anomaly_score,
            "severity":      record.anomaly.severity,
            "signal_count":  record.anomaly.signal_count,
            "signals":       record.anomaly.signals,
        },
        "quality": {
            "quality_score": record.quality.quality_score,
            "issues":        record.quality.issues,
        },
        "ml_evidence": {
            "model":      record.ml.model,
            "prediction": record.ml.prediction,
            "score":      record.ml.score,
            "reasons":    record.ml.reasons,
        },
        "rule_based_evidence": [
            {"rule_name": rn, "status": "violated", "description": v}
            for rn, v in zip(record.rules.rule_names, record.rules.violations)
        ] + [
            {"rule_name": rn, "status": "violated", "description": rn}
            for rn in record.rules.rule_names[len(record.rules.violations):]
        ],
        "bayesian": {
            "is_anomaly":  record.bayesian.is_anomaly,
            "probability": record.bayesian.probability,
            "confidence":  record.bayesian.confidence,
            "root_causes": record.bayesian.root_causes,
        },
        "sla": {
            "risk_score":  record.sla.risk_score,
            "risk_level":  record.sla.risk_level,
            "priority":    record.sla.priority,
            "status":      record.sla.status,
        },
        "evidence":  record.evidence,
        "metadata":  record.metadata,
        "context_for_rag": record.metadata.get("context_for_rag", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Local RAG pipeline call  (lazy-initialised singleton — loads model once)
# ─────────────────────────────────────────────────────────────────────────────

_rag_pipeline = None          # singleton
_rag_available: bool | None = None   # None = untested


def _call_local_rag(rag_input: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Attempt to call the local RAGPipeline (cached singleton).
    Returns the recommendation dict or None on failure.
    """
    global _rag_pipeline, _rag_available

    # Once we know it's broken, stop trying every record
    if _rag_available is False:
        return None

    try:
        if _rag_pipeline is None:
            from rag.pipeline.pipeline import RAGPipeline  # type: ignore
            _rag_pipeline  = RAGPipeline()
            _rag_available = True

        result = _rag_pipeline.process_single(rag_input)
        return result
    except Exception as exc:
        logger.warning("Local RAG pipeline unavailable: %s", exc)
        _rag_available = False   # stop retrying
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Map RAG result → RAGBlock
# ─────────────────────────────────────────────────────────────────────────────

def _map_rag_result(
    result: Dict[str, Any],
    record: StandardAnomalyRecord,
) -> RAGBlock:
    """Convert RAGPipeline output dict to RAGBlock."""
    rec = result.get("recommendation", {})
    xai = result.get("xai", {})

    recommendation = (
        rec.get("recommendation")
        or rec.get("summary")
        or xai.get("explanation", "")
        or ""
    )
    explanation = (
        xai.get("explanation")
        or rec.get("explanation", "")
        or ""
    )
    root_cause = (
        xai.get("root_cause")
        or rec.get("root_cause", "")
        or ""
    )

    actions_raw = rec.get("recommended_actions") or rec.get("actions") or []
    if isinstance(actions_raw, str):
        actions_raw = [actions_raw]

    evidence_raw = (
        result.get("retrieval", {}).get("knowledge", [])
        or rec.get("evidence", [])
        or []
    )
    evidence_list = [
        str(e.get("content", e) if isinstance(e, dict) else e)
        for e in evidence_raw[:5]
    ]

    confidence = float(
        rec.get("confidence")
        or xai.get("confidence", 0.0)
        or 0.0
    )

    return RAGBlock(
        recommendation      = recommendation,
        explanation         = explanation,
        root_cause          = root_cause,
        recommended_actions = actions_raw,
        priority            = record.sla.priority,
        confidence          = round(confidence, 4),
        evidence            = evidence_list,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Grounded fallback recommendation (no LLM required)
# ─────────────────────────────────────────────────────────────────────────────

_DATASET_CONTEXT = {
    "claims": {
        "domain":  "healthcare claims",
        "actor":   "claims processing team",
        "objects": "claim records",
    },
    "authorization": {
        "domain":  "prior authorization",
        "actor":   "authorization review team",
        "objects": "authorization requests",
    },
    "pharmacy": {
        "domain":  "pharmacy benefits",
        "actor":   "pharmacy operations team",
        "objects": "pharmacy records",
    },
}

_RULE_DESCRIPTIONS = {
    "EXCESSIVE_IMPORTANT_MISSINGNESS":  "critical fields are missing from the record",
    "EXCESSIVE_SUPPRESSED_VALUES":      "an unusually high number of fields contain suppressed or non-numeric values",
    "unusual_cost_per_claim_change":    "the cost per claim has changed unusually compared with historical patterns",
    "unusual_fills_per_claim":          "the number of fills per claim is higher than expected",
    "DUPLICATE_RECORD":                 "a duplicate record was detected",
    "INVALID_DATE":                     "an invalid or out-of-range date was detected",
    "MISSING_REQUIRED_FIELD":           "a required field is missing",
    "NEGATIVE_VALUE":                   "a field contains an unexpected negative value",
    "HIGH_DENIAL_RATE":                 "an abnormally high claim denial rate was detected",
    "EXPIRED_AUTHORIZATION":            "the authorization has expired or dates are inconsistent",
}


def _fallback_recommendation(record: StandardAnomalyRecord) -> RAGBlock:
    """
    Generate a grounded, specific recommendation without the RAG pipeline.
    Based on actual detected rules, Bayesian flags, and SLA level.
    """
    ctx = _DATASET_CONTEXT.get(record.dataset, _DATASET_CONTEXT["claims"])
    domain  = ctx["domain"]
    actor   = ctx["actor"]
    objects = ctx["objects"]

    severity   = record.anomaly.severity
    risk_level = record.sla.risk_level
    priority   = record.sla.priority
    violations = record.rules.violations
    rule_names = record.rules.rule_names
    signals    = record.anomaly.signals
    quality    = record.quality.quality_score

    # ── What happened ──────────────────────────────────────────────────────
    what_happened_parts = []
    if violations:
        for v in violations[:3]:
            what_happened_parts.append(v)
    elif record.bayesian.is_anomaly:
        what_happened_parts.append(
            f"Bayesian statistical analysis flagged this record with probability "
            f"{record.bayesian.probability:.3f}"
        )
    elif record.ml.prediction == "anomaly":
        what_happened_parts.append(
            f"The ML model ({record.ml.model}) scored this record "
            f"{record.ml.score:.3f}, indicating an anomaly"
        )
    if not what_happened_parts:
        what_happened_parts.append(
            f"An anomaly was detected in this {domain} record with "
            f"{severity} severity"
        )

    what_happened = "; ".join(what_happened_parts)

    # ── Why it was flagged ─────────────────────────────────────────────────
    signal_desc = ", ".join(signals) if signals else "multiple detection methods"
    explanation = (
        f"This {domain} record was flagged because {what_happened}. "
        f"Detection methods triggered: {signal_desc}. "
        f"Data quality score: {quality:.0f}/100."
    )

    # ── Root cause interpretation ──────────────────────────────────────────
    root_cause_parts = []
    for rn in rule_names[:2]:
        desc = _RULE_DESCRIPTIONS.get(rn)
        if desc:
            root_cause_parts.append(f"{rn.replace('_', ' ')}: {desc}")
        else:
            root_cause_parts.append(rn.replace("_", " "))

    if not root_cause_parts and record.bayesian.is_anomaly:
        root_cause_parts.append(
            "Statistical Bayesian outlier — values deviate significantly from the expected distribution"
        )
    if not root_cause_parts:
        root_cause_parts.append(
            "Undetermined — multiple signals triggered; detailed investigation recommended"
        )

    root_cause = "; ".join(root_cause_parts)

    # ── Recommended actions ────────────────────────────────────────────────
    actions = []

    if "EXCESSIVE_IMPORTANT_MISSINGNESS" in rule_names or "MISSING_REQUIRED_FIELD" in rule_names:
        actions.append(
            f"Identify and populate the missing required fields in the {domain} record "
            f"by cross-referencing the source system."
        )

    if "EXCESSIVE_SUPPRESSED_VALUES" in rule_names:
        actions.append(
            f"Review fields with suppressed or non-numeric values. "
            f"Determine whether suppression is valid or represents a data entry error."
        )

    if "unusual_cost_per_claim_change" in rule_names:
        actions.append(
            f"Audit the cost-per-claim values against historical baselines for this plan. "
            f"Check for billing code changes, provider updates, or data entry errors."
        )

    if "unusual_fills_per_claim" in rule_names:
        actions.append(
            f"Verify the number of fills per claim against expected pharmacy benefit rules. "
            f"Check for duplicate dispensing or eligibility issues."
        )

    if record.bayesian.is_anomaly and not actions:
        actions.append(
            f"Conduct a statistical review of this record's key metrics. "
            f"Compare against the distribution of similar {objects} from the same period."
        )

    if record.ml.prediction == "anomaly" and record.ml.score > 0.7:
        actions.append(
            f"The ML model assigned a high anomaly score ({record.ml.score:.3f}). "
            f"Review the flagged features: {', '.join(record.ml.reasons[:2]) if record.ml.reasons else 'see ML evidence'}."
        )

    if record.sla.escalation_required:
        actions.append(
            f"Escalate to senior {actor} immediately. "
            f"SLA response deadline: {record.sla.response_time}."
        )

    if not actions:
        actions.append(
            f"Review and validate this {domain} record in the source system. "
            f"Correct identified data quality issues and resubmit for processing."
        )

    # ── Main recommendation ────────────────────────────────────────────────
    sla_note = (
        f" This is a {priority} ({risk_level} risk) issue requiring action within {record.sla.response_time}."
        if record.anomaly.is_anomaly else ""
    )

    recommendation = (
        f"Anomaly detected in {domain} record {record.record_id} with "
        f"{severity} severity. Root cause: {root_cause_parts[0]}. "
        f"Recommended action: {actions[0]}{sla_note}"
    )

    # ── Confidence ────────────────────────────────────────────────────────
    # Higher confidence when more signals agree
    signal_count = record.anomaly.signal_count
    confidence = min(0.4 + signal_count * 0.15, 0.85)
    if record.rules.violation_count > 0:
        confidence = min(confidence + 0.10, 0.90)

    return RAGBlock(
        recommendation      = recommendation,
        explanation         = explanation,
        root_cause          = root_cause,
        recommended_actions = actions,
        priority            = priority,
        confidence          = round(confidence, 3),
        evidence            = record.evidence[:5],
    )


def _no_anomaly_rag() -> RAGBlock:
    return RAGBlock(
        recommendation      = "No anomaly detected. Record meets all quality checks.",
        explanation         = "This record passed all ML, rule-based, and Bayesian checks.",
        root_cause          = "No root cause — record is normal.",
        recommended_actions = ["Continue standard processing."],
        priority            = "P4",
        confidence          = 0.99,
        evidence            = [],
    )
