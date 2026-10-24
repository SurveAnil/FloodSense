import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.models import MODEL_VERSION
from app.services.dashboard import DashboardService


def database_path() -> Path:
    configured = os.getenv("FLOODSENSE_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "data" / "floodsense.sqlite3"


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize_database() -> None:
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN (
                        'CITIZEN',
                        'FIELD_RESPONSE_PLANNING',
                        'DISASTER_MANAGEMENT_ADMIN'
                    )
                ),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                is_demo INTEGER NOT NULL DEFAULT 0 CHECK (is_demo IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                revoked_at TEXT
            );
            CREATE INDEX IF NOT EXISTS sessions_user_id ON sessions(user_id);
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                area TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                historical_hotspot INTEGER NOT NULL CHECK (historical_hotspot IN (0, 1)),
                source_name TEXT NOT NULL,
                source_reference TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS demo_location_contexts (
                location_id TEXT PRIMARY KEY REFERENCES locations(id) ON DELETE CASCADE,
                citizen_report_count INTEGER NOT NULL CHECK (citizen_report_count >= 0),
                context_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS risk_predictions (
                id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL REFERENCES locations(id),
                score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
                risk_category TEXT NOT NULL CHECK (
                    risk_category IN ('Low', 'Moderate', 'High', 'Critical')
                ),
                updated_at TEXT NOT NULL,
                prediction_time TEXT NOT NULL,
                current_rainfall TEXT NOT NULL,
                forecast_rainfall TEXT NOT NULL,
                drivers_json TEXT NOT NULL,
                feature_explanations_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                data_mode TEXT NOT NULL CHECK (data_mode IN ('replay', 'live', 'unknown')),
                model_version TEXT NOT NULL,
                UNIQUE (location_id, prediction_time, model_version)
            );
            CREATE INDEX IF NOT EXISTS risk_predictions_rank
                ON risk_predictions(score DESC, location_id);
            CREATE TABLE IF NOT EXISTS data_sources (
                name TEXT PRIMARY KEY CHECK (name IN ('IMD', 'CWC', 'PMC', 'GIS')),
                source_type TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('Available', 'Stale', 'Unavailable')),
                last_updated TEXT NOT NULL,
                detail TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                actor_user_id TEXT REFERENCES users(id),
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS audit_logs_created_at ON audit_logs(created_at);
            CREATE TABLE IF NOT EXISTS citizen_reports (
                id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL REFERENCES users(id),
                location_id TEXT REFERENCES locations(id),
                location_name TEXT NOT NULL,
                area TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                category TEXT NOT NULL CHECK (
                    category IN ('WATERLOGGING', 'FLOODING', 'BLOCKED_DRAINAGE', 'OVERFLOW', 'OTHER')
                ),
                description TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'PENDING_VERIFICATION', 'VERIFIED', 'NOT_VERIFIED',
                        'NEEDS_INFORMATION', 'APPROVED', 'REJECTED'
                    )
                ),
                submitted_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS citizen_reports_status
                ON citizen_reports(status, submitted_at);
            CREATE INDEX IF NOT EXISTS citizen_reports_reporter
                ON citizen_reports(reporter_id, submitted_at DESC);
            CREATE TABLE IF NOT EXISTS field_reports (
                id TEXT PRIMARY KEY,
                author_user_id TEXT NOT NULL REFERENCES users(id),
                location_id TEXT REFERENCES locations(id),
                location_name TEXT NOT NULL,
                area TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                prediction_id TEXT REFERENCES risk_predictions(id),
                citizen_report_id TEXT REFERENCES citizen_reports(id),
                category TEXT NOT NULL CHECK (
                    category IN ('WATERLOGGING', 'FLOODING', 'BLOCKED_DRAINAGE', 'OVERFLOW', 'OTHER')
                ),
                description TEXT NOT NULL,
                observed_condition TEXT NOT NULL,
                outcome TEXT NOT NULL CHECK (outcome IN ('PROBLEM_FOUND', 'INSPECTED_NO_PROBLEM_FOUND')),
                severity TEXT CHECK (severity IS NULL OR severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
                status TEXT NOT NULL CHECK (
                    status IN ('PENDING_REVIEW', 'NEEDS_INFORMATION', 'APPROVED', 'REJECTED')
                ),
                observed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS field_reports_review
                ON field_reports(status, observed_at);
            CREATE TABLE IF NOT EXISTS field_verifications (
                id TEXT PRIMARY KEY,
                citizen_report_id TEXT NOT NULL REFERENCES citizen_reports(id),
                verifier_user_id TEXT NOT NULL REFERENCES users(id),
                outcome TEXT NOT NULL CHECK (outcome IN ('VERIFIED', 'NOT_VERIFIED')),
                observed_condition TEXT NOT NULL,
                severity TEXT CHECK (severity IS NULL OR severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
                notes TEXT NOT NULL,
                verified_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS field_verifications_report
                ON field_verifications(citizen_report_id, verified_at DESC);
            CREATE TABLE IF NOT EXISTS attachments (
                id TEXT PRIMARY KEY,
                uploader_user_id TEXT NOT NULL REFERENCES users(id),
                citizen_report_id TEXT REFERENCES citizen_reports(id),
                field_report_id TEXT REFERENCES field_reports(id),
                field_verification_id TEXT REFERENCES field_verifications(id),
                file_name TEXT NOT NULL,
                content_type TEXT NOT NULL CHECK (
                    content_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')
                ),
                size_bytes INTEGER NOT NULL CHECK (size_bytes BETWEEN 1 AND 5242880),
                sha256 TEXT NOT NULL,
                content BLOB NOT NULL,
                uploaded_at TEXT NOT NULL,
                CHECK (
                    (citizen_report_id IS NOT NULL) +
                    (field_report_id IS NOT NULL) +
                    (field_verification_id IS NOT NULL) = 1
                )
            );
            CREATE INDEX IF NOT EXISTS attachments_citizen_report
                ON attachments(citizen_report_id);
            CREATE INDEX IF NOT EXISTS attachments_field_report
                ON attachments(field_report_id);
            CREATE INDEX IF NOT EXISTS attachments_field_verification
                ON attachments(field_verification_id);
            CREATE TABLE IF NOT EXISTS report_reviews (
                id TEXT PRIMARY KEY,
                reviewer_user_id TEXT NOT NULL REFERENCES users(id),
                citizen_report_id TEXT REFERENCES citizen_reports(id),
                field_report_id TEXT REFERENCES field_reports(id),
                decision TEXT NOT NULL CHECK (
                    decision IN ('REQUEST_INFORMATION', 'APPROVE', 'REJECT')
                ),
                requested_information TEXT NOT NULL DEFAULT '',
                severity TEXT CHECK (severity IS NULL OR severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
                reviewed_at TEXT NOT NULL,
                CHECK (
                    (citizen_report_id IS NOT NULL) +
                    (field_report_id IS NOT NULL) = 1
                )
            );
            CREATE INDEX IF NOT EXISTS report_reviews_citizen
                ON report_reviews(citizen_report_id, reviewed_at DESC);
            CREATE INDEX IF NOT EXISTS report_reviews_field
                ON report_reviews(field_report_id, reviewed_at DESC);
            CREATE TABLE IF NOT EXISTS flood_problems (
                id TEXT PRIMARY KEY,
                citizen_report_id TEXT UNIQUE REFERENCES citizen_reports(id),
                field_report_id TEXT UNIQUE REFERENCES field_reports(id),
                severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
                status TEXT NOT NULL CHECK (status = 'OPEN'),
                approved_by_user_id TEXT NOT NULL REFERENCES users(id),
                approved_at TEXT NOT NULL,
                CHECK (
                    (citizen_report_id IS NOT NULL) +
                    (field_report_id IS NOT NULL) = 1
                )
            );
            CREATE INDEX IF NOT EXISTS flood_problems_approved
                ON flood_problems(approved_at DESC);
            CREATE TABLE IF NOT EXISTS response_tasks (
                id TEXT PRIMARY KEY,
                flood_problem_id TEXT NOT NULL REFERENCES flood_problems(id),
                instruction TEXT NOT NULL,
                details TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
                assigned_user_id TEXT NOT NULL REFERENCES users(id),
                due_at TEXT,
                status TEXT NOT NULL CHECK (
                    status IN ('ASSIGNED', 'ACCEPTED', 'EN_ROUTE', 'INSPECTED', 'ACTION_REQUIRED', 'RESOLVED')
                ),
                completion_status TEXT NOT NULL DEFAULT 'NOT_SUBMITTED' CHECK (
                    completion_status IN ('NOT_SUBMITTED', 'PENDING_REVIEW', 'APPROVED', 'RETURNED')
                ),
                created_by_user_id TEXT NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS response_tasks_assignee
                ON response_tasks(assigned_user_id, status, updated_at DESC);
            CREATE INDEX IF NOT EXISTS response_tasks_problem
                ON response_tasks(flood_problem_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS task_updates (
                id TEXT PRIMARY KEY,
                response_task_id TEXT NOT NULL REFERENCES response_tasks(id),
                actor_user_id TEXT NOT NULL REFERENCES users(id),
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                condition TEXT NOT NULL,
                internal_notes TEXT NOT NULL,
                blockers TEXT NOT NULL,
                completion_decision TEXT CHECK (
                    completion_decision IS NULL OR completion_decision IN ('APPROVE', 'RETURN_FOR_ACTION')
                ),
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS task_updates_task
                ON task_updates(response_task_id, created_at, id);
            CREATE TABLE IF NOT EXISTS task_evidence (
                id TEXT PRIMARY KEY,
                task_update_id TEXT NOT NULL REFERENCES task_updates(id),
                uploader_user_id TEXT NOT NULL REFERENCES users(id),
                file_name TEXT NOT NULL,
                content_type TEXT NOT NULL CHECK (
                    content_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')
                ),
                size_bytes INTEGER NOT NULL CHECK (size_bytes BETWEEN 1 AND 5242880),
                sha256 TEXT NOT NULL,
                content BLOB NOT NULL,
                uploaded_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS task_evidence_update
                ON task_evidence(task_update_id);
            CREATE TABLE IF NOT EXISTS public_status_updates (
                id TEXT PRIMARY KEY,
                flood_problem_id TEXT NOT NULL REFERENCES flood_problems(id),
                citizen_report_id TEXT NOT NULL REFERENCES citizen_reports(id),
                response_task_id TEXT REFERENCES response_tasks(id),
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                published_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS public_status_report
                ON public_status_updates(citizen_report_id, published_at, id);
            """
        )
        user_columns = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "updated_at" not in user_columns:
            db.execute("ALTER TABLE users ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
            db.execute("UPDATE users SET updated_at = created_at WHERE updated_at = ''")
        location_columns = {row["name"] for row in db.execute("PRAGMA table_info(locations)").fetchall()}
        if "source_name" not in location_columns:
            db.execute("ALTER TABLE locations ADD COLUMN source_name TEXT NOT NULL DEFAULT 'REPLAY'")
        if "source_reference" not in location_columns:
            db.execute("ALTER TABLE locations ADD COLUMN source_reference TEXT NOT NULL DEFAULT ''")
            db.execute("UPDATE locations SET source_reference = id WHERE source_reference = ''")
        prediction_columns = {row["name"] for row in db.execute("PRAGMA table_info(risk_predictions)").fetchall()}
        if "feature_explanations_json" not in prediction_columns:
            db.execute("ALTER TABLE risk_predictions ADD COLUMN feature_explanations_json TEXT NOT NULL DEFAULT '[]'")
        if "created_at" not in prediction_columns:
            db.execute("ALTER TABLE risk_predictions ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
            db.execute(
                "UPDATE risk_predictions SET created_at = ? WHERE created_at = ''",
                (utc_now(),),
            )
        _seed_risk_snapshot(db)


def _seed_risk_snapshot(db: sqlite3.Connection) -> None:
    service = DashboardService()
    records = {record["id"]: record for record in service.adapter.locations()}
    for prediction in service._locations():
        record = records[prediction.id]
        demo_scenario = record.get("demoScenario")
        model_version = prediction.model_version or MODEL_VERSION
        feature_explanations = [] if demo_scenario else service.model.explain(record)
        db.execute(
            """
            INSERT INTO locations
                (id, name, area, latitude, longitude, historical_hotspot, source_name, source_reference)
            VALUES (?, ?, ?, ?, ?, ?, 'REPLAY', ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                area = excluded.area,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                historical_hotspot = excluded.historical_hotspot,
                source_name = excluded.source_name,
                source_reference = excluded.source_reference
            """,
            (
                prediction.id,
                prediction.name,
                prediction.area,
                prediction.coordinates[0],
                prediction.coordinates[1],
                int(prediction.historical_hotspot),
                record["id"],
            ),
        )
        db.execute(
            """
            INSERT OR IGNORE INTO risk_predictions
                (id, location_id, score, risk_category, updated_at, prediction_time,
                 current_rainfall, forecast_rainfall, drivers_json, feature_explanations_json,
                 created_at, data_mode, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'replay', ?)
            """,
            (
                str(uuid.uuid5(uuid.NAMESPACE_URL, f"{prediction.id}:{prediction.prediction_time}:{model_version}")),
                prediction.id,
                prediction.score,
                prediction.risk,
                prediction.updated_at,
                prediction.prediction_time,
                prediction.current_rainfall,
                prediction.forecast_rainfall,
                json.dumps(prediction.drivers),
                json.dumps(feature_explanations),
                utc_now(),
                model_version,
            ),
        )
        if demo_scenario:
            db.execute(
                """
                INSERT INTO demo_location_contexts (location_id, citizen_report_count, context_json)
                VALUES (?, ?, ?)
                ON CONFLICT(location_id) DO UPDATE SET
                    citizen_report_count = excluded.citizen_report_count,
                    context_json = excluded.context_json
                """,
                (
                    prediction.id,
                    demo_scenario["citizenReportCount"],
                    json.dumps(demo_scenario),
                ),
            )
    for source in service.source_status().sources:
        db.execute(
            """
            INSERT INTO data_sources
                (name, source_type, state, last_updated, detail)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                source_type = excluded.source_type,
                state = excluded.state,
                last_updated = excluded.last_updated,
                detail = excluded.detail
            """,
            (source.name, service._source_type(source.name), source.state, source.last_updated, source.detail),
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_audit(
    db: sqlite3.Connection,
    *,
    actor_user_id: str | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: dict[str, object] | None = None,
) -> None:
    db.execute(
        """
        INSERT INTO audit_logs
            (id, actor_user_id, action, target_type, target_id, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            actor_user_id,
            action,
            target_type,
            target_id,
            json.dumps(details or {}),
            utc_now(),
        ),
    )
