"""Out-of-sample probability calibration helpers."""
from __future__ import annotations

import math
from typing import Iterable, Sequence


def _clip_probability(value: float) -> float:
    return max(1e-6, min(1.0 - 1e-6, float(value)))


def _logit(value: float) -> float:
    p = _clip_probability(value)
    return math.log(p / (1.0 - p))


class IdentityCalibrator:
    """Pass-through calibrator used for small samples or missing dependencies."""

    method = "identity"

    def __init__(self, reason: str = "identity") -> None:
        self.reason = reason
        self.fitted = True

    def fit(self, probabilities: Sequence[float], outcomes: Sequence[int]) -> "IdentityCalibrator":
        self.sample_size = len(list(probabilities))
        self.positive_count = sum(1 for value in outcomes if int(value) == 1)
        return self

    def predict_proba(self, probabilities: Iterable[float]) -> list[float]:
        return [_clip_probability(float(value)) for value in probabilities]

    def metadata(self) -> dict[str, object]:
        return {
            "method": self.method,
            "reason": self.reason,
            "sample_size": getattr(self, "sample_size", 0),
            "positive_count": getattr(self, "positive_count", 0),
        }


class PlattCalibrator:
    """Platt scaling with lazy sklearn import and identity fallback."""

    method = "platt"

    def __init__(
        self,
        *,
        min_samples: int = 50,
        min_positive: int = 5,
        min_negative: int = 5,
    ) -> None:
        self.min_samples = min_samples
        self.min_positive = min_positive
        self.min_negative = min_negative
        self._model = None
        self._fallback: IdentityCalibrator | None = None
        self.sample_size = 0
        self.positive_count = 0

    def fit(self, probabilities: Sequence[float], outcomes: Sequence[int]) -> "PlattCalibrator":
        probs = [_clip_probability(float(value)) for value in probabilities]
        labels = [int(value) for value in outcomes]
        self.sample_size = len(probs)
        self.positive_count = sum(1 for value in labels if value == 1)
        negative_count = self.sample_size - self.positive_count

        if (
            self.sample_size < self.min_samples
            or self.positive_count < self.min_positive
            or negative_count < self.min_negative
        ):
            self._fallback = IdentityCalibrator("insufficient_calibration_sample").fit(probs, labels)
            return self

        try:
            from sklearn.linear_model import LogisticRegression
        except Exception:
            self._fallback = IdentityCalibrator("sklearn_unavailable").fit(probs, labels)
            return self

        try:
            features = [[_logit(value)] for value in probs]
            model = LogisticRegression(solver="lbfgs")
            model.fit(features, labels)
        except Exception:
            self._fallback = IdentityCalibrator("platt_fit_failed").fit(probs, labels)
            return self

        self._model = model
        self._fallback = None
        return self

    def predict_proba(self, probabilities: Iterable[float]) -> list[float]:
        probs = [_clip_probability(float(value)) for value in probabilities]
        if self._fallback is not None or self._model is None:
            fallback = self._fallback or IdentityCalibrator("not_fitted")
            return fallback.predict_proba(probs)

        features = [[_logit(value)] for value in probs]
        calibrated = self._model.predict_proba(features)[:, 1]
        return [_clip_probability(float(value)) for value in calibrated]

    def metadata(self) -> dict[str, object]:
        if self._fallback is not None:
            fallback = self._fallback.metadata()
            fallback["requested_method"] = self.method
            return fallback
        return {
            "method": self.method,
            "sample_size": self.sample_size,
            "positive_count": self.positive_count,
            "negative_count": self.sample_size - self.positive_count,
        }
