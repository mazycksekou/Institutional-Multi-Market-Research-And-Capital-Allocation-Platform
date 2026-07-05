from __future__ import annotations

from typing import Any

from src.providers.registry import provider_min_interval_seconds

_PROFILE_BY_MARKET_TYPE = {
    "sports_pregame_main": "sports_pregame_main",
    "sports_player_props": "sports_player_props",
    "sports_live": "sports_live",
    "prediction_markets": "prediction_markets",
    "stocks_watchlist": "stocks_watchlist",
    "stocks_broad": "stocks_broad",
    "news_events": "news_events",
    "low_liquidity": "low_liquidity",
}


def resolve_profile_name(market_type: str, low_liquidity: bool = False) -> str:
    if low_liquidity:
        return "low_liquidity"
    return _PROFILE_BY_MARKET_TYPE.get(market_type, "news_events")


def choose_next_check_seconds(
    *,
    market_type: str,
    opportunity_score: float,
    provider_name: str,
    config: dict[str, Any],
    low_liquidity: bool = False,
    market_closed: bool = False,
    stale_data: bool = False,
) -> dict[str, Any]:
    if market_closed:
        return {
            "profile_name": resolve_profile_name(market_type, low_liquidity),
            "next_check_seconds": 0,
            "provider_min_interval_seconds": provider_min_interval_seconds(provider_name, config),
            "not_competitive_for_live": False,
        }

    profile_name = resolve_profile_name(market_type, low_liquidity)
    profile = config["cadence_profiles"][profile_name]
    if profile_name == "low_liquidity":
        desired_seconds = profile.get("standard_watchlist_seconds", 900)
    elif "hot_watchlist_seconds" in profile:
        if opportunity_score >= config["score_thresholds"]["urgent_threshold"]:
            desired_seconds = profile["hot_watchlist_seconds"]
        elif opportunity_score >= config["score_thresholds"]["review_threshold"]:
            desired_seconds = profile.get("standard_watchlist_seconds", profile.get("broad_scan_seconds", profile["hot_watchlist_seconds"]))
        else:
            desired_seconds = profile.get("broad_scan_seconds", profile.get("standard_watchlist_seconds", profile.get("fallback_seconds", 300)))
    else:
        desired_seconds = profile.get("standard_scan_seconds", profile.get("standard_watchlist_seconds", 300))
    if stale_data:
        desired_seconds = max(int(desired_seconds), 300)
    if low_liquidity:
        desired_seconds = max(int(desired_seconds), 900)

    provider_floor = provider_min_interval_seconds(provider_name, config)
    next_check_seconds = max(provider_floor, int(desired_seconds))
    not_competitive_for_live = bool(
        market_type == "sports_live"
        and profile.get("streaming_preferred")
        and not config["providers"].get(provider_name, {}).get("streaming_supported", False)
    )
    if not_competitive_for_live:
        next_check_seconds = max(next_check_seconds, int(profile["fallback_seconds"]))

    return {
        "profile_name": profile_name,
        "next_check_seconds": next_check_seconds,
        "provider_min_interval_seconds": provider_floor,
        "not_competitive_for_live": not_competitive_for_live,
    }
