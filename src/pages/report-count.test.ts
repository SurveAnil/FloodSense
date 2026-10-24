import { describe, expect, it } from 'vitest';
import { formatReportCount } from './report-count';

describe('formatReportCount', () => {
  it('uses the singular form for exactly one report', () => {
    expect(formatReportCount(1)).toBe('1 report');
  });

  it('uses the plural form for zero and multiple reports', () => {
    expect(formatReportCount(0)).toBe('0 reports');
    expect(formatReportCount(2)).toBe('2 reports');
  });
});
