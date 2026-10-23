import hashlib
import os
import sqlite3
import tempfile
import unittest
from http.cookies import SimpleCookie
from pathlib import Path

from fastapi import HTTPException, Response

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
        self.assertEqual(total, 6)
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
        self.assertEqual(citizen_view.sources, [])
        self.assertEqual(citizen_view.model_version, "replay-logistic-baseline-v1")
        self.assertEqual(len(field_view.sources), 4)
        self.assertEqual(field_view.model_version, "replay-logistic-baseline-v1")
        self.assertEqual(admin_view.model_version, "replay-logistic-baseline-v1")
        self.assertTrue(all(prediction.model_version == "replay-logistic-baseline-v1" for prediction in get_risk_predictions(self.citizen)))
        self.assertTrue(all(prediction.model_version == "replay-logistic-baseline-v1" for prediction in get_risk_predictions(self.field)))
        self.assertTrue(all(prediction.model_version == "replay-logistic-baseline-v1" for prediction in get_risk_predictions(self.admin)))

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
        self.assertEqual(len(get_data_status(self.field).sources), 4)
        self.assertEqual(len(get_data_status(self.admin).sources), 4)
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
