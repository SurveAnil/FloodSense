from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import DashboardResponse, LocationResponse, PriorityResponse, SourceStatusResponse
from app.services.dashboard import DashboardService

app = FastAPI(
    title="FloodSense API",
    version="0.2.0",
    description="Local Phase 2 API for Pune urban flood-risk decision support.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

service = DashboardService()


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "data_mode": service.data_mode}


@app.get("/api/dashboard", response_model=DashboardResponse, tags=["dashboard"])
def get_dashboard() -> DashboardResponse:
    return service.dashboard()


@app.get("/api/data/status", response_model=SourceStatusResponse, tags=["data"])
def get_data_status() -> SourceStatusResponse:
    return service.source_status()


@app.get("/api/locations/{location_id}", response_model=LocationResponse, tags=["locations"])
def get_location(location_id: str) -> LocationResponse:
    location = service.location(location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@app.get("/api/priorities", response_model=PriorityResponse, tags=["priorities"])
def get_priorities(risk_category: str | None = Query(default=None)) -> PriorityResponse:
    return service.priorities(risk_category)
