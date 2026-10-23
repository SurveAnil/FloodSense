import base64
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from app.auth import Role, provision_user, require_role
from app.database import connection, initialize_database
from app.main import (
    create_citizen_report,
    create_field_report,
    download_evidence,
    get_my_report,
    list_flood_problems,
    list_field_reports,
    list_my_reports,
    list_pending_citizen_reports,
    list_reports_for_review,
    review_report,
    supplement_field_report,
    update_my_report,
    verify_citizen_report,
)
from app.models import (
    CitizenReportCreate,
    CitizenReportUpdate,
    FieldReportCreate,
    FieldReportSupplement,
    FieldVerificationCreate,
    EvidenceUpload,
    ReportReviewCreate,
)
from app.services.reports import validated_evidence


class PhaseTwoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = os.environ.get("FLOODSENSE_DB_PATH")
        os.environ["FLOODSENSE_DB_PATH"] = str(Path(cls.temp_dir.name) / "phase2.sqlite3")
        initialize_database()
        cls.citizen = provision_user(
            email="phase2-citizen@example.test",
            password="citizen-password-123",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.other_citizen = provision_user(
            email="phase2-other@example.test",
            password="other-password-123",
            role=Role.CITIZEN,
            actor=None,
        )
        cls.field = provision_user(
            email="phase2-field@example.test",
            password="field-password-123",
            role=Role.FIELD_RESPONSE_PLANNING,
            actor=None,
        )
        cls.admin = provision_user(
            email="phase2-admin@example.test",
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

    def new_citizen_report(self, *, evidence=None):
        return create_citizen_report(
            CitizenReportCreate(
                location={"location_id": "kothrud"},
                category="FLOODING",
                description="Flood water reached the road entrance.",
                evidence=evidence or [],
            ),
            self.citizen,
        )

    def verified_report(self):
        report = self.new_citizen_report()
        verified = verify_citizen_report(
            report.id,
            FieldVerificationCreate(
                outcome="VERIFIED",
                observed_condition="Standing floodwater blocks one lane.",
                severity="HIGH",
                notes="Observed during field visit.",
            ),
            self.field,
        )
        self.assertEqual(verified.status, "VERIFIED")
        return verified

    def test_citizens_can_create_and_track_only_their_own_reports(self) -> None:
        with connection() as db:
            problems_before = db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0]
        report = self.new_citizen_report()
        self.assertEqual(report.status, "PENDING_VERIFICATION")
        with self.assertRaises(HTTPException) as raised:
            review_report(
                "CITIZEN_REPORT",
                report.id,
                ReportReviewCreate(decision="APPROVE", severity="HIGH"),
                self.admin,
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual([item.id for item in list_my_reports(self.citizen)], [report.id])
        self.assertNotIn("reporter_id", report.model_dump())
        with self.assertRaises(HTTPException) as raised:
            get_my_report(report.id, self.other_citizen)
        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(list_my_reports(self.other_citizen), [])
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0], problems_before)

    def test_field_verification_is_separate_and_admin_approval_creates_problem(self) -> None:
        report = self.new_citizen_report()
        self.assertIn(report.id, [item.id for item in list_pending_citizen_reports(self.field)])
        verified = verify_citizen_report(
            report.id,
            FieldVerificationCreate(
                outcome="VERIFIED",
                observed_condition="Drain overflow observed.",
                severity="HIGH",
                notes="Verified independently.",
            ),
            self.field,
        )
        self.assertEqual(verified.status, "VERIFIED")
        with connection() as db:
            db.execute(
                "UPDATE field_verifications SET notes = 'INTERNAL: dispatch planning note' WHERE citizen_report_id = ?",
                (report.id,),
            )
        citizen_view = get_my_report(report.id, self.citizen)
        public_payload = citizen_view.model_dump()
        self.assertIsNone(citizen_view.requested_information)
        self.assertNotIn("reviews", public_payload)
        self.assertNotIn("reporter_id", public_payload)
        self.assertNotIn("verifier_user_id", public_payload["verifications"][0])
        self.assertNotIn("notes", public_payload["verifications"][0])
        admin_report = next(
            item for item in list_reports_for_review(self.admin)["citizen_reports"]
            if item["id"] == report.id
        )
        self.assertIn("verifier_user_id", admin_report["verifications"][0])
        self.assertEqual(admin_report["verifications"][0]["notes"], "INTERNAL: dispatch planning note")
        self.assertEqual(len(verified.verifications), 1)
        self.assertNotEqual(verified.id, verified.verifications[0].id)
        self.assertEqual(verified.flood_problem_id, None)
        with connection() as db:
            before = db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0]
            predictions_before = db.execute("SELECT COUNT(*) FROM risk_predictions").fetchone()[0]
        result = review_report(
            "CITIZEN_REPORT",
            report.id,
            ReportReviewCreate(decision="APPROVE", severity="HIGH"),
            self.admin,
        )
        approved = get_my_report(report.id, self.citizen)
        self.assertEqual(approved.status, "APPROVED")
        self.assertEqual(approved.flood_problem_id, result["flood_problem_id"])
        self.assertEqual(result["decision"], "APPROVE")
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0], before + 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM risk_predictions").fetchone()[0], predictions_before)
            problem = db.execute(
                "SELECT citizen_report_id, field_report_id, severity FROM flood_problems WHERE id = ?",
                (result["flood_problem_id"],),
            ).fetchone()
            self.assertEqual(problem["citizen_report_id"], report.id)
            self.assertIsNone(problem["field_report_id"])
            self.assertEqual(problem["severity"], "HIGH")
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM audit_logs WHERE action = 'flood_problem.approved' AND target_id = ?",
                    (result["flood_problem_id"],),
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM audit_logs WHERE action = 'report.approve' AND target_id = ?",
                    (report.id,),
                ).fetchone()[0],
                1,
            )
        with self.assertRaises(HTTPException) as raised:
            review_report(
                "CITIZEN_REPORT",
                report.id,
                ReportReviewCreate(decision="APPROVE", severity="HIGH"),
                self.admin,
            )
        self.assertEqual(raised.exception.status_code, 409)

    def test_field_can_report_without_citizen_and_no_problem_finding_is_not_approvable(self) -> None:
        with connection() as db:
            prediction_id = db.execute("SELECT id FROM risk_predictions LIMIT 1").fetchone()["id"]
        report = create_field_report(
            FieldReportCreate(
                location={"location_name": "New drainage point", "area": "Baner", "latitude": 18.56, "longitude": 73.78},
                category="BLOCKED_DRAINAGE",
                description="Proactive inspection of newly reported drainage condition.",
                observed_condition="Inlet was clear and water drained normally.",
                outcome="INSPECTED_NO_PROBLEM_FOUND",
                prediction_id=prediction_id,
            ),
            self.field,
        )
        self.assertIsNone(report.citizen_report_id)
        self.assertEqual(report.prediction_id, prediction_id)
        self.assertEqual(report.outcome, "INSPECTED_NO_PROBLEM_FOUND")
        self.assertEqual(report.status, "PENDING_REVIEW")
        self.assertIn(report.id, [item.id for item in list_field_reports(self.field)])
        with connection() as db:
            before = db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0]
        with self.assertRaises(HTTPException) as raised:
            review_report(
                "FIELD_REPORT",
                report.id,
                ReportReviewCreate(decision="APPROVE", severity="HIGH"),
                self.admin,
            )
        self.assertEqual(raised.exception.status_code, 409)
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0], before)

    def test_independent_problem_finding_requires_admin_approval(self) -> None:
        with connection() as db:
            problems_before = db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0]
        report = create_field_report(
            FieldReportCreate(
                location={"location_id": "aundh"},
                category="WATERLOGGING",
                description="Water pooling at the underpass during inspection.",
                observed_condition="Water depth approximately ten centimeters.",
                outcome="PROBLEM_FOUND",
                severity="MODERATE",
            ),
            self.field,
        )
        self.assertIsNone(report.citizen_report_id)
        self.assertIsNone(report.flood_problem_id)
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0], problems_before)
        result = review_report(
            "FIELD_REPORT",
            report.id,
            ReportReviewCreate(decision="APPROVE"),
            self.admin,
        )
        with connection() as db:
            problem = db.execute(
                "SELECT field_report_id, citizen_report_id, severity, approved_by_user_id FROM flood_problems WHERE id = ?",
                (result["flood_problem_id"],),
            ).fetchone()
        self.assertEqual(problem["field_report_id"], report.id)
        self.assertIsNone(problem["citizen_report_id"])
        self.assertEqual(problem["severity"], "MODERATE")
        self.assertEqual(problem["approved_by_user_id"], self.admin.id)

    def test_linked_citizen_and_field_sources_cannot_create_duplicate_official_problems(self) -> None:
        problems_before = len(list_flood_problems(self.admin))
        report = self.verified_report()
        field_report = create_field_report(
            FieldReportCreate(
                location={"location_id": "kothrud"},
                citizen_report_id=report.id,
                category="FLOODING",
                description="Field inspection confirms the citizen observation.",
                observed_condition="Water confirmed across the eastbound lane.",
                outcome="PROBLEM_FOUND",
                severity="HIGH",
            ),
            self.field,
        )
        citizen_review = review_report(
            "CITIZEN_REPORT",
            report.id,
            ReportReviewCreate(decision="APPROVE", severity="HIGH"),
            self.admin,
        )
        self.assertTrue(citizen_review["flood_problem_id"])
        with self.assertRaises(HTTPException) as raised:
            review_report(
                "FIELD_REPORT",
                field_report.id,
                ReportReviewCreate(decision="APPROVE", severity="HIGH"),
                self.admin,
            )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(len(list_flood_problems(self.admin)), problems_before + 1)

    def test_information_request_reverification_and_rejection_create_no_problem(self) -> None:
        with connection() as db:
            problems_before = db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0]
        report = self.verified_report()
        request = review_report(
            "CITIZEN_REPORT",
            report.id,
            ReportReviewCreate(decision="REQUEST_INFORMATION", requested_information="Confirm the affected road lane."),
            self.admin,
        )
        self.assertIsNone(request["flood_problem_id"])
        needs_info = get_my_report(report.id, self.citizen)
        self.assertEqual(needs_info.status, "NEEDS_INFORMATION")
        self.assertEqual(needs_info.requested_information, "Confirm the affected road lane.")
        self.assertNotIn("reviews", needs_info.model_dump())
        self.assertNotIn("notes", needs_info.verifications[-1].model_dump())
        updated = update_my_report(
            report.id,
            CitizenReportUpdate(description="Flood water covers the east lane beside the drainage outlet."),
            self.citizen,
        )
        self.assertEqual(updated.status, "PENDING_VERIFICATION")
        verified_again = verify_citizen_report(
            report.id,
            FieldVerificationCreate(outcome="NOT_VERIFIED", observed_condition="Road lane is dry on repeat visit."),
            self.field,
        )
        self.assertEqual(verified_again.status, "NOT_VERIFIED")
        rejected = review_report(
            "CITIZEN_REPORT",
            report.id,
            ReportReviewCreate(decision="REJECT"),
            self.admin,
        )
        self.assertIsNone(rejected["flood_problem_id"])
        self.assertEqual(get_my_report(report.id, self.citizen).status, "REJECTED")
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0], problems_before)

    def test_field_report_information_request_can_be_supplemented_and_rejected(self) -> None:
        with connection() as db:
            problems_before = db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0]
        report = create_field_report(
            FieldReportCreate(
                location={"location_id": "sinhagad"},
                category="OVERFLOW",
                description="Water overflow observed beside the underpass.",
                observed_condition="Flow observed, but the affected section needs confirmation.",
                outcome="PROBLEM_FOUND",
                severity="MODERATE",
            ),
            self.field,
        )
        requested = review_report(
            "FIELD_REPORT",
            report.id,
            ReportReviewCreate(
                decision="REQUEST_INFORMATION",
                requested_information="Confirm the affected lane and provide a follow-up observation.",
            ),
            self.admin,
        )
        self.assertIsNone(requested["flood_problem_id"])
        self.assertEqual(requested["decision"], "REQUEST_INFORMATION")
        supplemented = supplement_field_report(
            report.id,
            FieldReportSupplement(
                description="Follow-up confirms overflow affected the northbound lane.",
                observed_condition="Northbound curb lane remained flooded at follow-up.",
                outcome="PROBLEM_FOUND",
                severity="HIGH",
            ),
            self.field,
        )
        self.assertEqual(supplemented.status, "PENDING_REVIEW")
        rejected = review_report(
            "FIELD_REPORT",
            report.id,
            ReportReviewCreate(decision="REJECT"),
            self.admin,
        )
        self.assertIsNone(rejected["flood_problem_id"])
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM flood_problems").fetchone()[0], problems_before)

    def test_evidence_is_validated_private_and_audited(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"phase-two-evidence"
        encoded = base64.b64encode(png).decode("ascii")
        report = self.new_citizen_report(
            evidence=[{"file_name": "drain.png", "content_type": "image/png", "content_base64": encoded}]
        )
        self.assertEqual(len(report.evidence), 1)
        attachment_id = report.evidence[0].id
        response = download_evidence(attachment_id, self.citizen)
        self.assertEqual(response.body, png)
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertEqual(download_evidence(attachment_id, self.field).body, png)
        with self.assertRaises(HTTPException) as raised:
            download_evidence(attachment_id, self.other_citizen)
        self.assertEqual(raised.exception.status_code, 404)
        with connection() as db:
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM audit_logs WHERE action = 'evidence.accessed' AND target_id = ?",
                    (attachment_id,),
                ).fetchone()[0],
                2,
            )
            before = db.execute("SELECT COUNT(*) FROM citizen_reports").fetchone()[0]
        with self.assertRaises(HTTPException):
            self.new_citizen_report(
                evidence=[{
                    "file_name": "fake.jpg",
                    "content_type": "image/jpeg",
                    "content_base64": base64.b64encode(b"not a jpeg").decode("ascii"),
                }]
            )
        with connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM citizen_reports").fetchone()[0], before)
        oversized = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * (5 * 1024 * 1024)).decode("ascii")
        with self.assertRaises(HTTPException) as raised:
            validated_evidence([
                EvidenceUpload(file_name="large.png", content_type="image/png", content_base64=oversized)
            ])
        self.assertEqual(raised.exception.status_code, 413)

    def test_failed_approval_rolls_back_review_status_problem_and_audit(self) -> None:
        report = self.verified_report()
        with connection() as db:
            db.execute(
                """
                CREATE TRIGGER force_problem_insert_failure
                BEFORE INSERT ON flood_problems
                BEGIN
                    SELECT RAISE(ABORT, 'simulated database failure');
                END
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            review_report(
                "CITIZEN_REPORT",
                report.id,
                ReportReviewCreate(decision="APPROVE", severity="HIGH"),
                self.admin,
            )
        with connection() as db:
            db.execute("DROP TRIGGER force_problem_insert_failure")
            status_row = db.execute("SELECT status FROM citizen_reports WHERE id = ?", (report.id,)).fetchone()
            review_count = db.execute(
                "SELECT COUNT(*) FROM report_reviews WHERE citizen_report_id = ?", (report.id,)
            ).fetchone()[0]
            problem_count = db.execute(
                "SELECT COUNT(*) FROM flood_problems WHERE citizen_report_id = ?", (report.id,)
            ).fetchone()[0]
            audit_count = db.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE target_id = ? AND action IN ('report.approve', 'flood_problem.approved')",
                (report.id,),
            ).fetchone()[0]
        self.assertEqual(status_row["status"], "VERIFIED")
        self.assertEqual(review_count, 0)
        self.assertEqual(problem_count, 0)
        self.assertEqual(audit_count, 0)

    def test_roles_remain_restricted_to_the_three_phase_one_roles(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            require_role(Role.FIELD_RESPONSE_PLANNING)(self.citizen)
        self.assertEqual(raised.exception.status_code, 403)
        with connection() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(
                    """
                    INSERT INTO users
                        (id, email, password_hash, role, is_active, is_demo, created_at, updated_at)
                    VALUES ('phase2-invalid', 'phase2-invalid@example.test', 'unused',
                            'SYSTEM_ADMIN', 1, 0, 'now', 'now')
                    """
                )


if __name__ == "__main__":
    unittest.main()
