"""Point-in-time NFL cutoff-week feature snapshots (no future data, no claims).

Computes feature snapshots from already-validated compact NFL open-data rows
using ONLY data available through an explicit (season, cutoff_week). No provider
calls, no downloads, no fabrication, and no predictive claims. Postseason games
are excluded by default and cutoff-sensitive feature groups
(injury/roster-continuity/depth-chart/market) are blocked unless
allow_cutoff_sensitive_fields is explicitly enabled. Every emitted value carries
provenance (source_id, source_fields_used, season, max_week_used, cutoff_week,
cutoff_passed, leakage_risk, cutoff_required).
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


NFL_CUTOFF_FEATURES_SCHEMA_VERSION = "nfl_cutoff_week_features_v1"
NFL_MODULE = "americanfootball_nfl"

POSTSEASON_GAME_TYPES = {"WC", "DIV", "CON", "SB", "POST"}

# Feature group -> source lane and cutoff posture.
# cutoff_sensitive groups reflect point-in-time availability/market state and
# are blocked unless allow_cutoff_sensitive_fields is explicitly enabled.
CUTOFF_FEATURE_GROUPS: dict[str, dict[str, Any]] = {
    "team_game_play_volume": {
        "source_id": "nflverse_pace_or_play_volume",
        "scope": "team",
        "cutoff_sensitive": False,
        "leakage_risk": "in_season_cutoff_required",
        "value_fields": ["play_id"],
        "scope_fields": ["posteam", "team"],
    },
    "team_game_efficiency_candidates": {
        "source_id": "nflverse_play_by_play",
        "scope": "team",
        "cutoff_sensitive": False,
        "leakage_risk": "in_season_cutoff_required",
        "value_fields": ["yards_gained", "epa"],
        "scope_fields": ["posteam", "team"],
    },
    "player_usage_snaps": {
        "source_id": "nflverse_snap_counts",
        "scope": "player",
        "cutoff_sensitive": False,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["offense_snaps", "defense_snaps", "st_snaps"],
        "scope_fields": ["player", "player_id"],
    },
    "player_usage_participation": {
        "source_id": "nflverse_participation",
        "scope": "game",
        "cutoff_sensitive": False,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["play_id"],
        "scope_fields": ["possession_team"],
    },
    "nextgen_efficiency_candidates": {
        "source_id": "nflverse_nextgen_stats",
        "scope": "player",
        "cutoff_sensitive": False,
        "leakage_risk": "in_season_cutoff_required",
        "value_fields": ["attempts", "completions"],
        "scope_fields": ["player_gsis_id", "player_display_name"],
    },
    "roster_continuity": {
        "source_id": "nflverse_weekly_rosters",
        "scope": "team",
        "cutoff_sensitive": True,
        "leakage_risk": "in_season_cutoff_required",
        "value_fields": ["gsis_id"],
        "scope_fields": ["team"],
    },
    "injury_availability": {
        "source_id": "nflverse_injuries",
        "scope": "team",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["report_status"],
        "scope_fields": ["team"],
    },
    "depth_chart_stability": {
        "source_id": "nflverse_depth_charts",
        "scope": "team",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["pos_rank"],
        "scope_fields": ["team", "club_code"],
    },
    "market_odds": {
        "source_id": "nflverse_betting_lines_or_market_odds",
        "scope": "game",
        "cutoff_sensitive": True,
        "leakage_risk": "market_timing_cutoff_required",
        "value_fields": ["spread_line", "total_line"],
        "scope_fields": ["home_team", "away_team"],
    },
}

DEFAULT_SOURCE_LANES = list(CUTOFF_FEATURE_GROUPS.keys())


class CutoffContextError(ValueError):
    """Raised when a cutoff context is missing required parameters."""


def cutoff_feature_availability_summary() -> dict[str, Any]:
    """Static availability summary (no data read) for readiness reports."""
    default_eligible = sorted(lane for lane, group in CUTOFF_FEATURE_GROUPS.items() if not group["cutoff_sensitive"])
    cutoff_sensitive = sorted(lane for lane, group in CUTOFF_FEATURE_GROUPS.items() if group["cutoff_sensitive"])
    return {
        "nfl_cutoff_week_features_available": True,
        "nfl_cutoff_week_feature_groups_available": default_eligible,
        "nfl_cutoff_week_cutoff_sensitive_groups": cutoff_sensitive,
        "nfl_cutoff_week_leakage_guard_status": "active_future_data_excluded",
    }


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _week(row: dict[str, Any]) -> int | None:
    return None if (value := _number(row.get("week"))) is None else int(value)


def build_cutoff_week_context(
    *,
    season: int | str | None,
    cutoff_week: int | str | None,
    team: str | None = None,
    player_id: str | None = None,
    source_lanes: list[str] | None = None,
    include_postseason: bool = False,
    allow_cutoff_sensitive_fields: bool = False,
) -> dict[str, Any]:
    if season is None or str(season).strip() == "":
        raise CutoffContextError("season is required for a cutoff-week context")
    if cutoff_week is None or str(cutoff_week).strip() == "":
        raise CutoffContextError("cutoff_week is required for a cutoff-week context")
    try:
        cutoff_week_int = int(cutoff_week)
    except (TypeError, ValueError) as exc:
        raise CutoffContextError("cutoff_week must be an integer") from exc
    lanes = list(source_lanes or DEFAULT_SOURCE_LANES)
    invalid = [lane for lane in lanes if lane not in CUTOFF_FEATURE_GROUPS]
    lanes = [lane for lane in lanes if lane in CUTOFF_FEATURE_GROUPS]
    return {
        "season": str(season),
        "cutoff_week": cutoff_week_int,
        "team": team,
        "player_id": player_id,
        "source_lanes": lanes,
        "invalid_source_lanes": invalid,
        "include_postseason": bool(include_postseason),
        "allow_cutoff_sensitive_fields": bool(allow_cutoff_sensitive_fields),
    }


def _load_lane_rows(source_id: str, season: str, base: Path) -> list[dict[str, Any]]:
    root = base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    candidates = [root / "by_season" / f"{sanitize_filename(season)}.json", root / "latest.json"]
    for path in candidates:
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        for row in payload.get("sample_rows") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("season") or "") != str(season):
                continue
            key = str(row.get("record_id") or json.dumps({k: row.get(k) for k in sorted(row)}, sort_keys=True, default=str))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def _is_postseason(row: dict[str, Any]) -> bool:
    return str(row.get("game_type") or row.get("season_type") or "").strip().upper() in POSTSEASON_GAME_TYPES


def filter_records_by_cutoff(records: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    cutoff_week = int(context["cutoff_week"])
    include_postseason = bool(context.get("include_postseason"))
    kept: list[dict[str, Any]] = []
    excluded_future = 0
    excluded_postseason = 0
    excluded_unverifiable = 0
    for row in records:
        if _is_postseason(row) and not include_postseason:
            excluded_postseason += 1
            continue
        week = _week(row)
        if week is None:
            excluded_unverifiable += 1
            continue
        if week > cutoff_week:
            excluded_future += 1
            continue
        kept.append(row)
    return {
        "kept": kept,
        "kept_count": len(kept),
        "excluded_future": excluded_future,
        "excluded_postseason": excluded_postseason,
        "excluded_cutoff_unverifiable": excluded_unverifiable,
        "max_week_used": max((_week(row) for row in kept if _week(row) is not None), default=None),
    }


def validate_no_future_data_used(records: list[dict[str, Any]], context: dict[str, Any]) -> bool:
    cutoff_week = int(context["cutoff_week"])
    include_postseason = bool(context.get("include_postseason"))
    for row in records:
        week = _week(row)
        if week is None or week > cutoff_week:
            return False
        if _is_postseason(row) and not include_postseason:
            return False
    return True


def _scope_filter(rows: list[dict[str, Any]], context: dict[str, Any], group: dict[str, Any]) -> list[dict[str, Any]]:
    team = context.get("team")
    player_id = context.get("player_id")
    scope_fields = group.get("scope_fields") or []
    out = rows
    if team:
        out = [row for row in out if any(str(row.get(field) or "") == str(team) for field in scope_fields) or str(row.get("team") or "") == str(team)]
    if player_id and group.get("scope") == "player":
        out = [row for row in out if str(row.get("player_id") or row.get("player_gsis_id") or "") == str(player_id)]
    return out


def _compute_group_values(rows: list[dict[str, Any]], group: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {"record_count": len(rows)}
    source_fields_used: list[str] = []
    for field in group.get("value_fields") or []:
        present = [row.get(field) for row in rows if field in row and row.get(field) not in (None, "")]
        if not present:
            continue
        source_fields_used.append(field)
        numeric = [n for n in (_number(v) for v in present) if n is not None]
        if numeric and len(numeric) == len(present):
            values[f"sum_{field}"] = round(sum(numeric), 4)
            values[f"count_{field}"] = len(numeric)
        else:
            values[f"count_{field}"] = len(present)
    return {"values": values, "source_fields_used": source_fields_used}


def compute_cutoff_feature_values(context: dict[str, Any], *, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    base = resolve_base_data_dir(base_data_dir)
    season = str(context["season"])
    cutoff_week = int(context["cutoff_week"])
    allow_sensitive = bool(context.get("allow_cutoff_sensitive_fields"))
    results: list[dict[str, Any]] = []
    for lane in context["source_lanes"]:
        group = CUTOFF_FEATURE_GROUPS[lane]
        source_id = group["source_id"]
        base_provenance = {
            "source_id": source_id,
            "season": season,
            "cutoff_week": cutoff_week,
            "leakage_risk": group["leakage_risk"],
            "cutoff_required": True,
        }
        if group["cutoff_sensitive"] and not allow_sensitive:
            results.append(
                {
                    "feature_group": lane,
                    "status": "blocked",
                    "blocked_reason": "cutoff_sensitive_field_requires_explicit_allow",
                    "provenance": {**base_provenance, "source_fields_used": [], "max_week_used": None, "cutoff_passed": False},
                    "values": {},
                    "no_fabricated_values": True,
                }
            )
            continue
        rows = _scope_filter(_load_lane_rows(source_id, season, base), context, group)
        cutoff = filter_records_by_cutoff(rows, context)
        kept = cutoff["kept"]
        cutoff_passed = validate_no_future_data_used(kept, context)
        if not kept:
            results.append(
                {
                    "feature_group": lane,
                    "status": "blocked",
                    "blocked_reason": "no_cutoff_eligible_records_available",
                    "provenance": {**base_provenance, "source_fields_used": [], "max_week_used": None, "cutoff_passed": cutoff_passed},
                    "values": {},
                    "cutoff_filter": {k: v for k, v in cutoff.items() if k != "kept"},
                    "no_fabricated_values": True,
                }
            )
            continue
        computed = _compute_group_values(kept, group)
        results.append(
            {
                "feature_group": lane,
                "status": "available",
                "blocked_reason": None,
                "provenance": {
                    **base_provenance,
                    "source_fields_used": computed["source_fields_used"],
                    "max_week_used": cutoff["max_week_used"],
                    "cutoff_passed": cutoff_passed,
                },
                "values": computed["values"],
                "cutoff_filter": {k: v for k, v in cutoff.items() if k != "kept"},
                "no_fabricated_values": True,
            }
        )
    return results


def build_team_cutoff_snapshot(context: dict[str, Any], *, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    team_lanes = [lane for lane in context["source_lanes"] if CUTOFF_FEATURE_GROUPS[lane]["scope"] == "team"]
    return compute_cutoff_feature_values({**context, "source_lanes": team_lanes}, base_data_dir=base_data_dir)


def build_player_cutoff_snapshot(context: dict[str, Any], *, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    player_lanes = [lane for lane in context["source_lanes"] if CUTOFF_FEATURE_GROUPS[lane]["scope"] == "player"]
    return compute_cutoff_feature_values({**context, "source_lanes": player_lanes}, base_data_dir=base_data_dir)


def build_game_cutoff_snapshot(context: dict[str, Any], *, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    game_lanes = [lane for lane in context["source_lanes"] if CUTOFF_FEATURE_GROUPS[lane]["scope"] == "game"]
    return compute_cutoff_feature_values({**context, "source_lanes": game_lanes}, base_data_dir=base_data_dir)


def build_cutoff_feature_report(
    *,
    season: int | str | None,
    cutoff_week: int | str | None,
    team: str | None = None,
    player_id: str | None = None,
    source_lanes: list[str] | None = None,
    include_postseason: bool = False,
    allow_cutoff_sensitive_fields: bool = False,
    max_records: int | None = None,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    context = build_cutoff_week_context(
        season=season,
        cutoff_week=cutoff_week,
        team=team,
        player_id=player_id,
        source_lanes=source_lanes,
        include_postseason=include_postseason,
        allow_cutoff_sensitive_fields=allow_cutoff_sensitive_fields,
    )
    features = compute_cutoff_feature_values(context, base_data_dir=base)
    available = [row for row in features if row["status"] == "available"]
    blocked = [row for row in features if row["status"] != "available"]
    leakage_guard_status = "passed" if all(row["provenance"]["cutoff_passed"] for row in available) else "blocked_future_data_detected"
    groups_available = sorted({row["feature_group"] for row in available})
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_CUTOFF_FEATURES_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_cutoff_features_{season}_w{context['cutoff_week']}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "context": context,
        "nfl_cutoff_week_features_available": bool(available),
        "nfl_cutoff_week_feature_groups_available": groups_available,
        "nfl_cutoff_week_snapshot_count": len(available),
        "nfl_cutoff_week_leakage_guard_status": leakage_guard_status,
        "features": features,
        "blocked_feature_groups": [{"feature_group": row["feature_group"], "blocked_reason": row["blocked_reason"]} for row in blocked],
        "no_future_data_used": leakage_guard_status == "passed",
        "no_target_labels_used": True,
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


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "cutoff_features"
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


def render_cutoff_feature_markdown(report: dict[str, Any]) -> str:
    context = report.get("context") or {}
    lines = [
        "# NFL Cutoff-Week Feature Snapshot",
        "",
        f"1. season: {context.get('season')}; cutoff_week: {context.get('cutoff_week')}",
        f"2. team: {context.get('team')}; player_id: {context.get('player_id')}",
        f"3. include_postseason: {str(context.get('include_postseason')).lower()}; allow_cutoff_sensitive_fields: {str(context.get('allow_cutoff_sensitive_fields')).lower()}",
        f"4. feature_groups_available: {', '.join(report.get('nfl_cutoff_week_feature_groups_available') or []) if report.get('nfl_cutoff_week_feature_groups_available') else 'none'}",
        f"5. snapshot_count: {report.get('nfl_cutoff_week_snapshot_count')}",
        f"6. leakage_guard_status: {report.get('nfl_cutoff_week_leakage_guard_status')}",
        "7. no_future_data_used; no_target_labels_used; no_predictive_claim=true; no_fabricated_values=true",
        "8. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Feature Groups",
    ]
    for row in report.get("features") or []:
        provenance = row.get("provenance") or {}
        lines.append(
            f"- {row.get('feature_group')}: status={row.get('status')}; max_week_used={provenance.get('max_week_used')}; "
            f"cutoff_passed={str(provenance.get('cutoff_passed')).lower()}; blocked_reason={row.get('blocked_reason')}"
        )
    return "\n".join(lines) + "\n"


def write_cutoff_feature_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_cutoff_features_{uuid4().hex[:8]}"))
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
    markdown = render_cutoff_feature_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True)
    parser.add_argument("--cutoff-week", required=True)
    parser.add_argument("--team", default=None)
    parser.add_argument("--player-id", default=None)
    parser.add_argument("--include-postseason", action="store_true")
    parser.add_argument("--allow-cutoff-sensitive-fields", action="store_true")
    parser.add_argument("--source-lanes", default=None, help="comma-separated feature groups")
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    lanes = [lane.strip() for lane in args.source_lanes.split(",")] if args.source_lanes else None
    report = build_cutoff_feature_report(
        season=args.season,
        cutoff_week=args.cutoff_week,
        team=args.team,
        player_id=args.player_id,
        source_lanes=lanes,
        include_postseason=args.include_postseason,
        allow_cutoff_sensitive_fields=args.allow_cutoff_sensitive_fields,
        max_records=args.max_records,
    )
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_cutoff_feature_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "season": report["context"]["season"],
                "cutoff_week": report["context"]["cutoff_week"],
                "nfl_cutoff_week_features_available": report["nfl_cutoff_week_features_available"],
                "nfl_cutoff_week_feature_groups_available": report["nfl_cutoff_week_feature_groups_available"],
                "nfl_cutoff_week_snapshot_count": report["nfl_cutoff_week_snapshot_count"],
                "nfl_cutoff_week_leakage_guard_status": report["nfl_cutoff_week_leakage_guard_status"],
                "no_future_data_used": report["no_future_data_used"],
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
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
