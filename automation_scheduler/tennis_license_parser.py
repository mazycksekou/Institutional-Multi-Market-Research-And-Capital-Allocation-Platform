from __future__ import annotations

from .completed_sports_license_parser import evaluate_completed_sports_license


def evaluate_tennis_license(candidate: dict[str, object]) -> dict[str, object]:
    return dict(evaluate_completed_sports_license(candidate))
