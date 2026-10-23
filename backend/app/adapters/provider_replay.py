from typing import Any

from app.adapters.contracts import ProviderSnapshot
from app.adapters.replay import ReplayDataAdapter


class ReplayProviderAdapter:
    """Source-specific replay view until real provider contracts are verified."""

    def __init__(self, replay: ReplayDataAdapter, source: str) -> None:
        self._replay = replay
        self.source = source

    def snapshot(self) -> ProviderSnapshot:
        source = next(
            item for item in self._replay.sources() if item["name"] == self.source
        )
        payload: dict[str, Any] = {"source": self.source}
        return ProviderSnapshot(
            source=self.source,
            state=source["state"],
            last_updated=source["last_updated"],
            detail=source["detail"],
            payload=payload,
        )

    def locations(self) -> list[dict[str, Any]]:
        return self._replay.locations()


def build_replay_provider_adapters(
    replay: ReplayDataAdapter,
) -> dict[str, ReplayProviderAdapter]:
    return {
        source: ReplayProviderAdapter(replay, source)
        for source in ("IMD", "CWC", "PMC", "GIS")
    }
