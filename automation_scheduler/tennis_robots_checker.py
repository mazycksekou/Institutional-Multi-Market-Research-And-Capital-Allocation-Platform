from __future__ import annotations

from .completed_sports_robots_checker import evaluate_completed_sports_robots


def evaluate_tennis_robots(candidate: dict[str, object]) -> dict[str, object]:
    return dict(evaluate_completed_sports_robots(candidate))
