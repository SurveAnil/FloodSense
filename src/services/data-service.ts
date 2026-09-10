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
