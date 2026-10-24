from datetime import datetime
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.ml.features import FEATURE_NAMES, build_feature_vector
from app.models import LocationResponse


class RiskModel:
    """Small reproducible logistic baseline over the replay feature snapshot.

    The bundled training rows are replay/demo observations, not a validated
    historical Pune event dataset. The API exposes the output shape needed by
    the UI while keeping model selection and labels revisitable.
    """

    FEATURE_NAMES = FEATURE_NAMES

    def __init__(self) -> None:
        training = np.array([
            [6, 12, 0, 0], [8, 18, 0, 1], [12, 24, 1, 0],
            [15, 30, 1, 1], [18, 35, 0, 1], [22, 42, 1, 1],
            [4, 10, 0, 0], [10, 26, 1, 0], [14, 34, 1, 1],
            [20, 38, 0, 1], [7, 16, 0, 0], [16, 32, 1, 0],
        ], dtype=float)
        labels = np.array([0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1])
        self._model = LogisticRegression(random_state=42, solver="liblinear")
        self._model.fit(training, labels)

    def predict(self, record: dict[str, Any]) -> LocationResponse:
        features = build_feature_vector(record)
        probability = float(self._model.predict_proba(features)[0, 1])
        score = max(0, min(100, round(probability * 100)))
        risk = self._category(score)
        demo_scenario = record.get("demoScenario")
        if demo_scenario:
            score = int(demo_scenario["predictionScore"])
            risk = demo_scenario["riskState"]
        updated = record["updatedAt"]
        return LocationResponse(
            id=record["id"],
            name=record["name"],
            area=record["area"],
            risk=risk,
            score=score,
            updated_at=updated,
            prediction_time=record["predictionTime"],
            current_rainfall=f'{record["currentRainfallMm"]:.1f} mm',
            forecast_rainfall=f'{record["forecastRainfallMm"]:.0f} mm',
            drivers=record["drivers"],
            historical_hotspot=record["historicalHotspot"],
            coordinates=tuple(record["coordinates"]),
            illustrative_image_url=record.get("illustrativeImageUrl"),
            model_version="mentor-demo-scenario-v1" if demo_scenario else None,
        )

    def explain(self, record: dict[str, Any]) -> list[dict[str, float | str]]:
        features = build_feature_vector(record)[0]
        coefficients = self._model.coef_[0]
        explanations = []
        for name, value, coefficient in zip(self.FEATURE_NAMES, features, coefficients):
            contribution = float(value * coefficient)
            explanations.append({
                "feature": name,
                "input_value": float(value),
                "logit_contribution": contribution,
                "interpretation": (
                    "increases" if contribution > 0
                    else "decreases" if contribution < 0
                    else "neutral"
                ),
            })
        return explanations

    @staticmethod
    def _category(score: int) -> str:
        if score >= 75:
            return "Critical"
        if score >= 55:
            return "High"
        if score >= 35:
            return "Moderate"
        return "Low"
