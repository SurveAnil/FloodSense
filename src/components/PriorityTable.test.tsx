import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { PriorityTable } from './PriorityTable';
import type { RiskLocation } from '../types/domain';

const baseLocation: RiskLocation = {
  id: 'test-location',
  name: 'Test location',
  area: 'Test area',
  risk: 'Critical',
  score: 88,
  updatedAt: '14:32 IST',
  predictionTime: 'Demo window',
  currentRainfall: '3.2 mm',
  forecastRainfall: '12 mm',
  drivers: [],
  historicalHotspot: false,
  coordinates: [18.5993, 73.7578],
  modelVersion: 'mentor-demo-scenario-v1',
  dataMode: 'replay',
  featureExplanations: [],
};

describe('PriorityTable demo location context', () => {
  it('shows the mock report aggregate and issue status beneath the location', () => {
    const markup = renderToStaticMarkup(
      <PriorityTable
        locations={[{
          ...baseLocation,
          demoContext: {
            citizenReportCount: 14,
            citizenReportExamples: [],
            fieldObservationSummary: 'Demo observation.',
            officialProblemStatus: 'Active',
            officialProblemSummary: 'Demo issue.',
            contextualNotes: 'Demo context.',
            sourceLabel: 'Not verified.',
          },
        }]}
        onSelect={vi.fn()}
      />,
    );

    expect(markup).toContain('Demo: 14 citizen reports · Active issue');
  });
});
