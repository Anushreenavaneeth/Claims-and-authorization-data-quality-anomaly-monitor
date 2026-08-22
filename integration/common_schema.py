"""
Common Standardized Schema
===========================
All three dataset adapters (Claims, Authorization, Pharmacy) produce a
StandardAnomalyRecord.  The SLA engine and RAG layer consume only this schema.

Design rules:
  - Never lose existing information: dataset-specific fields land in `metadata`.
  - All required fields have safe defaults so one bad record can't crash the pipeline.
  - Validated via `validate_standard_record()` before further processing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Supported datasets
# ─────────────────────────────────────────────────────────────────────────────

VALID_DATASETS = {"claims", "authorization", "pharmacy"}


# ─────────────────────────────────────────────────────────────────────────────
# Sub-structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AnomalyBlock:
    is_anomaly:    bool  = False
    anomaly_score: float = 0.0
    severity:      str   = "LOW"
    signal_count:  int   = 0
    signals:       List[str] = field(default_factory=list)


@dataclass
class QualityBlock:
    quality_score: float      = 100.0
    issues:        List[str]  = field(default_factory=list)


@dataclass
class MLBlock:
    model:      str       = ""
    prediction: str       = "normal"
    score:      float     = 0.0
    reasons:    List[str] = field(default_factory=list)


@dataclass
class RulesBlock:
    violations:      List[str] = field(default_factory=list)
    violation_count: int       = 0
    rule_names:      List[str] = field(default_factory=list)
    severity:        str       = "NONE"


@dataclass
class BayesianBlock:
    is_anomaly:  bool       = False
    score:       float      = 0.0
    probability: float      = 0.0
    threshold:   float      = 0.0
    root_causes: List[str]  = field(default_factory=list)
    confidence:  float      = 0.0


@dataclass
class SLABlock:
    risk_score:          float = 0.0
    risk_level:          str   = "LOW"
    priority:            str   = "P4"
    status:              str   = "NORMAL"
    response_time:       str   = "72 hours"
    escalation_required: bool  = False
    action:              str   = "Continue Normal Monitoring"
    recommendation:      str   = ""


@dataclass
class RAGBlock:
    recommendation:      str       = ""
    explanation:         str       = ""
    root_cause:          str       = ""
    recommended_actions: List[str] = field(default_factory=list)
    priority:            str       = "Medium"
    confidence:          float     = 0.0
    evidence:            List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Root record
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StandardAnomalyRecord:
    """
    One record in the unified pipeline output.
    All three datasets map onto this structure.
    """

    schema_version: str = "2.0"
    record_id:      str = ""
    dataset:        str = ""          # "claims" | "authorization" | "pharmacy"
    timestamp:      str = ""

    anomaly:  AnomalyBlock  = field(default_factory=AnomalyBlock)
    quality:  QualityBlock  = field(default_factory=QualityBlock)
    ml:       MLBlock       = field(default_factory=MLBlock)
    rules:    RulesBlock    = field(default_factory=RulesBlock)
    bayesian: BayesianBlock = field(default_factory=BayesianBlock)
    evidence: List[str]     = field(default_factory=list)
    sla:      SLABlock      = field(default_factory=SLABlock)
    rag:      RAGBlock      = field(default_factory=RAGBlock)

    # Dataset-specific fields preserved here
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Internal pipeline status
    processing_status: str = "pending"   # pending | sla_done | rag_done | complete
    processing_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_api_dict(self) -> Dict[str, Any]:
        """Serialisable dict suitable for the REST API response."""
        d = self.to_dict()
        return d


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

class SchemaValidationError(Exception):
    pass


def validate_standard_record(record: StandardAnomalyRecord) -> List[str]:
    """
    Returns a list of validation errors.
    Empty list means the record is valid.
    """
    errors: List[str] = []

    if not record.record_id:
        errors.append("record_id is empty")

    if record.dataset not in VALID_DATASETS:
        errors.append(f"dataset '{record.dataset}' is not one of {VALID_DATASETS}")

    if not (0.0 <= record.anomaly.anomaly_score <= 1.0):
        # Scores may legitimately be outside [0,1] in some ML outputs —
        # normalise rather than reject.
        pass

    if record.anomaly.severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL", "NONE"}:
        errors.append(f"anomaly.severity '{record.anomaly.severity}' is invalid")

    if record.sla.risk_level not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        errors.append(f"sla.risk_level '{record.sla.risk_level}' is invalid")

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_record_id(prefix: str, raw_id: str) -> str:
    """Build a stable unique record ID like CLAIMS-10091OR0770001."""
    if not raw_id:
        raw_id = str(uuid.uuid4())[:8]
    return f"{prefix.upper()}-{raw_id}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def signals_from_string(signals_str: str) -> List[str]:
    """Convert 'Rule, Bayesian, ML' → ['Rule', 'Bayesian', 'ML']."""
    if not signals_str or signals_str.strip().lower() in ("none", ""):
        return []
    return [s.strip() for s in signals_str.split(",") if s.strip()]


def quality_score_from_record(raw_record: Dict[str, Any]) -> float:
    """
    Derive a 0-100 quality score from the raw ML record.
    Rule: start at 100, subtract for anomaly signals.
    """
    final = raw_record.get("final_assessment", {})
    is_anomaly   = bool(final.get("anomaly", False))
    severity     = str(final.get("severity", "LOW")).upper()
    signal_count = int(final.get("signal_count", 0))

    if not is_anomaly:
        return 100.0

    deductions = {"LOW": 10, "MEDIUM": 25, "HIGH": 45, "CRITICAL": 65, "NONE": 0}
    base_deduction = deductions.get(severity, 10)
    signal_penalty = min(signal_count * 5, 20)

    return max(0.0, 100.0 - base_deduction - signal_penalty)
