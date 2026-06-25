from __future__ import annotations

from typing import Any, Mapping

from .confidence import build_confidence_profile
from .report import build_market_intelligence_report
from .risk import build_risk_profile
from .targets import build_targets


def build_impact_report(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    targets = build_targets(data)
    confidence = build_confidence_profile(data)
    risk = build_risk_profile(data)
    return build_market_intelligence_report(
        {
            "market": str(data.get("market") or data.get("asset_type") or "impact"),
            "symbol_or_event": data.get("symbol") or data.get("event") or "",
            "current_price_or_odds": data.get("current_price_or_odds") or data.get("price"),
            "bias": data.get("bias") or "neutral",
            "confidence": confidence["confidence"],
            "primary_target": targets["primary_target"],
            "secondary_target": targets["secondary_target"],
            "stretch_target": targets["stretch_target"],
            "expected_move": targets["expected_move"],
            "support": targets["support"],
            "resistance": targets["resistance"],
            "trade_plan": data.get("trade_plan") or "review_only",
            "risk": risk["risk_label"],
            "stop": risk["stop"],
            "invalidation": risk["invalidation"],
            "reasoning": list(data.get("reasoning") or []),
            "no_trade_reason": data.get("no_trade_reason") or "none",
        }
    )

