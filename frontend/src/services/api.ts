/**
 * API Service Layer — integrated with HDOP backend
 * Base URL: http://localhost:8000
 *
 * Auth token is read from localStorage (set by the main frontend login).
 * Falls back to mock data for endpoints not yet built in the backend.
 */

import axios from 'axios';
import type {
  DataSource, QualityCheck, QuarantinedRecord, Anomaly,
  SLAItem, Recommendation, KnowledgeBaseItem, Resolution,
  Feedback, DashboardSummary, TimeSeriesData, ReviewItem,
} from '../types';
import {
  mockDataSources, mockQualityChecks, mockQuarantinedRecords,
  mockSLAItems, mockRecommendations, mockKnowledgeBase,
  mockResolutions, mockFeedback, mockReviewItems,
  mockAnomalyTrends, mockSeverityBreakdown,
} from './mockData';

// ── Axios instance — picks up JWT from localStorage ──────────────────────
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

let tokenPromise: Promise<string | null> | null = null;

async function getDevToken(): Promise<string | null> {
  const existing = localStorage.getItem('access_token');
  if (existing) return existing;
  try {
    const res = await axios.post('http://localhost:8000/auth/login', {
      email: 'admin@example.com',
      password: 'Admin1234!',
    });
    if (res.data?.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(res.data.user));
      return res.data.access_token;
    }
  } catch {
    // backend offline or login failed
  }
  return null;
}

api.interceptors.request.use(async cfg => {
  let token = localStorage.getItem('access_token');
  if (!token) {
    if (!tokenPromise) {
      tokenPromise = getDevToken().finally(() => { tokenPromise = null; });
    }
    token = await tokenPromise;
  }
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// On 401 don't redirect — claims-monitor is standalone, just log it
api.interceptors.response.use(
  r => r,
  err => { console.warn('API error:', err.response?.status, err.config?.url); return Promise.reject(err); }
);

// ── Shape adapter: backend Anomaly → frontend Anomaly ────────────────────
// Backend fields: severity (CRITICAL/HIGH/MEDIUM/LOW), status (OPEN/IN_PROGRESS/RESOLVED/IGNORED)
// Frontend expects: severityScore (0-100), status (open/investigating/resolved/false_positive)

const SEVERITY_SCORE: Record<string, number> = {
  CRITICAL: 90, HIGH: 70, MEDIUM: 45, LOW: 15,
};

const STATUS_MAP: Record<string, Anomaly['status']> = {
  OPEN:        'open',
  IN_PROGRESS: 'investigating',
  RESOLVED:    'resolved',
  IGNORED:     'false_positive',
};

function adaptAnomaly(b: Record<string, unknown>): Anomaly {
  const sev = String(b.severity ?? 'MEDIUM').toUpperCase();
  const st  = String(b.status  ?? 'OPEN').toUpperCase();
  return {
    id:             String(b.id),
    source:         String(b.source_dataset ?? 'Unknown'),
    anomalyType:    String(b.anomaly_type ?? 'Unknown').replace(/_/g, ' '),
    severityScore:  SEVERITY_SCORE[sev] ?? 45,
    detectedTime:   String(b.timestamp ?? new Date().toISOString()),
    status:         STATUS_MAP[st] ?? 'open',
    affectedRecords: undefined,
    description:    String(b.error_message ?? ''),
    rootCause:      b.likely_cause   ? String(b.likely_cause)   : undefined,
    impactAnalysis: undefined,
  };
}

// ── Dashboard APIs ────────────────────────────────────────────────────────

export async function getDashboardSummary(): Promise<DashboardSummary> {
  try {
    const [, openRes] = await Promise.all([
      api.get('/anomalies?page_size=1'),
      api.get('/anomalies?status=OPEN&page_size=1'),
    ]);
    return {
      totalRecordsProcessed: 1245678,          // not tracked yet — static
      dataQualityPassRate:   96.8,              // not tracked yet — static
      openAnomalies:         openRes.data.total ?? 0,
      slaBreaches:           0,                 // SLA not built yet
      avgResolutionTime:     4.2,               // not tracked yet — static
    };
  } catch {
    return { totalRecordsProcessed: 0, dataQualityPassRate: 0, openAnomalies: 0, slaBreaches: 0, avgResolutionTime: 0 };
  }
}

export async function getAnomalyTrends(): Promise<TimeSeriesData[]> {
  // Not a built endpoint yet — keep mock
  return mockAnomalyTrends;
}

export async function getSeverityBreakdown(): Promise<TimeSeriesData[]> {
  try {
    const res = await api.get('/anomalies?page_size=200');
    const items: Record<string, unknown>[] = res.data.items ?? [];
    const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    items.forEach(a => { const s = String(a.severity ?? '').toUpperCase(); if (s in counts) counts[s]++; });
    return [
      { date: 'Critical', value: counts.CRITICAL, category: 'severity' },
      { date: 'High',     value: counts.HIGH,     category: 'severity' },
      { date: 'Medium',   value: counts.MEDIUM,   category: 'severity' },
      { date: 'Low',      value: counts.LOW,       category: 'severity' },
    ];
  } catch {
    return mockSeverityBreakdown;
  }
}

// ── Anomaly APIs (LIVE) ───────────────────────────────────────────────────

export async function getAnomalies(): Promise<Anomaly[]> {
  try {
    const res = await api.get('/anomalies?page_size=100');
    return (res.data.items ?? []).map(adaptAnomaly);
  } catch {
    return [];
  }
}

export async function getAnomalyById(id: string): Promise<Anomaly | undefined> {
  try {
    const res = await api.get(`/anomalies/${id}`);
    return adaptAnomaly(res.data);
  } catch {
    return undefined;
  }
}

export async function updateAnomalyStatus(
  id: string,
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'IGNORED' | 'IN_REVIEW'
): Promise<void> {
  await api.patch(`/anomalies/${id}/status`, { status });
}

export async function assignAnomalyToWorker(
  anomalyId: string,
  workerId: string | null,
  workerName?: string
): Promise<void> {
  await api.patch(`/anomalies/${anomalyId}/assign`, {
    worker_id: workerId,
    worker_name: workerName ?? null,
  });
}

export async function triggerRerun(id: string): Promise<void> {
  await api.post(`/anomalies/${id}/rerun`);
}

export async function getWorkersList(): Promise<Array<{
  id: string; name: string; email: string; role: string; is_active: boolean; is_archived?: boolean; created_at: string; contact?: string;
}>> {
  try {
    const token = localStorage.getItem('access_token');
    const res = await api.get('/admin/workers', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return Array.isArray(res.data) ? res.data : [];
  } catch {
    return [];
  }
}

export async function suspendWorker(workerId: string): Promise<void> {
  const token = localStorage.getItem('access_token');
  await api.patch(`/admin/workers/${workerId}/suspend`, {}, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

export async function reactivateWorker(workerId: string): Promise<void> {
  const token = localStorage.getItem('access_token');
  await api.patch(`/admin/workers/${workerId}/reactivate`, {}, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

export async function archiveWorker(workerId: string): Promise<void> {
  const token = localStorage.getItem('access_token');
  await api.patch(`/admin/workers/${workerId}/archive`, {}, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

export async function restoreWorker(workerId: string): Promise<void> {
  const token = localStorage.getItem('access_token');
  await api.patch(`/admin/workers/${workerId}/restore`, {}, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
}

// ── Notification & SMTP Settings APIs ────────────────────────────────────

export interface NotificationSettingsData {
  email_notifications_enabled: boolean;
  worker_invitations: boolean;
  critical_anomalies: boolean;
  sla_at_risk: boolean;
  sla_breached: boolean;
  pipeline_failures: boolean;
  worker_assignments: boolean;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_password_configured?: boolean;
  smtp_from_email?: string;
  smtp_from_name?: string;
  smtp_use_tls?: boolean;
  admin_alert_email?: string;
}

export async function getNotificationSettings(): Promise<NotificationSettingsData> {
  const token = localStorage.getItem('access_token');
  const res = await api.get('/admin/notifications/settings', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.data;
}

export async function updateNotificationSettings(
  settings: Partial<NotificationSettingsData>
): Promise<NotificationSettingsData> {
  const token = localStorage.getItem('access_token');
  const res = await api.post('/admin/notifications/settings', settings, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.data;
}

export async function testSMTPConnection(
  recipientEmail: string,
  customSettings?: Partial<NotificationSettingsData>
): Promise<{ success: boolean; recipient: string; message: string }> {
  const token = localStorage.getItem('access_token');
  const res = await api.post('/admin/notifications/test-email', {
    recipient_email: recipientEmail,
    ...(customSettings || {}),
  }, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.data;
}




// ── Data Source APIs (mock — backend tracks uploads, not persistent sources) ──

export async function getDataSources(): Promise<DataSource[]> {
  return mockDataSources;
}

export async function getDataSourceById(id: string): Promise<DataSource | undefined> {
  return mockDataSources.find(s => s.id === id);
}

// ── Quality Check APIs (mock — ETL team builds this) ─────────────────────

export async function getQualityChecks(): Promise<QualityCheck[]> {
  return mockQualityChecks;
}

export async function getQuarantinedRecords(): Promise<QuarantinedRecord[]> {
  return mockQuarantinedRecords;
}

// ── SLA APIs (mock — not built yet) ──────────────────────────────────────

export async function getSLAItems(): Promise<SLAItem[]> {
  return mockSLAItems;
}

// ── Recommendation APIs — RAG endpoint for per-anomaly recommendations ────

export async function getRecommendations(): Promise<Recommendation[]> {
  return mockRecommendations;
}

export async function getRecommendationsByAnomalyId(anomalyId: string): Promise<Recommendation[]> {
  return mockRecommendations.filter(r => r.anomalyId === anomalyId);
}

export async function getAIRecommendation(anomalyId: string): Promise<{
  admin_summary: string;
  employee_action: string;
  recommendation: string;
  root_cause?: { cause: string };
  resolution?: { procedure: string };
  severity: string;
  priority: string;
  rag_available: boolean;
  rag_error?: string;
}> {
  const res = await api.get(`/anomalies/${anomalyId}/recommend`);
  return res.data;
}

// ── Knowledge Base APIs (mock) ────────────────────────────────────────────

export async function getKnowledgeBase(): Promise<KnowledgeBaseItem[]> {
  return mockKnowledgeBase;
}

export async function searchKnowledgeBase(query: string): Promise<KnowledgeBaseItem[]> {
  const q = query.toLowerCase();
  return mockKnowledgeBase.filter(
    item => item.title.toLowerCase().includes(q) || item.tags.some(t => t.toLowerCase().includes(q))
  );
}

// ── Resolution APIs — status changes go to real backend ──────────────────

export async function getResolutions(): Promise<Resolution[]> {
  // Map live anomalies into resolution objects
  try {
    const res = await api.get('/anomalies?page_size=100');
    const items: Record<string, unknown>[] = res.data.items ?? [];
    return items.map(a => ({
      id:          `res-${a.id}`,
      anomalyId:   String(a.id),
      status:      a.status === 'RESOLVED' ? 'completed'
                 : a.status === 'IN_PROGRESS' ? 'in_progress'
                 : 'pending',
      actionType:  'Fix Data' as Resolution['actionType'],
      assignedTo:  'Unassigned',
      notes:       [String(a.recommended_fix ?? '')].filter(Boolean),
      slaDeadline: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
    } as Resolution));
  } catch {
    return mockResolutions;
  }
}

export async function getResolutionByAnomalyId(anomalyId: string): Promise<Resolution | undefined> {
  const all = await getResolutions();
  return all.find(r => r.anomalyId === anomalyId);
}

export async function updateResolutionStatus(
  id: string,
  status: Resolution['status'],
  note?: string
): Promise<Resolution> {
  // id format: "res-{anomalyId}"
  const anomalyId = id.replace('res-', '');
  const backendStatus =
    status === 'completed'   ? 'RESOLVED'    :
    status === 'in_progress' ? 'IN_PROGRESS' :
    status === 'failed'      ? 'IGNORED'     : 'OPEN';

  await api.patch(`/anomalies/${anomalyId}/status`, { status: backendStatus });

  const resolution = mockResolutions.find(r => r.id === id) ?? {
    id, anomalyId, status, actionType: 'Fix Data' as Resolution['actionType'],
    assignedTo: 'Current User', notes: [], slaDeadline: new Date().toISOString(),
  };
  resolution.status = status;
  if (note) resolution.notes.push(note);
  if (status === 'in_progress' && !resolution.startTime) resolution.startTime = new Date().toISOString();
  if (status === 'completed') resolution.completedTime = new Date().toISOString();
  return resolution;
}

// ── Review APIs — approve/reject maps to anomaly status ──────────────────

export async function getReviewItems(): Promise<ReviewItem[]> {
  try {
    const res = await api.get('/anomalies?status=OPEN&page_size=50');
    const items: Record<string, unknown>[] = res.data.items ?? [];
    return items.map((a, i) => ({
      id:             `rev-${a.id}`,
      anomaly:        adaptAnomaly(a),
      recommendation: mockRecommendations[i % mockRecommendations.length],
      status:         'pending_review' as ReviewItem['status'],
    }));
  } catch {
    return mockReviewItems;
  }
}

export async function approveAction(id: string, comments?: string): Promise<ReviewItem> {
  const anomalyId = id.replace('rev-', '');
  await api.patch(`/anomalies/${anomalyId}/status`, { status: 'RESOLVED' });
  const item = mockReviewItems.find(r => r.id === id) ?? mockReviewItems[0];
  return { ...item, status: 'approved', reviewedBy: 'Current User', reviewedAt: new Date().toISOString(), reviewComments: comments };
}

export async function rejectAction(id: string, comments: string): Promise<ReviewItem> {
  const anomalyId = id.replace('rev-', '');
  await api.patch(`/anomalies/${anomalyId}/status`, { status: 'IGNORED' });
  const item = mockReviewItems.find(r => r.id === id) ?? mockReviewItems[0];
  return { ...item, status: 'rejected', reviewedBy: 'Current User', reviewedAt: new Date().toISOString(), reviewComments: comments };
}

export async function modifyAction(
  id: string,
  modifiedRecommendation: Partial<Recommendation>,
  comments?: string
): Promise<ReviewItem> {
  const item = mockReviewItems.find(r => r.id === id) ?? mockReviewItems[0];
  Object.assign(item.recommendation, modifiedRecommendation);
  return { ...item, status: 'modified', reviewedBy: 'Current User', reviewedAt: new Date().toISOString(), reviewComments: comments };
}

// ── Feedback APIs (mock) ──────────────────────────────────────────────────

export async function getFeedback(): Promise<Feedback[]> {
  return mockFeedback;
}

export async function submitFeedback(
  feedback: Omit<Feedback, 'id' | 'submittedAt' | 'submittedBy'>
): Promise<Feedback> {
  const newFeedback: Feedback = {
    ...feedback,
    id: `fb-${Date.now()}`,
    submittedBy: 'Current User',
    submittedAt: new Date().toISOString(),
  };
  mockFeedback.push(newFeedback);
  return newFeedback;
}

// ── ML Anomaly Detection & Ingestion APIs (LIVE) ──────────────────────────

export async function getMLHealth(): Promise<import('../types').MLHealthStatus> {
  try {
    const res = await api.get('/ml/health');
    return res.data;
  } catch (err: any) {
    return {
      status: 'unavailable',
      error: err.response?.data?.detail || 'Cannot connect to ML service on port 8000',
    };
  }
}

export async function predictAuthorizationAnomaly(
  record: Record<string, any>
): Promise<import('../types').MLPredictionResult> {
  const res = await api.post('/ml/predict', record);
  return res.data;
}

export async function analyzeAndStoreAnomaly(
  record: Record<string, any>
): Promise<any> {
  const res = await api.post('/ml/analyze-and-store', { record, auto_store: true });
  return res.data;
}

export async function uploadDatasetFile(
  file: File,
  sourceType: 'CLAIMS' | 'PHARMACY' | 'AUTHORIZATION'
): Promise<import('../types').DatasetUploadResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('source_type', sourceType);

  const res = await api.post('/datasets/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

// ── Auth APIs (LIVE) ──────────────────────────────────────────────────────

export async function loginUser(email: string, password: string): Promise<{ access_token: string; user: import('../types').UserProfile }> {
  const res = await api.post('/auth/login', { email, password });
  return res.data;
}

export async function getMe(): Promise<import('../types').UserProfile> {
  const res = await api.get('/auth/me');
  return res.data;
}

export async function verifyInviteToken(token: string): Promise<{ valid: boolean; email?: string; name?: string; message?: string }> {
  const res = await api.get('/auth/verify-token', { params: { token } });
  return res.data;
}

export async function setPasswordWithToken(token: string, password: string): Promise<{ access_token: string; user: import('../types').UserProfile }> {
  const res = await api.post('/auth/set-password', { token, password });
  return res.data;
}

// ── Worker Management APIs (LIVE) ─────────────────────────────────────────

export async function getWorkers(): Promise<import('../types').UserProfile[]> {
  const res = await api.get('/admin/workers');
  return res.data;
}

export async function createWorker(payload: {
  name: string;
  email: string;
  phone_number?: string;
  password?: string;
}): Promise<import('../types').WorkerCreatedResponse> {
  const res = await api.post('/admin/workers', payload);
  return res.data;
}

export async function resendWorkerInvite(workerId: string): Promise<import('../types').WorkerCreatedResponse> {
  const res = await api.post(`/admin/workers/${workerId}/resend-invite`);
  return res.data;
}

export async function deactivateWorker(workerId: string): Promise<import('../types').UserProfile> {
  const res = await api.patch(`/admin/workers/${workerId}/deactivate`);
  return res.data;
}

// ── Audit Trail & Change History APIs (LIVE) ──────────────────────────────

export async function getAuditTrail(params?: {
  anomaly_id?: string;
  record_id?: string;
  action?: string;
  source_dataset?: string;
  performed_by?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<import('../types').AuditTrailSummary> {
  try {
    const res = await api.get('/audit-trail', { params });
    return res.data;
  } catch {
    return { total: 0, page: 1, page_size: 20, items: [] };
  }
}

export async function createAuditEntry(payload: {
  anomaly_id?: string;
  record_id?: string;
  source_dataset?: string;
  action: string;
  field_name?: string;
  old_value?: string;
  new_value?: string;
  performed_by?: string;
  notes?: string;
  metadata_json?: Record<string, any>;
}): Promise<import('../types').AuditLogEntry> {
  const res = await api.post('/audit-trail', payload);
  return res.data;
}
