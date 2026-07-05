from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


STANDARD_REPORT_FIELDS = (
    "market",
    "symbol_or_event",
    "current_price_or_odds",
    "bias",
    "confidence",
    "primary_target",
    "secondary_target",
    "stretch_target",
    "expected_move",
    "support",
    "resistance",
    "liquidity_zones",
    "positioning_summary",
    "flow_summary",
    "catalysts",
    "trade_plan",
    "risk",
    "stop",
    "invalidation",
    "reasoning",
    "no_trade_reason",
)


@dataclass(slots=True)
class MarketIntelligenceContract:
    market: str
    symbol_or_event: str = ""
    current_price_or_odds: float | None = None
    bias: str = "neutral"
    confidence: float = 0.0
    primary_target: Any = None
    secondary_target: Any = None
    stretch_target: Any = None
    expected_move: Any = None
    support: Any = None
    resistance: Any = None
    liquidity_zones: list[dict[str, Any]] = field(default_factory=list)
    positioning_summary: str = ""
    flow_summary: str = ""
    catalysts: list[str] = field(default_factory=list)
    trade_plan: str = ""
    risk: str = ""
    stop: Any = None
    invalidation: str = ""
    reasoning: list[str] = field(default_factory=list)
    no_trade_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_market_intelligence_contract(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> MarketIntelligenceContract:
    data = dict(payload or {})
    data.update(overrides)
    return MarketIntelligenceContract(
        market=str(data.get("market") or "unknown"),
        symbol_or_event=str(data.get("symbol_or_event") or data.get("symbol") or data.get("event") or ""),
        current_price_or_odds=data.get("current_price_or_odds"),
        bias=str(data.get("bias") or "neutral"),
        confidence=float(data.get("confidence") or 0.0),
        primary_target=data.get("primary_target"),
        secondary_target=data.get("secondary_target"),
        stretch_target=data.get("stretch_target"),
        expected_move=data.get("expected_move"),
        support=data.get("support"),
        resistance=data.get("resistance"),
        liquidity_zones=list(data.get("liquidity_zones") or []),
        positioning_summary=str(data.get("positioning_summary") or ""),
        flow_summary=str(data.get("flow_summary") or ""),
        catalysts=list(data.get("catalysts") or []),
        trade_plan=str(data.get("trade_plan") or ""),
        risk=str(data.get("risk") or ""),
        stop=data.get("stop"),
        invalidation=str(data.get("invalidation") or ""),
        reasoning=list(data.get("reasoning") or []),
        no_trade_reason=str(data.get("no_trade_reason") or ""),
    )
