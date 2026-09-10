# Design Brief

## AI-Based Urban Flood Risk Forecasting & Hotspot Prioritization System — Pune

**Design status:** Product-design specification for MVP
**Primary users:** Municipal disaster-management officers, field-response/maintenance teams, traffic-management teams, emergency coordinators
**Primary task:** Understand where urban flooding is most likely during extreme rainfall and decide where attention should be prioritized
**Primary experience:** GIS decision-support dashboard
**Design principle:** **From rainfall information to location-specific risk to response priority**

This brief translates the PRD and TRD into a concrete UX/UI direction. It does **not** introduce new product capabilities beyond those documents. The original proposal establishes GIS-based risk visualization, location-specific risk, prioritization, dashboards and actionable response as the intended direction. 

---

# 1. Design Principles

The product should feel like an **operational decision tool**, not a generic smart-city dashboard.

### 1.1 Answer the four questions immediately

Every primary screen should help the user answer:

**Where?**
Which locations are currently at risk?

**How serious?**
What is the current risk level?

**Why?**
What factors are driving that risk?

**What needs attention first?**
Which hotspots should be prioritized?

### 1.2 Map first, explanation second

The geographic relationship between rainfall, hotspots and predicted risk is central to the product. The map is therefore the main workspace, with tables and detail panels supporting it.

### 1.3 Separate prediction from observation

The interface must visually distinguish:

* **predicted risk**
* **historical hotspot**
* **observed/current rainfall**
* **source/data status**

A historical hotspot must never visually look like proof that flooding is happening now.

### 1.4 Risk is not certainty

“High” and “Critical” represent model-generated risk states, not guaranteed flooding or official emergency declarations.

### 1.5 Operational clarity over visual decoration

Avoid:

* excessive cards;
* large decorative statistics;
* unnecessary gradients;
* overly dense dashboards;
* animated map effects that compete with alerts.

This is a decision-support product. Nobody needs a weather dashboard designed like a cryptocurrency exchange.

---

# 2. Primary User Flows

## Flow 1 — Check current city-wide flood risk

**User:** Disaster-management officer

```text
Open Dashboard
      ↓
Check Data Status
      ↓
Review Current Rainfall / Forecast
      ↓
View Pune Risk Map
      ↓
Identify High / Critical Areas
      ↓
Open Hotspot Details
      ↓
Review Risk Drivers
```

### Design objective

The user should understand the current situation within seconds without navigating through multiple pages.

### Key interaction

Clicking a high-risk map region should open the corresponding location detail panel without taking the user away from the map.

---

# 3. Flow 2 — Find the highest-priority hotspots

```text
Dashboard
   ↓
Priority List
   ↓
Sort/Filter by Risk
   ↓
Select Top-Ranked Location
   ↓
View Risk Drivers
   ↓
View Location on Map
```

### Design objective

Turn model output into an operationally useful ordered list.

### Key interaction

Selecting a ranked hotspot should:

1. highlight it in the list;
2. focus the map on the location;
3. open its detail panel.

This creates a continuous relationship between **ranking ↔ map ↔ explanation**.

---

# 4. Flow 3 — Inspect one location

```text
Risk Map
   ↓
Select Hotspot
   ↓
Location Detail
   ↓
Review:
  Risk
  Rainfall
  Historical Status
  Spatial Factors
  Prediction Time
  Data Freshness
   ↓
Return to Map
```

### Design objective

Give the user enough context to understand the prediction without overwhelming them with ML terminology.

---

# 5. Flow 4 — Investigate a rainfall event

```text
Dashboard
   ↓
Rainfall / Forecast View
   ↓
Review Current + Forecast Conditions
   ↓
Compare with Flood-Risk Map
   ↓
Identify affected hotspots
   ↓
Open Priority List
```

The product should visually connect weather conditions to predicted urban consequences.

---

# 6. Flow 5 — Check system/data health

```text
Dashboard
   ↓
Data Status
   ↓
Review:
  IMD
  CWC
  PMC
  GIS
   ↓
Identify stale/unavailable source
   ↓
Interpret predictions accordingly
```

This is especially important because the TRD explicitly requires data freshness and source status to be visible.

---

# 7. Flow 6 — Handle missing or stale data

```text
New Data Expected
      ↓
Source unavailable / stale
      ↓
System marks source status
      ↓
Prediction affected?
      ↓
Display clear warning
      ↓
User continues with qualified information
```

The interface should never silently transform “data unavailable” into “risk low.”

---

# 8. Screen Inventory

The MVP can be implemented with **six primary views**.

| Screen                       | Purpose                                   | Priority  |
| ---------------------------- | ----------------------------------------- | --------- |
| 1. Flood Risk Dashboard      | Main operational workspace                | MVP       |
| 2. Risk Map                  | Spatial analysis                          | MVP       |
| 3. Priority Hotspots         | Ranked locations                          | MVP       |
| 4. Location Detail           | Explain an individual prediction          | MVP       |
| 5. Data Status               | Show source health/freshness              | MVP       |
| 6. Historical / Event Review | Inspect prediction and historical context | MVP/basic |

No separate citizen application, public emergency alert center, resource-dispatch system or unrelated hazard dashboards should appear in the MVP.

---

# 9. Screen 1 — Flood Risk Dashboard

## Purpose

The primary entry point and highest-priority operational screen.

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Header                                                       │
│ Product Name | Pune | Data Status | Last Updated            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Risk Summary Bar                                             │
│ Low | Moderate | High | Critical                            │
│                                                              │
├───────────────────────────────┬──────────────────────────────┤
│                               │                              │
│                               │   Priority Hotspots          │
│                               │   1. Location A             │
│        PUNE RISK MAP          │   2. Location B             │
│                               │   3. Location C             │
│                               │                              │
│                               │   View All                  │
│                               │                              │
├───────────────────────────────┴──────────────────────────────┤
│                                                              │
│ Rainfall / Forecast Context                                  │
│ Current | Forecast | Nowcast | Timestamp                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Header

Contains:

* product name;
* Pune geographic scope;
* current data-health indicator;
* latest update timestamp.

### Risk Summary

Four compact states:

* Low
* Moderate
* High
* Critical

These should be interactive filters rather than decorative KPI cards.

### Main map

Occupies the majority of the viewport.

### Priority panel

Displays the most important high/critical locations.

Each row contains:

* rank;
* location;
* risk;
* timestamp.

### Rainfall context

Shows the current/forecast rainfall information supporting the current situation.

---

# 10. Screen 2 — Risk Map

## Purpose

Detailed spatial exploration.

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Header                                                       │
├───────────────┬──────────────────────────────────────────────┤
│ Map Controls  │                                              │
│               │                                              │
│ Risk          │                                              │
│ Hotspots      │                 PUNE MAP                    │
│ Rainfall      │                                              │
│ GIS Layers    │                                              │
│               │                                  ┌─────────┐ │
│ Legend        │                                  │ Legend  │ │
│               │                                  └─────────┘ │
├───────────────┴──────────────────────────────────────────────┤
│ Selected Location Detail Drawer                              │
└──────────────────────────────────────────────────────────────┘
```

### Left control rail

Controls:

* risk layer;
* historical hotspots;
* rainfall information;
* available GIS layers.

Do not show unavailable layers as if they exist.

### Map

Primary interactive workspace.

### Map legend

Clearly defines:

* Low;
* Moderate;
* High;
* Critical;
* historical hotspot;
* other enabled layers.

### Detail drawer

Clicking a location opens a right/bottom detail panel rather than routing immediately to a new screen.

This allows users to preserve geographical context.

---

# 11. Screen 3 — Priority Hotspots

## Purpose

Answer:

> **Where should attention be prioritized first?**

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Page Header                                                  │
│ Priority Hotspots | Updated [timestamp]                     │
├──────────────────────────────────────────────────────────────┤
│ Filters                                                      │
│ Risk | Area/Ward if available | Status                      │
├──────┬────────────────────┬──────────┬──────────┬────────────┤
│ Rank │ Location           │ Risk     │ Score    │ Updated    │
├──────┼────────────────────┼──────────┼──────────┼────────────┤
│  1   │ Hotspot A          │ Critical │   ...    │ ...        │
│  2   │ Hotspot B          │ High     │   ...    │ ...        │
│  3   │ Hotspot C          │ High     │   ...    │ ...        │
└──────┴────────────────────┴──────────┴──────────┴────────────┘
```

### Table design

Risk should be visually dominant.

Users should be able to:

* scan rankings;
* open a location;
* see the corresponding map position.

### Important restraint

Do not create an elaborate “resource allocation optimizer” here. The PRD requires **prioritization**, not autonomous allocation.

---

# 12. Screen 4 — Location Detail

## Purpose

Explain a single risk prediction.

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ ← Back                         Location Name                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│             CRITICAL                                        │
│          Risk Score: XX                                    │
│                                                              │
│ Prediction generated: [timestamp]                           │
│ Data updated: [timestamp]                                   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ RISK DRIVERS                                                 │
│                                                              │
│ ● Rainfall forecast             High                         │
│ ● Recent rainfall accumulation  High                         │
│ ● Historical hotspot            Yes                          │
│ ● Spatial/drainage context      Available / unavailable     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ RAINFALL CONTEXT                                             │
│                                                              │
│ Current | Forecast | Nowcast                                │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ LOCATION                                                     │
│                                                              │
│ Mini-map / geographic context                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Information hierarchy

1. Risk state
2. Location
3. Prediction timestamp
4. Risk drivers
5. Rainfall context
6. Spatial context

---

# 13. Screen 5 — Data Status

## Purpose

Show whether the information supporting the model is current and available.

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Data Status                                                  │
├───────────┬────────────┬─────────────────┬──────────────────┤
│ Source    │ Status     │ Last Updated    │ Data Type        │
├───────────┼────────────┼─────────────────┼──────────────────┤
│ IMD       │ Available  │ [timestamp]     │ Rainfall         │
│ CWC       │ Available  │ [timestamp]     │ Hydrology        │
│ PMC       │ Available  │ [timestamp]     │ Hotspots         │
│ GIS       │ Unavailable│ —               │ Spatial          │
└───────────┴────────────┴─────────────────┴──────────────────┘
```

### Status hierarchy

Use text plus icon/state:

* Available
* Stale
* Unavailable

Do not rely on color alone.

---

# 14. Screen 6 — Historical / Event Review

## Purpose

Provide contextual review of previous predictions and observed/historical flood information where such data are available.

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Event / Historical Review                                   │
├──────────────────────────┬───────────────────────────────────┤
│ Event / Date Filter      │ Event Summary                     │
├──────────────────────────┴───────────────────────────────────┤
│                                                              │
│                     Historical Map                           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Prediction vs Historical/Observed Information                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Because the TRD does not yet guarantee event-level historical data, this screen should begin as a **basic validation/review interface** and only expose information actually available.

---

# 15. Responsive Layout Strategy

The primary deployment context is expected to be desktop-oriented operational use.

### Desktop

**Recommended composition:**

* persistent top header;
* large central map;
* secondary side panel;
* tables/detail drawers.

### Tablet

* map remains primary;
* priority panel becomes collapsible.

### Mobile

No separate mobile feature set is required by the PRD.

The UI should remain usable for viewing basic risk information, but full operational workflows are primarily designed around desktop/tablet use.

---

# 16. Reusable Component List

## Global Components

### `AppHeader`

Contains:

* product identity;
* location/context;
* system state;
* timestamp.

### `PageTitle`

Consistent page heading with supporting metadata.

### `StatusBadge`

Used for:

* Available;
* Stale;
* Unavailable;
* risk states.

### `TimestampLabel`

Displays:

* data timestamp;
* prediction timestamp;
* last update.

---

## Risk Components

### `RiskBadge`

Four defined states:

* Low;
* Moderate;
* High;
* Critical.

### `RiskLegend`

Map legend for risk categories.

### `RiskSummary`

Compact aggregate status display.

### `RiskScore`

Displays numerical model score where available.

### `RiskDriverList`

Shows major factors contributing to the prediction.

### `PriorityRank`

Visual rank indicator for hotspot lists.

---

# 17. Mapping Components

### `RiskMap`

Primary geographic visualization.

### `MapLayerControl`

Enables available layers.

### `MapLegend`

Defines symbols and risk categories.

### `MapLocationMarker`

Represents a location/hotspot.

### `LocationPopup`

Quick summary after selecting a map feature.

### `LocationDrawer`

Expanded location information without losing map context.

### `MapLoadingState`

Used when spatial data are loading.

---

# 18. Data Components

### `DataSourceCard`

Displays source status.

### `DataSourceTable`

Displays all available source-health information.

### `DataFreshnessIndicator`

Shows current/stale/unavailable state.

### `WeatherSummary`

Presents rainfall and forecast context.

### `NowcastSummary`

Presents current nowcast information where available.

---

# 19. Table Components

### `PriorityTable`

Core ranked hotspot table.

### `TableRow`

Reusable location result.

### `TableFilter`

Controls filtering.

### `SortControl`

Controls ordering.

### `Pagination`

Use only where dataset size requires it; exact implementation is not prescribed by the PRD.

---

# 20. Feedback Components

### `Toast`

For non-blocking system messages.

### `InlineAlert`

For important contextual warnings.

### `ErrorState`

For failed operations.

### `EmptyState`

For unavailable/no-data situations.

### `LoadingState`

For asynchronous data/model operations.

---

# 21. Design Tokens

The PRD/TRD do not prescribe a visual identity or exact color system. The following is therefore a **proposed design system for implementation**, not a claim inherited from the PRD.

The token system should prioritize risk communication, accessibility and operational clarity.

---

# 22. Color Palette

## Base Colors

| Token                  | Suggested use                |
| ---------------------- | ---------------------------- |
| `background-primary`   | Main application background  |
| `background-secondary` | Panels and secondary regions |
| `surface`              | Cards, drawers, tables       |
| `border`               | Dividers and boundaries      |
| `text-primary`         | Main content                 |
| `text-secondary`       | Supporting information       |
| `text-muted`           | Metadata                     |

Use neutral surfaces so risk information remains visually dominant.

---

## Risk Colors

The product already defines four risk levels, so the visual system should map those levels consistently:

| Risk     | Suggested visual treatment |
| -------- | -------------------------- |
| Low      | Green                      |
| Moderate | Yellow/amber               |
| High     | Orange                     |
| Critical | Red                        |

Do not rely exclusively on color; pair each with:

* text label;
* icon;
* map symbol/pattern where appropriate.

This follows the original product concept's four-level risk structure. 

---

# 23. Typography

A clean sans-serif UI typeface should be used consistently.

### Recommended type scale

| Token     |  Size | Use                       |
| --------- | ----: | ------------------------- |
| `display` | 32 px | Major page state          |
| `h1`      | 24 px | Page heading              |
| `h2`      | 20 px | Section heading           |
| `h3`      | 16 px | Component heading         |
| `body-lg` | 16 px | Important supporting text |
| `body`    | 14 px | Default UI                |
| `body-sm` | 13 px | Secondary information     |
| `caption` | 12 px | Metadata/timestamps       |

### Type weight

* Regular: body text
* Medium: labels
* Semibold: headings and important values
* Bold: critical risk state only when appropriate

Avoid excessive bolding. A dashboard where everything is shouting has technically achieved maximum volume and minimum hierarchy.

---

# 24. Spacing

Use a consistent 4 px base spacing system:

```text
4 px   — micro spacing
8 px   — icon/text spacing
12 px  — compact component spacing
16 px  — standard padding
24 px  — section spacing
32 px  — major separation
48 px  — page-level spacing
```

### Component padding

Standard cards/panels:

**16–24 px**

Major screen sections:

**24–32 px**

---

# 25. Radius

Use restrained geometry:

| Token       | Radius |
| ----------- | -----: |
| `radius-sm` |   4 px |
| `radius-md` |   8 px |
| `radius-lg` |  12 px |

Risk indicators and map controls should not be excessively rounded.

The visual language should communicate **professional municipal tooling**, not consumer social media.

---

# 26. Elevation

Use subtle elevation only for:

* floating map controls;
* drawers;
* active panels;
* modal dialogs.

Avoid heavy shadows throughout the interface.

---

# 27. Icons

Icons should supplement labels rather than replace them.

Recommended semantic icons:

* rainfall/cloud;
* warning;
* map pin;
* location;
* data source;
* clock;
* information;
* refresh;
* error;
* visibility/layer.

The exact icon library is not specified by the PRD/TRD and should be selected during implementation.

---

# 28. Interface States

State management is particularly important because this system depends on external data.

## 28.1 Initial Loading

```text
Loading flood-risk information…
```

Show:

* skeleton map region;
* skeleton priority rows;
* clear loading indicator.

Avoid blank screens.

---

# 29. Partial Loading

Example:

**Map available**
**CWC data loading**

The rest of the interface should remain usable.

Display a local status message instead of blocking the entire application.

---

# 30. Empty State — No Risk Predictions

Message:

> **No flood-risk predictions are currently available.**

Supporting text:

> Prediction data may not yet be generated or required input data may be unavailable.

Action:

* View data status

Do not display “No risk detected.”

That distinction is operationally essential.

---

# 31. Empty State — No Hotspots

Message:

> **No hotspot records are available for this view.**

Possible reason:

* selected filter;
* unavailable PMC data;
* no matching records.

---

# 32. Stale Data State

Example:

> **IMD data may be stale. Last successful update: [timestamp].**

The risk map remains visible but the warning should remain prominent enough to affect interpretation.

---

# 33. Error State

### Full data failure

> **Flood-risk data could not be loaded.**

Supporting text:

> Check source availability and try again.

Action:

**Retry**

### Individual source failure

> **PMC hotspot data unavailable.**

The source-specific failure should not automatically make unrelated data disappear.

---

# 34. Prediction Failure

Message:

> **Risk prediction unavailable for this location.**

Supporting text:

> Required input data are missing or the prediction could not be generated.

The interface should provide the prediction status without inventing a risk category.

---

# 35. Success State

For non-destructive operations:

> **Risk information updated successfully.**

For new prediction processing:

> **Risk predictions updated.**

Keep confirmation subtle; users should not receive celebratory confetti because a database query succeeded.

---

# 36. Warning State

Warnings should be used for materially important situations:

> **Prediction based on incomplete data**

or:

> **Some source data are stale. Interpret current risk with caution.**

Warnings should explain **what is wrong and why it matters**.

---

# 37. Accessibility Requirements

## 37.1 Color Independence

Risk must never be represented solely through red/yellow/orange/green.

Every risk state should include:

* text label;
* icon or distinct marker;
* optional pattern/shape difference.

Example:

**● LOW**
**▲ MODERATE**
**◆ HIGH**
**■ CRITICAL**

The exact symbol set may be finalized by the design team.

---

# 38. Contrast

Text and interactive elements must maintain sufficient contrast against their background.

Risk colors should also remain distinguishable when rendered in:

* low-quality displays;
* grayscale;
* bright outdoor conditions.

---

# 39. Keyboard Navigation

All important controls must be keyboard accessible:

* map controls;
* filters;
* tables;
* drawers;
* close buttons;
* retry controls.

Focus states must be clearly visible.

---

# 40. Screen Readers

Meaningful labels should exist for:

* risk level;
* map locations;
* data source states;
* timestamps;
* buttons;
* filters.

Avoid exposing raw GIS coordinates as the only description of a location.

---

# 41. Map Accessibility

Interactive maps are inherently challenging for screen-reader users.

Therefore, every important map result should also appear in a non-map representation such as:

**Priority Hotspots table**

This ensures the core decision task does not depend exclusively on visual spatial interaction.

---

# 42. Motion

Animations should be:

* minimal;
* functional;
* short.

Avoid animated rainfall effects, moving markers or continuously changing visual elements that could distract users during high-pressure operational use.

---

# 43. Language and Comprehension

The MVP should use straightforward operational language.

Prefer:

> **High flood risk**

over:

> **ML inference probability threshold exceeded**

Technical information can appear in secondary detail views.

---

# 44. Key UX Rules for Risk Communication

### Rule 1

Always show **what time the prediction applies to**.

### Rule 2

Always show **when the underlying data were last updated**.

### Rule 3

Always distinguish **observed** from **predicted**.

### Rule 4

Never imply that:

**High Risk = certain flooding**

### Rule 5

Never imply:

**Data unavailable = Low Risk**

---

# 45. Recommended Information Hierarchy

Across the product, the hierarchy should be:

```text
1. CURRENT FLOOD RISK
        ↓
2. LOCATION
        ↓
3. PRIORITY
        ↓
4. WHY THE LOCATION IS HIGH RISK
        ↓
5. RAINFALL / FORECAST CONTEXT
        ↓
6. DATA FRESHNESS
        ↓
7. TECHNICAL DETAILS
```

This makes the system usable by non-ML decision-makers while preserving technical transparency.

---

# 46. Component-to-Screen Mapping

| Component           | Dashboard | Risk Map | Priority | Location | Data Status |
| ------------------- | :-------: | :------: | :------: | :------: | :---------: |
| App Header          |     ✓     |     ✓    |     ✓    |     ✓    |      ✓      |
| Risk Summary        |     ✓     |     ✓    |     —    |     ✓    |      —      |
| Risk Map            |     ✓     |     ✓    |     —    |     ✓    |      —      |
| Priority Table      |     ✓     |     —    |     ✓    |     —    |      —      |
| Location Drawer     |     ✓     |     ✓    |     —    |     —    |      —      |
| Risk Drivers        |     —     |     ✓    |     —    |     ✓    |      —      |
| Rainfall Summary    |     ✓     |     ✓    |     —    |     ✓    |      —      |
| Data Status         |     ✓     |     ✓    |     —    |     ✓    |      ✓      |
| Timestamp           |     ✓     |     ✓    |     ✓    |     ✓    |      ✓      |
| Risk Legend         |     ✓     |     ✓    |     —    |     —    |      —      |
| Error/Loading State |     ✓     |     ✓    |     ✓    |     ✓    |      ✓      |

---

# 47. Design-to-Development Handoff Guidance

Each screen should be specified using:

**Component**
What it is.

**Data source**
Which backend/API data it consumes.

**State**
Loading / available / stale / unavailable / error.

**Interaction**
What happens when the user clicks, filters or selects it.

**Accessibility**
Keyboard, contrast, labels and non-map alternatives.

Example:

### Priority Hotspot Row

**Data:** `location_id`, `risk_score`, `risk_category`, `prediction_time`

**Visual hierarchy:**
Rank → Location → Risk → Timestamp

**Click:**
Open location detail and focus corresponding map location.

**Unavailable data:**
Show missing information explicitly.

This format should be used consistently in the design-to-development handoff.

---

# 48. MVP Design Acceptance Criteria

The design is ready for implementation when:

### Dashboard

* A user can identify the current city-wide risk state immediately.
* High/critical locations are visible without navigating deeply.
* Current/forecast rainfall context is visible.
* Data freshness is clear.

### Map

* Users can distinguish risk levels.
* Historical hotspots are distinguishable from current predictions.
* Selecting a location reveals its risk details.
* Map data are supported by an equivalent accessible non-map representation.

### Priority List

* Locations can be scanned in risk order.
* High/critical hotspots are visually clear.
* Selecting an item connects it to its geographic location.

### Location Detail

* Risk state is prominent.
* Prediction timestamp is visible.
* Major risk drivers are understandable.
* Observed versus predicted information is clearly differentiated.

### Data Status

* IMD, CWC, PMC and GIS status can be displayed where those sources are part of the implementation.
* Stale/unavailable states are visible.
* No-data conditions are not interpreted as safe conditions.

---

# 49. Final Design Direction

The product should visually communicate one simple progression:

```text
RAIN
  ↓
WHERE IS RISK INCREASING?
  ↓
WHICH HOTSPOTS COME FIRST?
  ↓
WHY?
  ↓
WHERE SHOULD HUMAN ATTENTION GO?
```

The map is the **spatial workspace**.
The priority list is the **decision queue**.
The location detail is the **explanation layer**.
The data-status view is the **trust layer**.

That structure directly supports the PRD's central product proposition: turning fragmented environmental information into location-specific flood-risk intelligence and prioritization. The original project concept already frames this broader transition as moving from prediction through impact assessment toward actionable response. 

The most important design decision is therefore not adding more screens. It is keeping the product focused enough that, during an extreme-rainfall event, a municipal user can open the system and understand **where the risk is, why it is there, and which locations deserve attention first** within a few interactions.
