import { AlertTriangle, Circle, Diamond, Square } from 'lucide-react';
import type { RiskLevel } from '../types/domain';

const config = {
  Low: { className: 'risk-low', Icon: Circle },
  Moderate: { className: 'risk-moderate', Icon: Diamond },
  High: { className: 'risk-high', Icon: AlertTriangle },
  Critical: { className: 'risk-critical', Icon: Square },
} as const;

export function RiskBadge({ risk, compact = false }: { risk: RiskLevel; compact?: boolean }) {
  const { className, Icon } = config[risk];
  return (
    <span className={`risk-badge ${className} ${compact ? 'risk-badge-compact' : ''}`}>
      <Icon size={compact ? 13 : 15} strokeWidth={2.5} aria-hidden="true" />
      {risk}
    </span>
  );
}
