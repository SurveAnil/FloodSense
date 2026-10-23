import hashlib
import sqlite3
import uuid
from datetime import timezone

from fastapi import HTTPException

from app.auth import AuthenticatedUser, Role
from app.database import utc_now, write_audit
from app.models import (
    ResponseTaskCompletionReview,
    ResponseTaskCreate,
    ResponseTaskUpdateCreate,
)
from app.services.reports import validated_evidence

PUBLIC_STATUS_TEXT = {
    "ASSIGNED": "A response team has been assigned to this reported issue.",
    "ACCEPTED": "The response team has accepted the assignment.",
    "EN_ROUTE": "The response team is on the way.",
    "INSPECTED": "The response team has inspected the reported issue.",
    "ACTION_REQUIRED": "Further response action is in progress.",
    "RESOLVED": "The response team submitted a completion update for review.",
}
TRANSITIONS = {
    "ASSIGNED": "ACCEPTED",
    "ACCEPTED": "EN_ROUTE",
    "EN_ROUTE": "INSPECTED",
    "INSPECTED": "ACTION_REQUIRED",
    "ACTION_REQUIRED": "RESOLVED",
}


def citizen_report_for_problem(db: sqlite3.Connection, problem_id: str) -> str | None:
    row = db.execute(
        """
        SELECT COALESCE(
            p.citizen_report_id,
            (SELECT f.citizen_report_id FROM field_reports f WHERE f.id = p.field_report_id)
        ) AS citizen_report_id
        FROM flood_problems p WHERE p.id = ?
        """,
        (problem_id,),
    ).fetchone()
    return row["citizen_report_id"] if row else None


def add_public_status(
    db: sqlite3.Connection,
    *,
    problem_id: str,
    task_id: str | None,
    status: str,
    published_at: str,
    summary: str | None = None,
) -> None:
    citizen_report_id = citizen_report_for_problem(db, problem_id)
    if citizen_report_id is None:
        return
    db.execute(
        """
        INSERT INTO public_status_updates
            (id, flood_problem_id, citizen_report_id, response_task_id, status, summary, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()), problem_id, citizen_report_id, task_id,
            status, summary or PUBLIC_STATUS_TEXT[status], published_at,
        ),
    )


def task_update_response(db: sqlite3.Connection, update_id: str) -> dict[str, object]:
    row = db.execute("SELECT * FROM task_updates WHERE id = ?", (update_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Response task update was not found.")
    evidence = db.execute(
        """
        SELECT id, file_name, content_type, size_bytes, sha256, uploaded_at
        FROM task_evidence WHERE task_update_id = ? ORDER BY uploaded_at, id
        """,
        (update_id,),
    ).fetchall()
    return {
        **dict(row),
        "evidence": [
            {
                **dict(file),
                "download_url": f"/api/evidence/{file['id']}",
            }
            for file in evidence
        ],
    }


def response_task_response(db: sqlite3.Connection, task_id: str) -> dict[str, object]:
    row = db.execute(
        """
        SELECT t.*, u.email AS assigned_user_email
        FROM response_tasks t JOIN users u ON u.id = t.assigned_user_id
        WHERE t.id = ?
        """,
        (task_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Response task was not found.")
    updates = db.execute(
        "SELECT id FROM task_updates WHERE response_task_id = ? ORDER BY created_at, id",
        (task_id,),
    ).fetchall()
    return {
        **dict(row),
        "updates": [task_update_response(db, update["id"]) for update in updates],
    }


def create_task(
    db: sqlite3.Connection,
    *,
    admin: AuthenticatedUser,
    payload: ResponseTaskCreate,
) -> dict[str, object]:
    db.execute("BEGIN IMMEDIATE")
    if db.execute("SELECT 1 FROM flood_problems WHERE id = ?", (payload.flood_problem_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Only an approved FloodProblem can receive a response task.")
    assignee = db.execute(
        "SELECT id FROM users WHERE id = ? AND role = ? AND is_active = 1",
        (payload.assigned_user_id, Role.FIELD_RESPONSE_PLANNING.value),
    ).fetchone()
    if assignee is None:
        raise HTTPException(status_code=422, detail="Select an active Field Response & Planning account.")
    task_id = str(uuid.uuid4())
    now = utc_now()
    due_at = payload.due_at.astimezone(timezone.utc).isoformat() if payload.due_at else None
    db.execute(
        """
        INSERT INTO response_tasks
            (id, flood_problem_id, instruction, details, priority, assigned_user_id,
             due_at, status, created_by_user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ASSIGNED', ?, ?, ?)
        """,
        (
            task_id, payload.flood_problem_id, payload.instruction.strip(), payload.details.strip(),
            payload.priority, payload.assigned_user_id, due_at, admin.id, now, now,
        ),
    )
    add_public_status(
        db,
        problem_id=payload.flood_problem_id,
        task_id=task_id,
        status="ASSIGNED",
        published_at=now,
    )
    write_audit(
        db,
        actor_user_id=admin.id,
        action="response_task.created",
        target_type="response_task",
        target_id=task_id,
        details={
            "flood_problem_id": payload.flood_problem_id,
            "assigned_user_id": payload.assigned_user_id,
            "priority": payload.priority,
        },
    )
    return response_task_response(db, task_id)


def update_task(
    db: sqlite3.Connection,
    *,
    field_user: AuthenticatedUser,
    task_id: str,
    payload: ResponseTaskUpdateCreate,
) -> dict[str, object]:
    db.execute("BEGIN IMMEDIATE")
    task = db.execute(
        "SELECT * FROM response_tasks WHERE id = ? AND assigned_user_id = ?",
        (task_id, field_user.id),
    ).fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail="Assigned response task was not found.")
    expected = TRANSITIONS.get(task["status"])
    if expected != payload.new_status:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid response transition from {task['status']} to {payload.new_status}.",
        )
    update_id = str(uuid.uuid4())
    now = utc_now()
    completion_status = "PENDING_REVIEW" if payload.new_status == "RESOLVED" else task["completion_status"]
    db.execute(
        """
        INSERT INTO task_updates
            (id, response_task_id, actor_user_id, previous_status, new_status,
             action_taken, condition, internal_notes, blockers, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            update_id, task_id, field_user.id, task["status"], payload.new_status,
            payload.action_taken.strip(), payload.condition.strip(), payload.internal_notes.strip(),
            payload.blockers.strip(), now,
        ),
    )
    evidence = validated_evidence(payload.evidence)
    for item, content in evidence:
        db.execute(
            """
            INSERT INTO task_evidence
                (id, task_update_id, uploader_user_id, file_name, content_type,
                 size_bytes, sha256, content, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()), update_id, field_user.id, item.file_name.strip(),
                item.content_type, len(content), hashlib.sha256(content).hexdigest(), content, now,
            ),
        )
    db.execute(
        "UPDATE response_tasks SET status = ?, completion_status = ?, updated_at = ? WHERE id = ?",
        (payload.new_status, completion_status, now, task_id),
    )
    add_public_status(
        db,
        problem_id=task["flood_problem_id"],
        task_id=task_id,
        status=payload.new_status,
        published_at=now,
    )
    write_audit(
        db,
        actor_user_id=field_user.id,
        action="response_task.transitioned",
        target_type="response_task",
        target_id=task_id,
        details={"previous_status": task["status"], "new_status": payload.new_status},
    )
    return response_task_response(db, task_id)


def review_task_completion(
    db: sqlite3.Connection,
    *,
    admin: AuthenticatedUser,
    task_id: str,
    payload: ResponseTaskCompletionReview,
) -> dict[str, object]:
    db.execute("BEGIN IMMEDIATE")
    task = db.execute("SELECT * FROM response_tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail="Response task was not found.")
    if task["status"] != "RESOLVED" or task["completion_status"] != "PENDING_REVIEW":
        raise HTTPException(status_code=409, detail="This task has no completion update awaiting review.")
    now = utc_now()
    next_status = "RESOLVED" if payload.decision == "APPROVE" else "ACTION_REQUIRED"
    next_completion_status = "APPROVED" if payload.decision == "APPROVE" else "RETURNED"
    db.execute(
        """
        INSERT INTO task_updates
            (id, response_task_id, actor_user_id, previous_status, new_status,
             action_taken, condition, internal_notes, blockers, completion_decision, created_at)
        VALUES (?, ?, ?, ?, ?, '', '', ?, '', ?, ?)
        """,
        (
            str(uuid.uuid4()), task_id, admin.id, task["status"], next_status,
            payload.internal_notes.strip(), payload.decision, now,
        ),
    )
    db.execute(
        "UPDATE response_tasks SET status = ?, completion_status = ?, updated_at = ? WHERE id = ?",
        (next_status, next_completion_status, now, task_id),
    )
    add_public_status(
        db,
        problem_id=task["flood_problem_id"],
        task_id=task_id,
        status=next_status,
        published_at=now,
        summary=(
            "An administrator confirmed the response is complete."
            if payload.decision == "APPROVE"
            else None
        ),
    )
    write_audit(
        db,
        actor_user_id=admin.id,
        action="response_task.completion_reviewed",
        target_type="response_task",
        target_id=task_id,
        details={"decision": payload.decision, "status": next_status},
    )
    return response_task_response(db, task_id)


def public_status_updates(db: sqlite3.Connection, report_id: str) -> list[dict[str, object]]:
    rows = db.execute(
        """
        SELECT id, status, summary, published_at FROM public_status_updates
        WHERE citizen_report_id = ? ORDER BY published_at, id
        """,
        (report_id,),
    ).fetchall()
    return [dict(row) for row in rows]
