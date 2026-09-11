from app.adapters.replay import ReplayDataAdapter
from app.adapters.provider_replay import build_replay_provider_adapters
from app.adapters.contracts import ProviderSnapshot
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
        self.providers = build_replay_provider_adapters(self.adapter)
        self.model = RiskModel()
        self.data_mode = self.adapter.data_mode

    def _locations(self) -> list[LocationResponse]:
        return [self.model.predict(record) for record in self.adapter.locations()]

    def source_status(self) -> SourceStatusResponse:
        return SourceStatusResponse(sources=[
            DataSourceStatus(
                name=snapshot.source,
                type=self._source_type(snapshot.source),
                state=snapshot.state,
                last_updated=snapshot.last_updated,
                detail=snapshot.detail,
            )
            for snapshot in self._provider_snapshots()
        ])

    def _provider_snapshots(self) -> list[ProviderSnapshot]:
        return [
            provider.snapshot()
            for provider in self.providers.values()
        ]

    @staticmethod
    def _source_type(source: str) -> str:
        return {
            "IMD": "Rainfall & forecast",
            "CWC": "Hydrological context",
            "PMC": "Historical hotspots",
            "GIS": "Spatial context",
        }[source]

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
