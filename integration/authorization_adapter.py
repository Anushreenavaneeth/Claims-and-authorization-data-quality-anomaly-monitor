"""
Authorization Adapter
======================
Converts one raw authorization JSON record (authorization.json format)
into a StandardAnomalyRecord.

Input fields used:
  record_id.authorization_id / record_id.reference_number
  entity.patient_id / provider_id / payer_id / authorization_type /
         service_code / service_description / approval_status
  final_assessment.anomaly / severity / risk_score / signal_count / signals
  bayesian.*
  rule_engine.*
  ml_evidence.*

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
    Convert one authorization raw record → StandardAnomalyRecord.
    Never raises — errors are captured in processing_errors.
    """
    record = StandardAnomalyRecord()
    record.dataset   = "authorization"
    record.timestamp = utc_now()

    try:
        # ── record_id ──────────────────────────────────────────────────────
        rid         = raw.get("record_id", {})
        auth_id     = str(rid.get("authorization_id",  "") or "")
        ref_number  = str(rid.get("reference_number",  "") or "")
        raw_key     = auth_id or ref_number or "UNKNOWN"
        record.record_id = make_record_id("AUTH", raw_key)

        # ── entity / metadata ──────────────────────────────────────────────
        entity = raw.get("entity", {})
        record.metadata = {
            "authorization_id":   auth_id,
            "reference_number":   ref_number,
            "patient_id":         entity.get("patient_id",          ""),
            "provider_id":        entity.get("provider_id",         ""),
            "payer_id":           entity.get("payer_id",            ""),
            "authorization_type": entity.get("authorization_type",  ""),
            "service_code":       entity.get("service_code",        ""),
            "service_description": entity.get("service_description",""),
            "approval_status":    entity.get("approval_status",     ""),
        }

        # ── final_assessment → AnomalyBlock ────────────────────────────────
        fa          = raw.get("final_assessment", {})
        severity    = str(fa.get("severity", "LOW")).upper()
        if severity == "NONE":
            severity = "LOW"
        signals_raw  = str(fa.get("signals", "None"))
        signals_list = signals_from_string(signals_raw)

        # Authorization records include an explicit risk_score (0–100)
        raw_risk   = float(fa.get("risk_score", 0) or 0)
        norm_score = round(raw_risk / 100.0, 4) if raw_risk > 1 else round(raw_risk, 4)

        record.anomaly = AnomalyBlock(
            is_anomaly    = bool(fa.get("anomaly", False)),
            anomaly_score = norm_score or _derive_anomaly_score(raw),
            severity      = severity,
            signal_count  = int(fa.get("signal_count", 0) or 0),
            signals       = signals_list,
        )

        # ── quality ────────────────────────────────────────────────────────
        q_score = quality_score_from_record(raw)
        issues: list[str] = []
        if record.anomaly.is_anomaly:
            issues.append(f"Authorization anomaly — {severity} severity")
        rule_eng = raw.get("rule_engine", {})
        if rule_eng.get("anomaly"):
            reason = str(rule_eng.get("reason", ""))
            for r in reason.split(";"):
                r = r.strip()
                if r and r.lower() != "no rule violation detected":
                    issues.append(r)
        approval = entity.get("approval_status", "")
        if approval and approval.lower() not in ("approved", ""):
            issues.append(f"Approval status: {approval}")

        record.quality = QualityBlock(
            quality_score = round(q_score, 2),
            issues        = issues,
        )

        # ── ML evidence → MLBlock ──────────────────────────────────────────
        ml_ev      = raw.get("ml_evidence", {})
        ml_score   = norm_score or _derive_anomaly_score(raw)
        ml_reasons = []
        if ml_ev.get("summary"):
            ml_reasons.append(str(ml_ev["summary"]))
        if ml_ev.get("types"):
            ml_reasons.append(f"Evidence types: {ml_ev['types']}")
        if ml_ev.get("features"):
            ml_reasons.append(f"Features: {ml_ev['features']}")
        if entity.get("authorization_type"):
            ml_reasons.append(f"Authorization type: {entity['authorization_type']}")

        record.ml = MLBlock(
            model      = "Isolation Forest (Authorization Pipeline)",
            prediction = "anomaly" if record.anomaly.is_anomaly else "normal",
            score      = round(ml_score, 4),
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
        bay_score = float(bay.get("score",       0) or 0)
        bay_prob  = float(bay.get("probability", 0) or 0)
        bay_thr   = float(bay.get("threshold",   0) or 0)
        bay_anom  = bool(bay.get("anomaly", False))

        # Authorization Bayesian scores look like 5.22 (probability ×100)
        # normalise to [0,1]
        if bay_score > 1.0:
            bay_score_norm = round(bay_score / 100.0, 4)
        else:
            bay_score_norm = round(bay_score, 4)

        if bay_prob > 1.0:
            bay_prob_norm = round(bay_prob / 100.0, 4)
        else:
            bay_prob_norm = round(bay_prob, 4)

        record.bayesian = BayesianBlock(
            is_anomaly  = bay_anom,
            score       = bay_score_norm,
            probability = bay_prob_norm,
            threshold   = round(bay_thr, 4),
            root_causes = [],
            confidence  = bay_prob_norm,
        )

        # ── evidence list ──────────────────────────────────────────────────
        evidence = []
        if record.rules.violations:
            evidence.extend(record.rules.violations)
        if record.bayesian.is_anomaly:
            evidence.append(f"Bayesian probability {bay_prob_norm:.4f} exceeds threshold")
        if ml_ev.get("summary"):
            evidence.append(str(ml_ev["summary"]))
        if entity.get("service_description"):
            evidence.append(f"Service: {entity['service_description']}")
        record.evidence = evidence

        record.processing_status = "adapted"

    except Exception as exc:
        logger.exception("AuthorizationAdapter error for record: %s", raw)
        record.processing_errors.append(f"AuthorizationAdapter: {exc}")
        record.processing_status = "error"

    return record


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _derive_anomaly_score(raw: Dict[str, Any]) -> float:
    bay  = raw.get("bayesian", {})
    prob = float(bay.get("probability", 0) or 0)
    if prob > 1.0:
        return round(prob / 100.0, 4)
    return round(prob, 4)
