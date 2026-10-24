import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { LocationDetail } from './LocationDetail';
import type { RiskLocation } from '../types/domain';

const location: RiskLocation = {
  id: 'loc-1',
  name: 'Test location',
  area: 'Test area',
  risk: 'Low',
  score: 10,
  updatedAt: '',
  predictionTime: '',
  currentRainfall: '',
  forecastRainfall: '',
  drivers: [],
  historicalHotspot: false,
  coordinates: [0, 0],
  dataMode: 'replay',
  featureExplanations: [],
};

describe('LocationDetail', () => {
  it('renders the parent-specific back label', () => {
    const markup = renderToStaticMarkup(
      <LocationDetail
        location={location}
        backLabel="Back to priority list"
        onBack={vi.fn()}
      />,
    );

    expect(markup).toContain('Back to priority list');
  });
});
