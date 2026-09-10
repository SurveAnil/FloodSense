import { MapPin, MousePointer2 } from 'lucide-react';
import type { RiskLocation } from '../types/domain';
import { RiskBadge } from './RiskBadge';

export function RiskMap({ locations, selectedId, onSelect }: { locations: RiskLocation[]; selectedId?: string; onSelect: (id: string) => void }) {
  return (
    <div className="map-shell" aria-label="Pune risk map placeholder">
      <div className="map-grid" />
      <div className="map-river" />
      <div className="map-label map-label-pune">PUNE</div>
      <div className="map-label map-label-kothrud">Kothrud</div>
      <div className="map-label map-label-aundh">Aundh</div>
      <div className="map-label map-label-sinhagad">Sinhagad Road</div>
      <div className="map-label map-label-hadapsar">Hadapsar</div>
      {locations.map((location, index) => (
        <button key={location.id} className={`map-marker marker-${location.risk.toLowerCase()} ${selectedId === location.id ? 'map-marker-selected' : ''}`} style={{ left: `${22 + (index * 15) % 60}%`, top: `${28 + ((index * 19) % 45)}%` }} onClick={() => onSelect(location.id)} aria-label={`${location.name}, ${location.risk} risk`}>
          <span className="marker-pulse" /><MapPin size={25} fill="currentColor" />
          <span className="marker-tooltip">{location.name}<br /><RiskBadge risk={location.risk} compact /></span>
        </button>
      ))}
      <div className="map-hint"><MousePointer2 size={14} /> Select a location to view details</div>
      <div className="map-legend"><span className="legend-title">Predicted risk</span>{(['Low', 'Moderate', 'High', 'Critical'] as const).map((risk) => <span key={risk}><i className={`legend-dot legend-${risk.toLowerCase()}`} />{risk}</span>)}</div>
      <span className="map-placeholder-label">Interactive GIS layer<br /><small>Placeholder for Phase 1</small></span>
    </div>
  );
}
