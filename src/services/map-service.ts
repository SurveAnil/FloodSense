import { ApiError, apiBaseUrl } from './auth-service';

export type MapFeatureType = 'CITIZEN_REPORT' | 'FIELD_OBSERVATION' | 'OFFICIAL_PROBLEM';

export interface MapFeature {
  id: string;
  feature_type: MapFeatureType;
  title: string;
  area: string;
  latitude: number;
  longitude: number;
  status: string;
  observed_at: string;
  category: string | null;
  outcome: 'PROBLEM_FOUND' | 'INSPECTED_NO_PROBLEM_FOUND' | null;
  severity: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | null;
}

export async function getMapFeatures(): Promise<MapFeature[]> {
  const response = await fetch(`${apiBaseUrl}/api/map/features`, { credentials: 'include' });
  if (!response.ok) {
    let message = 'Map observations could not be loaded.';
    try {
      const error = (await response.json()) as { detail?: string };
      if (error.detail) message = error.detail;
    } catch {
      // Keep the map-specific message for non-JSON errors.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as MapFeature[];
}
