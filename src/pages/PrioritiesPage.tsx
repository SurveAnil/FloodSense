import { ArrowLeft, Filter, Info } from 'lucide-react';
import type { DashboardData } from '../types/domain';
import { PriorityTable } from '../components/PriorityTable';
import { LocationDetail } from '../components/LocationDetail';
import { RiskMap } from '../components/RiskMap';
import { useCallback, useEffect, useState } from 'react';
import { getMapFeatures, type MapFeature } from '../services/map-service';

export function PrioritiesPage({ data, onSelectLocation }: { data: DashboardData; onSelectLocation?: (id: string) => void }) {
  const [selectedId, setSelectedId] = useState<string>();
  const [riskFilter, setRiskFilter] = useState<string>('All');
  const [search, setSearch] = useState('');
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
  const onSelect = (id: string) => {
    setSelectedId(id);
    onSelectLocation?.(id);
  };
  const searchText = search.trim().toLocaleLowerCase();
  const visibleLocations = riskFilter === 'All'
    ? data.locations
    : data.locations.filter((location) => location.risk === riskFilter);
  const filteredLocations = visibleLocations.filter((location) =>
    !searchText || `${location.name} ${location.area}`.toLocaleLowerCase().includes(searchText),
  );
  const filteredFeatures = features.filter((feature) =>
    !searchText || `${feature.title} ${feature.area}`.toLocaleLowerCase().includes(searchText),
  );
  if (selected) return <LocationDetail location={selected} backLabel="Back to priority list" onBack={() => setSelectedId(undefined)} />;
  return <div className="page priorities-page"><div className="page-heading"><div><span className="eyebrow">Decision queue</span><h1>Priority hotspots</h1><p>Ranked by prediction score; scores and categories come from the saved prediction records.</p></div><span className="last-updated">{data.dataMode === 'replay' ? 'Replay snapshot label' : 'Data timestamp'} {data.lastUpdated}</span></div><div className="status-banner subtle"><span><Info size={17} /><strong>Interpret with care.</strong> Historical records and predicted risk are separate signals.</span></div>
    <section className="panel priorities-map-panel"><div className="panel-header"><div><h2>Hotspot map</h2><p>Select any predicted hotspot to inspect its details.</p></div></div><RiskMap locations={filteredLocations} features={filteredFeatures} selectedId={selectedId} onSelect={onSelect} loadingFeatures={loadingFeatures} featureError={featureError} onRetryFeatures={() => void loadFeatures()} sources={data.sources} /></section>
    <section className="panel full-panel"><div className="panel-header"><div><h2>Ranked locations</h2><p>{filteredLocations.length} matching prediction locations</p></div><div className="priorities-controls"><label className="priority-search"><span className="sr-only">Search by location or area</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search location or area" /></label><label className="risk-filter-label"><Filter size={15} /><span>Risk</span><select aria-label="Filter hotspots by risk" className="risk-filter" value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>{['All', 'Low', 'Moderate', 'High', 'Critical'].map((risk) => <option key={risk}>{risk}</option>)}</select></label></div></div><PriorityTable locations={[...filteredLocations].sort((a, b) => b.score - a.score)} onSelect={onSelect} /></section>
    <button className="back-link" onClick={() => window.dispatchEvent(new CustomEvent('navigate-dashboard'))}><ArrowLeft size={15} /> Return to risk dashboard</button></div>;
}
