# Product Requirements Document (PRD)

## AI-Based Urban Flood Risk Forecasting & Hotspot Prioritization System — Pune, Maharashtra

**Document status:** Proposal / Concept Stage
**Product stage:** Pre-MVP
**Primary hazard:** Urban flooding caused by extreme rainfall
**Target geography:** Pune, Maharashtra
**Primary product output:** Location-specific urban flood-risk prediction and hotspot prioritization
**Primary users:** Municipal disaster-management and field-response teams
**Secondary users:** Traffic management, drainage/maintenance teams, emergency coordinators, and citizens

---

## 0. Product Context and Scoping Assumptions

The original project proposal was designed as a broad, multi-hazard climate-resilience platform covering flood, heatwave and cyclone prediction, vulnerability analysis, health-risk assessment, resource prioritization, GIS, alerts and continuous learning. 

For this PRD, that scope is deliberately narrowed to a single operational problem:

> **Predict where extreme rainfall is most likely to cause disruptive urban flooding in Pune, rank those locations by risk, and provide actionable information to response teams.**

The product is **not intended to replace IMD, CWC, PMC or existing warning systems**. Its role is to function as an intelligence layer that combines available information and converts it into localized urban flood-risk intelligence.

The project is currently conceptual. The existing proposal explicitly states that final technology/model choices depend on dataset availability and that the demonstrated flood scenario is conceptual and requires validation against real-world datasets.  

### Key product questions considered before defining the PRD

The requirements below are based on four decisions:

| Product question                        | PRD decision                                                        |
| --------------------------------------- | ------------------------------------------------------------------- |
| What problem should anchor the product? | Urban flooding caused by extreme rainfall in Pune                   |
| Who needs the product most?             | Authorities and field-response teams making time-critical decisions |
| What is the primary AI output?          | Hyperlocal flood-risk score and hotspot priority                    |
| What can realistically be built first?  | Data ingestion → prediction → prioritization → GIS dashboard        |

The most important product constraint is therefore **depth over breadth**. The MVP must prove one useful prediction-and-decision workflow rather than demonstrate six disconnected AI capabilities.

---

# 1. Problem Statement

## 1.1 Core Problem

During intense rainfall, Pune can experience localized urban flooding and waterlogging that disrupt roads, mobility, drainage systems, public services and access to critical locations.

The operational challenge is not simply determining whether heavy rain is occurring. Decision-makers need to answer a more specific question:

> **Which parts of Pune are most likely to experience disruptive flooding, given the current and forecast rainfall and the characteristics of the urban environment?**

The current project concept identifies a gap between hazard detection and actionable response: conventional systems provide weather/hazard information, while the proposed product aims to connect that information to vulnerability, location and response decisions. 

## 1.2 Product Opportunity

Pune already has potentially valuable information distributed across different sources:

* rainfall and forecast information;
* nowcast/weather information;
* hydrological/flood information;
* historical waterlogging locations;
* GIS and drainage information where accessible.

The problem is that these sources may exist as separate information streams rather than as one dynamic decision layer.

The product therefore focuses on:

**Data → Risk intelligence → Location prioritization → Action**

rather than attempting to create new weather forecasting infrastructure.

## 1.3 Why the Problem Matters

Urban flooding creates several simultaneous operational consequences:

* road and traffic disruption;
* interruption of daily movement;
* difficulty accessing homes, schools and workplaces;
* reduced accessibility for emergency vehicles;
* pressure on drainage and municipal response teams;
* increased difficulty deciding which locations deserve immediate attention.

A useful flood-management product must therefore be evaluated not only by model performance but by whether it improves **decision timing and prioritization**.

---

# 2. Target Users

## 2.1 Primary Persona — Municipal Disaster Management Officer

**Role:** Coordinates flood preparedness and response.

**Primary need:** A city-level operational view showing where flood risk is increasing and where intervention should happen first.

**Pain points:**

* Multiple information sources must be monitored.
* Weather warnings may cover a broad geographical area.
* Historical hotspot information may not reflect current conditions.
* During an event, many locations compete for attention.
* Decision-making time is limited.

**Product value:** A single risk map and ranked hotspot list.

### Typical task

> “Heavy rainfall is forecast. Which locations should my teams monitor or prepare first?”

---

## 2.2 Secondary Persona — Field Response / Municipal Maintenance Team

**Role:** Performs on-ground inspections, drainage response and mitigation.

**Needs:**

* exact or near-exact location of priority areas;
* current risk level;
* reason for the risk;
* recommended response priority.

**Pain points:**

* Cannot inspect every vulnerable location simultaneously.
* Historical problem locations may differ from today's highest-risk locations.
* Field teams need information that is quickly understandable.

**Product value:** A ranked operational task list rather than a complex analytical dashboard.

---

## 2.3 Secondary Persona — Traffic Management Team

**Role:** Manages traffic and road safety during severe rainfall.

**Needs:**

* identification of roads likely to become waterlogged;
* early awareness of high-risk corridors;
* map-based visibility of affected areas.

**Pain points:**

* waterlogging can rapidly create congestion;
* traffic impacts may cascade beyond the original flood location;
* weather information alone does not indicate specific road-level disruption.

**Product value:** Early visibility of locations requiring traffic intervention.

---

## 2.4 Secondary Persona — Emergency Coordinator

**Role:** Coordinates multiple municipal or emergency response activities.

**Needs:**

* high-level risk summary;
* priority locations;
* severity trends;
* status of response actions.

**Product value:** Rapid situational awareness.

---

## 2.5 Future Persona — Citizens

Citizens are a potential future user group for simplified alerts and safety information.

However, the citizen experience should **not be the primary MVP**. The current project's strongest value proposition is institutional decision support, while direct public alerting introduces additional reliability, liability, accessibility and communication requirements.

---

# 3. User Stories

## 3.1 Disaster Management

**US-01 — View current risk**

> As a disaster-management officer, I want to see the current flood-risk level across Pune so that I can quickly understand which areas require attention.

**Acceptance criteria:**

* Map displays defined geographic units.
* Each location has a risk category.
* Risk status is timestamped.
* User can identify high- and critical-risk locations quickly.

---

**US-02 — Understand why a location is high risk**

> As a disaster-management officer, I want to see the factors contributing to a location's risk so that I can trust and interpret the prediction.

**Acceptance criteria:**

* Risk detail displays key contributing variables.
* The system distinguishes observed versus forecast information.
* Risk explanation is understandable without ML expertise.

---

**US-03 — Prioritize response**

> As a response coordinator, I want a ranked list of high-risk locations so that limited teams can be assigned to the most critical areas first.

**Acceptance criteria:**

* Locations are ranked by risk.
* Ranking can be filtered by severity.
* Each entry provides location and relevant risk information.
* Ranking refreshes when new prediction data are processed.

---

## 3.2 Field Response

**US-04 — Find priority hotspot**

> As a field-response team member, I want to identify the nearest priority hotspot so that my team can be directed where intervention is likely to be most valuable.

**Acceptance criteria:**

* Priority locations are displayed geographically.
* Location details are available.
* Risk state is clearly visible.

---

**US-05 — Verify changing conditions**

> As a field-response coordinator, I want to compare predicted risk with reported/observed incidents so that the system can be checked against what is actually happening.

**Acceptance criteria:**

* Observations can be recorded or imported where available.
* Predicted and observed states are distinguishable.
* Historical events can be reviewed.

---

## 3.3 Traffic Management

**US-06 — Identify road-risk locations**

> As a traffic operator, I want to see predicted waterlogging hotspots affecting important roads so that traffic-control measures can be considered before disruption becomes severe.

---

## 3.4 System Administration / Data Operations

**US-07 — Monitor data health**

> As a system administrator, I want to know when a data source is unavailable, stale or incomplete so that users do not mistake missing data for safe conditions.

This is particularly important because the current project does not yet have fully committed datasets or guaranteed real-time access.

---

# 4. Core Features

## 4.1 MVP Scope

The MVP should contain **six core capabilities**.

### MVP-1. Multi-Source Data Ingestion

The system should support ingestion of:

* IMD rainfall observations;
* IMD rainfall forecast/nowcast information;
* CWC flood/hydrological information where relevant;
* PMC-published waterlogging hotspot data;
* PMC GIS/drainage data if access is obtained;
* supporting geographic/terrain datasets where required.

The architecture should permit both API-based and static-file ingestion.

**Requirement:** Every data record must retain its source and timestamp.

---

### MVP-2. Data Validation and Standardization

The platform should:

* normalize timestamps;
* standardize units;
* validate coordinates;
* detect missing values;
* flag stale data;
* prevent duplicated observations;
* associate data with the chosen geographic units.

**Why this matters:** A risk score based on stale or mismatched data can be more dangerous than displaying no prediction at all.

---

### MVP-3. Urban Flood-Risk Prediction

The core AI component should estimate the probability or severity category of urban flooding for each defined location.

Conceptually:

**Rainfall conditions + historical flood information + spatial context → Flood-risk score**

Potential model families include:

* logistic regression baseline;
* Random Forest;
* XGBoost;
* another interpretable tabular model selected after dataset evaluation.

The existing proposal already identifies XGBoost, LSTM and PyTorch among candidate technologies, while explicitly avoiding accuracy claims until data analysis is completed. 

For the MVP, **an interpretable tabular model should be preferred over deep learning unless the available dataset clearly justifies a more complex architecture**.

---

### MVP-4. Dynamic Risk Map

A GIS dashboard should display:

* Pune geographic area;
* flood-risk zones;
* historical flood hotspots;
* rainfall state;
* risk severity;
* relevant infrastructure layers where available.

The existing proposal already includes a GIS risk map with low, moderate, high and critical categories. 

Recommended risk states:

| Level    | Meaning                        | MVP response implication     |
| -------- | ------------------------------ | ---------------------------- |
| Low      | Limited predicted flood risk   | Monitor                      |
| Moderate | Elevated risk                  | Prepare                      |
| High     | Significant probability/impact | Prioritize inspection        |
| Critical | Severe predicted risk          | Immediate response attention |

These labels should describe **model output**, not represent official emergency declarations.

---

### MVP-5. Hotspot Prioritization

The system should create a ranked list of locations based on predicted flood risk.

Each hotspot record should include:

* location;
* risk score;
* risk category;
* current/forecast rainfall;
* historical flood indicator;
* relevant geographic/drainage factors;
* prediction timestamp;
* model confidence/uncertainty where feasible.

This is the **central operational feature** of the product.

---

### MVP-6. Decision-Support Dashboard

The dashboard should answer four questions immediately:

**Where?**
Which locations are at risk?

**How serious?**
What is the predicted risk level?

**Why?**
Which variables are driving the prediction?

**What should happen next?**
Which locations deserve response attention first?

The dashboard should avoid becoming a generic “smart city” dashboard. Its interface should be optimized for flood-event decision making.

---

# 4.2 MVP Non-Functional Requirements

### Reliability

The system should clearly indicate:

* data freshness;
* unavailable sources;
* model status;
* last successful update.

### Explainability

The system should provide basic explanations for risk scores.

A black-box statement such as **“Risk = 87%”** is insufficient for a government decision-support product.

### Performance

Dashboard interactions should remain responsive under expected prototype-scale load.

### Auditability

Every prediction should ideally be traceable to:

* model version;
* input timestamp;
* data sources;
* prediction timestamp.

### Security

The prototype should protect:

* API credentials;
* administrative access;
* any non-public datasets;
* user authentication information.

---

# 4.3 Future Iterations

These features can be added after the MVP is validated.

### Phase 2 — Operational Intelligence

* real-time incident reporting;
* field-team status;
* historical prediction-versus-observation analysis;
* road-risk prioritization;
* response tracking;
* improved drainage intelligence.

### Phase 3 — Public Safety

* citizen-facing flood-risk view;
* location-based notifications;
* travel advisories;
* simplified multilingual alerts;
* accessibility improvements.

### Phase 4 — Advanced Prediction

* higher-resolution spatial modelling;
* satellite-derived flood indicators;
* CCTV/computer-vision integration;
* hydrodynamic modelling;
* advanced temporal/deep-learning models.

### Phase 5 — Advanced Resource Optimization

The original proposal includes AI-assisted allocation of emergency teams, supplies and shelters. 

This should become a later optimization module rather than an MVP requirement.

---

# 5. Success Metrics

Metrics should be divided into **model performance**, **product performance** and **operational usefulness**.

## 5.1 Model KPIs

Because datasets have not yet been committed, target values should be treated as **acceptance goals to be finalized after a baseline is established**, not promises.

### Prediction quality

Measure:

* Precision
* Recall
* F1-score
* ROC-AUC where appropriate
* PR-AUC for imbalanced flood-event data
* calibration of predicted probabilities

### Most important metric

For disaster-response prioritization, **recall for genuinely high-risk locations** should be emphasized over raw overall accuracy.

A model that achieves 95% accuracy by declaring almost everything “safe” would be a spectacular achievement only if the objective were to impress PowerPoint.

---

## 5.2 Spatial Prioritization KPI

Measure:

> **Top-K hotspot capture rate**

Example:

> Among the top 20 locations predicted by the system, how many actually experienced waterlogging?

This metric closely aligns model performance with the actual product use case.

---

## 5.3 Lead-Time KPI

Measure:

> How much earlier does the system identify a high-risk location before observed flooding/waterlogging?

This should become a major KPI once historical event timestamps are available.

---

## 5.4 Data Quality KPIs

Track:

* percentage of successful data updates;
* percentage of records with valid timestamps;
* percentage of records with valid geographic information;
* data freshness;
* API failure rate.

---

## 5.5 Product KPIs

For a pilot deployment:

* time required to identify highest-risk locations;
* number of clicks/actions required to reach hotspot information;
* percentage of users who correctly interpret risk categories;
* dashboard response time;
* percentage of predictions successfully generated after new data arrive.

---

## 5.6 Operational KPIs

During a real or retrospective simulation:

* percentage of observed hotspots detected;
* percentage of high-priority hotspots ranked in Top-K;
* false-alarm rate;
* average lead time;
* percentage of response recommendations acted upon.

The project should **not claim reductions in flood damage, casualties or economic loss during the academic prototype stage**, because those outcomes require real deployment and controlled evaluation.

---

# 6. Edge Cases

## 6.1 Missing IMD Data

**Scenario:** API unavailable or rainfall observation delayed.

**Expected behavior:**

* system marks the source as unavailable/stale;
* prediction confidence is reduced or prediction withheld;
* dashboard clearly displays data status.

The system must never silently interpret missing rainfall data as zero rainfall.

---

## 6.2 Conflicting Data Sources

**Scenario:** rainfall, hydrological and municipal information indicate different conditions.

**Expected behavior:**

* retain source-specific values;
* do not arbitrarily overwrite one source;
* apply documented precedence/validation rules;
* flag the disagreement when material.

---

## 6.3 New Flood Location Not in Historical Hotspot List

**Scenario:** A location that has never previously appeared on the PMC hotspot list becomes waterlogged.

**Expected behavior:**

* model must be able to assign risk based on current rainfall and spatial factors;
* system should not be dependent entirely on historical labels.

This is a critical product requirement. A pure “hotspot database” would simply reproduce yesterday's failures.

---

## 6.4 Historical Hotspot No Longer Vulnerable

**Scenario:** Drainage infrastructure is improved at a previously problematic location.

**Expected behavior:**

* historical hotspot status remains as historical context;
* current prediction can differ from historical risk;
* model should not permanently classify an area as high risk merely because it flooded in the past.

---

## 6.5 Extreme Rainfall Beyond Historical Training Data

**Scenario:** Rainfall intensity substantially exceeds what the model has seen historically.

**Expected behavior:**

* identify out-of-distribution conditions where possible;
* reduce confidence;
* clearly warn users that model reliability may be lower.

---

## 6.6 Rapidly Changing Weather

**Scenario:** Rainfall intensity changes significantly within a short period.

**Expected behavior:**

* prediction should refresh when new valid data arrive;
* old predictions must remain timestamped;
* the dashboard should show when the current forecast was generated.

---

## 6.7 Spatial Resolution Mismatch

**Scenario:** Weather data is available at a broader geographic scale than the hotspot locations.

**Expected behavior:**

* clearly distinguish measured resolution from modelled localization;
* avoid implying street-level precision unsupported by the data.

This is especially important for stakeholder trust.

---

## 6.8 Drainage GIS Unavailable

**Scenario:** PMC does not provide current machine-readable drainage data.

**Expected behavior:**

* MVP must still operate using rainfall, historical hotspot and alternative spatial datasets;
* missing drainage layers should reduce feature richness, not block the entire product.

This requirement protects the team from making institutional data access a single point of failure.

---

## 6.9 False Positive

**Scenario:** System predicts high risk but flooding does not occur.

**Expected behavior:**

* prediction should be logged;
* event should contribute to evaluation;
* users should not interpret every high-risk prediction as confirmation that flooding is certain.

---

## 6.10 False Negative

**Scenario:** Flooding occurs where the model predicted low risk.

**Expected behavior:**

* incident should be recorded;
* root cause should be examined;
* the event becomes a candidate for model retraining or feature improvement.

---

# 7. Out-of-Scope

The following are explicitly excluded from the MVP.

## 7.1 Other Climate Hazards

No:

* heatwave prediction;
* drought prediction;
* cyclone prediction;
* multi-hazard risk engine.

Although the original concept includes floods, heatwaves and cyclones,  the narrowed product addresses only urban flooding.

---

## 7.2 National Weather Forecasting

The system will **consume meteorological information rather than attempt to replace IMD's forecasting capability**.

---

## 7.3 Full Hydrodynamic City Simulation

The MVP will not attempt to simulate every:

* drain;
* nalla;
* culvert;
* pipe;
* water-flow path;
* street-level water depth.

Such a system would require significantly more engineering, hydraulic data and validation than is appropriate for the initial project.

---

## 7.4 Medical and Climate-Health Prediction

The original proposal includes climate-health risk assessment. 

This is excluded because it introduces a separate modelling domain, additional health datasets and substantially higher validation requirements.

---

## 7.5 Broad Population Vulnerability Modelling

Demographic vulnerability scoring may be useful later, but it is not required for the first version.

---

## 7.6 Autonomous Resource Dispatch

The product may **recommend priorities**, but it will not autonomously:

* dispatch emergency vehicles;
* control pumps;
* close roads;
* order evacuations;
* allocate public funds.

Human decision-makers remain responsible for operational action.

---

## 7.7 Full Citizen Emergency Alert Infrastructure

The MVP will not claim to operate as an official emergency-warning authority.

Citizen-facing alerts can be developed later after the prediction system itself is validated.

---

## 7.8 Guaranteed Flood Prediction

The system will provide **risk estimates**, not deterministic claims such as:

> “This road will definitely flood at 6:30 PM.”

This distinction must remain explicit throughout the product and pitch.

---

# 8. Product Architecture at MVP Level

The recommended product architecture is intentionally simple:

```text
                 DATA SOURCES
 ┌─────────────────────────────────────────┐
 │ IMD Rainfall / Forecast / Nowcast       │
 │ CWC Hydrological / Flood Information    │
 │ PMC Waterlogging Hotspots               │
 │ PMC GIS / Drainage (if accessible)      │
 │ Supporting Terrain / Spatial Data      │
 └────────────────────┬────────────────────┘
                      ↓
          DATA INGESTION & VALIDATION
                      ↓
          SPATIO-TEMPORAL FEATURE ENGINE
                      ↓
            AI FLOOD-RISK MODEL
                      ↓
             RISK SCORE / CLASS
                      ↓
          HOTSPOT PRIORITIZATION
                      ↓
             GIS DECISION DASHBOARD
                      ↓
        HUMAN DECISION & RESPONSE
```

This is consistent with the team's existing architecture concept, which separates data sources, an AI climate engine and a decision/feedback layer. 

---

# 9. Recommended MVP Definition

The MVP is complete when the team can demonstrate the following scenario end-to-end:

> **An extreme-rainfall event is approaching Pune. New rainfall/forecast data enter the system. The system processes the event, evaluates selected urban locations, assigns flood-risk scores, ranks the highest-risk hotspots, and displays them on a GIS dashboard with understandable reasons for the ranking.**

### MVP success demonstration

A strong hackathon/semester demo should show:

**1. Incoming rainfall information**
↓
**2. AI-generated risk update**
↓
**3. Pune risk map changes**
↓
**4. Top hotspots are ranked**
↓
**5. Decision-maker sees why those locations are high risk**
↓
**6. Suggested response priority is displayed**

That gives the judges a complete story without pretending to have built the municipal equivalent of an entire Ministry of Earth Sciences.

---

# 10. Product North Star

### North Star Statement

> **Turn Pune's fragmented rainfall, flood and urban-spatial data into timely, location-specific flood-risk intelligence that helps authorities decide where to act first.**

### Product principle

**Do not build another warning system. Build the intelligence layer between warning and action.**

That is the sharpest interpretation of the original proposal's objective of moving from **hazard prediction and generic alerts toward impact assessment and actionable response**. 

### Final scope in one line

> **Predict the next urban flooding hotspots in Pune from extreme rainfall, rank them by risk, and show decision-makers where attention is needed first.**
