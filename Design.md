# Design Brief

## Product type

Authenticated risk-intelligence workspace for Pune, shared by public, field
planning, and command users.

## Design goal

Translate rainfall context and hotspot information into a simple, useful risk-prioritization view for municipal response teams.

## Primary experience

The interface should answer four questions immediately:

1. Where is risk the highest?
2. How serious is it?
3. Why is a location flagged?
4. What should receive attention first?

## Core screens

### 0. Sign-in and role-aware shell

- Real email/password sign-in; the backend supplies the account role.
- Development/demo account shortcuts appear only when demo mode is enabled.
- The three allowed roles share the same underlying risk and location records.

### 1. Flood risk dashboard

Primary overview with:
- city risk summary
- map view
- hotspot priority list
- rainfall context banner

### 2. Priority hotspots

Ordered list of the top-ranked locations.

### 3. Location detail

Expanded detail for a selected hotspot with:
- current rainfall
- forecast rainfall
- prediction time
- risk drivers
- historical hotspot status

### 4. Data status

Shows whether data sources are available, stale, or unavailable.

## Interaction model

- Selecting a hotspot updates the detail panel and highlight state.
- Map and list selection remain aligned.
- Missing or stale data is communicated explicitly rather than hidden.
- All risk labels are presented as demo outputs rather than official warnings.

## Visual guidance

- Clear risk colors for Low, Moderate, High, and Critical.
- Operational dashboard styling rather than generic analytics-heavy decoration.
- Keep the path from overview to hotspot detail short and direct.

## Out of scope for the current design

- citizen report and public incident-status workflows (planned Phase 2/3)
- automated emergency response workflows
- multi-hazard dashboards
- live GIS tiles or external map services
- validated forecasting and operational model claims
