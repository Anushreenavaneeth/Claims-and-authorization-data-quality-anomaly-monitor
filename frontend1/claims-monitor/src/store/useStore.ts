import { create } from "zustand";
import type {
  DataSource,
  QualityCheck,
  Anomaly,
  SLAItem,
  Recommendation,
  Resolution,
  ReviewItem,
  DashboardSummary,
} from "../types";

interface AppState {
  // Data
  dashboardSummary: DashboardSummary | null;
  dataSources: DataSource[];
  qualityChecks: QualityCheck[];
  anomalies: Anomaly[];
  slaItems: SLAItem[];
  recommendations: Recommendation[];
  resolutions: Resolution[];
  reviewItems: ReviewItem[];

  // UI State
  selectedAnomalyId: string | null;
  sidebarCollapsed: boolean;

  // Actions
  setDashboardSummary: (summary: DashboardSummary) => void;
  setDataSources: (sources: DataSource[]) => void;
  setQualityChecks: (checks: QualityCheck[]) => void;
  setAnomalies: (anomalies: Anomaly[]) => void;
  setSLAItems: (items: SLAItem[]) => void;
  setRecommendations: (recommendations: Recommendation[]) => void;
  setResolutions: (resolutions: Resolution[]) => void;
  setReviewItems: (items: ReviewItem[]) => void;
  setSelectedAnomalyId: (id: string | null) => void;
  toggleSidebar: () => void;
  updateAnomaly: (id: string, updates: Partial<Anomaly>) => void;
  updateResolution: (id: string, updates: Partial<Resolution>) => void;
  updateReviewItem: (id: string, updates: Partial<ReviewItem>) => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial State
  dashboardSummary: null,
  dataSources: [],
  qualityChecks: [],
  anomalies: [],
  slaItems: [],
  recommendations: [],
  resolutions: [],
  reviewItems: [],
  selectedAnomalyId: null,
  sidebarCollapsed: false,

  // Actions
  setDashboardSummary: (summary) => set({ dashboardSummary: summary }),
  setDataSources: (sources) => set({ dataSources: sources }),
  setQualityChecks: (checks) => set({ qualityChecks: checks }),
  setAnomalies: (anomalies) => set({ anomalies }),
  setSLAItems: (items) => set({ slaItems: items }),
  setRecommendations: (recommendations) => set({ recommendations }),
  setResolutions: (resolutions) => set({ resolutions }),
  setReviewItems: (items) => set({ reviewItems: items }),
  setSelectedAnomalyId: (id) => set({ selectedAnomalyId: id }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  
  updateAnomaly: (id, updates) =>
    set((state) => ({
      anomalies: state.anomalies.map((anomaly) =>
        anomaly.id === id ? { ...anomaly, ...updates } : anomaly
      ),
    })),
  
  updateResolution: (id, updates) =>
    set((state) => ({
      resolutions: state.resolutions.map((resolution) =>
        resolution.id === id ? { ...resolution, ...updates } : resolution
      ),
    })),
  
  updateReviewItem: (id, updates) =>
    set((state) => ({
      reviewItems: state.reviewItems.map((item) =>
        item.id === id ? { ...item, ...updates } : item
      ),
    })),
}));
