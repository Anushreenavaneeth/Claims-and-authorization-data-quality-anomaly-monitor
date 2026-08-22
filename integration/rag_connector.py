"""
RAG Connector
=============
Bridges StandardAnomalyRecord → RAG pipeline → RAGBlock.

Strategy:
  1. Try the local RAGPipeline (singleton, loads model once).
  2. If unavailable, use the grounded rule-based fallback (no LLM needed).
"""

from __future__ import annotations

# ── Path bootstrap ────────────────────────────────────────────────────────
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
# ─────────────────────────────────────────────────────────────────────────

import logging
from typing import Any, Dict, Optional

from integration.common_schema import RAGBlock, StandardAnomalyRecord

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def apply_rag(record: StandardAnomalyRecord) -> StandardAnomalyRecord:
    """Generate and attach a RAG recommendation to the record (in-place)."""
    try:
        if not record.anomaly.is_anomaly:
            record.rag = _no_anomaly_rag()
            if record.processing_status == "sla_done":
                record.processing_status = "rag_done"
            return record

        rag_input  = _build_rag_input(record)
        rag_result = _call_local_rag(rag_input)

        record.rag = _map_rag_result(rag_result, record) if rag_result else _fallback_recommendation(record)

        if record.processing_status == "sla_done":
            record.processing_status = "rag_done"

    except Exception as exc:
        logger.exception("RAG connector error for record %s", record.record_id)
        record.processing_errors.append(f"RAGConnector: {exc}")
        record.rag = _fallback_recommendation(record)

    return record


# ─────────────────────────────────────────────────────────────────────────────
# Build RAG input dict
# ─────────────────────────────────────────────────────────────────────────────

def _build_rag_input(record: StandardAnomalyRecord) -> Dict[str, Any]:
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
        "quality":      {"quality_score": record.quality.quality_score, "issues": record.quality.issues},
        "ml_evidence":  {"model": record.ml.model, "prediction": record.ml.prediction, "score": record.ml.score, "reasons": record.ml.reasons},
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
        "sla":          {"risk_score": record.sla.risk_score, "risk_level": record.sla.risk_level, "priority": record.sla.priority, "status": record.sla.status},
        "evidence":     record.evidence,
        "metadata":     record.metadata,
        "context_for_rag": record.metadata.get("context_for_rag", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Local RAG pipeline — lazy singleton so model loads only once
# ─────────────────────────────────────────────────────────────────────────────

_rag_pipeline = None
# Set to False by default for batch pipeline — the local RAG validator requires
# a different schema ('detection_summary', 'ml_based_evidence', 'record_context')
# that doesn't match our standard schema.  The grounded fallback produces
# specific, actionable recommendations without needing the LLM model.
# Set env var USE_LOCAL_RAG=1 to attempt the local RAG pipeline instead.
import os as _os
_rag_available: Optional[bool] = None if _os.getenv("USE_LOCAL_RAG") == "1" else False


def _call_local_rag(rag_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    global _rag_pipeline, _rag_available
    if _rag_available is False:
        return None
    try:
        if _rag_pipeline is None:
            from rag.pipeline.pipeline import RAGPipeline  # type: ignore
            _rag_pipeline  = RAGPipeline()
            _rag_available = True
        return _rag_pipeline.process_single(rag_input)
    except Exception as exc:
        logger.warning("Local RAG pipeline unavailable: %s", exc)
        _rag_available = False
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Map RAG result → RAGBlock
# ─────────────────────────────────────────────────────────────────────────────

def _map_rag_result(result: Dict[str, Any], record: StandardAnomalyRecord) -> RAGBlock:
    rec = result.get("recommendation", {})
    xai = result.get("xai", {})
    recommendation = rec.get("recommendation") or rec.get("summary") or xai.get("explanation", "") or ""
    explanation    = xai.get("explanation") or rec.get("explanation", "") or ""
    root_cause     = xai.get("root_cause") or rec.get("root_cause", "") or ""
    actions_raw    = rec.get("recommended_actions") or rec.get("actions") or []
    if isinstance(actions_raw, str):
        actions_raw = [actions_raw]
    evidence_raw  = result.get("retrieval", {}).get("knowledge", []) or rec.get("evidence", []) or []
    evidence_list = [str(e.get("content", e) if isinstance(e, dict) else e) for e in evidence_raw[:5]]
    confidence    = float(rec.get("confidence") or xai.get("confidence", 0.0) or 0.0)
    return RAGBlock(
        recommendation=recommendation, explanation=explanation, root_cause=root_cause,
        recommended_actions=actions_raw, priority=record.sla.priority,
        confidence=round(confidence, 4), evidence=evidence_list,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Grounded fallback (no LLM — uses actual detected rules and SLA data)
# ─────────────────────────────────────────────────────────────────────────────

_DATASET_CONTEXT = {
    "claims":        {"domain": "healthcare claims",    "actor": "claims processing team",      "objects": "claim records"},
    "authorization": {"domain": "prior authorization",  "actor": "authorization review team",   "objects": "authorization requests"},
    "pharmacy":      {"domain": "pharmacy benefits",    "actor": "pharmacy operations team",    "objects": "pharmacy records"},
}

_RULE_DESCRIPTIONS = {
    "EXCESSIVE_IMPORTANT_MISSINGNESS": "critical fields are missing from the record",
    "EXCESSIVE_SUPPRESSED_VALUES":     "an unusually high number of fields contain suppressed or non-numeric values",
    "unusual_cost_per_claim_change":   "the cost per claim has changed unusually compared with historical patterns",
    "unusual_fills_per_claim":         "the number of fills per claim is higher than expected",
    "DUPLICATE_RECORD":                "a duplicate record was detected",
    "INVALID_DATE":                    "an invalid or out-of-range date was detected",
    "MISSING_REQUIRED_FIELD":          "a required field is missing",
    "NEGATIVE_VALUE":                  "a field contains an unexpected negative value",
    "HIGH_DENIAL_RATE":                "an abnormally high claim denial rate was detected",
    "EXPIRED_AUTHORIZATION":           "the authorization has expired or dates are inconsistent",
}


def _fallback_recommendation(record: StandardAnomalyRecord) -> RAGBlock:
    ctx      = _DATASET_CONTEXT.get(record.dataset, _DATASET_CONTEXT["claims"])
    domain   = ctx["domain"]
    actor    = ctx["actor"]
    objects  = ctx["objects"]
    severity = record.anomaly.severity
    priority = record.sla.priority
    violations = record.rules.violations
    rule_names = record.rules.rule_names
    signals    = record.anomaly.signals
    quality    = record.quality.quality_score

    # What happened
    what_parts = violations[:3] if violations else (
        [f"Bayesian flag: probability {record.bayesian.probability:.3f}"] if record.bayesian.is_anomaly
        else [f"ML model ({record.ml.model}) scored {record.ml.score:.3f}"] if record.ml.prediction == "anomaly"
        else [f"Anomaly detected with {severity} severity"]
    )
    what_happened = "; ".join(what_parts)

    signal_desc = ", ".join(signals) if signals else "multiple detection methods"
    explanation = (
        f"This {domain} record was flagged because {what_happened}. "
        f"Detection methods triggered: {signal_desc}. "
        f"Data quality score: {quality:.0f}/100."
    )

    # Root cause
    rc_parts = []
    for rn in rule_names[:2]:
        desc = _RULE_DESCRIPTIONS.get(rn)
        rc_parts.append(f"{rn.replace('_', ' ')}: {desc}" if desc else rn.replace("_", " "))
    if not rc_parts and record.bayesian.is_anomaly:
        rc_parts.append("Statistical Bayesian outlier — values deviate from expected distribution")
    if not rc_parts:
        rc_parts.append("Undetermined — multiple signals triggered; investigation recommended")
    root_cause = "; ".join(rc_parts)

    # Actions
    actions = []
    if "EXCESSIVE_IMPORTANT_MISSINGNESS" in rule_names or "MISSING_REQUIRED_FIELD" in rule_names:
        actions.append(f"Identify and populate missing required fields in the {domain} record by cross-referencing the source system.")
    if "EXCESSIVE_SUPPRESSED_VALUES" in rule_names:
        actions.append("Review fields with suppressed or non-numeric values. Determine whether suppression is valid or a data entry error.")
    if "unusual_cost_per_claim_change" in rule_names:
        actions.append("Audit cost-per-claim values against historical baselines. Check for billing code changes, provider updates, or data entry errors.")
    if "unusual_fills_per_claim" in rule_names:
        actions.append("Verify fills-per-claim against expected pharmacy benefit rules. Check for duplicate dispensing or eligibility issues.")
    if "EXPIRED_AUTHORIZATION" in rule_names:
        actions.append("Review authorization dates against service dates. Re-submit authorization request if service is still required.")
    if record.bayesian.is_anomaly and not actions:
        actions.append(f"Conduct a statistical review of this record's key metrics against similar {objects} from the same period.")
    if record.ml.prediction == "anomaly" and record.ml.score > 0.7:
        features = ", ".join(record.ml.reasons[:2]) if record.ml.reasons else "see ML evidence"
        actions.append(f"ML model assigned high anomaly score ({record.ml.score:.3f}). Review flagged features: {features}.")
    if record.sla.escalation_required:
        actions.append(f"Escalate to senior {actor} immediately. SLA response deadline: {record.sla.response_time}.")
    if not actions:
        actions.append(f"Review and validate this {domain} record in the source system. Correct data quality issues and resubmit for processing.")

    sla_note = f" This is a {priority} ({record.sla.risk_level} risk) issue requiring action within {record.sla.response_time}."
    recommendation = (
        f"Anomaly detected in {domain} record {record.record_id} with {severity} severity. "
        f"Root cause: {rc_parts[0]}. Recommended action: {actions[0]}{sla_note}"
    )

    signal_count = record.anomaly.signal_count
    confidence   = min(0.4 + signal_count * 0.15 + (0.10 if record.rules.violation_count > 0 else 0), 0.90)

    return RAGBlock(
        recommendation=recommendation, explanation=explanation, root_cause=root_cause,
        recommended_actions=actions, priority=priority,
        confidence=round(confidence, 3), evidence=record.evidence[:5],
    )


def _no_anomaly_rag() -> RAGBlock:
    return RAGBlock(
        recommendation="No anomaly detected. Record meets all quality checks.",
        explanation="This record passed all ML, rule-based, and Bayesian checks.",
        root_cause="No root cause — record is normal.",
        recommended_actions=["Continue standard processing."],
        priority="P4", confidence=0.99, evidence=[],
    )
