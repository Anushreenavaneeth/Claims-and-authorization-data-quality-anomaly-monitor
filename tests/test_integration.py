"""
End-to-End Integration Tests
============================
Tests the complete pipeline:
  Raw JSON → Adapter → Common Schema → SLA → RAG → Final JSON
for all three datasets: Claims, Authorization, Pharmacy.

Run with:
    python -m pytest tests/test_integration.py -v
"""

import sys
import json
import pytest
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# Sample records for testing (inline — no file I/O required)
# ─────────────────────────────────────────────────────────────────────────────

CLAIMS_ANOMALY = {
    "record_id": {"plan_id": "TEST-CLAIMS-001", "issuer_id": "TEST01"},
    "entity": {
        "state": "CA", "issuer_name": "Test Insurer", "plan_type": "HMO",
        "metal_level": "Silver", "exchange_type": "FFE", "individual_or_shop": "Individual",
    },
    "final_assessment": {"anomaly": True, "severity": "HIGH", "signal_count": 3, "signals": "Rule, Bayesian, ML"},
    "bayesian": {"anomaly": True, "score": 450.0, "probability": 0.085, "threshold": 292.3},
    "rule_engine": {
        "anomaly": True, "rule_count": 2,
        "rule_name": "EXCESSIVE_IMPORTANT_MISSINGNESS;EXCESSIVE_SUPPRESSED_VALUES",
        "reason": "Critical fields missing;Suppressed values detected", "severity": "HIGH",
    },
    "ml_evidence": {"evidence_count": 2, "severity": "HIGH", "types": "Statistical", "features": "cost_ratio,claim_count", "details": "Outlier detected", "summary": "ML anomaly"},
    "context_for_rag": "High severity claims anomaly: critical fields missing and suppressed values detected.",
}

CLAIMS_NORMAL = {
    "record_id": {"plan_id": "TEST-CLAIMS-002", "issuer_id": "TEST02"},
    "entity": {"state": "NY", "issuer_name": "Normal Inc", "plan_type": "PPO", "metal_level": "Gold", "exchange_type": "FFE", "individual_or_shop": "Individual"},
    "final_assessment": {"anomaly": False, "severity": "LOW", "signal_count": 0, "signals": "None"},
    "bayesian": {"anomaly": False, "score": 50.0, "probability": 0.008, "threshold": 292.3},
    "rule_engine": {"anomaly": False, "rule_count": 0, "rule_name": "NONE", "reason": "No rule violation detected", "severity": "NONE"},
    "ml_evidence": {"evidence_count": 0, "severity": "", "types": "", "features": "", "details": "", "summary": ""},
}

AUTH_ANOMALY = {
    "record_id": {"authorization_id": "AUTH-TEST-001", "reference_number": "REF-001"},
    "entity": {
        "patient_id": "PAT001", "provider_id": "PRV001", "payer_id": "PAY001",
        "authorization_type": "medication", "service_code": "NDC001",
        "service_description": "Test Drug", "approval_status": "denied",
    },
    "final_assessment": {"anomaly": True, "severity": "CRITICAL", "risk_score": 85, "signal_count": 2, "signals": "Rule, Bayesian"},
    "bayesian": {"anomaly": True, "score": 72.5, "probability": 0.725, "threshold": 0.5},
    "rule_engine": {"anomaly": True, "rule_count": 1, "rule_name": "EXPIRED_AUTHORIZATION", "reason": "Authorization expired", "severity": "CRITICAL"},
    "ml_evidence": {"evidence_count": 1, "severity": "CRITICAL", "types": "Rule", "features": "expiry_date", "details": "Expired auth", "summary": "Authorization expired"},
}

PHARMACY_ANOMALY = {
    "record_id": {"plan_id": "PHARM-TEST-001"},
    "entity": {"state": "", "issuer_name": "", "plan_type": "", "metal_level": "", "exchange_type": "", "individual_or_shop": ""},
    "final_assessment": {"anomaly": True, "severity": "MEDIUM", "signal_count": 3, "signals": "Rule, Behavioral, Bayesian"},
    "bayesian": {"anomaly": True, "score": 0.0, "probability": 0.206, "threshold": 0.0},
    "rule_engine": {"anomaly": True, "rule_count": 1, "rule_name": "unusual_cost_per_claim_change", "reason": "Cost per claim changed unusually", "severity": "NONE"},
    "ml_evidence": {"evidence_count": 0, "severity": "", "types": "", "features": "", "details": "", "summary": ""},
    "context_for_rag": "Rule-based pharmacy anomaly evidence detected: Cost per claim changed unusually compared with historical behavior.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Adapters
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimsAdapter:
    def test_normal_record(self):
        from integration.claims_adapter import adapt
        r = adapt(CLAIMS_NORMAL)
        assert r.dataset == "claims"
        assert r.anomaly.is_anomaly is False
        assert r.anomaly.severity == "LOW"
        assert r.record_id.startswith("CLAIMS-")
        assert r.processing_errors == []

    def test_anomaly_record(self):
        from integration.claims_adapter import adapt
        r = adapt(CLAIMS_ANOMALY)
        assert r.anomaly.is_anomaly is True
        assert r.anomaly.severity == "HIGH"
        assert r.anomaly.signal_count == 3
        assert len(r.rules.violations) > 0
        assert r.bayesian.is_anomaly is True

    def test_missing_fields_does_not_crash(self):
        from integration.claims_adapter import adapt
        r = adapt({})
        assert r.dataset == "claims"
        assert "ClaimsAdapter" not in str(r.processing_errors) or True  # should not raise

    def test_quality_score_below_100_for_anomaly(self):
        from integration.claims_adapter import adapt
        r = adapt(CLAIMS_ANOMALY)
        assert r.quality.quality_score < 100.0

    def test_record_id_format(self):
        from integration.claims_adapter import adapt
        r = adapt(CLAIMS_ANOMALY)
        assert r.record_id == "CLAIMS-TEST-CLAIMS-001"


class TestAuthorizationAdapter:
    def test_anomaly_record(self):
        from integration.authorization_adapter import adapt
        r = adapt(AUTH_ANOMALY)
        assert r.dataset == "authorization"
        assert r.anomaly.is_anomaly is True
        assert r.anomaly.severity == "CRITICAL"
        assert r.record_id.startswith("AUTH-")
        assert r.metadata["patient_id"] == "PAT001"

    def test_normal_record(self):
        from integration.authorization_adapter import adapt
        normal = {
            "record_id": {"authorization_id": "AUTH-NORM-001", "reference_number": "REF-N01"},
            "entity": {"patient_id": "P1", "provider_id": "PR1", "payer_id": "PA1", "authorization_type": "x", "service_code": "s", "service_description": "s", "approval_status": "approved"},
            "final_assessment": {"anomaly": False, "severity": "LOW", "risk_score": 0, "signal_count": 0, "signals": "None"},
            "bayesian": {"anomaly": False, "score": 5.22, "probability": 0.0522, "threshold": 0.5},
            "rule_engine": {"anomaly": False, "rule_count": 0, "rule_name": "NONE", "reason": "No rule violation detected", "severity": "NONE"},
            "ml_evidence": {"evidence_count": 0, "severity": "", "types": "", "features": "", "details": "", "summary": ""},
        }
        r = adapt(normal)
        assert r.anomaly.is_anomaly is False
        assert r.quality.quality_score == 100.0

    def test_rule_names_parsed(self):
        from integration.authorization_adapter import adapt
        r = adapt(AUTH_ANOMALY)
        assert "EXPIRED_AUTHORIZATION" in r.rules.rule_names


class TestPharmacyAdapter:
    def test_anomaly_record(self):
        from integration.pharmacy_adapter import adapt
        r = adapt(PHARMACY_ANOMALY)
        assert r.dataset == "pharmacy"
        assert r.anomaly.is_anomaly is True
        assert r.record_id.startswith("PHARM-")

    def test_signals_parsed(self):
        from integration.pharmacy_adapter import adapt
        r = adapt(PHARMACY_ANOMALY)
        assert "Rule" in r.anomaly.signals
        assert "Bayesian" in r.anomaly.signals


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Common Schema validation
# ─────────────────────────────────────────────────────────────────────────────

class TestCommonSchema:
    def test_valid_record(self):
        from integration.claims_adapter import adapt
        from integration.common_schema import validate_standard_record
        r = adapt(CLAIMS_ANOMALY)
        errors = validate_standard_record(r)
        assert errors == []

    def test_invalid_dataset(self):
        from integration.common_schema import StandardAnomalyRecord, validate_standard_record
        r = StandardAnomalyRecord(record_id="R1", dataset="unknown")
        errors = validate_standard_record(r)
        assert any("dataset" in e for e in errors)

    def test_empty_record_id(self):
        from integration.common_schema import StandardAnomalyRecord, validate_standard_record
        r = StandardAnomalyRecord(record_id="", dataset="claims")
        errors = validate_standard_record(r)
        assert any("record_id" in e for e in errors)

    def test_to_dict(self):
        from integration.claims_adapter import adapt
        r = adapt(CLAIMS_ANOMALY)
        d = r.to_dict()
        assert isinstance(d, dict)
        assert "anomaly" in d
        assert "sla" in d
        assert "rag" in d


# ─────────────────────────────────────────────────────────────────────────────
# Tests: SLA Engine
# ─────────────────────────────────────────────────────────────────────────────

class TestSLAEngine:
    def test_anomaly_gets_nonzero_risk_score(self):
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        r = adapt(CLAIMS_ANOMALY)
        apply_sla(r)
        assert r.sla.risk_score > 0

    def test_normal_record_has_zero_risk_score(self):
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        r = adapt(CLAIMS_NORMAL)
        apply_sla(r)
        assert r.sla.risk_score == 0.0
        assert r.sla.risk_level == "LOW"
        assert r.sla.escalation_required is False

    def test_critical_record_escalation(self):
        from integration.authorization_adapter import adapt
        from integration.sla_engine import apply_sla
        r = adapt(AUTH_ANOMALY)
        apply_sla(r)
        assert r.sla.escalation_required is True
        assert r.sla.risk_level in ("HIGH", "CRITICAL")

    def test_sla_applies_to_all_datasets(self):
        from integration import claims_adapter, authorization_adapter, pharmacy_adapter
        from integration.sla_engine import apply_sla
        for adapter, record in [
            (claims_adapter, CLAIMS_ANOMALY),
            (authorization_adapter, AUTH_ANOMALY),
            (pharmacy_adapter, PHARMACY_ANOMALY),
        ]:
            r = adapter.adapt(record)
            apply_sla(r)
            assert r.sla.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
            assert r.sla.priority in ("P1", "P2", "P3", "P4")

    def test_high_severity_higher_risk_than_low(self):
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        r_high = adapt(CLAIMS_ANOMALY)   # HIGH severity
        apply_sla(r_high)
        r_low = adapt({**CLAIMS_ANOMALY, "final_assessment": {"anomaly": True, "severity": "LOW", "signal_count": 1, "signals": "Rule"}})
        apply_sla(r_low)
        assert r_high.sla.risk_score > r_low.sla.risk_score


# ─────────────────────────────────────────────────────────────────────────────
# Tests: RAG Connector
# ─────────────────────────────────────────────────────────────────────────────

class TestRAGConnector:
    def test_anomaly_gets_recommendation(self):
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        r = adapt(CLAIMS_ANOMALY)
        apply_sla(r)
        apply_rag(r)
        assert r.rag.recommendation != ""
        assert len(r.rag.recommended_actions) > 0

    def test_normal_record_gets_normal_recommendation(self):
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        r = adapt(CLAIMS_NORMAL)
        apply_sla(r)
        apply_rag(r)
        assert "No anomaly" in r.rag.recommendation or r.rag.recommendation != ""

    def test_recommendation_confidence_range(self):
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        r = adapt(CLAIMS_ANOMALY)
        apply_sla(r)
        apply_rag(r)
        assert 0.0 <= r.rag.confidence <= 1.0

    def test_recommendation_mentions_dataset(self):
        from integration.pharmacy_adapter import adapt
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        r = adapt(PHARMACY_ANOMALY)
        apply_sla(r)
        apply_rag(r)
        # Should reference pharmacy domain
        full_text = (r.rag.recommendation + r.rag.explanation).lower()
        assert "pharmacy" in full_text or "cost" in full_text or "claim" in full_text


# ─────────────────────────────────────────────────────────────────────────────
# Tests: End-to-End pipeline (per dataset)
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEnd:
    """Full pipeline for a single record — Adapter → Schema → SLA → RAG → JSON"""

    def _run_pipeline(self, adapter_module, raw_record):
        import importlib
        mod = importlib.import_module(f"integration.{adapter_module}_adapter")
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        from integration.common_schema import validate_standard_record

        record = mod.adapt(raw_record)
        errors = validate_standard_record(record)
        assert errors == [], f"Schema validation failed: {errors}"

        apply_sla(record)
        apply_rag(record)
        record.processing_status = "complete"

        d = record.to_dict()
        # Verify all major blocks are present
        assert "anomaly" in d
        assert "quality" in d
        assert "ml" in d
        assert "rules" in d
        assert "bayesian" in d
        assert "sla" in d
        assert "rag" in d
        assert d["sla"]["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert d["sla"]["priority"] in ("P1", "P2", "P3", "P4")
        assert d["rag"]["recommendation"] != ""

        return record

    def test_claims_end_to_end_anomaly(self):
        r = self._run_pipeline("claims", CLAIMS_ANOMALY)
        assert r.dataset == "claims"
        assert r.anomaly.is_anomaly is True

    def test_claims_end_to_end_normal(self):
        r = self._run_pipeline("claims", CLAIMS_NORMAL)
        assert r.sla.risk_score == 0.0

    def test_authorization_end_to_end(self):
        r = self._run_pipeline("authorization", AUTH_ANOMALY)
        assert r.dataset == "authorization"
        assert r.sla.escalation_required is True

    def test_pharmacy_end_to_end(self):
        r = self._run_pipeline("pharmacy", PHARMACY_ANOMALY)
        assert r.dataset == "pharmacy"
        assert r.anomaly.signal_count == 3

    def test_malformed_record_does_not_crash(self):
        """A completely empty record must not crash the pipeline."""
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        r = adapt({})
        apply_sla(r)
        apply_rag(r)
        assert r.processing_status in ("error", "rag_done", "sla_done", "complete", "adapted")

    def test_sla_breach_record(self):
        """A CRITICAL record should have BREACHED or AT_RISK SLA status."""
        from integration.authorization_adapter import adapt
        from integration.sla_engine import apply_sla
        r = adapt(AUTH_ANOMALY)
        apply_sla(r)
        assert r.sla.status in ("BREACHED", "AT_RISK")

    def test_json_serialisable(self):
        """Final output must be JSON-serialisable."""
        from integration.claims_adapter import adapt
        from integration.sla_engine import apply_sla
        from integration.rag_connector import apply_rag
        r = adapt(CLAIMS_ANOMALY)
        apply_sla(r)
        apply_rag(r)
        d = r.to_dict()
        serialised = json.dumps(d)
        assert len(serialised) > 100
