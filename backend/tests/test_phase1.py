import hashlib
import os
import sqlite3
import tempfile
import unittest
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, Response
from fastapi.testclient import TestClient

from app.adapters.contracts import ProviderSnapshot
from app.auth import (
    Role,
    create_session,
    get_current_user,
    hash_password,
    login,
    provision_user,
    require_role,
    verify_password,
)
from app.database import connection, initialize_database
from app.main import (
    app,
    authenticate,
    create_user,
    demo_login,
    get_dashboard,
    get_data_status,
    get_location,
    get_locations,
    get_priorities,
    get_risk_predictions,
    logout,
    service,
)
from app.models import CreateUserRequest, DemoLoginRequest, LoginRequest


class PhaseOneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = os.environ.get("FLOODSENSE_DB_PATH")
        cls.original_demo_mode = os.environ.get("FLOODSENSE_DEMO_MODE")
        os.environ["FLOODSENSE_DB_PATH"] = str(Path(cls.temp_dir.name) / "test.sqlite3")
        os.environ["FLOODSENSE_DEMO_MODE"] = "false"
        initialize_database()
        cls.citizen = provision_user(
            email="citizen@example.test",
            password="citizen-password-123",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.field = provision_user(
            email="field@example.test",
            password="field-password-123",
            role=Role.FIELD_RESPONSE_PLANNING,
            actor=None,
        )
        cls.admin = provision_user(
            email="admin@example.test",
            password="admin-password-123",
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
        if cls.original_demo_mode is None:
            os.environ.pop("FLOODSENSE_DEMO_MODE", None)
        else:
            os.environ["FLOODSENSE_DEMO_MODE"] = cls.original_demo_mode

    def test_database_enforces_only_three_roles_and_seeds_shared_risk_data(self) -> None:
        with connection() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(
                    """
                    INSERT INTO users (id, email, password_hash, role, created_at, updated_at)
                    VALUES ('bad', 'bad@example.test', 'unused', 'SYSTEM_ADMIN', 'now', 'now')
                    """
                )
            role_values = {
                row["role"]
                for row in db.execute("SELECT DISTINCT role FROM users").fetchall()
            }
            location_count = db.execute("SELECT COUNT(*) AS n FROM locations").fetchone()["n"]
            prediction_count = db.execute("SELECT COUNT(*) AS n FROM risk_predictions").fetchone()["n"]
            unreferenced_locations = db.execute(
                "SELECT COUNT(*) AS n FROM locations WHERE source_name != 'REPLAY' OR source_reference = ''"
            ).fetchone()["n"]
        self.assertEqual(role_values, {role.value for role in Role})
        self.assertGreater(location_count, 0)
        self.assertEqual(prediction_count, location_count)
        self.assertEqual(unreferenced_locations, 0)

    def test_demo_location_scenarios_seed_scores_context_and_no_fake_workflow_reports(self) -> None:
        expected = {
            "bhumkar-chowk": ("Critical", 88, 14, "Active", (18.5993, 73.7578)),
            "shivaji-chowk-hinjawadi": ("Critical", 92, 19, "Active", (18.5913, 73.7389)),
            "laxmi-chowk-hinjawadi": ("High", 78, 9, "Pending Inspection", (18.5985, 73.7226)),
            "punawale-highway-underpass": ("High", 76, 11, "Active", (18.6212, 73.7481)),
            "kasturi-chowk-kaspate": ("Moderate", 58, 6, "Monitored", (18.5947, 73.7745)),
            "dange-chowk-under-flyover": ("High", 72, 8, "Active", (18.6086, 73.7794)),
            "maan-road-phase-3": ("Moderate", 54, 5, "Logged", (18.5772, 73.6934)),
        }
        locations = {location.id: location for location in get_locations(self.citizen)}
        self.assertTrue(set(expected).issubset(locations))
        for location_id, (risk, score, report_count, problem_status, coordinates) in expected.items():
            location = locations[location_id]
            self.assertEqual((location.risk, location.score), (risk, score))
            self.assertEqual(location.coordinates, coordinates)
            self.assertIsNotNone(location.demo_context)
            self.assertEqual(location.demo_context.citizen_report_count, report_count)
            self.assertEqual(location.demo_context.official_problem_status, problem_status)
            self.assertTrue(location.demo_context.citizen_report_examples)
            self.assertIn("light rain", location.demo_context.contextual_notes.lower())
            self.assertEqual(location.model_version, "mentor-demo-scenario-v1")

        with connection() as db:
            context_count = db.execute("SELECT COUNT(*) AS n FROM demo_location_contexts").fetchone()["n"]
            fake_report_count = db.execute(
                "SELECT COUNT(*) AS n FROM citizen_reports WHERE location_id IN ({})".format(
                    ",".join("?" for _ in expected)
                ),
                tuple(expected),
            ).fetchone()["n"]
            fake_problem_count = db.execute(
                """
                SELECT COUNT(*) AS n FROM flood_problems fp
                JOIN citizen_reports cr ON cr.id = fp.citizen_report_id
                WHERE cr.location_id IN ({})
                """.format(",".join("?" for _ in expected)),
                tuple(expected),
            ).fetchone()["n"]
        self.assertEqual(context_count, 7)
        self.assertEqual(fake_report_count, 0)
        self.assertEqual(fake_problem_count, 0)

    def test_every_replay_location_has_a_bundled_demo_illustration(self) -> None:
        records = service.adapter.locations()
        project_root = Path(__file__).resolve().parents[2]

        self.assertEqual(len(records), 12)
        for record in records:
            image_url = record["illustrativeImageUrl"]
            image_path = project_root.joinpath("public", *image_url.lstrip("/").split("/"))
            self.assertTrue(image_path.is_file(), f"Missing illustration for {record['id']}: {image_path}")
            self.assertIn("NOT GROUND TRUTH", image_path.read_text(encoding="utf-8"))

    def test_dashboard_api_exposes_demo_scenario_context(self) -> None:
        token = create_session(self.citizen.id)
        weather = ProviderSnapshot(
            source="Open-Meteo",
            state="Available",
            last_updated="2026-10-24T10:00+05:30",
            detail="Live Open-Meteo observation; precipitation 0.2 mm, rain 0.0 mm.",
            payload={},
        )
        with patch.object(service.weather_provider, "snapshot", return_value=weather):
            with TestClient(app) as client:
                client.cookies.set("floodsense_session", token)
                response = client.get("/api/dashboard")

        self.assertEqual(response.status_code, 200)
        locations = {location["id"]: location for location in response.json()["locations"]}
        bhumkar = locations["bhumkar-chowk"]
        self.assertEqual((bhumkar["risk"], bhumkar["score"]), ("Critical", 88))
        self.assertEqual(bhumkar["coordinates"], [18.5993, 73.7578])
        self.assertEqual(bhumkar["illustrative_image_url"], "/images/locations/bhumkar-chowk.svg")
        self.assertEqual(bhumkar["demo_context"]["citizen_report_count"], 14)
        self.assertEqual(bhumkar["demo_context"]["official_problem_status"], "Active")
        self.assertIn("not verified", bhumkar["demo_context"]["source_label"].lower())
        sources = response.json()["sources"]
        self.assertEqual(len(sources), 5)
        self.assertEqual(next(source for source in sources if source["name"] == "Open-Meteo")["state"], "Available")

    def test_initialization_is_idempotent_and_preserves_prediction_history(self) -> None:
        with connection() as db:
            prediction = db.execute("SELECT * FROM risk_predictions LIMIT 1").fetchone()
            db.execute(
                """
                INSERT INTO risk_predictions
                    (id, location_id, score, risk_category, updated_at, prediction_time,
                     current_rainfall, forecast_rainfall, drivers_json, created_at, data_mode, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "historical-snapshot",
                    prediction["location_id"],
                    prediction["score"],
                    prediction["risk_category"],
                    prediction["updated_at"],
                    prediction["prediction_time"],
                    prediction["current_rainfall"],
                    prediction["forecast_rainfall"],
                    prediction["drivers_json"],
                    "9999-01-01T00:00:00+00:00",
                    prediction["data_mode"],
                    "test-historical-version",
                ),
            )
        initialize_database()
        with connection() as db:
            total = db.execute("SELECT COUNT(*) AS n FROM risk_predictions").fetchone()["n"]
            old_snapshot = db.execute(
                "SELECT model_version FROM risk_predictions WHERE id = 'historical-snapshot'"
            ).fetchone()
            source_name = db.execute(
                "SELECT source_name FROM locations WHERE id = ?",
                (prediction["location_id"],),
            ).fetchone()["source_name"]
        self.assertEqual(total, 13)
        self.assertEqual(old_snapshot["model_version"], "test-historical-version")
        self.assertEqual(source_name, "REPLAY")

    def test_database_initialization_adds_location_provenance_to_existing_schema(self) -> None:
        legacy_path = Path(self.temp_dir.name) / "legacy.sqlite3"
        legacy_db = sqlite3.connect(legacy_path)
        try:
            legacy_db.executescript(
                """
                CREATE TABLE locations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    area TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    historical_hotspot INTEGER NOT NULL
                );
                INSERT INTO locations VALUES ('legacy', 'Legacy', 'Test', 1, 2, 0);
                """
            )
        finally:
            legacy_db.close()
        original_path = os.environ["FLOODSENSE_DB_PATH"]
        os.environ["FLOODSENSE_DB_PATH"] = str(legacy_path)
        try:
            initialize_database()
            with connection() as db:
                legacy_location = db.execute(
                    "SELECT source_name, source_reference FROM locations WHERE id = 'legacy'"
                ).fetchone()
            self.assertEqual(legacy_location["source_name"], "REPLAY")
            self.assertEqual(legacy_location["source_reference"], "legacy")
        finally:
            os.environ["FLOODSENSE_DB_PATH"] = original_path

    def test_passwords_are_salted_and_verified(self) -> None:
        first = hash_password("correct-horse-battery")
        second = hash_password("correct-horse-battery")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("correct-horse-battery", first))
        self.assertFalse(verify_password("wrong-password", first))

    def test_login_returns_backend_assigned_role_and_revocable_session(self) -> None:
        response = Response()
        user_response = authenticate(
            LoginRequest(email=" CITIZEN@example.test ", password="citizen-password-123"),
            response,
        )
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        token = cookie["floodsense_session"].value
        self.assertEqual(user_response.role, "CITIZEN")
        self.assertTrue(cookie["floodsense_session"]["httponly"])
        self.assertEqual(get_current_user(token).id, self.citizen.id)

    def test_real_login_ignores_a_client_supplied_role(self) -> None:
        payload = LoginRequest.model_validate(
            {
                "email": "citizen@example.test",
                "password": "citizen-password-123",
                "role": "DISASTER_MANAGEMENT_ADMIN",
            }
        )
        user_response = authenticate(payload, Response())
        self.assertEqual(user_response.role, "CITIZEN")

    def test_logout_revokes_the_server_side_session(self) -> None:
        response = Response()
        authenticate(
            LoginRequest(email="field@example.test", password="field-password-123"),
            response,
        )
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        token = cookie["floodsense_session"].value
        user = get_current_user(token)
        logout_response = logout(token, user)
        self.assertEqual(logout_response.status_code, 204)
        with self.assertRaises(HTTPException) as raised:
            get_current_user(token)
        self.assertEqual(raised.exception.status_code, 401)

    def test_expired_session_is_rejected(self) -> None:
        token = create_session(self.citizen.id)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with connection() as db:
            db.execute(
                "UPDATE sessions SET expires_at = ? WHERE token_hash = ?",
                ("2000-01-01T00:00:00+00:00", token_hash),
            )
        with self.assertRaises(HTTPException) as raised:
            get_current_user(token)
        self.assertEqual(raised.exception.status_code, 401)

    def test_all_roles_read_the_same_persisted_risk_records(self) -> None:
        weather = ProviderSnapshot(
            source="Open-Meteo",
            state="Available",
            last_updated="2026-10-24T10:00+05:30",
            detail="Live Open-Meteo observation.",
            payload={},
        )
        with patch.object(service.weather_provider, "snapshot", return_value=weather):
            citizen_view = get_dashboard(self.citizen)
            field_view = get_dashboard(self.field)
            admin_view = get_dashboard(self.admin)
        prediction_location_ids = [prediction.location_id for prediction in get_risk_predictions(self.citizen)]
        self.assertEqual(
            [location.id for location in citizen_view.locations],
            [location.id for location in field_view.locations],
        )
        self.assertEqual(
            [location.id for location in citizen_view.locations],
            [location.id for location in admin_view.locations],
        )
        self.assertEqual(set(prediction_location_ids), {location.id for location in citizen_view.locations})
        self.assertEqual(len(citizen_view.sources), 5)
        self.assertIn("Open-Meteo", {source.name for source in citizen_view.sources})
        self.assertEqual(citizen_view.model_version, "replay-logistic-baseline-v1")
        self.assertEqual(len(field_view.sources), 5)
        self.assertEqual(field_view.model_version, "replay-logistic-baseline-v1")
        self.assertEqual(admin_view.model_version, "replay-logistic-baseline-v1")
        prediction_versions = {
            prediction.location_id: prediction.model_version
            for prediction in get_risk_predictions(self.citizen)
        }
        demo_location_ids = {
            "bhumkar-chowk",
            "shivaji-chowk-hinjawadi",
            "laxmi-chowk-hinjawadi",
            "punawale-highway-underpass",
            "kasturi-chowk-kaspate",
            "dange-chowk-under-flyover",
            "maan-road-phase-3",
        }
        self.assertEqual(
            {
                version
                for location_id, version in prediction_versions.items()
                if location_id not in demo_location_ids
            },
            {"replay-logistic-baseline-v1"},
        )
        self.assertTrue(
            all(
                prediction_versions[location_id] == "mentor-demo-scenario-v1"
                for location_id in demo_location_ids
            )
        )
        for user in (self.field, self.admin):
            self.assertEqual(
                {
                    prediction.location_id: prediction.model_version
                    for prediction in get_risk_predictions(user)
                },
                prediction_versions,
            )

    def test_authenticated_risk_and_hotspot_apis_share_latest_location_records(self) -> None:
        citizen_locations = get_locations(self.citizen)
        field_locations = get_locations(self.field)
        admin_locations = get_locations(self.admin)
        self.assertEqual(
            [location.id for location in citizen_locations],
            [location.id for location in field_locations],
        )
        self.assertEqual(
            [location.id for location in citizen_locations],
            [location.id for location in admin_locations],
        )
        location = get_location(citizen_locations[0].id, self.citizen)
        self.assertEqual(location.id, citizen_locations[0].id)
        priorities = get_priorities(None, self.field)
        self.assertEqual(priorities.priorities[0].location_id, citizen_locations[0].id)
        critical = get_priorities("Critical", self.admin)
        self.assertTrue(all(item.risk_category == "Critical" for item in critical.priorities))

    def test_source_status_is_scoped_to_operational_roles(self) -> None:
        weather = ProviderSnapshot(
            source="Open-Meteo",
            state="Available",
            last_updated="2026-10-24T10:00+05:30",
            detail="Live Open-Meteo observation.",
            payload={},
        )
        with patch.object(service.weather_provider, "snapshot", return_value=weather):
            self.assertEqual(len(get_data_status(self.field).sources), 5)
            self.assertEqual(len(get_data_status(self.admin).sources), 5)
        self.assertEqual(
            require_role(Role.FIELD_RESPONSE_PLANNING, Role.DISASTER_MANAGEMENT_ADMIN)(self.field).role,
            Role.FIELD_RESPONSE_PLANNING,
        )
        self.assertEqual(
            require_role(Role.FIELD_RESPONSE_PLANNING, Role.DISASTER_MANAGEMENT_ADMIN)(self.admin).role,
            Role.DISASTER_MANAGEMENT_ADMIN,
        )
        with self.assertRaises(HTTPException) as raised:
            require_role(Role.FIELD_RESPONSE_PLANNING, Role.DISASTER_MANAGEMENT_ADMIN)(self.citizen)
        self.assertEqual(raised.exception.status_code, 403)

    def test_non_admin_cannot_provision_accounts(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            require_role(Role.DISASTER_MANAGEMENT_ADMIN)(self.citizen)
        self.assertEqual(raised.exception.status_code, 403)

    def test_demo_role_selector_is_unavailable_when_demo_mode_is_disabled(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            demo_login(DemoLoginRequest(role="CITIZEN"), Response())
        self.assertEqual(raised.exception.status_code, 404)

    def test_admin_can_provision_only_one_of_the_allowed_roles(self) -> None:
        created = create_user(
            CreateUserRequest(
                email="new-field@example.test",
                password="temporary-password-123",
                role="FIELD_RESPONSE_PLANNING",
            ),
            self.admin,
        )
        self.assertEqual(created.role, "FIELD_RESPONSE_PLANNING")
        self.assertEqual(login(created.email, "temporary-password-123")[0].role, Role.FIELD_RESPONSE_PLANNING)


if __name__ == "__main__":
    unittest.main()
