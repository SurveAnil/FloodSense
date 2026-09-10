# Technical Requirements Document (TRD)

## AI-Based Urban Flood Risk Forecasting & Hotspot Prioritization System — Pune, Maharashtra

**Document Status:** Technical Design — Proposal / Pre-MVP
**Product Status:** Conceptual / Proposal Stage
**Primary Hazard:** Urban flooding caused by extreme rainfall
**Geographic Scope:** Pune, Maharashtra
**Primary Users:** Municipal disaster-management and field-response teams
**Primary Technical Output:** Location-specific urban flood-risk score and ranked hotspot prioritization
**Primary Decision Flow:**
**Data ingestion → Data validation → Feature engineering → AI flood-risk prediction → Hotspot ranking → GIS decision dashboard**

---

## 1. Purpose and Technical Scope

This TRD translates the approved PRD into an implementation-oriented technical specification.

The system is deliberately limited to the PRD's defined product scope: **predicting where extreme rainfall is most likely to cause disruptive urban flooding in Pune, ranking those locations by risk, and presenting the result through a GIS-based decision-support interface.**

The PRD explicitly establishes that the project is still conceptual and that real datasets, prediction parameters and final model selection have not yet been committed. Therefore, this TRD distinguishes between:

* **DECIDED** — explicitly established by the PRD;
* **REQUIRED** — technically necessary to implement an already-decided capability;
* **TBD** — deliberately unresolved because the PRD does not provide enough evidence to determine it.

### Important specification rule

No upstream API URL, authentication mechanism, cloud provider, software version, prediction horizon, spatial unit, target-label definition, model hyperparameter or numerical performance target is invented in this document.

Where such information is required, it is recorded as a formal **TBD decision item**.

---

# 2. System Architecture

## 2.1 High-Level Architecture

The system shall follow a modular architecture:

```text
┌───────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                  │
│                                                           │
│  IMD          CWC          PMC             GIS            │
│  Rainfall     Flood/       Hotspots        Drainage/     │
│  Forecast     Hydro Data   Historical      Spatial Data  │
│  Nowcast                   Waterlogging                   │
└──────┬──────────┬───────────┬───────────────┬─────────────┘
       │          │           │               │
       └──────────┴───────────┴───────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│              DATA INGESTION & VALIDATION                  │
│                                                           │
│  Source Adapters → Normalization → Validation →           │
│  Timestamp / Geographic Alignment → Data Quality Status  │
└──────────────────────────┬────────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────────┐
│             SPATIO-TEMPORAL FEATURE ENGINE                │
│                                                           │
│  Rainfall Features + Historical Flood Context +          │
│  Spatial / Terrain / Drainage Features                   │
└──────────────────────────┬────────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────────┐
│                 AI FLOOD-RISK MODEL                       │
│                                                           │
│  Baseline → Candidate ML Models → Evaluation →           │
│  Selected Model → Risk Score / Risk Category             │
└──────────────────────────┬────────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────────┐
│              HOTSPOT PRIORITIZATION ENGINE                │
│                                                           │
│  Risk Ranking → Priority Locations → Risk Drivers        │
└──────────────────────────┬────────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────────┐
│                GIS DECISION DASHBOARD                    │
│                                                           │
│  Risk Map | Hotspot Ranking | Rainfall | Risk Details    │
│  Data Freshness | Prediction Timestamp                   │
└───────────────────────────────────────────────────────────┘
                           ↓
                  HUMAN DECISION / RESPONSE
```

The architecture follows the PRD's principle that the product should operate as an **intelligence layer over existing information systems**, rather than replacing IMD, CWC or PMC.

---

# 3. System Components

## 3.1 External Data Adapter Layer

The adapter layer provides a common internal interface for external sources.

### Required sources

| Source         | Required information                           | Role                       |
| -------------- | ---------------------------------------------- | -------------------------- |
| IMD            | Rainfall observations, forecast, nowcast       | Meteorological input       |
| CWC            | Flood/hydrological information where relevant  | Hydrological context       |
| PMC            | Historical waterlogging/flood hotspots         | Historical spatial prior   |
| PMC GIS        | Drainage and urban spatial data, if accessible | Spatial context            |
| Supporting GIS | Terrain/spatial information                    | Spatial feature generation |

The system shall isolate external-source-specific formats from the rest of the application.

This means the ML system should consume a **normalized internal data model**, not depend directly on the raw format of an individual provider.

---

# 4. Technology Stack

The following stack is derived from the PRD and is not expanded with uncommitted technologies.

| Layer             | Technology                                            | Status                   |
| ----------------- | ----------------------------------------------------- | ------------------------ |
| Frontend          | React                                                 | **DECIDED**              |
| Web technologies  | HTML / CSS / JavaScript                               | **DECIDED**              |
| Backend           | Python + FastAPI                                      | **DECIDED**              |
| ML baseline       | Scikit-learn                                          | **DECIDED**              |
| Candidate ML      | XGBoost                                               | **DECIDED**              |
| Database          | PostgreSQL                                            | **DECIDED**              |
| Spatial database  | PostGIS                                               | **DECIDED**              |
| Data processing   | Python / Pandas / GeoPandas                           | **DECIDED**              |
| Mapping           | OpenStreetMap-based tooling or appropriate map API    | **DECIDED**              |
| Deployment        | Cloud-ready architecture or university infrastructure | **DECIDED**              |
| Cloud provider    | TBD                                                   | **Not committed by PRD** |
| Containerization  | TBD                                                   | **Not committed by PRD** |
| Orchestration     | TBD                                                   | **Not committed by PRD** |
| Software versions | TBD                                                   | **Not committed by PRD** |

### Technology decision principle

The PRD explicitly prefers an interpretable tabular ML approach unless dataset analysis justifies greater complexity.

The system therefore shall **not assume deep learning merely because it is available**.

---

# 5. External Data Requirements

## 5.1 IMD Interface

### Purpose

Provide meteorological inputs required to estimate urban flood risk.

### Logical interface

```text
IMD Adapter
    ↓
Normalized Weather Data
```

### Logical operations

```text
getRainfallObservations()
getRainfallForecast()
getNowcast()
getWarningInformation()
```

These are **logical application interfaces**, not claimed upstream IMD endpoints.

### Normalized rainfall observation model

```text
RainfallObservation
-------------------
source
observation_time
location_id
latitude
longitude
rainfall_value
rainfall_unit
data_status
source_timestamp
ingested_at
```

### Normalized forecast model

```text
RainfallForecast
----------------
source
forecast_issued_at
forecast_valid_from
forecast_valid_to
location_id
latitude
longitude
forecast_value
forecast_unit
forecast_category
data_status
ingested_at
```

### Nowcast model

```text
RainfallNowcast
---------------
source
issued_at
valid_from
valid_to
location_id
intensity_category
severity_category
data_status
ingested_at
```

### TBD — Upstream IMD contract

**Field purpose:** Defines the actual external API/interface consumed by the adapter.

**Depends on:** IMD data access and interface verification.

**Decision required:** Confirm actual endpoint, authentication, request parameters, response structure, rate limits and update frequency when access is established.

---

# 6. CWC Interface

## 6.1 Purpose

Provide hydrological/flood information where relevant to Pune's urban flood-risk assessment.

The system shall treat CWC information as **hydrological context**, not as a replacement for the urban waterlogging prediction layer.

### Logical interface

```text
CWC Adapter
    ↓
Normalized Hydrological Data
```

### Logical operations

```text
getFloodInformation()
getHydrologicalObservations()
```

### Normalized hydrological model

```text
HydrologicalObservation
-----------------------
source
observation_time
location_id
water_level
water_level_unit
flow_value
flow_unit
flood_status
data_status
source_timestamp
ingested_at
```

Fields such as `flow_value` remain subject to actual CWC data availability.

### TBD — CWC field availability

**Field purpose:** Determines which hydrological variables can actually be consumed.

**Depends on:** CWC data access and available data structure.

**Decision required:** Select only fields actually available and relevant to the Pune study area.

---

# 7. PMC Data Interface

## 7.1 Historical Waterlogging Hotspots

### Purpose

Provide historical spatial information about locations that have experienced recurring waterlogging/flooding.

### Logical interface

```text
PMC Hotspot Adapter
        ↓
Normalized Hotspot Dataset
```

### Logical operation

```text
getWaterloggingHotspots()
```

### Hotspot model

```text
WaterloggingHotspot
-------------------
hotspot_id
location_name
latitude
longitude
ward_id
historical_status
source
source_date
geometry
data_status
```

Some fields, particularly `ward_id` and precise geometry, depend on the format of the data obtained.

### TBD — Historical event detail

**Field purpose:** Determines how much historical flood information can be used for model training.

**Depends on:** PMC data access.

**Decision required:** Establish whether the available data contain only hotspot locations or historical event-level information such as date, time and severity.

---

# 8. PMC GIS / Drainage Interface

## 8.1 Purpose

Provide urban spatial context for flood-risk prediction where accessible.

Potential data categories already identified by the PRD include:

* stormwater drainage;
* nallas;
* culverts;
* drainage catchments;
* road networks;
* elevation/terrain;
* low-lying areas;
* municipal boundaries.

### Logical interface

```text
PMC GIS Adapter
       ↓
Normalized Spatial Layers
```

### Logical operation

```text
getSpatialLayers()
```

### Generic spatial-layer model

```text
GISFeature
----------
feature_id
layer_type
geometry
attributes
source
source_timestamp
data_status
```

### Important dependency

PMC GIS/drainage data are **not guaranteed to be available**.

The system must therefore remain operational without them.

### TBD — GIS availability

**Field purpose:** Determines which spatial features can become ML inputs.

**Depends on:** PMC data access and availability of machine-readable GIS layers.

**Decision required:** Identify accessible layers, geographic coordinate system, update frequency, geometry quality and relevant attributes.

---

# 9. Data Normalization Requirements

All external data shall pass through a common normalization process before entering the ML pipeline.

## Required processing

### Timestamp normalization

All records shall use a common internal timestamp representation.

**TBD:** Exact timestamp standard/timezone representation.

**Depends on:** Source formats and implementation convention.

---

### Geographic normalization

All spatial records shall be transformed into the system's selected geographic reference.

**TBD — Spatial reference system**

**Purpose:** Provides consistent spatial joins between rainfall, hotspots and GIS layers.

**Depends on:** Selected mapping implementation and available source coordinate systems.

**Decision required:** Select the final coordinate reference system after actual GIS data are obtained.

---

### Unit normalization

Rainfall and hydrological measurements shall use standardized internal units.

**TBD:** Exact canonical unit for each variable.

**Depends on:** Actual upstream datasets.

**Decision required:** Establish canonical units during data-ingestion implementation.

---

# 10. Data Quality Management

Every external data record shall retain sufficient metadata to establish:

* source;
* observation/forecast time;
* ingestion time;
* data status;
* geographic reference.

The system shall detect:

* missing values;
* invalid coordinates;
* duplicate records;
* stale information;
* invalid timestamps;
* unavailable sources.

### Critical requirement

Missing rainfall data shall **not** automatically be interpreted as zero rainfall.

---

# 11. Machine Learning Pipeline

## 11.1 ML Objective

The ML system shall answer:

> **Given current and/or forecast rainfall and available urban spatial context, how likely is a defined Pune location to experience disruptive urban flooding?**

The system predicts **urban flood risk**, not weather itself.

---

# 12. ML Pipeline Stages

```text
Raw Data
   ↓
Data Validation
   ↓
Data Alignment
   ↓
Feature Engineering
   ↓
Training Dataset
   ↓
Baseline Model
   ↓
Candidate Model Evaluation
   ↓
Selected Model
   ↓
Risk Prediction
   ↓
Risk Classification
   ↓
Hotspot Ranking
```

---

## 12.1 Stage 1 — Input Data

The pipeline may use:

### Meteorological features

* rainfall observation;
* rainfall forecast;
* rainfall nowcast;
* rainfall intensity;
* recent accumulated rainfall;
* warning/severity information.

### Historical flood features

* historical waterlogging hotspot status;
* historical flood occurrence where event-level data are available.

### Spatial features

* terrain/elevation where available;
* drainage-related features where accessible;
* urban spatial characteristics supported by available GIS data.

### Hydrological context

* relevant CWC information where available.

---

# 13. ML Feature Schema

The internal feature vector can conceptually be represented as:

```text
FloodRiskFeatureVector
----------------------
location_id
timestamp

rainfall_current
rainfall_forecast
rainfall_nowcast
rainfall_intensity
rainfall_accumulation

historical_hotspot_indicator

terrain_features
drainage_features
hydrological_features

data_quality_indicators
```

Not every field is guaranteed to exist.

### TBD — Feature availability

**Field purpose:** Determines which variables can actually be supplied to the model.

**Depends on:** Final datasets and data-access permissions.

**Decision required:** Create the final feature list only after exploratory analysis of the obtained datasets.

---

# 14. Prediction Horizon

### `prediction_horizon`

**Purpose:** Defines how far ahead the system predicts urban flood risk.

**Current status:** **TBD**

**Depends on:**

* IMD forecast/nowcast resolution;
* historical event timestamps;
* available training data;
* operational usefulness.

**Decision required:** Determine the prediction horizon after data availability and retrospective event analysis.

The TRD intentionally does **not** specify a number of minutes or hours.

---

# 15. Spatial Unit

### `spatial_unit`

**Purpose:** Defines the geographic unit for which the model produces a prediction.

Possible representations already compatible with the PRD include:

* hotspot;
* grid cell;
* ward;
* road/location unit.

**Current status:** **TBD**

**Depends on:**

* geographic resolution of source data;
* availability of hotspot coordinates;
* GIS data resolution;
* model training data.

**Decision required:** Select the geographic unit that provides sufficient data quality without claiming unsupported street-level precision.

---

# 16. Target Label

### `target_label`

**Purpose:** Defines what the model learns to predict.

Potential conceptual outcomes consistent with the PRD include:

* observed flooding/waterlogging;
* flood-risk category;
* probability of disruptive flooding.

**Current status:** **TBD**

**Depends on:** Historical event data available for supervised learning.

**Decision required:** Define the target variable after determining what historical flood observations can actually be obtained.

No target label should be fabricated from the existing hotspot list without validating whether the data support such use.

---

# 17. Model Selection

The PRD establishes the following modelling direction:

### Baseline

**Logistic Regression / Scikit-learn baseline**

Purpose:

* establish a simple benchmark;
* provide an interpretable reference;
* evaluate whether more complex models provide meaningful improvement.

### Candidate model

**XGBoost**

Purpose:

* handle structured/tabular features;
* support nonlinear relationships;
* provide interpretable feature contribution mechanisms.

### Selection process

```text
Baseline
   ↓
Candidate model
   ↓
Validation
   ↓
Compare performance
   ↓
Select model
```

### Model selection criterion

The final model shall be selected after dataset analysis rather than being predetermined.

### TBD — Final ML algorithm

**Purpose:** Select the production/prototype model.

**Depends on:** Dataset size, quality, feature types, target-label structure and validation results.

**Decision required:** Finalize model after empirical comparison of the available candidate models.

---

# 18. ML Hyperparameters

### Status: TBD

The PRD does not specify:

* tree depth;
* learning rate;
* number of estimators;
* regularization;
* class weights;
* threshold values;
* training epochs;
* batch size.

These shall therefore **not be predetermined in the TRD**.

**Purpose:** Controls model training and classification behaviour.

**Depends on:** Dataset characteristics and validation results.

**Decision required:** Tune and freeze parameters during model-development validation.

---

# 19. Intermediate ML Outputs

The model pipeline shall produce:

### 1. Feature vector

Normalized input variables for a location/time.

### 2. Model prediction

A model-derived flood-risk value.

### 3. Risk category

The PRD establishes four user-facing categories:

| Category | Interpretation               |
| -------- | ---------------------------- |
| Low      | Monitor                      |
| Moderate | Prepare                      |
| High     | Prioritize / alert           |
| Critical | Immediate response attention |

These categories are **product risk categories**, not official government emergency declarations.

### TBD — Risk thresholds

**Purpose:** Converts model output into Low/Moderate/High/Critical.

**Depends on:** Model output format and validation dataset.

**Decision required:** Establish thresholds empirically after model training and evaluation.

---

# 20. Model Explainability

The PRD requires understandable risk information.

The system should therefore expose the principal factors contributing to an individual prediction.

Example conceptual output:

```text
Location: [Hotspot A]

Risk: HIGH

Contributing factors:
- High forecast rainfall
- Recent rainfall accumulation
- Historical waterlogging
- Spatial/drainage conditions
```

The exact explanation mechanism is **TBD**.

**Purpose:** Explain why a location received its risk score.

**Depends on:** Final ML model.

**Decision required:** Select an explanation method compatible with the final model.

---

# 21. Hotspot Prioritization

After prediction, the system shall transform individual risk estimates into a ranked list.

```text
Risk Predictions
       ↓
Filter relevant locations
       ↓
Sort by risk
       ↓
Priority Ranking
```

### Hotspot output

```text
RiskPriority
------------
rank
location_id
location_name
risk_score
risk_category
prediction_time
risk_drivers
data_freshness
```

The prioritization layer does **not** autonomously dispatch resources.

Its role is to provide a decision-support ranking.

---

# 22. Database Design

## 22.1 Database Technology

**PostgreSQL + PostGIS**

PostgreSQL provides relational storage while PostGIS supports spatial data and geographic queries.

---

# 23. Logical Database Model

```text
                    ┌──────────────────┐
                    │    DataSource    │
                    └────────┬─────────┘
                             │
           ┌─────────────────┼──────────────────┐
           ↓                 ↓                  ↓
 ┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
 │ RainfallData    │ │ ForecastData  │ │ HydroData       │
 └────────┬────────┘ └───────┬───────┘ └────────┬────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
                    ┌─────────────────┐
                    │ SpatialFeature  │
                    └────────┬────────┘
                             │
          ┌──────────────────┴─────────────────┐
          ↓                                    ↓
 ┌──────────────────┐                 ┌──────────────────┐
 │ FloodHotspot     │                 │ RiskPrediction   │
 └──────────────────┘                 └────────┬─────────┘
                                               ↓
                                      ┌──────────────────┐
                                      │ PriorityRanking  │
                                      └──────────────────┘
```

---

# 24. Core Database Tables

## 24.1 `data_sources`

Stores metadata about external information sources.

| Field                       | Purpose                       |
| --------------------------- | ----------------------------- |
| `source_id`                 | Unique source identifier      |
| `source_name`               | IMD/CWC/PMC/GIS               |
| `source_type`               | Weather/Hydrology/Hotspot/GIS |
| `status`                    | Available/unavailable/stale   |
| `last_successful_ingestion` | Last successful update        |
| `created_at`                | Record creation               |

---

## 24.2 `rainfall_observations`

Stores normalized rainfall observations.

| Field              | Purpose               |
| ------------------ | --------------------- |
| `observation_id`   | Unique record         |
| `source_id`        | Data-source reference |
| `location_id`      | Geographic location   |
| `observation_time` | Measurement time      |
| `rainfall_value`   | Rainfall measurement  |
| `rainfall_unit`    | Measurement unit      |
| `geometry`         | Spatial location      |
| `data_status`      | Quality status        |
| `ingested_at`      | Ingestion timestamp   |

---

## 24.3 `rainfall_forecasts`

Stores forecast information.

| Field               | Purpose               |
| ------------------- | --------------------- |
| `forecast_id`       | Unique record         |
| `source_id`         | Source reference      |
| `location_id`       | Geographic location   |
| `issued_at`         | Forecast issue time   |
| `valid_from`        | Forecast period start |
| `valid_to`          | Forecast period end   |
| `forecast_value`    | Forecast rainfall     |
| `forecast_unit`     | Measurement unit      |
| `forecast_category` | Available category    |
| `data_status`       | Quality status        |

---

## 24.4 `rainfall_nowcasts`

Stores nowcast information.

| Field                | Purpose                |
| -------------------- | ---------------------- |
| `nowcast_id`         | Unique record          |
| `source_id`          | Source reference       |
| `location_id`        | Geographic location    |
| `issued_at`          | Issue timestamp        |
| `valid_from`         | Validity start         |
| `valid_to`           | Validity end           |
| `intensity_category` | Rainfall intensity     |
| `severity_category`  | Warning/severity state |
| `data_status`        | Quality status         |

---

## 24.5 `hydrological_observations`

Stores relevant CWC information.

| Field              | Purpose                     |
| ------------------ | --------------------------- |
| `hydro_id`         | Unique identifier           |
| `source_id`        | CWC source                  |
| `location_id`      | Hydrological location       |
| `observation_time` | Observation time            |
| `water_level`      | Available water-level value |
| `flow_value`       | Available flow value        |
| `flood_status`     | Available flood state       |
| `data_status`      | Quality status              |

Fields whose upstream values are unavailable shall not be fabricated.

---

# 25. `flood_hotspots`

Stores historical PMC waterlogging locations.

| Field               | Purpose                      |
| ------------------- | ---------------------------- |
| `hotspot_id`        | Unique identifier            |
| `location_name`     | Human-readable location      |
| `latitude`          | Latitude                     |
| `longitude`         | Longitude                    |
| `ward_id`           | Ward if available            |
| `geometry`          | PostGIS geometry             |
| `historical_status` | Historical hotspot indicator |
| `source_date`       | Source/list date             |
| `source_id`         | PMC reference                |

---

# 26. `spatial_features`

Stores GIS-derived information used by the prediction system.

| Field              | Purpose                    |
| ------------------ | -------------------------- |
| `feature_id`       | Unique feature             |
| `feature_type`     | Drainage/terrain/road/etc. |
| `geometry`         | PostGIS geometry           |
| `attributes`       | Source attributes          |
| `source_id`        | Source reference           |
| `source_timestamp` | Data timestamp             |

The exact feature taxonomy is **TBD** because it depends on accessible GIS data.

---

# 27. `risk_predictions`

Stores model outputs.

| Field             | Purpose                        |
| ----------------- | ------------------------------ |
| `prediction_id`   | Unique prediction              |
| `location_id`     | Predicted location             |
| `prediction_time` | Prediction timestamp           |
| `risk_score`      | Model output                   |
| `risk_category`   | Low/Moderate/High/Critical     |
| `model_version`   | Model used                     |
| `data_timestamp`  | Input-data timestamp           |
| `confidence`      | If supported by selected model |
| `explanation`     | Risk drivers where supported   |

### TBD fields

`risk_score` format, confidence representation and explanation format depend on the final model.

---

# 28. `priority_rankings`

Stores ranked flood-risk locations.

| Field           | Purpose              |
| --------------- | -------------------- |
| `ranking_id`    | Unique ranking       |
| `prediction_id` | Prediction reference |
| `rank`          | Priority position    |
| `location_id`   | Location             |
| `risk_category` | Risk level           |
| `generated_at`  | Ranking timestamp    |

---

# 29. Database Relationships

The core relationships are:

```text
DataSource
   │
   ├── RainfallObservation
   ├── RainfallForecast
   ├── RainfallNowcast
   ├── HydrologicalObservation
   ├── FloodHotspot
   └── SpatialFeature

FloodHotspot
      │
      ↓
RiskPrediction
      │
      ↓
PriorityRanking
```

The system shall preserve source traceability so that predictions can be associated with the data used to generate them.

---

# 30. Storage Strategy

The database shall store:

1. normalized external data;
2. spatial information;
3. historical hotspot information;
4. model predictions;
5. ranking outputs;
6. source/data-quality metadata.

Raw upstream formats may be retained only if required by the eventual implementation and storage constraints.

### TBD — Raw-data retention

**Purpose:** Determine whether original upstream payloads must be retained.

**Depends on:** Data-access terms, storage constraints and validation requirements.

**Decision required:** Establish retention policy once real data sources are obtained.

---

# 31. Internal API Architecture

The backend shall expose logical APIs to the React frontend and internal processing components.

The exact URL naming convention is **not specified by the PRD**; the following are logical endpoint contracts rather than externally committed URLs.

---

# 32. Data APIs

## `GET /api/data/status`

### Purpose

Return the current health/freshness state of data sources.

### Output

```json
{
  "sources": [
    {
      "source": "IMD",
      "status": "available",
      "last_updated": "TBD"
    }
  ]
}
```

Actual timestamp and status values are runtime data.

---

## `GET /api/rainfall/current`

### Purpose

Retrieve normalized current rainfall information.

### Inputs

Potential filters:

```text
location_id: optional
time: optional
```

Exact query parameters are **TBD** based on frontend requirements.

### Output

```json
{
  "observations": [
    {
      "location_id": "TBD",
      "rainfall_value": "TBD",
      "observation_time": "TBD",
      "data_status": "TBD"
    }
  ]
}
```

---

## `GET /api/rainfall/forecast`

### Purpose

Retrieve normalized rainfall forecast information.

### Inputs

```text
location_id: optional
forecast_period: TBD
```

### Output

Forecast records with:

* location;
* forecast value;
* validity period;
* category;
* source timestamp.

---

## `GET /api/rainfall/nowcast`

### Purpose

Retrieve normalized nowcast information.

### Output

* location;
* nowcast validity;
* rainfall intensity;
* severity;
* timestamp.

---

## `GET /api/hydrology`

### Purpose

Retrieve relevant normalized CWC hydrological information.

### Inputs

```text
location_id: optional
time: optional
```

### Output

Available hydrological observations.

---

## `GET /api/hotspots`

### Purpose

Retrieve PMC historical waterlogging hotspots.

### Inputs

Potential filters:

```text
ward_id: optional
risk_status: optional
```

Final filters are **TBD**.

### Output

```json
{
  "hotspots": [
    {
      "hotspot_id": "TBD",
      "location_name": "TBD",
      "latitude": "TBD",
      "longitude": "TBD"
    }
  ]
}
```

---

## `GET /api/gis/layers`

### Purpose

Retrieve accessible spatial layers.

### Inputs

```text
layer_type: TBD
```

### Output

Normalized spatial features.

Availability depends on PMC GIS access.

---

# 33. Prediction APIs

## `POST /api/predictions/generate`

### Purpose

Generate flood-risk predictions from currently available validated inputs.

### Input

Conceptually:

```json
{
  "locations": ["TBD"],
  "prediction_time": "TBD"
}
```

Exact request fields are **TBD** based on the selected spatial unit and prediction workflow.

### Output

```json
{
  "predictions": [
    {
      "location_id": "TBD",
      "risk_score": "TBD",
      "risk_category": "HIGH",
      "prediction_time": "TBD",
      "model_version": "TBD"
    }
  ]
}
```

---

## `GET /api/predictions`

### Purpose

Retrieve previously generated predictions.

### Inputs

Potential filters:

```text
location_id: optional
risk_category: optional
timestamp: optional
```

Exact filters are **TBD**.

---

## `GET /api/predictions/{location_id}`

### Purpose

Retrieve prediction details for a specific location.

### Output

Should include, where supported:

* risk score;
* risk category;
* prediction timestamp;
* input-data timestamp;
* model version;
* risk drivers.

---

# 34. Prioritization APIs

## `GET /api/priorities`

### Purpose

Retrieve ranked flood-risk hotspots.

### Inputs

Potential filters:

```text
risk_category: optional
limit: TBD
```

`limit` is TBD because the PRD does not specify a fixed number of locations.

### Output

```json
{
  "priorities": [
    {
      "rank": 1,
      "location_id": "TBD",
      "risk_score": "TBD",
      "risk_category": "CRITICAL"
    }
  ]
}
```

---

# 35. GIS Dashboard APIs

## `GET /api/map/risk`

### Purpose

Provide the data required to render the current flood-risk map.

### Output

Each geographic unit should expose:

* location/geometry;
* risk score;
* risk category;
* prediction timestamp;
* relevant risk information.

The exact geometry response format is **TBD** based on the selected mapping implementation.

---

## `GET /api/map/hotspots`

### Purpose

Return historical and predicted hotspot information for map display.

---

# 36. Data-Processing APIs

These interfaces are primarily internal.

## `POST /internal/ingestion/imd`

Purpose: Process normalized IMD data.

## `POST /internal/ingestion/cwc`

Purpose: Process normalized CWC information.

## `POST /internal/ingestion/pmc`

Purpose: Process PMC hotspot information.

## `POST /internal/ingestion/gis`

Purpose: Process available GIS layers.

These are logical interfaces; their final implementation mechanism is **TBD**.

---

# 37. API Error Handling

The backend shall distinguish between:

* invalid request;
* unavailable external data;
* stale data;
* incomplete data;
* prediction unavailable;
* internal processing failure.

The frontend shall not display a normal “safe” state when required data are unavailable.

### Example

```text
IMD data unavailable
        ↓
Data status = STALE/UNAVAILABLE
        ↓
Prediction confidence reduced OR prediction withheld
        ↓
Dashboard displays data warning
```

The exact fallback policy is **TBD** and depends on the final model's data requirements.

---

# 38. Frontend Technical Requirements

## 38.1 Framework

**React**

The frontend shall consume backend APIs rather than directly depending on external data-provider interfaces.

---

## 38.2 Primary Views

The MVP dashboard shall contain:

### Risk Map

Displays:

* Pune geographic area;
* risk categories;
* hotspots;
* relevant spatial information.

### Priority List

Displays:

* ranking;
* location;
* risk level;
* relevant risk information.

### Location Detail

Displays:

* risk score/category;
* rainfall context;
* historical hotspot status;
* risk drivers;
* timestamp.

### Data Status

Displays:

* source availability;
* data freshness;
* last update.

---

# 39. Risk Visualization

The PRD establishes:

```text
Low       → Monitor
Moderate  → Prepare
High      → Prioritize / Alert
Critical  → Immediate Response Attention
```

The exact visual implementation is a frontend decision and does not alter the model output.

The dashboard shall clearly distinguish **predicted risk** from **observed flooding**.

---

# 40. Machine Learning Training Architecture

The ML development pipeline should be separated from the prediction-serving workflow.

```text
Historical Data
      ↓
Data Cleaning
      ↓
Feature Engineering
      ↓
Training Dataset
      ↓
Train Baseline
      ↓
Train Candidate Model
      ↓
Evaluate
      ↓
Select Model
      ↓
Model Artifact
      ↓
Prediction Service
```

### Model retraining

The original PRD identifies model improvement as a future capability but does not define an automated retraining schedule.

Therefore:

**Automated continuous retraining:** **Out of current implementation scope unless separately approved.**

---

# 41. Model Versioning

Every generated prediction shall identify the model version where practical.

Example:

```text
model_version = TBD
```

### TBD — Versioning implementation

**Purpose:** Trace predictions back to the model used.

**Depends on:** Final ML deployment workflow.

**Decision required:** Establish a model-version naming and storage mechanism during implementation.

---

# 42. Non-Functional Requirements

The PRD establishes several non-functional requirements but does not provide numerical targets. Therefore, numerical values are deliberately left unresolved.

## 42.1 Performance

### Requirement

The dashboard should remain responsive at expected prototype scale.

### Status

**DECIDED qualitatively; quantitative target TBD.**

### TBD — API latency

**Purpose:** Define maximum acceptable response time for backend APIs.

**Depends on:** Dataset size, deployment environment and dashboard usage.

**Decision required:** Benchmark the deployed prototype and establish acceptable latency targets.

---

## 42.2 Prediction Latency

The system should process newly available data and produce predictions within a useful operational timeframe.

### Status

**Required, but numerical limit TBD.**

**Depends on:**

* upstream data update frequency;
* preprocessing time;
* model execution time;
* deployment environment.

**Decision required:** Establish an acceptable end-to-end prediction latency after a working pipeline exists.

---

# 43. Data Freshness

The system shall display when information was last updated.

The system must distinguish:

```text
Current
Stale
Unavailable
```

### TBD — Freshness threshold

**Purpose:** Determine when data should be considered stale.

**Depends on:** Actual update frequency of IMD/CWC/PMC data.

**Decision required:** Establish source-specific freshness thresholds after access is verified.

---

# 44. Scalability

The architecture shall be modular and cloud-ready, but the PRD does not establish a production-scale user count or geographic expansion requirement.

Therefore:

### Current requirement

Support the expected **Pune prototype workload**.

### Not established

* national deployment;
* multi-city deployment;
* millions of users;
* high-volume public alerting.

### TBD — Capacity

**Purpose:** Determine infrastructure requirements for actual deployment.

**Depends on:** Pilot user count, geographic resolution, API frequency and data volume.

**Decision required:** Define capacity targets if the project progresses beyond prototype stage.

---

# 45. Reliability

The system shall:

* detect unavailable data sources;
* identify stale data;
* preserve source timestamps;
* avoid silently using invalid inputs;
* maintain prediction timestamps;
* maintain model-version information where available.

### External dependency failure

Failure of one external data source should not automatically crash the entire dashboard.

However, the system must indicate which information is unavailable.

---

# 46. Security

The PRD establishes security as a system requirement but does not define a detailed security architecture.

The implementation shall protect:

* external API credentials, if required;
* administrative access;
* non-public datasets;
* system configuration;
* stored information.

### TBD — Authentication

**Purpose:** Determine how authorized users access protected functions.

**Depends on:** Whether the pilot requires authenticated municipal users.

**Decision required:** Define authentication mechanism before operational deployment.

### TBD — Authorization

**Purpose:** Control access to administrative/data-management functions.

**Depends on:** Final user roles and deployment context.

**Decision required:** Define role permissions if multiple operational user types require differentiated access.

---

# 47. Explainability Requirement

The system shall not present a flood-risk number without sufficient context.

A location-level prediction should expose:

```text
Risk Category
Risk Score
Prediction Timestamp
Major Risk Drivers
Data Freshness
```

Exact explainability implementation is **TBD** based on the selected model.

---

# 48. Auditability

The system should retain sufficient information to answer:

> **“Why did the system generate this prediction?”**

The prediction record should therefore be associated with:

* model version;
* prediction time;
* input-data timestamps;
* location;
* risk score;
* risk category.

The exact audit-retention period is **TBD**.

---

# 49. Deployment Setup

## 49.1 Deployment Requirement

The PRD specifies a **cloud-ready architecture** that can operate on cloud infrastructure or university infrastructure.

Therefore:

```text
React Frontend
       ↓
FastAPI Backend
       ↓
Python ML / Processing
       ↓
PostgreSQL + PostGIS
```

may be deployed within the selected infrastructure.

---

# 50. Containerization

### Status: TBD

The PRD does not explicitly commit to Docker or another container technology.

**Purpose:** Package application components consistently for deployment.

**Depends on:** Final deployment environment.

**Decision required:** Determine whether containerization is required after infrastructure is selected.

---

# 51. Orchestration

### Status: TBD

No orchestration platform is specified.

The TRD therefore does not require Kubernetes or another orchestration system.

**Purpose:** Manage multiple application instances if deployment scale requires it.

**Depends on:** Deployment scale and infrastructure.

**Decision required:** Determine whether orchestration is necessary beyond the prototype.

---

# 52. Cloud Provider

### Status: TBD

No AWS, Azure, GCP or other provider is selected.

**Purpose:** Host the application and supporting infrastructure.

**Depends on:** Institutional resources, cost and deployment requirements.

**Decision required:** Select infrastructure provider only when deployment requirements are known.

---

# 53. Deployment Environments

At minimum, the implementation should conceptually distinguish:

```text
Development
    ↓
Testing / Validation
    ↓
Prototype Deployment
```

Exact environment configuration is **TBD**.

---

# 54. Monitoring

The system shall expose sufficient information to determine:

* whether data ingestion is working;
* whether data are stale;
* whether predictions are being generated;
* whether backend requests are failing.

### TBD — Monitoring technology

**Purpose:** Observe application and data-pipeline health.

**Depends on:** Deployment environment and infrastructure.

**Decision required:** Select monitoring/logging tooling when deployment infrastructure is chosen.

The PRD does **not** mandate Prometheus, Grafana, ELK or another monitoring platform, so none is specified here.

---

# 55. Logging

The application should record operational events necessary for debugging and traceability.

Relevant events include:

* ingestion attempt;
* ingestion success/failure;
* data validation failure;
* model execution;
* prediction generation;
* API failure.

Sensitive credentials and protected information shall not be written into logs.

---

# 56. Data Failure Behaviour

The system shall explicitly handle:

### IMD unavailable

```text
IMD unavailable
     ↓
Source status = unavailable
     ↓
Assess whether required model inputs remain available
     ↓
Generate prediction OR withhold prediction
     ↓
Display warning
```

The final fallback strategy is **TBD**.

---

### PMC GIS unavailable

The MVP must remain capable of operating without PMC drainage GIS because the PRD explicitly treats access as conditional.

The system can continue using available:

* rainfall information;
* historical hotspots;
* other available spatial information.

---

### CWC unavailable

CWC information is contextual and should not automatically make the urban flood-risk system unusable unless the final model depends on it.

The exact dependency will be determined after feature selection.

---

# 57. Edge-Case Technical Requirements

## 57.1 New Flood Location

A location absent from the historical hotspot database must still be capable of receiving a prediction if sufficient model features are available.

This prevents the system from becoming merely a static hotspot lookup service.

---

## 57.2 Historical Hotspot No Longer Vulnerable

Historical status must remain distinguishable from current predicted risk.

The database should therefore preserve:

```text
historical_hotspot = TRUE
current_risk = model-derived value
```

rather than permanently equating the two.

---

## 57.3 Extreme Out-of-Distribution Rainfall

If input conditions are materially outside the training data:

* prediction reliability should be treated cautiously;
* uncertainty should be surfaced where technically supported;
* the system should avoid implying certainty.

The exact out-of-distribution detection method is **TBD**.

---

# 58. Data-to-Decision End-to-End Flow

The complete MVP technical workflow is:

```text
                IMD
        Rainfall / Forecast
                │
                ↓
                ┐
CWC ────────────┤
Hydrological    │
                │
PMC ────────────┤
Hotspots        │
                │
GIS ────────────┘
                ↓
       DATA INGESTION
                ↓
       DATA VALIDATION
                ↓
    SPATIAL/TEMPORAL ALIGNMENT
                ↓
       FEATURE ENGINEERING
                ↓
         ML RISK MODEL
                ↓
         RISK SCORE
                ↓
      LOW/MODERATE/HIGH/
           CRITICAL
                ↓
      HOTSPOT PRIORITIZATION
                ↓
          GIS DASHBOARD
                ↓
       HUMAN DECISION
```

This is the core system that should be implemented before any future expansion.

---

# 59. Future Technical Scope

The PRD defines several future iterations. They should remain architecturally possible but should **not be treated as MVP requirements**.

## Phase 2

Potentially:

* incident reporting;
* field-team status;
* prediction-versus-observation analysis;
* road-risk prioritization;
* response tracking;
* improved drainage intelligence.

## Phase 3

Potentially:

* citizen-facing flood-risk information;
* location-based notifications;
* travel advisories;
* multilingual alerts;
* accessibility improvements.

## Phase 4

Potentially:

* higher-resolution spatial modelling;
* satellite-derived flood indicators;
* CCTV/computer vision;
* hydrodynamic modelling;
* advanced temporal/deep-learning approaches.

## Phase 5

Potentially:

* advanced emergency-resource optimization.

These phases must not be allowed to alter the MVP architecture or acceptance criteria until separately approved.

---

# 60. Explicitly Excluded Technical Components

The following shall **not** be implemented as part of this TRD's MVP:

### Hazard models

* heatwave prediction;
* drought prediction;
* cyclone prediction;
* multi-hazard modelling.

### AI models

* health-risk prediction;
* broad demographic vulnerability modelling;
* infrastructure-damage prediction;
* autonomous resource optimization.

### Infrastructure simulation

* full city-wide hydrodynamic simulation;
* automated pump control;
* autonomous drainage control.

### Emergency operations

* autonomous evacuation decisions;
* autonomous road closures;
* autonomous emergency dispatch.

### External systems

* replacement of IMD forecasting;
* replacement of CWC flood forecasting;
* replacement of PMC emergency-management systems.

### Public communication infrastructure

* production emergency SMS system;
* production WhatsApp emergency system;
* official government emergency-warning authority.

---

# 61. Technical Acceptance Criteria for the MVP

The MVP should be considered technically complete when the following end-to-end workflow works using whatever real datasets are successfully obtained:

### AC-01 — Data ingestion

The system can ingest at least the available required source data through normalized adapters.

### AC-02 — Data validation

The system detects and flags missing, stale or invalid data.

### AC-03 — Spatial integration

Available rainfall, hotspot and spatial data can be associated with the selected geographic unit.

### AC-04 — ML training

At least one baseline model can be trained if sufficient historical labelled data exist.

### AC-05 — Model evaluation

Candidate model performance can be compared using the evaluation methodology selected after dataset analysis.

### AC-06 — Risk prediction

The system produces a location-level risk score/category.

### AC-07 — Prioritization

The system produces an ordered list of higher-risk locations.

### AC-08 — GIS visualization

Predicted risk can be displayed spatially.

### AC-09 — Explainability

The system presents the available risk drivers or explanation associated with a prediction.

### AC-10 — Data transparency

Users can see prediction and data timestamps.

### AC-11 — Failure handling

Unavailable or stale data are visibly identified rather than silently treated as normal conditions.

### AC-12 — Traceability

Predictions can be associated with the model version and input-data timestamps where those mechanisms have been implemented.

---

# 62. TBD Decision Register

This section is deliberately important. These are **not missing requirements to be guessed later**; they are unresolved technical decisions explicitly inherited from the conceptual status of the PRD.

| TBD                        | What it defines                         | Depends on                | Decision required                     |
| -------------------------- | --------------------------------------- | ------------------------- | ------------------------------------- |
| Prediction horizon         | How far ahead risk is predicted         | IMD + historical data     | Select useful horizon                 |
| Spatial unit               | Geographic prediction granularity       | GIS/data resolution       | Select hotspot/grid/ward/etc.         |
| Target label               | What constitutes a positive flood event | Historical flood data     | Define training target                |
| Final feature set          | Variables entering model                | Dataset availability      | Select validated features             |
| Final ML model             | Production prediction algorithm         | Model evaluation          | Select empirically                    |
| ML hyperparameters         | Training configuration                  | Dataset/model             | Tune during validation                |
| Risk thresholds            | Score → risk category                   | Model outputs             | Establish validation-based thresholds |
| Confidence method          | Prediction uncertainty                  | Final model               | Select supported approach             |
| Explainability method      | Risk-driver generation                  | Final model               | Select compatible method              |
| Upstream API contracts     | Actual source interfaces                | Provider access           | Verify endpoints/auth/schema          |
| API update frequency       | Refresh schedule                        | Provider behaviour        | Determine from source                 |
| Data freshness thresholds  | Stale-data definition                   | Source update frequency   | Define per source                     |
| Spatial reference system   | GIS coordinate standard                 | GIS datasets              | Select after data inspection          |
| GIS layer inventory        | Available spatial features              | PMC access                | Confirm accessible layers             |
| Historical event structure | Training-data granularity               | PMC data access           | Determine available event detail      |
| Database retention         | How long data remain stored             | Data policy/resources     | Define retention policy               |
| API latency target         | Maximum response time                   | Deployment benchmark      | Establish benchmark target            |
| Prediction latency target  | End-to-end processing limit             | Pipeline benchmark        | Establish operational target          |
| Prototype capacity         | Users/requests/data volume              | Deployment scenario       | Define if needed                      |
| Authentication             | User access mechanism                   | Deployment users          | Select if protected access needed     |
| Authorization              | Role permissions                        | User roles                | Define operational permissions        |
| Containerization           | Packaging method                        | Deployment environment    | Decide if needed                      |
| Orchestration              | Multi-service management                | Deployment scale          | Decide if needed                      |
| Cloud provider             | Hosting environment                     | Institutional constraints | Select provider if applicable         |
| Monitoring tooling         | Infrastructure observability            | Deployment environment    | Select tooling                        |

---

# 63. Final Technical Boundary

The implementation target can therefore be reduced to one precise technical statement:

> **Build a modular Pune-focused system that ingests available IMD rainfall/forecast/nowcast data, relevant CWC hydrological information, PMC historical waterlogging hotspots and accessible GIS data; normalizes and spatially aligns those inputs; generates an AI-based urban flood-risk prediction; ranks locations by risk; and exposes the result through a React GIS decision-support dashboard backed by Python/FastAPI and PostgreSQL/PostGIS.**

The most important architectural principle is:

```text
Existing Government Data
          ↓
     Our Integration
          ↓
     Our AI Layer
          ↓
   Risk Prioritization
          ↓
    Decision Support
```

**Not:**

```text
Build a new weather service
+ Build a new flood authority
+ Build a hydrodynamic simulator
+ Build a health platform
+ Build a resource-management system
+ Build a citizen emergency network
```

The former is technically aligned with the PRD and realistically prototypeable. The latter would violate the deliberate product boundary.

The original project material already establishes that final model selection and technology choices depend on dataset availability and research analysis, and that the flood scenario requires validation against real-world data.   The TRD therefore keeps those unresolved decisions explicitly visible rather than manufacturing false technical certainty.

**Recommended implementation sequence:**
**data access → data schema validation → historical-event dataset creation → baseline model → XGBoost comparison → spatial integration → prediction API → hotspot ranking → React GIS dashboard → retrospective validation.**
