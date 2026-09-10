import { ArrowLeft, CalendarClock, CheckCircle2, CloudRain, Eye, History, MapPin, Sparkles } from 'lucide-react';
import type { RiskLocation } from '../types/domain';
import { RiskBadge } from './RiskBadge';

export function LocationDetail({ location, onBack }: { location: RiskLocation; onBack: () => void }) {
  return <section className="detail-panel">
    <button className="back-button" onClick={onBack}><ArrowLeft size={16} /> Back to dashboard</button>
    <div className="detail-heading"><div><span className="eyebrow">Selected location</span><h1>{location.name}</h1><p><MapPin size={15} /> {location.area}, Pune</p></div><RiskBadge risk={location.risk} /></div>
    <div className="detail-score-row"><div><span className="eyebrow predicted-label">Predicted risk score</span><div className="detail-score">{location.score}<small>/100</small></div></div><div className="detail-time"><CalendarClock size={17} /><div><span>Prediction applies</span><strong>{location.predictionTime}</strong></div></div></div>
    <div className="detail-section"><div className="detail-section-title"><Sparkles size={17} /> Why this location is prioritized</div><div className="driver-list">{location.drivers.map((driver) => <div className="driver" key={driver}><CheckCircle2 size={16} /><span>{driver}</span></div>)}</div></div>
    <div className="detail-section"><div className="detail-section-title"><CloudRain size={17} /> Rainfall context</div><div className="observed-predicted"><div className="context-card observed-card"><span className="context-tag"><Eye size={14} /> Observed</span><strong>{location.currentRainfall}</strong><span>Current rainfall</span></div><div className="context-card predicted-card"><span className="context-tag"><CloudRain size={14} /> Predicted</span><strong>{location.forecastRainfall}</strong><span>Forecast rainfall</span></div></div></div>
    <div className="detail-section"><div className="detail-section-title"><History size={17} /> Historical context</div><div className="historical-note">{location.historicalHotspot ? 'This location is included in the historical hotspot reference list.' : 'No historical hotspot record is attached to this location.'} Historical context is shown separately from the current prediction.</div></div>
    <div className="mini-map"><div className="mini-map-road" /><MapPin size={30} className={`mini-pin pin-${location.risk.toLowerCase()}`} /><span>Location context · GIS layer placeholder</span></div>
    <div className="demo-disclaimer">Demo data only. This is a model-output interface prototype, not a validated live prediction or official warning.</div>
  </section>;
}
