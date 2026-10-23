# FloodSense Implementation Plan

## Product direction

FloodSense is an AI flood-risk and hotspot-prioritization decision-support
system. Its primary path is:

```text
RiskPrediction -> hotspot prioritization -> field inspection
-> FieldReport / FieldVerification -> administrative review
-> FloodProblem -> ResponseTask -> response/status update
```

Citizen reports are a second input to verification and review; they are not a
prerequisite for proactive field inspection. Predicted risk, citizen reports,
field observations, officially recognized problems, and response instructions
remain separate concepts and records.

The application has exactly these roles:

- `CITIZEN`
- `FIELD_RESPONSE_PLANNING`
- `DISASTER_MANAGEMENT_ADMIN`

Each account has exactly one role, stored directly in `users.role`. The backend
assigns and returns the account's role after authentication. A real login never
accepts a role from the client. A role chooser may be provided only through an
explicitly labeled demo-account flow that is disabled unless development demo
mode is enabled.

Delivery is feature-by-feature in vertical slices. A phase may include more
than one role, but no phase is a role-specific build. Every slice that changes
workflow state includes persistence, API validation, authorization, UI, audit
where applicable, and tests.

## Priority order

| Priority | Feature | Phase | Dependencies |
| --- | --- | --- | --- |
| P0.1 | Shared location and persisted risk-prediction foundation | 1 | Existing replay adapter and scoring service |
| P0.2 | Account authentication, one-role assignment, and authorization for all three roles | 1 | User/session schema |
| P0.3 | Common risk map, prioritized hotspots, and role-appropriate risk views | 1 | P0.1, P0.2 |
| P0.4 | Citizen report submission and own-report tracking | 2 | P0.2, locations |
| P0.5 | Proactive field inspection, independent field reports, and “inspected — no problem found” | 2 | P0.1, P0.2 |
| P0.6 | Citizen-report verification and separate field verification records | 2 | P0.4, P0.5 |
| P0.7 | Admin review, approve/reject, and official FloodProblem creation | 2 | P0.4, P0.5, P0.6 |
| P0.8 | Admin response instruction and ResponseTask assignment | 3 | P0.7 |
| P0.9 | Field task updates and public status / citizen report tracking | 3 | P0.8 |
| P1.1 | Prediction-versus-observation and historical hotspot analysis | 4 | P0.1, P0.5, stable lifecycle data |
| P1.2 | Risk explanation, data freshness, and model-version visibility | 4 | Risk/data-source contracts |
| P1.3 | Security, accessibility, performance, integration, and operational hardening | 4 | Phases 1–3 |
| P2 | SMS/WhatsApp, CCTV, satellite detection, advanced hydrodynamic modelling, autonomous dispatch, road-closure automation, multi-hazard expansion | Future | Explicitly outside P0 delivery |

P1 and P2 work must not delay the P0 end-to-end workflow.

## Phase 1 — Foundation + AI Risk Intelligence

**Vertical slice:** establish one shared identity, authorization, location, and
RiskPrediction foundation and deliver appropriately scoped risk information
to Citizen, Field Response Planning, and Disaster Management Admin.

### Features and dependencies

1. Persist locations, risk predictions, source metadata, and audit events.
   Reuse the existing replay adapter and model; identify outputs as replay/demo
   predictions rather than validated forecasts. No live provider or accuracy
   claim is introduced.
2. Authenticate users and derive role from the persisted account. Store exactly
   one `users.role`, constrained to the three allowed enum values.
3. Deliver the same underlying risk/location/prediction records through shared
   services and APIs, with public, operational, or command-level presentation
   appropriate to the authenticated role.
4. Provide a development-only demo-account login selector only when demo mode is
   explicitly enabled. It resolves to backend-provisioned demo accounts; real
   login has no role input.
5. Provide a minimal admin account-provisioning path to support onboarding;
   the caller must already be an authenticated Disaster Management Admin.

### Database changes

- `users`: unique email, password hash, one constrained role, active flag,
  created/updated timestamps.
- `sessions`: hashed opaque session token, user foreign key, expiry, creation
  and revocation timestamps.
- `locations`: stable id, name, area, coordinates, source/reference metadata.
- `risk_predictions`: separate immutable prediction snapshot per location,
  score/category, prediction window/time, model version, drivers and data mode.
- `data_sources`: source state, freshness and descriptive status.
- `audit_logs`: actor, action, target type/id, timestamp, and non-sensitive
  structured detail.

No role mapping table and no generic Problem table. A local SQLite database is
the initial persistence adapter; its path is configurable and production
deployment must provide a persistent supported database location.

### API changes

- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- Demo-only `POST /api/auth/demo-login`, unavailable when demo mode is off
- Admin-only `POST /api/admin/users`
- Authenticated `GET /api/dashboard`, `/api/locations`, `/api/locations/{id}`,
  `/api/priorities`, and `/api/data/status`
- Health endpoint remains public and contains no account or private data.
- Session cookies are HttpOnly, SameSite-protected, expiring, and revocable.
- Validate roles against the closed three-value set; real login and profile
  responses obtain role only from the stored account.

### Frontend changes

- Add real email/password sign-in and session restoration/logout.
- Add clearly marked development/demo-account sign-in controls only when the
  backend reports demo mode; controls do not masquerade as real authentication.
- Reuse the risk map and hotspot views for all roles; identify the role and use
  role-appropriate page framing without duplicating the risk model/data path.
- Handle expired sessions and API errors explicitly.

### RBAC

| Capability | CITIZEN | FIELD_RESPONSE_PLANNING | DISASTER_MANAGEMENT_ADMIN |
| --- | --- | --- | --- |
| Sign in and view risk/location data | Yes, public risk information | Yes, operational risk and hotspots | Yes, command-level risk and source status |
| Read internal data-source or model configuration | No | Operational source status only | Yes |
| Read another user's private data | No | No | Only future admin review workflows as explicitly authorized |
| Provision accounts / assign one allowed role | No | No | Yes |
| Change own role through login/profile | No | No | No |

### Acceptance criteria

- Each of the three roles can authenticate and reach its role-appropriate risk
  view from a backend-persisted account.
- The account's role is returned from backend identity; changing a client
  request cannot elevate permissions.
- The same location and RiskPrediction records feed all role views.
- Risk and source values remain clearly labeled replay/demo where applicable.
- Demo role selection cannot run unless development demo mode is enabled.

### Tests

- Role constraint and unique user/session persistence tests.
- Password verification, session expiry/revocation, login, logout, and `/me`
  tests.
- API authorization tests for each role, including forbidden admin user
  provisioning by non-admins.
- Risk prediction persistence and shared ranking tests.
- Frontend build and sign-in/session behavior tests.

### Definition of Done

- All three roles authenticate and access appropriately scoped risk intelligence
  backed by the same persisted location and prediction architecture.
- Role assignment is backend-controlled; exactly three roles are possible.
- Existing dashboard functionality remains available behind authentication.
- Database/API/UI and authorization behavior are tested; no report/problem/task
  concepts are conflated or prematurely implemented.

## Phase 2 — Report → Verify → Official Problem

**Vertical slice:** accept both citizen-submitted and proactive field-discovered
inputs, record field observation independently, then require human admin review
before any official FloodProblem exists.

### Features and dependencies

1. Citizen submits Waterlogging, Flooding, Blocked Drainage, Overflow, or Other
   report with location, description, optional evidence, timestamp, and status.
2. Citizen lists and reads only their own reports and sees verification,
   response, and latest public status fields that are available.
3. Field Response sees reports requiring verification and can record a separate
   FieldVerification with verified/not-verified outcome, observed condition,
   severity, notes, evidence, and timestamp.
4. Field Response can independently create a FieldReport linked optionally to
   a prediction and/or citizen report; neither link is required. A proactive
   inspection can explicitly record `INSPECTED_NO_PROBLEM_FOUND`.
5. Admin reviews citizen reports, field verifications, and independent field
   reports; can request information, approve, or reject. Only explicit
   administrative approval creates a separate FloodProblem.

### Database changes

- `citizen_reports`: reporter, location, category, description, evidence
  reference, submission time, and status (`PENDING_VERIFICATION`, `VERIFIED`,
  `NOT_VERIFIED`, `NEEDS_INFORMATION`, `APPROVED`, or `REJECTED`).
- `field_reports`: author, location, category, description, severity, observed
  condition, outcome including no-problem-found, optional prediction/report
  references, evidence, observation time, and admin-review status.
- `field_verifications`: citizen report, verifier, outcome, condition,
  severity, notes/evidence, verified time.
- `report_reviews`: admin reviewer, source entity reference, decision,
  information request, severity/priority, decision timestamp.
- `flood_problems`: official status, severity/priority, approving admin,
  approval timestamp, separate optional source references.
- `attachments`: uploader, exactly one parent entity, file metadata, content
  bytes, SHA-256 digest, and upload time. Accept JPEG, PNG, WebP, and PDF up to
  5 MB per file, at most three files and 10 MB total per submission; validate
  decoded content signatures against declared content types.

Newly discovered places are stored as report location snapshots with
coordinates; they do not mutate the risk-location or RiskPrediction records.

### API changes

- Citizen create/list/detail endpoints enforce reporter ownership.
- Citizen report responses expose only the public-safe verification summary and
  user-facing information requests; internal field notes, reviewer identity,
  and administrative review metadata remain restricted to operational/admin
  endpoints.
- Field pending queue, independent FieldReport creation, and report verification
  endpoints require `FIELD_RESPONSE_PLANNING`.
- Admin review endpoints require `DISASTER_MANAGEMENT_ADMIN`.
- FloodProblem creation occurs only in the admin approval transaction.
- Validate lifecycle transitions and evidence metadata; record audit events.
- Implemented routes: `POST /api/reports`, `GET /api/reports/mine`,
  `GET /api/reports/mine/{id}`, `POST /api/reports/mine/{id}/update`,
  `GET /api/field/reports/pending`, `POST /api/field/reports/{id}/verify`,
  `POST /api/field/reports`, `GET /api/field/reports`,
  `POST /api/field/reports/{id}/supplement`, `GET /api/admin/reports`,
  `POST /api/admin/reports/{source_type}/{id}/review`,
  `GET /api/admin/flood-problems`, and authorized
  `GET /api/evidence/{attachment_id}`.

### Frontend changes

- Citizen report form and My Reports list/detail.
- Field risk-map inspection action that retains its RiskPrediction reference,
  verification queue, independent observation form, and distinct
  no-problem-found action.
- Admin review queue for both report types, evidence review, decision capture,
  request-information lifecycle, and official FloodProblem view.

### RBAC

- Citizens create reports and read only their own reports plus permitted
  public information.
- Field Response reads operationally relevant reports, records verification,
  and creates FieldReports; cannot approve or create FloodProblems.
- Admin can review source records and approve/reject; cannot rewrite a risk
  prediction as an observation.

### Acceptance criteria

- A report can be followed from citizen submission through independent field
  verification to admin review and official recognition.
- A FieldReport can be created from an AI hotspot or newly discovered location
  with no CitizenReport.
- `INSPECTED_NO_PROBLEM_FOUND` is persisted as an observation and is not
  interpreted as an official problem.
- No prediction, CitizenReport, or FieldReport automatically becomes a
  FloodProblem.

### Tests

- Citizen ownership and cross-account access denial.
- Field create-without-citizen-link and no-problem-found flows.
- Verification and report state-transition validation.
- Admin approval/rejection tests proving only approval creates FloodProblem.
- Non-final request-information/resubmission tests for both report streams.
- Evidence content/size/signature validation, owner authorization, download
  headers, audit events, and transaction rollback tests.

### Definition of Done

- Both citizen-driven and proactive AI-to-field paths reach admin review with
  distinct source records, and the only official problem creation path is
  authorized administrative approval.

## Phase 3 — Response Coordination

**Vertical slice:** turn approved official problems into accountable field
instructions, capture operational updates, and expose only an appropriate
public status to citizens.

### Features and dependencies

1. Admin creates an instruction only for an approved FloodProblem, assigns it
   to an active Field Response user, and sets priority, task details, and an
   optional timezone-aware deadline.
2. Field Response sees assigned tasks and advances valid states:
   `ASSIGNED -> ACCEPTED -> EN_ROUTE -> INSPECTED -> ACTION_REQUIRED ->
   RESOLVED`. A resolved submission is marked `PENDING_REVIEW`; Admin approves
   completion or returns the task to `ACTION_REQUIRED`.
3. Field Response records action, condition, internal notes, blockers, and
   optional evidence with each update; Admin monitors complete task progress
   and reviews completion submissions.
4. Citizen sees fixed public-safe progress summaries for an official problem
   linked to their own report; field notes, evidence, staff identity, and
   administrative review data remain private.

### Database changes

- `response_tasks`: official flood problem, instruction, priority, assignee,
  optional details/deadline, status, completion-review status, creator, and
  creation/update timestamps.
- `task_updates`: actor, previous/new status, action, condition, internal notes,
  blockers, completion decision, and timestamp.
- `task_evidence`: private file bytes and validated file metadata linked to a
  task update.
- `public_status_updates`: official problem/report/task relation, lifecycle
  status, fixed public-safe text, and publication timestamp.

### API changes

- Admin create/list/assign tasks and monitor progress.
- Field assigned-task list and transition/update endpoints.
- Citizen-safe incident and own-report status endpoints use explicit response
  schemas that exclude internal notes and audit data.
- Enforce valid state transitions, role permissions, and audit each transition.
- Implemented routes: `GET /api/admin/field-users`,
  `POST /api/admin/response-tasks`, `GET /api/admin/response-tasks`,
  `GET /api/field/response-tasks`,
  `POST /api/field/response-tasks/{id}/updates`,
  `POST /api/admin/response-tasks/{id}/completion-review`.

### Frontend changes

- Admin instruction/assignment and response monitor views.
- Field task inbox and step-by-step response updates.
- Public incident status and citizen My Reports status timeline.

### RBAC

- Admin creates and assigns tasks and sees full operational updates.
- Field Response updates tasks assigned to the role/user and sees operational
  detail required for response.
- Citizen reads only public incident data and their own report's permitted
  status; cannot see other citizens or internal notes/evidence.

### Acceptance criteria

- A reviewed official problem is assigned and can be tracked through valid field
  updates to resolution.
- Public updates are separated from internal notes and identify no private
  citizen data.
- Citizen can track their own report without gaining access to other reports.

### Tests

- Complete Admin → Field → Citizen response workflow.
- State transition and assignment authorization matrix.
- Public serializer leakage tests for internal notes, evidence, audit, and
  unrelated citizen identity.
- Task update audit and status consistency tests.

### Definition of Done

- The P0 end-to-end workflow runs from prediction/report through review,
  response, resolution, and appropriate citizen-visible status.

### Phase 3 implementation status

- Implemented approved-problem-only task creation, active field-user assignment,
  priority/details, and optional timezone-aware deadlines.
- Implemented assigned-user-only field inbox, strict transitions, private
  operational updates/evidence, and administrator completion approval or
  return-for-action.
- Implemented fixed public-safe citizen status summaries scoped to the citizen's
  own linked report; no field/admin private details enter this response.

## Phase 4 — Analytics + Hardening

**Vertical slice:** make accumulated observations useful for all relevant
roles, while validating the integrated P0 workflow and improving reliability.

### Features and dependencies

1. Compare prediction snapshots with later FieldReports/FieldVerifications,
   including no-problem-found observations.
2. Analyze repeated hotspots, historical flood events, problem frequency, and
   preventive-attention needs.
3. Explain risk drivers, prediction time/window, model version, and data
   freshness using explicitly sourced information.
4. Harden security, accessibility, performance, errors, audit integrity, and
   operational documentation after P0 flows are stable.

### Database changes

- Add model/data-source version metadata and query indexes where measurements
  demonstrate a need.
- Preserve append-only prediction/observation history and avoid derived
  analytics that overwrite source records.
- Add analytics materializations only if query/load evidence requires them.

### API changes

- Role-scoped historical, trend, and prediction-vs-observation endpoints.
- Explicit model/data freshness and provenance endpoints.
- Security headers, rate limits, consistent error responses, and audit queries
  as required by deployment review.

### Frontend changes

- Planning trend and comparison views for Field Response and Admin.
- Public dashboard retains only public risk information.
- Improve accessible map alternatives, keyboard navigation, responsive
  behavior, and source/model transparency.

### RBAC

- Citizen sees only explicitly public summaries.
- Field Response sees operational analytics needed for planning.
- Admin sees command, system, model, and audit detail.
- No analytics endpoint bypasses source ownership or public/private filtering.

### Acceptance criteria

- Predictions can be compared with distinct field observations without
  relabeling historical predictions or fabricating model performance.
- Source/model provenance and stale/unavailable data are visible.
- All three roles retain their least-privilege boundaries after hardening.
- No deferred P2 feature is introduced as if operational.

### Tests

- Analytics correctness for found/no-problem observations and time windows.
- API security/RBAC regression and public-data leak tests.
- Accessibility checks, performance baselines, and end-to-end P0 regression.
- Audit completeness and data migration/backup-restore checks.

### Definition of Done

- P0 workflows remain integrated and secure, P1 analytics are evidence-based,
  and operational readiness limitations are documented; no unvalidated
  forecasting or autonomous emergency action is claimed.

## Current execution status

- The approved four-phase, role-spanning vertical-slice plan is documented
  above.
- Phase 1 implementation now includes SQLite persistence for locations and
  RiskPredictions, constrained one-role accounts, revocable cookie sessions,
  backend-derived roles, gated demo sign-in, admin account provisioning, and
  shared role-aware risk views.
- Phase 1 validation: backend unit tests, Python compilation, TypeScript
  production build, and HTTP smoke checks for auth/RBAC/risk access pass.
- Phase 2 implements citizen reporting, field verification and independent
  field reports, private evidence, admin review, and explicit-only
  FloodProblem approval. Citizen report responses use a public-safe schema that
  excludes internal verification and review details.
- Phase 3 implements admin response-task creation from approved FloodProblems,
  field assignment and lifecycle updates, admin completion review, and
  citizen-safe public status tracking scoped to the citizen's own report.
- Phase 3 validation: complete backend regression suite, frontend production
  build, authenticated HTTP lifecycle checks, browser checks of Admin, Field,
  and Citizen views, and `git diff --check` pass.
- Phase 4 adds historical prediction/observation summaries, distinct field
  outcomes, replay-model feature contribution explanations, public-safe
  citizen analytics, explicit replay/source snapshot labeling, and analytics
  and privacy regression tests. Comparisons use observations after the
  prediction window and do not treat unverified citizen submissions as
  outcomes. No model-accuracy metric is claimed.
- Phase 4 validation: all backend tests pass (33 tests), the frontend
  production build passes, analytics HTTP access/scoping is tested for all
  roles, browser validation covered the role-aware analytics UI, and
  `git diff --check` passes.
- Operational limitations remain: bundled replay/source timestamps are static,
  live weather/hydrology availability cannot be validated, no suitable
  evaluation dataset or methodology exists for model-performance claims, and
  production deployment/backup/monitoring have not been demonstrated.
- The bundled replay set contains one prediction snapshot per five locations
  and no historical field/verified outcomes in a clean database. The analytics
  UI therefore correctly shows empty observation/problem summaries until real
  records exist; correctness tests use isolated synthetic records and are not
  presented as observed flood history.
