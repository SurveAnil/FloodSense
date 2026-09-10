# FloodSense

## AI-Based Urban Flood Risk Forecasting for Pune

FloodSense is a proposed AI-driven urban flood-risk intelligence system for Pune, Maharashtra. It combines rainfall and forecast information with historical waterlogging hotspots and available spatial or drainage data to estimate where disruptive urban flooding is most likely and help response teams prioritize action.

The project is designed as an intelligence layer over existing systems such as IMD, CWC, and PMC data. It does not replace official weather, hydrological, or emergency-warning services.

## Problem

During intense rainfall, Pune can experience localized flooding and waterlogging that disrupt roads, transport, public services, and emergency access. Decision-makers need more than a broad rainfall warning: they need to know which locations are most likely to be affected and which locations should receive attention first.

## Proposed workflow

```text
Data ingestion
    -> Validation and normalization
    -> Spatio-temporal feature engineering
    -> AI flood-risk prediction
    -> Hotspot prioritization
    -> GIS decision-support dashboard
```

The system is expected to integrate:

- IMD rainfall observations, forecasts, and nowcasts
- CWC hydrological or flood information where relevant
- PMC historical waterlogging and flood-prone locations
- GIS, terrain, drainage, and urban spatial data where accessible

## Intended users

- Municipal disaster-management officers
- Field-response and drainage-maintenance teams
- Traffic-management teams
- Emergency coordinators

## Product output

- Location-specific flood-risk scores
- Risk categories and ranked hotspots
- Risk-driver explanations
- Map-based visualization of predicted risk, observed rainfall, and historical hotspots
- Data freshness and source-status indicators

Risk predictions are decision-support outputs, not guarantees of flooding or official emergency declarations.

## Project status

FloodSense is currently at the conceptual and pre-MVP stage. The datasets, spatial unit, prediction horizon, final model, and operational performance targets remain subject to validation and availability of real-world data.

## Documentation

- [Product Requirements Document](https://github.com/SurveAnil/FloodSense/blob/master/PRD.md)
- [Technical Requirements Document](https://github.com/SurveAnil/FloodSense/blob/master/TRD.md)
- [Design Brief](https://github.com/SurveAnil/FloodSense/blob/master/Design.md)
- [Project Report](https://github.com/SurveAnil/FloodSense/blob/master/Project_Report.md)
- [Audit Baseline](https://github.com/SurveAnil/FloodSense/blob/master/AUDIT_BASELINE.md)

## Scope

The initial scope is deliberately focused on urban flooding caused by extreme rainfall in Pune:

> Data → Risk intelligence → Location prioritization → Action

The project does not attempt to rebuild weather forecasting infrastructure, replace existing government warning systems, or provide a generic multi-hazard platform.
