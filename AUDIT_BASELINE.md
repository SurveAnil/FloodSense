# FloodSense Product and System Audit Baseline

**Audit date:** 2026-09-04  
**Repository state:** Conceptual/proposal stage; four Markdown documents; no application source, configuration, tests, deployment manifests, migrations, datasets, credentials, or CI files found.

## 1. Executive assessment

FloodSense has a strong and appropriately narrow product thesis: combine available Pune rainfall information, relevant hydrological context, historical waterlogging evidence, and accessible spatial data to estimate location-specific urban flood risk, rank locations, and support human response decisions through a GIS dashboard.

The PRD, TRD, Design brief, and Project Report are broadly consistent on hazard, geography, primary output, architecture direction, human-in-the-loop use, and explicit exclusions. They correctly avoid claiming official warnings, guaranteed prediction, or validated accuracy.

The project is **not ready to code the end-to-end product**. It is ready for a time-boxed discovery and data-feasibility phase. Coding against the current documents would require inventing the training label, spatial unit, forecast horizon, source contracts, thresholds, fallback behavior, and validation method. Those choices materially affect the data model, APIs, ML design, and UI.

The realistic semester/hackathon MVP is one reproducible retrospective or replayable pipeline:

`available source files/APIs -> validation -> aligned features -> interpretable baseline -> location risk -> ranking -> map/table/detail dashboard`

Live refresh, CWC/drainage enrichment, confidence, and event review must be capability-gated by actual data and access.

## 2. Documents read

- [PRD.md](C:/Users/Anil/Desktop/FloodSense/PRD.md): product scope, personas, stories, MVP, metrics, edge cases, exclusions.
- [TRD.md](C:/Users/Anil/Desktop/FloodSense/TRD.md): proposed stack, logical adapters, schemas, APIs, ML, database, NFRs, deployment, acceptance criteria, TBD register.
- [Design.md](C:/Users/Anil/Desktop/FloodSense/Design.md): flows, six views, components, states, accessibility, visual direction, design acceptance criteria.
- [Project_Report.md](C:/Users/Anil/Desktop/FloodSense/Project_Report.md): context, cited source landscape, feature/resource recommendations, semester boundary.

## 3. Consolidated product baseline

### A. Product objective

Turn fragmented Pune rainfall, forecast/nowcast, relevant hydrological, historical waterlogging, and accessible urban-spatial information into timely location-specific flood-risk intelligence that helps municipal and response users decide where human attention should go first.

### B. Problem statement

During extreme rainfall, broad weather information and static hotspot lists do not identify which Pune urban locations are most likely to experience disruptive waterlogging next. The product addresses the intelligence gap between hazard information and human operational prioritization. It does not replace IMD, CWC, PMC, official warnings, or emergency authority.

### C. Target users

**Primary:** municipal disaster-management officer and field-response/maintenance coordinator.  
**Secondary for MVP workflow:** traffic-management and emergency coordinators where their needs can be served by the same dashboard.  
**Future, not MVP:** citizens/public-alert recipients.

User decisions are prioritization, inspection, preparation, and contextual interpretation. The system must not autonomously dispatch, close roads, control pumps, order evacuation, or allocate funds.

### D. Primary user journey

1. Open Pune dashboard.
2. Check source health, freshness, and model status.
3. Review current/forecast rainfall context.
4. Inspect city risk map and accessible layers.
5. Identify high/critical locations.
6. Open a ranked location.
7. Review risk drivers, timestamps, data quality, and observed-versus-predicted distinction.
8. Use the ranking as human decision support.

### E. MVP capabilities

1. API and static-file adapters behind normalized internal contracts.
2. Record-level validation: timestamps, units, coordinates/geometry, duplicates, missingness, freshness, provenance.
3. Spatial and temporal alignment to one selected unit.
4. Training/evaluation dataset construction from available event evidence.
5. Interpretable baseline and empirical candidate comparison where data support it.
6. Location risk score/category with visible limitations and explanation.
7. Ranked priorities with deterministic tie/ordering behavior.
8. GIS map, accessible priority table, location detail, rainfall context, and source status.
9. Replay/retrospective demonstration if live feeds are unavailable.

The four user-facing categories remain **Low, Moderate, High, Critical**. They are model output labels, not official emergency declarations. “Alert” in source material means an in-dashboard warning state unless separately approved.

### F. Future/deferred capabilities

Citizen app and official alerts; SMS/WhatsApp; incident entry and field-team status; road closure integration; response tracking; automated retraining; satellite/CCTV; hydrodynamic simulation; deep temporal models; demographic/health modelling; autonomous resource optimization; multi-city or multi-hazard expansion.

Historical/event review is **MVP-basic only if event-level data exist**; otherwise it is a deferred validation view, not a fabricated feature.

### G. System architecture

External adapters (IMD, CWC where relevant, PMC hotspot, accessible GIS/supporting data) -> ingestion and provenance -> validation/quality status -> spatial/temporal alignment -> feature generation -> offline training/evaluation artifact -> prediction service -> prioritization -> React GIS dashboard -> human decision.

Keep training separate from serving. A scheduled or manual replay is sufficient for the prototype; do not assume event-driven live orchestration until source refresh behavior is verified.

### H. Data-source contracts

Every adapter contract must specify, for the actual source:

- access method, authentication, terms, rate limits, update cadence, outage behavior;
- raw payload version/hash or file identity where retention is permitted;
- source timestamp, ingestion timestamp, validity interval, timezone;
- location representation and CRS;
- measurement/category semantics and canonical units;
- schema/version, nullability, duplicate identity, quality flags;
- coverage, historical depth, and known bias/limitations.

Sources:

- **IMD:** observations, forecast, nowcast, warnings; exact endpoint/schema/access is TBD.
- **CWC:** hydrological context only where spatially and operationally relevant; fields and Pune coverage are TBD.
- **PMC:** hotspot locations and, if obtainable, event date/time/severity/duration; hotspot list alone is not a supervised label.
- **PMC GIS/supporting GIS:** only accessible, machine-readable layers; inventory, license, CRS, resolution, and update date are TBD.

### I. Internal data models

Use stable identifiers and explicit optionality. Minimum conceptual records:

- `DataSourceStatus`: source, capability, status, last success, observed timestamp, error/quality summary.
- `Location`: location id, name, selected spatial-unit type, geometry, CRS, ward/road fields if available.
- `RainfallObservation`: source, location, observation time, value/unit, provenance, quality.
- `RainfallForecast`: issue time, validity interval, location, value/unit/category, provenance, quality.
- `RainfallNowcast`: issue/validity interval, location, intensity/severity, provenance, quality.
- `HydrologicalObservation`: source, location, observation time, available values/units/status.
- `HotspotEvidence`: source record id, location, source date, historical indicator, event fields if present, provenance.
- `SpatialFeature`: layer/type, geometry/attributes, source/version/timestamp, quality.
- `FeatureSnapshot`: location/time, feature values, missingness/quality indicators, source references.
- `ModelRun/ModelArtifact`: version, training data snapshot, feature schema/version, code/config identity, evaluation results.
- `RiskPrediction`: location/time/horizon, score/category, model version, input snapshot references, explanation/uncertainty status, quality.
- `PriorityRanking`: run id, rank, prediction reference, ordering/filter context, generated time.

### J. Database entities

PostgreSQL + PostGIS is the approved direction. Tables proposed by the TRD (`data_sources`, rainfall observations/forecasts/nowcasts, hydrological observations, `flood_hotspots`, `spatial_features`, `risk_predictions`, `priority_rankings`) require a shared `locations`/spatial-unit entity, model-run/input-snapshot provenance, schema/version fields, and constraints before implementation.

The schema must prevent ambiguous geometry, duplicate observations, invalid time intervals, orphan predictions, and rankings assembled from mixed prediction runs. Raw payload retention and audit retention remain TBD and must respect source terms.

### K. API contracts

The TRD endpoints are logical placeholders, not committed public contracts:

- `GET /api/data/status`
- `GET /api/rainfall/current`
- `GET /api/rainfall/forecast`
- `GET /api/rainfall/nowcast`
- `GET /api/hydrology`
- `GET /api/hotspots`
- `GET /api/gis/layers`
- `POST /api/predictions/generate`
- `GET /api/predictions`
- `GET /api/predictions/{location_id}`
- `GET /api/priorities`
- `GET /api/map/risk`
- `GET /api/map/hotspots`

Before coding, define request/response schemas, pagination/limits, temporal semantics, geometry format, ordering/ties, error codes, stale/partial response shape, idempotency, authentication boundary, and whether generation is synchronous or job-based. Do not expose unavailable layers as available.

### L. ML pipeline

1. Acquire and document data.
2. Profile coverage, leakage, missingness, and spatial/temporal resolution.
3. Define the spatial unit, forecast horizon, event window, target label, and negative examples.
4. Build leakage-safe time/event-based training data.
5. Establish a transparent rule/simple or logistic baseline.
6. Compare Random Forest/XGBoost only if justified by data and validation.
7. Calibrate probabilities if a probability is presented.
8. Select category thresholds using validation and operational cost trade-offs.
9. Generate explanations compatible with the selected model.
10. Package a versioned artifact and immutable feature schema.
11. Serve predictions with input provenance and quality caveats.
12. Evaluate retrospectively and report uncertainty, false positives, false negatives, and lead time where measurable.

Do not fabricate labels from the PMC hotspot list. A hotspot prior may be a feature, but it is not proof that flooding occurred at a time window.

### M. UI/screen requirements

Desktop-first React experience with usable tablet behavior:

- Dashboard: current city risk, map, high/critical priority panel, rainfall context, freshness/model status.
- Risk Map: available layers only, legend, predicted versus historical visual distinction, selectable location drawer.
- Priority Hotspots: deterministic ranked table, severity/ward/status filters only when data exist, map focus on selection.
- Location Detail: risk category/score, applicable time/horizon, prediction/data timestamps, drivers, rainfall context, historical indicator, spatial-data availability, caveat.
- Data Status: source capability, available/stale/unavailable/error, last successful update, quality message.
- Historical/Event Review: only data-backed retrospective comparison; otherwise explicit unavailable state.

All screens require loading, partial loading, empty, stale, unavailable, prediction-failure, and retry states. Risk cannot be represented by color alone; map results need a table/non-map alternative; keyboard, focus, screen-reader labels, contrast, and clear observed/predicted language are required.

### N. Error/state handling

Never map missing data to zero or Low risk. Preserve source-specific values and disagreement flags. A source failure should degrade only dependent capabilities where possible. Required-input failure yields “prediction unavailable” or an explicitly qualified result according to a policy decided after feature selection. Show last successful update and what the limitation means.

### O. Security requirements

Keep credentials and non-public data out of source control, client bundles, logs, and error messages. Use environment/secret management appropriate to the chosen deployment. Define authentication and authorization before operational use; protect ingestion/admin/model endpoints. Apply least privilege, input validation, dependency/update hygiene, and backup/access policy if persistent deployment is used.

### P. Non-functional requirements

Prototype-scale responsiveness, reproducible runs, deterministic ranking, explicit freshness, fault isolation, auditability, accessibility, and no unsupported precision claims. Numerical latency, capacity, availability, retention, and recovery targets are TBD and must be benchmarked rather than invented.

### Q. Testing requirements

Required test layers:

- unit tests for normalization, units, timezone handling, geometry/CRS, validation, deduplication, freshness, feature calculations, thresholds, explanations, ranking ties;
- adapter contract fixtures and malformed/partial payload tests;
- database migration/constraint and spatial-query tests;
- ML data-leakage checks, time-based evaluation, baseline reproducibility, calibration/threshold tests;
- API schema/error/state tests;
- frontend interaction/accessibility tests for map/table/detail/status;
- end-to-end replay from known input snapshot to rendered ranking;
- performance smoke test and failure-injection test;
- documented retrospective evaluation report.

### R. Deployment requirements

Development -> validation/test -> prototype deployment environments. React -> FastAPI -> Python processing/model -> PostgreSQL/PostGIS is the approved conceptual topology. Cloud provider, containerization, orchestration, versions, domain/TLS, backups, migrations, scheduled jobs, and cost controls are TBD. A single-host or university deployment should be preferred for the prototype unless evidence requires more.

### S. Monitoring requirements

At minimum record ingestion attempts/results, source freshness, validation failures, prediction runs, model/version, API failures, latency, and dashboard-visible status. Alerting/monitoring tooling is TBD. Logs must exclude secrets and protected data. Provide a run identifier that connects source snapshots, feature generation, model execution, predictions, and ranking.

### T. Known TBDs

Prediction horizon; spatial unit/precision; target label and event window; historical event availability; final feature set; CWC relevance/fields; actual upstream contracts and access; GIS layer inventory/CRS; canonical units/timezone; source-specific freshness thresholds; fallback policy; final model/hyperparameters; score semantics and thresholds; uncertainty/confidence method; explanation method; raw/audit retention; API schemas and generation mode; authentication/authorization; deployment provider/packaging; capacity/latency/recovery targets; monitoring tooling; icon/map library; mobile support level.

For each TBD, the decision owner must record purpose, dependencies, evidence required, decision date, chosen option, rejected alternatives, and effect on requirements. Until then it must remain visibly `TBD - Decision required`.

### U. Risks and dependencies

The dominant dependencies are data access, historical event labels, spatial/temporal mismatch, source quality/freshness, institutional permissions, map licensing/tiles, and validation feasibility. Product risks are false confidence, unsupported hyperlocal claims, confusing historical evidence with current prediction, and a dashboard that appears authoritative despite missing inputs. Technical risks are leakage, class imbalance, sparse events, unstable thresholds, brittle adapters, and overbuilding infrastructure.

## 4. Full gap analysis and priorities

### P0 - resolve before product implementation

| Area | Gap | Why it matters | Evidence/decision required |
| --- | --- | --- | --- |
| Product/MVP | No go/no-go definition for live versus retrospective/replayable MVP. | Prevents building APIs/UI around unavailable feeds. | Inventory access and choose a demo mode. |
| Data contracts | No verified IMD, CWC, PMC, or GIS endpoint/file contract, terms, coverage, cadence, or historical depth. | Adapters, schema, and feasibility depend on reality. | Test access or obtain representative files and document contracts. |
| ML label | No operational definition of disruptive flooding, event window, negatives, severity, or observation source. | Without labels there is no valid supervised model or KPI. | Obtain event-level observations and approve label protocol; otherwise explicitly use a non-supervised baseline/demo. |
| Spatial unit | Hotspot, grid, ward, road, and “hyperlocal” are all mentioned. | Changes joins, labels, map semantics, schema, and claims. | Profile source resolution and approve one unit. |
| Forecast horizon | No minutes/hours or valid-time semantics. | Determines features, labels, UI wording, and lead-time KPI. | Compare forecast/nowcast cadence with event timestamps and approve horizon(s). |
| Validation | No split strategy, event de-duplication, leakage policy, minimum sample rule, or acceptance gate. | Random splits can inflate performance and undermine trust. | Approve time/event/geographic validation protocol and report format. |
| Data fallback | “Reduced confidence or withhold” is unresolved. | A failure can otherwise become a misleading safe result. | Define required versus optional features and fallback matrix after profiling. |
| Prediction semantics | Score/probability/severity and four thresholds are not defined. | UI/API/database cannot safely represent them. | Select score meaning, calibration policy, and validation-based thresholds. |
| Source-to-location alignment | No method for station/grid/river/hotspot matching or spatial uncertainty. | Can create false street-level precision and invalid features. | Document join method, resolution, CRS, and uncertainty. |
| Scope contradiction | Alert generation and historical review are inconsistently called MVP/basic/future. | Causes uncontrolled delivery scope and official-alert implications. | Approve the narrow MVP boundary in this baseline. |

### P1 - resolve during MVP implementation

| Area | Gap |
| --- | --- |
| Personas | No permissions, workflow ownership, or field/traffic-specific acceptance criteria. |
| User flows | No refresh/retry behavior, filter persistence, time selection, map/table synchronization details, or export/share need. |
| Requirements traceability | No mapping from each user story to API, model output, UI state, and test. |
| Data quality | No canonical units/timezone, duplicate key, null policy, outlier rules, source precedence, conflict threshold, or quality score. |
| Historical data | No event schema, source reliability hierarchy, intervention-change handling, or censoring/negative sampling plan. |
| Features | No exact aggregation windows, antecedent-rain definition, feature leakage checks, or missing-feature strategy. |
| Model | No baseline definition, imbalance handling, calibration, threshold selection, drift/OOD method, or reproducibility artifact. |
| Explainability | No definition of “driver,” contribution format, caveat, or unavailable explanation behavior. |
| Database | No `locations`, model runs, feature snapshots, provenance join, constraints, indexes, migration, or retention implementation. |
| APIs | Placeholder schemas omit units, validity intervals, quality, source provenance, geometry, pagination, and error envelopes. |
| Reliability | No retry/backoff/rate-limit/cache/idempotency policy or partial-run semantics. |
| UI | No map provider/tiles, geometry format, layer inventory behavior, responsive breakpoints, or accessibility test plan. |
| Security | No secret handling, auth boundary, roles, CORS, rate limiting, or privacy/data license handling. |
| QA | No fixtures, acceptance test cases, replay dataset, browser matrix, or performance baseline. |
| Operations | No run identifiers, structured logs, health checks, alert thresholds, backup/restore, or incident procedure. |

### P2 - resolve after MVP

Retention duration; richer CWC/drainage enrichment; incident entry; prediction-versus-observation analytics; road-risk specialization; field-team status; user research with additional departments; quantified capacity and SLOs; production auth hardening; formal model registry; automated scheduled ingestion if live access proves useful.

### P3 - future/optional

Citizen product, official notifications, multilingual public safety, satellite/CCTV, hydrodynamic/deep-learning models, digital twin, multi-hazard expansion, autonomous resource optimization, multi-city rollout.

## 5. Contradictions and inconsistencies

| Conflict | Why it matters | Recommended resolution | Approval status |
| --- | --- | --- | --- |
| PRD/TRD describe six MVP capabilities; Project Report adds “Alert generation” as a seventh core feature. | “Alert” can imply official emergency infrastructure and expands scope. | Treat dashboard warnings/status as part of decision support; defer public/official alert delivery. | Supported by PRD exclusions/TRD boundary; document wording should be aligned. |
| Design lists “Historical / Event Review” as MVP/basic; PRD places prediction-versus-observation analysis in Phase 2, while US-05 requests observations. | Requires event data and storage not otherwise guaranteed. | Keep only a data-backed basic retrospective view; otherwise defer. | Partly supported by Design caveat; team must approve MVP acceptance. |
| PRD secondary users include citizens; Design primary-user list includes traffic/emergency teams but not citizens; all documents exclude citizen MVP. | Could create conflicting UX/security/communication expectations. | Citizens are future users, not an MVP persona or acceptance target. | Supported by PRD future persona and exclusions. |
| PRD calls output “hyperlocal” and Project Report asks for exact/near-exact locations; TRD leaves spatial unit/resolution TBD and Design warns against street precision. | Unsupported precision is a safety and trust risk. | Use “selected geographic unit/location” until resolution is evidenced; reserve hyperlocal claim. | Requires explicit product sign-off; Design is the safer wording. |
| TRD marks XGBoost as a decided candidate while final algorithm is TBD; Project Report repeatedly recommends XGBoost. | Teams may implement XGBoost before establishing a valid baseline. | Logistic/simple baseline first; XGBoost remains a candidate, not a promise. | Supported by PRD/TRD model-selection language. |
| Project Report says event-driven real-time refresh is technically suitable; all documents say access/reliability/cadence are unverified. | Real-time behavior may be impossible or misleading in a demo. | Make replay/manual refresh the default until live contracts are verified. | Requires MVP mode decision; no source supports a live guarantee. |
| TRD says PostgreSQL + PostGIS is decided, while deployment/provider/versions remain TBD. | A database choice still needs local/dev/test provisioning and migration strategy. | Preserve PostGIS direction; defer hosting/packaging decisions, not schema design. | No contradiction after distinguishing component from hosting. |
| Risk categories include “High -> Prioritize / Alert,” while official alerting is out of scope. | UI copy could imply authority or certainty. | Use “prioritize attention” and “dashboard warning”; never imply official alert. | Supported by PRD/TRD exclusions. |

## 6. Implementation realism

### Realistic

React + FastAPI + Python tabular ML + PostgreSQL/PostGIS is technically appropriate, explainable, and feasible if reduced to one reproducible pipeline and a small set of locations/units. Static fixtures and replay are valid contingency modes, not evidence of live capability.

### Over-scoped or dependency-heavy

Simultaneous IMD/CWC/PMC/GIS live adapters; city-wide high-resolution mapping; drainage-network feature engineering; event-level historical analytics; confidence/OOD detection; six screens; real-time orchestration; production authentication; and operational monitoring are too much before feasibility is proven. Deep learning, hydrodynamics, CCTV, citizen alerts, resource optimization, and multi-hazard work must remain excluded.

### Simplifications that preserve the core

Start with one verified rainfall source plus one historical evidence source and one documented spatial unit. Use static GIS/base tiles if permitted. Implement manual/replay ingestion before scheduling. Use logistic regression or a transparent score baseline before XGBoost. Serve one current prediction snapshot and one deterministic priority list. Make CWC/drainage optional capability flags. Build the accessible table alongside the map, not after it.

### Hard stop conditions

If no defensible event-level label exists, do not present a trained flood predictor as validated. If source resolution cannot support the selected unit, reduce the claim and aggregate. If permissions/terms prohibit use, remove that source and show unavailable. If validation sample size is insufficient, label results exploratory and keep thresholds provisional.

## 7. Dependency-aware coding plan (after P0 approval)

1. Confirm MVP mode, data access, terms, owners, and decision log.
2. Create repository structure, environment conventions, dependency lock/version policy, and configuration/secrets policy.
3. Obtain representative source samples and write adapter/data contracts.
4. Decide spatial unit, CRS, timezone, canonical units, horizon, event window, target label, and fallback matrix.
5. Establish PostgreSQL/PostGIS migrations, shared locations, provenance, quality, model-run, prediction, and ranking entities.
6. Implement source adapters for verified sources, fixture/replay adapters, raw/normalized separation, and ingestion run records.
7. Implement validation, deduplication, normalization, freshness, conflict, and spatial/temporal alignment.
8. Build leakage-safe historical training dataset and data-quality report.
9. Implement reproducible simple baseline and evaluation protocol.
10. Compare candidate model(s), calibrate if appropriate, select thresholds, and package versioned artifact/explanations.
11. Implement prediction and deterministic prioritization services with provenance and partial-data states.
12. Finalize versioned API schemas and error envelopes; add contract tests.
13. Build React shell, status/freshness, map, accessible priority table, detail drawer, rainfall context, and all required states.
14. Integrate map/table/detail selection and source capability flags.
15. Run replay end-to-end, verify failure injection, accessibility, and performance smoke tests.
16. Produce retrospective evaluation and demo evidence; explicitly label limitations.
17. Select prototype deployment environment, package, migrate, secure, and add health/logging/run observability.
18. Reassess deferred features only after MVP acceptance.

## 8. Files to create or modify

### Created by this audit

- `AUDIT_BASELINE.md` (this source-of-truth audit and baseline).

### Required before implementation

- `DECISIONS.md` or equivalent decision register with owners/dates/status.
- `DATA_CONTRACTS.md` containing verified source contracts and licenses.
- `DATA_DICTIONARY.md` containing canonical fields, units, timezone, CRS, quality, and identifiers.
- `VALIDATION_PROTOCOL.md` containing label, horizon, spatial unit, leakage controls, splits, metrics, and acceptance gates.
- `TRACEABILITY.md` mapping PRD stories/design criteria/TRD acceptance criteria to tests and implementation.
- `README.md` with setup, safe configuration, replay/demo workflow, limitations, and no-data behavior.
- Machine-readable schemas, migrations, fixtures, tests, and deployment configuration once the corresponding P0 decisions are approved.

### Existing documents to align after approval

- [PRD.md](C:/Users/Anil/Desktop/FloodSense/PRD.md): resolve MVP alert/event-review wording and avoid unsupported hyperlocal/alert language.
- [TRD.md](C:/Users/Anil/Desktop/FloodSense/TRD.md): replace placeholder API/schema sections with approved contracts; retain unresolved items explicitly.
- [Design.md](C:/Users/Anil/Desktop/FloodSense/Design.md): align historical review scope, capability-gated layers, and operational copy.
- [Project_Report.md](C:/Users/Anil/Desktop/FloodSense/Project_Report.md): distinguish recommended possibilities from approved MVP requirements and live capability.

No application code should be created until the P0 decisions and evidence are recorded.

## 9. READY TO CODE checklist

- [ ] MVP mode (live, replay, or both) and demo acceptance scenario approved.
- [ ] At least one usable rainfall input and one historical flood-evidence input obtained, with permission/terms recorded.
- [ ] Actual source schemas, cadence, coverage, outage behavior, and provenance requirements documented.
- [ ] Defensible target label, event window, negative examples, prediction horizon, and validation split approved.
- [ ] One spatial unit, precision claim, spatial join method, CRS, and timezone approved.
- [ ] Required versus optional features and source-failure fallback policy approved.
- [ ] Score semantics, probability/calibration policy, category thresholds, uncertainty/explanation behavior approved.
- [ ] Shared location/provenance/model-run schema and migration plan approved.
- [ ] API request/response/error contracts and generation/refresh semantics approved.
- [ ] Map/tiles/licensing choice and available-layer capability model approved.
- [ ] Security boundary, secret handling, access roles, and data-retention policy appropriate to the prototype documented.
- [ ] Unit, adapter, ML leakage, API, UI/accessibility, end-to-end replay, and failure-injection test plan ready.
- [ ] Prototype performance/capacity targets and deployment environment selected or explicitly marked non-production.
- [ ] Logging, run identifiers, freshness monitoring, backup/recovery expectations, and demo limitation language prepared.
- [ ] PRD, TRD, Design, and Project Report wording is internally consistent.

**Readiness result:** **NOT READY TO CODE** until all unchecked P0 items are resolved. The next action is evidence collection and decision approval, not feature implementation.
