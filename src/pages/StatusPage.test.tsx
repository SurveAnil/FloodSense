import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { DashboardData } from '../types/domain';
import { StatusPage } from './StatusPage';

describe('StatusPage', () => {
  it('distinguishes live weather freshness from replay source labels', () => {
    const data: DashboardData = {
      dataMode: 'replay',
      lastUpdated: 'replay label',
      rainfall: { current: '', forecast: '', nowcast: '', outlook: '' },
      locations: [],
      sources: [
        {
          name: 'Open-Meteo',
          type: 'Live weather observation',
          state: 'Available',
          lastUpdated: '2026-10-24T12:00+05:30',
          detail: 'Live Open-Meteo observation.',
        },
      ],
    };
    const markup = renderToStaticMarkup(<StatusPage data={data} />);

    expect(markup).toContain('Mixed live and replay source status.');
    expect(markup).toContain('Observed at');
    expect(markup).toContain('2026-10-24T12:00+05:30');
    expect(markup).toContain('Live weather does not update the replay risk predictions.');
  });
});
