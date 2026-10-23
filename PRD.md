# Product Requirements Document (PRD)

## Project scope for this repository

FloodSense is a Pune-focused urban flood-risk decision-support system. The
current implementation provides authenticated public, operational, and
command-level access to a shared replay-based risk and hotspot foundation.

## Document status

This PRD distinguishes the implemented Phase 1 risk/authentication slice from
the planned report, verification, review, and response slices. Replay model
outputs are not validated forecasts.

## Problem statement

Pune experiences localized flooding during intense rainfall. Broad rainfall warnings alone do not show which specific urban areas are most likely to suffer disruptive waterlogging or road-level disruption first.

The current project addresses that gap by combining rainfall context, historical hotspot signals, and a simple demo prioritization model into a dashboard for municipal decision support.

## Application roles

- `CITIZEN`
- `FIELD_RESPONSE_PLANNING`
- `DISASTER_MANAGEMENT_ADMIN`

Each account has exactly one role. The backend derives it from the authenticated
account; real sign-in does not accept a client-selected role.

## Core user needs

1. See the current city risk picture quickly.
2. Identify high-priority hotspots.
3. Understand the risk drivers for a selected location.
4. Check whether data sources are available, stale, or unavailable.
5. Use the result as decision support rather than as an official emergency warning.

## Implemented Phase 1 requirements

### Shared risk dashboard
- Show a summary of current risk states for selected Pune locations.
- Display categories: Low, Moderate, High, Critical.
- Include rainfall context and briefly explain how risk is being interpreted.
- Show source health for IMD, CWC, PMC, and GIS.
- Authenticate the three allowed application roles and show the same persisted
  location and RiskPrediction foundation with role-appropriate framing.
- Permit account role selection only through an explicitly marked demo-account
  flow while backend demo mode is enabled.

### Priority hotspot workflow
- Rank selected locations by risk score.
- Allow users to select a hotspot from the map or priority list.
- Keep selection state consistent across the overview and detail views.

### Location detail
- Show location name, area, score, and prediction time.
- Display current rainfall, forecast rainfall, and key drivers.
- Distinguish observed context from predicted/ranked risk.
- Mark historical hotspot status where relevant.

### Data transparency
- Clearly label risk outputs as demo outputs, not official alerts.
- Display source data freshness and outages.
- Avoid implying that missing data equals low risk.

## Explicit non-goals for this repository

The repository does not yet include:

- authoritative flood forecasting or emergency dispatch
- production ML deployment or model serving
- live integration with official weather and hydrology APIs
- citizen report submission and own-report tracking
- field verification or independent FieldReport creation
- admin review and official FloodProblem lifecycle
- ResponseTask assignment, field updates, and public incident status
- autonomous governance, dispatch, or emergency action

## Scope boundary

The current risk source is a local replay-based demo and prioritization
workflow. It does not replace IMD, CWC, PMC, or emergency response services.

## Acceptance criteria for the current Phase 1 slice

- A user can open the dashboard and understand the current risk picture.
- A user can select a hotspot from the map or priority list.
- A user can inspect the reasons behind a high or critical risk score.
- A user can see whether each source is available, stale, or unavailable.
- The interface clearly labels outputs as demo or replay data instead of official warnings.
- All three roles authenticate, and changing a role field in a real login
  request cannot change the role returned by the backend.
