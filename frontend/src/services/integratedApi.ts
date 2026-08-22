// API service for the integrated anomaly pipeline endpoints

import api from './api';
import type {
  DashboardSummary,
  IntegratedRecord,
  PaginatedResponse,
  TrendData,
} from '../types/integrated';

export interface AnomalyQueryParams {
  dataset?:    string;
  severity?:   string;
  sla_status?: string;
  is_anomaly?: boolean;
  search?:     string;
  page?:       number;
  page_size?:  number;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>('/api/dashboard/summary');
  return data;
}

export async function getIntegratedAnomalies(
  params: AnomalyQueryParams = {},
): Promise<PaginatedResponse<IntegratedRecord>> {
  const { data } = await api.get<PaginatedResponse<IntegratedRecord>>(
    '/api/anomalies/integrated',
    { params },
  );
  return data;
}

export async function getIntegratedAnomaly(recordId: string): Promise<IntegratedRecord> {
  const { data } = await api.get<IntegratedRecord>(`/api/anomalies/integrated/${recordId}`);
  return data;
}

export async function getSLAForRecord(recordId: string) {
  const { data } = await api.get(`/api/anomalies/integrated/${recordId}/sla`);
  return data;
}

export async function getRecommendation(recordId: string) {
  const { data } = await api.get(`/api/anomalies/integrated/${recordId}/recommendation`);
  return data;
}

export async function getTrends(dataset?: string): Promise<TrendData> {
  const { data } = await api.get<TrendData>('/api/trends', {
    params: dataset ? { dataset } : {},
  });
  return data;
}

export async function getRootCauses(dataset?: string) {
  const { data } = await api.get('/api/root-causes', {
    params: dataset ? { dataset } : {},
  });
  return data;
}

export async function triggerPipeline(options: {
  dataset?: string;
  max_records?: number;
}) {
  const { data } = await api.post('/api/process', options);
  return data;
}

// ── Review API ───────────────────────────────────────────────────────────

export interface ReviewRecord {
  id:                      string;
  anomaly_record_id:       string;
  dataset:                 string;
  recommendation_snapshot: string | null;
  status:                  'pending_review' | 'approved' | 'rejected' | 'modified';
  reviewed_by:             string | null;
  review_comments:         string | null;
  reviewed_at:             string | null;
  created_at:              string;
  updated_at:              string;
}

export async function createReview(params: {
  anomaly_record_id: string;
  dataset: string;
  recommendation_snapshot?: string;
}): Promise<ReviewRecord> {
  const { data } = await api.post<ReviewRecord>('/reviews', params);
  return data;
}

export async function getReviews(params: {
  status?: string;
  dataset?: string;
  page?: number;
  page_size?: number;
}): Promise<ReviewRecord[]> {
  const { data } = await api.get<ReviewRecord[]>('/reviews', { params });
  return data;
}

export async function approveReview(id: string, comments?: string): Promise<ReviewRecord> {
  const { data } = await api.patch<ReviewRecord>(`/reviews/${id}/approve`, { comments });
  return data;
}

export async function rejectReview(id: string, comments: string): Promise<ReviewRecord> {
  const { data } = await api.patch<ReviewRecord>(`/reviews/${id}/reject`, { comments });
  return data;
}

export async function modifyReview(id: string, modified_recommendation: string, comments?: string): Promise<ReviewRecord> {
  const { data } = await api.patch<ReviewRecord>(`/reviews/${id}/modify`, { modified_recommendation, comments });
  return data;
}

// ── Actions API ──────────────────────────────────────────────────────────

export interface ActionRecord {
  id:                string;
  review_id:         string;
  anomaly_record_id: string;
  dataset:           string;
  action_type:       string;
  description:       string | null;
  status:            'created' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  assigned_to:       string | null;
  assigned_by:       string | null;
  assigned_at:       string | null;
  started_at:        string | null;
  completed_at:      string | null;
  notes:             string | null;
  resolution_notes:  string | null;
  created_at:        string;
  updated_at:        string;
}

export async function createAction(params: {
  review_id: string;
  action_type: string;
  description?: string;
}): Promise<ActionRecord> {
  const { data } = await api.post<ActionRecord>('/actions', params);
  return data;
}

export async function getActions(params: {
  status?: string;
  assigned_to?: string;
  dataset?: string;
}): Promise<ActionRecord[]> {
  const { data } = await api.get<ActionRecord[]>('/actions', { params });
  return data;
}

export async function assignAction(id: string, worker_id: string): Promise<ActionRecord> {
  const { data } = await api.patch<ActionRecord>(`/actions/${id}/assign`, { worker_id });
  return data;
}

export async function updateActionStatus(id: string, params: {
  status: string;
  notes?: string;
  resolution_notes?: string;
}): Promise<ActionRecord> {
  const { data } = await api.patch<ActionRecord>(`/actions/${id}/status`, params);
  return data;
}

// ── Workers list (for assignment dropdown) ────────────────────────────────
export async function getWorkers(): Promise<{ id: string; name: string; email: string; is_active: boolean }[]> {
  const { data } = await api.get('/admin/workers');
  return data;
}
