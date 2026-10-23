# Decision Log

## Current implementation decisions

| Decision | Status |
| --- | --- |
| Use a Pune-focused flood-risk dashboard prototype | Implemented |
| Prioritize a simple operational dashboard over a production forecasting system | Implemented |
| Use local replay data for initial demonstration | Implemented |
| Limit risk categories to Low / Moderate / High / Critical | Implemented |
| Show data-source health for IMD, CWC, PMC, and GIS | Implemented |
| Treat outputs as demo/model outputs rather than official warnings | Implemented |
| Persist shared locations and risk predictions in local SQLite | Implemented for Phase 1 |
| Store exactly one role on each user account | Implemented for Phase 1 |
| Derive real-login role from the backend account | Implemented for Phase 1 |
| Gate role-selectable demo login behind explicit demo mode | Implemented for Phase 1 |
| Show missing or stale source state explicitly | Implemented |

## Deferred scope

The following items are intentionally not part of the current repository scope and should not be treated as implemented capabilities:

- live IMD, CWC, or PMC integrations
- real hydrological or meteorological model deployment
- production-grade GIS analysis
- automated response or emergency dispatch
- citizen report, field verification, and official problem workflows
- response tasks and public incident-status updates
- public alerting or autonomous emergency response

## Removed from active scope

Older, broader multi-hazard and platform-level concepts have been narrowed to the current demo dashboard scope. The repo does not claim end-to-end forecasting, live alerting, or operational control systems.
