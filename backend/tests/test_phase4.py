import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.auth import Role, create_session, provision_user
from app.database import connection, initialize_database
from app.ml.risk_model import RiskModel
from app.main import app
from app.services.analytics import risk_observation_analytics


class PhaseFourAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = os.environ.get("FLOODSENSE_DB_PATH")
        os.environ["FLOODSENSE_DB_PATH"] = str(Path(cls.temp_dir.name) / "phase4.sqlite3")
        initialize_database()
        cls.field_user = provision_user(
            email="phase4-field@example.test",
            password="correct horse battery staple",
            role=Role.FIELD_RESPONSE_PLANNING,
            actor=None,
        )
        cls.citizen_user = provision_user(
            email="phase4-citizen@example.test",
            password="correct horse battery staple",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.other_citizen_user = provision_user(
            email="phase4-other-citizen@example.test",
            password="correct horse battery staple",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.admin_user = provision_user(
            email="phase4-admin@example.test",
            password="correct horse battery staple",
            role=Role.DISASTER_MANAGEMENT_ADMIN,
            actor=None,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()
        if cls.original_db_path is None:
            os.environ.pop("FLOODSENSE_DB_PATH", None)
        else:
            os.environ["FLOODSENSE_DB_PATH"] = cls.original_db_path

    def test_matched_observations_are_descriptive_and_citizen_view_is_public_safe(self) -> None:
        with connection() as db:
            prediction = db.execute(
                """
                SELECT id, location_id, prediction_time, risk_category
                FROM risk_predictions
                WHERE risk_category IN ('High', 'Critical')
                ORDER BY location_id LIMIT 1
                """
            ).fetchone()
            self.assertIsNotNone(prediction)
            db.execute(
                """
                INSERT INTO field_reports
                    (id, author_user_id, location_id, location_name, area, prediction_id,
                     category, description, observed_condition, outcome, severity, status,
                     observed_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'FLOODING', 'Phase 4 test observation',
                        'Water observed after prediction window', 'PROBLEM_FOUND', 'HIGH',
                        'PENDING_REVIEW', '2026-09-10T13:00:00+00:00',
                        '2026-09-10T13:00:00+00:00')
                """,
                (
                    "phase4-field-report",
                    self.field_user.id,
                    prediction["location_id"],
                    "Test location",
                    "Test area",
                    prediction["id"],
                ),
            )
            db.execute(
                """
                INSERT INTO citizen_reports
                    (id, reporter_id, location_id, location_name, area, category,
                     description, status, submitted_at, updated_at)
                VALUES ('phase4-unverified-citizen-report', ?, ?, 'Test location', 'Test area',
                        'FLOODING', 'Not verified; must not be ground truth',
                        'PENDING_VERIFICATION', '2026-09-10T11:00:00+00:00',
                        '2026-09-10T11:00:00+00:00')
                """,
                (self.citizen_user.id, prediction["location_id"]),
            )
            db.execute(
                """
                INSERT INTO field_reports
                    (id, author_user_id, location_id, location_name, area, prediction_id,
                     category, description, observed_condition, outcome, severity, status,
                     observed_at, updated_at)
                VALUES ('phase4-in-window-no-problem', ?, ?, 'Test location', 'Test area', ?,
                        'FLOODING', 'Inspection during prediction window',
                        'No issue observed during forecast window', 'INSPECTED_NO_PROBLEM_FOUND',
                        NULL, 'PENDING_REVIEW', '2026-09-10T10:00:00+00:00',
                        '2026-09-10T10:00:00+00:00')
                """,
                (self.field_user.id, prediction["location_id"], prediction["id"]),
            )
            field_result = risk_observation_analytics(db, public_only=False)
            citizen_result = risk_observation_analytics(db, public_only=True)

        self.assertGreaterEqual(field_result.summary.high_risk_with_problem_observation, 1)
        self.assertEqual(field_result.summary.high_risk_with_no_problem_inspection, 0)
        self.assertIn(
            "PROBLEM_FOUND",
            {
                observation.outcome
                for location in field_result.locations
                for observation in location.observation_history
            },
        )
        self.assertNotIn(
            "CITIZEN_REPORT",
            {
                observation.source_type
                for location in field_result.locations
                for observation in location.observation_history
            },
        )
        self.assertTrue(all(not location.observation_history for location in citizen_result.locations))
        self.assertEqual(citizen_result.summary.field_problem_findings, 0)
        self.assertEqual(citizen_result.summary.high_risk_with_problem_observation, 0)
        self.assertIn("No model accuracy", citizen_result.summary.evaluation_notice)

    def test_analytics_api_requires_session_and_scopes_citizen_response(self) -> None:
        with connection() as db:
            prediction = db.execute(
                "SELECT id, location_id FROM risk_predictions WHERE risk_category = 'Critical' LIMIT 1"
            ).fetchone()
            db.execute(
                """
                INSERT INTO field_reports
                    (id, author_user_id, location_id, location_name, area, prediction_id,
                     category, description, observed_condition, outcome, severity, status,
                     observed_at, updated_at)
                VALUES ('phase4-api-field-report', ?, ?, 'Test location', 'Test area', ?,
                        'FLOODING', 'API privacy test observation', 'Water observed',
                        'PROBLEM_FOUND', 'HIGH', 'PENDING_REVIEW',
                        '2026-09-10T13:00:00+00:00', '2026-09-10T13:00:00+00:00')
                """,
                (self.field_user.id, prediction["location_id"], prediction["id"]),
            )
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/analytics/risk-observations").status_code, 401)
            role_results = {}
            for role, user in (
                (Role.CITIZEN, self.citizen_user),
                (Role.FIELD_RESPONSE_PLANNING, self.field_user),
                (Role.DISASTER_MANAGEMENT_ADMIN, self.admin_user),
            ):
                token = create_session(user.id)
                client.cookies.set("floodsense_session", token)
                response = client.get("/api/analytics/risk-observations")
                self.assertEqual(response.status_code, 200)
                role_results[role] = response.json()

        self.assertTrue(all(
            not row["observation_history"]
            for row in role_results[Role.CITIZEN]["locations"]
        ))
        self.assertTrue(any(
            row["observation_history"]
            for row in role_results[Role.FIELD_RESPONSE_PLANNING]["locations"]
        ))
        self.assertTrue(any(
            row["observation_history"]
            for row in role_results[Role.DISASTER_MANAGEMENT_ADMIN]["locations"]
        ))
        self.assertEqual(role_results[Role.CITIZEN]["summary"]["field_problem_findings"], 0)
        self.assertEqual(set(role_results[Role.FIELD_RESPONSE_PLANNING]), {"summary", "locations"})
        self.assertEqual(set(role_results[Role.DISASTER_MANAGEMENT_ADMIN]), {"summary", "locations"})

    def test_model_explanations_are_signed_feature_contributions_not_accuracy(self) -> None:
        model = RiskModel()
        explanations = model.explain({
            "currentRainfallMm": 18.0,
            "forecastRainfallMm": 35.0,
            "historicalHotspot": True,
            "terrainSignal": 1,
        })
        self.assertEqual(
            {item["feature"] for item in explanations},
            set(model.FEATURE_NAMES),
        )
        self.assertTrue(all(isinstance(item["logit_contribution"], float) for item in explanations))
        self.assertTrue(all(
            item["interpretation"] in {"increases", "decreases", "neutral"}
            for item in explanations
        ))

    def test_map_features_are_role_scoped_and_exclude_internal_report_fields(self) -> None:
        with connection() as db:
            location = db.execute("SELECT id FROM locations LIMIT 1").fetchone()
            db.execute(
                """
                INSERT INTO citizen_reports
                    (id, reporter_id, location_id, location_name, area, category, description,
                     status, submitted_at, updated_at)
                VALUES ('map-own-citizen-report', ?, ?, 'Map location', 'Test area', 'FLOODING',
                        'Private citizen description', 'PENDING_VERIFICATION',
                        '2026-09-10T12:00:00+00:00', '2026-09-10T12:00:00+00:00')
                """,
                (self.citizen_user.id, location["id"]),
            )
            db.execute(
                """
                INSERT INTO citizen_reports
                    (id, reporter_id, location_id, location_name, area, category, description,
                     status, submitted_at, updated_at)
                VALUES ('map-other-citizen-report', ?, ?, 'Private location', 'Test area', 'FLOODING',
                        'Other user private description', 'PENDING_VERIFICATION',
                        '2026-09-10T12:00:00+00:00', '2026-09-10T12:00:00+00:00')
                """,
                (self.other_citizen_user.id, location["id"]),
            )
            db.execute(
                """
                INSERT INTO field_reports
                    (id, author_user_id, location_id, location_name, area, category, description,
                     observed_condition, outcome, severity, status, observed_at, updated_at)
                VALUES ('map-field-observation', ?, ?, 'Map location', 'Test area', 'FLOODING',
                        'Internal report description', 'Internal staff finding', 'PROBLEM_FOUND',
                        'HIGH', 'APPROVED', '2026-09-10T13:00:00+00:00',
                        '2026-09-10T13:00:00+00:00')
                """,
                (self.field_user.id, location["id"]),
            )
            db.execute(
                """
                INSERT INTO flood_problems
                    (id, field_report_id, severity, status, approved_by_user_id, approved_at)
                VALUES ('map-official-problem', 'map-field-observation', 'HIGH', 'OPEN', ?, 
                        '2026-09-10T14:00:00+00:00')
                """,
                (self.admin_user.id,),
            )

        role_results = {}
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/map/features").status_code, 401)
            for role, user in (
                (Role.CITIZEN, self.citizen_user),
                (Role.FIELD_RESPONSE_PLANNING, self.field_user),
                (Role.DISASTER_MANAGEMENT_ADMIN, self.admin_user),
            ):
                client.cookies.set("floodsense_session", create_session(user.id))
                response = client.get("/api/map/features")
                self.assertEqual(response.status_code, 200)
                role_results[role] = response.json()

        citizen_features = role_results[Role.CITIZEN]
        citizen_report_ids = {
            feature["id"] for feature in citizen_features
            if feature["feature_type"] == "CITIZEN_REPORT"
        }
        self.assertIn("map-own-citizen-report", citizen_report_ids)
        self.assertNotIn("map-other-citizen-report", citizen_report_ids)
        self.assertFalse(any(
            feature["feature_type"] == "FIELD_OBSERVATION"
            for feature in citizen_features
        ))
        self.assertTrue(any(
            feature["id"] == "map-official-problem"
            for feature in citizen_features
        ))
        self.assertTrue(any(
            feature["id"] == "map-field-observation"
            for feature in role_results[Role.FIELD_RESPONSE_PLANNING]
            if feature["feature_type"] == "FIELD_OBSERVATION"
        ))
        self.assertTrue(any(
            feature["id"] == "map-other-citizen-report"
            for feature in role_results[Role.DISASTER_MANAGEMENT_ADMIN]
            if feature["feature_type"] == "CITIZEN_REPORT"
        ))
        for feature in citizen_features + role_results[Role.FIELD_RESPONSE_PLANNING]:
            self.assertFalse({"description", "notes", "reviewer_user_id", "author_user_id"} & feature.keys())

    def test_legacy_prediction_migration_keeps_explanation_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as migration_dir:
            legacy_path = Path(migration_dir) / "legacy.sqlite3"
            original_path = os.environ.get("FLOODSENSE_DB_PATH")
            os.environ["FLOODSENSE_DB_PATH"] = str(legacy_path)
            try:
                db = sqlite3.connect(legacy_path)
                try:
                    db.executescript(
                        """
                        CREATE TABLE locations (
                            id TEXT PRIMARY KEY, name TEXT NOT NULL, area TEXT NOT NULL,
                            latitude REAL NOT NULL, longitude REAL NOT NULL,
                            historical_hotspot INTEGER NOT NULL, source_name TEXT NOT NULL,
                            source_reference TEXT NOT NULL
                        );
                        CREATE TABLE risk_predictions (
                            id TEXT PRIMARY KEY, location_id TEXT NOT NULL,
                            score INTEGER NOT NULL, risk_category TEXT NOT NULL,
                            updated_at TEXT NOT NULL, prediction_time TEXT NOT NULL,
                            current_rainfall TEXT NOT NULL, forecast_rainfall TEXT NOT NULL,
                            drivers_json TEXT NOT NULL, created_at TEXT NOT NULL,
                            data_mode TEXT NOT NULL, model_version TEXT NOT NULL,
                            UNIQUE (location_id, prediction_time, model_version)
                        );
                        INSERT INTO locations VALUES
                            ('kothrud', 'Old location', 'Kothrud', 18.5, 73.8, 1, 'REPLAY', 'kothrud');
                        INSERT INTO risk_predictions VALUES
                            ('legacy-prediction', 'kothrud', 91, 'Critical', 'old timestamp',
                             '10 Sep 2026, 15:00-18:00 IST', '21.8 mm', '42 mm', '[]',
                             'old created timestamp', 'replay', 'replay-logistic-baseline-v1');
                        """
                    )
                finally:
                    db.close()
                initialize_database()
                with connection() as db:
                    legacy = db.execute(
                        "SELECT id, feature_explanations_json FROM risk_predictions WHERE id = 'legacy-prediction'"
                    ).fetchone()
                self.assertEqual(legacy["id"], "legacy-prediction")
                self.assertEqual(legacy["feature_explanations_json"], "[]")
            finally:
                if original_path is None:
                    os.environ.pop("FLOODSENSE_DB_PATH", None)
                else:
                    os.environ["FLOODSENSE_DB_PATH"] = original_path


if __name__ == "__main__":
    unittest.main()
