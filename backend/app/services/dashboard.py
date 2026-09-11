from app.adapters.replay import ReplayDataAdapter
from app.ml.risk_model import RiskModel
from app.models import (
    DashboardResponse,
    DataSourceStatus,
    LocationResponse,
    PriorityItem,
    PriorityResponse,
    RainfallContext,
    SourceStatusResponse,
)


class DashboardService:
    """Application boundary used by API handlers and future scheduled ingestion."""

    def __init__(self) -> None:
        self.adapter = ReplayDataAdapter()
        self.model = RiskModel()
        self.data_mode = self.adapter.data_mode

    def _locations(self) -> list[LocationResponse]:
        return [self.model.predict(record) for record in self.adapter.locations()]

    def source_status(self) -> SourceStatusResponse:
        return SourceStatusResponse(sources=[
            DataSourceStatus(**source) for source in self.adapter.sources()
        ])

    def dashboard(self) -> DashboardResponse:
        snapshot = self.adapter.snapshot()
        return DashboardResponse(
            last_updated=snapshot["last_updated"],
            rainfall=RainfallContext(**snapshot["rainfall"]),
            sources=self.source_status().sources,
            locations=self._locations(),
        )

    def location(self, location_id: str) -> LocationResponse | None:
        for location in self._locations():
            if location.id == location_id:
                return location
        return None

    def priorities(self, risk_category: str | None = None) -> PriorityResponse:
        locations = self._locations()
        if risk_category:
            locations = [location for location in locations if location.risk == risk_category]
        locations.sort(key=lambda location: (-location.score, location.id))
        return PriorityResponse(priorities=[
            PriorityItem(
                rank=index,
                location_id=location.id,
                risk_score=location.score,
                risk_category=location.risk,
            )
            for index, location in enumerate(locations, start=1)
        ])
