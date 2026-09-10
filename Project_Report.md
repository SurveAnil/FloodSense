# Project Report

## AI-Driven Urban Flood Risk Forecasting and Response System for Pune, Maharashtra

### Executive Summary

Pune is increasingly exposed to disruptive urban flooding during intense and short-duration rainfall events. The problem is not limited to rainfall itself: rapid urbanisation, impermeable surfaces, drainage constraints, blocked stormwater infrastructure, low-lying areas, and disconnected or inadequate drainage pathways can convert a heavy-rain event into localised road flooding and severe disruption.

Pune Municipal Corporation (PMC) already maintains flood-prone/waterlogging locations and undertakes pre-monsoon drainage and mitigation work. In 2025, PMC identified **201 waterlogging-prone locations**, including locations compiled with Pune Traffic Police, and subsequently identified additional locations after rainfall exposed new failures. ([Hindustan Times][1]) PMC planning documents also describe extensive stormwater-drainage deficiencies, including obstructed drains and inadequate cross-drainage works. ([ADC Ecos][2])

At the same time, India already has substantial meteorological and hydrological warning infrastructure. IMD provides rainfall forecasts, district and station nowcasts, warnings, rainfall observations and AWS/ARG data through its public API ecosystem. ([IMD API Management][3]) CWC provides river-level and flood forecasting information through its flood forecasting system, using hydrological and meteorological observations and issuing forecasts in advance for monitored river locations. ([CWC][4])

The proposed project therefore should **not attempt to replace IMD or CWC, rebuild Pune's drainage model, or create a generic disaster-management platform**. Its focused contribution is an **AI-based urban flood-risk intelligence layer** that combines official rainfall/nowcast information with Pune-specific flood hotspots and, where access is obtained, GIS/drainage information to estimate which urban locations are most likely to experience disruptive waterlogging and to support prioritised action.

The project remains at the **conceptual/proposal stage**. No dataset has been fully committed or validated yet; consequently, model selection, accuracy and operational performance are not claimed at this stage. This is also consistent with the team's current proposal, which explicitly states that technology/model choices depend on dataset availability and that its flood-response scenario is conceptual pending validation with real-world datasets.  

---

# 1. Problem Statement

## 1.1 Urban Flooding as a Pune-Specific Challenge

Pune's flood problem is fundamentally an **urban water-management and decision-timing problem**, not simply a lack-of-rain problem.

The city has experienced repeated waterlogging and localised flooding during heavy rainfall, affecting roads, underpasses, residential areas, commercial districts and public movement. PMC's own preparedness activities demonstrate that the issue is spatially concentrated: before the 2025 monsoon, the civic body identified 201 waterlogging-prone locations. The list combined PMC-identified locations with 118 locations identified by Pune Traffic Police as recurring traffic problem areas during heavy rain. ([Hindustan Times][1])

The problem persisted despite preventive work. After the first spells of rain in May 2025, PMC identified **28 additional locations** where flooding occurred, illustrating an important weakness in a static hotspot-list approach: known locations can be mitigated, while new vulnerable locations can emerge when rainfall intensity, drainage conditions, construction and urban runoff patterns change. ([Hindustan Times][5])

Recent reporting also highlights how quickly severe rainfall can overwhelm urban systems. A 2025 PMC-related report described **46 waterlogging complaints in a single evening**, with blocked manholes and waste identified as contributors. ([Hindustan Times][6]) A subsequent PMC audit reported approximately **260 flood-prone locations**, with blocked stormwater chambers, deficient drainage and road-design problems contributing to flooding. ([Times of India][7])

## 1.2 Structural Causes

Pune's stormwater problem has been recognised in municipal planning documents for years. PMC's stormwater planning material identifies rapid urbanisation, increasing paved surfaces and reduced infiltration as drivers of greater runoff and notes that development has contributed to flooding even during moderate rainfall in some locations. ([Pune Open Data Portal][8])

A PMC stormwater master-plan document reports:

| Indicator                               | Reported scale |
| --------------------------------------- | -------------: |
| Nallas and branches                     |            712 |
| Nalla length                            |      874.08 km |
| Fully obstructed nallas                 |       86.32 km |
| Partially obstructed nallas             |       65.32 km |
| Frequently flooding nalla length        |       27.95 km |
| Total culvert/cross-drainage works      |          1,010 |
| Inadequate cross-drainage works         |            518 |
| Approx. additional road drains required |       2,168 km |

These figures illustrate that flooding is linked to the capacity and condition of the physical drainage system rather than rainfall alone. ([ADC Ecos][2])

## 1.3 Consequences

Urban flooding creates several interconnected impacts:

**Residents and communities:** difficulty reaching homes, schools and workplaces; exposure to contaminated standing water; disruption to mobility; and increased risk to vulnerable households.

**Road and transport infrastructure:** waterlogged roads, underpasses, traffic bottlenecks, vehicle failures and reduced emergency accessibility. Local reporting during the 2025 monsoon described significant waterlogging, potholes and traffic disruption across Pune. ([The Indian Express][9])

**Municipal services:** emergency-response teams must react to multiple locations simultaneously while drainage, traffic, sanitation and disaster-management departments coordinate under time pressure.

**Urban planning:** repeated flooding at the same or newly emerging locations indicates that historical hotspot information alone is insufficient for anticipating where the next significant disruption will occur.

## 1.4 Core Problem

The project therefore addresses the following problem:

> **Pune has rainfall forecasts, weather warnings, hydrological information and historically identified waterlogging locations, but these information streams are not necessarily combined into a single, dynamic, urban-scale risk layer that indicates which local areas are most likely to experience disruptive flooding during an approaching extreme-rainfall event and where response attention should be prioritised.**

This distinction is critical. The project is **not claiming that Pune lacks flood warnings**. It is targeting the gap between **hazard information** and **location-specific urban impact intelligence**.

---

# 2. Proposed Solution

## 2.1 Project Concept

The proposed system is an **AI-driven urban flood-risk intelligence pipeline for Pune**.

Its purpose is to transform multiple existing information sources into a dynamically updated map and prioritised risk assessment:

> **Observe → Forecast rainfall → Assess local flood likelihood → Rank vulnerable hotspots → Alert and prioritise response**

The system is conceived as an integration and intelligence layer above existing data and government warning systems rather than as a replacement for them.

This is a deliberate narrowing of the team's original multi-hazard concept. The current presentation proposes multiple hazards, vulnerability modelling, health-risk assessment, resource optimisation, GIS and decision support.  For the Pune project, these functions should be reduced to those directly supporting **urban flood risk from extreme rainfall**.

---

## 2.2 Proposed Data Integration

### A. IMD rainfall, forecast and nowcast data

IMD already exposes multiple relevant products through its API platform, including:

* district rainfall forecasts,
* district and station nowcasts,
* current weather,
* rainfall observations,
* AWS/ARG observations,
* district and subdivision warnings,
* quantitative precipitation products.

IMD's documented district nowcast service includes rainfall-intensity categories and warning severity information, while its AWS/ARG services can provide observation data where the required access is available. ([IMD API Management][3])

For the proposed project, IMD becomes the principal source of **meteorological hazard inputs**.

### B. CWC flood forecasting information

CWC's flood forecasting system provides real-time/near-real-time river information and forecasts for monitored locations. CWC reports using hydrological and meteorological observations for flood forecasting and generally issuing forecasts several hours in advance depending on location and river conditions. ([CWC][4])

For Pune, CWC data should be treated as **hydrological context**, particularly for river-related flooding and downstream conditions, rather than as a complete solution for street-level urban waterlogging.

This distinction is technically important:

> **CWC can inform river/flood conditions; the proposed system focuses on translating rainfall and city-specific spatial characteristics into urban waterlogging risk.**

### C. PMC waterlogging/flood-prone hotspot data

PMC's published/communicated hotspot information provides historical evidence about locations that repeatedly experience waterlogging. In 2025, PMC reported a consolidated list of 201 locations, derived partly from its own records and partly from Pune Traffic Police observations. ([Hindustan Times][1])

These data can provide the model with a **historical spatial prior**: locations with previous flooding are not treated equally to locations with no historical evidence.

However, the project should avoid treating the hotspot list as ground truth. The appearance of 28 additional flood-prone locations in 2025 demonstrates that static lists can become incomplete as urban conditions and rainfall characteristics change. ([Hindustan Times][5])

### D. PMC GIS and drainage data

Where accessible through open-data portals, institutional cooperation or formal data requests, the project should incorporate:

* stormwater drain networks,
* nallas,
* culverts,
* drainage catchments,
* road networks,
* elevation/terrain,
* land-use information,
* known drainage bottlenecks,
* municipal ward boundaries,
* critical infrastructure.

PMC's existing stormwater planning material demonstrates that detailed drainage information exists in municipal planning work, including drainage networks, hydraulic considerations and identified infrastructure deficiencies. ([Pune Open Data Portal][8])

However, **access to machine-readable, current GIS/drainage layers should be treated as a dependency, not an assumption**.

---

## 2.3 End-to-End Pipeline

### Stage 1 — Data Ingestion

The platform periodically retrieves available observations and forecasts from:

**IMD → rainfall / forecast / nowcast**
**CWC → river/flood information**
**PMC → historical flood hotspots**
**GIS → drainage, terrain, roads and urban features**

The ingestion layer timestamps and standardises the information.

### Stage 2 — Data Processing and Spatial Alignment

Different sources operate at different spatial and temporal resolutions.

The system therefore maps them onto a common geographic grid or set of urban zones, such as:

* road segments,
* neighbourhoods,
* wards,
* drainage catchments,
* predefined grid cells.

The prototype should use one spatial representation consistently rather than attempting a sophisticated city-wide hydrodynamic model.

### Stage 3 — Extreme Rainfall Analysis

The system identifies rainfall conditions associated with heightened urban flooding potential, considering variables such as:

* forecast rainfall amount,
* rainfall intensity,
* short-duration rainfall accumulation,
* recent cumulative rainfall,
* nowcast severity,
* antecedent wetness proxies,
* spatial concentration of rainfall.

IMD's nowcast categories provide directly useful rainfall-severity signals; for example, its API documentation distinguishes moderate rain at 5–15 mm/hour from heavy rain above 15 mm/hour and provides severity colour coding. ([IMD API Management][3])

### Stage 4 — Urban Flood-Risk Prediction

Rather than trying to predict the weather itself, the AI component estimates:

> **Given current/forecast rainfall and known urban characteristics, how likely is each hotspot or urban area to experience disruptive waterlogging?**

A practical prototype model could be based on:

* XGBoost,
* Random Forest,
* logistic regression as a baseline,
* or another interpretable tabular model.

The model can output a probability or categorical level such as:

**Low → Moderate → High → Critical**

The original proposal already envisaged explainable risk scoring and XGBoost-type models, but those choices were intentionally left subject to data analysis. 

### Stage 5 — Hotspot Ranking

Instead of simply showing weather warnings, the system produces a ranked list:

| Rank | Location  | Predicted Risk | Main Drivers                                               | Suggested Attention   |
| ---- | --------- | -------------- | ---------------------------------------------------------- | --------------------- |
| 1    | Hotspot A | Critical       | Heavy rainfall + historical flooding + drainage constraint | Immediate inspection  |
| 2    | Hotspot B | High           | High rainfall + low-lying terrain                          | Pre-position response |
| 3    | Hotspot C | High           | High rainfall + repeated historical incidents              | Monitor/prepare       |
| …    | …         | …              | …                                                          | …                     |

This ranking is one of the project's strongest practical outputs.

### Stage 6 — Alerts and Decision Support

The system can generate different outputs for different users.

**Authority dashboard:** risk map, ranked hotspots, rainfall status and recommended attention areas.

**Field-response view:** locations requiring inspection, drain clearing, barricading or traffic intervention.

**Citizen-facing view:** simplified location-specific flood-risk alerts and travel cautions.

For the hackathon/semester MVP, the system should focus primarily on the **authority/response dashboard**. Public alert delivery can remain a prototype extension.

---

## 2.4 Conceptual AI Architecture

The recommended architecture is:

**Official Data Sources**
↓
**Data Ingestion & Validation**
↓
**Spatio-Temporal Feature Engineering**
↓
**Urban Flood-Risk ML Model**
↓
**Hotspot Risk Score**
↓
**GIS Visualization + Priority Ranking**
↓
**Decision/Alert Layer**

This is significantly more defensible than positioning the project as a new national weather-prediction system.

---

## 2.5 Current Project Maturity

The project is currently **conceptual/proposal-stage**.

No dataset is presently treated as fully committed, production-ready or validated. Consequently:

* no model accuracy is claimed;
* no guaranteed lead time is claimed;
* final model selection is pending dataset analysis;
* real-time API reliability and access permissions remain to be verified;
* PMC GIS/drainage availability remains an access dependency;
* the prototype should initially be evaluated retrospectively using historical events.

The existing project proposal similarly states that final technology and model choices depend on dataset availability and that the flood-response scenario is conceptual until model outputs are validated with real datasets.  

---

# 3. Impact

## 3.1 Improved Flood-Risk Prediction

The system is expected to improve **local flood-risk estimation**, not necessarily raw weather prediction.

Its principal advantage would be combining:

**rainfall intensity + rainfall forecast + historical flooding + terrain/drainage context**

rather than using rainfall alone.

The result should be a more location-aware understanding of where an extreme-rainfall event is likely to translate into urban disruption.

## 3.2 Timelier Local Alerts

Official weather systems can communicate that heavy rainfall is occurring or expected. The proposed system adds another question:

> **Which places in Pune should be considered most at risk because of that rainfall?**

This can shorten the decision path between a meteorological warning and a local operational response.

## 3.3 Better Resource Allocation

During a major rainfall event, authorities may have limited:

* emergency teams,
* pumps,
* barricades,
* traffic personnel,
* field inspection teams,
* drainage maintenance crews.

A ranked risk map allows these resources to be deployed according to predicted need rather than solely according to complaint volume or historical priority.

## 3.4 Improved Urban Planning

The system's historical database can become useful beyond live alerts.

Repeated predictions and observed outcomes could identify:

* locations where drainage upgrades are consistently needed;
* newly emerging flood hotspots;
* areas where existing mitigation measures are ineffective;
* infrastructure that repeatedly becomes inaccessible.

This can support evidence-based prioritisation of future drainage and road interventions.

## 3.5 Reduction in Disruption

A successful system could reduce the severity or duration of disruptions by enabling authorities to act before waterlogging becomes severe.

Examples include:

* inspecting vulnerable locations before rainfall peaks;
* clearing critical drains;
* placing barricades ahead of severe waterlogging;
* redirecting traffic;
* positioning response teams closer to predicted hotspots.

The expected impact should be presented as **potential operational improvement**, not as a guaranteed percentage reduction in damages until the system is validated.

---

# 4. Value Proposition

## 4.1 Existing Systems Already Provide Important Inputs

A major strength of this proposal is that it does not need to pretend that current institutions are starting from zero.

IMD already provides weather forecasts, nowcasts, rainfall information and warnings. ([IMD API Management][3])

CWC already monitors river conditions and produces flood forecasts for its monitored locations. ([CWC][4])

PMC already identifies waterlogging-prone locations and conducts drainage and monsoon-preparedness interventions. ([Hindustan Times][1])

The opportunity is therefore to create a **decision-intelligence layer between these information sources and urban operations**.

## 4.2 The Missing Layer

The project's value proposition can be expressed simply:

> **Existing systems tell Pune about rainfall, river conditions and known problem areas. Our AI layer estimates where the next extreme-rainfall event is most likely to cause disruptive urban flooding and ranks those locations for action.**

This positioning is considerably stronger than:

> “We are building an AI platform that predicts floods, assesses health risks, allocates resources and manages disasters.”

The latter sounds ambitious but difficult to validate. The former identifies one specific operational gap.

## 4.3 Why Data Integration Matters

A single data source has limited explanatory power.

For example:

**Heavy rainfall warning alone**
does not tell an authority which road will flood first.

**Historical hotspot list alone**
does not tell an authority whether today's rainfall will be sufficient to trigger flooding.

**Drainage map alone**
does not indicate when the network will be stressed.

Combining these creates a richer representation of flood risk.

## 4.4 Real-Time Capability

IMD's public API ecosystem is explicitly designed around current weather, forecasts, nowcasts and warnings. ([IMD API Management][3])

This makes the project technically suitable for an event-driven dashboard where risk scores are refreshed whenever new rainfall or forecast information becomes available.

## 4.5 Potential Reduction in Damage and Disruption

The value should be framed operationally:

**Earlier information → better prioritisation → faster intervention → potentially less disruption**

The project does not require perfect prediction to create value. A system that consistently identifies the highest-risk subset of locations earlier than manual processes could already be useful.

---

# 5. Feature Scope

The following scope is recommended for the project.

## 5.1 Core Features — MVP

### 1. Multi-source data ingestion

Connect or simulate ingestion of:

* IMD rainfall data,
* IMD nowcast/forecast,
* CWC flood information where relevant,
* PMC hotspot records,
* GIS layers where available.

The architecture should support both APIs and static datasets.

### 2. Data validation and preprocessing

Handle:

* missing observations,
* timestamp alignment,
* duplicate records,
* geographic standardisation,
* unit conversion,
* incomplete API responses.

This is particularly important in a research prototype because model quality cannot compensate for poorly aligned inputs.

### 3. Extreme-rainfall risk engine

Calculate features such as:

* forecast rainfall,
* recent accumulated rainfall,
* rainfall intensity,
* warning category,
* historical flood occurrence,
* terrain/drainage indicators.

### 4. AI-based hotspot risk scoring

Generate:

**risk score + risk category + confidence/uncertainty indicator**

for each selected location.

### 5. Dynamic flood-risk map

GIS dashboard showing:

* Pune map,
* rainfall conditions,
* flood-risk zones,
* known hotspots,
* important roads,
* drainage infrastructure where available.

### 6. Hotspot prioritisation

Produce a ranked list of locations requiring attention.

This should be the **primary decision-support output**.

### 7. Alert generation

Generate warning states such as:

* Monitor,
* Prepare,
* High Risk,
* Critical Risk.

For the prototype, alerts can be dashboard notifications rather than full public emergency broadcasting.

---

## 5.2 Secondary Features — Later Phase

These should not become core semester deliverables:

* citizen mobile application;
* automated SMS/WhatsApp deployment;
* real-time road closure integration;
* automated pump control;
* optimisation of emergency-vehicle routing;
* advanced hydrodynamic flood simulation;
* satellite-based real-time water-depth estimation;
* multimodal AI with CCTV feeds;
* city-wide digital twin;
* autonomous emergency resource dispatch.

These ideas are technically interesting, but adding them would recreate the original scope problem.

---

## 5.3 Features to Explicitly Defer

The team's original proposal included **climate-health risk**, population vulnerability modelling, continuous learning and broad emergency resource optimisation. 

For this project, these should be deferred unless sufficient time and datasets remain after the flood-risk MVP works.

The strongest semester project is:

> **Rainfall → Urban flood-risk prediction → Hotspot ranking → GIS decision support**

rather than:

> Rainfall → flood → health → demographics → infrastructure → evacuation → resource optimisation → continuous learning.

One excellent model beats six PowerPoint models, Sir.

---

# 6. Resources Required

## 6.1 Data Resources

### Priority 1 — IMD

Required:

* rainfall observations,
* rainfall forecast,
* district/station nowcast,
* AWS/ARG observations where accessible,
* warning information.

IMD's official API documentation confirms the availability of these categories. ([IMD API Management][3])

### Priority 2 — Historical Flood/Waterlogging Data

Required:

* PMC hotspot list,
* date/time of flooding events,
* location coordinates,
* reported severity,
* duration where available,
* road/ward information.

The project should seek machine-readable versions rather than relying only on manually transcribed reports.

### Priority 3 — PMC GIS/Drainage Data

Potential requirements:

* stormwater network,
* nallas,
* culverts,
* catchments,
* road network,
* elevation,
* low-lying areas,
* municipal wards,
* drainage assets.

PMC planning documents show that substantial stormwater-network information exists, but project access to current machine-readable GIS layers must be confirmed. ([ADC Ecos][2])

### Priority 4 — CWC

Required where relevant:

* river water-level observations,
* flood forecasts,
* river-condition indicators,
* reservoir/inflow information where available and appropriate to the study area.

CWC's official flood forecasting framework includes river-level and inflow forecasting and near-real-time flood information. ([CWC][4])

---

## 6.2 Institutional Partnerships

The most valuable partnership would be with **PMC**, particularly:

* Disaster Management Department,
* Drainage Department,
* GIS/IT/open-data teams.

The project should request:

1. historical waterlogging-event records;
2. current hotspot lists;
3. coordinates for known flooding sites;
4. drainage network GIS layers;
5. stormwater assets;
6. historical intervention/mitigation records;
7. flood-related complaints or incident logs where available.

A relationship with **IMD** would improve access to meteorological data and interpretation, while **CWC** can provide hydrological context.

For an academic prototype, formal institutional partnership may not be secured immediately. The technical architecture should therefore support publicly available data and clearly label unavailable datasets.

---

## 6.3 Human Resources

A small student team can realistically implement the MVP with four complementary responsibilities:

| Role                 | Main Responsibility                                     |
| -------------------- | ------------------------------------------------------- |
| Data/ML Engineer     | Data processing, feature engineering, model development |
| GIS/Spatial Engineer | Mapping, spatial joins, hotspot analysis                |
| Backend Engineer     | APIs, database and pipeline orchestration               |
| Frontend/UX Engineer | Dashboard, visualisation and alerts                     |

One member can perform multiple roles depending on the team size.

The team should also have access to a faculty/domain mentor with knowledge of:

* GIS,
* hydrology,
* urban planning,
* disaster management,
* or environmental engineering.

---

## 6.4 Computing Infrastructure

The initial system does **not** require expensive infrastructure.

A reasonable prototype stack is:

**Frontend:** React
**Backend:** Python + FastAPI
**ML:** Scikit-learn / XGBoost
**Database:** PostgreSQL + PostGIS
**Maps:** OpenStreetMap-based tooling or an appropriate map API
**Processing:** Python/Pandas/GeoPandas
**Deployment:** cloud VM/container or university infrastructure

This is aligned with the broad technology direction already proposed in the team's presentation. 

GPU infrastructure should not be treated as mandatory unless the team later adopts deep-learning or image-based models.

---

# 7. Recommended Project Boundary

To keep the project realistically buildable during the semester/hackathon, the boundary should be explicit.

### The project WILL:

* focus only on **urban flooding caused by extreme rainfall in Pune**;
* ingest official weather information;
* combine it with historical flood hotspots;
* incorporate GIS/drainage information where accessible;
* develop an AI-based urban flood-risk model;
* produce location-specific risk scores;
* rank flood-prone locations;
* visualise results through GIS;
* demonstrate a response-prioritisation workflow.

### The project WILL NOT initially:

* forecast cyclones, droughts or heatwaves;
* build a national weather-prediction model;
* replace IMD or CWC;
* build a full hydrodynamic simulation of every Pune drain;
* produce medical/health-risk predictions;
* optimise every emergency resource in the city;
* guarantee evacuation decisions;
* autonomously operate municipal infrastructure.

---

# 8. Final Recommended Project Definition

### Proposed Title

**AI-Based Urban Flood Risk Forecasting and Hotspot Prioritization System for Pune**

### One-Line Value Proposition

> **An AI-powered decision-support system that combines real-time rainfall forecasts, hydrological information, historical waterlogging hotspots and urban GIS data to predict which parts of Pune are most likely to experience disruptive flooding during extreme rainfall and prioritise them for timely intervention.**

### Core AI Question

> **“Given the rainfall expected in Pune, where is urban flooding most likely to occur next?”**

### Core Output

> **A dynamically ranked, GIS-based urban flood-risk map with hotspot-level risk scores and recommended response priority.**

### The Single Missing Layer

The project's most defensible innovation is **not another weather alert system**.

It is:

> **An AI-driven impact layer that translates existing rainfall and flood information into hyperlocal urban waterlogging risk and response priority.**

That positioning fits the actual problem shown by Pune's recent experience: the city already has forecasts, preparedness programs and known flood-prone locations, but new waterlogging sites can emerge and previously addressed locations can still fail under intense rainfall. ([Hindustan Times][5])

It also fits the strongest idea already present in your team's PPT—moving from **“What is going to happen?” to “What should we do about it?”**—but reduces the implementation burden to one hazard and one measurable operational problem. 

### Bottom line

For the semester and hackathon, I would make the project:

**IMD/CWC data + PMC flood history + GIS → AI urban flood-risk prediction → hotspot ranking → authority dashboard.**

Everything else is secondary until this pipeline works on real historical Pune rainfall/flood events.

[1]: https://www.hindustantimes.com/cities/pune-news/pune-civic-body-begins-monsoon-preparedness-to-act-on-201-flood-prone-spots-101745433680626.html?utm_source=chatgpt.com "Pune civic body begins monsoon preparedness, to act on 201 flood-prone spots | Hindustan Times"
[2]: https://adc-ecos.enlightcloud.com/1133pmcwebsitev2/s3fs-public/2025-06/flood_control_and_disaster_management_action_plan_2025_0.pdf?VersionId=e2ab5c57-c8b4-48af-bf9d-a420ffef16cd&utm_source=chatgpt.com "Storm Water Master Plan of Pune Municipal Corporation"
[3]: https://api.imd.gov.in/public/api_reference.html?utm_source=chatgpt.com "IMD API Reference"
[4]: https://www.cwc.gov.in/sites/default/files/annual-report-cwc-2022-23_2.pdf?utm_source=chatgpt.com "सत्तमे्यमेतेव जयते"
[5]: https://www.hindustantimes.com/cities/pune-news/pmc-identifies-28-new-flood-prone-spots-across-city-after-first-spell-of-rain-101748372179789-amp.html?utm_source=chatgpt.com "PMC identifies 28 new flood-prone spots across city after first spell of rain | Hindustan Times"
[6]: https://www.hindustantimes.com/cities/pune-news/rains-expose-pmc-s-drainage-cleanup-claims-46-waterlogging-complaints-101747853574777.html?utm_source=chatgpt.com "Rains expose PMC’s drainage cleanup claims; 46 waterlogging complaints | Hindustan Times"
[7]: https://timesofindia.indiatimes.com/city/pune/trash-key-trigger-for-flooding-during-rain-pmc-audit-shows/articleshow/130026370.cms?utm_source=chatgpt.com "Trash key trigger for flooding during rain, PMC audit shows"
[8]: https://opendata.pmc.gov.in/opendata/PMCReports/PMC-Storm-Water-Drainage.pdf?utm_source=chatgpt.com "Design of NetworkBackgroundBase Map PreparationThe rapid urbanization has significantly changed the nature of drainage areas in Pune city. The open grounds"
[9]: https://indianexpress.com/article/cities/pune/waterlogging-potholes-traffic-snarls-across-city-fuel-commuters-frustration-10076900/?utm_source=chatgpt.com "Waterlogging, potholes, traffic snarls across city fuel commuters’ frustration | Pune News - The Indian Express"
