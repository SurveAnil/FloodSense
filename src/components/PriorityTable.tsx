import { ArrowUpRight } from 'lucide-react';
import type { RiskLocation } from '../types/domain';
import { RiskBadge } from './RiskBadge';

export function PriorityTable({ locations, onSelect, compact = false }: { locations: RiskLocation[]; onSelect: (id: string) => void; compact?: boolean }) {
  const rows = compact ? locations.filter((location) => location.risk === 'Critical' || location.risk === 'High').slice(0, 3) : locations;
  return (
    <div className="table-wrap">
      <table className="priority-table">
        <caption className="sr-only">Ranked flood-risk locations</caption>
        <thead><tr><th scope="col">Rank</th><th scope="col">Location</th><th scope="col">Risk</th><th scope="col">Score</th><th scope="col">Updated</th><th scope="col" aria-label="Actions"></th></tr></thead>
        <tbody>{rows.map((location, index) => <tr key={location.id}>
          <td><span className={`rank rank-${index + 1}`}>{index + 1}</span></td><td><strong>{location.name}</strong><small>{location.area}</small></td><td><RiskBadge risk={location.risk} compact /></td><td><strong className="score">{location.score}</strong><span className="score-max">/100</span></td><td className="table-time">{location.updatedAt}</td><td><button className="icon-button" type="button" aria-label={`Open details for ${location.name}`} onClick={() => onSelect(location.id)}><ArrowUpRight size={16} className="row-arrow" /></button></td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}
