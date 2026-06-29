from __future__ import annotations

import importlib
from typing import Any, Mapping, Sequence

from ._shared import build_text_summary, clamp, compact_list, normalize_text, safe_float, weighted_average
from .confidence import build_confidence_profile
from .flow import build_flow_summary
from .liquidity import build_liquidity_zones
from .no_trade import evaluate_no_trade
from .positioning import build_positioning_summary
from .report import build_market_intelligence_report
from .risk import build_risk_profile
from .targets import build_targets


SUPPORTED_SPORTS = (
    "baseball_mlb",
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaaw",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "golf_pga",
    "hockey_nhl",
    "soccer_epl",
    "tennis_atp",
)


def normalize_sport(value: Any) -> str:
    raw = normalize_text(value or "sports_betting").replace(" ", "_").replace("-", "_")
    aliases = {
        "nba": "basketball_nba",
        "wnba": "basketball_wnba",
        "ncaab": "basketball_ncaab",
        "ncaaw": "basketball_ncaaw",
        "nfl": "americanfootball_nfl",
        "ncaaf": "americanfootball_ncaaf",
        "mlb": "baseball_mlb",
        "nhl": "hockey_nhl",
        "pga": "golf_pga",
        "epl": "soccer_epl",
        "atp": "tennis_atp",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_SPORTS else "sports_betting")


def normalize_market(value: Any) -> str:
    raw = normalize_text(value or "moneyline").replace(" ", "_").replace("-", "_")
    aliases = {"ml": "moneyline", "h2h": "moneyline", "spread_line": "spread", "total_points": "total"}
    return aliases.get(raw, raw)


def normalize_role(value: Any) -> str:
    raw = normalize_text(value or "unknown", lower=False).replace("-", "_").replace(" ", "_").upper()
    aliases = {"QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE"}
    return aliases.get(raw, raw or "UNKNOWN")


def safe_flags(*, red_team_only: bool = False) -> dict[str, Any]:
    flags = {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "sportsbook_bet_execution_enabled": False,
    }
    if red_team_only:
        flags["red_team_only"] = True
    return flags


def finalize_sports_response(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    report = build_market_intelligence_report(
        {
            "market": "sports betting",
            "symbol_or_event": data.get("symbol") or data.get("event") or data.get("game_id") or "",
            "current_price_or_odds": data.get("current_line") or data.get("opening_line") or data.get("consensus_line") or data.get("line"),
            "bias": data.get("bias") or data.get("recommended_direction") or "neutral",
            "confidence": data.get("confidence") or 0.0,
            "primary_target": data.get("target_spread") or data.get("target_moneyline") or data.get("target_total"),
            "secondary_target": data.get("secondary_target"),
            "stretch_target": data.get("stretch_target"),
            "expected_move": data.get("expected_move"),
            "support": data.get("support"),
            "resistance": data.get("resistance"),
            "liquidity_zones": data.get("liquidity_zones") or [],
            "positioning_summary": data.get("positioning_summary") or "",
            "flow_summary": data.get("flow_summary") or "",
            "catalysts": compact_list(data.get("catalysts") or [], limit=10),
            "trade_plan": data.get("trade_plan") or "",
            "risk": data.get("risk") or "",
            "stop": data.get("stop"),
            "invalidation": data.get("invalidation") or "",
            "reasoning": compact_list(data.get("reasoning") or [], limit=12),
            "no_trade_reason": data.get("no_trade_reason") or "",
        }
    )
    report.update(safe_flags(red_team_only=bool(data.get("red_team_only"))))
    return report


def build_sports_confidence(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_confidence_profile(payload, **overrides)


def build_sports_targets(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_targets(payload, **overrides)


def build_sports_positioning(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_positioning_summary(payload, **overrides)


def build_sports_flow(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_flow_summary(payload, **overrides)


def build_sports_liquidity(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_liquidity_zones(payload, **overrides)


def build_sports_risk(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_risk_profile(payload, **overrides)


def build_sports_no_trade(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return evaluate_no_trade(payload, **overrides)


def build_sports_intelligence_report(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    confidence = build_sports_confidence(data).get("confidence", 0.0)
    targets = build_sports_targets(data)
    position = build_sports_positioning(data)
    flow = build_sports_flow(data)
    liquidity = build_sports_liquidity(data)
    risk = build_sports_risk(data)
    no_trade = build_sports_no_trade({**data, "confidence": confidence, "risk": risk.get("risk"), "liquidity_score": liquidity.get("liquidity_score")})
    report = finalize_sports_response(
        {
            **data,
            "market": "sports betting",
            "symbol_or_event": data.get("symbol") or data.get("event") or data.get("game_id") or "",
            "current_price_or_odds": data.get("current_line") or data.get("opening_line") or data.get("consensus_line") or data.get("line"),
            "bias": data.get("bias") or "neutral",
            "confidence": confidence,
            "primary_target": targets.get("primary_target"),
            "secondary_target": targets.get("secondary_target"),
            "stretch_target": targets.get("stretch_target"),
            "expected_move": targets.get("expected_move"),
            "support": targets.get("support"),
            "resistance": targets.get("resistance"),
            "liquidity_zones": liquidity.get("liquidity_zones"),
            "positioning_summary": position.get("positioning_summary"),
            "flow_summary": flow.get("flow_summary"),
            "catalysts": compact_list(data.get("catalysts") or data.get("injuries") or [], limit=10),
            "trade_plan": data.get("trade_plan") or "No live betting; use this only for review classification.",
            "risk": f"{risk.get('risk_label', 'low')} risk",
            "stop": risk.get("stop"),
            "invalidation": risk.get("invalidation") or "line moves against target or confidence degrades",
            "reasoning": [
                f"opening_line={data.get('opening_line')}",
                f"current_line={data.get('current_line')}",
                f"consensus_line={data.get('consensus_line')}",
                f"tickets={data.get('tickets')}",
                f"money={data.get('money')}",
                f"handle={data.get('handle')}",
            ],
            "no_trade_reason": no_trade.get("no_trade_reason"),
        }
    )
    report.update(
        {
            "opening_line": data.get("opening_line"),
            "current_line": data.get("current_line"),
            "consensus_line": data.get("consensus_line"),
            "tickets": data.get("tickets"),
            "money": data.get("money"),
            "handle": data.get("handle"),
            "reverse_line_movement": bool(data.get("reverse_line_movement")),
            "sharp_indicators": compact_list(data.get("sharp_indicators") or [], limit=10),
            "injuries": compact_list(data.get("injuries") or [], limit=10),
            "weather": data.get("weather"),
            "lineups": compact_list(data.get("lineups") or [], limit=10),
            "limits": data.get("limits"),
            "closing_line_movement": data.get("closing_line_movement"),
            "target_spread": data.get("target_spread") or targets.get("primary_target"),
            "target_moneyline": data.get("target_moneyline"),
            "target_total": data.get("target_total"),
            "no_trade_zone": no_trade.get("no_trade_zone"),
            "sport": normalize_sport(data.get("sport") or data.get("league")),
        }
    )
    return report


LEGACY_PACKAGE = "src.automation_scheduler_legacy"
SPORT_TOKENS = {"baseball", "golf", "hockey", "soccer", "combat", "tennis"}


def _legacy_sports_module_name(name: str) -> str | None:
    if name.startswith("evaluate_"):
        legacy_name = name[len("evaluate_") :]
    if name.startswith("build_"):
        legacy_name = name[len("build_") :]
        if legacy_name.endswith("_impact_diagnostics"):
            legacy_name = legacy_name[: -len("_impact_diagnostics")] + "_impact_report"
    else:
        if not name.startswith("evaluate_"):
            return None

    sport_token = legacy_name.split("_", 1)[0]
    if sport_token not in SPORT_TOKENS:
        return None
    return legacy_name


def __getattr__(name: str) -> Any:
    module_name = _legacy_sports_module_name(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = importlib.import_module(f"{LEGACY_PACKAGE}.{module_name}")
    try:
        attr = getattr(module, name)
    except AttributeError as exc:  # pragma: no cover - legacy compatibility guard
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    globals()[name] = attr
    return attr
