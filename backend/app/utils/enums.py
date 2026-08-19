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

class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyStatus(str, Enum):
    DETECTED = "detected"
    UNDER_INVESTIGATION = "under_investigation"
    REMEDIATED = "remediated"
    FALSE_POSITIVE = "false_positive"

class SLABreachRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BREACHED = "breached"
