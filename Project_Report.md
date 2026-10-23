# Project Report

## Overview

FloodSense in this repository is a Pune flood-risk decision-support application.
Its current Phase 1 slice provides a shared authenticated risk dashboard for
three roles using local replay data and persisted SQLite risk records.

## Current state

The repository contains:

- a React + Vite + TypeScript frontend
- an optional frontend mock fallback in `src/mock-data/pune.ts`
- a backend replay snapshot in `backend/data/pune_replay.json`
- dashboard, priorities, map, and location-detail interactions
- source-status panels for IMD, CWC, PMC, and GIS
- backend-derived account roles, session authentication, and admin account
  provisioning
- persisted locations, risk predictions, source status, and audit events

## What is implemented

- city-level flood-risk overview
- hotspot ranking and selection
- location detail for a selected hotspot
- rainfall context and driver explanation
- source availability and freshness indicators
- demo data mode with explicit label to avoid claiming official warnings
- shared sign-in for `CITIZEN`, `FIELD_RESPONSE_PLANNING`, and
  `DISASTER_MANAGEMENT_ADMIN`

## What is not implemented

- live weather or hydrology integrations
- validated ML model training or operational inference
- official alerting or emergency communication
- citizen reporting, field verification, and independent FieldReports
- admin review and official FloodProblem lifecycle
- ResponseTask assignment, field response updates, and citizen-visible status
- deployment and monitoring for production operations
- GIS layer integration beyond demo display patterns

## Assessment

The repository remains a replay-based decision-support system, not a
production-grade forecasting or emergency platform. Risk outputs are demo
predictions; the remaining operational workflows are planned in
`IMPLEMENTATION_PLAN.md`.
