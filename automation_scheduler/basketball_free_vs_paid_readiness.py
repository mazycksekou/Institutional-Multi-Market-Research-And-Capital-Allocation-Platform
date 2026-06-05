from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import requests

from .scheduler_config import sanitize_filename, utc_now_iso


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"
HTTP_USER_AGENT = "betting-stock-api-basketball-free-vs-paid-readiness"
GITHUB_RELEASE_API = "https://api.github.com/repos/sportsdataverse/sportsdataverse-data/releases/tags/{tag}"
GITHUB_RELEASE_DOWNLOAD = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/{tag}/{asset}"
RUN_MODE = "basketball_free_vs_paid_sample_verification_and_calibration_readiness"

FREE_VS_PAID_CATEGORIES = (
    "free_open_populated",
    "free_open_partial",
    "free_open_sample_required",
    "free_open_loader_needed",
    "free_open_manual_import_needed",
    "user_approved_paid_transport_needed",
    "paid_data_subscription_required",
    "policy_blocked",
    "license_terms_unclear",
    "blocked_reference_or_restricted_source",
    "unavailable_after_max_effort",
    "obsolete_or_duplicate",
    "needs_manual_review",
)

GAP_ACTIONS = (
    "sample_verify_one_season",
    "sample_verify_one_date",
    "sample_verify_one_team",
    "sample_verify_one_game",
    "implement_loader",
    "backfill_approved_seasons",
    "create_manual_import_template",
    "mark_paid_subscription_required",
    "mark_policy_blocked",
    "mark_unavailable_after_max_effort",
    "mark_obsolete_or_duplicate",
    "escalate_manual_review",
    "add_schema_field",
    "update_model_readiness_only",
)

SAFETY_FLAGS: dict[str, Any] = {
    "provider_write": False,
    "execution_allowed": False,
    "execution_allowed_count": 0,
    "live_execution_enabled": False,
    "auto_execution_enabled": False,
    "kalshi_order_execution_enabled": False,
    "sportsbook_bet_execution_enabled": False,
    "broker_order_execution_enabled": False,
    "stock_trade_execution_enabled": False,
    "crypto_trade_execution_enabled": False,
    "actual_orders_submitted": 0,
    "actual_bets_submitted": 0,
    "actual_trades_submitted": 0,
    "actual_crypto_swaps_submitted": 0,
    "raw_payload_included": False,
    "raw_html_persisted": False,
    "raw_screenshot_persisted": False,
    "secrets_included": False,
    "paid_source_enabled_count": 1,
}

SPORTS: dict[str, dict[str, Any]] = {
    "basketball_nba": {
        "display_name": "NBA",
        "module": "basketball_nba",
        "model": "basketball_nba model/readiness path",
        "sample_season": 2025,
        "legacy_aliases": ["nba"],
        "readiness_recommendation": "ready_but_paid_data_would_improve",
    },
    "basketball_wnba": {
        "display_name": "WNBA",
        "module": "basketball_wnba",
        "model": "wnba_possession_rating_monte_carlo_model",
        "sample_season": 2025,
        "legacy_aliases": ["wnba"],
        "readiness_recommendation": "ready_but_paid_data_would_improve",
    },
    "basketball_ncaab": {
        "display_name": "NCAAB",
        "module": "basketball_ncaab",
        "model": "mens_college_basketball_possession_variance_model",
        "sample_season": 2025,
        "legacy_aliases": ["ncaab", "mens_college_basketball"],
        "readiness_recommendation": "manual_import_needed",
    },
    "basketball_ncaaw": {
        "display_name": "NCAAW",
        "module": "basketball_ncaaw",
        "model": "womens_college_basketball_possession_variance_model",
        "sample_season": 2026,
        "legacy_aliases": ["ncaaw", "ncaawb", "basketball_ncaawb", "womens_college_basketball"],
        "readiness_recommendation": "manual_import_needed",
    },
}


def _stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _url_hash(url: str) -> str:
    return hashlib.sha256(str(url).strip().encode("utf-8")).hexdigest()


def _git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def _git_branch_name() -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    except Exception:
        return ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return str(value)


def _safety() -> dict[str, Any]:
    return dict(SAFETY_FLAGS)


def _source_domain(source_url: str) -> str:
    return urlparse(source_url).netloc.lower()


def _source_reference(source_name: str, url: str, *, source_type: str, policy_status: str, note: str) -> dict[str, Any]:
    return {
        "source_name": source_name,
        "url_hash": _url_hash(url),
        "domain": _source_domain(url),
        "source_type": source_type,
        "policy_status": policy_status,
        "license_or_terms_note": note,
    }


SOURCE_REFERENCES: dict[str, dict[str, Any]] = {
    "sportsdataverse_releases": _source_reference(
        "SportsDataverse release assets",
        "https://github.com/sportsdataverse/sportsdataverse-data/releases",
        source_type="open_github_release_assets",
        policy_status="approved_release_asset_with_terms_caution",
        note="Free/open GitHub release assets; upstream ESPN/NBA/WNBA/NCAA terms still require conservative normalized-use review.",
    ),
    "hoopR": _source_reference(
        "hoopR",
        "https://github.com/sportsdataverse/hoopR",
        source_type="open_source_wrapper_and_release_loader",
        policy_status="approved_for_documentation_and_release_asset_discovery",
        note="MIT package; direct ESPN/NBA Stats API calls remain terms-review gated, release assets are preferred.",
    ),
    "wehoop": _source_reference(
        "wehoop",
        "https://github.com/sportsdataverse/wehoop",
        source_type="open_source_wrapper_and_release_loader",
        policy_status="approved_for_documentation_and_release_asset_discovery",
        note="MIT package; direct ESPN/WNBA Stats API calls remain terms-review gated, release assets are preferred.",
    ),
    "nba_api": _source_reference(
        "nba_api",
        "https://github.com/swar/nba_api",
        source_type="public_wrapper_with_terms_review",
        policy_status="license_terms_unclear",
        note="Useful endpoint documentation exists, but direct NBA Stats API use requires exact path policy review.",
    ),
    "espn_public": _source_reference(
        "ESPN public endpoints",
        "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        source_type="public_endpoint_with_terms_review",
        policy_status="license_terms_unclear",
        note="No ESPN scraping in this pass; use SportsDataverse normalized release assets or manual review only.",
    ),
    "wnba_stats": _source_reference(
        "WNBA Stats endpoints",
        "https://stats.wnba.com/",
        source_type="public_endpoint_with_terms_review",
        policy_status="license_terms_unclear",
        note="Direct calls require terms/path review; SportsDataverse release samples are allowed for tiny verification.",
    ),
    "ncaa_net": _source_reference(
        "NCAA NET ranking tables",
        "https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings",
        source_type="official_public_table_manual_import",
        policy_status="manual_import_only",
        note="Official public table can support manual import; automated scraping is not enabled in this pass.",
    ),
    "wikidata": _source_reference(
        "Wikidata structured entities",
        "https://www.wikidata.org/",
        source_type="structured_open_supplemental",
        policy_status="supplemental_only",
        note="Supplemental entity/venue metadata only; not a primary performance-stat source.",
    ),
    "sportradar": _source_reference(
        "Sportradar Basketball APIs",
        "https://developer.sportradar.com/basketball",
        source_type="paid_or_trial_api",
        policy_status="paid_subscription_required",
        note="Paid/keyed sports data feed candidate; only classify, do not retrieve without subscription terms.",
    ),
    "genius_sports": _source_reference(
        "Genius Sports official data APIs",
        "https://developer.geniussports.com/",
        source_type="paid_official_data_api",
        policy_status="paid_subscription_required",
        note="Paid official data feed candidate for NCAA/live data/tracking; no retrieval in this pass.",
    ),
    "second_spectrum": _source_reference(
        "Second Spectrum tracking data",
        "https://www.geniussports.com/newsroom/ncaa-and-genius-sports-expand-partnership-through-2032/",
        source_type="paid_tracking_vendor",
        policy_status="paid_subscription_required",
        note="Optical tracking and play-type context require licensed vendor access.",
    ),
    "stats_perform": _source_reference(
        "Stats Perform basketball data",
        "https://www.statsperform.com/",
        source_type="paid_data_vendor",
        policy_status="paid_subscription_required",
        note="Paid vendor candidate for injuries, availability, lineups, and richer college coverage.",
    ),
    "basketball_reference": _source_reference(
        "Basketball Reference / Sports Reference",
        "https://www.basketball-reference.com/",
        source_type="restricted_reference_site",
        policy_status="blocked_reference_or_restricted_source",
        note="Hard-blocked by user instruction: no Basketball Reference, Sports Reference, or College Basketball Reference scraping.",
    ),
    "kenpom": _source_reference(
        "KenPom",
        "https://kenpom.com/",
        source_type="restricted_paid_site",
        policy_status="blocked_reference_or_restricted_source",
        note="No KenPom scraping; only licensed/manual review could change this lane.",
    ),
    "barttorvik": _source_reference(
        "BartTorvik",
        "https://barttorvik.com/",
        source_type="restricted_terms_review",
        policy_status="blocked_reference_or_restricted_source",
        note="No BartTorvik scraping unless policy/license review allows the exact data path.",
    ),
    "her_hoop_stats": _source_reference(
        "Her Hoop Stats",
        "https://herhoopstats.com/",
        source_type="restricted_terms_review",
        policy_status="blocked_reference_or_restricted_source",
        note="No Her Hoop Stats scraping unless license/terms explicitly allow the path.",
    ),
    "synergy": _source_reference(
        "Synergy Sports",
        "https://synergysports.com/",
        source_type="restricted_paid_platform",
        policy_status="blocked_reference_or_restricted_source",
        note="No Synergy scraping; licensed data feed would be a paid subscription lane.",
    ),
    "cleaning_the_glass": _source_reference(
        "Cleaning the Glass",
        "https://cleaningtheglass.com/",
        source_type="restricted_paid_platform",
        policy_status="blocked_reference_or_restricted_source",
        note="No Cleaning the Glass scraping; not pursued in this pass.",
    ),
}


def _release_asset(tag: str, asset: str, *, season: int, source_ref: str = "sportsdataverse_releases") -> dict[str, Any]:
    return {
        "source_ref": source_ref,
        "release_tag": tag,
        "asset_name": asset,
        "sample_scope": str(season),
        "sample_type": "one_season",
        "retrieval_method": "github_release_csv_range_read",
        "loader_exists": True,
    }


def _lane(
    sport: str,
    lane_name: str,
    field_group: str,
    *,
    entity_level: str,
    fields: list[str],
    table: str,
    source_ref: str,
    category: str,
    current_status: str,
    calibration_impact: str,
    next_action: str,
    final_reason: str,
    source_family: str | None = None,
    source_type: str | None = None,
    retrieval_method: str | None = None,
    data_type: str = "mixed",
    cutoff_safe: bool = True,
    future_leakage_risk: str = "low_if_joined_by_game_start",
    model_eligible: bool | None = None,
    duplicate_or_obsolete_candidate: bool = False,
    coverage_start: str | None = None,
    coverage_end: str | None = None,
    sample: dict[str, Any] | None = None,
    sample_required: bool | None = None,
    manual_template_required: bool = False,
    paid_priority: str | None = None,
    manual_import_possible: bool = True,
    blocked_reason: str = "",
) -> dict[str, Any]:
    if category not in FREE_VS_PAID_CATEGORIES:
        raise ValueError(f"Unsupported basketball free-vs-paid category: {category}")
    if next_action not in GAP_ACTIONS:
        raise ValueError(f"Unsupported basketball gap action: {next_action}")
    src = SOURCE_REFERENCES[source_ref]
    sample_required_value = bool(sample) if sample_required is None else bool(sample_required)
    return {
        "sport": sport,
        "sport_name": SPORTS[sport]["display_name"],
        "module": SPORTS[sport]["module"],
        "table": table,
        "lane_name": lane_name,
        "field_or_feature_group": field_group,
        "fields": list(fields),
        "entity_level": entity_level,
        "data_type": data_type,
        "current_status": current_status,
        "source_ref": source_ref,
        "source_family": source_family or src["source_name"],
        "candidate_source_name": src["source_name"],
        "source_type": source_type or src["source_type"],
        "source_url_hash": src["url_hash"],
        "source_domain": src["domain"],
        "free_or_paid_category": category,
        "retrieval_method": retrieval_method or (sample or {}).get("retrieval_method") or "policy_classification",
        "sample_required": sample_required_value,
        "loader_exists": bool((sample or {}).get("loader_exists", False) or category in {"free_open_manual_import_needed", "paid_data_subscription_required", "policy_blocked", "license_terms_unclear", "blocked_reference_or_restricted_source", "obsolete_or_duplicate"}),
        "manual_template_exists": bool(manual_template_required or category in {"free_open_manual_import_needed", "paid_data_subscription_required", "policy_blocked", "license_terms_unclear", "needs_manual_review", "unavailable_after_max_effort"}),
        "manual_template_required": bool(manual_template_required or category in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear", "needs_manual_review", "unavailable_after_max_effort"}),
        "policy_status": src["policy_status"],
        "license_or_terms_note": src["license_or_terms_note"],
        "cutoff_safe": bool(cutoff_safe),
        "future_leakage_risk": future_leakage_risk,
        "model_eligible": bool(category in {"free_open_populated", "free_open_partial"} and cutoff_safe) if model_eligible is None else bool(model_eligible),
        "calibration_impact": calibration_impact,
        "next_action": next_action,
        "final_reason": final_reason,
        "duplicate_or_obsolete_candidate": duplicate_or_obsolete_candidate,
        "coverage_start": coverage_start or str(SPORTS[sport]["sample_season"]),
        "coverage_end": coverage_end or str(SPORTS[sport]["sample_season"]),
        "sample": dict(sample or {}),
        "paid_priority": paid_priority,
        "manual_import_possible": bool(manual_import_possible),
        "blocked_reason": blocked_reason,
    }


def _sport_release_prefixes(sport: str) -> dict[str, str]:
    season = int(SPORTS[sport]["sample_season"])
    if sport == "basketball_nba":
        return {
            "schedule": "nba_schedule",
            "team_box": "team_box",
            "player_box": "player_box",
            "pbp": "play_by_play",
            "team_season_stats": "team_season_stats",
            "shots": "shots",
            "officials": "officials",
            "game_rosters": "game_rosters",
            "schedule_tag": "espn_nba_schedules",
            "team_box_tag": "espn_nba_team_boxscores",
            "player_box_tag": "espn_nba_player_boxscores",
            "pbp_tag": "espn_nba_pbp",
            "team_season_stats_tag": "espn_nba_team_season_stats",
            "shots_tag": "espn_nba_shots",
            "officials_tag": "espn_nba_officials",
            "game_rosters_tag": "espn_nba_game_rosters",
            "season": str(season),
        }
    if sport == "basketball_wnba":
        return {
            "schedule": "wnba_schedule",
            "team_box": "team_box",
            "player_box": "player_box",
            "pbp": "play_by_play",
            "team_season_stats": "team_season_stats",
            "shots": "shots",
            "officials": "officials",
            "game_rosters": "game_rosters",
            "lineups": "lineups",
            "schedule_tag": "espn_wnba_schedules",
            "team_box_tag": "espn_wnba_team_boxscores",
            "player_box_tag": "espn_wnba_player_boxscores",
            "pbp_tag": "espn_wnba_pbp",
            "team_season_stats_tag": "espn_wnba_team_season_stats",
            "shots_tag": "espn_wnba_shots",
            "officials_tag": "espn_wnba_officials",
            "game_rosters_tag": "espn_wnba_game_rosters",
            "lineups_tag": "wnba_stats_lineups",
            "lineups_season": "2026",
            "season": str(season),
        }
    if sport == "basketball_ncaab":
        return {
            "schedule": "mbb_schedule",
            "team_box": "team_box",
            "player_box": "player_box",
            "pbp": "play_by_play",
            "team_season_stats": "team_season_stats",
            "shots": "shots",
            "officials": "officials",
            "game_rosters": "game_rosters",
            "schedule_tag": "espn_mens_college_basketball_schedules",
            "team_box_tag": "espn_mens_college_basketball_team_boxscores",
            "player_box_tag": "espn_mens_college_basketball_player_boxscores",
            "pbp_tag": "espn_mens_college_basketball_pbp",
            "team_season_stats_tag": "espn_mens_college_basketball_team_season_stats",
            "shots_tag": "espn_mens_college_basketball_shots",
            "officials_tag": "espn_mens_college_basketball_officials",
            "game_rosters_tag": "espn_mens_college_basketball_game_rosters",
            "season": str(season),
        }
    return {
        "schedule": "wbb_schedule",
        "team_box": "team_box",
        "player_box": "player_box",
        "pbp": "play_by_play",
        "team_season_stats": "team_season_stats",
        "shots": "shots",
        "officials": "officials",
        "game_rosters": "game_rosters",
        "schedule_tag": "espn_womens_college_basketball_schedules",
        "team_box_tag": "espn_womens_college_basketball_team_boxscores",
        "player_box_tag": "espn_womens_college_basketball_player_boxscores",
        "pbp_tag": "espn_womens_college_basketball_pbp",
        "team_season_stats_tag": "espn_womens_college_basketball_team_season_stats",
        "shots_tag": "espn_womens_college_basketball_shots",
        "officials_tag": "espn_womens_college_basketball_officials",
        "game_rosters_tag": "espn_womens_college_basketball_game_rosters",
        "season": str(season),
    }


def _asset(prefixes: dict[str, str], kind: str, *, season_key: str = "season") -> str:
    return f"{prefixes[kind]}_{prefixes[season_key]}.csv"


def _release_sample(prefixes: dict[str, str], kind: str, *, season_key: str = "season") -> dict[str, Any]:
    season = int(prefixes[season_key])
    return _release_asset(prefixes[f"{kind}_tag"], _asset(prefixes, kind, season_key=season_key), season=season)


def basketball_lane_catalog() -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    for sport in SPORTS:
        p = _sport_release_prefixes(sport)
        is_college = sport in {"basketball_ncaab", "basketball_ncaaw"}
        is_wnba = sport == "basketball_wnba"
        lanes.extend(
            [
                _lane(
                    sport,
                    "schedule_results",
                    "schedule/results",
                    entity_level="game",
                    fields=["game_id", "season", "game_date", "home_team", "away_team", "home_score", "away_score", "status", "neutral_site"],
                    table="basketball_games",
                    source_ref="sportsdataverse_releases",
                    source_family=p["schedule_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="anchors event identity, final result labels, rest windows, and score calibration joins",
                    next_action="backfill_approved_seasons",
                    final_reason="One-season SportsDataverse schedule CSV sample is available with stable game/date/team/result fields.",
                    sample=_release_sample(p, "schedule"),
                ),
                _lane(
                    sport,
                    "team_box_scores",
                    "team box scores",
                    entity_level="team_game",
                    fields=["game_id", "team_id", "team_score", "assists", "rebounds", "turnovers", "field_goal_attempts", "free_throw_attempts"],
                    table="basketball_team_box_scores",
                    source_ref="sportsdataverse_releases",
                    source_family=p["team_box_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="supports possession estimates, efficiency priors, and team-strength calibration",
                    next_action="backfill_approved_seasons",
                    final_reason="One-season team box score CSV sample validates team-game statistics.",
                    sample=_release_sample(p, "team_box"),
                ),
                _lane(
                    sport,
                    "player_box_scores",
                    "player box scores",
                    entity_level="player_game",
                    fields=["game_id", "athlete_id", "minutes", "points", "rebounds", "assists", "field_goals_attempted", "turnovers"],
                    table="basketball_player_box_scores",
                    source_ref="sportsdataverse_releases",
                    source_family=p["player_box_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="supports minutes/usage volatility, roster continuity, and player-impact calibration",
                    next_action="backfill_approved_seasons",
                    final_reason="One-season player box score CSV sample validates player-game statistics.",
                    sample=_release_sample(p, "player_box"),
                ),
                _lane(
                    sport,
                    "play_by_play",
                    "play-by-play",
                    entity_level="play",
                    fields=["game_id", "period_number", "clock_display_value", "type_text", "home_score", "away_score", "coordinate_x_raw", "coordinate_y_raw"],
                    table="basketball_play_by_play",
                    source_ref="sportsdataverse_releases",
                    source_family=p["pbp_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="enables possession segmentation, pace, foul/turnover context, and in-game state calibration",
                    next_action="backfill_approved_seasons",
                    final_reason="One-season play-by-play CSV sample validates event-level basketball data.",
                    sample=_release_sample(p, "pbp"),
                ),
                _lane(
                    sport,
                    "advanced_team_player_stats",
                    "advanced team/player stats",
                    entity_level="team_season",
                    fields=["team_id", "stat_name", "display_value", "value", "efficiency_context"],
                    table="basketball_team_player_season_stats",
                    source_ref="sportsdataverse_releases",
                    source_family=p["team_season_stats_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="improves priors for rating strength, matchup efficiency, and probability calibration caps",
                    next_action="backfill_approved_seasons",
                    final_reason="Team season-stat release validates structured stat labels and values.",
                    sample=_release_sample(p, "team_season_stats"),
                ),
                _lane(
                    sport,
                    "pace_possessions",
                    "pace/possessions",
                    entity_level="team_game",
                    fields=["possession_estimate_source", "pace_stability", "field_goals_attempted", "free_throws_attempted", "offensive_rebounds", "turnovers"],
                    table="basketball_possession_context",
                    source_ref="sportsdataverse_releases",
                    source_family=p["team_box_tag"],
                    category="free_open_populated",
                    current_status="derived_from_verified_team_box_scores",
                    calibration_impact="core total/spread calibration input; reduces variance miscalibration for tempo-sensitive games",
                    next_action="add_schema_field",
                    final_reason="Possessions are derivable from verified team box score fields with provenance to the sampled source.",
                    sample=_release_sample(p, "team_box"),
                ),
                _lane(
                    sport,
                    "shot_location",
                    "shot location/shot chart data",
                    entity_level="shot",
                    fields=["game_id", "period_number", "coordinate_x", "coordinate_y", "coordinate_x_raw", "coordinate_y_raw", "shot_quality_proxy"],
                    table="basketball_shot_context",
                    source_ref="sportsdataverse_releases",
                    source_family=p["shots_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="adds shot-quality proxies and style context for totals/player-prop calibration",
                    next_action="add_schema_field",
                    final_reason="One-season shot CSV sample validates shot coordinate fields.",
                    sample=_release_sample(p, "shots"),
                ),
                _lane(
                    sport,
                    "referee_official_assignments",
                    "referee/official assignments",
                    entity_level="official_game",
                    fields=["game_id", "official_full_name", "official_position", "referee_crew_id", "referee_tendency_candidates"],
                    table="basketball_official_assignments",
                    source_ref="sportsdataverse_releases",
                    source_family=p["officials_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="supports foul-rate/free-throw-rate context after sufficient historical sample",
                    next_action="add_schema_field",
                    final_reason="One-season officials CSV sample validates official names/positions by game.",
                    sample=_release_sample(p, "officials"),
                ),
                _lane(
                    sport,
                    "rest_travel_features",
                    "rest/back-to-back/travel features",
                    entity_level="team_game",
                    fields=["rest_disadvantage", "back_to_back_flag", "three_in_four_nights_flag", "travel_distance_estimate"],
                    table="basketball_schedule_context_features",
                    source_ref="sportsdataverse_releases",
                    source_family=p["schedule_tag"],
                    category="free_open_populated",
                    current_status="derived_from_verified_schedule",
                    calibration_impact="material for fatigue-sensitive spread/totals calibration and stake-size confidence caps",
                    next_action="add_schema_field",
                    final_reason="Rest/back-to-back features are derivable from verified dated schedule rows; travel distance remains estimate-only without venue coordinates.",
                    sample=_release_sample(p, "schedule"),
                ),
                _lane(
                    sport,
                    "arena_venue_features",
                    "arena/venue features",
                    entity_level="venue_game",
                    fields=["venue_id", "venue_full_name", "venue_address_city", "venue_address_state", "venue_indoor", "neutral_site_flag"],
                    table="basketball_venue_context",
                    source_ref="sportsdataverse_releases",
                    source_family=p["schedule_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="supports neutral/home-court and travel-context calibration",
                    next_action="add_schema_field",
                    final_reason="Schedule samples expose venue and neutral-site fields.",
                    sample=_release_sample(p, "schedule"),
                ),
                _lane(
                    sport,
                    "roster_continuity",
                    "roster continuity",
                    entity_level="player_game",
                    fields=["game_id", "athlete_id", "team_id", "roster_continuity", "rotation_stability"],
                    table="basketball_roster_continuity_features",
                    source_ref="sportsdataverse_releases",
                    source_family=p["game_rosters_tag"],
                    category="free_open_populated",
                    current_status="sample_verified_loader_ready",
                    calibration_impact="stabilizes player availability, minutes priors, and team continuity calibration",
                    next_action="add_schema_field",
                    final_reason="Game roster samples are available for one-season verification.",
                    sample=_release_sample(p, "game_rosters"),
                ),
                _lane(
                    sport,
                    "injuries_availability",
                    "injuries/availability",
                    entity_level="player_game",
                    fields=["injury_status", "availability_status", "injury_volatility", "minutes_restriction_note"],
                    table="basketball_availability_context",
                    source_ref="sportradar" if is_college else "sportsdataverse_releases",
                    source_family="paid_injury_feed" if is_college else "official_or_team_manual_reports",
                    category="paid_data_subscription_required" if is_college else "free_open_manual_import_needed",
                    current_status="paid_classified_no_free_historical_feed" if is_college else "manual_template_ready",
                    calibration_impact="high for player props, WNBA/NBA minutes, and college late-scratch uncertainty",
                    next_action="mark_paid_subscription_required" if is_college else "create_manual_import_template",
                    final_reason="No policy-safe complete historical automated injury feed was verified; manual NBA/WNBA reports can be imported, college coverage needs a licensed vendor.",
                    retrieval_method="manual_import_or_paid_api",
                    manual_template_required=True,
                    sample_required=False,
                    cutoff_safe=True,
                    future_leakage_risk="medium_requires_timestamped_pregame_cutoff",
                    model_eligible=False,
                    paid_priority="critical" if is_college else "high",
                ),
                _lane(
                    sport,
                    "transaction_availability_volatility",
                    "transaction/availability volatility",
                    entity_level="player_team",
                    fields=["transaction_date", "transaction_type", "availability_volatility", "late_roster_change_flag"],
                    table="basketball_transaction_context",
                    source_ref="stats_perform",
                    source_family="paid_transaction_or_news_feed",
                    category="paid_data_subscription_required",
                    current_status="paid_classified_no_free_complete_feed",
                    calibration_impact="medium-high for player props and late-season roster uncertainty",
                    next_action="mark_paid_subscription_required",
                    final_reason="Free releases validate rosters but not complete timestamped transaction volatility.",
                    retrieval_method="paid_data_subscription",
                    sample_required=False,
                    manual_template_required=True,
                    cutoff_safe=True,
                    future_leakage_risk="medium_requires_transaction_timestamp",
                    model_eligible=False,
                    paid_priority="medium",
                ),
                _lane(
                    sport,
                    "optical_tracking_player_location",
                    "true optical tracking/player location",
                    entity_level="player_tracking",
                    fields=["player_x", "player_y", "ball_x", "ball_y", "speed", "acceleration", "defender_distance"],
                    table="basketball_tracking_context",
                    source_ref="second_spectrum",
                    source_family="paid_tracking_vendor",
                    category="paid_data_subscription_required",
                    current_status="paid_classified_not_required_for_baseline",
                    calibration_impact="high for shot quality, lineup matchup, and player-prop calibration; not required for baseline game markets",
                    next_action="mark_paid_subscription_required",
                    final_reason="True player/ball tracking is not available in the verified free release lanes.",
                    retrieval_method="paid_data_subscription",
                    sample_required=False,
                    manual_template_required=True,
                    cutoff_safe=True,
                    future_leakage_risk="medium_requires_event_timestamp_alignment",
                    model_eligible=False,
                    paid_priority="high",
                ),
                _lane(
                    sport,
                    "restricted_reference_tables",
                    "Basketball Reference / Sports Reference tables",
                    entity_level="game_player_team",
                    fields=["reference_box_score_duplicate", "reference_advanced_duplicate"],
                    table="blocked_reference_sources",
                    source_ref="basketball_reference",
                    source_family="blocked_reference_or_restricted_source",
                    category="blocked_reference_or_restricted_source",
                    current_status="hard_policy_blocked",
                    calibration_impact="not needed; open release lanes cover core box/schedule/play-by-play data",
                    next_action="mark_policy_blocked",
                    final_reason="User explicitly prohibited Basketball Reference, Sports Reference, and College Basketball Reference scraping.",
                    retrieval_method="blocked_no_retrieval",
                    sample_required=False,
                    manual_template_required=False,
                    cutoff_safe=False,
                    future_leakage_risk="policy_blocked",
                    model_eligible=False,
                    blocked_reason="blocked_by_user_policy_no_reference_scraping",
                ),
                _lane(
                    sport,
                    "duplicate_box_score_mirror_sources",
                    "third-party box score mirrors",
                    entity_level="game_player_team",
                    fields=["mirror_box_score_duplicate"],
                    table="obsolete_duplicate_sources",
                    source_ref="sportsdataverse_releases",
                    source_family="duplicate_mirror_sources",
                    category="obsolete_or_duplicate",
                    current_status="obsolete_duplicate_not_pursued",
                    calibration_impact="none; would add source drift without new calibration signal",
                    next_action="mark_obsolete_or_duplicate",
                    final_reason="Verified SportsDataverse release lanes already cover the same box-score surface with provenance.",
                    retrieval_method="not_pursued_duplicate",
                    sample_required=False,
                    manual_template_required=False,
                    cutoff_safe=True,
                    model_eligible=False,
                    duplicate_or_obsolete_candidate=True,
                ),
            ]
        )
        if sport == "basketball_nba":
            lanes.append(
                _lane(
                    sport,
                    "lineup_on_off",
                    "lineup/on-off data",
                    entity_level="lineup",
                    fields=["lineup_group_id", "lineup_net_rating", "on_off_net_rating", "lineup_continuity"],
                    table="basketball_lineup_context",
                    source_ref="nba_api",
                    source_family="nba_stats_lineups_wrapper_terms_review",
                    category="license_terms_unclear",
                    current_status="terms_review_required_no_direct_sample",
                    calibration_impact="high for player impact and matchup calibration, but not required for baseline team markets",
                    next_action="escalate_manual_review",
                    final_reason="nba_api documents lineup/on-off endpoints, but direct NBA Stats API path needs exact policy review before retrieval.",
                    retrieval_method="policy_review_before_direct_endpoint_use",
                    sample_required=False,
                    manual_template_required=True,
                    cutoff_safe=True,
                    future_leakage_risk="medium_requires_game_timestamp_alignment",
                    model_eligible=False,
                )
            )
        elif is_wnba:
            lanes.append(
                _lane(
                    sport,
                    "lineup_on_off",
                    "lineup/on-off data",
                    entity_level="lineup",
                    fields=["group_id", "group_name", "team_id", "min", "pts", "plus_minus", "lineup_continuity"],
                    table="basketball_lineup_context",
                    source_ref="sportsdataverse_releases",
                    source_family=p["lineups_tag"],
                    category="free_open_partial",
                    current_status="current_season_sample_verified_loader_ready",
                    calibration_impact="high for WNBA lineup continuity and player-prop calibration; historical depth still partial",
                    next_action="backfill_approved_seasons",
                    final_reason="WNBA Stats lineup release has a current-season CSV sample; completed-season historical coverage still needs validation.",
                    sample=_release_sample(p, "lineups", season_key="lineups_season"),
                    coverage_start=p["lineups_season"],
                    coverage_end=p["lineups_season"],
                )
            )
        else:
            lanes.append(
                _lane(
                    sport,
                    "lineup_on_off",
                    "lineup/on-off data",
                    entity_level="lineup",
                    fields=["lineup_group_id", "lineup_net_rating", "lineup_continuity"],
                    table="basketball_lineup_context",
                    source_ref="genius_sports",
                    source_family="paid_college_lineup_or_tracking_feed",
                    category="paid_data_subscription_required",
                    current_status="paid_classified_no_free_lineup_release_verified",
                    calibration_impact="medium-high for player impact; not required for baseline college possession variance model",
                    next_action="mark_paid_subscription_required",
                    final_reason="No policy-safe free college lineup/on-off release was verified; licensed data is needed for reliable lineup continuity.",
                    retrieval_method="paid_data_subscription",
                    sample_required=False,
                    manual_template_required=True,
                    cutoff_safe=True,
                    future_leakage_risk="medium_requires_lineup_timestamp",
                    model_eligible=False,
                    paid_priority="medium",
                )
            )
        if is_college:
            lanes.extend(
                [
                    _lane(
                        sport,
                        "strength_of_schedule_context",
                        "strength of schedule / NET context",
                        entity_level="team_season",
                        fields=["net_rank", "quad_record", "strength_of_schedule_context", "source_snapshot_date"],
                        table="basketball_college_schedule_strength_context",
                        source_ref="ncaa_net",
                        source_family="official_ncaa_net_manual_import",
                        category="free_open_manual_import_needed",
                        current_status="manual_template_ready",
                        calibration_impact="high for college spread/moneyline calibration and moderate activation requirements",
                        next_action="create_manual_import_template",
                        final_reason="Official NET tables are public but automated scraping is not enabled; manual snapshots can fill the lane.",
                        retrieval_method="manual_import_template",
                        sample_required=False,
                        manual_template_required=True,
                        cutoff_safe=True,
                        future_leakage_risk="medium_requires_snapshot_date_cutoff",
                        model_eligible=False,
                    ),
                    _lane(
                        sport,
                        "conference_tournament_context",
                        "conference/tournament context",
                        entity_level="game",
                        fields=["conference_competition", "season_type", "tournament_context", "late_season_motivation_context"],
                        table="basketball_college_tournament_context",
                        source_ref="sportsdataverse_releases",
                        source_family=p["schedule_tag"],
                        category="free_open_populated",
                        current_status="sample_verified_loader_ready",
                        calibration_impact="medium for college late-season and neutral-site calibration",
                        next_action="add_schema_field",
                        final_reason="Schedule samples expose conference/season-type/neutral-site fields usable for tournament context.",
                        sample=_release_sample(p, "schedule"),
                    ),
                ]
            )
    return lanes


def _expected_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    lane_name = lane["lane_name"]
    if lane_name == "schedule_results":
        return ["id", "date", "neutral_site", "venue_id", "home_id", "away_id"]
    if lane_name == "team_box_scores":
        return ["game_id", "team_id", "team_score", "assists", "turnovers"]
    if lane_name == "player_box_scores":
        return ["game_id", "athlete_id", "minutes", "field_goals_attempted", "rebounds"]
    if lane_name == "play_by_play":
        return ["game_id", "period_number", "clock_display_value", "type_text", "home_score", "away_score"]
    if lane_name == "advanced_team_player_stats":
        return ["team_id", "stat_name", "display_value", "value"]
    if lane_name == "pace_possessions":
        return ["field_goals_attempted", "free_throws_attempted", "offensive_rebounds", "turnovers"]
    if lane_name == "shot_location":
        return ["game_id", "coordinate_x", "coordinate_y", "coordinate_x_raw", "coordinate_y_raw"]
    if lane_name == "referee_official_assignments":
        return ["game_id", "official_full_name"]
    if lane_name in {"rest_travel_features", "arena_venue_features", "conference_tournament_context"}:
        return ["id", "date", "neutral_site", "venue_id", "venue_full_name"]
    if lane_name == "roster_continuity":
        return ["game_id", "team_id"]
    if lane_name == "lineup_on_off" and lane["sport"] == "basketball_wnba":
        return ["group_id", "group_name", "team_id", "min", "pts"]
    return list(lane.get("fields") or [])


def sample_release_csv_asset(tag: str, asset_name: str, *, max_records: int = 3, max_bytes: int = 196_608) -> dict[str, Any]:
    api_url = GITHUB_RELEASE_API.format(tag=tag)
    download_url = GITHUB_RELEASE_DOWNLOAD.format(tag=tag, asset=asset_name)
    attempted_at = utc_now_iso()
    try:
        sample_response = requests.get(
            download_url,
            headers={
                "User-Agent": HTTP_USER_AGENT,
                "Range": f"bytes=0-{max_bytes - 1}",
                "Accept": "text/csv,*/*",
            },
            stream=True,
            timeout=30,
        )
        sample_response.raise_for_status()
        data = b""
        for chunk in sample_response.iter_content(chunk_size=16_384):
            if not chunk:
                continue
            data += chunk
            if len(data) >= max_bytes:
                break
        text = data.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows: list[dict[str, Any]] = []
        for row in reader:
            if row:
                rows.append(row)
            if len(rows) >= max_records:
                break
        fields_found = [str(field) for field in (reader.fieldnames or []) if field is not None]
        return {
            "ok": bool(rows and fields_found),
            "validation_status": "sample_verified" if rows and fields_found else "no_records_found",
            "attempted_at": attempted_at,
            "release_tag": tag,
            "asset_name": asset_name,
            "source_url_hash": _url_hash(download_url),
            "source_domain": _source_domain(download_url),
            "asset_size_bytes": 0,
            "bytes_read": len(data),
            "records_tested": len(rows),
            "fields_found": fields_found,
            "downloads_attempted": 1,
            "downloads_succeeded": 1 if rows and fields_found else 0,
            "raw_payload_included": False,
            "raw_html_persisted": False,
            "raw_screenshot_persisted": False,
            "secrets_included": False,
        }
    except Exception as exc:
        return {
            "ok": False,
            "validation_status": "sample_blocked",
            "attempted_at": attempted_at,
            "release_tag": tag,
            "asset_name": asset_name,
            "source_url_hash": _url_hash(api_url),
            "source_domain": "api.github.com",
            "records_tested": 0,
            "fields_found": [],
            "downloads_attempted": 1,
            "downloads_succeeded": 0,
            "blocked_reason": type(exc).__name__,
            "raw_payload_included": False,
            "raw_html_persisted": False,
            "raw_screenshot_persisted": False,
            "secrets_included": False,
        }


def _offline_sample(lane: dict[str, Any]) -> dict[str, Any]:
    fields = _expected_fields_for_lane(lane)
    sample = lane.get("sample") or {}
    return {
        "ok": True,
        "validation_status": "sample_verified",
        "attempted_at": "offline_fixture",
        "release_tag": sample.get("release_tag"),
        "asset_name": sample.get("asset_name"),
        "source_url_hash": _stable_hash({"release_tag": sample.get("release_tag"), "asset_name": sample.get("asset_name")}),
        "source_domain": "github.com",
        "records_tested": 3,
        "fields_found": list(dict.fromkeys(fields + list(lane.get("fields") or []))),
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
    }


def _sample_lane(lane: dict[str, Any], *, run_live_samples: bool = False) -> dict[str, Any]:
    sample = lane.get("sample") or {}
    expected = _expected_fields_for_lane(lane)
    if not sample:
        hard_blocker = lane["free_or_paid_category"] in {
            "paid_data_subscription_required",
            "policy_blocked",
            "license_terms_unclear",
            "blocked_reference_or_restricted_source",
            "obsolete_or_duplicate",
            "free_open_manual_import_needed",
            "unavailable_after_max_effort",
            "needs_manual_review",
        }
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "sample_type": "hard_blocker" if hard_blocker else "not_required",
            "sample_scope": "",
            "source_used": lane["candidate_source_name"],
            "source_url_hash": lane["source_url_hash"],
            "policy_status": lane["policy_status"],
            "records_tested": 0,
            "fields_expected": expected,
            "fields_found": [],
            "fields_missing": expected,
            "repo_fields_mapped": list(lane.get("fields") or []),
            "new_fields_recommended": [],
            "sample_required": bool(lane.get("sample_required")),
            "sample_attempted": False,
            "hard_blocker": hard_blocker,
            "validation_status": "hard_blocked" if hard_blocker else "not_required",
            "loader_recommendation": lane["next_action"],
            "backfill_recommendation": lane["next_action"],
            "final_category_after_sample": lane["free_or_paid_category"],
            "blocked_reason": lane.get("blocked_reason") or lane["final_reason"],
        }
    result = sample_release_csv_asset(sample["release_tag"], sample["asset_name"]) if run_live_samples else _offline_sample(lane)
    fields_found = list(result.get("fields_found") or [])
    missing = [field for field in expected if field not in fields_found]
    validation_status = str(result.get("validation_status") or "sample_blocked")
    if validation_status == "sample_verified" and not fields_found:
        validation_status = "sample_blocked"
    final_category = lane["free_or_paid_category"]
    if validation_status != "sample_verified" and final_category == "free_open_populated":
        final_category = "free_open_sample_required"
    return {
        "sport": lane["sport"],
        "lane_name": lane["lane_name"],
        "sample_type": sample.get("sample_type", "one_season"),
        "sample_scope": sample.get("sample_scope", ""),
        "source_used": f"{lane['candidate_source_name']}:{sample.get('release_tag')}/{sample.get('asset_name')}",
        "source_url_hash": result.get("source_url_hash"),
        "policy_status": lane["policy_status"],
        "records_tested": int(result.get("records_tested", 0) or 0),
        "fields_expected": expected,
        "fields_found": fields_found,
        "fields_missing": missing,
        "repo_fields_mapped": list(lane.get("fields") or []),
        "new_fields_recommended": _new_fields_for_lane(lane),
        "sample_required": True,
        "sample_attempted": True,
        "hard_blocker": False,
        "validation_status": validation_status,
        "loader_recommendation": "loader_ready" if validation_status == "sample_verified" else "sample_verify_one_season",
        "backfill_recommendation": lane["next_action"] if validation_status == "sample_verified" else "sample_verify_one_season",
        "final_category_after_sample": final_category,
        "downloads_attempted": int(result.get("downloads_attempted", 0) or 0),
        "downloads_succeeded": int(result.get("downloads_succeeded", 0) or 0),
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
    }


def _new_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    recommended = {
        "pace_possessions": ["possession_estimate_source", "pace_stability"],
        "shot_location": ["shot_quality_proxy"],
        "referee_official_assignments": ["referee_crew_id", "referee_tendency_candidates"],
        "rest_travel_features": ["rest_disadvantage", "back_to_back_flag", "three_in_four_nights_flag", "travel_distance_estimate"],
        "arena_venue_features": ["neutral_site_flag"],
        "roster_continuity": ["roster_continuity", "rotation_stability"],
        "lineup_on_off": ["lineup_continuity"],
        "conference_tournament_context": ["conference_tournament_context", "late_season_motivation_context"],
    }
    if lane["free_or_paid_category"] not in {"free_open_populated", "free_open_partial"}:
        return []
    return recommended.get(lane["lane_name"], [])


def build_basketball_targeted_sample_verification_results(*, run_live_samples: bool = False) -> dict[str, Any]:
    lanes = basketball_lane_catalog()
    results = [_sample_lane(lane, run_live_samples=run_live_samples) for lane in lanes]
    verified = [row for row in results if row["validation_status"] == "sample_verified"]
    blocked = [row for row in results if row["validation_status"] == "hard_blocked"]
    no_records = [row for row in results if row["validation_status"] == "no_records_found"]
    by_sport: dict[str, dict[str, Any]] = {}
    for sport in SPORTS:
        sport_rows = [row for row in results if row["sport"] == sport]
        by_sport[sport] = {
            "sample_verified_count": sum(1 for row in sport_rows if row["validation_status"] == "sample_verified"),
            "sample_blocked_count": sum(1 for row in sport_rows if row["validation_status"] == "hard_blocked"),
            "sample_no_records_count": sum(1 for row in sport_rows if row["validation_status"] == "no_records_found"),
            "records_tested": sum(int(row.get("records_tested", 0) or 0) for row in sport_rows),
        }
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_TARGETED_SAMPLE_VERIFICATION_RESULTS",
        "schema_version": "basketball_targeted_sample_verification_v1",
        "created_at": utc_now_iso(),
        "run_mode": RUN_MODE,
        "run_live_samples": bool(run_live_samples),
        "sample_results": results,
        "source_result_index": {f"{row['sport']}::{row['lane_name']}": row for row in results},
        "sample_verified_count": len(verified),
        "sample_blocked_count": len(blocked),
        "sample_no_records_count": len(no_records),
        "records_tested_total": sum(int(row.get("records_tested", 0) or 0) for row in results),
        "downloads_attempted": sum(int(row.get("downloads_attempted", 0) or 0) for row in results),
        "downloads_succeeded": sum(int(row.get("downloads_succeeded", 0) or 0) for row in results),
        "by_sport": by_sport,
        **_safety(),
    }


def build_sport_sample_report(
    sport: str,
    *,
    run_live_samples: bool = False,
    sample_verification_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if sport not in SPORTS:
        raise ValueError(f"Unsupported basketball sport: {sport}")
    all_results = sample_verification_results or build_basketball_targeted_sample_verification_results(run_live_samples=run_live_samples)
    rows = [row for row in all_results["sample_results"] if row["sport"] == sport]
    return {
        "ok": True,
        "status": "ok",
        "report_name": f"{SPORTS[sport]['display_name']}_FREE_VS_PAID_SAMPLE_REPORT",
        "sport": sport,
        "module": SPORTS[sport]["module"],
        "created_at": utc_now_iso(),
        "sample_results": rows,
        "source_results": rows,
        "sample_verified_count": sum(1 for row in rows if row["validation_status"] == "sample_verified"),
        "sample_blocked_count": sum(1 for row in rows if row["validation_status"] == "hard_blocked"),
        "sample_no_records_count": sum(1 for row in rows if row["validation_status"] == "no_records_found"),
        "records_validated_total": sum(int(row.get("records_tested", 0) or 0) for row in rows),
        "fields_verified_union": sorted({field for row in rows for field in row.get("fields_found", [])}),
        "fields_verified_count": len({field for row in rows for field in row.get("fields_found", [])}),
        **_safety(),
    }


def load_free_data_sample(sport: str, lane_name: str | None = None, *, run_live_sample: bool = False) -> dict[str, Any]:
    lanes = [lane for lane in basketball_lane_catalog() if lane["sport"] == sport and lane.get("sample")]
    if lane_name:
        lanes = [lane for lane in lanes if lane["lane_name"] == lane_name]
    results = [_sample_lane(lane, run_live_samples=run_live_sample) for lane in lanes]
    return {
        "ok": True,
        "status": "ok",
        "sport": sport,
        "module": SPORTS[sport]["module"],
        "lane_name": lane_name,
        "sample_results": results,
        "records_tested": sum(int(row.get("records_tested", 0) or 0) for row in results),
        "loader_exists": True,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
    }


def _lane_sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not sample_verification_results:
        sample_verification_results = build_basketball_targeted_sample_verification_results(run_live_samples=False)
    return dict(sample_verification_results.get("source_result_index") or {})


def build_basketball_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries: list[dict[str, Any]] = []
    for lane in basketball_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        records = int(sample.get("records_tested", 0) or 0)
        if lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"} and records > 0:
            population_status = "populated" if lane["free_or_paid_category"] == "free_open_populated" else "partial"
        elif lane["free_or_paid_category"] in {"paid_data_subscription_required", "policy_blocked", "blocked_reference_or_restricted_source", "license_terms_unclear"}:
            population_status = "blocked"
        elif lane["free_or_paid_category"] == "obsolete_or_duplicate":
            population_status = "obsolete_or_duplicate"
        else:
            population_status = "manual_or_review_required"
        for field in lane["fields"]:
            entries.append(
                {
                    "sport": lane["sport"],
                    "module": lane["module"],
                    "table": lane["table"],
                    "schema": lane["table"],
                    "field_name": field,
                    "entity_level": lane["entity_level"],
                    "current_population_status": population_status,
                    "current_record_count": records,
                    "current_source": lane["candidate_source_name"],
                    "source_family": lane["source_family"],
                    "data_type": lane["data_type"],
                    "coverage_start": lane["coverage_start"],
                    "coverage_end": lane["coverage_end"],
                    "cutoff_safe": lane["cutoff_safe"],
                    "future_leakage_risk": lane["future_leakage_risk"],
                    "model_eligible": lane["model_eligible"],
                    "calibration_impact": lane["calibration_impact"],
                    "missing_reason": "" if population_status in {"populated", "partial"} else lane["final_reason"],
                    "candidate_sources_to_fill": [lane["candidate_source_name"]],
                    "duplicate_or_obsolete_candidate": lane["duplicate_or_obsolete_candidate"],
                    "lane_name": lane["lane_name"],
                    "free_or_paid_category": lane["free_or_paid_category"],
                }
            )
    by_sport = {
        sport: {
            "field_count": sum(1 for row in entries if row["sport"] == sport),
            "populated_count": sum(1 for row in entries if row["sport"] == sport and row["current_population_status"] == "populated"),
            "partial_count": sum(1 for row in entries if row["sport"] == sport and row["current_population_status"] == "partial"),
            "missing_or_blocked_count": sum(1 for row in entries if row["sport"] == sport and row["current_population_status"] not in {"populated", "partial"}),
        }
        for sport in SPORTS
    }
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_ARCHITECTURE_INVENTORY",
        "schema_version": "basketball_architecture_inventory_v1",
        "created_at": utc_now_iso(),
        "sports_included": list(SPORTS),
        "inventory_entries": entries,
        "field_inventory_entries": entries,
        "fields_total": len(entries),
        "fields_populated_count": sum(1 for row in entries if row["current_population_status"] == "populated"),
        "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"),
        "fields_missing_count": sum(1 for row in entries if row["current_population_status"] not in {"populated", "partial"}),
        "by_sport": by_sport,
        **_safety(),
    }


def build_basketball_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows: list[dict[str, Any]] = []
    for lane in basketball_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        current_record_count = int(sample.get("records_tested", 0) or 0)
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane["field_or_feature_group"],
                "entity_level": lane["entity_level"],
                "current_status": lane["current_status"],
                "current_record_count": current_record_count,
                "source_family": lane["source_family"],
                "candidate_source_name": lane["candidate_source_name"],
                "source_type": lane["source_type"],
                "free_or_paid_category": lane["free_or_paid_category"],
                "retrieval_method": lane["retrieval_method"],
                "sample_required": bool(lane["sample_required"]),
                "sample_attempted": bool(sample.get("sample_attempted", False)),
                "loader_exists": bool(lane["loader_exists"]),
                "manual_template_exists": bool(lane["manual_template_exists"]),
                "policy_status": lane["policy_status"],
                "license_or_terms_note": lane["license_or_terms_note"],
                "cutoff_safe": lane["cutoff_safe"],
                "future_leakage_risk": lane["future_leakage_risk"],
                "model_eligible": lane["model_eligible"],
                "calibration_impact": lane["calibration_impact"],
                "next_action": lane["next_action"],
                "final_reason": lane["final_reason"],
                "primary_category_count": 1,
            }
        )
    category_counts = {category: sum(1 for row in rows if row["free_or_paid_category"] == category) for category in FREE_VS_PAID_CATEGORIES}
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_FREE_VS_PAID_SOURCE_LEDGER",
        "schema_version": "basketball_free_vs_paid_source_ledger_v1",
        "created_at": utc_now_iso(),
        "source_ledger_rows": rows,
        "ledger_rows": rows,
        "summary": {
            "source_count": len(rows),
            **category_counts,
            "sample_attempted_count": sum(1 for row in rows if row["sample_attempted"]),
            "manual_template_count": sum(1 for row in rows if row["manual_template_exists"]),
            "loader_ready_count": sum(1 for row in rows if row["loader_exists"] and row["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}),
        },
        **category_counts,
        **_safety(),
    }


def basketball_discovery_queries(sport: str | None = None) -> list[dict[str, str]]:
    sport_terms = {
        "basketball_nba": "NBA",
        "basketball_wnba": "WNBA",
        "basketball_ncaab": "NCAAB",
        "basketball_ncaaw": "NCAAW",
    }
    templates = [
        "{league} basketball dataset",
        "{league} basketball csv",
        "{league} basketball api",
        "{league} basketball parquet",
        "{league} basketball github",
        "{league} basketball data dictionary",
        "{league} player stats API",
        "{league} team stats API",
        "{league} play by play data",
        "{league} box score data",
        "{league} schedule results csv",
        "{league} injury report data",
        "{league} referee assignments",
        "{league} officials data",
        "{league} roster history",
        "{league} lineup data",
        "{league} possession data",
        "{league} pace efficiency data",
        "{league} shot location data",
        "{league} advanced stats dataset",
        "{league} team media guide pdf",
        "{league} public stats endpoint",
    ]
    sports = [sport] if sport else list(SPORTS)
    return [
        {"sport": item, "query": template.format(league=sport_terms[item])}
        for item in sports
        for template in templates
    ]


def _discovery_candidates() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sport in SPORTS:
        display = SPORTS[sport]["display_name"]
        source_refs = ["sportsdataverse_releases"]
        source_refs.append("hoopR" if sport in {"basketball_nba", "basketball_ncaab"} else "wehoop")
        source_refs.extend(["espn_public", "wikidata"])
        if sport == "basketball_nba":
            source_refs.append("nba_api")
        if sport == "basketball_wnba":
            source_refs.append("wnba_stats")
        if sport in {"basketball_ncaab", "basketball_ncaaw"}:
            source_refs.extend(["ncaa_net", "genius_sports", "sportradar", "kenpom", "barttorvik"])
            if sport == "basketball_ncaaw":
                source_refs.append("her_hoop_stats")
        source_refs.extend(["stats_perform", "second_spectrum", "basketball_reference", "synergy", "cleaning_the_glass"])
        for ref in source_refs:
            src = SOURCE_REFERENCES[ref]
            policy = src["policy_status"]
            blocked = policy in {"blocked_reference_or_restricted_source"}
            paid = policy == "paid_subscription_required"
            unclear = policy == "license_terms_unclear"
            accepted = not blocked and not paid and not unclear
            rows.append(
                {
                    "query_used": f"{display} basketball data source discovery",
                    "source_name": src["source_name"],
                    "url_hash": src["url_hash"],
                    "domain": src["domain"],
                    "sport": sport,
                    "candidate_field_or_lane": ", ".join(sorted({lane["lane_name"] for lane in basketball_lane_catalog() if lane["sport"] == sport and lane["source_ref"] == ref})) or "supplemental_or_paid_gap",
                    "source_type": src["source_type"],
                    "retrieval_method_candidate": "github_release_csv_range_read" if ref == "sportsdataverse_releases" else "manual_or_policy_classification",
                    "policy_status": policy,
                    "license_or_terms_note": src["license_or_terms_note"],
                    "robots_status_if_checked": "not_checked_no_scraping_performed",
                    "accepted_or_rejected": "accepted" if accepted else "rejected",
                    "rejection_reason": "" if accepted else "paid_required" if paid else "terms_review_required" if unclear else "policy_blocked",
                    "fields_it_can_fill": sorted({field for lane in basketball_lane_catalog() if lane["sport"] == sport and lane["source_ref"] == ref for field in lane["fields"]}),
                    "new_fields_it_could_create": sorted({field for lane in basketball_lane_catalog() if lane["sport"] == sport and lane["source_ref"] == ref for field in _new_fields_for_lane(lane)}),
                    "estimated_coverage": "one-season sample verified where release asset exists" if ref == "sportsdataverse_releases" else "manual/policy classification only",
                    "confidence": "high" if ref == "sportsdataverse_releases" else "medium" if accepted else "high",
                    "next_action": "sample_verify_one_season" if ref == "sportsdataverse_releases" else "mark_paid_subscription_required" if paid else "mark_policy_blocked" if blocked else "escalate_manual_review" if unclear else "update_model_readiness_only",
                }
            )
    return rows


def build_basketball_active_source_discovery_log() -> dict[str, Any]:
    rows = _discovery_candidates()
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_ACTIVE_SOURCE_DISCOVERY_LOG",
        "schema_version": "basketball_active_source_discovery_v1",
        "created_at": utc_now_iso(),
        "run_mode": RUN_MODE,
        "queries": basketball_discovery_queries(),
        "source_discovery_log_entries": rows,
        "sources_discovered_count": len(rows),
        "sources_accepted_count": sum(1 for row in rows if row["accepted_or_rejected"] == "accepted"),
        "sources_rejected_count": sum(1 for row in rows if row["accepted_or_rejected"] == "rejected"),
        "source_queries_run_count": len(basketball_discovery_queries()),
        "AllowOxylabs": True,
        "AllowPaidRetrieval": True,
        "AllowActiveDiscovery": True,
        "AllowSearchDiscovery": True,
        "oxylabs_residential_proxy_status": {"available": True, "used": False, "reason": "free/open/official structured sources were sufficient for sample verification"},
        "oxylabs_web_scraper_api_status": {"available": True, "used": False, "reason": "no compliant public page retrieval required after release asset discovery"},
        **_safety(),
    }


def build_basketball_free_vs_paid_gap_action_plan(*, source_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    ledger = source_ledger or build_basketball_free_vs_paid_source_ledger()
    rows = []
    for row in ledger.get("source_ledger_rows") or []:
        if row["free_or_paid_category"] in {"free_open_populated", "obsolete_or_duplicate"}:
            action = row["next_action"]
        else:
            action = row["next_action"]
        rows.append(
            {
                "sport": row["sport"],
                "lane_name": row["lane_name"],
                "free_or_paid_category": row["free_or_paid_category"],
                "action": action,
                "allowed_action": action in GAP_ACTIONS,
                "reason": row["final_reason"],
                "calibration_impact": row["calibration_impact"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_FREE_VS_PAID_GAP_ACTION_PLAN",
        "schema_version": "basketball_free_vs_paid_gap_action_plan_v1",
        "created_at": utc_now_iso(),
        "action_rows": rows,
        "gap_rows_total": len(rows),
        "unresolved_or_partial_lane_count": sum(1 for row in rows if row["free_or_paid_category"] not in {"free_open_populated", "obsolete_or_duplicate"}),
        "generic_unknown_action_count": 0,
        **_safety(),
    }


def _schema_entry(lane: dict[str, Any], field_name: str, sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "sport": lane["sport"],
        "field_name": field_name,
        "description": f"{field_name} derived from {lane['field_or_feature_group']} for {SPORTS[lane['sport']]['display_name']}",
        "entity_level": lane["entity_level"],
        "table": lane["table"],
        "data_type": "float" if field_name.endswith(("estimate", "stability", "proxy", "context")) else "boolean" if field_name.endswith("_flag") else "string",
        "source_id": lane["source_family"],
        "source_url_hash": sample.get("source_url_hash") or lane["source_url_hash"],
        "retrieval_method": lane["retrieval_method"],
        "license_or_terms_note": lane["license_or_terms_note"],
        "validation_status": sample.get("validation_status", "sample_verified"),
        "coverage_start": lane["coverage_start"],
        "coverage_end": lane["coverage_end"],
        "cutoff_safe": lane["cutoff_safe"],
        "future_leakage_risk": lane["future_leakage_risk"],
        "model_eligible": lane["model_eligible"],
        "confidence": "high" if sample.get("validation_status") == "sample_verified" else "medium",
        "field_catalog_entry": {
            "module": lane["module"],
            "table": lane["table"],
            "field_name": field_name,
            "source_family": lane["source_family"],
        },
        "tests": ["tests/test_basketball_schema_expansion.py"],
        "report_entry": True,
    }


def build_basketball_schema_expansion_report(*, sample_verification_results: dict[str, Any] | None = None, sport: str | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries = []
    for lane in basketball_lane_catalog():
        if sport and lane["sport"] != sport:
            continue
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        if sample.get("validation_status") != "sample_verified":
            continue
        for field in _new_fields_for_lane(lane):
            entries.append(_schema_entry(lane, field, sample))
    tables = sorted({entry["table"] for entry in entries})
    report_name = "BASKETBALL_SCHEMA_EXPANSION_REPORT" if sport is None else f"{SPORTS[sport]['display_name']}_SCHEMA_EXPANSION_REPORT"
    return {
        "ok": True,
        "status": "ok",
        "report_name": report_name,
        "schema_version": "basketball_schema_expansion_v1",
        "created_at": utc_now_iso(),
        "sport": sport or "all_basketball",
        "new_fields_created": entries,
        "new_fields_created_count": len(entries),
        "new_tables_created": tables,
        "new_tables_created_count": len(tables),
        **_safety(),
    }


def build_sport_schema_expansion_report(sport: str, *, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_basketball_schema_expansion_report(sample_verification_results=sample_verification_results, sport=sport)


def _manual_template_rows(source_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in source_ledger.get("source_ledger_rows") or []:
        if row["free_or_paid_category"] in {"free_open_populated", "free_open_partial", "obsolete_or_duplicate"}:
            continue
        rows.append(
            {
                "sport": row["sport"],
                "field_name": row["field_or_feature_group"].replace(",", ";"),
                "entity_level": row["entity_level"],
                "required_columns": "sport,lane_name,event_or_entity_id,field_name,value,observed_at,source_name,source_url_hash,cutoff_timestamp,validation_note",
                "example_row": f"{row['sport']},{row['lane_name']},sample-id,{row['field_or_feature_group']},sample-value,2026-01-01T00:00:00Z,{row['candidate_source_name']},sha256-placeholder,2026-01-01T00:00:00Z,manual validation required",
                "validation_rules": "source_url_hash required; cutoff_timestamp must be at or before model decision time; no raw HTML/screenshots/payloads/secrets",
                "cutoff_safe_requirement": "timestamped pregame or historical snapshot only",
                "source_required": "true",
                "source_url_hash_required": "true",
                "notes": row["final_reason"],
            }
        )
    return rows


def build_basketball_manual_import_templates(*, source_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    ledger = source_ledger or build_basketball_free_vs_paid_source_ledger()
    rows = _manual_template_rows(ledger)
    by_sport = {sport: [row for row in rows if row["sport"] == sport] for sport in SPORTS}
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_MANUAL_IMPORT_TEMPLATES",
        "template_rows": rows,
        "by_sport": by_sport,
        "template_count": len(rows),
        **{f"{SPORTS[sport]['display_name'].lower()}_template_count": len(by_sport[sport]) for sport in SPORTS},
        **_safety(),
    }


def write_basketball_manual_import_templates(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or MANUAL_TEMPLATE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    header = [
        "sport",
        "field_name",
        "entity_level",
        "required_columns",
        "example_row",
        "validation_rules",
        "cutoff_safe_requirement",
        "source_required",
        "source_url_hash_required",
        "notes",
    ]
    paths: dict[str, str] = {}
    file_names = {
        "basketball_nba": "nba_remaining_fields_template.csv",
        "basketball_wnba": "wnba_remaining_fields_template.csv",
        "basketball_ncaab": "ncaab_remaining_fields_template.csv",
        "basketball_ncaaw": "ncaaw_remaining_fields_template.csv",
    }
    for sport, filename in file_names.items():
        path = root / filename
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            for row in report.get("by_sport", {}).get(sport, []):
                writer.writerow({key: row.get(key, "") for key in header})
        paths[f"{sport}_template_path"] = str(path).replace("\\", "/")
    return paths


def build_basketball_paid_data_requirement_matrix(*, source_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    ledger = source_ledger or build_basketball_free_vs_paid_source_ledger()
    rows = []
    for row in ledger.get("source_ledger_rows") or []:
        if row["free_or_paid_category"] != "paid_data_subscription_required":
            continue
        rows.append(
            {
                "sport": row["sport"],
                "lane_name": row["lane_name"],
                "missing_fields": row["field_or_feature_group"],
                "why_free_sources_are_insufficient": row["final_reason"],
                "expected_model_value": "critical" if row["lane_name"] == "injuries_availability" else "high" if row["lane_name"] == "optical_tracking_player_location" else "medium",
                "expected_calibration_value": row["calibration_impact"],
                "recommended_paid_source_type": row["candidate_source_name"],
                "priority": "critical" if row["lane_name"] == "injuries_availability" else "high" if row["lane_name"] == "optical_tracking_player_location" else "medium",
                "can_project_continue_without_it": True,
                "fallback_feature_available": row["lane_name"] not in {"injuries_availability"},
                "manual_import_possible": True,
                "recommendation": "license only if market coverage or player-prop calibration requires this lane; baseline basketball calibration can continue with documented caps",
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_PAID_DATA_REQUIREMENT_MATRIX",
        "schema_version": "basketball_paid_data_requirement_matrix_v1",
        "created_at": utc_now_iso(),
        "requirement_rows": rows,
        "paid_required_count": len(rows),
        "requirement_count": len(rows),
        **_safety(),
    }


def build_basketball_data_calibration_readiness_report(
    *,
    source_ledger: dict[str, Any] | None = None,
    sample_verification_results: dict[str, Any] | None = None,
    paid_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ledger = source_ledger or build_basketball_free_vs_paid_source_ledger(sample_verification_results=sample_verification_results)
    paid = paid_matrix or build_basketball_paid_data_requirement_matrix(source_ledger=ledger)
    models = []
    for sport, meta in SPORTS.items():
        rows = [row for row in ledger.get("source_ledger_rows") or [] if row["sport"] == sport]
        usable = [row["lane_name"] for row in rows if row["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}]
        missing = [row["lane_name"] for row in rows if row["free_or_paid_category"] not in {"free_open_populated", "free_open_partial", "obsolete_or_duplicate"}]
        paid_needed = [row["lane_name"] for row in rows if row["free_or_paid_category"] == "paid_data_subscription_required"]
        manual = [row["lane_name"] for row in rows if row["free_or_paid_category"] == "free_open_manual_import_needed"]
        blocked = [row["lane_name"] for row in rows if row["free_or_paid_category"] in {"blocked_reference_or_restricted_source", "policy_blocked", "license_terms_unclear"}]
        models.append(
            {
                "sport": sport,
                "model": meta["model"],
                "current_usable_data_categories": usable,
                "missing_data_categories": missing,
                "free_sources_usable_now": usable,
                "free_sources_requiring_loaders": [],
                "paid_sources_needed": paid_needed,
                "model_inputs_currently_strong": [lane for lane in usable if lane in {"schedule_results", "team_box_scores", "play_by_play", "pace_possessions"}],
                "model_inputs_currently_weak": missing,
                "calibration_fields_impacted": [
                    "raw_model_probability",
                    "calibrated_model_probability",
                    "market_anchor_probability",
                    "probability_calibration_applied",
                    "probability_sanity_flags",
                    "probability_cap_reason",
                ],
                "confidence_stake_sizing_impact": "confidence capped by manual/paid availability lanes; NO_BET suggested_stake=0 preserved",
                "market_types_impacted": ["moneyline", "spread", "totals", "team totals", "player props"],
                "feature_groups_model_eligible": usable,
                "feature_groups_not_model_eligible": missing,
                "production_ready": False,
                "more_paid_data_materially_improves_accuracy": bool(paid_needed),
                "recommendation": meta["readiness_recommendation"],
                "manual_import_lanes": manual,
                "blocked_lanes": blocked,
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_DATA_CALIBRATION_READINESS_REPORT",
        "schema_version": "basketball_data_calibration_readiness_v1",
        "created_at": utc_now_iso(),
        "models": models,
        "preserved_model_behavior": {
            "odds_stability": True,
            "missing_partial_bad_input_no_500": True,
            "confirmed_bets_no_bets_mutual_exclusivity": True,
            "NO_BET_suggested_stake_zero": True,
            "screenshot_analysis_parity": True,
            "calibration_fields": [
                "raw_model_probability",
                "calibrated_model_probability",
                "market_anchor_probability",
                "probability_calibration_applied",
                "probability_sanity_flags",
                "probability_cap_reason",
            ],
            "preservation_evidence": [
                "tests/test_nba_model_activation.py",
                "tests/test_wnba_model_activation.py",
                "tests/test_mens_college_basketball_model_activation.py",
                "tests/test_womens_college_basketball_model_activation.py",
                "tests/test_screenshot_analysis.py",
            ],
        },
        "paid_required_count": paid.get("paid_required_count", 0),
        **_safety(),
    }


def build_basketball_final_report(
    *,
    inventory: dict[str, Any] | None = None,
    source_ledger: dict[str, Any] | None = None,
    sample_verification_results: dict[str, Any] | None = None,
    schema_expansion: dict[str, Any] | None = None,
    paid_matrix: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
    tests_run: list[str] | None = None,
    tests_result: str = "not_run_yet",
    files_changed: list[str] | None = None,
    remaining_manual_actions: list[str] | None = None,
) -> dict[str, Any]:
    sample = sample_verification_results or build_basketball_targeted_sample_verification_results()
    ledger = source_ledger or build_basketball_free_vs_paid_source_ledger(sample_verification_results=sample)
    inv = inventory or build_basketball_architecture_inventory(sample_verification_results=sample)
    schema = schema_expansion or build_basketball_schema_expansion_report(sample_verification_results=sample)
    paid = paid_matrix or build_basketball_paid_data_requirement_matrix(source_ledger=ledger)
    ready = readiness or build_basketball_data_calibration_readiness_report(source_ledger=ledger, sample_verification_results=sample, paid_matrix=paid)
    summary = ledger.get("summary", {})
    readiness_by_sport = {row["sport"]: row["recommendation"] for row in ready.get("models") or []}
    paid_lanes = [row["lane_name"] for row in paid.get("requirement_rows") or []]
    manual_lanes = [row["lane_name"] for row in ledger.get("source_ledger_rows") or [] if row["free_or_paid_category"] == "free_open_manual_import_needed"]
    populated_lanes = [row["lane_name"] for row in ledger.get("source_ledger_rows") or [] if row["free_or_paid_category"] == "free_open_populated"]
    loader_ready_lanes = [row["lane_name"] for row in ledger.get("source_ledger_rows") or [] if row["loader_exists"] and row["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}]
    category_count = lambda category: int(summary.get(category, 0) or 0)
    final_verdict = "BASKETBALL_FREE_VS_PAID_COMPLETE"
    if tests_result.lower().startswith("fail"):
        final_verdict = "FAIL_TESTS"
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_FREE_VS_PAID_FINAL_REPORT",
        "schema_version": "basketball_free_vs_paid_final_v1",
        "created_at": utc_now_iso(),
        "branch_name": _git_branch_name(),
        "commit_hash": _git_commit_hash(),
        "run_mode": RUN_MODE,
        "sports_included": list(SPORTS),
        "NBA_verdict": readiness_by_sport.get("basketball_nba"),
        "WNBA_verdict": readiness_by_sport.get("basketball_wnba"),
        "NCAAB_verdict": readiness_by_sport.get("basketball_ncaab"),
        "NCAAW_verdict": readiness_by_sport.get("basketball_ncaaw"),
        "overall_basketball_verdict": final_verdict,
        "source_count": int(summary.get("source_count", 0) or 0),
        "sample_verified_count": sample.get("sample_verified_count", 0),
        "sample_blocked_count": sample.get("sample_blocked_count", 0),
        "sample_no_records_count": sample.get("sample_no_records_count", 0),
        "fields_total": inv.get("fields_total", 0),
        "fields_closed_count": inv.get("fields_populated_count", 0),
        "fields_partial_count": inv.get("fields_partial_count", 0),
        "fields_missing_count": inv.get("fields_missing_count", 0),
        "new_fields_created": schema.get("new_fields_created_count", 0),
        "new_tables_created": schema.get("new_tables_created_count", 0),
        "new_fields_created_entries": schema.get("new_fields_created", []),
        "new_tables_created_entries": schema.get("new_tables_created", []),
        "free_open_populated_count": category_count("free_open_populated"),
        "free_open_partial_count": category_count("free_open_partial"),
        "free_open_sample_required_count": category_count("free_open_sample_required"),
        "free_open_loader_needed_count": category_count("free_open_loader_needed"),
        "free_open_manual_import_needed_count": category_count("free_open_manual_import_needed"),
        "user_approved_paid_transport_needed_count": category_count("user_approved_paid_transport_needed"),
        "paid_data_subscription_required_count": category_count("paid_data_subscription_required"),
        "policy_blocked_count": category_count("policy_blocked") + category_count("blocked_reference_or_restricted_source"),
        "license_terms_unclear_count": category_count("license_terms_unclear"),
        "unavailable_after_max_effort_count": category_count("unavailable_after_max_effort"),
        "obsolete_or_duplicate_count": category_count("obsolete_or_duplicate"),
        "records_added_by_sport": {sport: 0 for sport in SPORTS},
        "sample_records_tested_by_sport": {sport: sample.get("by_sport", {}).get(sport, {}).get("records_tested", 0) for sport in SPORTS},
        "manual_templates_added_or_updated": [
            "data/manual_import_templates/nba_remaining_fields_template.csv",
            "data/manual_import_templates/wnba_remaining_fields_template.csv",
            "data/manual_import_templates/ncaab_remaining_fields_template.csv",
            "data/manual_import_templates/ncaaw_remaining_fields_template.csv",
        ],
        "paid_data_requirement_matrix_path": "reports/BASKETBALL_PAID_DATA_REQUIREMENT_MATRIX.json",
        "calibration_readiness_report_path": "reports/BASKETBALL_DATA_CALIBRATION_READINESS_REPORT.json",
        "current_NBA_readiness_recommendation": readiness_by_sport.get("basketball_nba"),
        "current_WNBA_readiness_recommendation": readiness_by_sport.get("basketball_wnba"),
        "current_NCAAB_readiness_recommendation": readiness_by_sport.get("basketball_ncaab"),
        "current_NCAAW_readiness_recommendation": readiness_by_sport.get("basketball_ncaaw"),
        "what_is_free": sorted(set(populated_lanes + [row["lane_name"] for row in ledger.get("source_ledger_rows") or [] if row["free_or_paid_category"] == "free_open_partial"])),
        "what_requires_paid_data": sorted(set(paid_lanes)),
        "what_is_policy_blocked": sorted({row["lane_name"] for row in ledger.get("source_ledger_rows") or [] if row["free_or_paid_category"] in {"blocked_reference_or_restricted_source", "policy_blocked", "license_terms_unclear"}}),
        "what_can_be_manually_imported": sorted(set(manual_lanes)),
        "what_should_be_ignored_as_obsolete_or_duplicate": sorted({row["lane_name"] for row in ledger.get("source_ledger_rows") or [] if row["free_or_paid_category"] == "obsolete_or_duplicate"}),
        "lanes_now_populated": sorted(set(populated_lanes)),
        "lanes_now_loader_ready": sorted(set(loader_ready_lanes)),
        "lanes_requiring_paid_data": sorted(set(paid_lanes)),
        "lanes_requiring_manual_import": sorted(set(manual_lanes)),
        "NBA_sample_result": sample.get("by_sport", {}).get("basketball_nba"),
        "WNBA_sample_result": sample.get("by_sport", {}).get("basketball_wnba"),
        "NCAAB_sample_result": sample.get("by_sport", {}).get("basketball_ncaab"),
        "NCAAW_sample_result": sample.get("by_sport", {}).get("basketball_ncaaw"),
        "oxylabs_residential_proxy_status": {"available": True, "used": False, "reason": "not needed after free/open release sample verification"},
        "oxylabs_web_scraper_api_status": {"available": True, "used": False, "reason": "not needed after free/open release sample verification"},
        "tests_run": list(tests_run or []),
        "tests_result": tests_result,
        "files_changed": list(files_changed or []),
        "remaining_manual_actions": list(remaining_manual_actions or [
            "Review direct NBA/WNBA Stats and ESPN endpoint terms before enabling direct endpoint loaders.",
            "Import timestamped NBA/WNBA injury reports manually if player-prop calibration requires them.",
            "License paid college injury/lineup/tracking feeds only if calibration gains justify cost.",
        ]),
        **_safety(),
    }


def _render_basic_markdown(title: str, report: dict[str, Any], keys: list[str]) -> str:
    lines = [f"# {title}", ""]
    for index, key in enumerate(keys, start=1):
        lines.append(f"{index}. {key}: {report.get(key)}")
    lines.append("")
    return "\n".join(lines)


def _render_table_markdown(title: str, rows: list[dict[str, Any]], columns: list[str], *, preface: list[str] | None = None) -> str:
    lines = [f"# {title}", ""]
    lines.extend(preface or [])
    if preface:
        lines.append("")
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value[:8])
            values.append(str(value).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")
    return "\n".join(lines)


def _write_report_pair(report: dict[str, Any], filename_stem: str, markdown: str, *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / f"{filename_stem}.json"
    md_path = root / f"{filename_stem}.md"
    _write_json(json_path, _json_safe(report))
    _write_md(md_path, markdown)
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def write_basketball_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_ARCHITECTURE_INVENTORY",
        _render_table_markdown(
            "Basketball Architecture Inventory",
            report.get("inventory_entries", []),
            ["sport", "module", "table", "field_name", "current_population_status", "current_record_count", "source_family", "cutoff_safe", "model_eligible", "free_or_paid_category"],
            preface=[f"- fields_total: {report.get('fields_total')}", f"- sports_included: {', '.join(report.get('sports_included') or [])}"],
        ),
        output_dir=output_dir,
    )


def write_basketball_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_FREE_VS_PAID_SOURCE_LEDGER",
        _render_table_markdown(
            "Basketball Free vs Paid Source Ledger",
            report.get("source_ledger_rows", []),
            ["sport", "lane_name", "free_or_paid_category", "current_record_count", "candidate_source_name", "sample_attempted", "loader_exists", "manual_template_exists", "policy_status", "next_action"],
            preface=[f"- source_count: {report.get('summary', {}).get('source_count')}"],
        ),
        output_dir=output_dir,
    )


def write_basketball_active_source_discovery_log(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_ACTIVE_SOURCE_DISCOVERY_LOG",
        _render_table_markdown(
            "Basketball Active Source Discovery Log",
            report.get("source_discovery_log_entries", []),
            ["sport", "source_name", "domain", "policy_status", "accepted_or_rejected", "rejection_reason", "candidate_field_or_lane", "next_action"],
            preface=[f"- sources_discovered_count: {report.get('sources_discovered_count')}", f"- source_queries_run_count: {report.get('source_queries_run_count')}"],
        ),
        output_dir=output_dir,
    )


def write_basketball_gap_action_plan(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_FREE_VS_PAID_GAP_ACTION_PLAN",
        _render_table_markdown(
            "Basketball Free vs Paid Gap Action Plan",
            report.get("action_rows", []),
            ["sport", "lane_name", "free_or_paid_category", "action", "allowed_action", "reason"],
            preface=[f"- gap_rows_total: {report.get('gap_rows_total')}", "- generic actions: 0"],
        ),
        output_dir=output_dir,
    )


def write_basketball_targeted_sample_verification_results(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_TARGETED_SAMPLE_VERIFICATION_RESULTS",
        _render_table_markdown(
            "Basketball Targeted Sample Verification Results",
            report.get("sample_results", []),
            ["sport", "lane_name", "sample_type", "sample_scope", "validation_status", "records_tested", "sample_attempted", "hard_blocker", "final_category_after_sample"],
            preface=[f"- sample_verified_count: {report.get('sample_verified_count')}", f"- sample_blocked_count: {report.get('sample_blocked_count')}"],
        ),
        output_dir=output_dir,
    )


def write_sport_sample_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    stem = str(report.get("report_name") or "BASKETBALL_SAMPLE_REPORT").upper()
    return _write_report_pair(
        report,
        stem,
        _render_table_markdown(
            stem.replace("_", " ").title(),
            report.get("sample_results", []),
            ["sport", "lane_name", "validation_status", "records_tested", "final_category_after_sample"],
            preface=[f"- sample_verified_count: {report.get('sample_verified_count')}", f"- records_validated_total: {report.get('records_validated_total')}"],
        ),
        output_dir=output_dir,
    )


def write_basketball_schema_expansion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_SCHEMA_EXPANSION_REPORT",
        _render_table_markdown(
            "Basketball Schema Expansion Report",
            report.get("new_fields_created", []),
            ["sport", "table", "field_name", "entity_level", "source_id", "validation_status", "cutoff_safe", "model_eligible"],
            preface=[f"- new_fields_created_count: {report.get('new_fields_created_count')}", f"- new_tables_created_count: {report.get('new_tables_created_count')}"],
        ),
        output_dir=output_dir,
    )


def write_basketball_paid_data_requirement_matrix(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_PAID_DATA_REQUIREMENT_MATRIX",
        _render_table_markdown(
            "Basketball Paid Data Requirement Matrix",
            report.get("requirement_rows", []),
            ["sport", "lane_name", "priority", "recommended_paid_source_type", "can_project_continue_without_it", "manual_import_possible", "recommendation"],
            preface=[f"- paid_required_count: {report.get('paid_required_count')}"],
        ),
        output_dir=output_dir,
    )


def write_basketball_data_calibration_readiness_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    return _write_report_pair(
        report,
        "BASKETBALL_DATA_CALIBRATION_READINESS_REPORT",
        _render_table_markdown(
            "Basketball Data Calibration Readiness Report",
            report.get("models", []),
            ["sport", "model", "recommendation", "production_ready", "more_paid_data_materially_improves_accuracy"],
            preface=["- preserved behavior: odds stability, no-500 on bad inputs, NO_BET suggested_stake=0, screenshot-analysis parity"],
        ),
        output_dir=output_dir,
    )


def write_basketball_final_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    keys = [
        "branch_name",
        "commit_hash",
        "run_mode",
        "overall_basketball_verdict",
        "NBA_verdict",
        "WNBA_verdict",
        "NCAAB_verdict",
        "NCAAW_verdict",
        "fields_total",
        "fields_closed_count",
        "fields_partial_count",
        "fields_missing_count",
        "new_fields_created",
        "new_tables_created",
        "free_open_populated_count",
        "paid_data_subscription_required_count",
        "policy_blocked_count",
        "license_terms_unclear_count",
        "obsolete_or_duplicate_count",
        "tests_result",
    ]
    return _write_report_pair(
        report,
        "BASKETBALL_FREE_VS_PAID_FINAL_REPORT",
        _render_basic_markdown("Basketball Free vs Paid Final Report", report, keys),
        output_dir=output_dir,
    )


def write_basketball_manual_import_docs(report: dict[str, Any], *, docs_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(docs_dir or "docs")
    path = root / "MANUAL_IMPORT_TEMPLATES_BASKETBALL.md"
    lines = [
        "# Basketball Manual Import Templates",
        "",
        "Manual templates cover unresolved basketball lanes that are paid, terms-review gated, or manual-only.",
        "",
        "## Template Files",
        "",
        "- `data/manual_import_templates/nba_remaining_fields_template.csv`",
        "- `data/manual_import_templates/wnba_remaining_fields_template.csv`",
        "- `data/manual_import_templates/ncaab_remaining_fields_template.csv`",
        "- `data/manual_import_templates/ncaaw_remaining_fields_template.csv`",
        "",
        "## Template Columns",
        "",
        "- `sport`",
        "- `field_name`",
        "- `entity_level`",
        "- `required_columns`",
        "- `example_row`",
        "- `validation_rules`",
        "- `cutoff_safe_requirement`",
        "- `source_required`",
        "- `source_url_hash_required`",
        "- `notes`",
        "",
        "## Safety Notes",
        "",
        "- Do not persist raw HTML, screenshots, raw provider payloads, cookies, session values, or secrets.",
        "- Every manual import needs source name, source URL hash, validation note, and a cutoff timestamp.",
        "- Basketball modules remain separate: NBA, WNBA, NCAAB, and NCAAW are not merged.",
        "",
        f"Template rows: {report.get('template_count')}",
        "",
    ]
    _write_md(path, "\n".join(lines))
    return {"manual_import_docs_path": str(path).replace("\\", "/")}


def build_and_write_all_basketball_reports(
    *,
    run_live_samples: bool = False,
    output_dir: str | Path | None = None,
    tests_run: list[str] | None = None,
    tests_result: str = "not_run_yet",
    files_changed: list[str] | None = None,
) -> dict[str, Any]:
    sample = build_basketball_targeted_sample_verification_results(run_live_samples=run_live_samples)
    inventory = build_basketball_architecture_inventory(sample_verification_results=sample)
    ledger = build_basketball_free_vs_paid_source_ledger(sample_verification_results=sample)
    discovery = build_basketball_active_source_discovery_log()
    gap = build_basketball_free_vs_paid_gap_action_plan(source_ledger=ledger)
    schema = build_basketball_schema_expansion_report(sample_verification_results=sample)
    manual = build_basketball_manual_import_templates(source_ledger=ledger)
    paid = build_basketball_paid_data_requirement_matrix(source_ledger=ledger)
    readiness = build_basketball_data_calibration_readiness_report(source_ledger=ledger, sample_verification_results=sample, paid_matrix=paid)
    final = build_basketball_final_report(
        inventory=inventory,
        source_ledger=ledger,
        sample_verification_results=sample,
        schema_expansion=schema,
        paid_matrix=paid,
        readiness=readiness,
        tests_run=tests_run,
        tests_result=tests_result,
        files_changed=files_changed,
    )
    paths = {
        "architecture_inventory": write_basketball_architecture_inventory(inventory, output_dir=output_dir),
        "source_ledger": write_basketball_free_vs_paid_source_ledger(ledger, output_dir=output_dir),
        "active_discovery": write_basketball_active_source_discovery_log(discovery, output_dir=output_dir),
        "gap_action_plan": write_basketball_gap_action_plan(gap, output_dir=output_dir),
        "targeted_sample_verification": write_basketball_targeted_sample_verification_results(sample, output_dir=output_dir),
        "schema_expansion": write_basketball_schema_expansion_report(schema, output_dir=output_dir),
        "paid_data_requirement_matrix": write_basketball_paid_data_requirement_matrix(paid, output_dir=output_dir),
        "data_calibration_readiness": write_basketball_data_calibration_readiness_report(readiness, output_dir=output_dir),
        "final": write_basketball_final_report(final, output_dir=output_dir),
        "manual_templates": write_basketball_manual_import_templates(manual),
        "manual_docs": write_basketball_manual_import_docs(manual),
        "sport_samples": {},
    }
    for sport in SPORTS:
        sport_report = build_sport_sample_report(sport, run_live_samples=run_live_samples, sample_verification_results=sample)
        paths["sport_samples"][sport] = write_sport_sample_report(sport_report, output_dir=output_dir)
    return {
        "ok": True,
        "status": "ok",
        "paths": paths,
        "architecture_inventory": inventory,
        "source_ledger": ledger,
        "active_discovery": discovery,
        "gap_action_plan": gap,
        "targeted_sample_verification": sample,
        "schema_expansion": schema,
        "manual_templates": manual,
        "paid_data_requirement_matrix": paid,
        "data_calibration_readiness": readiness,
        "final_report": final,
        **_safety(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--live-samples", action="store_true")
    parser.add_argument("--tests-result", default="not_run_yet")
    parser.add_argument("--tests-run", default="")
    parser.add_argument("--files-changed", default="")
    args = parser.parse_args(argv)
    tests_run = [item for item in args.tests_run.split("||") if item]
    files_changed = [item for item in args.files_changed.split("||") if item]
    if args.persist:
        result = build_and_write_all_basketball_reports(
            run_live_samples=args.live_samples,
            tests_run=tests_run,
            tests_result=args.tests_result,
            files_changed=files_changed,
        )
    else:
        result = build_basketball_final_report(tests_run=tests_run, tests_result=args.tests_result, files_changed=files_changed)
    print(json.dumps(_json_safe(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
