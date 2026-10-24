export function formatReportCount(count: number): string {
  return `${count} ${count === 1 ? 'report' : 'reports'}`;
}
