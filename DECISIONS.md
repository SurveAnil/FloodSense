# Version 2 decisions

## 2026-09-11

| Decision | Default | Reasoning | Revisit when |
| --- | --- | --- | --- |
| Development data mode | Versioned local replay snapshot | No verified provider credentials/contracts are present; reproducible local tests are safer than invented live integrations. | IMD/CWC/PMC access and schemas are confirmed. |
| API shape | `GET /api/dashboard`, `/api/data/status`, `/api/locations/{id}`, `/api/priorities` | Matches the existing frontend service output and keeps the Phase 1 UI boundary stable. | Real API pagination or job semantics require expansion. |
| Prediction spatial unit | Selected named locations from replay data | The audit left grid/ward/road/hotspot unresolved; named locations avoid claiming unsupported street-level precision. | Verified geometry and event coverage support another unit. |
| Prediction horizon | `10 Sep 2026, 15:00-18:00 IST` replay window | The audit left horizon TBD; a visible three-hour window makes the demo semantics explicit without claiming a production horizon. | Source cadence and event timestamps are analyzed. |
| Baseline model | Logistic regression with deterministic replay feature rows | Required baseline from the TRD; interpretable and light enough for local development. | Validated historical labels justify candidate comparison. |
| Risk thresholds | Low <35, Moderate 35-54, High 55-74, Critical >=75 | Temporary, monotonic demo thresholds that preserve four UI states. | Calibrated validation data and operational cost analysis are available. |
| Missing optional GIS | Preserve `Unavailable`; do not impute safety | Existing product rule says missing data must not become low risk. | GIS contract and feature dependency are verified. |

## Provider integration note

IMD, CWC, and PMC adapter contracts are represented by the replay boundary only. No credentials, endpoint behavior, or live response schema has been invented.
