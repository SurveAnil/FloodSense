import { CheckCircle2, Clock3, CircleOff } from 'lucide-react';
import type { DataState } from '../types/domain';

const icons = { Available: CheckCircle2, Stale: Clock3, Unavailable: CircleOff };

export function StatusBadge({ state }: { state: DataState }) {
  const Icon = icons[state];
  return (
    <span className={`status-badge status-${state.toLowerCase()}`}>
      <Icon size={15} aria-hidden="true" />
      {state}
    </span>
  );
}
