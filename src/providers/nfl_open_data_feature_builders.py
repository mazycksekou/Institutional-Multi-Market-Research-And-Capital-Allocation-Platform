"""Source-supported NFL open-data feature builders (availability + provenance only).

This module inspects the already fully backfilled, compact normalized NFL
open-data outputs and reports which source-supported feature builders can be
constructed. It does NOT fabricate values, make predictive claims, or create
betting/trading outputs. Every feature carries provenance (source_id,
source_fields_used, seasons_supported, granularity, cutoff_required,
leakage_risk). Builders return a blocked feature with a reason when required
source fields are missing.

No provider calls and no downloads occur here; only local compact outputs are
read.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from src.data.open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_FEATURE_BUILDERS_SCHEMA_VERSION = "nfl_open_data_feature_builders_v1"
NFL_MODULE = "americanfootball_nfl"

# Leakage / cutoff classification vocabulary used across feature builders.
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


# Feature builder specifications grouped by feature family (Phase 3 A-G).
# Each spec is matched against the verified fields present in the lane's
# compact validated output. No values are computed; only buildability and
# provenance are reported.
FEATURE_BUILDER_SPECS: list[dict[str, Any]] = [
    # A. team_game_play_volume
    _builder(
        name="team_game_play_volume",
        feature_group="team_game_play_volume",
        source_id="nflverse_pace_or_play_volume",
        required_fields=["game_id", "play_id", "posteam", "defteam"],
        optional_fields=["play_type", "down", "drive", "qtr", "half_seconds_remaining"],
        granularity="team_game_from_play_by_play",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="plays, offensive_plays, defensive_plays, total_plays, situation counts",
    ),
    # B. team_game_efficiency_candidates
    _builder(
        name="team_game_efficiency_candidates",
        feature_group="team_game_efficiency_candidates",
        source_id="nflverse_play_by_play",
        required_fields=["play_id", "posteam", "yards_gained"],
        optional_fields=[
            "epa",
            "success",
            "interception",
            "fumble_lost",
            "third_down_converted",
            "third_down_failed",
            "fourth_down_converted",
            "fourth_down_failed",
            "yardline_100",
            "touchdown",
        ],
        granularity="team_game_from_play_by_play",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="yards_per_play, turnovers, turnover_margin, third_down_proxy, red_zone_proxy, explosive_play_count, EPA-like (only if epa present)",
    ),
    # C. player_usage (snap counts)
    _builder(
        name="player_usage_snaps",
        feature_group="player_usage",
        source_id="nflverse_snap_counts",
        required_fields=["season", "week", "team", "player", "offense_snaps"],
        optional_fields=["offense_pct", "defense_snaps", "defense_pct", "st_snaps", "st_pct", "position"],
        granularity="player_game_or_week",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="snap_count, snap_pct (offense/defense/special teams), usage share proxy",
    ),
    # C. player_usage (participation)
    _builder(
        name="player_usage_participation",
        feature_group="player_usage",
        source_id="nflverse_participation",
        required_fields=["nflverse_game_id", "play_id", "offense_players"],
        optional_fields=["offense_personnel", "defense_personnel", "players_on_play", "n_offense", "n_defense"],
        granularity="play_participation",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="participation_count, personnel grouping availability proxy",
    ),
    # D. roster_continuity
    _builder(
        name="roster_continuity",
        feature_group="roster_continuity",
        source_id="nflverse_weekly_rosters",
        required_fields=["season", "team", "gsis_id"],
        optional_fields=["week", "position", "status", "depth_chart_position"],
        granularity="player_week_team",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="returning_players, returning_player_rate, position_group_returning_rate, roster_churn_rate",
    ),
    # E. injury_availability
    _builder(
        name="injury_availability",
        feature_group="injury_availability",
        source_id="nflverse_injuries",
        required_fields=["season", "week", "team", "report_status"],
        optional_fields=["practice_status", "gsis_id", "position", "report_primary_injury"],
        granularity="player_week_injury",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=False,
        description="players_listed, questionable_count, doubtful_count, out_count, practice_limited_count, availability_risk_proxy",
    ),
    # F. depth_chart_stability
    _builder(
        name="depth_chart_stability",
        feature_group="depth_chart_stability",
        source_id="nflverse_depth_charts",
        required_fields=["season", "week", "team", "pos_rank"],
        optional_fields=["depth_team", "depth_position", "pos_grp", "gsis_id", "position"],
        granularity="team_week_position",
        cutoff_required=True,
        leakage_risk=LEAKAGE_AVAILABILITY_CUTOFF,
        allowed_for_regular_season_snapshot=False,
        description="projected_starters_count, depth_chart_changes, position_group_stability_proxy",
    ),
    # G. nextgen_efficiency_candidates
    _builder(
        name="nextgen_efficiency_candidates",
        feature_group="nextgen_efficiency_candidates",
        source_id="nflverse_nextgen_stats",
        required_fields=["season", "player_gsis_id", "team_abbr"],
        optional_fields=[
            "avg_time_to_throw",
            "completion_percentage_above_expectation",
            "aggressiveness",
            "avg_air_yards_differential",
            "avg_air_yards_to_sticks",
            "passer_rating",
            "expected_completion_percentage",
        ],
        granularity="player_season_nextgen_stat",
        cutoff_required=True,
        leakage_risk=LEAKAGE_IN_SEASON_CUTOFF,
        allowed_for_regular_season_snapshot=True,
        description="source-supported nextgen efficiency fields with preserved provenance",
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
    path = base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _lane_fields_and_seasons(source_id: str, base: Path) -> tuple[set[str], list[str], int]:
    latest = _validated_latest(source_id, base)
    fields = {str(field) for field in latest.get("fields_available") or []}
    seasons = [str(season) for season in latest.get("seasons_backfilled") or latest.get("seasons_available") or []]
    records = int(latest.get("records_validated", 0) or 0)
    return fields, sorted(seasons), records


def evaluate_feature_builder(spec: dict[str, Any], *, base: Path) -> dict[str, Any]:
    """Return a provenance-rich descriptor stating whether a builder is buildable.

    No values are computed and nothing is fabricated; missing source fields yield
    a blocked feature with an explicit reason.
    """
    fields, seasons, records = _lane_fields_and_seasons(spec["source_id"], base)
    required = list(spec["required_fields"])
    optional = list(spec["optional_fields"])
    missing_required = [field for field in required if field not in fields]
    present_optional = [field for field in optional if field in fields]
    source_fields_used = [field for field in required if field in fields] + present_optional
    if records <= 0:
        status = "blocked"
        blocked_reason = "no_validated_records_for_source"
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


def build_nfl_feature_builders(*, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    base = resolve_base_data_dir(base_data_dir)
    return [evaluate_feature_builder(spec, base=base) for spec in FEATURE_BUILDER_SPECS]


def _availability_flags(builders: list[dict[str, Any]]) -> dict[str, bool]:
    available_groups = {row["feature_group"] for row in builders if row["status"] == "available"}
    return {
        "nfl_play_by_play_efficiency_available": "team_game_efficiency_candidates" in available_groups,
        "nfl_pace_play_volume_available": "team_game_play_volume" in available_groups,
        "nfl_snap_usage_available": any(
            row["feature_name"] == "player_usage_snaps" and row["status"] == "available" for row in builders
        ),
        "nfl_participation_available": any(
            row["feature_name"] == "player_usage_participation" and row["status"] == "available" for row in builders
        ),
        "nfl_depth_chart_available": "depth_chart_stability" in available_groups,
        "nfl_injury_availability_available": "injury_availability" in available_groups,
        "nfl_roster_continuity_available": "roster_continuity" in available_groups,
        "nfl_nextgen_efficiency_available": "nextgen_efficiency_candidates" in available_groups,
    }


def _market_odds_available(base: Path) -> bool:
    for source_id in ("nflverse_betting_lines_or_market_odds", "nflverse_schedules_results"):
        fields, _seasons, records = _lane_fields_and_seasons(source_id, base)
        if records > 0 and ({"spread_line", "total_line"} & fields or {"home_moneyline", "away_moneyline"} & fields):
            return True
    return False


def build_nfl_feature_builder_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    builders = build_nfl_feature_builders(base_data_dir=base)
    available = [row for row in builders if row["status"] == "available"]
    blocked = [row for row in builders if row["status"] != "available"]
    flags = _availability_flags(builders)
    flags["nfl_market_odds_available"] = _market_odds_available(base)
    cutoff_sensitive = [row["feature_name"] for row in available if row["cutoff_required"]]
    leakage_sensitive = [row["feature_name"] for row in available if row["leakage_risk"] != LEAKAGE_LOW]
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_FEATURE_BUILDERS_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_feature_builders_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "feature_builders": builders,
        "feature_builders_added": [row["feature_name"] for row in available],
        "feature_builders_blocked": [
            {"feature_name": row["feature_name"], "blocked_reason": row["blocked_reason"], "source_id": row["provenance"]["source_id"]}
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


def nfl_feature_availability_flags(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    """Compact availability flags + counts for the derived feature report (Phase 4)."""
    report = build_nfl_feature_builder_report(base_data_dir=base_data_dir)
    flags = dict(report["feature_availability"])
    flags["nfl_feature_builder_count"] = report["feature_builder_count"]
    flags["nfl_feature_builder_blockers"] = [row["blocked_reason"] for row in report["feature_builders_blocked"]]
    flags["nfl_cutoff_sensitive_feature_count"] = report["cutoff_sensitive_feature_count"]
    flags["nfl_leakage_sensitive_feature_count"] = report["leakage_sensitive_feature_count"]
    return flags


def build_expanded_feature_readiness(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    """Expanded feature readiness summary consumed by the pattern lab (Phase 5)."""
    report = build_nfl_feature_builder_report(base_data_dir=base_data_dir)
    builders = report["feature_builders"]
    available_groups = sorted({row["feature_group"] for row in builders if row["status"] == "available"})
    blocked_groups = sorted({row["feature_group"] for row in builders if row["status"] != "available"})
    regular_season_candidates = sorted(
        {row["feature_name"] for row in builders if row["status"] == "available" and row["allowed_for_regular_season_snapshot"]}
    )
    return {
        "expanded_feature_catalog_available": report["feature_builder_count"] > 0,
        "expanded_feature_families_available": available_groups,
        "expanded_feature_families_blocked": blocked_groups,
        "expanded_regular_season_features_candidate": regular_season_candidates,
        "expanded_cutoff_sensitive_features": report["cutoff_sensitive_features"],
        "expanded_leakage_sensitive_features": report["leakage_sensitive_features"],
        "source_supported_feature_count": report["feature_builder_count"],
        "source_supported_feature_builder_count": len(FEATURE_BUILDER_SPECS),
        "no_predictive_claim": True,
    }


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "feature_builders"
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


def render_nfl_feature_builder_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Open Data Feature Builders",
        "",
        f"1. feature_builder_count: {report.get('feature_builder_count')}",
        f"2. feature_builder_blocked_count: {report.get('feature_builder_blocked_count')}",
        f"3. cutoff_sensitive_feature_count: {report.get('cutoff_sensitive_feature_count')}",
        f"4. leakage_sensitive_feature_count: {report.get('leakage_sensitive_feature_count')}",
        "5. no_predictive_claim=true; no_fabricated_values=true",
        "6. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Builders",
    ]
    for row in report.get("feature_builders") or []:
        provenance = row.get("provenance") or {}
        lines.append(
            f"- {row.get('feature_name')} [{row.get('feature_group')}]: status={row.get('status')}; "
            f"source_id={provenance.get('source_id')}; cutoff_required={str(row.get('cutoff_required')).lower()}; "
            f"leakage_risk={row.get('leakage_risk')}; blocked_reason={row.get('blocked_reason')}"
        )
    return "\n".join(lines) + "\n"


def write_nfl_feature_builder_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_feature_builders_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_nfl_feature_builder_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_feature_builder_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_feature_builder_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "feature_builder_count": report.get("feature_builder_count"),
                "feature_builder_blocked_count": report.get("feature_builder_blocked_count"),
                "cutoff_sensitive_feature_count": report.get("cutoff_sensitive_feature_count"),
                "leakage_sensitive_feature_count": report.get("leakage_sensitive_feature_count"),
                "feature_availability": report.get("feature_availability"),
                "no_predictive_claim": True,
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
