export type RiskLevel = 'Low' | 'Moderate' | 'High' | 'Critical';
export type DataState = 'Available' | 'Stale' | 'Unavailable';

export interface RiskLocation {
  id: string;
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
  rainfall: {
    current: string;
    forecast: string;
    nowcast: string;
    outlook: string;
  };
}
