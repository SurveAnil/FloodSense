# FloodSense

## Current project status

FloodSense is a Pune-focused urban flood-risk decision-support application. The
current implementation provides a shared, authenticated risk dashboard and a
human-reviewed report-to-official-problem workflow for three application
roles, using local replay/mock risk data.

This is not a production weather or hydrology system, and it does not claim to provide official alerts, emergency warnings, or a validated ML forecast.

## What the project does today

The app currently provides:

- a city-level risk summary for selected Pune locations
- a risk map and hotspot selection flow
- a priority hotspot list ranked by demo risk score
- a location detail view with rainfall context and risk drivers
- a source-status panel for live Open-Meteo weather freshness and replay-only
  IMD, CWC, PMC, and GIS labels
- account sign-in with backend-assigned roles: `CITIZEN`,
  `FIELD_RESPONSE_PLANNING`, and `DISASTER_MANAGEMENT_ADMIN`
- an admin-only account provisioning screen
- persisted local location and `RiskPrediction` records
- citizen flood reports with private owner-only tracking and optional evidence
- field verification records linked to citizen reports
- independent field inspections linked optionally to an AI prediction or
  citizen report, including “Inspected — No Problem Found”
- admin review of citizen and field evidence; only explicit approval creates a
  separate official `FloodProblem`
- admin response instructions and field-assigned `ResponseTask` lifecycle
- role-scoped prediction history and field-outcome analytics, with public-safe
  aggregates for citizens and no accuracy claims
- replay model input contributions and explicit replay/source-status labels
- live Open-Meteo current-weather freshness status, visible to every role
- interactive Leaflet risk map with OpenStreetMap street tiles, ArcGIS imagery
  and topographic basemaps, and
  independently toggleable authorized report/observation/problem layers and a
  separate demo-scenario-context layer

Risk values remain replay/demo outputs; the seven mentor-demo scenario scores
are supplied example values, not baseline-model predictions. Risk predictions,
demo context, reports, field observations, and official problems are distinct
records. Citizen reports and field findings never automatically become
official problems.

## Important scope boundaries

The current repo does not yet include:

- live IMD/CWC/PMC API integration
- official emergency alerts or dispatch workflows
- production ML model training or inference
- real GIS layers or operational map services
- rainfall/weather map overlays
- live monitoring, alerting, or automated CI/CD pipelines
- live IMD/CWC/PMC feeds or dynamically refreshed freshness for those sources
- a validated evaluation dataset or methodology for model-performance metrics

Deployment steps for a temporary Render API and Vercel mentor demo are in
[docs/deploy-render-vercel.md](./docs/deploy-render-vercel.md). The demo
deployment still uses replay data and ephemeral SQLite storage; it is not a
production service.

## Runtime

Install dependencies:

```bash
npm install
```

Run the backend locally (PowerShell):

```bash
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLOODSENSE_DEMO_MODE = "true"
uvicorn app.main:app --reload
```

For real account sign-in, provision an initial account from the trusted backend
environment. The role is assigned during account provisioning, never selected
on the real sign-in form:

```powershell
cd backend
python -m app.cli --email admin@example.org --role DISASTER_MANAGEMENT_ADMIN
```

Run the frontend in a second terminal:

```powershell
npm run dev
```

Build the frontend:

```bash
npm run build
npm run preview
```

Run the backend regression tests from `backend`:

```powershell
python -m unittest discover -s tests -v
```

## Data model and current implementation

The backend loads demo/replay data from:

- `backend/data/pune_replay.json`

On first startup, the backend initializes a local SQLite database at
`backend/data/floodsense.sqlite3` (override with `FLOODSENSE_DB_PATH`) and stores
the replay locations and risk predictions. Demo-account sign-in controls are
available only when `FLOODSENSE_DEMO_MODE=true`; the real email/password
authentication flow never accepts a role from the client. Set
`FLOODSENSE_COOKIE_SECURE=true` behind HTTPS in deployment. If the deployed
frontend and API are on different sites, use
`FLOODSENSE_COOKIE_SAMESITE=none` together with secure cookies and explicitly
allow the frontend origin. Keep the frontend and API on the same hostname for
the default local `SameSite=Lax` cookie behavior.

The active data mode is `replay`; risk values are illustrative model outputs,
not validated forecasts or official warnings.

The replay dataset also includes seven user-supplied mentor-demo scenarios
around Wakad, Hinjawadi, Punawale, Thergaon, and Maan. Their specified scores,
report-count aggregates, field summaries, and issue statuses are labeled as
demo context only; they are not imported as actual citizen submissions,
verified field reports, or approved FloodProblems.

Location detail cards and map popups include original vector illustrations for
all tracked locations. These are explicitly labeled as illustrative scenes,
not ground-truth photographs; replace the SVGs under
`public/images/locations/` with verified, licensed location photos when
available.

The street map uses the OpenStreetMap standard tile service with visible
attribution. That public service is subject to its tile usage policy and does
not provide a production availability guarantee; deployments with sustained or
high-volume map traffic should configure a compliant tile host/provider.
Satellite imagery and topographic tiles use ArcGIS basemap styles. Configure
`VITE_ARCGIS_API_KEY` in the frontend build environment (including local `.env`
when developing); Vite includes this key in browser code, so restrict its
ArcGIS privileges and allowed referrers to the deployed site domains. ArcGIS
credits are displayed in the map attribution control.

Live weather freshness is fetched from Open-Meteo for central Pune and cached
for up to five minutes. The status is based on the returned observation time;
provider errors and observations older than one hour are surfaced as
Unavailable or Stale. Replay risk scores and rainfall inputs remain separate
from the live weather freshness source and are not recalculated from it.

## Summary

FloodSense is being delivered feature-by-feature as integrated vertical slices.
The four-phase roadmap and acceptance criteria are in
[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md). It is not yet a live
operational forecasting or emergency-response system.
