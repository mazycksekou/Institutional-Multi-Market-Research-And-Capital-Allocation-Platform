from __future__ import annotations

from typing import Any, Mapping

from src.brokerage.readiness import evaluate_future_execution_eligibility as _evaluate_future_execution_eligibility


def evaluate_future_execution_eligibility(
    candidate: Mapping[str, Any] | None = None,
    *,
    aggregate: Mapping[str, Any] | None = None,
    hard_gate_result: Mapping[str, Any] | None = None,
    actor_type: str = "system",
) -> dict[str, Any]:
    return _evaluate_future_execution_eligibility(
        candidate,
        aggregate=aggregate,
        hard_gate_result=hard_gate_result,
        actor_type=actor_type,
    )
