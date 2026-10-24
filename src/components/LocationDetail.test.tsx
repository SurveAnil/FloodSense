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

  it('labels supplied hotspot notes as demo context instead of verified reports', () => {
    const markup = renderToStaticMarkup(
      <LocationDetail
        location={{
          ...location,
          demoContext: {
            citizenReportCount: 14,
            citizenReportExamples: ['Vehicles stalled near underpass'],
            fieldObservationSummary: 'Demo observation: water pooling.',
            officialProblemStatus: 'Active',
            officialProblemSummary: 'Demo issue: drainage needs review.',
            contextualNotes: 'Demo scenario: light rain causes congestion.',
            sourceLabel: 'User-supplied demonstration scenario; not verified.',
          },
        }}
        backLabel="Back"
        onBack={vi.fn()}
      />,
    );

    expect(markup).toContain('Demo scenario context — not verified');
    expect(markup).toContain('Demo scenario score');
    expect(markup).toContain('Scenario applies');
    expect(markup).toContain('not an output from the baseline model');
    expect(markup).toContain('14 mock citizen reports');
    expect(markup).toContain('Vehicles stalled near underpass');
  });

  it('labels location illustrations as non-ground-truth imagery', () => {
    const markup = renderToStaticMarkup(
      <LocationDetail
        location={{
          ...location,
          illustrativeImageUrl: '/images/locations/test.svg',
        }}
        backLabel="Back"
        onBack={vi.fn()}
      />,
    );

    expect(markup).toContain('src="/images/locations/test.svg"');
    expect(markup).toContain('not a verified ground-truth photo');
    expect(markup).toContain('Replace with a location-verified image when available.');
  });
});
