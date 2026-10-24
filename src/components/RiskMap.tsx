import { useEffect, useRef, useState } from 'react';
import {
  CircleHelp,
  CloudRain,
  Map as MapIcon,
  MapPin,
  Waves,
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { DataSourceStatus, RiskLocation } from '../types/domain';
import type { MapFeature } from '../services/map-service';

type MapLayer = 'predictions' | 'citizen' | 'field' | 'official' | 'demoContext';

const initialLayers: Record<MapLayer, boolean> = {
  predictions: true,
  citizen: true,
  field: true,
  official: true,
  demoContext: true,
};

const riskStyle: Record<RiskLocation['risk'], { marker: string }> = {
  Low: { marker: 'LOW' },
  Moderate: { marker: 'MOD' },
  High: { marker: 'HIGH' },
  Critical: { marker: 'CRIT' },
};

const featureStyle: Record<MapFeature['feature_type'], { color: string; symbol: string; label: string }> = {
  CITIZEN_REPORT: { color: '#1769aa', symbol: 'R', label: 'Citizen report' },
  FIELD_OBSERVATION: { color: '#7148a5', symbol: 'F', label: 'Field observation' },
  OFFICIAL_PROBLEM: { color: '#263a50', symbol: '!', label: 'Official flood problem' },
};

const tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const tileAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character] ?? character);
}

function featurePopup(feature: MapFeature) {
  const style = featureStyle[feature.feature_type];
  const result = feature.outcome === 'INSPECTED_NO_PROBLEM_FOUND'
    ? 'Inspected — no problem found'
    : feature.outcome === 'PROBLEM_FOUND' ? 'Problem observed' : '';
  return `<strong>${escapeHtml(feature.title)}</strong><br>${escapeHtml(style.label)}${result ? ` · ${escapeHtml(result)}` : ''}<br>${escapeHtml(feature.status)}<br>${escapeHtml(feature.observed_at)}`;
}

function demoContextPopup(location: RiskLocation): string {
  const context = location.demoContext;
  if (!context) return '';
  return `<hr><strong>DEMO SCENARIO CONTEXT — NOT VERIFIED</strong><br>${escapeHtml(context.sourceLabel)}<br>Mock citizen report count: ${context.citizenReportCount} (${context.citizenReportExamples.length} example summaries)<br>Examples: ${context.citizenReportExamples.map(escapeHtml).join(' · ')}<br>Field observation: ${escapeHtml(context.fieldObservationSummary)}<br>Mock official-problem status: ${escapeHtml(context.officialProblemStatus)} — ${escapeHtml(context.officialProblemSummary)}<br>Why light rain can cause congestion: ${escapeHtml(context.contextualNotes)}`;
}

export function RiskMap({
  locations,
  features,
  selectedId,
  onSelect,
  loadingFeatures,
  featureError,
  onRetryFeatures,
  sources,
}: {
  locations: RiskLocation[];
  features: MapFeature[];
  selectedId?: string;
  onSelect: (id: string) => void;
  loadingFeatures: boolean;
  featureError?: string;
  onRetryFeatures: () => void;
  sources: DataSourceStatus[];
}) {
  const mapElement = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layersRef = useRef<Record<MapLayer, L.LayerGroup> | null>(null);
  const [tileUnavailable, setTileUnavailable] = useState(false);
  const [visible, setVisible] = useState(initialLayers);
  const [basemap, setBasemap] = useState<'street' | 'satellite' | 'terrain'>('street');

  useEffect(() => {
    if (!mapElement.current) return;
    const map = L.map(mapElement.current, {
      center: [18.5204, 73.8567],
      zoom: 11,
      zoomControl: true,
      scrollWheelZoom: false,
    });
    const tiles = L.tileLayer(tileUrl, {
      maxZoom: 19,
      attribution: tileAttribution,
      crossOrigin: true,
    });
    tiles.on('tileerror', () => setTileUnavailable(true));
    tiles.addTo(map);
    mapRef.current = map;
    layersRef.current = {
      predictions: L.layerGroup().addTo(map),
      citizen: L.layerGroup().addTo(map),
      field: L.layerGroup().addTo(map),
      official: L.layerGroup().addTo(map),
      demoContext: L.layerGroup().addTo(map),
    };
    return () => {
      map.remove();
      mapRef.current = null;
      layersRef.current = null;
    };
  }, []);

  useEffect(() => {
    const groups = layersRef.current;
    const map = mapRef.current;
    if (!groups || !map) return;
    Object.values(groups).forEach((group) => group.clearLayers());

    for (const location of locations) {
      if (location.demoContext && visible.demoContext) {
        L.circleMarker(location.coordinates, {
          radius: 32,
          color: '#925300',
          weight: 2,
          dashArray: '5 4',
          fillColor: '#f2bd45',
          fillOpacity: 0.12,
        })
          .bindPopup(`<strong>${escapeHtml(location.name)}</strong>${demoContextPopup(location)}`)
          .addTo(groups.demoContext);
      }
      if (!visible.predictions) continue;
      const style = riskStyle[location.risk];
      const marker = L.marker(location.coordinates, {
        keyboard: true,
        title: `${location.name}, ${location.risk} risk, score ${location.score}`,
        alt: `${location.risk} flood-risk category`,
        icon: L.divIcon({
          className: 'risk-leaflet-icon',
          html: `<span class="risk-map-marker risk-${location.risk.toLowerCase()}"><strong>${style.marker}</strong><small>${location.score}</small></span>`,
          iconSize: [48, 48],
          iconAnchor: [24, 24],
        }),
      });
      marker.bindPopup(
        `<strong>${escapeHtml(location.name)}</strong><br>${escapeHtml(location.area)} · Pune<br>${escapeHtml(location.risk)} risk · ${location.score}/100<br>${location.demoContext ? 'Scenario window' : 'Prediction window'}: ${escapeHtml(location.predictionTime)}<br>Score basis: ${escapeHtml(location.modelVersion ?? 'replay')} · ${escapeHtml(location.dataMode)} data<br>Context: ${escapeHtml(location.drivers.join(', ') || 'unavailable')}<br>Sources: ${escapeHtml(sources.length ? sources.map((source) => `${source.name}: ${source.state} (${source.lastUpdated})`).join('; ') : 'source freshness unavailable')}${demoContextPopup(location)}`,
      );
      marker.on('click', () => onSelect(location.id));
      marker.addTo(groups.predictions);
    }

    for (const feature of features) {
      const layerName: MapLayer = feature.feature_type === 'CITIZEN_REPORT'
        ? 'citizen'
        : feature.feature_type === 'FIELD_OBSERVATION' ? 'field' : 'official';
      if (!visible[layerName]) continue;
      const style = featureStyle[feature.feature_type];
      const marker = L.marker([feature.latitude, feature.longitude], {
        keyboard: true,
        title: `${style.label}: ${feature.title}, ${feature.status}`,
        alt: style.label,
        icon: L.divIcon({
          className: 'incident-leaflet-icon',
          html: `<span class="incident-map-marker" style="--marker-color:${style.color}">${style.symbol}</span>`,
          iconSize: [34, 34],
          iconAnchor: [17, 17],
        }),
      });
      marker.bindPopup(featurePopup(feature));
      marker.addTo(groups[layerName]);
    }
  }, [features, locations, onSelect, visible]);

  useEffect(() => {
    if (!mapRef.current || !selectedId) return;
    const location = locations.find((item) => item.id === selectedId);
    if (location) mapRef.current.flyTo(location.coordinates, Math.max(mapRef.current.getZoom(), 13), { duration: 0.45 });
  }, [locations, selectedId]);

  const toggle = (layer: MapLayer) => {
    setVisible((current) => ({ ...current, [layer]: !current[layer] }));
  };

  return (
    <div className="gis-map-card">
      <div className="gis-map-toolbar">
        <label className="basemap-select">
          <MapIcon size={16} />
          <span>Basemap</span>
          <select
            aria-label="Basemap style"
            value={basemap}
            onChange={(event) => setBasemap(event.target.value as typeof basemap)}
          >
            <option value="street">Street · OpenStreetMap</option>
            <option value="satellite" disabled>Satellite · provider unavailable</option>
            <option value="terrain" disabled>Terrain · provider unavailable</option>
          </select>
        </label>
        <span className="tile-provider-note"><CircleHelp size={14} /> Satellite and terrain tiles are not configured.</span>
        <span className="map-source-freshness" title={sources.map((source) => `${source.name}: ${source.state}; ${source.lastUpdated}`).join('\n')}>
          {sources.length
            ? sources.map((source) => `${source.name} ${source.state.toLowerCase()}`).join(' · ')
            : 'Source freshness unavailable for this view'}
        </span>
      </div>
      <fieldset className="map-layer-controls">
        <legend>Map layers</legend>
        <label><input type="checkbox" checked={visible.predictions} onChange={() => toggle('predictions')} /><span className="layer-symbol layer-risk" />Risk hotspots</label>
        <label><input type="checkbox" checked={visible.citizen} onChange={() => toggle('citizen')} /><span className="layer-symbol layer-citizen">R</span>Citizen reports</label>
        <label><input type="checkbox" checked={visible.field} onChange={() => toggle('field')} /><span className="layer-symbol layer-field">F</span>Field observations</label>
        <label><input type="checkbox" checked={visible.official} onChange={() => toggle('official')} /><span className="layer-symbol layer-official">!</span>Official problems</label>
        <label><input type="checkbox" checked={visible.demoContext} onChange={() => toggle('demoContext')} /><span className="layer-symbol layer-demo-context">D</span>Demo scenario context</label>
        <span className="weather-layer-unavailable"><CloudRain size={14} /> Rainfall/weather overlay unavailable</span>
      </fieldset>
      <div className="gis-map-frame">
        <div ref={mapElement} className="leaflet-map" role="region" aria-label="Interactive map of Pune flood-risk predictions and authorized reports" />
        {tileUnavailable && <div className="tile-error-banner" role="status"><Waves size={15} /> Street tiles unavailable. Markers and zoom remain usable.</div>}
        {loadingFeatures && <div className="map-loading-banner" role="status">Loading authorized report and problem layers…</div>}
        {featureError && <div className="map-feature-error" role="alert"><span>{featureError}</span><button type="button" onClick={onRetryFeatures}>Retry layers</button></div>}
        {!locations.length && !features.length && !loadingFeatures && !featureError && <div className="map-empty-state">No prediction or incident locations to display.</div>}
        <div className="map-coordinate-note"><MapPin size={12} /> WGS84 coordinates · OpenStreetMap © contributors</div>
      </div>
      <div className="map-legend map-legend-gis" aria-label="Map symbol legend">
        <span><i className="legend-risk-sample risk-critical" />Risk category (color) and score</span>
        <span><i className="legend-symbol legend-citizen">R</i>Citizen report</span>
        <span><i className="legend-symbol legend-field">F</i>Field observation</span>
        <span><i className="legend-symbol legend-official">!</i>Official problem</span>
        <span><i className="legend-symbol legend-demo-context">D</i>Demo scenario context (not verified)</span>
      </div>
    </div>
  );
}
