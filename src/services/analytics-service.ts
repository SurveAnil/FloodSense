import { ApiError, apiBaseUrl } from './auth-service';

export interface RiskHistoryItem {
  id: string;
  score: number;
  risk_category: 'Low' | 'Moderate' | 'High' | 'Critical';
  prediction_time: string;
  created_at: string;
  model_version: string;
  data_mode: 'replay' | 'live' | 'unknown';
}

export interface RiskObservation {
  source_type: 'FIELD_REPORT' | 'FIELD_VERIFICATION';
  outcome: 'PROBLEM_FOUND' | 'INSPECTED_NO_PROBLEM_FOUND' | 'VERIFIED' | 'NOT_VERIFIED';
  observed_at: string;
  review_status: string | null;
  linked_prediction_id: string | null;
}

export interface RiskAnalyticsLocation {
  location_id: string;
  name: string;
  area: string;
  historical_hotspot_reference: boolean;
  latest_prediction: RiskHistoryItem | null;
  prediction_history: RiskHistoryItem[];
  observation_history: RiskObservation[];
  officially_approved_problem_count: number;
}

export interface RiskAnalytics {
  summary: {
    data_mode: 'replay' | 'live' | 'unknown';
    model_versions: string[];
    prediction_snapshots: number;
    latest_snapshot_high_risk_locations: number;
    historical_hotspot_references: number;
    field_problem_findings: number;
    no_problem_inspections: number;
    verified_citizen_report_findings: number;
    not_verified_citizen_reports: number;
    officially_approved_problems: number;
    high_risk_with_problem_observation: number;
    high_risk_with_no_problem_inspection: number;
    high_risk_without_matching_inspection: number;
    lower_risk_with_problem_observation: number;
    period_start: string | null;
    period_end: string | null;
    evaluation_notice: string;
  };
  locations: RiskAnalyticsLocation[];
}

export async function getRiskAnalytics(): Promise<RiskAnalytics> {
  const response = await fetch(`${apiBaseUrl}/api/analytics/risk-observations`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new ApiError('Risk analytics could not be loaded.', response.status);
  }
  return (await response.json()) as RiskAnalytics;
}
