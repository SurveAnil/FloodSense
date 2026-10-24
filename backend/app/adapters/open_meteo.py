import json
import math
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.adapters.contracts import ProviderSnapshot

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=18.5204&longitude=73.8567&current=precipitation,rain"
)
MAX_OBSERVATION_AGE = timedelta(hours=1)
CACHE_SECONDS = 300


class OpenMeteoWeatherProvider:
    source = "Open-Meteo"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cached_snapshot: ProviderSnapshot | None = None
        self._cached_at = 0.0

    def snapshot(self) -> ProviderSnapshot:
        with self._lock:
            now = time.monotonic()
            if self._cached_snapshot is not None and now - self._cached_at < CACHE_SECONDS:
                return self._cached_snapshot
            snapshot = self._fetch_snapshot()
            self._cached_snapshot = snapshot
            self._cached_at = now
            return snapshot

    def _fetch_snapshot(self) -> ProviderSnapshot:
        request = Request(
            OPEN_METEO_URL,
            headers={"User-Agent": "FloodSense/0.1 weather freshness check"},
        )
        try:
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read())
            current = payload["current"]
            observed_at = datetime.fromisoformat(current["time"].replace("Z", "+00:00"))
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=timezone.utc)
            precipitation = current["precipitation"]
            rain = current["rain"]
            if (
                isinstance(precipitation, bool)
                or not isinstance(precipitation, (int, float))
                or not math.isfinite(precipitation)
                or isinstance(rain, bool)
                or not isinstance(rain, (int, float))
                or not math.isfinite(rain)
            ):
                raise ValueError("Current precipitation values are not finite numbers.")
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            return self._unavailable(f"Open-Meteo request failed: {error}")
        except (AttributeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            return self._unavailable(f"Open-Meteo returned invalid current-weather data: {error}")

        now = datetime.now(timezone.utc)
        age = now - observed_at.astimezone(timezone.utc)
        state = "Available" if timedelta(0) <= age <= MAX_OBSERVATION_AGE else "Stale"
        observed_local = observed_at.astimezone(timezone(timedelta(hours=5, minutes=30)))
        return ProviderSnapshot(
            source=self.source,
            state=state,
            last_updated=observed_local.isoformat(timespec="minutes"),
            detail=(
                f"Live Open-Meteo observation; precipitation {precipitation:g} mm, "
                f"rain {rain:g} mm."
            ),
            payload=payload,
        )

    def _unavailable(self, detail: str) -> ProviderSnapshot:
        return ProviderSnapshot(
            source=self.source,
            state="Unavailable",
            last_updated="—",
            detail=detail,
            payload={},
        )
