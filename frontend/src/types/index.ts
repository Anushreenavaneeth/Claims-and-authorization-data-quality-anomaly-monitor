// Data Source Types
export interface DataSource {
  id: string;
  name: string;
  type: "Claims" | "Prescriber" | "Pharmacy" | "Authorization";
  subType?: string;
  recordCount: number;
  lastSync: string;
  status: "healthy" | "warning" | "error" | "offline";
  errorCount: number;
  ingestionRate?: number;
  description?: string;
}

// Quality Check Types
export type QualityCheckType =
  | "Schema Validation"
  | "Completeness Check"
  | "Uniqueness Check"
  | "Referential Integrity"
  | "Business Rule Check";

export interface QualityCheck {
  id: string;
  name: string;
  type: QualityCheckType;
  recordsChecked: number;
  recordsFailed: number;
  passPercentage: number;
  lastRun: string;
  status: "pass" | "fail" | "warning";
  description?: string;
}

export interface QuarantinedRecord {
  id: string;
  recordId: string;
  sourceTable: string;
  sourceType: string;
  failReason: string;
  checkType: QualityCheckType;
  quarantinedAt: string;
  data?: Record<string, any>;
}

// Anomaly Types
export interface Anomaly {
  id: string;
  source: string;
  anomalyType: string;
  severityScore: number;
  detectedTime: string;
  status: "open" | "investigating" | "resolved" | "false_positive";
  rootCause?: string;
  impactAnalysis?: ImpactAnalysis;
  affectedRecords?: number;
  description: string;
}

export interface ImpactAnalysis {
  affectedClaimsCount: number;
  estimatedVolumeImpact: number;
  downstreamSystems: string[];
  businessImpact: string;
  financialImpact?: number;
}

// SLA & Priority Types
export interface SLAItem {
  id: string;
  title: string;
  priority: "High" | "Medium" | "Low";
  slaHours: number;
  detectedTime: string;
  estimatedResolutionTime: number;
  status: "on_track" | "at_risk" | "breached";
  assignedTo?: string;
  source: string;
}

// Recommendation Types
export interface Recommendation {
  id: string;
  anomalyId: string;
  actionType: "Fix Data" | "Reprocess" | "Escalate" | "Contact Team";
  description: string;
  confidence: number;
  relevanceScore: number;
  sopReference: string;
  estimatedEffort: string;
  steps?: string[];
}

export interface KnowledgeBaseItem {
  id: string;
  title: string;
  category: "SOP" | "Business Rule" | "Past Resolution" | "Policy";
  content: string;
  tags: string[];
  lastUpdated: string;
  relevanceCount: number;
}

// Resolution Types
export interface Resolution {
  id: string;
  anomalyId: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  actionType: "Fix Data" | "Reprocess Claims" | "Escalate/Contact Team";
  assignedTo: string;
  startTime?: string;
  completedTime?: string;
  notes: string[];
  slaDeadline: string;
}

// Feedback Types
export interface Feedback {
  id: string;
  anomalyId?: string;
  recommendationId?: string;
  wasHelpful: boolean;
  comments: string;
  suggestedImprovement?: string;
  submittedBy: string;
  submittedAt: string;
  category: "Recommendation Quality" | "Rule Improvement" | "False Positive" | "Other";
}

// Dashboard Summary Types
export interface DashboardSummary {
  totalRecordsProcessed: number;
  dataQualityPassRate: number;
  openAnomalies: number;
  slaBreaches: number;
  avgResolutionTime: number;
}

// Time Series Data
export interface TimeSeriesData {
  date: string;
  value: number;
  category?: string;
}

// Human Review Types
export interface ReviewItem {
  id: string;
  anomaly: Anomaly;
  recommendation: Recommendation;
  status: "pending_review" | "approved" | "rejected" | "modified";
  reviewedBy?: string;
  reviewedAt?: string;
  reviewComments?: string;
}

// Machine Learning Types
export interface MLContributingFeature {
  feature: string;
  value: number;
  direction: "above_normal" | "below_normal" | string;
  deviation_score: number;
}

export interface MLPredictionResult {
  authorization_id?: string;
  is_anomaly: boolean;
  anomaly_score: number;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  contributing_features: MLContributingFeature[];
  model: string;
}

export interface MLHealthStatus {
  status: "ready" | "unavailable";
  model?: string;
  features?: string[];
  error?: string;
}

export interface DatasetUploadResult {
  upload_id: string;
  filename: string;
  source_type: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  status: string;
  issues: {
    type: string;
    severity: string;
    column?: string;
    rows?: number;
    message: string;
  }[];
  anomalies_created: number;
  timestamp: string;
}

// User & Worker Management Types
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone_number?: string;
  role: "admin" | "worker" | string;
  is_active: boolean;
  has_password?: boolean;
  invite_token?: string;
  created_at?: string;
}

export interface WorkerCreatedResponse {
  worker: UserProfile;
  invite_token?: string;
  invite_url?: string;
  email_dispatched: boolean;
  message: string;
}

// Audit Trail & Change Monitoring Types
export interface AuditLogEntry {
  id: string;
  anomaly_id?: string;
  record_id?: string;
  source_dataset?: string;
  action: string;
  field_name?: string;
  old_value?: string;
  new_value?: string;
  performed_by: string;
  notes?: string;
  metadata_json?: Record<string, any>;
  timestamp: string;
}

export interface AuditTrailSummary {
  total: number;
  page: number;
  page_size: number;
  items: AuditLogEntry[];
}
