import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from app.models import (
    RiskAnalyticsLocation,
    RiskAnalyticsResponse,
    RiskAnalyticsSummary,
    RiskObservationAnalytics,
    RiskPredictionHistoryItem,
)

EVALUATION_NOTICE = (
    "These are descriptive records, not an evaluation dataset. No model accuracy, "
    "precision, recall, or causal effect is calculated."
)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        match = re.match(
            r"(\d{1,2} [A-Za-z]{3} \d{4}), \d{2}:\d{2}-(\d{2}:\d{2}) IST",
            value,
        )
        if not match:
            return None
        try:
            return datetime.strptime(
                f"{match.group(1)} {match.group(2)} +0530", "%d %b %Y %H:%M %z"
            ).astimezone(timezone.utc)
        except ValueError:
            return None


def _observation_rows(db: sqlite3.Connection) -> list[dict[str, object]]:
    fields = db.execute(
        """
        SELECT COALESCE(f.location_id, p.location_id) AS location_id,
               f.prediction_id AS linked_prediction_id,
               f.outcome, f.observed_at, f.status AS review_status,
               'FIELD_REPORT' AS source_type
        FROM field_reports f
        LEFT JOIN risk_predictions p ON p.id = f.prediction_id
        WHERE COALESCE(f.location_id, p.location_id) IS NOT NULL
        """
    ).fetchall()
    verifications = db.execute(
        """
        SELECT c.location_id, NULL AS linked_prediction_id, v.outcome,
               v.verified_at AS observed_at, c.status AS review_status,
               'FIELD_VERIFICATION' AS source_type
        FROM field_verifications v
        JOIN citizen_reports c ON c.id = v.citizen_report_id
        WHERE c.location_id IS NOT NULL
        """
    ).fetchall()
    return [dict(row) for row in fields + verifications]


def risk_observation_analytics(
    db: sqlite3.Connection,
    *,
    public_only: bool,
) -> RiskAnalyticsResponse:
    locations = db.execute(
        "SELECT id, name, area, historical_hotspot FROM locations ORDER BY name, id"
    ).fetchall()
    prediction_rows = db.execute(
        """
        SELECT id, location_id, score, risk_category, prediction_time,
               created_at, model_version, data_mode
        FROM risk_predictions ORDER BY created_at, rowid
        """
    ).fetchall()
    predictions: dict[str, list[RiskPredictionHistoryItem]] = {}
    parsed_windows: dict[str, datetime | None] = {}
    for row in prediction_rows:
        prediction = RiskPredictionHistoryItem(
            id=row["id"],
            score=row["score"],
            risk_category=row["risk_category"],
            prediction_time=row["prediction_time"],
            created_at=row["created_at"],
            model_version=row["model_version"],
            data_mode=row["data_mode"],
        )
        predictions.setdefault(row["location_id"], []).append(prediction)
        parsed_windows[row["id"]] = _parse_timestamp(row["prediction_time"])

    observations_by_location: dict[str, list[RiskObservationAnalytics]] = {}
    raw_observations_by_location: dict[str, list[dict[str, object]]] = {}
    all_observations = _observation_rows(db)
    for row in all_observations:
        location_id = str(row["location_id"])
        raw_observations_by_location.setdefault(location_id, []).append(row)
        if public_only:
            continue
        observations_by_location.setdefault(location_id, []).append(
            RiskObservationAnalytics(
                source_type=row["source_type"],
                outcome=row["outcome"],
                observed_at=row["observed_at"],
                review_status=row["review_status"],
                linked_prediction_id=row["linked_prediction_id"],
            )
        )

    approved_rows = db.execute(
        """
        SELECT COALESCE(c.location_id, f.location_id, p.location_id) AS location_id,
               COUNT(*) AS count
        FROM flood_problems fp
        LEFT JOIN citizen_reports c ON c.id = fp.citizen_report_id
        LEFT JOIN field_reports f ON f.id = fp.field_report_id
        LEFT JOIN risk_predictions p ON p.id = f.prediction_id
        WHERE COALESCE(c.location_id, f.location_id, p.location_id) IS NOT NULL
        GROUP BY COALESCE(c.location_id, f.location_id, p.location_id)
        """
    ).fetchall()
    approved_by_location = {row["location_id"]: row["count"] for row in approved_rows}

    high_with_problem = 0
    high_with_no_problem = 0
    high_without_inspection = 0
    lower_with_problem = 0
    field_problem_findings = 0
    no_problem_inspections = 0
    verified_citizen_findings = 0
    not_verified_citizen_reports = 0
    for row in all_observations:
        if row["source_type"] == "FIELD_REPORT":
            if row["outcome"] == "PROBLEM_FOUND":
                field_problem_findings += 1
            elif row["outcome"] == "INSPECTED_NO_PROBLEM_FOUND":
                no_problem_inspections += 1
        elif row["outcome"] == "VERIFIED":
            verified_citizen_findings += 1
        elif row["outcome"] == "NOT_VERIFIED":
            not_verified_citizen_reports += 1

    location_results: list[RiskAnalyticsLocation] = []
    prediction_count = 0
    current_high_risk = 0
    hotspot_count = 0
    all_prediction_dates: list[datetime] = []
    for location in locations:
        location_id = location["id"]
        history = predictions.get(location_id, [])
        prediction_count += len(history)
        if history:
            current_high_risk += history[-1].risk_category in {"High", "Critical"}
            all_prediction_dates.extend(
                parsed for prediction in history
                if (parsed := parsed_windows.get(prediction.id)) is not None
            )
        hotspot = bool(location["historical_hotspot"])
        hotspot_count += hotspot
        observations = raw_observations_by_location.get(location_id, [])
        matched_by_prediction: dict[str, set[str]] = {}
        for observation in observations:
            observed_at = _parse_timestamp(str(observation["observed_at"]))
            linked_id = observation["linked_prediction_id"]
            matching_predictions = (
                [prediction for prediction in history if prediction.id == linked_id]
                if linked_id
                else history
            )
            for prediction in matching_predictions:
                prediction_time = parsed_windows.get(prediction.id)
                if observed_at is None or prediction_time is None or observed_at < prediction_time:
                    continue
                outcomes = matched_by_prediction.setdefault(prediction.id, set())
                if observation["source_type"] == "FIELD_REPORT":
                    if observation["outcome"] == "PROBLEM_FOUND":
                        outcomes.add("PROBLEM_FOUND")
                    elif observation["outcome"] == "INSPECTED_NO_PROBLEM_FOUND":
                        outcomes.add("NO_PROBLEM_FOUND")
                elif observation["outcome"] == "VERIFIED":
                    outcomes.add("PROBLEM_FOUND")
                elif observation["outcome"] == "NOT_VERIFIED":
                    outcomes.add("NO_PROBLEM_FOUND")
        for prediction in history:
            outcomes = matched_by_prediction.get(prediction.id, set())
            high_risk = prediction.risk_category in {"High", "Critical"}
            if "PROBLEM_FOUND" in outcomes:
                if high_risk:
                    high_with_problem += 1
                else:
                    lower_with_problem += 1
            elif "NO_PROBLEM_FOUND" in outcomes and high_risk:
                high_with_no_problem += 1
            elif high_risk:
                high_without_inspection += 1

        public_problem_count = approved_by_location.get(location_id, 0)
        location_results.append(
            RiskAnalyticsLocation(
                location_id=location_id,
                name=location["name"],
                area=location["area"],
                historical_hotspot_reference=hotspot,
                latest_prediction=history[-1] if history else None,
                prediction_history=history,
                observation_history=observations_by_location.get(location_id, []),
                officially_approved_problem_count=public_problem_count,
            )
        )
    models = sorted({item["model_version"] for item in prediction_rows})
    data_modes = {item["data_mode"] for item in prediction_rows}
    data_mode = (
        "live" if data_modes == {"live"}
        else "replay" if data_modes and data_modes <= {"replay"}
        else "unknown"
    )
    return RiskAnalyticsResponse(
        summary=RiskAnalyticsSummary(
            data_mode=data_mode,
            model_versions=models,
            prediction_snapshots=prediction_count,
            latest_snapshot_high_risk_locations=current_high_risk,
            historical_hotspot_references=hotspot_count,
            field_problem_findings=0 if public_only else field_problem_findings,
            no_problem_inspections=0 if public_only else no_problem_inspections,
            verified_citizen_report_findings=0 if public_only else verified_citizen_findings,
            not_verified_citizen_reports=0 if public_only else not_verified_citizen_reports,
            officially_approved_problems=sum(approved_by_location.values()),
            high_risk_with_problem_observation=0 if public_only else high_with_problem,
            high_risk_with_no_problem_inspection=0 if public_only else high_with_no_problem,
            high_risk_without_matching_inspection=0 if public_only else high_without_inspection,
            lower_risk_with_problem_observation=0 if public_only else lower_with_problem,
            period_start=min(all_prediction_dates).isoformat() if all_prediction_dates else None,
            period_end=max(all_prediction_dates).isoformat() if all_prediction_dates else None,
            evaluation_notice=EVALUATION_NOTICE,
        ),
        locations=location_results,
    )
