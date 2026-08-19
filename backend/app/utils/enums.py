from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    WORKER = "worker"
    VIEWER = "viewer"

class PipelineStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ANOMALOUS = "anomalous"

# ── Anomaly enums — match frontend types exactly ──────────────────────────

class SourceDataset(str, Enum):
    CLAIMS        = "CLAIMS"
    PHARMACY      = "PHARMACY"
    AUTHORIZATION = "AUTHORIZATION"

class AnomalyType(str, Enum):
    MISSING_FIELD          = "MISSING_FIELD"
    TYPE_MISMATCH          = "TYPE_MISMATCH"
    NEGATIVE_VALUE         = "NEGATIVE_VALUE"
    DUPLICATE_RECORD       = "DUPLICATE_RECORD"
    SLA_PROCESSING_SPIKE   = "SLA_PROCESSING_SPIKE"
    INVALID_DOMAIN         = "INVALID_DOMAIN"

class AnomalySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"

class AnomalyStatus(str, Enum):
    OPEN        = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED    = "RESOLVED"
    IGNORED     = "IGNORED"

class SLABreachRisk(str, Enum):
    NONE     = "none"
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    BREACHED = "breached"
