import { Activity, Clock3, Info, ListFilter, RefreshCw, ShieldAlert } from 'lucide-react';
import { useState } from 'react';
import type { DashboardData } from '../types/domain';
import { PriorityTable } from '../components/PriorityTable';
import { RainfallStrip } from '../components/RainfallStrip';
import { RiskBadge } from '../components/RiskBadge';
import { RiskMap } from '../components/RiskMap';
import { LocationDetail } from '../components/LocationDetail';

export function DashboardPage({ data, onPriorityView }: { data: DashboardData; onPriorityView: () => void }) {
  const [selectedId, setSelectedId] = useState<string>();
  const selected = data.locations.find((location) => location.id === selectedId);
  if (selected) return <LocationDetail location={selected} onBack={() => setSelectedId(undefined)} />;
  const counts = (['Low', 'Moderate', 'High', 'Critical'] as const).map((risk) => ({ risk, count: data.locations.filter((location) => location.risk === risk).length }));
  return <div className="page">
    <div className="page-heading"><div><span className="eyebrow">Operational overview</span><h1>Flood risk dashboard</h1><p>Understand where rainfall may translate into urban disruption.</p></div><div className="heading-actions"><span className="last-updated"><Clock3 size={15} /> Updated {data.lastUpdated}</span><button className="icon-button" aria-label="Refresh demo data"><RefreshCw size={16} /></button></div></div>
    <div className="status-banner"><span><Info size={17} /><strong>{data.dataMode === 'replay' ? 'Replay data is active.' : 'Backend data is active.'}</strong> Risk states are model outputs for prioritizing attention, not official warnings.</span><button onClick={onPriorityView}>View priority list <ListFilter size={15} /></button></div>
    <section className="summary-card"><div className="summary-head"><div><span className="eyebrow">Current risk picture</span><h2>Risk across selected Pune locations</h2></div><span className="summary-source"><Activity size={15} /> Model status: {data.dataMode}</span></div><div className="risk-summary">{counts.map(({ risk, count }) => <button key={risk} className={`summary-risk summary-${risk.toLowerCase()}`}><RiskBadge risk={risk} /><strong>{count}</strong><span>locations</span></button>)}</div></section>
    <div className="dashboard-grid"><section className="panel map-panel"><div className="panel-header"><div><h2>Risk map</h2><p>Predicted risk by selected location</p></div><span className="map-meta"><ShieldAlert size={15} /> Not an official warning</span></div><RiskMap locations={data.locations} selectedId={selectedId} onSelect={setSelectedId} /></section><section className="panel priority-panel"><div className="panel-header"><div><h2>Priority hotspots</h2><p>Where attention may be needed first</p></div><button className="text-button" onClick={onPriorityView}>View all</button></div><PriorityTable locations={data.locations} onSelect={setSelectedId} compact /></section></div>
    <RainfallStrip rainfall={data.rainfall} />
  </div>;
}
