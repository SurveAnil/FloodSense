import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.adapters.open_meteo import OPEN_METEO_URL, OpenMeteoWeatherProvider


class OpenMeteoWeatherProviderTests(unittest.TestCase):
    def response(self, observed_at: datetime) -> MagicMock:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "current": {
                "time": observed_at.isoformat(),
                "precipitation": 1.2,
                "rain": 0.8,
            },
        }).encode()
        return response

    @patch("app.adapters.open_meteo.urlopen")
    def test_live_observation_has_freshness_and_weather_values(self, urlopen: MagicMock) -> None:
        urlopen.return_value = self.response(datetime.now(timezone.utc))

        snapshot = OpenMeteoWeatherProvider().snapshot()

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, OPEN_METEO_URL)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)
        self.assertEqual(snapshot.source, "Open-Meteo")
        self.assertEqual(snapshot.state, "Available")
        self.assertIn("precipitation 1.2 mm", snapshot.detail)
        self.assertIn("rain 0.8 mm", snapshot.detail)
        self.assertTrue(snapshot.last_updated.endswith("+05:30"))

    @patch("app.adapters.open_meteo.urlopen")
    def test_old_observation_is_reported_as_stale(self, urlopen: MagicMock) -> None:
        urlopen.return_value = self.response(datetime.now(timezone.utc) - timedelta(hours=2))

        snapshot = OpenMeteoWeatherProvider().snapshot()

        self.assertEqual(snapshot.state, "Stale")

    @patch("app.adapters.open_meteo.urlopen", side_effect=TimeoutError("provider timed out"))
    def test_provider_failure_is_reported_as_unavailable(self, _urlopen: MagicMock) -> None:
        snapshot = OpenMeteoWeatherProvider().snapshot()

        self.assertEqual(snapshot.state, "Unavailable")
        self.assertIn("provider timed out", snapshot.detail)
