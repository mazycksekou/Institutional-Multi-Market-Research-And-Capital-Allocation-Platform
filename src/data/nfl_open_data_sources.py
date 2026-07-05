from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_OPEN_DATA_SOURCE_SCHEMA_VERSION = "nfl_open_data_sources_v1"
NFL_MODULE = "americanfootball_nfl"

REQUIRED_DATA_CATEGORIES = [
    "schedules_results",
    "play_by_play",
    "team_stats",
    "player_stats",
    "rosters",
    "weekly_rosters",
    "snap_counts",
    "participation",
    "depth_charts",
    "injuries",
    "transactions",
    "draft",
    "combine",
    "coaching",
    "officials",
    "stadiums",
    "weather",
    "betting_lines_or_market_odds",
    "advanced_efficiency",
    "pace_or_play_volume",
    "roster_continuity",
]

BLOCKED_FEATURE_FAMILIES = [
    "roster_continuity",
    "injury_lineup_profile",
    "market_price_or_odds",
    "pace_or_advanced_efficiency",
]


def _source(
    *,
    source_id: str,
    source_name: str,
    source_family: str,
    data_category: str,
    source_access_type: str,
    current_phase_allowed: bool,
    future_paid_candidate: bool = False,
    requires_budget_approval: bool = False,
    approval_status: str = "approved_open_metadata",
    enabled: bool = False,
    no_call_supported: bool = True,
    metadata_only_supported: bool = True,
    live_download_supported: bool = True,
    requires_api_key: bool = False,
    requires_auth: bool = False,
    terms_review_status: str = "reviewed_open_metadata",
    expected_formats: list[str] | None = None,
    expected_granularity: str = "unknown",
    expected_join_keys: list[str] | None = None,
    likely_supported_features: list[str] | None = None,
    blocked_features: list[str] | None = None,
    blockers: list[str] | None = None,
    safety_notes: str = "read-only open-data lane; source remains disabled until explicit local workflow run",
    release_tag: str | None = None,
    asset_name: str | None = None,
    asset_prefix: str | None = None,
    asset_regex: str | None = None,
    season_asset_template: str | None = None,
    prefer_csv_gz: bool = True,
    large_source: bool = False,
    derived_from_source_ids: list[str] | None = None,
) -> dict[str, Any]:
    if data_category not in REQUIRED_DATA_CATEGORIES:
        raise ValueError(f"unsupported NFL data category: {data_category}")
    return {
        "source_id": source_id,
        "source_name": source_name,
        "source_family": source_family,
        "module": NFL_MODULE,
        "data_category": data_category,
        "source_access_type": source_access_type,
        "current_phase_allowed": bool(current_phase_allowed),
        "future_paid_candidate": bool(future_paid_candidate),
        "requires_budget_approval": bool(requires_budget_approval),
        "approval_status": approval_status,
        "enabled": bool(enabled),
        "no_call_supported": bool(no_call_supported),
        "metadata_only_supported": bool(metadata_only_supported),
        "live_download_supported": bool(live_download_supported),
        "requires_api_key": bool(requires_api_key),
        "requires_auth": bool(requires_auth),
        "terms_review_status": terms_review_status,
        "expected_formats": list(expected_formats or ["csv", "csv.gz", "parquet", "rds", "qs"]),
        "expected_granularity": expected_granularity,
        "expected_join_keys": list(expected_join_keys or []),
        "likely_supported_features": list(likely_supported_features or []),
        "blocked_features": list(blocked_features or []),
        "blockers": list(blockers or []),
        "safety_notes": safety_notes,
        "release_tag": release_tag,
        "asset_name": asset_name,
        "asset_prefix": asset_prefix,
        "asset_regex": asset_regex,
        "season_asset_template": season_asset_template,
        "prefer_csv_gz": bool(prefer_csv_gz),
        "large_source": bool(large_source),
        "derived_from_source_ids": list(derived_from_source_ids or []),
        "raw_payload_persistence_allowed": False,
        "provider_write": False,
        "execution_allowed": False,
    }


def nfl_open_data_sources() -> list[dict[str, Any]]:
    nflverse_common = {
        "source_family": "nflverse",
        "source_access_type": "open_github_release",
        "approval_status": "approved_open_metadata",
        "current_phase_allowed": True,
        "future_paid_candidate": False,
        "requires_budget_approval": False,
        "terms_review_status": "reviewed_open_metadata",
    }
    schedules_features = [
        "schedule_results",
        "postseason_labels",
        "rest_travel",
        "team_identity",
        "stadium_weather",
    ]
    return [
        _source(
            source_id="nflverse_schedules_results",
            source_name="nflverse schedules/results",
            data_category="schedules_results",
            release_tag="schedules",
            asset_name="games.csv",
            expected_granularity="game",
            expected_join_keys=["game_id", "season", "week", "home_team", "away_team"],
            likely_supported_features=schedules_features,
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_play_by_play",
            source_name="nflverse play-by-play",
            data_category="play_by_play",
            release_tag="pbp",
            asset_prefix="play_by_play_",
            season_asset_template="play_by_play_{season}.csv.gz",
            expected_granularity="play",
            expected_join_keys=["game_id", "play_id", "season", "week", "posteam", "defteam"],
            likely_supported_features=["play_by_play_efficiency", "pace_play_volume", "scoring_profile"],
            large_source=True,
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_team_stats",
            source_name="nflverse weekly team stats",
            data_category="team_stats",
            release_tag="stats_team",
            asset_prefix="stats_team_week_",
            season_asset_template="stats_team_week_{season}.csv.gz",
            expected_granularity="team_week",
            expected_join_keys=["season", "week", "team"],
            likely_supported_features=["scoring_profile", "defensive_profile", "pace_play_volume"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_weekly_player_stats",
            source_name="nflverse weekly player stats",
            data_category="player_stats",
            release_tag="stats_player",
            asset_prefix="stats_player_week_",
            season_asset_template="stats_player_week_{season}.csv.gz",
            expected_granularity="player_week",
            expected_join_keys=["season", "week", "player_id", "recent_team"],
            likely_supported_features=["player_availability", "scoring_profile"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_rosters",
            source_name="nflverse season rosters",
            data_category="rosters",
            release_tag="rosters",
            asset_prefix="roster_",
            season_asset_template="roster_{season}.csv",
            expected_granularity="player_season_team",
            expected_join_keys=["season", "team", "player_id", "gsis_id"],
            likely_supported_features=["roster_continuity", "team_identity"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_weekly_rosters",
            source_name="nflverse weekly rosters",
            data_category="weekly_rosters",
            release_tag="weekly_rosters",
            asset_prefix="roster_weekly_",
            season_asset_template="roster_weekly_{season}.csv",
            expected_granularity="player_week_team",
            expected_join_keys=["season", "week", "team", "player_id", "gsis_id"],
            likely_supported_features=["roster_continuity", "player_availability"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_snap_counts",
            source_name="nflverse snap counts",
            data_category="snap_counts",
            release_tag="snap_counts",
            asset_prefix="snap_counts_",
            season_asset_template="snap_counts_{season}.csv.gz",
            expected_granularity="player_game_or_week",
            expected_join_keys=["season", "week", "team", "player", "game_id"],
            likely_supported_features=["player_availability", "roster_continuity"],
            prefer_csv_gz=False,
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_participation",
            source_name="nflverse play participation",
            data_category="participation",
            release_tag="pbp_participation",
            asset_prefix="pbp_participation_",
            season_asset_template="pbp_participation_{season}.csv",
            expected_granularity="play_participation",
            expected_join_keys=["season", "game_id", "play_id", "team", "player_id"],
            likely_supported_features=["player_availability", "roster_continuity", "play_by_play_efficiency"],
            large_source=True,
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_depth_charts",
            source_name="nflverse depth charts",
            data_category="depth_charts",
            release_tag="depth_charts",
            asset_prefix="depth_charts_",
            season_asset_template="depth_charts_{season}.csv",
            expected_granularity="team_week_position",
            expected_join_keys=["season", "week", "team", "depth_team", "player_id"],
            likely_supported_features=["depth_chart", "player_availability", "roster_continuity"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_injuries",
            source_name="nflverse injuries",
            data_category="injuries",
            release_tag="injuries",
            asset_prefix="injuries_",
            season_asset_template="injuries_{season}.csv",
            expected_granularity="player_week_injury",
            expected_join_keys=["season", "week", "team", "player_id", "gsis_id"],
            likely_supported_features=["injury_lineup", "player_availability"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_transactions",
            source_name="nflverse trades",
            data_category="transactions",
            release_tag="trades",
            asset_name="trades.csv",
            expected_granularity="trade_transaction",
            expected_join_keys=["season", "team", "player_id"],
            likely_supported_features=["transactions", "roster_continuity"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_draft",
            source_name="nflverse draft picks",
            data_category="draft",
            release_tag="draft_picks",
            asset_name="draft_picks.csv",
            expected_granularity="player_draft_pick",
            expected_join_keys=["season", "team", "player_id", "pfr_id"],
            likely_supported_features=["draft_capital", "team_identity"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_combine",
            source_name="nflverse combine",
            data_category="combine",
            release_tag="combine",
            asset_name="combine.csv",
            expected_granularity="player_combine_result",
            expected_join_keys=["season", "player_name", "pfr_id"],
            likely_supported_features=["combine_athletic_profile", "draft_capital"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_players",
            source_name="nflverse players",
            data_category="player_stats",
            release_tag="players",
            asset_name="players.csv",
            expected_granularity="player_identity",
            expected_join_keys=["player_id", "gsis_id", "pfr_id", "espn_id"],
            likely_supported_features=["team_identity", "roster_continuity"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_teams",
            source_name="nflverse teams",
            data_category="team_stats",
            release_tag="teams",
            asset_name="teams_colors_logos.csv",
            expected_granularity="team_identity",
            expected_join_keys=["team_abbr", "team_id", "team_name"],
            likely_supported_features=["team_identity"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_officials",
            source_name="nflverse officials",
            data_category="officials",
            release_tag="officials",
            asset_name="officials.csv",
            expected_granularity="game_official",
            expected_join_keys=["game_id", "official_id", "official_name"],
            likely_supported_features=["officials"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_stadiums",
            source_name="nflverse stadium fields from schedules",
            data_category="stadiums",
            release_tag="schedules",
            asset_name="games.csv",
            expected_granularity="game_stadium",
            expected_join_keys=["game_id", "season", "stadium", "home_team"],
            likely_supported_features=["stadium_weather", "team_identity"],
            derived_from_source_ids=["nflverse_schedules_results"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_weather",
            source_name="nflverse weather fields from schedules",
            data_category="weather",
            release_tag="schedules",
            asset_name="games.csv",
            expected_granularity="game_weather",
            expected_join_keys=["game_id", "season", "home_team", "away_team"],
            likely_supported_features=["stadium_weather", "rest_travel"],
            derived_from_source_ids=["nflverse_schedules_results"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_betting_lines_or_market_odds",
            source_name="nflverse historical betting-line fields from schedules",
            data_category="betting_lines_or_market_odds",
            release_tag="schedules",
            asset_name="games.csv",
            expected_granularity="game_market_line",
            expected_join_keys=["game_id", "season", "home_team", "away_team"],
            likely_supported_features=["market_odds"],
            blocked_features=["prediction_market_outcome_persistence", "live_execution"],
            safety_notes="read-only historical line fields only; no sportsbook or prediction-market writes",
            derived_from_source_ids=["nflverse_schedules_results"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_pace_or_play_volume",
            source_name="nflverse play volume from play-by-play",
            data_category="pace_or_play_volume",
            release_tag="pbp",
            asset_prefix="play_by_play_",
            season_asset_template="play_by_play_{season}.csv.gz",
            expected_granularity="game_or_team_play_volume",
            expected_join_keys=["season", "game_id", "posteam", "defteam"],
            likely_supported_features=["pace_play_volume", "play_by_play_efficiency"],
            large_source=True,
            derived_from_source_ids=["nflverse_play_by_play"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_roster_continuity",
            source_name="nflverse roster-continuity source bundle",
            data_category="roster_continuity",
            release_tag="weekly_rosters",
            asset_prefix="roster_weekly_",
            season_asset_template="roster_weekly_{season}.csv",
            expected_granularity="team_week_roster_continuity_input",
            expected_join_keys=["season", "week", "team", "player_id", "gsis_id"],
            likely_supported_features=["roster_continuity"],
            derived_from_source_ids=["nflverse_rosters", "nflverse_weekly_rosters", "nflverse_snap_counts"],
            **nflverse_common,
        ),
        _source(
            source_id="nflverse_nextgen_stats",
            source_name="nflverse next-gen stats",
            data_category="advanced_efficiency",
            release_tag="nextgen_stats",
            asset_prefix="ngs_",
            asset_regex=r"^ngs_\d{4}_(passing|receiving|rushing)\.csv\.gz$",
            expected_granularity="player_season_nextgen_stat",
            expected_join_keys=["season", "player_id", "player_gsis_id", "team_abbr"],
            likely_supported_features=["advanced_efficiency", "combine_athletic_profile"],
            current_phase_allowed=True,
            source_family="nflverse",
            source_access_type="open_github_release",
            approval_status="approved_open_metadata",
            future_paid_candidate=False,
            requires_budget_approval=False,
            terms_review_status="reviewed_open_metadata",
            large_source=True,
        ),
        _source(
            source_id="nflverse_coaching_research",
            source_name="NFL coaching open-data research lane",
            source_family="research",
            data_category="coaching",
            source_access_type="research_required",
            current_phase_allowed=False,
            approval_status="research_required",
            live_download_supported=False,
            terms_review_status="research_required",
            expected_formats=[],
            expected_granularity="coach_team_season",
            expected_join_keys=["season", "team", "coach_id"],
            likely_supported_features=["coaching_staff"],
            blockers=["open_structured_no_auth_source_not_confirmed"],
            safety_notes="blocked until an approved open no-auth coaching source is verified",
        ),
        _source(
            source_id="nflverse_pfr_advstats_blocked",
            source_name="nflverse PFR advanced stats terms-review lane",
            source_family="nflverse",
            data_category="advanced_efficiency",
            source_access_type="open_release_terms_review_required",
            current_phase_allowed=False,
            approval_status="terms_review_required",
            release_tag="pfr_advstats",
            live_download_supported=False,
            terms_review_status="sports_reference_derivative_terms_review_required",
            expected_granularity="player_advanced_stat",
            expected_join_keys=["season", "week", "player", "player_id"],
            likely_supported_features=["advanced_efficiency"],
            blocked_features=["pace_or_advanced_efficiency"],
            blockers=["sports_reference_derivative_terms_review_required"],
            safety_notes="metadata may be inspected, but no download/backfill occurs in this phase",
        ),
        _source(
            source_id="nflverse_ftn_charting_blocked",
            source_name="nflverse FTN charting terms-review lane",
            source_family="nflverse",
            data_category="advanced_efficiency",
            source_access_type="open_release_terms_review_required",
            current_phase_allowed=False,
            approval_status="terms_review_required",
            release_tag="ftn_charting",
            live_download_supported=False,
            terms_review_status="third_party_terms_review_required",
            expected_granularity="play_charting",
            expected_join_keys=["season", "game_id", "play_id"],
            likely_supported_features=["advanced_efficiency"],
            blocked_features=["pace_or_advanced_efficiency"],
            blockers=["third_party_terms_review_required"],
            safety_notes="metadata may be inspected, but no download/backfill occurs in this phase",
        ),
    ]


def source_by_id(source_id: str) -> dict[str, Any] | None:
    for source in nfl_open_data_sources():
        if source["source_id"] == source_id:
            return source
    return None


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "sources"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build_nfl_open_data_source_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    sources = nfl_open_data_sources()
    categories_present = sorted({str(source["data_category"]) for source in sources})
    missing_categories = [category for category in REQUIRED_DATA_CATEGORIES if category not in categories_present]
    enabled_count = sum(1 for source in sources if source.get("enabled"))
    paid_enabled = sum(
        1
        for source in sources
        if source.get("enabled") and (source.get("future_paid_candidate") or source.get("requires_budget_approval"))
    )
    approval_counts = Counter(str(source.get("approval_status") or "unknown") for source in sources)
    terms_review = [
        source["source_id"]
        for source in sources
        if str(source.get("terms_review_status") or "").endswith("required")
        or source.get("approval_status") == "terms_review_required"
    ]
    api_key_sources = [source["source_id"] for source in sources if source.get("requires_api_key")]
    budget_sources = [source["source_id"] for source in sources if source.get("requires_budget_approval")]
    approved = [
        source["source_id"]
        for source in sources
        if source.get("current_phase_allowed")
        and not source.get("requires_auth")
        and not source.get("requires_api_key")
        and not source.get("future_paid_candidate")
        and not source.get("requires_budget_approval")
    ]
    ok = enabled_count == 0 and paid_enabled == 0 and not missing_categories
    return {
        **SAFETY_FIELDS,
        "ok": ok,
        "status": "ok" if ok else "blocked",
        "schema_version": NFL_OPEN_DATA_SOURCE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_sources_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "sources_registered": len(sources),
        "required_categories": REQUIRED_DATA_CATEGORIES,
        "categories_present": categories_present,
        "missing_required_categories": missing_categories,
        "enabled_source_count": enabled_count,
        "paid_source_enabled_count": paid_enabled,
        "approval_status_counts": dict(sorted(approval_counts.items())),
        "approved_free_open_sources": approved,
        "research_or_blocked_sources": [
            source["source_id"]
            for source in sources
            if not source.get("current_phase_allowed") or source.get("blockers")
        ],
        "terms_review_required_sources": terms_review,
        "api_key_required_sources": api_key_sources,
        "budget_approval_required_sources": budget_sources,
        "blocked_feature_families_tracked": BLOCKED_FEATURE_FAMILIES,
        "sources": sources,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
        "recommended_next_action": "run metadata checks, then explicit AllowDownload tiny samples for approved nflverse lanes",
    }


def render_nfl_open_data_source_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Open Data Sources",
        "",
        f"1. sources_registered: {report.get('sources_registered')}",
        f"2. categories_present: {', '.join(report.get('categories_present') or [])}",
        f"3. missing_required_categories: {', '.join(report.get('missing_required_categories') or []) if report.get('missing_required_categories') else 'none'}",
        f"4. enabled_source_count: {report.get('enabled_source_count')}",
        f"5. paid_source_enabled_count: {report.get('paid_source_enabled_count')}",
        f"6. approved_free_open_sources: {', '.join(report.get('approved_free_open_sources') or [])}",
        f"7. research_or_blocked_sources: {', '.join(report.get('research_or_blocked_sources') or []) if report.get('research_or_blocked_sources') else 'none'}",
        f"8. terms_review_required_sources: {', '.join(report.get('terms_review_required_sources') or []) if report.get('terms_review_required_sources') else 'none'}",
        "9. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Source Lanes",
    ]
    for source in report.get("sources") or []:
        blockers = ", ".join(source.get("blockers") or []) or "none"
        lines.append(
            f"- {source.get('source_id')}: category={source.get('data_category')}; allowed={str(source.get('current_phase_allowed')).lower()}; enabled=false; access={source.get('source_access_type')}; blockers={blockers}"
        )
    return "\n".join(lines) + "\n"


def write_nfl_open_data_source_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_sources_{created}_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
        "daily_json_path": _rel(daily_json, base_data_dir),
        "daily_markdown_path": _rel(daily_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, render_nfl_open_data_source_markdown(payload))
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, render_nfl_open_data_source_markdown(payload))
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, render_nfl_open_data_source_markdown(payload))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_open_data_source_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_open_data_source_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "run_id": report.get("run_id"),
                "sources_registered": report.get("sources_registered"),
                "categories_present": report.get("categories_present"),
                "missing_required_categories": report.get("missing_required_categories"),
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "latest_json_path": paths.get("latest_json_path"),
                "latest_markdown_path": paths.get("latest_markdown_path"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
