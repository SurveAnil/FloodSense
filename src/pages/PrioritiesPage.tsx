import { ArrowLeft, Filter, Info } from 'lucide-react';
import type { DashboardData } from '../types/domain';
import { PriorityTable } from '../components/PriorityTable';
import { LocationDetail } from '../components/LocationDetail';
import { useState } from 'react';

export function PrioritiesPage({ data }: { data: DashboardData }) {
  const [selectedId, setSelectedId] = useState<string>();
  const selected = data.locations.find((location) => location.id === selectedId);
  if (selected) return <LocationDetail location={selected} onBack={() => setSelectedId(undefined)} />;
  return <div className="page"><div className="page-heading"><div><span className="eyebrow">Decision queue</span><h1>Priority hotspots</h1><p>Ranked locations based on placeholder risk outputs.</p></div><span className="last-updated">Updated {data.lastUpdated}</span></div><div className="status-banner subtle"><span><Info size={17} /><strong>Interpret with care.</strong> Historical records and predicted risk are separate signals.</span></div><section className="panel full-panel"><div className="panel-header"><div><h2>Locations requiring attention</h2><p>Select a row to open its explanation and map context.</p></div><button className="filter-button"><Filter size={15} /> Risk: All</button></div><PriorityTable locations={data.locations} onSelect={setSelectedId} /></section><button className="back-link" onClick={() => window.dispatchEvent(new CustomEvent('navigate-dashboard'))}><ArrowLeft size={15} /> Return to risk dashboard</button></div>;
}
