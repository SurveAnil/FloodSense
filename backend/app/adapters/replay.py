from datetime import datetime
from pathlib import Path
import json
from typing import Any


class ReplayDataAdapter:
    """Reads a versioned local replay snapshot until provider contracts are verified.

    This intentionally does not pretend to be an IMD/CWC/PMC live integration.
    The snapshot keeps local development reproducible and makes the adapter
    contract replaceable when access and schemas are confirmed.
    """

    data_mode = "replay"

    def __init__(self) -> None:
        path = Path(__file__).resolve().parents[2] / "data" / "pune_replay.json"
        self._payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    def snapshot(self) -> dict[str, Any]:
        return self._payload["snapshot"]

    def locations(self) -> list[dict[str, Any]]:
        return self._payload["locations"]

    def sources(self) -> list[dict[str, str]]:
        sources = []
        for source in self._payload["sources"]:
            item = dict(source)
            item["last_updated"] = item.pop("lastUpdated")
            sources.append(item)
        return sources

    @staticmethod
    def observed_at() -> datetime:
        return datetime.fromisoformat("2026-09-10T14:32:00+05:30")
