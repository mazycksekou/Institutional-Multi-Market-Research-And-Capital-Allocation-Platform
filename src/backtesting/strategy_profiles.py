from __future__ import annotations

from typing import Any, Mapping


_PROFILE_ALIASES = {
    "nba": "basketball_nba",
    "nfl": "americanfootball_nfl",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "soccer": "association_football",
    "kalshi": "prediction_market",
    "all_sports": "all_sports",
}


def normalize_strategy_profile_key(value: Any) -> str | None:
    if value in (None, ""):
        return None
    key = str(value).strip().lower()
    return _PROFILE_ALIASES.get(key, key)


def infer_strategy_profile_key_from_row(row: Mapping[str, Any]) -> str | None:
    if not isinstance(row, Mapping):
        return None
    return normalize_strategy_profile_key(row.get("sport") or row.get("league") or row.get("market_type"))


def _profile_payload(
    *,
    profile_name: str,
    profile_scope: str,
    selection_reason: str,
    intercept: float = 0.5,
    feature_weights: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "profile_name": profile_name,
        "profile_scope": profile_scope,
        "selection_reason": selection_reason,
        "intercept": float(intercept),
        "feature_weights": dict(feature_weights or {}),
    }


def build_strategy_config_for_row(
    row: Mapping[str, Any],
    *,
    all_sports_profile: Mapping[str, Any] | None = None,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    sport_key = infer_strategy_profile_key_from_row(row) or "all_sports"
    sport_profiles = dict(sport_profiles or {})
    if sport_key in sport_profiles:
        profile = dict(sport_profiles[sport_key])
        return _profile_payload(
            profile_name=sport_key,
            profile_scope="sport_specific",
            selection_reason="sport_specific_match",
            intercept=float(profile.get("intercept", 0.5) or 0.5),
            feature_weights=profile.get("feature_weights") or {},
        )
    if all_sports_profile:
        profile = dict(all_sports_profile)
        return _profile_payload(
            profile_name="all_sports",
            profile_scope="all_sports",
            selection_reason="forced_all_sports",
            intercept=float(profile.get("intercept", 0.5) or 0.5),
            feature_weights=profile.get("feature_weights") or {},
        )
    return _profile_payload(
        profile_name=sport_key,
        profile_scope="auto",
        selection_reason="auto_selected",
    )


def describe_regression_profiles() -> dict[str, Any]:
    return {
        "data_readiness_owner": "src.data.historical_sources",
        "strategy_profile_owner": "src.backtesting.strategy_profiles",
        "public_runner": "src.backtesting.engine.run_backtest",
        "sport_profiles": {
            "basketball_nba": {"display_name": "NBA", "profile_name": "basketball_nba"},
            "baseball_mlb": {"display_name": "MLB", "profile_name": "baseball_mlb"},
            "americanfootball_nfl": {"display_name": "NFL", "profile_name": "americanfootball_nfl"},
            "icehockey_nhl": {"display_name": "NHL", "profile_name": "icehockey_nhl"},
            "association_football": {"display_name": "Soccer", "profile_name": "association_football"},
            "prediction_market": {"display_name": "Prediction Market", "profile_name": "prediction_market"},
        },
        "notes": [
            "local_only",
            "no_live_execution",
            "no_scheduler_dependency",
        ],
    }


def get_regression_profile(
    *,
    sport: Any,
    profile_scope: str = "auto",
    all_sports_profile: Mapping[str, Any] | None = None,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    row = {"sport": sport}
    profile = build_strategy_config_for_row(
        row,
        all_sports_profile=all_sports_profile,
        sport_profiles=sport_profiles,
    )
    profile["profile_scope"] = profile_scope if profile_scope != "auto" else profile["profile_scope"]
    return profile


__all__ = [
    "build_strategy_config_for_row",
    "describe_regression_profiles",
    "get_regression_profile",
    "infer_strategy_profile_key_from_row",
    "normalize_strategy_profile_key",
]
