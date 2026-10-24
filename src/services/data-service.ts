import { puneDashboardData } from '../mock-data/pune';
import { ApiError, apiBaseUrl } from './auth-service';
import type { DashboardData, RiskLocation } from '../types/domain';

export interface FloodSenseDataService {
  getDashboardData(): Promise<DashboardData>;
  getLocation(id: string): Promise<RiskLocation | undefined>;
}

export const mockDataService: FloodSenseDataService = {
  async getDashboardData() {
    return puneDashboardData;
  },
  async getLocation(id) {
    return puneDashboardData.locations.find((location) => location.id === id);
  },
};

type BackendLocation = {
  id: string; risk_prediction_id: string; name: string; area: string; risk: RiskLocation['risk']; score: number;
  updated_at: string; prediction_time: string; current_rainfall: string;
  forecast_rainfall: string; drivers: string[]; historical_hotspot: boolean;
  coordinates: [number, number];
  model_version: string | null; data_mode: 'replay' | 'live' | 'unknown';
  feature_explanations: RiskLocation['featureExplanations'];
  demo_context?: {
    citizen_report_count: number;
    citizen_report_examples: string[];
    field_observation_summary: string;
    official_problem_status: NonNullable<RiskLocation['demoContext']>['officialProblemStatus'];
    official_problem_summary: string;
    contextual_notes: string;
    source_label: string;
  } | null;
};

type BackendDashboard = {
  last_updated: string;
  model_version?: string | null;
  rainfall: DashboardData['rainfall'];
  sources: Array<{ name: 'IMD' | 'CWC' | 'PMC' | 'GIS'; type: string; state: 'Available' | 'Stale' | 'Unavailable'; last_updated: string; detail: string }>;
  locations: BackendLocation[];
};

const normalizeLocation = (location: BackendLocation): RiskLocation => ({
  id: location.id,
  riskPredictionId: location.risk_prediction_id,
  name: location.name,
  area: location.area,
  risk: location.risk,
  score: location.score,
  updatedAt: location.updated_at,
  predictionTime: location.prediction_time,
  currentRainfall: location.current_rainfall,
  forecastRainfall: location.forecast_rainfall,
  drivers: location.drivers,
  historicalHotspot: location.historical_hotspot,
  coordinates: location.coordinates,
  modelVersion: location.model_version ?? undefined,
  dataMode: location.data_mode,
  featureExplanations: location.feature_explanations,
  demoContext: location.demo_context ? {
    citizenReportCount: location.demo_context.citizen_report_count,
    citizenReportExamples: location.demo_context.citizen_report_examples,
    fieldObservationSummary: location.demo_context.field_observation_summary,
    officialProblemStatus: location.demo_context.official_problem_status,
    officialProblemSummary: location.demo_context.official_problem_summary,
    contextualNotes: location.demo_context.contextual_notes,
    sourceLabel: location.demo_context.source_label,
  } : undefined,
});

export const apiDataService: FloodSenseDataService = {
  async getDashboardData() {
    const [dashboardResponse, healthResponse] = await Promise.all([
      fetch(`${apiBaseUrl}/api/dashboard`, { credentials: 'include' }),
      fetch(`${apiBaseUrl}/health`, { credentials: 'include' }),
    ]);
    if (!dashboardResponse.ok || !healthResponse.ok) {
      const response = !dashboardResponse.ok ? dashboardResponse : healthResponse;
      throw new ApiError('FloodSense risk information is unavailable.', response.status);
    }
    const dashboard = (await dashboardResponse.json()) as BackendDashboard;
    const health = (await healthResponse.json()) as { data_mode?: DashboardData['dataMode'] };
    return {
      lastUpdated: dashboard.last_updated,
      rainfall: dashboard.rainfall,
      sources: dashboard.sources.map((source) => ({
        name: source.name,
        type: source.type,
        state: source.state,
        lastUpdated: source.last_updated,
        detail: source.detail,
      })),
      locations: dashboard.locations.map(normalizeLocation),
      dataMode: health.data_mode ?? 'unknown',
      modelVersion: dashboard.model_version ?? undefined,
    };
  },
  async getLocation(id) {
    const response = await fetch(`${apiBaseUrl}/api/locations/${id}`, { credentials: 'include' });
    if (response.status === 404) return undefined;
    if (!response.ok) throw new ApiError('Location data is unavailable.', response.status);
    return normalizeLocation((await response.json()) as BackendLocation);
  },
};
