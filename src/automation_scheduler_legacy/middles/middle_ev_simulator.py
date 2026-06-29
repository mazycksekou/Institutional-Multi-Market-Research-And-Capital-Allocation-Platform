from __future__ import annotations

from typing import Any

from src.core.opportunity_scanner import simulate_middle_ev_from_prices


def simulate_middle_ev(
    *,
    left_odds_american: Any,
    right_odds_american: Any,
    middle_hit_probability: float,
    stake_per_side: float = 100.0,
) -> dict[str, Any]:
    return simulate_middle_ev_from_prices(
        left_odds_american=left_odds_american,
        right_odds_american=right_odds_american,
        middle_hit_probability=middle_hit_probability,
        stake_per_side=stake_per_side,
    )
