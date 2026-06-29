from __future__ import annotations

from typing import Any

from src.core.risk_engine import simulate_stake_plan as _risk_simulate_stake_plan


def simulate_stake_plan(
    candidate: dict[str, Any],
    *,
    bankroll: float,
    risk_profile: str = "medium",
    max_loss_cap: float | None = None,
) -> dict[str, Any]:
    return _risk_simulate_stake_plan(
        candidate,
        bankroll=bankroll,
        risk_profile=risk_profile,
        max_loss_cap=max_loss_cap,
    )
