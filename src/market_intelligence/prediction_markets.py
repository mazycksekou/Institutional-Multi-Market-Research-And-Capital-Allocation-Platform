from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, compact_list, safe_float
from .confidence import build_confidence_profile
from .flow import build_flow_summary
from .liquidity import build_liquidity_zones
from .no_trade import evaluate_no_trade
from .positioning import build_positioning_summary
from .report import build_market_intelligence_report
from .risk import build_risk_profile
from .targets import build_targets


def build_prediction_market_intelligence_report(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    yes_price = safe_float(data.get("yes_price") or data.get("current_price_or_odds") or data.get("price")) or 0.0
    no_price = safe_float(data.get("no_price")) or round(max(0.0, 1.0 - yes_price), 4)
    opening_probability = safe_float(data.get("opening_probability") or data.get("implied_probability") or yes_price) or yes_price
    probability_movement = safe_float(data.get("probability_movement")) or round(yes_price - opening_probability, 4)
    confidence = build_confidence_profile(data).get("confidence", 0.0)
    confidence = max(confidence, clamp(yes_price * 100.0), clamp(opening_probability * 100.0))
    targets = build_targets(
        {
            "current_price_or_odds": yes_price,
            "bias": "bullish" if yes_price >= 0.5 else "bearish",
            "expected_move": abs(probability_movement) or 0.05,
            "support": data.get("probability_support") or max(0.0, yes_price - 0.1),
            "resistance": data.get("probability_resistance") or min(1.0, yes_price + 0.1),
        }
    )
    positioning = build_positioning_summary({"current_price_or_odds": yes_price, "support": targets["support"], "resistance": targets["resistance"]})
    flow = build_flow_summary({"volume": data.get("volume"), "open_interest": data.get("open_interest"), "tickets": data.get("tickets"), "money": data.get("money"), "handle": data.get("handle"), "current_price_or_odds": yes_price})
    liquidity = build_liquidity_zones({"current_price_or_odds": yes_price, "support": targets["support"], "resistance": targets["resistance"], "order_book_depth": data.get("order_book_depth")})
    risk = build_risk_profile({"risk": data.get("risk"), "stop": data.get("stop"), "invalidation": data.get("invalidation")})
    no_trade = evaluate_no_trade({"confidence": confidence, "risk": risk.get("risk"), "liquidity_score": liquidity.get("liquidity_score"), "regime": data.get("regime")})
    return build_market_intelligence_report(
        {
            "market": "prediction markets",
            "symbol_or_event": data.get("symbol_or_event") or data.get("event") or data.get("market"),
            "current_price_or_odds": yes_price,
            "bias": "bullish" if yes_price >= 0.5 else "bearish",
            "confidence": confidence,
            "primary_target": data.get("target_probability") or targets.get("primary_target"),
            "secondary_target": targets.get("secondary_target"),
            "stretch_target": targets.get("stretch_target"),
            "expected_move": probability_movement,
            "support": data.get("probability_support") or targets.get("support"),
            "resistance": data.get("probability_resistance") or targets.get("resistance"),
            "liquidity_zones": liquidity.get("liquidity_zones"),
            "positioning_summary": positioning.get("positioning_summary"),
            "flow_summary": flow.get("flow_summary"),
            "catalysts": compact_list(data.get("news_catalysts") or data.get("catalysts") or [], limit=10),
            "trade_plan": data.get("trade_plan") or "Review only; no live prediction-market execution.",
            "risk": f"{risk.get('risk_label', 'low')} risk",
            "stop": data.get("stop") or risk.get("stop"),
            "invalidation": data.get("invalidation") or "probability breaks support/resistance or settlement uncertainty increases",
            "reasoning": [
                f"yes_price={yes_price}",
                f"no_price={no_price}",
                f"opening_probability={opening_probability}",
                f"probability_movement={probability_movement}",
            ],
            "no_trade_reason": no_trade.get("no_trade_reason"),
            "yes_price": round(yes_price, 4),
            "no_price": round(no_price, 4),
            "opening_probability": round(opening_probability, 4),
            "probability_movement": round(probability_movement, 4),
            "order_book_depth": data.get("order_book_depth"),
            "volume": data.get("volume"),
            "open_interest": data.get("open_interest"),
            "holder_concentration": data.get("holder_concentration"),
            "large_trades": compact_list(data.get("large_trades") or [], limit=8),
            "time_until_resolution": data.get("time_until_resolution"),
            "news_catalysts": compact_list(data.get("news_catalysts") or [], limit=10),
            "probability_support": data.get("probability_support") or targets.get("support"),
            "probability_resistance": data.get("probability_resistance") or targets.get("resistance"),
            "buy_zone": data.get("buy_zone") or targets.get("support"),
            "sell_zone": data.get("sell_zone") or targets.get("resistance"),
            "take_profit_zone": data.get("take_profit_zone") or targets.get("stretch_target"),
            "breakout_probability": data.get("breakout_probability") or clamp(50.0 + probability_movement * 100.0),
            "target_probability": data.get("target_probability") or targets.get("primary_target"),
            "invalidation_level": data.get("invalidation_level") or risk.get("invalidation"),
            "order_flow_summary": flow.get("flow_summary"),
        }
    )


def build_prediction_market_signal(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_prediction_market_intelligence_report(payload, **overrides)
