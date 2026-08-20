/**
 * API Service Layer
 * 
 * This module contains all API calls that will interact with the backend.
 * Currently using mock data - replace these implementations with actual
 * fetch/axios calls when backend is ready.
 * 
 * Pattern for each function:
 * 1. Import mock data
 * 2. Simulate async behavior with Promise
 * 3. Return mock data
 * 
 * To integrate with real backend:
 * 1. Replace mock imports with fetch calls
 * 2. Add error handling
 * 3. Add request/response type validation
 */

import {
  mockDashboardSummary,
  mockAnomalyTrends,
  mockSeverityBreakdown,
  mockDataSources,
  mockQualityChecks,
  mockQuarantinedRecords,
  mockAnomalies,
  mockSLAItems,
  mockRecommendations,
  mockKnowledgeBase,
  mockResolutions,
  mockFeedback,
  mockReviewItems,
} from "./mockData";

import type {
  DataSource,
  QualityCheck,
  QuarantinedRecord,
  Anomaly,
  SLAItem,
  Recommendation,
  KnowledgeBaseItem,
  Resolution,
  Feedback,
  DashboardSummary,
  TimeSeriesData,
  ReviewItem,
} from "../types";

// Simulate API delay
const delay = (ms: number = 300) => new Promise((resolve) => setTimeout(resolve, ms));

// Dashboard APIs
export async function getDashboardSummary(): Promise<DashboardSummary> {
  await delay();
  return mockDashboardSummary;
  // TODO: Replace with: return fetch('/api/dashboard/summary').then(r => r.json())
}

export async function getAnomalyTrends(): Promise<TimeSeriesData[]> {
  await delay();
  return mockAnomalyTrends;
  // TODO: Replace with: return fetch('/api/dashboard/anomaly-trends').then(r => r.json())
}

export async function getSeverityBreakdown(): Promise<TimeSeriesData[]> {
  await delay();
  return mockSeverityBreakdown;
  // TODO: Replace with: return fetch('/api/dashboard/severity-breakdown').then(r => r.json())
}

// Data Source APIs
export async function getDataSources(): Promise<DataSource[]> {
  await delay();
  return mockDataSources;
  // TODO: Replace with: return fetch('/api/sources').then(r => r.json())
}

export async function getDataSourceById(id: string): Promise<DataSource | undefined> {
  await delay();
  return mockDataSources.find((source) => source.id === id);
  // TODO: Replace with: return fetch(`/api/sources/${id}`).then(r => r.json())
}

// Quality Check APIs
export async function getQualityChecks(): Promise<QualityCheck[]> {
  await delay();
  return mockQualityChecks;
  // TODO: Replace with: return fetch('/api/quality-checks').then(r => r.json())
}

export async function getQuarantinedRecords(): Promise<QuarantinedRecord[]> {
  await delay();
  return mockQuarantinedRecords;
  // TODO: Replace with: return fetch('/api/quality-checks/quarantine').then(r => r.json())
}

// Anomaly APIs
export async function getAnomalies(): Promise<Anomaly[]> {
  await delay();
  return mockAnomalies;
  // TODO: Replace with: return fetch('/api/anomalies').then(r => r.json())
}

export async function getAnomalyById(id: string): Promise<Anomaly | undefined> {
  await delay();
  return mockAnomalies.find((anomaly) => anomaly.id === id);
  // TODO: Replace with: return fetch(`/api/anomalies/${id}`).then(r => r.json())
}

// SLA APIs
export async function getSLAItems(): Promise<SLAItem[]> {
  await delay();
  return mockSLAItems;
  // TODO: Replace with: return fetch('/api/sla-items').then(r => r.json())
}

// Recommendation APIs
export async function getRecommendations(): Promise<Recommendation[]> {
  await delay();
  return mockRecommendations;
  // TODO: Replace with: return fetch('/api/recommendations').then(r => r.json())
}

export async function getRecommendationsByAnomalyId(
  anomalyId: string
): Promise<Recommendation[]> {
  await delay();
  return mockRecommendations.filter((rec) => rec.anomalyId === anomalyId);
  // TODO: Replace with: return fetch(`/api/recommendations?anomalyId=${anomalyId}`).then(r => r.json())
}

// Knowledge Base APIs
export async function getKnowledgeBase(): Promise<KnowledgeBaseItem[]> {
  await delay();
  return mockKnowledgeBase;
  // TODO: Replace with: return fetch('/api/knowledge-base').then(r => r.json())
}

export async function searchKnowledgeBase(query: string): Promise<KnowledgeBaseItem[]> {
  await delay();
  const lowerQuery = query.toLowerCase();
  return mockKnowledgeBase.filter(
    (item) =>
      item.title.toLowerCase().includes(lowerQuery) ||
      item.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
  );
  // TODO: Replace with: return fetch(`/api/knowledge-base/search?q=${query}`).then(r => r.json())
}

// Resolution APIs
export async function getResolutions(): Promise<Resolution[]> {
  await delay();
  return mockResolutions;
  // TODO: Replace with: return fetch('/api/resolutions').then(r => r.json())
}

export async function getResolutionByAnomalyId(
  anomalyId: string
): Promise<Resolution | undefined> {
  await delay();
  return mockResolutions.find((res) => res.anomalyId === anomalyId);
  // TODO: Replace with: return fetch(`/api/resolutions?anomalyId=${anomalyId}`).then(r => r.json())
}

export async function updateResolutionStatus(
  id: string,
  status: Resolution["status"],
  note?: string
): Promise<Resolution> {
  await delay();
  const resolution = mockResolutions.find((res) => res.id === id);
  if (!resolution) throw new Error("Resolution not found");
  
  resolution.status = status;
  if (note) resolution.notes.push(note);
  if (status === "in_progress" && !resolution.startTime) {
    resolution.startTime = new Date().toISOString();
  }
  if (status === "completed") {
    resolution.completedTime = new Date().toISOString();
  }
  
  return resolution;
  // TODO: Replace with: return fetch(`/api/resolutions/${id}`, { method: 'PATCH', body: JSON.stringify({ status, note }) }).then(r => r.json())
}

// Review APIs
export async function getReviewItems(): Promise<ReviewItem[]> {
  await delay();
  return mockReviewItems;
  // TODO: Replace with: return fetch('/api/reviews').then(r => r.json())
}

export async function approveAction(
  id: string,
  comments?: string
): Promise<ReviewItem> {
  await delay();
  const item = mockReviewItems.find((rev) => rev.id === id);
  if (!item) throw new Error("Review item not found");
  
  item.status = "approved";
  item.reviewedBy = "Current User"; // TODO: Get from auth context
  item.reviewedAt = new Date().toISOString();
  item.reviewComments = comments;
  
  return item;
  // TODO: Replace with: return fetch(`/api/reviews/${id}/approve`, { method: 'POST', body: JSON.stringify({ comments }) }).then(r => r.json())
}

export async function rejectAction(
  id: string,
  comments: string
): Promise<ReviewItem> {
  await delay();
  const item = mockReviewItems.find((rev) => rev.id === id);
  if (!item) throw new Error("Review item not found");
  
  item.status = "rejected";
  item.reviewedBy = "Current User"; // TODO: Get from auth context
  item.reviewedAt = new Date().toISOString();
  item.reviewComments = comments;
  
  return item;
  // TODO: Replace with: return fetch(`/api/reviews/${id}/reject`, { method: 'POST', body: JSON.stringify({ comments }) }).then(r => r.json())
}

export async function modifyAction(
  id: string,
  modifiedRecommendation: Partial<Recommendation>,
  comments?: string
): Promise<ReviewItem> {
  await delay();
  const item = mockReviewItems.find((rev) => rev.id === id);
  if (!item) throw new Error("Review item not found");
  
  item.status = "modified";
  item.reviewedBy = "Current User"; // TODO: Get from auth context
  item.reviewedAt = new Date().toISOString();
  item.reviewComments = comments;
  Object.assign(item.recommendation, modifiedRecommendation);
  
  return item;
  // TODO: Replace with: return fetch(`/api/reviews/${id}/modify`, { method: 'POST', body: JSON.stringify({ modifiedRecommendation, comments }) }).then(r => r.json())
}

// Feedback APIs
export async function getFeedback(): Promise<Feedback[]> {
  await delay();
  return mockFeedback;
  // TODO: Replace with: return fetch('/api/feedback').then(r => r.json())
}

export async function submitFeedback(
  feedback: Omit<Feedback, "id" | "submittedAt" | "submittedBy">
): Promise<Feedback> {
  await delay();
  const newFeedback: Feedback = {
    ...feedback,
    id: `fb-${Date.now()}`,
    submittedBy: "Current User", // TODO: Get from auth context
    submittedAt: new Date().toISOString(),
  };
  mockFeedback.push(newFeedback);
  return newFeedback;
  // TODO: Replace with: return fetch('/api/feedback', { method: 'POST', body: JSON.stringify(feedback) }).then(r => r.json())
}
