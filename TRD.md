# Technical Requirements Document (TRD)

## Document status

This document reflects the current repository implementation and the approved
four-phase roadmap. The shared Phase 1 risk-intelligence and authentication
slice is implemented; Phases 2–4 remain planned.

## Purpose

The technical scope in this repo is limited to a decision-support interface that presents flood-risk prioritization for selected Pune locations.

## Current architecture

```text
React frontend
  -> authenticated role-aware application shell
  -> shared risk dashboard / hotspot priority list / location detail
  -> FastAPI session and risk APIs
  -> SQLite users, locations, risk predictions, data sources, audit log
  -> replay/mock provider adapter and demo baseline
```

## Implemented components

### Frontend
- React + Vite + TypeScript application
- dashboard, priorities, and status pages
- risk summary widgets and badge states
- map and detail interactions
- account sign-in and backend-derived role display
- demo-account sign-in controls gated by explicit backend demo mode
- admin account provisioning

### Data layer
- `backend/data/pune_replay.json` stores a replay snapshot
- SQLite persists location, RiskPrediction, account/session, source-status, and
  audit foundation records
- data mode is `replay`; predictions are illustrative and unvalidated

### Current UI requirements
- Display current risk across urban locations
- Show ranked priority hotspots
- Allow selection and focus across map/list/detail views
- Show state for IMD, CWC, PMC, and GIS sources
- Separate observed conditions from predicted risk scores

## Data source handling

The current source-status panel represents data availability for:

- IMD: rainfall and forecast context
- CWC: hydrological context
- PMC: historical hotspot information
- GIS: optional spatial context

These are status indicators only. They are not live production integrations, and no external API credentials or live service contracts are required for the demo.

## Authentication and role constraints

- There are exactly three roles: `CITIZEN`, `FIELD_RESPONSE_PLANNING`, and
  `DISASTER_MANAGEMENT_ADMIN`.
- Each user has one constrained `users.role`; there is no role mapping table.
- Real authentication takes email/password only. Role is retrieved from the
  authenticated account and cannot be selected by the user.
- Demo role selection is available only when `FLOODSENSE_DEMO_MODE=true` and
  resolves to backend-provisioned demo accounts.
- Create the first real account with `python -m app.cli --email <email>
  --role <allowed-role>` from the backend directory. Admins can provision
  additional accounts through the authenticated API/UI.
- Set `FLOODSENSE_COOKIE_SECURE=true` when serving over HTTPS and configure
  `FLOODSENSE_ALLOWED_ORIGINS` for the deployed frontend.

## Constraints and remaining scope

- No official weather, hydrology, or emergency API is called.
- The current prediction baseline is not a validated operational ML model.
- No scheduler or telemetry stack is required for the current repository state.
- Citizen reports, field reports/verifications, official FloodProblems, and
  ResponseTasks are separate planned vertical slices; none is implemented yet.

## Decision baseline for the current repo

| Topic | Current decision | Status |
| --- | --- | --- |
| Data mode | Replay/mock local dataset | Implemented |
| Risk categories | Low / Moderate / High / Critical | Implemented |
| Hotspot selection | Map and list interaction | Implemented |
| Source-status panel | Available / Stale / Unavailable | Implemented |
| Application roles | Exactly three, one per user | Implemented in Phase 1 slice |
| Authentication | Backend-issued HttpOnly session cookie | Implemented in Phase 1 slice |
| Risk/location persistence | SQLite shared location and prediction records | Implemented in Phase 1 slice |
| Live data integrations | Deferred | Not present |
| Validated ML model | Deferred | Not present |
| Production deployment | Deferred | Not part of current repo |

## Approved implementation plan

The exact feature priorities, dependencies, per-phase database/API/frontend
changes, RBAC, acceptance criteria, tests, and Definitions of Done are in
[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md). Delivery is vertical-slice
based across relevant roles, not role-by-role.
