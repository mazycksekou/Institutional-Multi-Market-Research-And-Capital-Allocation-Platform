from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional


MODEL_LEVEL_NOT_BUILT = "not_built"
MODEL_LEVEL_MARKET_DERIVED_ONLY = "market_derived_only"
MODEL_LEVEL_PROJECTION_READY = "projection_ready"
MODEL_LEVEL_BLENDED_READY = "blended_ready"
MODEL_LEVEL_FULLY_INDEPENDENT = "fully_independent"

CONFIRMED_BET_ELIGIBLE_LEVELS = frozenset({
    MODEL_LEVEL_PROJECTION_READY,
    MODEL_LEVEL_BLENDED_READY,
    MODEL_LEVEL_FULLY_INDEPENDENT,
})

GLOBAL_MODEL_REGISTRY_RULES = [
    "Market-derived-only probabilities cannot create confirmed bets.",
    "Confirmed bets require independent projection inputs.",
    "No sport may be promoted without backtesting and logging.",
    "100 plus sportsbook positive EV scanning requires a configured provider such as OddsJam or equivalent.",
    "Direct B2B bet execution is not enabled until approved official API access exists.",
]

BASE_LOG_FIELDS_REQUIRED = [
    "timestamp",
    "sport_key",
    "event_id",
    "market",
    "selection",
    "sportsbook",
    "odds_american",
    "model_level",
    "probability_type",
    "final_probability",
    "decision",
    "stake",
    "risk_profile",
]

MARKET_ONLY_COMPONENTS = [
    "sportsbook_odds_ingestion",
    "best_price_selection",
    "consensus_probability",
    "no_vig_probability",
    "line_evaluation",
]

NOT_BUILT_COMPONENTS = [
    "registry_placeholder",
    "provider_requirements_defined",
    "confirmed_bet_governance_disabled",
]

STANDARD_PROVIDER_NEEDS = [
    "sportsbook odds provider for events and prices",
    "independent projection provider",
    "injury or availability provider",
    "historical odds and closing-line dataset",
    "backtesting dataset with settled outcomes",
]

STANDARD_RISK_NOTES = [
    "Confirmed bets disabled until independent projections and backtests are connected.",
    "Market odds alone may identify target lines or watchlist candidates only.",
]

STANDARD_CORRELATION_RULES = [
    "Limit exposure by event_id, market, and correlated selections.",
    "Do not combine highly correlated sides, totals, and player props without explicit correlation scoring.",
]


def _sport(
    sport_key: str,
    display_name: str,
    supported_markets: list[str],
    supported_props: list[str],
    *,
    status: str = "not_started",
    model_level: str = MODEL_LEVEL_NOT_BUILT,
    confirmed_allowed: bool = False,
    required_inputs: Optional[list[str]] = None,
    optional_inputs: Optional[list[str]] = None,
    provider_needs: Optional[list[str]] = None,
    recommended_providers: Optional[list[str]] = None,
    model_components: Optional[list[str]] = None,
    risk_notes: Optional[list[str]] = None,
    correlation_rules: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "sport_key": sport_key,
        "display_name": display_name,
        "status": status,
        "model_level": model_level,
        "confirmed_bets_allowed": bool(confirmed_allowed and model_level in CONFIRMED_BET_ELIGIBLE_LEVELS),
        "supported_markets": supported_markets,
        "supported_props": supported_props,
        "required_independent_inputs": required_inputs or [],
        "optional_independent_inputs": optional_inputs or [],
        "provider_needs": provider_needs or list(STANDARD_PROVIDER_NEEDS),
        "recommended_providers": recommended_providers or [],
        "model_components": model_components or list(NOT_BUILT_COMPONENTS),
        "risk_notes": risk_notes or list(STANDARD_RISK_NOTES),
        "correlation_rules": correlation_rules or list(STANDARD_CORRELATION_RULES),
        "log_fields_required": list(BASE_LOG_FIELDS_REQUIRED),
    }


SPORT_MODEL_REGISTRY = [
    _sport(
        "americanfootball_nfl",
        "NFL",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "americanfootball_ncaaf",
        "College Football",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "basketball_nba",
        "NBA",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "basketball_wnba",
        "WNBA",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "basketball_ncaab",
        "College Basketball",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "baseball_mlb",
        "MLB",
        ["h2h", "spreads", "totals"],
        [],
        status="market_pricing_live",
        model_level=MODEL_LEVEL_MARKET_DERIVED_ONLY,
        provider_needs=[
            "sportsbook odds provider for events and prices",
            "independent game projection provider",
            "probable pitcher provider",
            "lineup provider",
            "weather provider",
            "bullpen usage provider",
            "park factor dataset",
            "umpire assignment dataset",
            "historical odds and closing-line dataset",
            "backtesting dataset with settled outcomes",
        ],
        recommended_providers=["the_odds_api"],
        model_components=MARKET_ONLY_COMPONENTS,
        risk_notes=[
            "MLB pricing is live but independent projection data is not connected.",
            "Market-derived MLB probabilities may produce target lines, watchlist items, or no_bet only.",
        ],
        correlation_rules=[
            "Group exposure by game, side, total, run line, and same-game related selections.",
            "Do not confirm bets from market-derived MLB probabilities.",
        ],
    ),
    _sport(
        "soccer",
        "Soccer",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "icehockey_nhl",
        "NHL",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "tennis",
        "Tennis",
        ["h2h", "spreads", "totals"],
        [],
    ),
    _sport(
        "mma_mixed_martial_arts",
        "MMA",
        ["h2h"],
        [],
    ),
    _sport(
        "boxing",
        "Boxing",
        ["h2h"],
        [],
    ),
    _sport(
        "golf",
        "Golf",
        ["outrights", "h2h"],
        [],
    ),
    _sport(
        "formula1",
        "Formula 1",
        ["outrights", "h2h"],
        [],
    ),
    _sport(
        "cricket",
        "Cricket",
        ["h2h", "totals"],
        [],
    ),
]

_REGISTRY_BY_KEY = {sport["sport_key"]: sport for sport in SPORT_MODEL_REGISTRY}


def _validate_registry() -> None:
    if len(_REGISTRY_BY_KEY) != len(SPORT_MODEL_REGISTRY):
        raise ValueError("SPORT_MODEL_REGISTRY contains duplicate sport_key values")
    for sport in SPORT_MODEL_REGISTRY:
        model_level = sport.get("model_level")
        if model_level not in CONFIRMED_BET_ELIGIBLE_LEVELS and sport.get("confirmed_bets_allowed"):
            raise ValueError(f"{sport.get('sport_key')} cannot allow confirmed bets at model level {model_level}")
        if not sport.get("supported_markets"):
            raise ValueError(f"{sport.get('sport_key')} must define at least one supported market")
        for required_field in (
            "supported_props",
            "provider_needs",
            "log_fields_required",
            "required_independent_inputs",
            "optional_independent_inputs",
        ):
            if required_field not in sport:
                raise ValueError(f"{sport.get('sport_key')} is missing {required_field}")


def get_sport_model_config(sport_key: str) -> Optional[dict[str, Any]]:
    config = _REGISTRY_BY_KEY.get((sport_key or "").strip())
    return deepcopy(config) if config else None


def is_supported_sport(sport_key: str) -> bool:
    return (sport_key or "").strip() in _REGISTRY_BY_KEY


def confirmed_bets_allowed(sport_key: str) -> bool:
    config = _REGISTRY_BY_KEY.get((sport_key or "").strip())
    if not config:
        return False
    return bool(
        config.get("confirmed_bets_allowed")
        and config.get("model_level") in CONFIRMED_BET_ELIGIBLE_LEVELS
    )


def get_required_inputs(sport_key: str) -> Optional[list[str]]:
    config = _REGISTRY_BY_KEY.get((sport_key or "").strip())
    return deepcopy(config.get("required_independent_inputs")) if config else None


def get_supported_markets(sport_key: str) -> Optional[list[str]]:
    config = _REGISTRY_BY_KEY.get((sport_key or "").strip())
    return deepcopy(config.get("supported_markets")) if config else None


def classify_model_level(sport_key: str) -> Optional[str]:
    config = _REGISTRY_BY_KEY.get((sport_key or "").strip())
    return str(config.get("model_level")) if config else None


def get_sports_model_registry_response() -> dict[str, Any]:
    sports = deepcopy(SPORT_MODEL_REGISTRY)
    return {
        "ok": True,
        "endpoint": "getSportsModelRegistry",
        "sports": sports,
        "summary": {
            "total_sports": len(sports),
            "confirmed_bet_enabled_sports": sum(1 for sport in sports if sport["confirmed_bets_allowed"]),
            "market_derived_only_sports": sum(
                1 for sport in sports if sport["model_level"] == MODEL_LEVEL_MARKET_DERIVED_ONLY
            ),
            "not_built_sports": sum(1 for sport in sports if sport["model_level"] == MODEL_LEVEL_NOT_BUILT),
        },
        "global_rules": list(GLOBAL_MODEL_REGISTRY_RULES),
        "error": None,
        "detail": None,
    }


_validate_registry()
