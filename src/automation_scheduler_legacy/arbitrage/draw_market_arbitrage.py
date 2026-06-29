from __future__ import annotations

from typing import Any

from .three_way_arbitrage import detect_three_way_arbitrage


def detect_draw_market_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_three_way_arbitrage(offers, **kwargs)
