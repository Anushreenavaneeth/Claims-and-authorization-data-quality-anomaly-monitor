// Re-export integrated types so legacy store imports work
export type {
  IntegratedRecord as Anomaly,
  DashboardSummary,
  TrendData,
} from "./integrated";

// Minimal stubs for types used in useStore but not needed for our real API
export interface DataSource {
  id: string; name: string; type: string; subType?: string;
  recordCount: number; lastSync: string; status: string;
  errorCount: number; ingestionRate?: number; description?: string;
}
export interface QualityCheck {
  id: string; name: string; type: string; recordsChecked: number;
  recordsFailed: number; passPercentage: number; lastRun: string; status: string;
}
export interface SLAItem {
  id: string; title: string; priority: string; slaHours: number;
  detectedTime: string; estimatedResolutionTime: number; status: string;
  assignedTo?: string; source: string;
}
export interface Recommendation {
  id: string; anomalyId: string; actionType: string;
  description: string; confidence: number; relevanceScore: number;
  sopReference: string; estimatedEffort: string; steps?: string[];
}
export interface Resolution {
  id: string; anomalyId: string; status: string; actionType: string;
  assignedTo: string; startTime?: string; completedTime?: string;
  notes: string[]; slaDeadline: string;
}
export interface ReviewItem {
  id: string; anomaly: Record<string, unknown>; recommendation: Recommendation;
  status: string; reviewedBy?: string; reviewedAt?: string; reviewComments?: string;
}
