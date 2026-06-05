from __future__ import annotations

from .completed_sports_terms_parser import evaluate_completed_sports_terms


def evaluate_golf_terms(candidate: dict[str, object]) -> dict[str, object]:
    return dict(evaluate_completed_sports_terms(candidate))

