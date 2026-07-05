from __future__ import annotations

from typing import Any, Mapping

from .flow import build_flow_summary
from .report import build_market_intelligence_report
from .targets import build_targets


def build_futures_intelligence_report(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    targets = build_targets(data)
    flow = build_flow_summary(data)
    return build_market_intelligence_report(
        {
            "market": "futures",
            "symbol_or_event": data.get("symbol") or data.get("contract") or "",
            "current_price_or_odds": data.get("price") or data.get("current_price"),
            "bias": data.get("bias") or "neutral",
            "confidence": data.get("confidence") or 0.0,
            "primary_target": targets["primary_target"],
            "secondary_target": targets["secondary_target"],
            "stretch_target": targets["stretch_target"],
            "expected_move": targets["expected_move"],
            "support": targets["support"],
            "resistance": targets["resistance"],
            "flow_summary": flow["flow_summary"],
            "trade_plan": data.get("trade_plan") or "Review only; no live futures trading.",
            "risk": data.get("risk") or "low",
            "invalidation": data.get("invalidation") or "risk/reward deteriorates",
        }
    )

