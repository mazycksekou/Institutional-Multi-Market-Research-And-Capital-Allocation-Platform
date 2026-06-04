from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .mlb_open_data_common import MLB_MODULE, mlb_atomic_write_json, mlb_atomic_write_text, mlb_rel, mlb_report_root, mlb_root, mlb_safe_payload
from .mlb_open_data_sources import source_by_id
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso
from .mlb_structured_seed_sources import mlb_structured_seed_sources


MLB_FEATURE_BUILDERS_SCHEMA_VERSION = "mlb_open_data_feature_builders_v1"

LEAKAGE_LOW = "low"
LEAKAGE_IN_SEASON_CUTOFF = "in_season_cutoff_required"
LEAKAGE_AVAILABILITY_CUTOFF = "availability_in_season_cutoff_required"
LEAKAGE_MARKET_CUTOFF = "market_timing_cutoff_required"


def _builder(
    *,
    name: str,
    feature_group: str,
    source_id: str,
    required_fields: list[str],
    optional_fields: list[str] | None = None,
    granularity: str,
    cutoff_required: bool,
    leakage_risk: str,
    allowed_for_regular_season_snapshot: bool,
    description: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "feature_group": feature_group,
        "source_id": source_id,
        "required_fields": list(required_fields),
        "optional_fields": list(optional_fields or []),
        "granularity": granularity,
        "cutoff_required": bool(cutoff_required),
        "leakage_risk": leakage_risk,
        "allowed_for_regular_season_snapshot": bool(allowed_for_regular_season_snapshot),
        "allowed_for_postseason_target": False,
        "description": description,
    }


FEATURE_BUILDER_SPECS: list[dict[str, Any]] = [
    _builder(
        name="team_game_run_profile",
        feature_group="team_game_run_profile",
        source_id="team_stats_lahman",
        required_fields=["yearID", "teamID", "R", "RA"],
        optional_fields=["W", "L", "HR", "BB", "SO"],
        granularity="team_season",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="runs_for, runs_against, run_differential, win_rate, home_away_run_balance proxy",
    ),
    _builder(
        name="batting_profile",
        feature_group="batting_profile",
        source_id="batting_stats_lahman",
        required_fields=["playerID", "yearID", "AB", "H", "HR", "BB", "SO"],
        optional_fields=["RBI", "SB", "CS", "TB"],
        granularity="player_season_stint",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="batting average, on-base proxy, slugging proxy, power/discipline profile",
    ),
    _builder(
        name="pitching_profile",
        feature_group="pitching_profile",
        source_id="pitching_stats_lahman",
        required_fields=["playerID", "yearID", "ERA", "G", "GS", "IPouts"],
        optional_fields=["SO", "BB", "HR", "W", "L", "SHO"],
        granularity="player_season_stint",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="era, workload, starter/reliever split, strikeout and walk profile",
    ),
    _builder(
        name="fielding_profile",
        feature_group="fielding_profile",
        source_id="fielding_stats_lahman",
        required_fields=["playerID", "yearID", "teamID", "pos", "PO", "A", "E"],
        optional_fields=["GS", "InnOuts", "DP"],
        granularity="player_season_position",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="fielding opportunities, errors, assists, position split",
    ),
    _builder(
        name="bullpen_usage",
        feature_group="bullpen_usage",
        source_id="bullpen_usage_mlb_stats_api",
        required_fields=["game_pk", "team_id", "player_id", "pitch_count", "innings_pitched"],
        optional_fields=["relief_flag", "save_opportunity"],
        granularity="game_team_player_relief",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="relief workload, leverage proxy, bullpen fatigue proxy",
    ),
    _builder(
        name="starting_pitcher_profile",
        feature_group="starting_pitcher_profile",
        source_id="starting_pitchers_mlb_stats_api",
        required_fields=["game_pk", "team_id", "player_id", "start_flag", "innings_pitched"],
        optional_fields=["pitch_count", "probable", "hand"],
        granularity="game_team_starting_pitcher",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="starter identification, expected workload, opening pitcher availability proxy",
    ),
    _builder(
        name="roster_continuity",
        feature_group="roster_continuity",
        source_id="rosters_mlb_stats_api",
        required_fields=["team_id", "player_id", "season", "status"],
        optional_fields=["position", "jersey_number", "bat_side", "pitch_hand"],
        granularity="player_team_roster",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="returning_players, roster churn, active roster stability proxy",
    ),
    _builder(
        name="lineup_stability",
        feature_group="lineup_stability",
        source_id="lineups_mlb_stats_api",
        required_fields=["game_pk", "team_id", "player_id", "batting_order"],
        optional_fields=["position", "status"],
        granularity="game_lineup",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="batting order stability, lineup confirmation proxy, late swap risk",
    ),
    _builder(
        name="player_availability",
        feature_group="player_availability",
        source_id="injuries_mlb_stats_api",
        required_fields=["player_id", "team_id", "report_date", "status"],
        optional_fields=["injury_note", "expected_return"],
        granularity="player_team_day",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="injury availability, absence risk, day-of-game status",
    ),
    _builder(
        name="park_factor",
        feature_group="park_factor",
        source_id="park_factors_lahman",
        required_fields=["park_id", "yearID", "runs_factor"],
        optional_fields=["hr_factor", "latitude", "longitude"],
        granularity="park_season",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="park run environment, home run environment, venue adjustment",
    ),
    _builder(
        name="stadium_weather",
        feature_group="stadium_weather",
        source_id="weather_mlb_stats_api",
        required_fields=["game_pk", "game_date", "temperature", "wind_speed"],
        optional_fields=["humidity", "precipitation", "wind_direction"],
        granularity="game_weather",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="temperature, wind, precipitation, weather-driven run environment proxy",
    ),
    _builder(
        name="postseason_context",
        feature_group="postseason_context",
        source_id="postseason_labels_retrosheet",
        required_fields=["game_id", "season", "game_type"],
        optional_fields=["playoff_round", "series_label", "postseason_flag"],
        granularity="game_postseason_label",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="postseason labeling, series round, playoff context",
    ),
    _builder(
        name="manager_continuity_candidates",
        feature_group="manager_continuity",
        source_id="managers_coaches_mlb_stats_api",
        required_fields=["team_id", "season", "manager_name"],
        optional_fields=["role", "start_date", "end_date"],
        granularity="team_season_staff",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="manager continuity, staff turnover, role continuity proxy",
    ),
    _builder(
        name="team_identity",
        feature_group="team_identity",
        source_id="franchises_lahman",
        required_fields=["franchID", "team_name"],
        optional_fields=["active", "first_year", "last_year", "city", "nickname"],
        granularity="franchise_identity",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="franchise identity, team naming, historical continuity",
    ),
    _builder(
        name="people_identifier_crosswalk",
        feature_group="people_identifier_crosswalk",
        source_id="people_identifiers_chadwick",
        required_fields=["key_mlbam", "key_retro", "key_bbref"],
        optional_fields=["key_fangraphs", "name_first", "name_last"],
        granularity="person_identifier",
        cutoff_required=False,
        leakage_risk=LEAKAGE_LOW,
        allowed_for_regular_season_snapshot=True,
        description="player identity crosswalk for roster, stats, and historical joins",
    ),
    _builder(
        name="pitch_quality_candidates",
        feature_group="pitch_quality_candidates",
        source_id="pitch_by_pitch_research_lane",
        required_fields=["game_pk", "pitch_number", "pitcher", "batter"],
        optional_fields=["pitch_type", "release_speed", "plate_x", "plate_z"],
        granularity="pitch",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=False,
        description="blocked research lane; not enabled until a safe non-scraping feed is verified",
    ),
    _builder(
        name="batted_ball_quality_candidates",
        feature_group="batted_ball_quality_candidates",
        source_id="statcast_batted_ball_research_lane",
        required_fields=["game_pk", "pitch_number", "batter"],
        optional_fields=["launch_speed", "launch_angle", "hit_distance_sc", "bb_type"],
        granularity="batted_ball",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=False,
        description="blocked research lane; no scraping or raw payload persistence",
    ),
    _builder(
        name="market_odds_candidates",
        feature_group="market_odds",
        source_id="market_odds_blocked",
        required_fields=["game_id", "date", "moneyline", "spread_line", "total_line"],
        optional_fields=["closing_line"],
        granularity="game_market_line",
        cutoff_required=True,
        leakage_risk=LEAKAGE_MARKET_CUTOFF,
        allowed_for_regular_season_snapshot=False,
        description="blocked no-spend market lane; kept for classification only",
    ),
]


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _validated_latest(source_id: str, base: Path) -> dict[str, Any]:
    path = base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _lane_fields_and_seasons(source_id: str, base: Path) -> tuple[set[str], list[str], int]:
    latest = _validated_latest(source_id, base)
    fields = {str(field) for field in latest.get("fields_available") or []}
    seasons = [str(season) for season in latest.get("seasons_backfilled") or latest.get("seasons_available") or []]
    records = int(latest.get("records_validated", 0) or 0)
    return fields, sorted(seasons), records


def evaluate_feature_builder(spec: dict[str, Any], *, base: Path) -> dict[str, Any]:
    fields, seasons, records = _lane_fields_and_seasons(spec["source_id"], base)
    required = list(spec["required_fields"])
    optional = list(spec["optional_fields"])
    missing_required = [field for field in required if field not in fields]
    present_optional = [field for field in optional if field in fields]
    source_fields_used = [field for field in required if field in fields] + present_optional
    source_info = source_by_id(spec["source_id"])
    if source_info is not None:
        current_phase_allowed = bool(source_info.get("current_phase_allowed"))
        blocker = (source_info.get("blockers") or [None])[0]
    else:
        current_phase_allowed = True
        blocker = None
    if records <= 0:
        status = "blocked"
        blocked_reason = "no_validated_records_for_source"
    elif not current_phase_allowed:
        status = "blocked"
        blocked_reason = blocker or "source_not_current_phase_allowed"
    elif missing_required:
        status = "blocked"
        blocked_reason = "missing_required_source_fields"
    else:
        status = "available"
        blocked_reason = None
    return {
        "feature_name": spec["name"],
        "feature_group": spec["feature_group"],
        "status": status,
        "blocked_reason": blocked_reason,
        "provenance": {
            "source_id": spec["source_id"],
            "source_fields_used": source_fields_used,
            "required_fields": required,
            "missing_required_fields": missing_required,
            "optional_fields_present": present_optional,
            "seasons_supported": seasons,
            "granularity": spec["granularity"],
            "cutoff_required": spec["cutoff_required"],
            "leakage_risk": spec["leakage_risk"],
        },
        "cutoff_required": spec["cutoff_required"],
        "leakage_risk": spec["leakage_risk"],
        "allowed_for_regular_season_snapshot": spec["allowed_for_regular_season_snapshot"],
        "allowed_for_postseason_target": spec["allowed_for_postseason_target"],
        "uses_future_data": False,
        "uses_postseason_target_label_as_feature": False,
        "no_fabricated_values": True,
        "description": spec["description"],
    }


def build_mlb_feature_builders(*, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    base = resolve_base_data_dir(base_data_dir)
    return [evaluate_feature_builder(spec, base=base) for spec in FEATURE_BUILDER_SPECS]


def _availability_flags(builders: list[dict[str, Any]]) -> dict[str, bool]:
    available_groups = {row["feature_group"] for row in builders if row["status"] == "available"}
    return {
        "mlb_team_game_run_profile_available": "team_game_run_profile" in available_groups,
        "mlb_batting_profile_available": "batting_profile" in available_groups,
        "mlb_pitching_profile_available": "pitching_profile" in available_groups,
        "mlb_fielding_profile_available": "fielding_profile" in available_groups,
        "mlb_bullpen_usage_available": "bullpen_usage" in available_groups,
        "mlb_starting_pitcher_profile_available": "starting_pitcher_profile" in available_groups,
        "mlb_roster_continuity_available": "roster_continuity" in available_groups,
        "mlb_lineup_stability_available": "lineup_stability" in available_groups,
        "mlb_player_availability_available": "player_availability" in available_groups,
        "mlb_park_factor_available": "park_factor" in available_groups,
        "mlb_stadium_weather_available": "stadium_weather" in available_groups,
        "mlb_postseason_context_available": "postseason_context" in available_groups,
        "mlb_manager_continuity_available": "manager_continuity" in available_groups,
        "mlb_team_identity_available": "team_identity" in available_groups,
        "mlb_people_identifier_crosswalk_available": "people_identifier_crosswalk" in available_groups,
        "mlb_pitch_quality_candidates_available": "pitch_quality_candidates" in available_groups,
        "mlb_batted_ball_quality_candidates_available": "batted_ball_quality_candidates" in available_groups,
        "mlb_market_odds_available": "market_odds" in available_groups,
    }


def build_mlb_feature_availability_flags(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_mlb_feature_builder_report(base_data_dir=base_data_dir)
    flags = dict(report["feature_availability"])
    flags["mlb_feature_builder_count"] = report["feature_builder_count"]
    flags["mlb_feature_builder_blockers"] = [row["blocked_reason"] for row in report["feature_builders_blocked"]]
    flags["mlb_cutoff_sensitive_feature_count"] = report["cutoff_sensitive_feature_count"]
    flags["mlb_leakage_sensitive_feature_count"] = report["leakage_sensitive_feature_count"]
    return flags


def _market_odds_available(base: Path) -> bool:
    for source_id in ("market_odds_blocked",):
        fields, _seasons, records = _lane_fields_and_seasons(source_id, base)
        if records > 0 and ({"spread_line", "total_line", "moneyline"} & fields):
            return True
    return False


def build_mlb_feature_builder_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    builders = build_mlb_feature_builders(base_data_dir=base)
    available = [row for row in builders if row["status"] == "available"]
    blocked = [row for row in builders if row["status"] != "available"]
    flags = _availability_flags(builders)
    flags["mlb_market_odds_available"] = _market_odds_available(base)
    cutoff_sensitive = [row["feature_name"] for row in available if row["cutoff_required"]]
    leakage_sensitive = [row["feature_name"] for row in available if row["leakage_risk"] != LEAKAGE_LOW]
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_FEATURE_BUILDERS_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"mlb_open_data_feature_builders_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
            "module": MLB_MODULE,
            "runtime_data_dir": str(base),
            "feature_builders": builders,
            "feature_builders_added": [row["feature_name"] for row in available],
            "feature_builders_blocked": [
                {
                    "feature_name": row["feature_name"],
                    "blocked_reason": row["blocked_reason"],
                    "source_id": row["provenance"]["source_id"],
                }
                for row in blocked
            ],
            "feature_builder_count": len(available),
            "feature_builder_blocked_count": len(blocked),
            "cutoff_sensitive_features": sorted(cutoff_sensitive),
            "cutoff_sensitive_feature_count": len(cutoff_sensitive),
            "leakage_sensitive_features": sorted(leakage_sensitive),
            "leakage_sensitive_feature_count": len(leakage_sensitive),
            "feature_availability": flags,
            "no_predictive_claim": True,
            "no_fabricated_values": True,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "storage_health": get_storage_health(),
        }
    )


def build_expanded_feature_readiness(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_mlb_feature_builder_report(base_data_dir=base_data_dir)
    builders = report["feature_builders"]
    available_groups = sorted({row["feature_group"] for row in builders if row["status"] == "available"})
    blocked_groups = sorted({row["feature_group"] for row in builders if row["status"] != "available"})
    structured_seed_available = any(
        source.get("current_phase_allowed") for source in mlb_structured_seed_sources() if source.get("structured_seed_supported")
    )
    return {
        "expanded_feature_catalog_available": bool(available_groups),
        "source_supported_feature_builder_count": report["feature_builder_count"],
        "feature_builder_blocked_count": report["feature_builder_blocked_count"],
        "expanded_feature_families_available": available_groups,
        "expanded_feature_families_blocked": blocked_groups,
        "structured_seed_available": structured_seed_available,
        "feature_availability": report["feature_availability"],
        "no_predictive_claim": True,
        "no_fabricated_values": True,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "mlb_open_data" / "feature_builders"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Open Data Feature Builders",
        "",
        f"1. feature_builder_count: {report.get('feature_builder_count')}",
        f"2. feature_builder_blocked_count: {report.get('feature_builder_blocked_count')}",
        f"3. cutoff_sensitive_feature_count: {report.get('cutoff_sensitive_feature_count')}",
        f"4. leakage_sensitive_feature_count: {report.get('leakage_sensitive_feature_count')}",
        f"5. feature_builders_added: {', '.join(report.get('feature_builders_added') or []) if report.get('feature_builders_added') else 'none'}",
        f"6. feature_builders_blocked: {len(report.get('feature_builders_blocked') or [])}",
        f"7. feature_availability: {json.dumps(report.get('feature_availability') or {}, sort_keys=True)}",
        "8. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Builders",
    ]
    for row in report.get("feature_builders") or []:
        lines.append(
            f"- {row.get('feature_name')}: status={row.get('status')}; group={row.get('feature_group')}; source={row.get('provenance', {}).get('source_id')}; leakage={row.get('leakage_risk')}"
        )
    return "\n".join(lines) + "\n"


def write_mlb_feature_builder_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_open_data_feature_builders_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "latest_json_path": mlb_rel(latest_json, base_data_dir),
        "latest_markdown_path": mlb_rel(latest_md, base_data_dir),
        "item_json_path": mlb_rel(item_json, base_data_dir),
        "item_markdown_path": mlb_rel(item_md, base_data_dir),
    }
    payload = mlb_safe_payload({**report, **paths})
    mlb_atomic_write_json(latest_json, payload)
    mlb_atomic_write_text(latest_md, _render_markdown(payload))
    mlb_atomic_write_json(item_json, payload)
    mlb_atomic_write_text(item_md, _render_markdown(payload))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_mlb_feature_builder_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_mlb_feature_builder_report(report)
        report.update(paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
