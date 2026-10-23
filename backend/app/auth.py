import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import Cookie, Depends, HTTPException, status

from app.database import connection, utc_now, write_audit

SESSION_COOKIE = "floodsense_session"
SESSION_HOURS = 8
PBKDF2_ITERATIONS = 310_000


class Role(str, Enum):
    CITIZEN = "CITIZEN"
    FIELD_RESPONSE_PLANNING = "FIELD_RESPONSE_PLANNING"
    DISASTER_MANAGEMENT_ADMIN = "DISASTER_MANAGEMENT_ADMIN"


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str
    role: Role
    is_demo: bool


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt_hex, digest_hex = encoded.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds),
        )
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=422, detail="A valid email address is required.")
    return normalized


def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(hours=SESSION_HOURS)).isoformat()
    with connection() as db:
        db.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token_hash, user_id, expires, now.isoformat()),
        )
    return token


def get_current_user(session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE)) -> AuthenticatedUser:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    with connection() as db:
        row = db.execute(
            """
            SELECT u.id, u.email, u.role, u.is_demo, s.expires_at, s.revoked_at
            FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND u.is_active = 1
            """,
            (token_hash,),
        ).fetchone()
    if (
        row is None
        or row["revoked_at"] is not None
        or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is invalid or expired.")
    return AuthenticatedUser(
        id=row["id"],
        email=row["email"],
        role=Role(row["role"]),
        is_demo=bool(row["is_demo"]),
    )


def require_role(*roles: Role):
    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to perform this action.")
        return user

    return dependency


def login(email: str, password: str) -> tuple[AuthenticatedUser, str]:
    normalized = validate_email(email)
    with connection() as db:
        row = db.execute(
            "SELECT id, email, password_hash, role, is_demo FROM users WHERE email = ? AND is_active = 1",
            (normalized,),
        ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    user = AuthenticatedUser(row["id"], row["email"], Role(row["role"]), bool(row["is_demo"]))
    return user, create_session(user.id)


def provision_user(
    *,
    email: str,
    password: str,
    role: Role,
    actor: AuthenticatedUser | None,
    is_demo: bool = False,
) -> AuthenticatedUser:
    normalized = validate_email(email)
    if len(password) < 12 or len(password) > 256:
        raise HTTPException(status_code=422, detail="Password must be 12 to 256 characters.")
    user_id = str(uuid.uuid4())
    with connection() as db:
        try:
            db.execute(
                """
                INSERT INTO users
                    (id, email, password_hash, role, is_active, is_demo, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (user_id, normalized, hash_password(password), role.value, int(is_demo), utc_now(), utc_now()),
            )
        except sqlite3.IntegrityError as error:
            if "UNIQUE constraint failed: users.email" in str(error):
                raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
            raise
        write_audit(
            db,
            actor_user_id=actor.id if actor else None,
            action="user.created",
            target_type="user",
            target_id=user_id,
            details={"role": role.value},
        )
    return AuthenticatedUser(user_id, normalized, role, is_demo)


def initialize_demo_users() -> None:
    if os.getenv("FLOODSENSE_DEMO_MODE", "").lower() != "true":
        return
    for role in Role:
        email = f"demo-{role.value.lower()}@floodsense.invalid"
        with connection() as db:
            exists = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if exists is None:
            provision_user(
                email=email,
                password=secrets.token_urlsafe(32),
                role=role,
                actor=None,
                is_demo=True,
            )
