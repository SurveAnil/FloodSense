import { Database, Info } from 'lucide-react';
import type { DashboardData } from '../types/domain';
import { StatusBadge } from '../components/StatusBadge';

export function StatusPage({ data }: { data: DashboardData }) {
  const hasLiveWeather = data.sources.some((source) => source.name === 'Open-Meteo');
  return <div className="page">
    <div className="page-heading">
      <div><span className="eyebrow">Trust layer</span><h1>Data status</h1><p>Know what information is available before interpreting risk.</p></div>
      <span className="last-updated">Risk snapshot label: {data.lastUpdated}</span>
    </div>
    <div className="status-banner subtle">
      <span><Info size={17} /><strong>{hasLiveWeather ? 'Mixed live and replay source status.' : 'Replay source status; not live monitoring.'}</strong> Open-Meteo freshness is measured from its live Pune observation time; other sources remain bundled replay labels. Live weather does not update the replay risk predictions.</span>
    </div>
    <section className="panel full-panel">
      <div className="panel-header">
        <div><h2>Source availability</h2><p>Weather freshness is live; other source states are from the {data.dataMode} snapshot.</p></div>
        <Database size={20} className="panel-icon" />
      </div>
      {data.sources.length
        ? <div className="source-table">{data.sources.map((source) => <div className="source-row" key={source.name}>
          <div className="source-name"><span className={`source-icon source-icon-${source.state.toLowerCase()}`}><Database size={16} /></span><div><strong>{source.name}</strong><small>{source.type}</small></div></div>
          <StatusBadge state={source.state} />
          <div className="source-updated"><span>{source.name === 'Open-Meteo' ? 'Observed at' : 'Replay timestamp'}</span><strong>{source.lastUpdated}</strong></div>
          <div className="source-detail">{source.detail}</div>
        </div>)}</div>
        : <p className="report-muted">No source status is available.</p>}
    </section>
    <div className="info-grid">
      <div className="info-card"><h3>How to read this</h3><p>Open-Meteo is Available when its current observation is no more than one hour old, Stale when older or future-dated, and Unavailable when the provider request or payload fails. Other sources show replay status only.</p></div>
      <div className="info-card"><h3>Model transparency</h3><p>Risk snapshots identify their model version where recorded. Replay drivers are contextual notes; feature contributions are separately labeled and are not causal effects or accuracy claims.</p></div>
    </div>
  </div>;
}
