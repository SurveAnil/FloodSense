from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderSnapshot:
    """Normalized provider payload used by the application service."""

    source: str
    state: str
    last_updated: str
    detail: str
    payload: dict[str, Any]


class DataProviderAdapter(Protocol):
    """Contract for replacing replay data with a verified provider adapter."""

    source: str

    def snapshot(self) -> ProviderSnapshot:
        """Return a normalized snapshot or an explicit unavailable state."""


class LocationDataProviderAdapter(DataProviderAdapter, Protocol):
    def locations(self) -> list[dict[str, Any]]:
        """Return normalized location observations for the provider."""
