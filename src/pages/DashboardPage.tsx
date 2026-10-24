import { Activity, AlertTriangle, CheckCircle2, Clock3, Info, ListFilter, RefreshCw, Search, ShieldAlert } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import type { DashboardData, RiskLocation } from '../types/domain';
import { PriorityTable } from '../components/PriorityTable';
import { RainfallStrip } from '../components/RainfallStrip';
import { RiskBadge } from '../components/RiskBadge';
import { RiskMap } from '../components/RiskMap';
import { LocationDetail } from '../components/LocationDetail';
import type { AppRole } from '../services/auth-service';
import { getMapFeatures, type MapFeature } from '../services/map-service';

const roleContext: Record<AppRole, string> = {
  CITIZEN: 'Public flood-risk information for Pune',
  FIELD_RESPONSE_PLANNING: 'Operational risk and proactive inspection priorities',
  DISASTER_MANAGEMENT_ADMIN: 'Command-level risk and data status',
};

export function DashboardPage({ data, role, onPriorityView, onRefresh, onInspectHotspot }: { data: DashboardData; role: AppRole; onPriorityView: () => void; onRefresh: () => Promise<void>; onInspectHotspot?: (location: RiskLocation) => void }) {
  const [selectedId, setSelectedId] = useState<string>();
  const [riskFilter, setRiskFilter] = useState<DashboardData['locations'][number]['risk']>();
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [features, setFeatures] = useState<MapFeature[]>([]);
  const [loadingFeatures, setLoadingFeatures] = useState(true);
  const [featureError, setFeatureError] = useState<string>();
  const selected = data.locations.find((location) => location.id === selectedId);
  const loadFeatures = useCallback(async () => {
    setLoadingFeatures(true);
    setFeatureError(undefined);
    try {
      setFeatures(await getMapFeatures());
    } catch (reason) {
      setFeatureError(reason instanceof Error ? reason.message : 'Map incident layers could not be loaded.');
    } finally {
      setLoadingFeatures(false);
    }
  }, []);
  useEffect(() => { void loadFeatures(); }, [loadFeatures]);
  const searchText = search.trim().toLocaleLowerCase();
  const visibleLocations = data.locations
    .filter((location) => !riskFilter || location.risk === riskFilter)
    .filter((location) => !searchText || `${location.name} ${location.area}`.toLocaleLowerCase().includes(searchText));
  const visibleFeatures = features.filter((feature) =>
    !searchText || `${feature.title} ${feature.area}`.toLocaleLowerCase().includes(searchText),
  );
  if (selected) return <LocationDetail location={selected} backLabel="Back to dashboard" onBack={() => setSelectedId(undefined)} onInspect={onInspectHotspot ? () => onInspectHotspot(selected) : undefined} />;
  const refresh = async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };
  const counts = (['Low', 'Moderate', 'High', 'Critical'] as const).map((risk) => ({ risk, count: data.locations.filter((location) => location.risk === risk).length }));
  const priorityCount = data.locations.filter((location) => location.risk === 'High' || location.risk === 'Critical').length;
  const pendingCount = features.filter((feature) => feature.feature_type === 'CITIZEN_REPORT' && ['PENDING_VERIFICATION', 'NEEDS_INFORMATION'].includes(feature.status)).length;
  const officialCount = features.filter((feature) => feature.feature_type === 'OFFICIAL_PROBLEM').length;
  return <div className="page">
    <div className="page-heading"><div><span className="eyebrow">{roleContext[role]}</span><h1>Flood risk dashboard</h1><p>Review model risk outputs and prioritize human attention.</p></div><div className="heading-actions"><span className="last-updated"><Clock3 size={15} /> {data.dataMode === 'replay' ? 'Replay snapshot label' : 'Data timestamp'} {data.lastUpdated}</span><button className="icon-button" aria-label="Refresh risk data" title="Refresh risk data" onClick={refresh} disabled={refreshing}><RefreshCw size={16} className={refreshing ? 'refreshing-icon' : ''} /></button></div></div>
    <div className="status-banner"><span><Info size={17} /><strong>{data.dataMode === 'replay' ? 'Replay/demo data is active; values are not live.' : data.dataMode === 'live' ? 'Live data mode is active.' : 'Data mode is unknown.'}</strong> Risk states prioritize attention; they are not official warnings or confirmed incidents.</span><button onClick={onPriorityView}>View priority list <ListFilter size={15} /></button></div>
    <section className="summary-card"><div className="summary-head"><div><span className="eyebrow">Prediction snapshot</span><h2>Risk across selected Pune locations</h2></div><span className="summary-source"><Activity size={15} /> {data.modelVersion ? `Model ${data.modelVersion}` : `Model status: ${data.dataMode}`}</span></div><div className="risk-summary">{counts.map(({ risk, count }) => <button key={risk} type="button" aria-pressed={riskFilter === risk} onClick={() => setRiskFilter(riskFilter === risk ? undefined : risk)} className={`summary-risk summary-${risk.toLowerCase()} ${riskFilter === risk ? 'summary-risk-selected' : ''}`}><RiskBadge risk={risk} /><strong>{count}</strong><span>locations</span></button>)}</div></section>
    <section className="map-summary-cards" aria-label="Operational summary">
      <article><AlertTriangle size={18} /><strong>{priorityCount}</strong><span>High-priority hotspots</span></article>
      <article><Clock3 size={18} /><strong>{loadingFeatures ? '—' : pendingCount}</strong><span>{role === 'CITIZEN' ? 'My reports awaiting review' : 'Pending verification'}</span></article>
      <article><CheckCircle2 size={18} /><strong>{loadingFeatures ? '—' : officialCount}</strong><span>Official flood problems</span></article>
    </section>
    <div className="dashboard-grid"><section className="panel map-panel"><div className="panel-header"><div><h2>Flood-risk and incident map</h2><p>{riskFilter ? `${riskFilter} prediction markers` : 'Predictions, reports, observations, and approved problems'}</p></div><span className="map-meta"><ShieldAlert size={15} /> Predicted risk is not an official warning</span></div><label className="map-search"><Search size={16} /><span className="sr-only">Search locations</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search location or area" /></label><RiskMap locations={visibleLocations} features={visibleFeatures} selectedId={selectedId} onSelect={setSelectedId} loadingFeatures={loadingFeatures} featureError={featureError} onRetryFeatures={() => void loadFeatures()} sources={data.sources} /></section><section className="panel priority-panel"><div className="panel-header"><div><h2>Priority hotspots</h2><p>{riskFilter ? `${riskFilter} locations ranked by risk` : 'Highest predicted risk first'}</p></div><button className="text-button" onClick={onPriorityView}>View all</button></div><PriorityTable locations={[...visibleLocations].sort((a, b) => b.score - a.score)} onSelect={setSelectedId} compact /></section></div>
    <RainfallStrip rainfall={data.rainfall} />
  </div>;
}
