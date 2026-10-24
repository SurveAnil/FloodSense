import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { formatReportCount } from './report-count';
import {
  reportService,
  type AdminReportQueue,
  type CitizenReport,
  type EvidenceFile,
  type FieldReport,
  type FloodProblem,
  type MyCitizenReport,
  type ReportCategory,
  type ReportSeverity,
  type ReviewDecision,
} from '../services/report-service';
import type { AppRole } from '../services/auth-service';
import type { RiskLocation } from '../types/domain';

const categories: Array<{ value: ReportCategory; label: string }> = [
  { value: 'WATERLOGGING', label: 'Waterlogging' },
  { value: 'FLOODING', label: 'Flooding' },
  { value: 'BLOCKED_DRAINAGE', label: 'Blocked drainage' },
  { value: 'OVERFLOW', label: 'Overflow' },
  { value: 'OTHER', label: 'Other' },
];
const severities: ReportSeverity[] = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];

function formValue(form: HTMLFormElement, name: string): string {
  return String(new FormData(form).get(name) ?? '');
}

function humanize(value: string): string {
  return value.replace(/_/g, ' ');
}

function filesFrom(form: HTMLFormElement): FileList | null {
  return form.querySelector<HTMLInputElement>('input[type="file"]')?.files ?? null;
}

function StatusPill({ status }: { status: string }) {
  return <span className={`report-status status-${status.toLowerCase().replace(/_/g, '-')}`}>{humanize(status)}</span>;
}

function EvidenceLinks({ files }: { files: EvidenceFile[] }) {
  if (!files.length) return <span className="report-muted">No evidence attached</span>;
  return <ul className="evidence-list">{files.map((file) =>
    <li key={file.id}><a href={reportService.evidenceUrl(file)} target="_blank" rel="noreferrer">{file.file_name}</a> <small>{Math.ceil(file.size_bytes / 1024)} KB</small></li>,
  )}</ul>;
}

function LocationSelect({
  locations,
  selectedId,
  onChange,
  allowNew = false,
}: {
  locations: RiskLocation[];
  selectedId?: string;
  onChange?: (value: string) => void;
  allowNew?: boolean;
}) {
  return <label>{allowNew ? 'Location' : 'AI hotspot / location'}
    <select name="location_id" value={selectedId} onChange={(event) => onChange?.(event.target.value)} required>
      <option value="">Select a location</option>
      {locations.map((location) => <option key={location.id} value={location.id}>
        {location.name} · {location.risk} ({location.score}/100)
      </option>)}
      {allowNew && <option value="__new__">Add a new location</option>}
    </select>
  </label>;
}

export function ReportsPage({
  role,
  locations,
  inspectionLocationId,
}: {
  role: AppRole;
  locations: RiskLocation[];
  inspectionLocationId?: string;
}) {
  const [mine, setMine] = useState<MyCitizenReport[]>([]);
  const [pending, setPending] = useState<CitizenReport[]>([]);
  const [fieldReports, setFieldReports] = useState<FieldReport[]>([]);
  const [queue, setQueue] = useState<AdminReportQueue>({ citizen_reports: [], field_reports: [] });
  const [problems, setProblems] = useState<FloodProblem[]>([]);
  const [selectedLocation, setSelectedLocation] = useState(inspectionLocationId ?? '');
  const [activeAdminTab, setActiveAdminTab] = useState<'review' | 'problems'>('review');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();

  const reload = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    try {
      if (role === 'CITIZEN') setMine(await reportService.listMine());
      if (role === 'FIELD_RESPONSE_PLANNING') {
        const [reports, authored] = await Promise.all([reportService.listPending(), reportService.listField()]);
        setPending(reports);
        setFieldReports(authored);
      }
      if (role === 'DISASTER_MANAGEMENT_ADMIN') {
        const [reports, officialProblems] = await Promise.all([reportService.adminQueue(), reportService.floodProblems()]);
        setQueue(reports);
        setProblems(officialProblems);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Reports could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => { if (inspectionLocationId) setSelectedLocation(inspectionLocationId); }, [inspectionLocationId]);

  const run = async (operation: () => Promise<unknown>, success: string) => {
    setBusy(true);
    setError(undefined);
    setNotice(undefined);
    try {
      await operation();
      setNotice(success);
      await reload();
      return true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The report action could not be completed.');
      return false;
    } finally {
      setBusy(false);
    }
  };

  const submitCitizen = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    return run(async () => {
      const selection = formValue(form, 'location_id');
      const location = selection === '__new__'
        ? {
            location_name: formValue(form, 'location_name'),
            area: formValue(form, 'area'),
            latitude: Number(formValue(form, 'latitude')),
            longitude: Number(formValue(form, 'longitude')),
          }
        : { location_id: selection };
      await reportService.createCitizen({
        location,
        category: formValue(form, 'category') as ReportCategory,
        description: formValue(form, 'description'),
        evidence: await reportService.encodeFiles(filesFrom(form)),
      });
      form.reset();
      setSelectedLocation('');
    }, 'Your report has been submitted for field verification.');
  };

  const submitFieldReport = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    return run(async () => {
      const selection = formValue(form, 'location_id');
      const outcome = formValue(form, 'outcome') as FieldReport['outcome'];
      const location = selection === '__new__'
        ? {
            location_name: formValue(form, 'location_name'),
            area: formValue(form, 'area'),
            latitude: Number(formValue(form, 'latitude')),
            longitude: Number(formValue(form, 'longitude')),
          }
        : { location_id: selection };
      const selected = locations.find((item) => item.id === selection);
      await reportService.createField({
        location,
        category: formValue(form, 'category') as ReportCategory,
        description: formValue(form, 'description'),
        observed_condition: formValue(form, 'observed_condition'),
        outcome,
        severity: outcome === 'PROBLEM_FOUND' ? formValue(form, 'severity') as ReportSeverity : undefined,
        prediction_id: selected?.riskPredictionId,
        evidence: await reportService.encodeFiles(filesFrom(form)),
      });
      form.reset();
      setSelectedLocation('');
    }, 'Field observation saved and sent for administrative review.');
  };

  const title = role === 'CITIZEN' ? 'My flood reports'
    : role === 'FIELD_RESPONSE_PLANNING' ? 'Field verification & reports'
      : 'Report review';
  const subtitle = role === 'CITIZEN'
    ? 'Submit a local observation and follow its verification and review status.'
    : role === 'FIELD_RESPONSE_PLANNING'
      ? 'Verify citizen reports or record an independent hotspot inspection.'
      : 'Review submitted evidence. Only an explicit approval creates an official FloodProblem.';

  return <div className="page reports-page">
    <div className="page-heading">
      <div><span className="eyebrow">Phase 2 · Report → Verify → Official Problem</span><h1>{title}</h1><p>{subtitle}</p></div>
      <button type="button" className="secondary-button" onClick={() => void reload()} disabled={loading || busy}>Refresh</button>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {notice && <div className="form-success" role="status">{notice}</div>}
    {loading ? <section className="panel"><p>Loading report workflow…</p></section> : <>
      {role === 'CITIZEN' && <CitizenView reports={mine} locations={locations} busy={busy} onSubmit={submitCitizen} onUpdate={(id, payload) => run(async () => reportService.updateCitizen(id, {
        description: payload.description,
        evidence: await reportService.encodeFiles(payload.evidence),
      }), 'Additional information submitted for field verification.')} />}
      {role === 'FIELD_RESPONSE_PLANNING' && <FieldView
        pending={pending}
        reports={fieldReports}
        locations={locations}
        selectedLocation={selectedLocation}
        setSelectedLocation={setSelectedLocation}
        busy={busy}
        onCreate={submitFieldReport}
        onVerify={(id, payload) => run(async () => reportService.verifyCitizen(id, {
          ...payload, evidence: await reportService.encodeFiles(payload.evidence),
        }), 'Field verification recorded.')}
        onSupplement={(id, payload) => run(async () => reportService.supplementField(id, {
          ...payload, evidence: await reportService.encodeFiles(payload.evidence),
        }), 'Additional field evidence submitted for review.')}
      />}
      {role === 'DISASTER_MANAGEMENT_ADMIN' && <AdminView
        queue={queue}
        problems={problems}
        activeTab={activeAdminTab}
        setActiveTab={setActiveAdminTab}
        busy={busy}
        onReview={(source, id, payload) => run(() => reportService.review(source, id, payload), payload.decision === 'APPROVE' ? 'Official FloodProblem created by administrative approval.' : 'Administrative review decision recorded.')}
      />}
    </>}
  </div>;
}

function CitizenView({
  reports, locations, busy, onSubmit, onUpdate,
}: {
  reports: MyCitizenReport[];
  locations: RiskLocation[];
  busy: boolean;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<boolean>;
  onUpdate: (id: string, payload: { description: string; evidence: FileList | null }) => Promise<boolean>;
}) {
  const [newLocation, setNewLocation] = useState(false);
  return <>
    <section className="panel report-form-panel">
      <h2>Submit a flood report</h2>
      <p>Reports are observations, not official incidents. Field verification and administrator review are required.</p>
      <form className="auth-form report-form" onSubmit={async (event) => { if (await onSubmit(event)) setNewLocation(false); }}>
        <LocationSelect locations={locations} allowNew selectedId={newLocation ? '__new__' : undefined} onChange={(value) => setNewLocation(value === '__new__')} />
        {newLocation && <div className="report-form-grid">
          <label>Location name<input name="location_name" required maxLength={160} /></label>
          <label>Area / neighborhood<input name="area" maxLength={120} /></label>
          <label>Latitude<input name="latitude" type="number" min={-90} max={90} step="any" required /></label>
          <label>Longitude<input name="longitude" type="number" min={-180} max={180} step="any" required /></label>
        </div>}
        <label>Report category<select name="category" required defaultValue="WATERLOGGING">{categories.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>What did you observe?<textarea name="description" minLength={10} maxLength={2000} rows={4} required placeholder="Describe the water or drainage condition and when you observed it." /></label>
        <label>Evidence (optional)<input name="evidence" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple /><small>Up to 3 JPEG, PNG, WebP, or PDF files; 5 MB each.</small></label>
        <button className="primary-button" type="submit" disabled={busy}>Submit report</button>
      </form>
    </section>
    <section className="report-list-section"><div className="report-section-heading"><div><span className="eyebrow">Private to your account</span><h2>My reports</h2></div><span>{formatReportCount(reports.length)}</span></div>
      {reports.length === 0 ? <section className="panel report-empty">No reports yet. Your submissions will appear here.</section> : reports.map((report) =>
        <article className="panel report-card" key={report.id}>
          <div className="report-card-heading"><div><span className="eyebrow">{humanize(report.category)}</span><h3>{report.location_name}{report.area ? ` · ${report.area}` : ''}</h3></div><StatusPill status={report.status} /></div>
          <p>{report.description}</p><small>Submitted {new Date(report.submitted_at).toLocaleString()}</small>
          {report.flood_problem_id && <p className="official-problem-note"><strong>Official problem approved:</strong> {report.flood_problem_id}</p>}
          {report.public_status_updates.length > 0 && <div className="report-history public-status-timeline">
            <strong>Public response status</strong>
            {report.public_status_updates.map((update) => <span key={update.id}>
              <StatusPill status={update.status} /> {update.summary} · {new Date(update.published_at).toLocaleString()}
            </span>)}
          </div>}
          <details><summary>Verification & evidence ({report.verifications.length + report.evidence.length})</summary>
            <EvidenceLinks files={report.evidence} />
            {report.verifications.map((verification) => <div className="report-history" key={verification.id}>
              <strong>Field verification · {humanize(verification.outcome)}</strong>
              <span>{verification.observed_condition}</span>
              <EvidenceLinks files={verification.evidence} />
            </div>)}
            {report.requested_information && <div className="report-history">
              <strong>Information requested</strong>
              <span>{report.requested_information}</span>
            </div>}
          </details>
          {report.status === 'NEEDS_INFORMATION' && <form className="auth-form report-update-form" onSubmit={async (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            if (await onUpdate(report.id, { description: formValue(form, 'description'), evidence: filesFrom(form) })) form.reset();
          }}>
            <label>Additional description<textarea name="description" minLength={10} maxLength={2000} required defaultValue={report.description} rows={3} /></label>
            <label>Additional evidence<input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple /><small>Up to 3 files, 5 MB each.</small></label>
            <button className="primary-button" type="submit">Send requested information</button>
          </form>}
        </article>,
      )}
    </section>
  </>;
}

function VerificationForm({
  report, busy, onVerify,
}: {
  report: CitizenReport;
  busy: boolean;
  onVerify: (id: string, payload: {
    outcome: 'VERIFIED' | 'NOT_VERIFIED'; observed_condition: string;
    severity?: ReportSeverity; notes: string; evidence: FileList | null;
  }) => Promise<boolean>;
}) {
  return <form className="auth-form nested-report-form" onSubmit={async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const outcome = formValue(form, 'outcome') as 'VERIFIED' | 'NOT_VERIFIED';
    if (await onVerify(report.id, {
        outcome,
        observed_condition: formValue(form, 'observed_condition'),
        severity: outcome === 'VERIFIED' ? formValue(form, 'severity') as ReportSeverity : undefined,
        notes: formValue(form, 'notes'),
        evidence: filesFrom(form),
      })) form.reset();
  }}>
    <label>Verification outcome<select name="outcome" defaultValue="VERIFIED"><option value="VERIFIED">Problem verified</option><option value="NOT_VERIFIED">Problem not verified</option></select></label>
    <label>Observed condition<textarea name="observed_condition" minLength={3} maxLength={1000} required rows={2} /></label>
    <label>Severity<select name="severity" defaultValue="MODERATE">{severities.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
    <label>Field notes<textarea name="notes" maxLength={2000} rows={2} /></label>
    <label>Evidence<input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple /><small>Up to 3 files, 5 MB each.</small></label>
    <button className="primary-button" type="submit" disabled={busy}>Save field verification</button>
  </form>;
}

function FieldView({
  pending, reports, locations, selectedLocation, setSelectedLocation, busy, onCreate, onVerify, onSupplement,
}: {
  pending: CitizenReport[];
  reports: FieldReport[];
  locations: RiskLocation[];
  selectedLocation: string;
  setSelectedLocation: (value: string) => void;
  busy: boolean;
  onCreate: (event: FormEvent<HTMLFormElement>) => Promise<boolean>;
  onVerify: (id: string, payload: Omit<Parameters<typeof reportService.verifyCitizen>[1], 'evidence'> & { evidence: FileList | null }) => Promise<boolean>;
  onSupplement: (id: string, payload: Omit<Parameters<typeof reportService.supplementField>[1], 'evidence'> & { evidence: FileList | null }) => Promise<boolean>;
}) {
  const [newLocation, setNewLocation] = useState(false);
  return <>
    <section className="panel report-form-panel">
      <h2>Record an independent field inspection</h2>
      <p>Start from a predicted hotspot or document a newly discovered location. Citizen complaints are optional.</p>
      <form className="auth-form report-form" onSubmit={async (event) => { if (await onCreate(event)) setNewLocation(false); }}>
        <LocationSelect locations={locations} allowNew selectedId={newLocation ? '__new__' : selectedLocation} onChange={(value) => { setNewLocation(value === '__new__'); setSelectedLocation(value === '__new__' ? '' : value); }} />
        {newLocation && <div className="report-form-grid">
          <label>Location name<input name="location_name" required maxLength={160} /></label>
          <label>Area / neighborhood<input name="area" maxLength={120} /></label>
          <label>Latitude<input name="latitude" type="number" min={-90} max={90} step="any" required /></label>
          <label>Longitude<input name="longitude" type="number" min={-180} max={180} step="any" required /></label>
        </div>}
        <label>Observed issue<select name="category" defaultValue="FLOODING">{categories.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>Inspection outcome<select name="outcome" defaultValue="PROBLEM_FOUND"><option value="PROBLEM_FOUND">Problem found</option><option value="INSPECTED_NO_PROBLEM_FOUND">Inspected — No Problem Found</option></select></label>
        <label>Observed condition<textarea name="observed_condition" minLength={3} maxLength={1000} rows={3} required placeholder="Describe the observed water, drainage, or no-problem condition." /></label>
        <label>Severity<select name="severity" defaultValue="MODERATE">{severities.map((value) => <option key={value} value={value}>{value}</option>)}</select><small>Used only when a problem is found.</small></label>
        <label>Inspection notes<textarea name="description" minLength={10} maxLength={2000} rows={3} required /></label>
        <label>Evidence (optional)<input name="evidence" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple /><small>Up to 3 files, 5 MB each.</small></label>
        <button className="primary-button" type="submit" disabled={busy}>Save field report for admin review</button>
      </form>
    </section>
    <section className="report-list-section"><div className="report-section-heading"><div><span className="eyebrow">Citizen submissions awaiting inspection</span><h2>Pending citizen reports</h2></div><span>{pending.length} pending</span></div>
      {pending.length === 0 ? <section className="panel report-empty">No citizen reports are waiting for field verification.</section> : pending.map((report) =>
        <article className="panel report-card" key={report.id}>
          <div className="report-card-heading"><div><span className="eyebrow">{humanize(report.category)}</span><h3>{report.location_name}{report.area ? ` · ${report.area}` : ''}</h3></div><StatusPill status={report.status} /></div>
          <p>{report.description}</p><EvidenceLinks files={report.evidence} />
          <VerificationForm report={report} busy={busy} onVerify={onVerify} />
        </article>,
      )}
    </section>
    <section className="report-list-section"><div className="report-section-heading"><div><span className="eyebrow">Your field submissions</span><h2>My field reports</h2></div><span>{formatReportCount(reports.length)}</span></div>
      {reports.length === 0 ? <section className="panel report-empty">No independent field reports have been recorded.</section> : reports.map((report) =>
        <article className="panel report-card" key={report.id}>
          <div className="report-card-heading"><div><span className="eyebrow">{humanize(report.category)}</span><h3>{report.location_name}{report.area ? ` · ${report.area}` : ''}</h3></div><StatusPill status={report.status} /></div>
          <p>{report.description}</p><p><strong>Observation:</strong> {report.observed_condition}</p>
          <p><strong>Outcome:</strong> {report.outcome === 'INSPECTED_NO_PROBLEM_FOUND' ? 'Inspected — No Problem Found' : `Problem found · ${report.severity}`}</p>
          {report.prediction_id && <p className="report-muted">AI risk prediction reference: {report.prediction_id}</p>}
          {report.citizen_report_id && <p className="report-muted">Linked citizen report: {report.citizen_report_id}</p>}
          <EvidenceLinks files={report.evidence} />
          {report.flood_problem_id && <p className="official-problem-note">Official problem approved: {report.flood_problem_id}</p>}
          {report.reviews.map((review) => <div className="report-history" key={review.id}><strong>Admin · {humanize(review.decision)}</strong>{review.requested_information && <span>{review.requested_information}</span>}</div>)}
          {report.status === 'NEEDS_INFORMATION' && <form className="auth-form report-update-form" onSubmit={async (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const outcome = formValue(form, 'outcome') as FieldReport['outcome'];
            if (await onSupplement(report.id, {
              description: formValue(form, 'description'),
              observed_condition: formValue(form, 'observed_condition'),
              outcome,
              severity: outcome === 'PROBLEM_FOUND' ? formValue(form, 'severity') as ReportSeverity : undefined,
              evidence: filesFrom(form),
            })) form.reset();
          }}>
            <label>Updated observation<textarea name="observed_condition" minLength={3} maxLength={1000} required defaultValue={report.observed_condition} rows={2} /></label>
            <label>Outcome<select name="outcome" defaultValue={report.outcome}><option value="PROBLEM_FOUND">Problem found</option><option value="INSPECTED_NO_PROBLEM_FOUND">Inspected — No Problem Found</option></select></label>
            <label>Severity<select name="severity" defaultValue={report.severity ?? 'MODERATE'}>{severities.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            <label>Updated notes<textarea name="description" minLength={10} maxLength={2000} defaultValue={report.description} rows={2} required /></label>
            <label>Additional evidence<input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" multiple /></label>
            <button className="primary-button" type="submit">Send additional information</button>
          </form>}
        </article>,
      )}
    </section>
  </>;
}

function ReviewActions({
  source,
  id,
  defaultSeverity,
  allowApprove = true,
  disabled,
  onReview,
}: {
  source: 'CITIZEN_REPORT' | 'FIELD_REPORT';
  id: string;
  defaultSeverity?: ReportSeverity | null;
  allowApprove?: boolean;
  disabled: boolean;
  onReview: (source: 'CITIZEN_REPORT' | 'FIELD_REPORT', id: string, payload: {
    decision: ReviewDecision; requested_information?: string; severity?: ReportSeverity;
  }) => Promise<boolean>;
}) {
  const [decision, setDecision] = useState<ReviewDecision>(allowApprove ? 'APPROVE' : 'REJECT');
  const [severity, setSeverity] = useState<ReportSeverity>(defaultSeverity ?? 'MODERATE');
  const [information, setInformation] = useState('');
  return <div className="review-controls">
    <label>Decision<select value={decision} onChange={(event) => setDecision(event.target.value as ReviewDecision)}>
      {allowApprove && <option value="APPROVE">Approve official FloodProblem</option>}
      <option value="REJECT">Reject report</option>
      <option value="REQUEST_INFORMATION">Request more information</option>
    </select></label>
    {decision === 'APPROVE' && <label>Official severity<select value={severity} onChange={(event) => setSeverity(event.target.value as ReportSeverity)}>{severities.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>}
    {decision === 'REQUEST_INFORMATION' && <label>Information needed<input value={information} onChange={(event) => setInformation(event.target.value)} maxLength={2000} /></label>}
    <button className={decision === 'APPROVE' ? 'primary-button' : 'secondary-button'} disabled={disabled || (decision === 'REQUEST_INFORMATION' && information.trim().length < 3)} onClick={() => void onReview(source, id, {
      decision,
      requested_information: information,
      severity: decision === 'APPROVE' ? severity : undefined,
    })}>{decision === 'APPROVE' ? 'Approve official problem' : decision === 'REJECT' ? 'Reject report' : 'Request information'}</button>
  </div>;
}

function AdminView({
  queue, problems, activeTab, setActiveTab, busy, onReview,
}: {
  queue: AdminReportQueue;
  problems: FloodProblem[];
  activeTab: 'review' | 'problems';
  setActiveTab: (tab: 'review' | 'problems') => void;
  busy: boolean;
  onReview: (source: 'CITIZEN_REPORT' | 'FIELD_REPORT', id: string, payload: {
    decision: ReviewDecision; requested_information?: string; severity?: ReportSeverity;
  }) => Promise<boolean>;
}) {
  return <>
    <div className="report-tabs" role="tablist" aria-label="Administrative review views">
      <button role="tab" aria-selected={activeTab === 'review'} onClick={() => setActiveTab('review')}>Review queue ({queue.citizen_reports.length + queue.field_reports.length})</button>
      <button role="tab" aria-selected={activeTab === 'problems'} onClick={() => setActiveTab('problems')}>Official FloodProblems ({problems.length})</button>
    </div>
    {activeTab === 'review' ? <>
      <section className="report-list-section"><div className="report-section-heading"><div><span className="eyebrow">Field verification required before citizen approval</span><h2>Citizen reports</h2></div><span>{queue.citizen_reports.length} awaiting review</span></div>
        {queue.citizen_reports.length === 0 ? <section className="panel report-empty">No verified citizen reports are awaiting administrative review.</section> : queue.citizen_reports.map((report) => {
          const verification = report.verifications[report.verifications.length - 1];
          return <article className="panel report-card" key={report.id}>
            <div className="report-card-heading"><div><span className="eyebrow">{humanize(report.category)} · Citizen report</span><h3>{report.location_name}{report.area ? ` · ${report.area}` : ''}</h3></div><StatusPill status={report.status} /></div>
            <p>{report.description}</p><p><strong>Latest field finding:</strong> {verification ? humanize(verification.outcome) : 'Not verified'} — {verification?.observed_condition}</p>
            <EvidenceLinks files={report.evidence} />
            {verification && <div className="report-history"><strong>Field notes · {verification.severity ?? 'Severity not set'}</strong><span>{verification.notes}</span><EvidenceLinks files={verification.evidence} /></div>}
            <ReviewActions source="CITIZEN_REPORT" id={report.id} defaultSeverity={verification?.severity} allowApprove={report.status === 'VERIFIED'} disabled={busy} onReview={onReview} />
            {report.status === 'NOT_VERIFIED' && <p className="report-muted">This report was not verified; it cannot be approved as an official problem.</p>}
          </article>;
        })}
      </section>
      <section className="report-list-section"><div className="report-section-heading"><div><span className="eyebrow">Independent proactive inspections</span><h2>Field reports</h2></div><span>{queue.field_reports.length} awaiting review</span></div>
        {queue.field_reports.length === 0 ? <section className="panel report-empty">No field reports are awaiting administrative review.</section> : queue.field_reports.map((report) =>
          <article className="panel report-card" key={report.id}>
            <div className="report-card-heading"><div><span className="eyebrow">{humanize(report.category)} · Field report</span><h3>{report.location_name}{report.area ? ` · ${report.area}` : ''}</h3></div><StatusPill status={report.status} /></div>
            <p>{report.description}</p><p><strong>Observed condition:</strong> {report.observed_condition}</p>
            <p><strong>Inspection outcome:</strong> {report.outcome === 'INSPECTED_NO_PROBLEM_FOUND' ? 'Inspected — No Problem Found' : `Problem found · ${report.severity}`}</p>
            {report.prediction_id && <p className="report-muted">RiskPrediction reference: {report.prediction_id}</p>}
            {report.citizen_report_id && <p className="report-muted">Related CitizenReport: {report.citizen_report_id}</p>}
            <EvidenceLinks files={report.evidence} />
            {report.outcome === 'INSPECTED_NO_PROBLEM_FOUND' && <p className="report-muted">A no-problem inspection is an observation and cannot create a FloodProblem.</p>}
            <ReviewActions source="FIELD_REPORT" id={report.id} defaultSeverity={report.severity} allowApprove={report.outcome === 'PROBLEM_FOUND'} disabled={busy} onReview={onReview} />
          </article>,
        )}
      </section>
    </> : <section className="report-list-section"><div className="report-section-heading"><div><span className="eyebrow">Human-approved only</span><h2>Official FloodProblems</h2></div><span>{problems.length} official</span></div>
      {problems.length === 0 ? <section className="panel report-empty">No official FloodProblems have been approved.</section> : problems.map((problem) =>
        <article className="panel report-card" key={problem.id}>
          <div className="report-card-heading"><div><span className="eyebrow">FloodProblem · {problem.id}</span><h3>{problem.severity} · {problem.status}</h3></div><StatusPill status={problem.status} /></div>
          <p>Approved {new Date(problem.approved_at).toLocaleString()} by admin account {problem.approved_by_user_id}.</p>
          <p>{problem.citizen_report_id ? `CitizenReport: ${problem.citizen_report_id}` : `FieldReport: ${problem.field_report_id}`}</p>
        </article>,
      )}
    </section>}
  </>;
}
