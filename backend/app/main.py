import hashlib
import json
import os
import uuid
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.auth import (
    SESSION_COOKIE,
    SESSION_HOURS,
    AuthenticatedUser,
    Role,
    create_session,
    get_current_user,
    initialize_demo_users,
    login,
    provision_user,
    require_role,
)
from app.database import connection, initialize_database, utc_now, write_audit
from app.models import (
    CreateUserRequest,
    CitizenReportCreate,
    CitizenReportPublicResponse,
    CitizenReportResponse,
    CitizenReportUpdate,
    CitizenReportProgressResponse,
    DashboardResponse,
    DemoLoginRequest,
    FieldReportCreate,
    FieldReportResponse,
    FieldReportSupplement,
    FieldVerificationCreate,
    FieldUserResponse,
    FloodProblemResponse,
    LocationResponse,
    MapFeatureResponse,
    LoginRequest,
    PriorityItem,
    PriorityResponse,
    RiskAnalyticsResponse,
    ReportReviewCreate,
    ResponseTaskCompletionReview,
    ResponseTaskCreate,
    ResponseTaskResponse,
    ResponseTaskUpdateCreate,
    RiskPredictionResponse,
    SourceStatusResponse,
    UserResponse,
)
from app.services.dashboard import DashboardService
from app.services.analytics import risk_observation_analytics
from app.services.reports import (
    citizen_report_public_response,
    citizen_report_response,
    field_report_response,
    insert_evidence,
    record_report_review,
    require_field_report,
    require_report,
    resolve_location,
)
from app.services.response_tasks import (
    create_task,
    public_status_updates,
    response_task_response,
    review_task_completion,
    update_task,
)


def citizen_report_progress_response(db, report_id: str) -> dict[str, object]:
    return {
        **citizen_report_public_response(db, report_id),
        "public_status_updates": public_status_updates(db, report_id),
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    initialize_demo_users()
    yield


app = FastAPI(
    title="FloodSense API",
    version="0.3.0",
    description="Flood-risk intelligence and role-aware decision support for Pune.",
    lifespan=lifespan,
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FLOODSENSE_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

service = DashboardService()


def set_session_cookie(response: Response, token: str) -> None:
    same_site = os.getenv("FLOODSENSE_COOKIE_SAMESITE", "lax").lower()
    secure = os.getenv("FLOODSENSE_COOKIE_SECURE", "").lower() == "true"
    if same_site not in {"lax", "strict", "none"}:
        raise RuntimeError("FLOODSENSE_COOKIE_SAMESITE must be lax, strict, or none.")
    if same_site == "none" and not secure:
        raise RuntimeError("FLOODSENSE_COOKIE_SECURE=true is required with SameSite=None.")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_HOURS * 60 * 60,
        httponly=True,
        secure=secure,
        samesite=same_site,
        path="/",
    )


def user_response(user: AuthenticatedUser) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, role=user.role.value, is_demo=user.is_demo)


def persisted_locations(location_id: str | None = None) -> list[LocationResponse]:
    query = """
        SELECT l.id, p.id AS risk_prediction_id, l.name, l.area, l.latitude, l.longitude, l.historical_hotspot,
               p.risk_category, p.score, p.updated_at, p.prediction_time,
               p.current_rainfall, p.forecast_rainfall, p.drivers_json,
               p.feature_explanations_json, p.model_version, p.data_mode
        FROM locations l JOIN risk_predictions p ON p.id = (
            SELECT latest.id
            FROM risk_predictions latest
            WHERE latest.location_id = l.id
            ORDER BY latest.created_at DESC, latest.rowid DESC
            LIMIT 1
        )
    """
    parameters: tuple[str, ...] = ()
    if location_id is not None:
        query += " WHERE l.id = ?"
        parameters = (location_id,)
    else:
        query += " ORDER BY p.score DESC, l.id"
    with connection() as db:
        rows = db.execute(query, parameters).fetchall()
    return [
        LocationResponse(
            id=row["id"],
            risk_prediction_id=row["risk_prediction_id"],
            name=row["name"],
            area=row["area"],
            risk=row["risk_category"],
            score=row["score"],
            updated_at=row["updated_at"],
            prediction_time=row["prediction_time"],
            current_rainfall=row["current_rainfall"],
            forecast_rainfall=row["forecast_rainfall"],
            drivers=json.loads(row["drivers_json"]),
            historical_hotspot=bool(row["historical_hotspot"]),
            coordinates=(row["latitude"], row["longitude"]),
            model_version=row["model_version"],
            data_mode=row["data_mode"],
            feature_explanations=json.loads(row["feature_explanations_json"] or "[]"),
        )
        for row in rows
    ]


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "data_mode": service.data_mode,
        "demo_mode": str(os.getenv("FLOODSENSE_DEMO_MODE", "").lower() == "true").lower(),
    }


@app.post("/api/auth/login", response_model=UserResponse, tags=["authentication"])
def authenticate(payload: LoginRequest, response: Response) -> UserResponse:
    user, token = login(payload.email, payload.password)
    set_session_cookie(response, token)
    with connection() as db:
        write_audit(db, actor_user_id=user.id, action="user.login", target_type="user", target_id=user.id)
    return user_response(user)


@app.get("/api/auth/me", response_model=UserResponse, tags=["authentication"])
def current_user(user: AuthenticatedUser = Depends(get_current_user)) -> UserResponse:
    return user_response(user)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["authentication"])
def logout(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    if session_token:
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        with connection() as db:
            db.execute(
                "UPDATE sessions SET revoked_at = ? WHERE token_hash = ? AND user_id = ?",
                (utc_now(), token_hash, user.id),
            )
            write_audit(db, actor_user_id=user.id, action="user.logout", target_type="user", target_id=user.id)
    logout_response = Response(status_code=status.HTTP_204_NO_CONTENT)
    logout_response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        secure=os.getenv("FLOODSENSE_COOKIE_SECURE", "").lower() == "true",
        samesite=os.getenv("FLOODSENSE_COOKIE_SAMESITE", "lax").lower(),
        path="/",
    )
    return logout_response


@app.post("/api/auth/demo-login", response_model=UserResponse, tags=["authentication"])
def demo_login(payload: DemoLoginRequest, response: Response) -> UserResponse:
    if os.getenv("FLOODSENSE_DEMO_MODE", "").lower() != "true":
        raise HTTPException(status_code=404, detail="Demo sign-in is disabled.")
    email = f"demo-{payload.role.lower()}@floodsense.invalid"
    with connection() as db:
        row = db.execute(
            "SELECT id, email, role, is_demo FROM users WHERE email = ? AND is_active = 1 AND is_demo = 1",
            (email,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=503, detail="Demo account is not provisioned.")
    user = AuthenticatedUser(row["id"], row["email"], Role(row["role"]), bool(row["is_demo"]))
    set_session_cookie(response, create_session(user.id))
    with connection() as db:
        write_audit(db, actor_user_id=user.id, action="user.demo_login", target_type="user", target_id=user.id)
    return user_response(user)


@app.post("/api/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(
    payload: CreateUserRequest,
    admin: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> UserResponse:
    user = provision_user(
        email=payload.email,
        password=payload.password,
        role=Role(payload.role),
        actor=admin,
    )
    return user_response(user)


@app.get("/api/dashboard", response_model=DashboardResponse, tags=["dashboard"])
def get_dashboard(user: AuthenticatedUser = Depends(get_current_user)) -> DashboardResponse:
    dashboard = service.dashboard()
    with connection() as db:
        sources = db.execute(
            "SELECT name, source_type, state, last_updated, detail FROM data_sources ORDER BY name"
        ).fetchall()
    return DashboardResponse(
        last_updated=dashboard.last_updated,
        rainfall=dashboard.rainfall,
        sources=[
            {
                "name": row["name"],
                "type": row["source_type"],
                "state": row["state"],
                "last_updated": row["last_updated"],
                "detail": row["detail"],
            }
            for row in sources
        ] if user.role != Role.CITIZEN else [],
        locations=persisted_locations(),
        model_version=dashboard.model_version,
    )


@app.get("/api/data/status", response_model=SourceStatusResponse, tags=["data"])
def get_data_status(
    _: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING, Role.DISASTER_MANAGEMENT_ADMIN)),
) -> SourceStatusResponse:
    with connection() as db:
        rows = db.execute(
            "SELECT name, source_type, state, last_updated, detail FROM data_sources ORDER BY name"
        ).fetchall()
    return SourceStatusResponse(
        sources=[
            {
                "name": row["name"],
                "type": row["source_type"],
                "state": row["state"],
                "last_updated": row["last_updated"],
                "detail": row["detail"],
            }
            for row in rows
        ]
    )


@app.get("/api/locations", response_model=list[LocationResponse], tags=["locations"])
def get_locations(_: AuthenticatedUser = Depends(get_current_user)) -> list[LocationResponse]:
    return persisted_locations()


@app.get("/api/locations/{location_id}", response_model=LocationResponse, tags=["locations"])
def get_location(
    location_id: str,
    _: AuthenticatedUser = Depends(get_current_user),
) -> LocationResponse:
    locations = persisted_locations(location_id)
    if not locations:
        raise HTTPException(status_code=404, detail="Location not found")
    return locations[0]


@app.get("/api/risk/predictions", response_model=list[RiskPredictionResponse], tags=["risk"])
def get_risk_predictions(user: AuthenticatedUser = Depends(get_current_user)) -> list[RiskPredictionResponse]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT id, location_id, score, risk_category, updated_at, prediction_time,
                   drivers_json, feature_explanations_json, model_version, data_mode
            FROM risk_predictions ORDER BY score DESC, location_id
            """
        ).fetchall()
    return [
        RiskPredictionResponse(
            id=row["id"],
            location_id=row["location_id"],
            score=row["score"],
            risk_category=row["risk_category"],
            updated_at=row["updated_at"],
            prediction_time=row["prediction_time"],
            drivers=json.loads(row["drivers_json"]),
            model_version=row["model_version"],
            data_mode=row["data_mode"],
            feature_explanations=json.loads(row["feature_explanations_json"] or "[]"),
        )
        for row in rows
    ]


@app.get(
    "/api/analytics/risk-observations",
    response_model=RiskAnalyticsResponse,
    tags=["analytics"],
)
def get_risk_observation_analytics(
    user: AuthenticatedUser = Depends(get_current_user),
) -> RiskAnalyticsResponse:
    with connection() as db:
        return risk_observation_analytics(
            db,
            public_only=user.role == Role.CITIZEN,
        )


@app.get(
    "/api/map/features",
    response_model=list[MapFeatureResponse],
    tags=["map"],
)
def get_map_features(
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[MapFeatureResponse]:
    with connection() as db:
        if user.role == Role.CITIZEN:
            report_filter = "c.reporter_id = ?"
            report_params: tuple[str, ...] = (user.id,)
        elif user.role == Role.FIELD_RESPONSE_PLANNING:
            report_filter = "c.status IN ('PENDING_VERIFICATION', 'NEEDS_INFORMATION')"
            report_params = ()
        else:
            report_filter = "1 = 1"
            report_params = ()
        citizen_reports = db.execute(
            f"""
            SELECT c.id, c.location_name AS title, c.area,
                   COALESCE(c.latitude, l.latitude) AS latitude,
                   COALESCE(c.longitude, l.longitude) AS longitude,
                   c.status, c.submitted_at AS observed_at, c.category
            FROM citizen_reports c
            LEFT JOIN locations l ON l.id = c.location_id
            WHERE {report_filter}
              AND COALESCE(c.latitude, l.latitude) IS NOT NULL
              AND COALESCE(c.longitude, l.longitude) IS NOT NULL
            ORDER BY c.submitted_at DESC, c.id
            """,
            report_params,
        ).fetchall()
        field_reports = db.execute(
            """
            SELECT f.id, f.location_name AS title, f.area,
                   COALESCE(f.latitude, l.latitude) AS latitude,
                   COALESCE(f.longitude, l.longitude) AS longitude,
                   f.status, f.observed_at, f.category, f.outcome, f.severity
            FROM field_reports f
            LEFT JOIN locations l ON l.id = f.location_id
            WHERE COALESCE(f.latitude, l.latitude) IS NOT NULL
              AND COALESCE(f.longitude, l.longitude) IS NOT NULL
            ORDER BY f.observed_at DESC, f.id
            """
        ).fetchall() if user.role != Role.CITIZEN else []
        official_problems = db.execute(
            """
            SELECT fp.id, COALESCE(c.location_name, f.location_name) AS title,
                   COALESCE(c.area, f.area) AS area,
                   COALESCE(c.latitude, f.latitude, l.latitude) AS latitude,
                   COALESCE(c.longitude, f.longitude, l.longitude) AS longitude,
                   fp.status, fp.approved_at AS observed_at,
                   COALESCE(c.category, f.category) AS category, fp.severity
            FROM flood_problems fp
            LEFT JOIN citizen_reports c ON c.id = fp.citizen_report_id
            LEFT JOIN field_reports f ON f.id = fp.field_report_id
            LEFT JOIN locations l ON l.id = COALESCE(c.location_id, f.location_id)
            WHERE COALESCE(c.latitude, f.latitude, l.latitude) IS NOT NULL
              AND COALESCE(c.longitude, f.longitude, l.longitude) IS NOT NULL
            ORDER BY fp.approved_at DESC, fp.id
            """
        ).fetchall()

    result = [
        MapFeatureResponse(
            id=row["id"],
            feature_type="CITIZEN_REPORT",
            title=row["title"],
            area=row["area"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            status=row["status"],
            observed_at=row["observed_at"],
            category=row["category"],
        )
        for row in citizen_reports
    ]
    result.extend(
        MapFeatureResponse(
            id=row["id"],
            feature_type="FIELD_OBSERVATION",
            title=row["title"],
            area=row["area"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            status=row["status"],
            observed_at=row["observed_at"],
            category=row["category"],
            outcome=row["outcome"],
            severity=row["severity"],
        )
        for row in field_reports
    )
    result.extend(
        MapFeatureResponse(
            id=row["id"],
            feature_type="OFFICIAL_PROBLEM",
            title=row["title"],
            area=row["area"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            status=row["status"],
            observed_at=row["observed_at"],
            category=row["category"],
            severity=row["severity"],
        )
        for row in official_problems
    )
    return result


@app.get("/api/priorities", response_model=PriorityResponse, tags=["priorities"])
def get_priorities(
    risk_category: str | None = Query(default=None, pattern="^(Low|Moderate|High|Critical)$"),
    _: AuthenticatedUser = Depends(get_current_user),
) -> PriorityResponse:
    with connection() as db:
        rows = db.execute(
            """
            SELECT location_id, score, risk_category FROM risk_predictions current
            WHERE current.id = (
                SELECT latest.id
                FROM risk_predictions latest
                WHERE latest.location_id = current.location_id
                ORDER BY latest.created_at DESC, latest.rowid DESC
                LIMIT 1
            )
              AND (? IS NULL OR risk_category = ?)
            ORDER BY score DESC, location_id
            """,
            (risk_category, risk_category),
        ).fetchall()
    return PriorityResponse(
        priorities=[
            PriorityItem(
                rank=index,
                location_id=row["location_id"],
                risk_score=row["score"],
                risk_category=row["risk_category"],
            )
            for index, row in enumerate(rows, start=1)
        ]
    )


@app.post(
    "/api/reports",
    response_model=CitizenReportProgressResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["citizen reports"],
)
def create_citizen_report(
    payload: CitizenReportCreate,
    citizen: AuthenticatedUser = Depends(require_role(Role.CITIZEN)),
) -> CitizenReportProgressResponse:
    now = utc_now()
    report_id = str(uuid.uuid4())
    with connection() as db:
        location = resolve_location(db, payload.location)
        db.execute(
            """
            INSERT INTO citizen_reports
                (id, reporter_id, location_id, location_name, area, latitude, longitude,
                 category, description, status, submitted_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_VERIFICATION', ?, ?)
            """,
            (
                report_id, citizen.id, location["location_id"], location["location_name"],
                location["area"], location["latitude"], location["longitude"],
                payload.category, payload.description.strip(), now, now,
            ),
        )
        insert_evidence(
            db,
            uploader=citizen,
            evidence=payload.evidence,
            parent_column="citizen_report_id",
            parent_id=report_id,
        )
        write_audit(
            db,
            actor_user_id=citizen.id,
            action="citizen_report.created",
            target_type="citizen_report",
            target_id=report_id,
            details={"category": payload.category, "location_id": location["location_id"]},
        )
        return CitizenReportProgressResponse.model_validate(citizen_report_progress_response(db, report_id))


@app.get("/api/reports/mine", response_model=list[CitizenReportProgressResponse], tags=["citizen reports"])
def list_my_reports(
    citizen: AuthenticatedUser = Depends(require_role(Role.CITIZEN)),
) -> list[CitizenReportProgressResponse]:
    with connection() as db:
        rows = db.execute(
            "SELECT id FROM citizen_reports WHERE reporter_id = ? ORDER BY submitted_at DESC",
            (citizen.id,),
        ).fetchall()
        return [
            CitizenReportProgressResponse.model_validate(citizen_report_progress_response(db, row["id"]))
            for row in rows
        ]


@app.get(
    "/api/reports/mine/{report_id}",
    response_model=CitizenReportProgressResponse,
    tags=["citizen reports"],
)
def get_my_report(
    report_id: str,
    citizen: AuthenticatedUser = Depends(require_role(Role.CITIZEN)),
) -> CitizenReportProgressResponse:
    with connection() as db:
        report = require_report(db, report_id)
        if report["reporter_id"] != citizen.id:
            raise HTTPException(status_code=404, detail="Citizen report was not found.")
        return CitizenReportProgressResponse.model_validate(citizen_report_progress_response(db, report_id))


@app.post(
    "/api/reports/mine/{report_id}/update",
    response_model=CitizenReportProgressResponse,
    tags=["citizen reports"],
)
def update_my_report(
    report_id: str,
    payload: CitizenReportUpdate,
    citizen: AuthenticatedUser = Depends(require_role(Role.CITIZEN)),
) -> CitizenReportProgressResponse:
    now = utc_now()
    with connection() as db:
        report = require_report(db, report_id)
        if report["reporter_id"] != citizen.id:
            raise HTTPException(status_code=404, detail="Citizen report was not found.")
        if report["status"] != "NEEDS_INFORMATION":
            raise HTTPException(status_code=409, detail="Only reports requesting more information can be updated.")
        db.execute(
            """
            UPDATE citizen_reports
            SET description = ?, status = 'PENDING_VERIFICATION', updated_at = ?
            WHERE id = ?
            """,
            (payload.description.strip(), now, report_id),
        )
        insert_evidence(
            db,
            uploader=citizen,
            evidence=payload.evidence,
            parent_column="citizen_report_id",
            parent_id=report_id,
        )
        write_audit(
            db,
            actor_user_id=citizen.id,
            action="citizen_report.updated",
            target_type="citizen_report",
            target_id=report_id,
        )
        return CitizenReportProgressResponse.model_validate(citizen_report_progress_response(db, report_id))


@app.get(
    "/api/field/reports/pending",
    response_model=list[CitizenReportResponse],
    tags=["field reports"],
)
def list_pending_citizen_reports(
    _: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> list[CitizenReportResponse]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT id FROM citizen_reports
            WHERE status = 'PENDING_VERIFICATION'
            ORDER BY submitted_at, id
            """
        ).fetchall()
        return [
            CitizenReportResponse.model_validate(citizen_report_response(db, row["id"]))
            for row in rows
        ]


@app.post(
    "/api/field/reports/{report_id}/verify",
    response_model=CitizenReportResponse,
    tags=["field reports"],
)
def verify_citizen_report(
    report_id: str,
    payload: FieldVerificationCreate,
    field_user: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> CitizenReportResponse:
    verification_id = str(uuid.uuid4())
    verified_at = utc_now()
    with connection() as db:
        report = require_report(db, report_id)
        if report["status"] not in {"PENDING_VERIFICATION", "NEEDS_INFORMATION"}:
            raise HTTPException(status_code=409, detail="This report is not awaiting field verification.")
        db.execute(
            """
            INSERT INTO field_verifications
                (id, citizen_report_id, verifier_user_id, outcome, observed_condition,
                 severity, notes, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                verification_id, report_id, field_user.id, payload.outcome,
                payload.observed_condition.strip(), payload.severity,
                payload.notes.strip(), verified_at,
            ),
        )
        insert_evidence(
            db,
            uploader=field_user,
            evidence=payload.evidence,
            parent_column="field_verification_id",
            parent_id=verification_id,
        )
        next_status = "VERIFIED" if payload.outcome == "VERIFIED" else "NOT_VERIFIED"
        db.execute(
            "UPDATE citizen_reports SET status = ?, updated_at = ? WHERE id = ?",
            (next_status, verified_at, report_id),
        )
        write_audit(
            db,
            actor_user_id=field_user.id,
            action="field_verification.created",
            target_type="citizen_report",
            target_id=report_id,
            details={"verification_id": verification_id, "outcome": payload.outcome},
        )
        return CitizenReportResponse.model_validate(citizen_report_response(db, report_id))


@app.post(
    "/api/field/reports",
    response_model=FieldReportResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["field reports"],
)
def create_field_report(
    payload: FieldReportCreate,
    field_user: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> FieldReportResponse:
    report_id = str(uuid.uuid4())
    now = utc_now()
    with connection() as db:
        location = resolve_location(db, payload.location)
        if payload.prediction_id and db.execute(
            "SELECT 1 FROM risk_predictions WHERE id = ?", (payload.prediction_id,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="Selected risk prediction was not found.")
        if payload.citizen_report_id:
            linked_report = require_report(db, payload.citizen_report_id)
            if linked_report["status"] in {"APPROVED", "REJECTED"}:
                raise HTTPException(status_code=409, detail="A final citizen report cannot be linked to a new field report.")
        db.execute(
            """
            INSERT INTO field_reports
                (id, author_user_id, location_id, location_name, area, latitude, longitude,
                 prediction_id, citizen_report_id, category, description, observed_condition,
                 outcome, severity, status, observed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', ?, ?)
            """,
            (
                report_id, field_user.id, location["location_id"], location["location_name"],
                location["area"], location["latitude"], location["longitude"],
                payload.prediction_id, payload.citizen_report_id, payload.category,
                payload.description.strip(), payload.observed_condition.strip(),
                payload.outcome, payload.severity, now, now,
            ),
        )
        insert_evidence(
            db,
            uploader=field_user,
            evidence=payload.evidence,
            parent_column="field_report_id",
            parent_id=report_id,
        )
        write_audit(
            db,
            actor_user_id=field_user.id,
            action="field_report.created",
            target_type="field_report",
            target_id=report_id,
            details={
                "outcome": payload.outcome,
                "prediction_id": payload.prediction_id,
                "citizen_report_id": payload.citizen_report_id,
            },
        )
        return FieldReportResponse.model_validate(field_report_response(db, report_id))


@app.get(
    "/api/field/reports",
    response_model=list[FieldReportResponse],
    tags=["field reports"],
)
def list_field_reports(
    field_user: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> list[FieldReportResponse]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT id FROM field_reports
            WHERE author_user_id = ? ORDER BY observed_at DESC
            """,
            (field_user.id,),
        ).fetchall()
        return [
            FieldReportResponse.model_validate(field_report_response(db, row["id"]))
            for row in rows
        ]


@app.post(
    "/api/field/reports/{report_id}/supplement",
    response_model=FieldReportResponse,
    tags=["field reports"],
)
def supplement_field_report(
    report_id: str,
    payload: FieldReportSupplement,
    field_user: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> FieldReportResponse:
    now = utc_now()
    with connection() as db:
        report = require_field_report(db, report_id)
        if report["author_user_id"] != field_user.id:
            raise HTTPException(status_code=404, detail="Field report was not found.")
        if report["status"] != "NEEDS_INFORMATION":
            raise HTTPException(status_code=409, detail="Only field reports requesting more information can be updated.")
        db.execute(
            """
            UPDATE field_reports
            SET description = ?, observed_condition = ?, outcome = ?, severity = ?,
                status = 'PENDING_REVIEW', updated_at = ?
            WHERE id = ?
            """,
            (
                payload.description.strip(), payload.observed_condition.strip(),
                payload.outcome, payload.severity, now, report_id,
            ),
        )
        insert_evidence(
            db,
            uploader=field_user,
            evidence=payload.evidence,
            parent_column="field_report_id",
            parent_id=report_id,
        )
        write_audit(
            db,
            actor_user_id=field_user.id,
            action="field_report.supplemented",
            target_type="field_report",
            target_id=report_id,
        )
        return FieldReportResponse.model_validate(field_report_response(db, report_id))


@app.get("/api/admin/reports", tags=["report review"])
def list_reports_for_review(
    _: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> dict[str, list[dict[str, object]]]:
    with connection() as db:
        citizen_ids = db.execute(
            """
            SELECT id FROM citizen_reports
            WHERE status IN ('VERIFIED', 'NOT_VERIFIED', 'NEEDS_INFORMATION')
            ORDER BY submitted_at
            """
        ).fetchall()
        field_ids = db.execute(
            """
            SELECT id FROM field_reports
            WHERE status IN ('PENDING_REVIEW', 'NEEDS_INFORMATION')
            ORDER BY observed_at
            """
        ).fetchall()
        return {
            "citizen_reports": [citizen_report_response(db, row["id"]) for row in citizen_ids],
            "field_reports": [field_report_response(db, row["id"]) for row in field_ids],
        }


@app.post(
    "/api/admin/reports/{source_type}/{source_id}/review",
    tags=["report review"],
)
def review_report(
    source_type: str,
    source_id: str,
    payload: ReportReviewCreate,
    admin: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> dict[str, object]:
    with connection() as db:
        review = record_report_review(
            db,
            admin=admin,
            source_type=source_type.upper(),
            source_id=source_id,
            decision=payload.decision,
            requested_information=payload.requested_information,
            severity=payload.severity,
        )
        return review


@app.get(
    "/api/admin/flood-problems",
    response_model=list[FloodProblemResponse],
    tags=["official problems"],
)
def list_flood_problems(
    _: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> list[FloodProblemResponse]:
    with connection() as db:
        rows = db.execute(
            "SELECT * FROM flood_problems ORDER BY approved_at DESC"
        ).fetchall()
        return [FloodProblemResponse.model_validate(dict(row)) for row in rows]


@app.get("/api/admin/field-users", response_model=list[FieldUserResponse], tags=["response coordination"])
def list_field_users(
    _: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> list[FieldUserResponse]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT id, email FROM users
            WHERE role = ? AND is_active = 1
            ORDER BY email
            """,
            (Role.FIELD_RESPONSE_PLANNING.value,),
        ).fetchall()
        return [FieldUserResponse.model_validate(dict(row)) for row in rows]


@app.post(
    "/api/admin/response-tasks",
    response_model=ResponseTaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["response coordination"],
)
def create_response_task(
    payload: ResponseTaskCreate,
    admin: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> ResponseTaskResponse:
    with connection() as db:
        return ResponseTaskResponse.model_validate(create_task(db, admin=admin, payload=payload))


@app.get(
    "/api/admin/response-tasks",
    response_model=list[ResponseTaskResponse],
    tags=["response coordination"],
)
def list_response_tasks(
    _: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> list[ResponseTaskResponse]:
    with connection() as db:
        rows = db.execute(
            "SELECT id FROM response_tasks ORDER BY created_at DESC, id"
        ).fetchall()
        return [
            ResponseTaskResponse.model_validate(response_task_response(db, row["id"]))
            for row in rows
        ]


@app.get(
    "/api/field/response-tasks",
    response_model=list[ResponseTaskResponse],
    tags=["response coordination"],
)
def list_assigned_response_tasks(
    field_user: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> list[ResponseTaskResponse]:
    with connection() as db:
        rows = db.execute(
            """
            SELECT id FROM response_tasks
            WHERE assigned_user_id = ? ORDER BY
                CASE priority WHEN 'URGENT' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'NORMAL' THEN 2 ELSE 3 END,
                due_at, created_at
            """,
            (field_user.id,),
        ).fetchall()
        return [
            ResponseTaskResponse.model_validate(response_task_response(db, row["id"]))
            for row in rows
        ]


@app.post(
    "/api/field/response-tasks/{task_id}/updates",
    response_model=ResponseTaskResponse,
    tags=["response coordination"],
)
def create_response_task_update(
    task_id: str,
    payload: ResponseTaskUpdateCreate,
    field_user: AuthenticatedUser = Depends(require_role(Role.FIELD_RESPONSE_PLANNING)),
) -> ResponseTaskResponse:
    with connection() as db:
        return ResponseTaskResponse.model_validate(
            update_task(db, field_user=field_user, task_id=task_id, payload=payload)
        )


@app.post(
    "/api/admin/response-tasks/{task_id}/completion-review",
    response_model=ResponseTaskResponse,
    tags=["response coordination"],
)
def review_response_task_completion(
    task_id: str,
    payload: ResponseTaskCompletionReview,
    admin: AuthenticatedUser = Depends(require_role(Role.DISASTER_MANAGEMENT_ADMIN)),
) -> ResponseTaskResponse:
    with connection() as db:
        return ResponseTaskResponse.model_validate(
            review_task_completion(db, admin=admin, task_id=task_id, payload=payload)
        )


@app.get("/api/evidence/{attachment_id}", tags=["evidence"])
def download_evidence(
    attachment_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    with connection() as db:
        attachment = db.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        task_file = None
        if attachment is None:
            task_file = db.execute(
                """
                SELECT e.*, t.assigned_user_id FROM task_evidence e
                JOIN task_updates u ON u.id = e.task_update_id
                JOIN response_tasks t ON t.id = u.response_task_id
                WHERE e.id = ?
                """,
                (attachment_id,),
            ).fetchone()
        if attachment is None and task_file is None:
            raise HTTPException(status_code=404, detail="Evidence was not found.")
        if task_file is not None:
            allowed = (
                user.role == Role.DISASTER_MANAGEMENT_ADMIN
                or (
                    user.role == Role.FIELD_RESPONSE_PLANNING
                    and task_file["assigned_user_id"] == user.id
                )
            )
            if not allowed:
                raise HTTPException(status_code=404, detail="Evidence was not found.")
            write_audit(
                db,
                actor_user_id=user.id,
                action="response_task.evidence_accessed",
                target_type="task_evidence",
                target_id=attachment_id,
            )
            content = bytes(task_file["content"])
            content_type = task_file["content_type"]
            file_name = task_file["file_name"]
        else:
            allowed = user.role == Role.DISASTER_MANAGEMENT_ADMIN
        if attachment is not None and user.role == Role.CITIZEN:
            allowed = db.execute(
                """
                SELECT 1 FROM attachments a
                WHERE a.id = ? AND (
                    EXISTS (
                        SELECT 1 FROM citizen_reports c
                        WHERE c.id = a.citizen_report_id AND c.reporter_id = ?
                    )
                    OR EXISTS (
                        SELECT 1 FROM field_verifications v
                        JOIN citizen_reports c ON c.id = v.citizen_report_id
                        WHERE v.id = a.field_verification_id AND c.reporter_id = ?
                    )
                    OR EXISTS (
                        SELECT 1 FROM field_reports f
                        JOIN citizen_reports c ON c.id = f.citizen_report_id
                        WHERE f.id = a.field_report_id AND c.reporter_id = ?
                    )
                )
                """,
                (attachment_id, user.id, user.id, user.id),
            ).fetchone() is not None
        elif attachment is not None and user.role == Role.FIELD_RESPONSE_PLANNING:
            allowed = (
                attachment["citizen_report_id"] is not None
                or attachment["field_report_id"] is not None
                or attachment["field_verification_id"] is not None
            )
        if attachment is not None:
            if not allowed:
                raise HTTPException(status_code=404, detail="Evidence was not found.")
            write_audit(
                db,
                actor_user_id=user.id,
                action="evidence.accessed",
                target_type="attachment",
                target_id=attachment_id,
            )
            content = bytes(attachment["content"])
            content_type = attachment["content_type"]
            file_name = attachment["file_name"]
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(file_name)}",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
