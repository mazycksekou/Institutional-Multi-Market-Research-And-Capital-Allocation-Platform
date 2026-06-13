"""Sport-aware regression profile selection for backtesting.

This module does not run backtests.
This module does not assess data readiness.

Responsibilities:
- choose all_sports vs sport_specific regression config
- normalize sport/profile keys for strategy selection
- keep regression profile routing separate from data availability tiers

Canonical public runner remains:
automation_scheduler.backtesting_engine.run_backtest
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from .data_availability_tiers import MODULE_PROFILE_ALIASES, SPORT_PROFILES
except Exception:  # pragma: no cover - defensive import guard
    MODULE_PROFILE_ALIASES = {}
    SPORT_PROFILES = {}


ALL_SPORTS_PROFILE_NAME = "all_sports"


DEFAULT_ALL_SPORTS_REGRESSION_PROFILE: dict[str, Any] = {
    "profile_name": ALL_SPORTS_PROFILE_NAME,
    "profile_scope": "all_sports",
    "intercept": 0.5,
    "feature_weights": {},
    "probability_floor": 0.01,
    "probability_ceiling": 0.99,
    "override_existing_probability": True,
}


DEFAULT_SPORT_REGRESSION_PROFILES: dict[str, dict[str, Any]] = {
    key: {
        "profile_name": key,
        "profile_scope": "sport_specific",
        "intercept": 0.5,
        "feature_weights": {},
        "probability_floor": 0.01,
        "probability_ceiling": 0.99,
        "override_existing_probability": True,
    }
    for key in sorted(SPORT_PROFILES.keys())
}


# Extra lightweight aliases for common real-time user/API terms.
SPORT_PROFILE_ALIASES: dict[str, str] = {
    **{str(k): str(v) for k, v in dict(MODULE_PROFILE_ALIASES).items()},
    "nba": "basketball_nba",
    "basketball": "basketball_nba",
    "wnba": "basketball_wnba",
    "ncaab": "basketball_ncaab",
    "ncaamb": "basketball_ncaab",
    "ncaaw": "basketball_ncaaw",
    "ncaawb": "basketball_ncaaw",
    "nfl": "americanfootball_nfl",
    "football": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "cfb": "americanfootball_ncaaf",
    "mlb": "baseball_mlb",
    "baseball": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "hockey": "icehockey_nhl",
    "soccer": "soccer",
    "epl": "soccer",
    "tennis": "tennis",
    "golf": "golf",
    "mma": "combat_sports",
    "ufc": "combat_sports",
    "boxing": "combat_sports",
    "combat": "combat_sports",
    "sportsbook": "sportsbook",
    "kalshi": "prediction_market",
    "polymarket": "prediction_market",
    "prediction_market": "prediction_market",
    "prediction_markets": "prediction_market",
}


def normalize_strategy_profile_key(value: Any) -> str | None:
    if value is None:
        return None

    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if not raw:
        return None

    if raw in SPORT_PROFILES:
        return raw

    alias = SPORT_PROFILE_ALIASES.get(raw)
    if alias:
        return alias

    return raw


def infer_strategy_profile_key_from_row(row: Mapping[str, Any]) -> str | None:
    for key in (
        "sport_profile",
        "module",
        "sport",
        "league",
        "source_type",
        "provider",
    ):
        value = row.get(key)
        normalized = normalize_strategy_profile_key(value)
        if normalized:
            return normalized

    return None


def _merge_profile(base: Mapping[str, Any], override: Mapping[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(base)
    if override:
        merged.update(dict(override))
    return merged


def get_regression_profile(
    *,
    sport: Any = None,
    row: Mapping[str, Any] | None = None,
    profile_scope: str = "auto",
    all_sports_profile: Mapping[str, Any] | None = None,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return selected regression profile.

    profile_scope:
    - all_sports: always use all_sports profile
    - sport_specific: use sport-specific when available, fallback if unknown
    - auto: use sport-specific when a profile key is present, otherwise all_sports
    """

    base_all = _merge_profile(DEFAULT_ALL_SPORTS_REGRESSION_PROFILE, all_sports_profile)
    base_all.setdefault("profile_name", ALL_SPORTS_PROFILE_NAME)
    base_all.setdefault("profile_scope", "all_sports")

    merged_sports: dict[str, dict[str, Any]] = {
        key: dict(value)
        for key, value in DEFAULT_SPORT_REGRESSION_PROFILES.items()
    }

    for key, value in dict(sport_profiles or {}).items():
        normalized_key = normalize_strategy_profile_key(key) or str(key)
        profile = dict(merged_sports.get(normalized_key, {}))
        profile.update(dict(value))
        profile.setdefault("profile_name", normalized_key)
        profile.setdefault("profile_scope", "sport_specific")
        merged_sports[normalized_key] = profile

    selected_key = normalize_strategy_profile_key(sport)
    if row is not None:
        selected_key = infer_strategy_profile_key_from_row(row) or selected_key

    if profile_scope == "all_sports":
        selected = dict(base_all)
        selected["selected_profile_key"] = selected_key
        selected["selection_reason"] = "forced_all_sports"
        return selected

    if selected_key and selected_key in merged_sports:
        selected = dict(merged_sports[selected_key])
        selected.setdefault("profile_name", selected_key)
        selected.setdefault("profile_scope", "sport_specific")
        selected["selected_profile_key"] = selected_key
        selected["selection_reason"] = "sport_specific_match"
        return selected

    selected = dict(base_all)
    selected["selected_profile_key"] = selected_key
    selected["selection_reason"] = "fallback_all_sports"
    return selected


def build_strategy_config_for_row(
    row: Mapping[str, Any],
    *,
    profile_scope: str = "auto",
    all_sports_profile: Mapping[str, Any] | None = None,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    profile = get_regression_profile(
        row=row,
        profile_scope=profile_scope,
        all_sports_profile=all_sports_profile,
        sport_profiles=sport_profiles,
    )

    return {
        "intercept": profile.get("intercept", 0.5),
        "feature_weights": dict(profile.get("feature_weights") or {}),
        "probability_floor": profile.get("probability_floor", 0.01),
        "probability_ceiling": profile.get("probability_ceiling", 0.99),
        "override_existing_probability": profile.get("override_existing_probability", True),
        "profile_name": profile.get("profile_name"),
        "profile_scope": profile.get("profile_scope"),
        "selected_profile_key": profile.get("selected_profile_key"),
        "selection_reason": profile.get("selection_reason"),
    }


def describe_regression_profiles(
    *,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    merged_sports: dict[str, dict[str, Any]] = {
        key: dict(value)
        for key, value in DEFAULT_SPORT_REGRESSION_PROFILES.items()
    }

    for key, value in dict(sport_profiles or {}).items():
        normalized_key = normalize_strategy_profile_key(key) or str(key)
        profile = dict(merged_sports.get(normalized_key, {}))
        profile.update(dict(value))
        merged_sports[normalized_key] = profile

    return {
        "all_sports_profile": dict(DEFAULT_ALL_SPORTS_REGRESSION_PROFILE),
        "sport_profiles": merged_sports,
        "sport_profile_aliases": dict(SPORT_PROFILE_ALIASES),
        "data_readiness_owner": "automation_scheduler.data_availability_tiers",
        "strategy_profile_owner": "automation_scheduler.backtest_strategy_profiles",
        "public_runner": "automation_scheduler.backtesting_engine.run_backtest",
    }
