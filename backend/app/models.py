from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["Low", "Moderate", "High", "Critical"]
DataState = Literal["Available", "Stale", "Unavailable"]
SourceName = Literal["IMD", "CWC", "PMC", "GIS"]


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


class LocationResponse(BaseModel):
    id: str
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


class DashboardResponse(BaseModel):
    last_updated: str
    rainfall: RainfallContext
    sources: list[DataSourceStatus]
    locations: list[LocationResponse]


class SourceStatusResponse(BaseModel):
    sources: list[DataSourceStatus]


class PriorityItem(BaseModel):
    rank: int
    location_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_category: RiskLevel


class PriorityResponse(BaseModel):
    priorities: list[PriorityItem]
