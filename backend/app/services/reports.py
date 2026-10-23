import base64
import binascii
import hashlib
import re
import sqlite3
import uuid

from fastapi import HTTPException

from app.auth import AuthenticatedUser
from app.database import utc_now, write_audit
from app.models import EvidenceResponse, EvidenceUpload, ReportLocation

MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
MAX_EVIDENCE_TOTAL_BYTES = 10 * 1024 * 1024
EVIDENCE_SIGNATURES = {
    "image/jpeg": lambda value: value.startswith(b"\xff\xd8\xff"),
    "image/png": lambda value: value.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda value: len(value) >= 12 and value[:4] == b"RIFF" and value[8:12] == b"WEBP",
    "application/pdf": lambda value: value.startswith(b"%PDF-"),
}


def resolve_location(db: sqlite3.Connection, location: ReportLocation) -> dict[str, object]:
    if location.location_id:
        row = db.execute(
            "SELECT id, name, area, latitude, longitude FROM locations WHERE id = ?",
            (location.location_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Selected location was not found.")
        return {
            "location_id": row["id"],
            "location_name": row["name"],
            "area": row["area"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
    return {
        "location_id": None,
        "location_name": location.location_name,
        "area": location.area,
        "latitude": location.latitude,
        "longitude": location.longitude,
    }


def validated_evidence(items: list[EvidenceUpload]) -> list[tuple[EvidenceUpload, bytes]]:
    decoded: list[tuple[EvidenceUpload, bytes]] = []
    total_bytes = 0
    for item in items:
        file_name = item.file_name.strip()
        if (
            not file_name
            or file_name in {".", ".."}
            or re.search(r"[\\/\x00-\x1f\x7f]", file_name)
        ):
            raise HTTPException(status_code=422, detail="Evidence filenames must not contain paths or control characters.")
        try:
            content = base64.b64decode(item.content_base64, validate=True)
        except (binascii.Error, ValueError) as error:
            raise HTTPException(status_code=422, detail="Evidence must contain valid base64 data.") from error
        if not content or len(content) > MAX_EVIDENCE_BYTES:
            raise HTTPException(status_code=413, detail="Each evidence file must be between 1 byte and 5 MB.")
        if not EVIDENCE_SIGNATURES[item.content_type](content):
            raise HTTPException(status_code=422, detail="Evidence content does not match its declared file type.")
        total_bytes += len(content)
        if total_bytes > MAX_EVIDENCE_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail="Evidence uploads cannot exceed 10 MB per report.")
        decoded.append((item, content))
    return decoded


def insert_evidence(
    db: sqlite3.Connection,
    *,
    uploader: AuthenticatedUser,
    evidence: list[EvidenceUpload],
    parent_column: str,
    parent_id: str,
) -> list[dict[str, object]]:
    if parent_column not in {"citizen_report_id", "field_report_id", "field_verification_id"}:
        raise ValueError("Unsupported evidence parent type.")
    inserted: list[dict[str, object]] = []
    for item, content in validated_evidence(evidence):
        attachment_id = str(uuid.uuid4())
        digest = hashlib.sha256(content).hexdigest()
        db.execute(
            f"""
            INSERT INTO attachments
                (id, uploader_user_id, {parent_column}, file_name, content_type,
                 size_bytes, sha256, content, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attachment_id,
                uploader.id,
                parent_id,
                item.file_name.strip(),
                item.content_type,
                len(content),
                digest,
                content,
                utc_now(),
            ),
        )
        inserted.append(
            {
                "id": attachment_id,
                "file_name": item.file_name.strip(),
                "content_type": item.content_type,
                "size_bytes": len(content),
                "sha256": digest,
                "download_url": f"/api/evidence/{attachment_id}",
            }
        )
    return inserted


def evidence_for(
    db: sqlite3.Connection,
    *,
    parent_column: str,
    parent_id: str,
) -> list[EvidenceResponse]:
    if parent_column not in {"citizen_report_id", "field_report_id", "field_verification_id"}:
        raise ValueError("Unsupported evidence parent type.")
    rows = db.execute(
        f"""
        SELECT id, file_name, content_type, size_bytes, sha256
        FROM attachments WHERE {parent_column} = ? ORDER BY uploaded_at, id
        """,
        (parent_id,),
    ).fetchall()
    return [
        EvidenceResponse(
            id=row["id"],
            file_name=row["file_name"],
            content_type=row["content_type"],
            size_bytes=row["size_bytes"],
            sha256=row["sha256"],
            download_url=f"/api/evidence/{row['id']}",
        )
        for row in rows
    ]


def verifications_for(db: sqlite3.Connection, report_id: str) -> list[dict[str, object]]:
    rows = db.execute(
        """
        SELECT id, verifier_user_id, outcome, observed_condition, severity, notes, verified_at
        FROM field_verifications WHERE citizen_report_id = ? ORDER BY verified_at, id
        """,
        (report_id,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "verifier_user_id": row["verifier_user_id"],
            "outcome": row["outcome"],
            "observed_condition": row["observed_condition"],
            "severity": row["severity"],
            "notes": row["notes"],
            "verified_at": row["verified_at"],
            "evidence": evidence_for(db, parent_column="field_verification_id", parent_id=row["id"]),
        }
        for row in rows
    ]


def reviews_for(
    db: sqlite3.Connection,
    *,
    parent_column: str,
    parent_id: str,
) -> list[dict[str, object]]:
    if parent_column not in {"citizen_report_id", "field_report_id"}:
        raise ValueError("Unsupported review parent type.")
    rows = db.execute(
        f"""
        SELECT id, reviewer_user_id, decision, requested_information, severity, reviewed_at
        FROM report_reviews WHERE {parent_column} = ? ORDER BY reviewed_at, id
        """,
        (parent_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def citizen_report_response(db: sqlite3.Connection, report_id: str) -> dict[str, object]:
    row = db.execute("SELECT * FROM citizen_reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Citizen report was not found.")
    problem = db.execute(
        "SELECT id FROM flood_problems WHERE citizen_report_id = ?",
        (report_id,),
    ).fetchone()
    return {
        **dict(row),
        "evidence": evidence_for(db, parent_column="citizen_report_id", parent_id=report_id),
        "verifications": verifications_for(db, report_id),
        "reviews": reviews_for(db, parent_column="citizen_report_id", parent_id=report_id),
        "flood_problem_id": problem["id"] if problem else None,
    }


def citizen_report_public_response(db: sqlite3.Connection, report_id: str) -> dict[str, object]:
    report = citizen_report_response(db, report_id)
    requested_information = db.execute(
        """
        SELECT requested_information FROM report_reviews
        WHERE citizen_report_id = ? AND decision = 'REQUEST_INFORMATION'
        ORDER BY reviewed_at DESC, id DESC LIMIT 1
        """,
        (report_id,),
    ).fetchone()
    return {
        "id": report["id"],
        "location_id": report["location_id"],
        "location_name": report["location_name"],
        "area": report["area"],
        "latitude": report["latitude"],
        "longitude": report["longitude"],
        "category": report["category"],
        "description": report["description"],
        "status": report["status"],
        "submitted_at": report["submitted_at"],
        "updated_at": report["updated_at"],
        "evidence": report["evidence"],
        "verifications": [
            {
                "id": verification["id"],
                "outcome": verification["outcome"],
                "observed_condition": verification["observed_condition"],
                "verified_at": verification["verified_at"],
                "evidence": verification["evidence"],
            }
            for verification in report["verifications"]
        ],
        "requested_information": (
            requested_information["requested_information"] if requested_information else None
        ),
        "flood_problem_id": report["flood_problem_id"],
    }


def field_report_response(db: sqlite3.Connection, report_id: str) -> dict[str, object]:
    row = db.execute("SELECT * FROM field_reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Field report was not found.")
    problem = db.execute(
        "SELECT id FROM flood_problems WHERE field_report_id = ?",
        (report_id,),
    ).fetchone()
    return {
        **dict(row),
        "evidence": evidence_for(db, parent_column="field_report_id", parent_id=report_id),
        "reviews": reviews_for(db, parent_column="field_report_id", parent_id=report_id),
        "flood_problem_id": problem["id"] if problem else None,
    }


def require_report(db: sqlite3.Connection, report_id: str) -> sqlite3.Row:
    row = db.execute("SELECT * FROM citizen_reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Citizen report was not found.")
    return row


def require_field_report(db: sqlite3.Connection, report_id: str) -> sqlite3.Row:
    row = db.execute("SELECT * FROM field_reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Field report was not found.")
    return row


def record_report_review(
    db: sqlite3.Connection,
    *,
    admin: AuthenticatedUser,
    source_type: str,
    source_id: str,
    decision: str,
    requested_information: str,
    severity: str | None,
) -> dict[str, object]:
    db.execute("BEGIN IMMEDIATE")
    is_citizen = source_type == "CITIZEN_REPORT"
    if source_type not in {"CITIZEN_REPORT", "FIELD_REPORT"}:
        raise HTTPException(status_code=422, detail="Unsupported review source type.")
    source = require_report(db, source_id) if is_citizen else require_field_report(db, source_id)
    if source["status"] in {"APPROVED", "REJECTED"}:
        raise HTTPException(status_code=409, detail="This report has already received a final decision.")
    if is_citizen:
        if source["status"] not in {"VERIFIED", "NOT_VERIFIED", "NEEDS_INFORMATION"}:
            raise HTTPException(status_code=409, detail="Citizen reports require a field verification before admin review.")
        if decision == "APPROVE" and source["status"] != "VERIFIED":
            raise HTTPException(status_code=409, detail="A report must be verified before it can become an official problem.")
        source_column = "citizen_report_id"
        current_severity = db.execute(
            """
            SELECT severity FROM field_verifications
            WHERE citizen_report_id = ? AND outcome = 'VERIFIED'
            ORDER BY verified_at DESC LIMIT 1
            """,
            (source_id,),
        ).fetchone()
        effective_severity = severity or (current_severity["severity"] if current_severity else None)
        related_citizen_id = source_id
        related_field_id = None
    else:
        if decision == "APPROVE" and source["outcome"] != "PROBLEM_FOUND":
            raise HTTPException(status_code=409, detail="An inspection finding no problem cannot be approved as an official problem.")
        if source["status"] not in {"PENDING_REVIEW", "NEEDS_INFORMATION"}:
            raise HTTPException(status_code=409, detail="This field report is not awaiting review.")
        source_column = "field_report_id"
        effective_severity = severity or source["severity"]
        related_citizen_id = source["citizen_report_id"]
        related_field_id = source_id
    if decision == "APPROVE" and not effective_severity:
        raise HTTPException(status_code=422, detail="Severity is required to approve an official problem.")
    if decision == "APPROVE":
        duplicate = db.execute(
            """
            SELECT 1 FROM flood_problems p
            WHERE (? IS NOT NULL AND p.citizen_report_id = ?)
               OR (? IS NOT NULL AND p.field_report_id = ?)
               OR (
                    ? IS NOT NULL AND p.field_report_id IN (
                        SELECT id FROM field_reports WHERE citizen_report_id = ?
                    )
               )
               OR (
                    ? IS NOT NULL AND p.citizen_report_id IN (
                        SELECT citizen_report_id FROM field_reports WHERE id = ?
                    )
               )
            LIMIT 1
            """,
            (
                related_citizen_id, related_citizen_id,
                related_field_id, related_field_id,
                related_citizen_id, related_citizen_id,
                related_field_id, related_field_id,
            ),
        ).fetchone()
        if duplicate:
            raise HTTPException(status_code=409, detail="An official problem already exists for this report.")

    review_id = str(uuid.uuid4())
    reviewed_at = utc_now()
    db.execute(
        f"""
        INSERT INTO report_reviews
            (id, reviewer_user_id, {source_column}, decision, requested_information, severity, reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            admin.id,
            source_id,
            decision,
            requested_information.strip(),
            effective_severity,
            reviewed_at,
        ),
    )
    next_status = {
        "REQUEST_INFORMATION": "NEEDS_INFORMATION",
        "APPROVE": "APPROVED",
        "REJECT": "REJECTED",
    }[decision]
    table = "citizen_reports" if is_citizen else "field_reports"
    db.execute(f"UPDATE {table} SET status = ?, updated_at = ? WHERE id = ?", (next_status, reviewed_at, source_id))
    problem_id = None
    if decision == "APPROVE":
        problem_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO flood_problems
                (id, citizen_report_id, field_report_id, severity, status, approved_by_user_id, approved_at)
            VALUES (?, ?, ?, ?, 'OPEN', ?, ?)
            """,
            (
                problem_id,
                source_id if is_citizen else None,
                source_id if not is_citizen else None,
                effective_severity,
                admin.id,
                reviewed_at,
            ),
        )
        write_audit(
            db,
            actor_user_id=admin.id,
            action="flood_problem.approved",
            target_type="flood_problem",
            target_id=problem_id,
            details={"source_type": source_type, "source_id": source_id, "severity": effective_severity},
        )
    write_audit(
        db,
        actor_user_id=admin.id,
        action=f"report.{decision.lower()}",
        target_type=source_type.lower(),
        target_id=source_id,
        details={"review_id": review_id, "severity": effective_severity},
    )
    return {
        "id": review_id,
        "reviewer_user_id": admin.id,
        "decision": decision,
        "requested_information": requested_information.strip(),
        "severity": effective_severity,
        "reviewed_at": reviewed_at,
        "flood_problem_id": problem_id,
    }
