import { ApiError, apiBaseUrl } from './auth-service';

export type ReportCategory = 'WATERLOGGING' | 'FLOODING' | 'BLOCKED_DRAINAGE' | 'OVERFLOW' | 'OTHER';
export type ReportSeverity = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type ReviewDecision = 'REQUEST_INFORMATION' | 'APPROVE' | 'REJECT';

export interface EvidenceFile {
  id: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  download_url: string;
}

export interface EvidenceUpload {
  file_name: string;
  content_type: 'image/jpeg' | 'image/png' | 'image/webp' | 'application/pdf';
  content_base64: string;
}

export interface ReportLocationPayload {
  location_id?: string;
  location_name?: string;
  area?: string;
  latitude?: number;
  longitude?: number;
}

export interface Verification {
  id: string;
  verifier_user_id: string;
  outcome: 'VERIFIED' | 'NOT_VERIFIED';
  observed_condition: string;
  severity: ReportSeverity | null;
  notes: string;
  verified_at: string;
  evidence: EvidenceFile[];
}

export interface CitizenVerification {
  id: string;
  outcome: 'VERIFIED' | 'NOT_VERIFIED';
  observed_condition: string;
  verified_at: string;
  evidence: EvidenceFile[];
}

export interface ReportReview {
  id: string;
  reviewer_user_id: string;
  decision: ReviewDecision;
  requested_information: string;
  severity: ReportSeverity | null;
  reviewed_at: string;
}

export interface CitizenReport {
  id: string;
  reporter_id: string;
  location_id: string | null;
  location_name: string;
  area: string;
  latitude: number | null;
  longitude: number | null;
  category: ReportCategory;
  description: string;
  status: 'PENDING_VERIFICATION' | 'VERIFIED' | 'NOT_VERIFIED' | 'UNDER_REVIEW' | 'NEEDS_INFORMATION' | 'APPROVED' | 'REJECTED';
  submitted_at: string;
  updated_at: string;
  evidence: EvidenceFile[];
  verifications: Verification[];
  reviews: ReportReview[];
  flood_problem_id: string | null;
}

export interface MyCitizenReport extends Omit<CitizenReport, 'reporter_id' | 'verifications' | 'reviews'> {
  verifications: CitizenVerification[];
  requested_information: string | null;
  public_status_updates: PublicStatusUpdate[];
}

export interface PublicStatusUpdate {
  id: string;
  status: string;
  summary: string;
  published_at: string;
}

export interface FieldReport {
  id: string;
  author_user_id: string;
  location_id: string | null;
  location_name: string;
  area: string;
  latitude: number | null;
  longitude: number | null;
  prediction_id: string | null;
  citizen_report_id: string | null;
  category: ReportCategory;
  description: string;
  observed_condition: string;
  outcome: 'PROBLEM_FOUND' | 'INSPECTED_NO_PROBLEM_FOUND';
  severity: ReportSeverity | null;
  status: 'PENDING_REVIEW' | 'NEEDS_INFORMATION' | 'APPROVED' | 'REJECTED';
  observed_at: string;
  updated_at: string;
  evidence: EvidenceFile[];
  reviews: ReportReview[];
  flood_problem_id: string | null;
}

export interface FloodProblem {
  id: string;
  citizen_report_id: string | null;
  field_report_id: string | null;
  severity: ReportSeverity;
  status: 'OPEN';
  approved_by_user_id: string;
  approved_at: string;
}

export interface AdminReportQueue {
  citizen_reports: CitizenReport[];
  field_reports: FieldReport[];
}

export interface ResponseTaskEvidence extends EvidenceFile {
  uploaded_at: string;
}

export interface ResponseTaskUpdate {
  id: string;
  actor_user_id: string;
  previous_status: string;
  new_status: string;
  action_taken: string;
  condition: string;
  internal_notes: string;
  blockers: string;
  completion_decision: 'APPROVE' | 'RETURN_FOR_ACTION' | null;
  created_at: string;
  evidence: ResponseTaskEvidence[];
}

export type ResponseTaskStatus = 'ASSIGNED' | 'ACCEPTED' | 'EN_ROUTE' | 'INSPECTED' | 'ACTION_REQUIRED' | 'RESOLVED';
export type ResponseTaskPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export interface ResponseTask {
  id: string;
  flood_problem_id: string;
  instruction: string;
  details: string;
  priority: ResponseTaskPriority;
  assigned_user_id: string;
  assigned_user_email: string;
  due_at: string | null;
  status: ResponseTaskStatus;
  completion_status: 'NOT_SUBMITTED' | 'PENDING_REVIEW' | 'APPROVED' | 'RETURNED';
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  updates: ResponseTaskUpdate[];
}

export interface FieldResponseUser {
  id: string;
  email: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: 'include',
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  });
  if (!response.ok) {
    let message = 'The report service could not complete the request.';
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the generic error for responses without JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function encodeFiles(files: FileList | null): Promise<EvidenceUpload[]> {
  if (!files?.length) return [];
  if (files.length > 3) throw new Error('Attach no more than 3 evidence files.');
  const supported: Record<string, EvidenceUpload['content_type'] | undefined> = {
    'image/jpeg': 'image/jpeg',
    'image/png': 'image/png',
    'image/webp': 'image/webp',
    'application/pdf': 'application/pdf',
  };
  const result: EvidenceUpload[] = [];
  for (const file of Array.from(files)) {
    const contentType = supported[file.type];
    if (!contentType) throw new Error(`${file.name}: use a JPEG, PNG, WebP, or PDF file.`);
    if (!file.size || file.size > 5 * 1024 * 1024) throw new Error(`${file.name}: evidence must be 5 MB or smaller.`);
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = '';
    const chunkSize = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
    }
    result.push({
      file_name: file.name,
      content_type: contentType,
      content_base64: btoa(binary),
    });
  }
  return result;
}

const json = (payload: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(payload) });

export const reportService = {
  encodeFiles,
  listMine: () => request<MyCitizenReport[]>('/api/reports/mine'),
  createCitizen: (payload: { location: ReportLocationPayload; category: ReportCategory; description: string; evidence: EvidenceUpload[] }) =>
    request<MyCitizenReport>('/api/reports', json(payload)),
  updateCitizen: (id: string, payload: { description: string; evidence: EvidenceUpload[] }) =>
    request<MyCitizenReport>(`/api/reports/mine/${encodeURIComponent(id)}/update`, json(payload)),
  listPending: () => request<CitizenReport[]>('/api/field/reports/pending'),
  verifyCitizen: (id: string, payload: { outcome: Verification['outcome']; observed_condition: string; severity?: ReportSeverity; notes: string; evidence: EvidenceUpload[] }) =>
    request<CitizenReport>(`/api/field/reports/${encodeURIComponent(id)}/verify`, json(payload)),
  listField: () => request<FieldReport[]>('/api/field/reports'),
  createField: (payload: {
    location: ReportLocationPayload; category: ReportCategory; description: string; observed_condition: string;
    outcome: FieldReport['outcome']; severity?: ReportSeverity; prediction_id?: string;
    citizen_report_id?: string; evidence: EvidenceUpload[];
  }) => request<FieldReport>('/api/field/reports', json(payload)),
  supplementField: (id: string, payload: {
    description: string; observed_condition: string; outcome: FieldReport['outcome'];
    severity?: ReportSeverity; evidence: EvidenceUpload[];
  }) => request<FieldReport>(`/api/field/reports/${encodeURIComponent(id)}/supplement`, json(payload)),
  adminQueue: () => request<AdminReportQueue>('/api/admin/reports'),
  review: (sourceType: 'CITIZEN_REPORT' | 'FIELD_REPORT', id: string, payload: {
    decision: ReviewDecision; requested_information?: string; severity?: ReportSeverity;
  }) => request<{ flood_problem_id: string | null }>(
    `/api/admin/reports/${sourceType}/${encodeURIComponent(id)}/review`, json(payload),
  ),
  floodProblems: () => request<FloodProblem[]>('/api/admin/flood-problems'),
  evidenceUrl: (file: EvidenceFile) => `${apiBaseUrl}${file.download_url}`,
  fieldUsers: () => request<FieldResponseUser[]>('/api/admin/field-users'),
  adminTasks: () => request<ResponseTask[]>('/api/admin/response-tasks'),
  fieldTasks: () => request<ResponseTask[]>('/api/field/response-tasks'),
  createTask: (payload: {
    flood_problem_id: string;
    instruction: string;
    details: string;
    priority: ResponseTaskPriority;
    assigned_user_id: string;
    due_at?: string;
  }) => request<ResponseTask>('/api/admin/response-tasks', json(payload)),
  updateTask: (id: string, payload: {
    new_status: ResponseTaskStatus;
    action_taken: string;
    condition: string;
    internal_notes: string;
    blockers: string;
    evidence: EvidenceUpload[];
  }) => request<ResponseTask>(`/api/field/response-tasks/${encodeURIComponent(id)}/updates`, json(payload)),
  reviewTaskCompletion: (id: string, payload: { decision: 'APPROVE' | 'RETURN_FOR_ACTION'; internal_notes: string }) =>
    request<ResponseTask>(`/api/admin/response-tasks/${encodeURIComponent(id)}/completion-review`, json(payload)),
};
