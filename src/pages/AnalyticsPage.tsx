import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Clock3, History, MapPin, ShieldCheck } from 'lucide-react';
import { ApiError } from '../services/auth-service';
import { getRiskAnalytics, type RiskAnalytics } from '../services/analytics-service';
import type { AppRole } from '../services/auth-service';

interface Props {
  role: AppRole;
}

const formatDate = (value: string | null) => value
  ? new Date(value).toLocaleString()
  : 'No dated prediction snapshots';

const outcomeLabel = (outcome: string) => ({
  PROBLEM_FOUND: 'Problem observed',
  INSPECTED_NO_PROBLEM_FOUND: 'Inspected — no problem found',
  VERIFIED: 'Citizen report verified by field staff',
  NOT_VERIFIED: 'Citizen report not verified',
}[outcome] ?? outcome);

export function AnalyticsPage({ role }: Props) {
  const [analytics, setAnalytics] = useState<RiskAnalytics>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const isPublic = role === 'CITIZEN';

  const load = async () => {
    setLoading(true);
    setError(undefined);
    try {
      setAnalytics(await getRiskAnalytics());
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 401
        ? 'Your session has expired. Sign in again to view analytics.'
        : reason instanceof Error ? reason.message : 'Risk analytics could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  if (loading) return <section className="analytics-page" aria-live="polite"><p>Loading historical risk summaries…</p></section>;
  if (error) return <section className="analytics-page"><div className="analytics-error" role="alert"><AlertTriangle size={20} /><span>{error}</span><button type="button" onClick={() => void load()}>Retry</button></div></section>;
  if (!analytics) return <section className="analytics-page"><p>Analytics are unavailable.</p></section>;

  const { summary } = analytics;
  return <section className="analytics-page">
    <header className="analytics-header">
      <div><span className="eyebrow">Historical analysis</span><h1>{isPublic ? 'Public risk history' : 'Prediction and observation analytics'}</h1>
        <p>{isPublic
          ? 'Historical prediction snapshots and aggregate official problem counts. This is not a live conditions feed.'
          : 'Compare risk snapshots with field observations and verified report outcomes. A record comparison is not a model evaluation.'}</p>
      </div>
      <span className={`analytics-mode mode-${summary.data_mode}`}><Activity size={16} /> {summary.data_mode === 'replay' ? 'Replay/demo records' : `${summary.data_mode} data`}</span>
    </header>
    <div className="analytics-cards">
      <article><History size={19} /><strong>{summary.prediction_snapshots}</strong><span>Prediction snapshots</span></article>
      <article><MapPin size={19} /><strong>{summary.historical_hotspot_references}</strong><span>Historical hotspot references</span></article>
      <article><ShieldCheck size={19} /><strong>{summary.officially_approved_problems}</strong><span>Admin-approved official problems</span></article>
      {!isPublic && <>
        <article><CheckCircle2 size={19} /><strong>{summary.field_problem_findings}</strong><span>Field problem observations</span></article>
        <article><Clock3 size={19} /><strong>{summary.no_problem_inspections}</strong><span>No-problem inspections</span></article>
        <article><Activity size={19} /><strong>{summary.verified_citizen_report_findings}</strong><span>Verified citizen report findings</span></article>
      </>}
    </div>
    {!isPublic && <section className="comparison-panel">
      <h2>Recorded outcomes after prediction windows</h2>
      <p>Comparisons count matched records; they do not measure model accuracy. Unverified citizen submissions are excluded.</p>
      <dl>
        <div><dt>High risk + problem observation</dt><dd>{summary.high_risk_with_problem_observation}</dd></div>
        <div><dt>High risk + no-problem inspection</dt><dd>{summary.high_risk_with_no_problem_inspection}</dd></div>
        <div><dt>High risk + no matching inspection</dt><dd>{summary.high_risk_without_matching_inspection}</dd></div>
        <div><dt>Lower risk + problem observation</dt><dd>{summary.lower_risk_with_problem_observation}</dd></div>
      </dl>
    </section>}
    <p className="analytics-notice">{summary.evaluation_notice}</p>
    <div className="analytics-period"><span>Prediction window-end range</span><strong>{formatDate(summary.period_start)} — {formatDate(summary.period_end)}</strong>
      <span>{summary.model_versions.length ? `Model version${summary.model_versions.length === 1 ? '' : 's'}: ${summary.model_versions.join(', ')}` : 'Model version unavailable'}</span>
    </div>
    {analytics.locations.length === 0 ? <p className="analytics-empty">No location history is available.</p> : <div className="analytics-location-list">
      {analytics.locations.map((location) => <article className="analytics-location" key={location.location_id}>
        <div className="analytics-location-heading"><div><h2>{location.name}</h2><span>{location.area}{location.historical_hotspot_reference ? ' · Historical hotspot reference' : ''}</span></div>
          <div className="analytics-location-stats"><span>{location.latest_prediction ? `${location.latest_prediction.risk_category} · ${location.latest_prediction.score}/100` : 'No prediction'}</span><span>{location.officially_approved_problem_count} official problem(s)</span></div>
        </div>
        {location.prediction_history.length > 0 ? <div className="prediction-history" aria-label={`Historical prediction trend for ${location.name}`}>
          {location.prediction_history.map((prediction) => <div className="prediction-history-item" key={prediction.id} title={`${prediction.prediction_time}; score ${prediction.score}; model ${prediction.model_version}`}>
            <span>{prediction.prediction_time}</span><strong>{prediction.score}/100 · {prediction.risk_category}</strong><small>{prediction.model_version} · {prediction.data_mode}</small>
          </div>)}
        </div> : <p className="analytics-empty">No prediction snapshots recorded.</p>}
        {!isPublic && (location.observation_history.length > 0
          ? <ul className="observation-list">{location.observation_history.map((observation, index) => <li key={`${observation.source_type}-${observation.observed_at}-${index}`}><span>{outcomeLabel(observation.outcome)}</span><small>{observation.source_type.replace(/_/g, ' ')} · {observation.review_status ?? 'review status unavailable'} · {observation.observed_at}</small></li>)}</ul>
          : <p className="analytics-empty">No field observations or verified report outcomes matched this location.</p>)}
      </article>)}
    </div>}
  </section>;
}
