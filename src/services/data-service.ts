import { puneDashboardData } from '../mock-data/pune';
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
  id: string; name: string; area: string; risk: RiskLocation['risk']; score: number;
  updated_at: string; prediction_time: string; current_rainfall: string;
  forecast_rainfall: string; drivers: string[]; historical_hotspot: boolean;
  coordinates: [number, number];
};

type BackendDashboard = {
  last_updated: string;
  rainfall: DashboardData['rainfall'];
  sources: Array<{ name: 'IMD' | 'CWC' | 'PMC' | 'GIS'; type: string; state: 'Available' | 'Stale' | 'Unavailable'; last_updated: string; detail: string }>;
  locations: BackendLocation[];
};

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

const normalizeLocation = (location: BackendLocation): RiskLocation => ({
  id: location.id,
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
});

export const apiDataService: FloodSenseDataService = {
  async getDashboardData() {
    const [dashboardResponse, healthResponse] = await Promise.all([
      fetch(`${apiBaseUrl}/api/dashboard`),
      fetch(`${apiBaseUrl}/health`),
    ]);
    if (!dashboardResponse.ok || !healthResponse.ok) {
      throw new Error('FloodSense backend is unavailable.');
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
    };
  },
  async getLocation(id) {
    const response = await fetch(`${apiBaseUrl}/api/locations/${id}`);
    if (response.status === 404) return undefined;
    if (!response.ok) throw new Error('Location data is unavailable.');
    return normalizeLocation((await response.json()) as BackendLocation);
  },
};
