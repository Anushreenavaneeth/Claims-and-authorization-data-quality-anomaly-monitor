"""
Pharmacy Adapter
================
Converts one raw pharmacy JSON record (anomaly_results.json format)
into a StandardAnomalyRecord.

The pharmacy records reuse the same envelope structure as claims, but:
  - record_id.plan_id refers to a pharmacy plan (not a health insurance plan)
  - entity fields are mostly empty in the current output
  - context_for_rag contains a pharmacy-specific description

Does NOT re-run any ML logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from integration.common_schema import (
    AnomalyBlock,
    BayesianBlock,
    MLBlock,
    QualityBlock,
    RulesBlock,
    StandardAnomalyRecord,
    make_record_id,
    quality_score_from_record,
    signals_from_string,
    utc_now,
)

logger = logging.getLogger(__name__)


def adapt(raw: Dict[str, Any]) -> StandardAnomalyRecord:
    """
    Convert one pharmacy raw record → StandardAnomalyRecord.
    Never raises — errors are captured in processing_errors.
    """
    record = StandardAnomalyRecord()
    record.dataset   = "pharmacy"
    record.timestamp = utc_now()

    try:
        # ── record_id ──────────────────────────────────────────────────────
        rid      = raw.get("record_id", {})
        plan_id  = str(rid.get("plan_id",   "") or "")
        raw_key  = plan_id or "UNKNOWN"
        record.record_id = make_record_id("PHARM", raw_key)

        # ── entity / metadata ──────────────────────────────────────────────
        entity = raw.get("entity", {})
        record.metadata = {
            "plan_id":            plan_id,
            "state":              entity.get("state",               ""),
            "issuer_name":        entity.get("issuer_name",         ""),
            "plan_type":          entity.get("plan_type",           ""),
            "metal_level":        entity.get("metal_level",         ""),
            "exchange_type":      entity.get("exchange_type",       ""),
            "individual_or_shop": entity.get("individual_or_shop",  ""),
            "context_for_rag":    raw.get("context_for_rag",        ""),
        }

        # ── final_assessment → AnomalyBlock ────────────────────────────────
        fa          = raw.get("final_assessment", {})
        severity    = str(fa.get("severity", "LOW")).upper()
        if severity == "NONE":
            severity = "LOW"
        signals_raw  = str(fa.get("signals", "None"))
        signals_list = signals_from_string(signals_raw)

        record.anomaly = AnomalyBlock(
            is_anomaly    = bool(fa.get("anomaly", False)),
            anomaly_score = _derive_anomaly_score(raw),
            severity      = severity,
            signal_count  = int(fa.get("signal_count", 0) or 0),
            signals       = signals_list,
        )

        # ── quality ────────────────────────────────────────────────────────
        q_score = quality_score_from_record(raw)
        issues: list[str] = []
        if record.anomaly.is_anomaly:
            issues.append(f"Pharmacy anomaly — {severity} severity")

        rule_eng = raw.get("rule_engine", {})
        if rule_eng.get("anomaly"):
            reason = str(rule_eng.get("reason", ""))
            for r in reason.split(";"):
                r = r.strip()
                if r and r.lower() != "no rule violation detected":
                    issues.append(r)

        ctx = raw.get("context_for_rag", "")
        if ctx and record.anomaly.is_anomaly:
            # Extract readable issue from context string
            prefix = "Rule-based pharmacy anomaly evidence detected: "
            if ctx.startswith(prefix):
                issues.append(ctx[len(prefix):].rstrip("."))

        record.quality = QualityBlock(
            quality_score = round(q_score, 2),
            issues        = issues,
        )

        # ── ML evidence → MLBlock ──────────────────────────────────────────
        ml_ev      = raw.get("ml_evidence", {})
        ml_reasons = []
        if ml_ev.get("summary"):
            ml_reasons.append(str(ml_ev["summary"]))
        if ml_ev.get("types"):
            ml_reasons.append(f"Evidence types: {ml_ev['types']}")
        if ml_ev.get("features"):
            ml_reasons.append(f"Features: {ml_ev['features']}")
        if ctx and not ml_reasons:
            ml_reasons.append(ctx)

        record.ml = MLBlock(
            model      = "Pharmacy Anomaly Model",
            prediction = "anomaly" if record.anomaly.is_anomaly else "normal",
            score      = round(_derive_anomaly_score(raw), 4),
            reasons    = ml_reasons,
        )

        # ── rule_engine → RulesBlock ───────────────────────────────────────
        rule_names_raw = str(rule_eng.get("rule_name", "NONE") or "NONE")
        rule_names     = [r.strip() for r in rule_names_raw.split(";")
                          if r.strip() and r.strip().upper() != "NONE"]
        violations_raw = str(rule_eng.get("reason", "") or "")
        violations     = [v.strip() for v in violations_raw.split(";")
                          if v.strip() and v.lower() != "no rule violation detected"]
        rule_severity  = str(rule_eng.get("severity", "NONE")).upper()

        record.rules = RulesBlock(
            violations      = violations,
            violation_count = int(rule_eng.get("rule_count", 0) or 0),
            rule_names      = rule_names,
            severity        = rule_severity,
        )

        # ── bayesian → BayesianBlock ───────────────────────────────────────
        bay      = raw.get("bayesian", {})
        bay_prob = float(bay.get("probability", 0) or 0)
        bay_thr  = float(bay.get("threshold",   0) or 0)
        bay_anom = bool(bay.get("anomaly", False))

        # Pharmacy Bayesian probabilities appear already in [0,1]
        record.bayesian = BayesianBlock(
            is_anomaly  = bay_anom,
            score       = round(bay_prob, 4),
            probability = round(bay_prob, 4),
            threshold   = round(bay_thr,  4),
            root_causes = [],
            confidence  = round(bay_prob, 4),
        )

        # ── evidence list ──────────────────────────────────────────────────
        evidence = []
        if record.rules.violations:
            evidence.extend(record.rules.violations)
        if record.bayesian.is_anomaly:
            evidence.append(f"Bayesian flag: probability {bay_prob:.4f}")
        if ctx:
            evidence.append(ctx)
        record.evidence = evidence

        record.processing_status = "adapted"

    except Exception as exc:
        logger.exception("PharmacyAdapter error for record: %s", raw)
        record.processing_errors.append(f"PharmacyAdapter: {exc}")
        record.processing_status = "error"

    return record


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _derive_anomaly_score(raw: Dict[str, Any]) -> float:
    ml_ev          = raw.get("ml_evidence", {})
    evidence_count = int(ml_ev.get("evidence_count", 0) or 0)

    if evidence_count > 0:
        return round(min(evidence_count / 5.0, 1.0), 4)

    bay  = raw.get("bayesian", {})
    prob = float(bay.get("probability", 0) or 0)
    if 0.0 <= prob <= 1.0:
        return round(prob, 4)

    return 0.0
