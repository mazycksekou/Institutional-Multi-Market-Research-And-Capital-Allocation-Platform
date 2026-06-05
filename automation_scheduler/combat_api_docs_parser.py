from __future__ import annotations

from .completed_sports_api_docs_parser import evaluate_completed_sports_api_docs


def evaluate_combat_api_docs(candidate: dict[str, object]) -> dict[str, object]:
    return dict(evaluate_completed_sports_api_docs(candidate))
