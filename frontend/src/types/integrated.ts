// Types for the integrated anomaly pipeline output

export interface AnomalyBlock {
  is_anomaly:    boolean;
  anomaly_score: number;
  severity:      'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  signal_count:  number;
  signals:       string[];
}

export interface QualityBlock {
  quality_score: number;
  issues:        string[];
}

export interface MLBlock {
  model:      string;
  prediction: string;
  score:      number;
  reasons:    string[];
}

export interface RulesBlock {
  violations:      string[];
  violation_count: number;
  rule_names:      string[];
  severity:        string;
}

export interface BayesianBlock {
  is_anomaly:  boolean;
  score:       number;
  probability: number;
  threshold:   number;
  root_causes: string[];
  confidence:  number;
}

export interface SLABlock {
  risk_score:          number;
  risk_level:          'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priority:            'P1' | 'P2' | 'P3' | 'P4';
  status:              'NORMAL' | 'ELEVATED' | 'AT_RISK' | 'BREACHED';
  response_time:       string;
  escalation_required: boolean;
  action:              string;
  recommendation:      string;
}

export interface RAGBlock {
  recommendation:      string;
  explanation:         string;
  root_cause:          string;
  recommended_actions: string[];
  priority:            string;
  confidence:          number;
  evidence:            string[];
}

export interface IntegratedRecord {
  schema_version:    string;
  record_id:         string;
  dataset:           'claims' | 'authorization' | 'pharmacy';
  timestamp:         string;
  anomaly:           AnomalyBlock;
  quality:           QualityBlock;
  ml:                MLBlock;
  rules:             RulesBlock;
  bayesian:          BayesianBlock;
  evidence:          string[];
  sla:               SLABlock;
  rag:               RAGBlock;
  metadata:          Record<string, string>;
  processing_status: string;
  processing_errors: string[];
}

export interface PaginatedResponse<T> {
  total:     number;
  page:      number;
  page_size: number;
  items:     T[];
}

export interface DashboardSummary {
  total_records:         number;
  total_anomalies:       number;
  normal_records:        number;
  anomaly_rate:          number;
  critical_issues:       number;
  high_issues:           number;
  medium_issues:         number;
  low_issues:            number;
  sla_breaches:          number;
  sla_at_risk:           number;
  average_quality_score: number;
  datasets:              { dataset: string; total: number; anomalies: number }[];
  severity_distribution: Record<string, number>;
  sla_distribution:      Record<string, number>;
}

export interface TrendData {
  datasets:              { dataset: string; total: number; anomalies: number }[];
  severity_distribution: Record<string, number>;
  sla_distribution:      Record<string, number>;
  total_records:         number;
  total_anomalies:       number;
}
