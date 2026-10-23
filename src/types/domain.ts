export type RiskLevel = 'Low' | 'Moderate' | 'High' | 'Critical';
export type DataState = 'Available' | 'Stale' | 'Unavailable';

export interface RiskLocation {
  id: string;
  riskPredictionId?: string;
  name: string;
  area: string;
  risk: RiskLevel;
  score: number;
  updatedAt: string;
  predictionTime: string;
  currentRainfall: string;
  forecastRainfall: string;
  drivers: string[];
  historicalHotspot: boolean;
  coordinates: [number, number];
  modelVersion?: string;
  dataMode: 'replay' | 'live' | 'unknown';
  featureExplanations: Array<{
    feature: string;
    input_value: number;
    logit_contribution: number;
    interpretation: 'increases' | 'decreases' | 'neutral';
  }>;
}

export interface DataSourceStatus {
  name: 'IMD' | 'CWC' | 'PMC' | 'GIS';
  type: string;
  state: DataState;
  lastUpdated: string;
  detail: string;
}

export interface DashboardData {
  locations: RiskLocation[];
  sources: DataSourceStatus[];
  lastUpdated: string;
  dataMode: 'replay' | 'live' | 'unknown';
  modelVersion?: string;
  rainfall: {
    current: string;
    forecast: string;
    nowcast: string;
    outlook: string;
  };
}
