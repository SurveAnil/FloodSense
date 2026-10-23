from typing import Any

import numpy as np


FEATURE_NAMES = ("current_rainfall", "forecast_rainfall", "hotspot", "terrain_signal")


def build_feature_vector(record: dict[str, Any]) -> np.ndarray:
    """Map a normalized replay/provider record to the baseline feature order."""

    return np.array([[
        float(record["currentRainfallMm"]),
        float(record["forecastRainfallMm"]),
        int(bool(record["historicalHotspot"])),
        float(record["terrainSignal"]),
    ]], dtype=float)
