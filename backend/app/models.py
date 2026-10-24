from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

RiskLevel = Literal["Low", "Moderate", "High", "Critical"]
DataState = Literal["Available", "Stale", "Unavailable"]
SourceName = Literal["IMD", "CWC", "PMC", "GIS"]
RoleCode = Literal["CITIZEN", "FIELD_RESPONSE_PLANNING", "DISASTER_MANAGEMENT_ADMIN"]
MODEL_VERSION = "replay-logistic-baseline-v1"
ReportCategory = Literal["WATERLOGGING", "FLOODING", "BLOCKED_DRAINAGE", "OVERFLOW", "OTHER"]
Severity = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)


class DemoLoginRequest(BaseModel):
    role: RoleCode


class CreateUserRequest(BaseModel):
    email: str
    password: str = Field(min_length=12, max_length=256)
    role: RoleCode


class UserResponse(BaseModel):
    id: str
    email: str
    role: RoleCode
    is_demo: bool


class RiskFeatureExplanation(BaseModel):
    feature: str
    input_value: float
    logit_contribution: float
    interpretation: Literal["increases", "decreases", "neutral"]


class RiskPredictionResponse(BaseModel):
    id: str
    location_id: str
    score: int = Field(ge=0, le=100)
    risk_category: RiskLevel
    updated_at: str
    prediction_time: str
    drivers: list[str]
    model_version: str | None = None
    data_mode: Literal["replay", "live", "unknown"]
    feature_explanations: list[RiskFeatureExplanation] = Field(default_factory=list)


class RiskObservationAnalytics(BaseModel):
    source_type: Literal["FIELD_REPORT", "FIELD_VERIFICATION"]
    outcome: Literal["PROBLEM_FOUND", "INSPECTED_NO_PROBLEM_FOUND", "VERIFIED", "NOT_VERIFIED"]
    observed_at: str
    review_status: str | None
    linked_prediction_id: str | None


class RiskPredictionHistoryItem(BaseModel):
    id: str
    score: int = Field(ge=0, le=100)
    risk_category: RiskLevel
    prediction_time: str
    created_at: str
    model_version: str
    data_mode: Literal["replay", "live", "unknown"]


class RiskAnalyticsLocation(BaseModel):
    location_id: str
    name: str
    area: str
    historical_hotspot_reference: bool
    latest_prediction: RiskPredictionHistoryItem | None
    prediction_history: list[RiskPredictionHistoryItem]
    observation_history: list[RiskObservationAnalytics]
    officially_approved_problem_count: int


class RiskAnalyticsSummary(BaseModel):
    data_mode: Literal["replay", "live", "unknown"]
    model_versions: list[str]
    prediction_snapshots: int
    latest_snapshot_high_risk_locations: int
    historical_hotspot_references: int
    field_problem_findings: int
    no_problem_inspections: int
    verified_citizen_report_findings: int
    not_verified_citizen_reports: int
    officially_approved_problems: int
    high_risk_with_problem_observation: int
    high_risk_with_no_problem_inspection: int
    high_risk_without_matching_inspection: int
    lower_risk_with_problem_observation: int
    period_start: str | None
    period_end: str | None
    evaluation_notice: str


class RiskAnalyticsResponse(BaseModel):
    summary: RiskAnalyticsSummary
    locations: list[RiskAnalyticsLocation]


class MapFeatureResponse(BaseModel):
    id: str
    feature_type: Literal["CITIZEN_REPORT", "FIELD_OBSERVATION", "OFFICIAL_PROBLEM"]
    title: str
    area: str
    latitude: float
    longitude: float
    status: str
    observed_at: str
    category: ReportCategory | None = None
    outcome: Literal["PROBLEM_FOUND", "INSPECTED_NO_PROBLEM_FOUND"] | None = None
    severity: Severity | None = None


class RainfallContext(BaseModel):
    current: str
    forecast: str
    nowcast: str
    outlook: str


class DataSourceStatus(BaseModel):
    name: SourceName
    type: str
    state: DataState
    last_updated: str
    detail: str


class DemoLocationContext(BaseModel):
    citizen_report_count: int = Field(ge=0)
    citizen_report_examples: list[str]
    field_observation_summary: str
    official_problem_status: Literal["Active", "Pending Inspection", "Monitored", "Logged"]
    official_problem_summary: str
    contextual_notes: str
    source_label: str = "User-supplied demonstration scenario; not verified."


class LocationResponse(BaseModel):
    id: str
    risk_prediction_id: str | None = None
    name: str
    area: str
    risk: RiskLevel
    score: int = Field(ge=0, le=100)
    updated_at: str
    prediction_time: str
    current_rainfall: str
    forecast_rainfall: str
    drivers: list[str]
    historical_hotspot: bool
    coordinates: tuple[float, float]
    model_version: str | None = None
    data_mode: Literal["replay", "live", "unknown"] = "unknown"
    feature_explanations: list[RiskFeatureExplanation] = Field(default_factory=list)
    demo_context: DemoLocationContext | None = None


class DashboardResponse(BaseModel):
    last_updated: str
    rainfall: RainfallContext
    sources: list[DataSourceStatus]
    locations: list[LocationResponse]
    model_version: str | None = None


class SourceStatusResponse(BaseModel):
    sources: list[DataSourceStatus]


class PriorityItem(BaseModel):
    rank: int
    location_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_category: RiskLevel


class PriorityResponse(BaseModel):
    priorities: list[PriorityItem]


class ReportLocation(BaseModel):
    location_id: str | None = None
    location_name: str | None = Field(default=None, min_length=1, max_length=160)
    area: str = Field(default="", max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def validate_location(self):
        if self.location_id:
            if any(value is not None for value in (self.location_name, self.latitude, self.longitude)):
                raise ValueError("Use either a known location or a new location with coordinates.")
        elif not self.location_name or self.latitude is None or self.longitude is None:
            raise ValueError("A new location requires a name and coordinates.")
        return self


class EvidenceUpload(BaseModel):
    file_name: str = Field(min_length=1, max_length=180)
    content_type: Literal["image/jpeg", "image/png", "image/webp", "application/pdf"]
    content_base64: str = Field(min_length=4, max_length=7_000_000)


class EvidenceResponse(BaseModel):
    id: str
    file_name: str
    content_type: str
    size_bytes: int
    sha256: str
    download_url: str


class CitizenReportCreate(BaseModel):
    location: ReportLocation
    category: ReportCategory
    description: str = Field(min_length=10, max_length=2000)
    evidence: list[EvidenceUpload] = Field(default_factory=list, max_length=3)


class CitizenReportUpdate(BaseModel):
    description: str = Field(min_length=10, max_length=2000)
    evidence: list[EvidenceUpload] = Field(default_factory=list, max_length=3)


class FieldVerificationCreate(BaseModel):
    outcome: Literal["VERIFIED", "NOT_VERIFIED"]
    observed_condition: str = Field(min_length=3, max_length=1000)
    severity: Severity | None = None
    notes: str = Field(default="", max_length=2000)
    evidence: list[EvidenceUpload] = Field(default_factory=list, max_length=3)


class FieldReportCreate(BaseModel):
    location: ReportLocation
    category: ReportCategory
    description: str = Field(min_length=10, max_length=2000)
    observed_condition: str = Field(min_length=3, max_length=1000)
    outcome: Literal["PROBLEM_FOUND", "INSPECTED_NO_PROBLEM_FOUND"]
    severity: Severity | None = None
    prediction_id: str | None = None
    citizen_report_id: str | None = None
    evidence: list[EvidenceUpload] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_outcome(self):
        if self.outcome == "PROBLEM_FOUND" and self.severity is None:
            raise ValueError("Severity is required when a problem is observed.")
        return self


class FieldReportSupplement(BaseModel):
    description: str = Field(min_length=10, max_length=2000)
    observed_condition: str = Field(min_length=3, max_length=1000)
    outcome: Literal["PROBLEM_FOUND", "INSPECTED_NO_PROBLEM_FOUND"]
    severity: Severity | None = None
    evidence: list[EvidenceUpload] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_outcome(self):
        if self.outcome == "PROBLEM_FOUND" and self.severity is None:
            raise ValueError("Severity is required when a problem is observed.")
        return self


class ReportReviewCreate(BaseModel):
    decision: Literal["REQUEST_INFORMATION", "APPROVE", "REJECT"]
    requested_information: str = Field(default="", max_length=2000)
    severity: Severity | None = None

    @model_validator(mode="after")
    def validate_request(self):
        if self.decision == "REQUEST_INFORMATION" and len(self.requested_information.strip()) < 3:
            raise ValueError("Describe the information needed.")
        return self


class FieldVerificationResponse(BaseModel):
    id: str
    verifier_user_id: str
    outcome: Literal["VERIFIED", "NOT_VERIFIED"]
    observed_condition: str
    severity: Severity | None
    notes: str
    verified_at: str
    evidence: list[EvidenceResponse]


class ReviewResponse(BaseModel):
    id: str
    reviewer_user_id: str
    decision: Literal["REQUEST_INFORMATION", "APPROVE", "REJECT"]
    requested_information: str
    severity: Severity | None
    reviewed_at: str


class CitizenReportResponse(BaseModel):
    id: str
    reporter_id: str
    location_id: str | None
    location_name: str
    area: str
    latitude: float | None
    longitude: float | None
    category: ReportCategory
    description: str
    status: Literal[
        "PENDING_VERIFICATION", "VERIFIED", "NOT_VERIFIED",
        "NEEDS_INFORMATION", "APPROVED", "REJECTED",
    ]
    submitted_at: str
    updated_at: str
    evidence: list[EvidenceResponse]
    verifications: list[FieldVerificationResponse]
    reviews: list[ReviewResponse]
    flood_problem_id: str | None


class CitizenFieldVerificationResponse(BaseModel):
    id: str
    outcome: Literal["VERIFIED", "NOT_VERIFIED"]
    observed_condition: str
    verified_at: str
    evidence: list[EvidenceResponse]


class CitizenReportPublicResponse(BaseModel):
    id: str
    location_id: str | None
    location_name: str
    area: str
    latitude: float | None
    longitude: float | None
    category: ReportCategory
    description: str
    status: Literal[
        "PENDING_VERIFICATION", "VERIFIED", "NOT_VERIFIED",
        "NEEDS_INFORMATION", "APPROVED", "REJECTED",
    ]
    submitted_at: str
    updated_at: str
    evidence: list[EvidenceResponse]
    verifications: list[CitizenFieldVerificationResponse]
    requested_information: str | None
    flood_problem_id: str | None


class FieldReportResponse(BaseModel):
    id: str
    author_user_id: str
    location_id: str | None
    location_name: str
    area: str
    latitude: float | None
    longitude: float | None
    prediction_id: str | None
    citizen_report_id: str | None
    category: ReportCategory
    description: str
    observed_condition: str
    outcome: Literal["PROBLEM_FOUND", "INSPECTED_NO_PROBLEM_FOUND"]
    severity: Severity | None
    status: Literal["PENDING_REVIEW", "NEEDS_INFORMATION", "APPROVED", "REJECTED"]
    observed_at: str
    updated_at: str
    evidence: list[EvidenceResponse]
    reviews: list[ReviewResponse]
    flood_problem_id: str | None


class FloodProblemResponse(BaseModel):
    id: str
    citizen_report_id: str | None
    field_report_id: str | None
    severity: Severity
    status: Literal["OPEN"]
    approved_by_user_id: str
    approved_at: str


class PublicStatusUpdateResponse(BaseModel):
    id: str
    status: str
    summary: str
    published_at: str


class CitizenReportProgressResponse(CitizenReportPublicResponse):
    public_status_updates: list[PublicStatusUpdateResponse]


class ResponseTaskCreate(BaseModel):
    flood_problem_id: str
    instruction: str = Field(min_length=3, max_length=500)
    details: str = Field(default="", max_length=2000)
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"]
    assigned_user_id: str
    due_at: datetime | None = None

    @model_validator(mode="after")
    def validate_deadline(self):
        if self.due_at is not None:
            if self.due_at.tzinfo is None or self.due_at.utcoffset() is None:
                raise ValueError("Task deadlines must include a timezone.")
            if self.due_at <= datetime.now(self.due_at.tzinfo):
                raise ValueError("Task deadlines must be in the future.")
        return self


class ResponseTaskUpdateCreate(BaseModel):
    new_status: Literal["ACCEPTED", "EN_ROUTE", "INSPECTED", "ACTION_REQUIRED", "RESOLVED"]
    action_taken: str = Field(min_length=3, max_length=2000)
    condition: str = Field(default="", max_length=1000)
    internal_notes: str = Field(default="", max_length=2000)
    blockers: str = Field(default="", max_length=1000)
    evidence: list[EvidenceUpload] = Field(default_factory=list, max_length=3)


class ResponseTaskCompletionReview(BaseModel):
    decision: Literal["APPROVE", "RETURN_FOR_ACTION"]
    internal_notes: str = Field(default="", max_length=2000)


class ResponseTaskEvidenceResponse(EvidenceResponse):
    uploaded_at: str


class ResponseTaskUpdateResponse(BaseModel):
    id: str
    actor_user_id: str
    previous_status: str
    new_status: str
    action_taken: str
    condition: str
    internal_notes: str
    blockers: str
    completion_decision: Literal["APPROVE", "RETURN_FOR_ACTION"] | None
    created_at: str
    evidence: list[ResponseTaskEvidenceResponse]


class ResponseTaskResponse(BaseModel):
    id: str
    flood_problem_id: str
    instruction: str
    details: str
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"]
    assigned_user_id: str
    assigned_user_email: str
    due_at: str | None
    status: Literal["ASSIGNED", "ACCEPTED", "EN_ROUTE", "INSPECTED", "ACTION_REQUIRED", "RESOLVED"]
    completion_status: Literal["NOT_SUBMITTED", "PENDING_REVIEW", "APPROVED", "RETURNED"]
    created_by_user_id: str
    created_at: str
    updated_at: str
    updates: list[ResponseTaskUpdateResponse]


class FieldUserResponse(BaseModel):
    id: str
    email: str
