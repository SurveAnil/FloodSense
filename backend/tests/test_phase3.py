import base64
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from app.auth import Role, provision_user
from app.database import connection, initialize_database
from app.main import (
    create_citizen_report,
    create_response_task,
    create_response_task_update,
    get_my_report,
    list_assigned_response_tasks,
    list_response_tasks,
    review_report,
    review_response_task_completion,
    verify_citizen_report,
)
from app.models import (
    CitizenReportCreate,
    FieldVerificationCreate,
    ReportReviewCreate,
    ResponseTaskCompletionReview,
    ResponseTaskCreate,
    ResponseTaskUpdateCreate,
)


class PhaseThreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = os.environ.get("FLOODSENSE_DB_PATH")
        os.environ["FLOODSENSE_DB_PATH"] = str(Path(cls.temp_dir.name) / "phase3.sqlite3")
        initialize_database()
        cls.citizen = provision_user(
            email="phase3-citizen@example.test",
            password="phase3-citizen-password-123",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.other_citizen = provision_user(
            email="phase3-other@example.test",
            password="phase3-other-password-123",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.field = provision_user(
            email="phase3-field@example.test",
            password="phase3-field-password-123",
            role=Role.FIELD_RESPONSE_PLANNING,
            actor=None,
        )
        cls.other_field = provision_user(
            email="phase3-other-field@example.test",
            password="phase3-other-field-password-123",
            role=Role.FIELD_RESPONSE_PLANNING,
            actor=None,
        )
        cls.admin = provision_user(
            email="phase3-admin@example.test",
            password="phase3-admin-password-123",
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

    def approved_problem(self) -> tuple[str, str]:
        report = create_citizen_report(
            CitizenReportCreate(
                location={"location_id": "kothrud"},
                category="FLOODING",
                description="Flood water blocks a section of the market road.",
            ),
            self.citizen,
        )
        verify_citizen_report(
            report.id,
            FieldVerificationCreate(
                outcome="VERIFIED",
                observed_condition="Floodwater confirmed across one traffic lane.",
                severity="HIGH",
                notes="Operational-only field inspection note.",
            ),
            self.field,
        )
        approved = review_report(
            "CITIZEN_REPORT",
            report.id,
            ReportReviewCreate(decision="APPROVE", severity="HIGH"),
            self.admin,
        )
        return report.id, approved["flood_problem_id"]

    def create_task(self) -> tuple[str, str]:
        report_id, problem_id = self.approved_problem()
        task = create_response_task(
            ResponseTaskCreate(
                flood_problem_id=problem_id,
                instruction="Inspect and clear the affected drainage channel.",
                details="Prioritize the southbound lane; coordinate with the municipal crew.",
                priority="URGENT",
                assigned_user_id=self.field.id,
            ),
            self.admin,
        )
        return report_id, task.id

    def test_only_approved_official_problems_can_receive_admin_response_tasks(self) -> None:
        report = create_citizen_report(
            CitizenReportCreate(
                location={"location_id": "kothrud"},
                category="FLOODING",
                description="Flood water blocks a section of the market road.",
            ),
            self.citizen,
        )
        with self.assertRaises(HTTPException) as raised:
            create_response_task(
                ResponseTaskCreate(
                    flood_problem_id=report.id,
                    instruction="Try to issue work from an unapproved report.",
                    priority="HIGH",
                    assigned_user_id=self.field.id,
                ),
                self.admin,
            )
        self.assertEqual(raised.exception.status_code, 404)
        _, problem_id = self.approved_problem()
        with self.assertRaises(HTTPException) as raised:
            create_response_task(
                ResponseTaskCreate(
                    flood_problem_id=problem_id,
                    instruction="Assign only to a valid field role.",
                    priority="HIGH",
                    assigned_user_id=self.citizen.id,
                ),
                self.admin,
            )
        self.assertEqual(raised.exception.status_code, 422)

    def test_task_progress_completion_review_and_citizen_public_status_are_separate(self) -> None:
        report_id, task_id = self.create_task()
        self.assertIn(task_id, [task.id for task in list_assigned_response_tasks(self.field)])
        self.assertEqual(list_assigned_response_tasks(self.other_field), [])
        with self.assertRaises(HTTPException):
            create_response_task_update(
                task_id,
                ResponseTaskUpdateCreate(new_status="EN_ROUTE", action_taken="Invalid skipped state."),
                self.field,
            )
        with self.assertRaises(HTTPException):
            create_response_task_update(
                task_id,
                ResponseTaskUpdateCreate(new_status="ACCEPTED", action_taken="Wrong staff member."),
                self.other_field,
            )
        for state, action in (
            ("ACCEPTED", "Accepted the flood response task."),
            ("EN_ROUTE", "Departed for the affected location."),
            ("INSPECTED", "Inspected the drain and road condition."),
            ("ACTION_REQUIRED", "Cleared debris from the drainage inlet."),
        ):
            create_response_task_update(
                task_id,
                ResponseTaskUpdateCreate(
                    new_status=state,
                    action_taken=action,
                    condition=f"Condition during {state.lower()} phase.",
                    internal_notes="PRIVATE FIELD NOTE: crew contact and internal logistics.",
                    blockers="Internal procurement blocker.",
                ),
                self.field,
            )
        png = b"\x89PNG\r\n\x1a\nphase3-evidence"
        resolved = create_response_task_update(
            task_id,
            ResponseTaskUpdateCreate(
                new_status="RESOLVED",
                action_taken="Cleared the drain and reopened the affected lane.",
                condition="No standing water remained during final inspection.",
                internal_notes="PRIVATE COMPLETION NOTE: internal staff details.",
                evidence=[{
                    "file_name": "resolution.png",
                    "content_type": "image/png",
                    "content_base64": base64.b64encode(png).decode("ascii"),
                }],
            ),
            self.field,
        )
        self.assertEqual(resolved.status, "RESOLVED")
        self.assertEqual(resolved.completion_status, "PENDING_REVIEW")
        self.assertEqual(len(resolved.updates[-1].evidence), 1)
        citizen_view = get_my_report(report_id, self.citizen).model_dump()
        self.assertEqual(citizen_view["public_status_updates"][-1]["status"], "RESOLVED")
        public_updates_json = str(citizen_view["public_status_updates"])
        self.assertNotIn("PRIVATE", public_updates_json)
        self.assertNotIn(self.field.id, public_updates_json)
        self.assertNotIn("internal_notes", citizen_view)
        with self.assertRaises(HTTPException):
            get_my_report(report_id, self.other_citizen)
        completed = review_response_task_completion(
            task_id,
            ResponseTaskCompletionReview(decision="APPROVE", internal_notes="Verified evidence and completion."),
            self.admin,
        )
        self.assertEqual(completed.completion_status, "APPROVED")
        self.assertEqual(completed.status, "RESOLVED")
        self.assertEqual(
            get_my_report(report_id, self.citizen).public_status_updates[-1].summary,
            "An administrator confirmed the response is complete.",
        )
        with connection() as db:
            actions = {
                row["action"]
                for row in db.execute(
                    "SELECT action FROM audit_logs WHERE target_id = ?", (task_id,)
                ).fetchall()
            }
            self.assertIn("response_task.created", actions)
            self.assertIn("response_task.transitioned", actions)
            self.assertIn("response_task.completion_reviewed", actions)

    def test_admin_can_return_completion_for_additional_action(self) -> None:
        _, task_id = self.create_task()
        for state in ("ACCEPTED", "EN_ROUTE", "INSPECTED", "ACTION_REQUIRED", "RESOLVED"):
            create_response_task_update(
                task_id,
                ResponseTaskUpdateCreate(new_status=state, action_taken=f"Completed {state.lower()} phase."),
                self.field,
            )
        returned = review_response_task_completion(
            task_id,
            ResponseTaskCompletionReview(decision="RETURN_FOR_ACTION", internal_notes="Repeat inspection required."),
            self.admin,
        )
        self.assertEqual(returned.status, "ACTION_REQUIRED")
        self.assertEqual(returned.completion_status, "RETURNED")
        again = create_response_task_update(
            task_id,
            ResponseTaskUpdateCreate(new_status="RESOLVED", action_taken="Repeat inspection and clear drain complete."),
            self.field,
        )
        self.assertEqual(again.completion_status, "PENDING_REVIEW")

    def test_task_update_failure_rolls_back_state_public_status_evidence_and_audit(self) -> None:
        report_id, task_id = self.create_task()
        with connection() as db:
            db.execute(
                """
                CREATE TRIGGER fail_response_task_update
                BEFORE INSERT ON task_updates
                BEGIN
                    SELECT RAISE(ABORT, 'simulated task update failure');
                END
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            create_response_task_update(
                task_id,
                ResponseTaskUpdateCreate(new_status="ACCEPTED", action_taken="Accept response task."),
                self.field,
            )
        with connection() as db:
            db.execute("DROP TRIGGER fail_response_task_update")
            task = db.execute(
                "SELECT status FROM response_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            update_count = db.execute(
                "SELECT COUNT(*) FROM task_updates WHERE response_task_id = ?", (task_id,)
            ).fetchone()[0]
            status_count = db.execute(
                "SELECT COUNT(*) FROM public_status_updates WHERE citizen_report_id = ?", (report_id,)
            ).fetchone()[0]
            audit_count = db.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE target_id = ? AND action = 'response_task.transitioned'",
                (task_id,),
            ).fetchone()[0]
        self.assertEqual(task["status"], "ASSIGNED")
        self.assertEqual(update_count, 0)
        self.assertEqual(status_count, 1)
        self.assertEqual(audit_count, 0)

    def test_admin_monitoring_returns_complete_task_history(self) -> None:
        _, task_id = self.create_task()
        monitored = next(task for task in list_response_tasks(self.admin) if task.id == task_id)
        self.assertEqual(monitored.assigned_user_id, self.field.id)
        self.assertEqual(monitored.assigned_user_email, self.field.email)
        self.assertEqual(monitored.priority, "URGENT")
        self.assertEqual(monitored.status, "ASSIGNED")


if __name__ == "__main__":
    unittest.main()
