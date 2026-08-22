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
