from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .mlb_open_data_common import MLB_MODULE, mlb_atomic_write_json, mlb_atomic_write_text, mlb_rel, mlb_root, mlb_safe_payload
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_CUTOFF_FEATURES_SCHEMA_VERSION = "mlb_cutoff_date_features_v1"

POSTSEASON_GAME_TYPES = {
    "POST",
    "WC",
    "DIV",
    "LDS",
    "LCS",
    "WS",
    "ALDS",
    "NLDS",
    "ALCS",
    "NLCS",
    "WORLD_SERIES",
}

CUTOFF_FEATURE_GROUPS: dict[str, dict[str, Any]] = {
    "team_game_run_profile": {
        "source_id": "team_stats_lahman",
        "scope": "team",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["R", "RA", "W", "L"],
        "scope_fields": ["teamID", "team_id", "team"],
    },
    "batting_profile": {
        "source_id": "batting_stats_lahman",
        "scope": "player",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["AB", "H", "HR", "BB", "SO"],
        "scope_fields": ["playerID", "player_id"],
    },
    "pitching_profile": {
        "source_id": "pitching_stats_lahman",
        "scope": "player",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["ERA", "G", "GS", "IPouts"],
        "scope_fields": ["playerID", "player_id"],
    },
    "fielding_profile": {
        "source_id": "fielding_stats_lahman",
        "scope": "player",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["PO", "A", "E", "GS"],
        "scope_fields": ["playerID", "player_id"],
    },
    "bullpen_usage": {
        "source_id": "bullpen_usage_mlb_stats_api",
        "scope": "game",
        "cutoff_sensitive": True,
        "leakage_risk": "in_season_cutoff_required",
        "value_fields": ["pitch_count", "innings_pitched"],
        "scope_fields": ["game_pk", "game_id", "team_id", "team"],
    },
    "starting_pitcher_profile": {
        "source_id": "starting_pitchers_mlb_stats_api",
        "scope": "game",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["innings_pitched", "pitch_count"],
        "scope_fields": ["game_pk", "game_id", "team_id", "team"],
    },
    "roster_continuity": {
        "source_id": "rosters_mlb_stats_api",
        "scope": "team",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["status"],
        "scope_fields": ["team_id", "team"],
    },
    "lineup_stability": {
        "source_id": "lineups_mlb_stats_api",
        "scope": "game",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["batting_order", "position"],
        "scope_fields": ["game_pk", "game_id", "team_id", "team"],
    },
    "player_availability": {
        "source_id": "injuries_mlb_stats_api",
        "scope": "team",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["status"],
        "scope_fields": ["team_id", "team", "player_id"],
    },
    "park_factor": {
        "source_id": "park_factors_lahman",
        "scope": "park",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["runs_factor", "hr_factor"],
        "scope_fields": ["park_id"],
    },
    "stadium_weather": {
        "source_id": "weather_mlb_stats_api",
        "scope": "game",
        "cutoff_sensitive": True,
        "leakage_risk": "availability_in_season_cutoff_required",
        "value_fields": ["temperature", "wind_speed"],
        "scope_fields": ["game_pk", "game_id"],
    },
    "postseason_context": {
        "source_id": "postseason_labels_retrosheet",
        "scope": "game",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["game_type", "playoff_round"],
        "scope_fields": ["game_id"],
    },
    "manager_continuity": {
        "source_id": "managers_coaches_mlb_stats_api",
        "scope": "team",
        "cutoff_sensitive": True,
        "leakage_risk": "in_season_cutoff_required",
        "value_fields": ["manager_name", "role"],
        "scope_fields": ["team_id", "team"],
    },
    "team_identity": {
        "source_id": "franchises_lahman",
        "scope": "team",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["team_name", "city", "nickname"],
        "scope_fields": ["franchID"],
    },
    "people_identifier_crosswalk": {
        "source_id": "people_identifiers_chadwick",
        "scope": "player",
        "cutoff_sensitive": False,
        "leakage_risk": "low",
        "value_fields": ["key_mlbam", "key_retro", "key_bbref"],
        "scope_fields": ["playerID", "player_id"],
    },
    "market_odds_candidates": {
        "source_id": "market_odds_blocked",
        "scope": "game",
        "cutoff_sensitive": True,
        "leakage_risk": "market_timing_cutoff_required",
        "value_fields": ["moneyline", "spread_line", "total_line"],
        "scope_fields": ["game_id"],
    },
}

DEFAULT_SOURCE_LANES = list(CUTOFF_FEATURE_GROUPS.keys())


class CutoffContextError(ValueError):
    """Raised when cutoff context is missing required parameters."""


def cutoff_feature_availability_summary() -> dict[str, Any]:
    default_eligible = sorted(lane for lane, group in CUTOFF_FEATURE_GROUPS.items() if not group["cutoff_sensitive"])
    cutoff_sensitive = sorted(lane for lane, group in CUTOFF_FEATURE_GROUPS.items() if group["cutoff_sensitive"])
    return {
        "mlb_cutoff_date_features_available": True,
        "mlb_cutoff_date_feature_groups_available": default_eligible,
        "mlb_cutoff_date_cutoff_sensitive_groups": cutoff_sensitive,
        "mlb_cutoff_date_leakage_guard_status": "active_future_data_excluded",
        "mlb_cutoff_date_postseason_default_excluded": True,
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


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date()
            except ValueError:
                continue
    return None


def _season(row: dict[str, Any]) -> str | None:
    for key in ("season", "year", "yearID", "season_year"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _event_date(row: dict[str, Any]) -> date | None:
    for key in ("event_date", "game_date", "date", "gameday", "timestamp"):
        parsed = _parse_date(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _season_int(value: int | str | None) -> int:
    if value is None or str(value).strip() == "":
        raise CutoffContextError("season is required for a cutoff-date context")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CutoffContextError("season must be an integer") from exc


def build_cutoff_date_context(
    *,
    season: int | str | None,
    cutoff_date: str | None,
    team: str | None = None,
    player_id: str | None = None,
    source_lanes: list[str] | None = None,
    include_postseason: bool = False,
    allow_cutoff_sensitive_fields: bool = False,
) -> dict[str, Any]:
    season_int = _season_int(season)
    if cutoff_date is None or str(cutoff_date).strip() == "":
        raise CutoffContextError("cutoff_date is required for a cutoff-date context")
    parsed = _parse_date(cutoff_date)
    if parsed is None:
        raise CutoffContextError("cutoff_date must be a valid ISO-like date")
    lanes = list(source_lanes or DEFAULT_SOURCE_LANES)
    invalid = [lane for lane in lanes if lane not in CUTOFF_FEATURE_GROUPS]
    lanes = [lane for lane in lanes if lane in CUTOFF_FEATURE_GROUPS]
    return {
        "season": str(season_int),
        "cutoff_date": parsed.isoformat(),
        "team": team,
        "player_id": player_id,
        "source_lanes": lanes,
        "invalid_source_lanes": invalid,
        "include_postseason": bool(include_postseason),
        "allow_cutoff_sensitive_fields": bool(allow_cutoff_sensitive_fields),
    }


def _load_lane_rows(source_id: str, season: str, base: Path) -> list[dict[str, Any]]:
    root = base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    candidates = [root / "by_season" / f"{sanitize_filename(season)}.json", root / "latest.json"]
    for path in candidates:
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        for row in payload.get("validated_rows") or payload.get("sample_rows") or []:
            if not isinstance(row, dict):
                continue
            if _season(row) not in {None, str(season)}:
                continue
            key = str(row.get("record_id") or json.dumps({k: row.get(k) for k in sorted(row)}, sort_keys=True, default=str))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def _is_postseason(row: dict[str, Any]) -> bool:
    game_type = str(row.get("game_type") or row.get("season_type") or row.get("postseason_label") or "").strip().upper()
    if not game_type:
        return False
    if game_type in POSTSEASON_GAME_TYPES:
        return True
    text = game_type.lower()
    return any(token in text for token in ("post", "playoff", "wild_card", "division", "world_series", "lcs", "lds"))


def filter_records_by_cutoff_date(records: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    cutoff = _parse_date(context["cutoff_date"])
    if cutoff is None:
        raise CutoffContextError("cutoff_date is required")
    include_postseason = bool(context.get("include_postseason"))
    kept: list[dict[str, Any]] = []
    excluded_future = 0
    excluded_postseason = 0
    excluded_unverifiable = 0
    for row in records:
        if _is_postseason(row) and not include_postseason:
            excluded_postseason += 1
            continue
        event_date = _event_date(row)
        if event_date is None:
            excluded_unverifiable += 1
            continue
        if event_date > cutoff:
            excluded_future += 1
            continue
        kept.append(row)
    return {
        "kept": kept,
        "kept_count": len(kept),
        "excluded_future": excluded_future,
        "excluded_postseason": excluded_postseason,
        "excluded_cutoff_unverifiable": excluded_unverifiable,
        "max_date_used": max((_event_date(row) for row in kept if _event_date(row) is not None), default=None).isoformat()
        if any(_event_date(row) is not None for row in kept)
        else None,
    }


def validate_no_future_data_used(records: list[dict[str, Any]], context: dict[str, Any]) -> bool:
    cutoff = _parse_date(context["cutoff_date"])
    if cutoff is None:
        return False
    include_postseason = bool(context.get("include_postseason"))
    for row in records:
        event_date = _event_date(row)
        if event_date is None or event_date > cutoff:
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
        out = [row for row in out if any(str(row.get(field) or "") == str(team) for field in scope_fields) or str(row.get("team") or row.get("team_id") or "") == str(team)]
    if player_id and group.get("scope") == "player":
        out = [row for row in out if str(row.get("player_id") or row.get("playerID") or "") == str(player_id)]
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
    allow_sensitive = bool(context.get("allow_cutoff_sensitive_fields"))
    results: list[dict[str, Any]] = []
    for lane in context["source_lanes"]:
        group = CUTOFF_FEATURE_GROUPS[lane]
        source_id = group["source_id"]
        base_provenance = {
            "source_id": source_id,
            "season": season,
            "cutoff_date": context["cutoff_date"],
            "leakage_risk": group["leakage_risk"],
            "cutoff_required": True,
        }
        if group["cutoff_sensitive"] and not allow_sensitive:
            results.append(
                {
                    "feature_group": lane,
                    "status": "blocked",
                    "blocked_reason": "cutoff_sensitive_field_requires_explicit_allow",
                    "provenance": {**base_provenance, "source_fields_used": [], "max_date_used": None, "cutoff_passed": False},
                    "values": {},
                    "no_fabricated_values": True,
                }
            )
            continue
        rows = _scope_filter(_load_lane_rows(source_id, season, base), context, group)
        cutoff = filter_records_by_cutoff_date(rows, context)
        kept = cutoff["kept"]
        cutoff_passed = validate_no_future_data_used(kept, context)
        if not kept:
            results.append(
                {
                    "feature_group": lane,
                    "status": "blocked",
                    "blocked_reason": "no_cutoff_eligible_records_available",
                    "provenance": {**base_provenance, "source_fields_used": [], "max_date_used": None, "cutoff_passed": cutoff_passed},
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
                    "max_date_used": cutoff["max_date_used"],
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
    season: int | str | None = None,
    cutoff_date: str | None = None,
    team: str | None = None,
    player_id: str | None = None,
    source_lanes: list[str] | None = None,
    include_postseason: bool = False,
    allow_cutoff_sensitive_fields: bool = False,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    context = build_cutoff_date_context(
        season=season,
        cutoff_date=cutoff_date,
        team=team,
        player_id=player_id,
        source_lanes=source_lanes,
        include_postseason=include_postseason,
        allow_cutoff_sensitive_fields=allow_cutoff_sensitive_fields,
    )
    snapshots = compute_cutoff_feature_values(context, base_data_dir=base_data_dir)
    available = [row for row in snapshots if row["status"] == "available"]
    blocked = [row for row in snapshots if row["status"] != "available"]
    team_snapshots = [row for row in snapshots if CUTOFF_FEATURE_GROUPS[row["feature_group"]]["scope"] == "team"]
    player_snapshots = [row for row in snapshots if CUTOFF_FEATURE_GROUPS[row["feature_group"]]["scope"] == "player"]
    game_snapshots = [row for row in snapshots if CUTOFF_FEATURE_GROUPS[row["feature_group"]]["scope"] == "game"]
    max_date_used = None
    for row in snapshots:
        candidate = row.get("provenance", {}).get("max_date_used")
        parsed = _parse_date(candidate)
        if parsed is None:
            continue
        if max_date_used is None or parsed > max_date_used:
            max_date_used = parsed
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_CUTOFF_FEATURES_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"mlb_cutoff_date_features_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
            "module": MLB_MODULE,
            "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
            "context": context,
            "snapshot_count": len(snapshots),
            "available_snapshot_count": len(available),
            "blocked_snapshot_count": len(blocked),
            "team_snapshot_count": len(team_snapshots),
            "player_snapshot_count": len(player_snapshots),
            "game_snapshot_count": len(game_snapshots),
            "feature_rows": snapshots,
            "feature_groups_available": [row["feature_group"] for row in available],
            "feature_groups_blocked": [row["feature_group"] for row in blocked],
            "max_date_used": max_date_used.isoformat() if max_date_used else None,
            "include_postseason": bool(include_postseason),
            "allow_cutoff_sensitive_fields": bool(allow_cutoff_sensitive_fields),
            "no_future_data_used": all(bool(row.get("provenance", {}).get("cutoff_passed")) for row in available),
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


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "mlb_open_data" / "cutoff_date_features"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Cutoff Date Features",
        "",
        f"1. snapshot_count: {report.get('snapshot_count')}",
        f"2. available_snapshot_count: {report.get('available_snapshot_count')}",
        f"3. blocked_snapshot_count: {report.get('blocked_snapshot_count')}",
        f"4. feature_groups_available: {', '.join(report.get('feature_groups_available') or []) if report.get('feature_groups_available') else 'none'}",
        f"5. feature_groups_blocked: {', '.join(report.get('feature_groups_blocked') or []) if report.get('feature_groups_blocked') else 'none'}",
        f"6. no_future_data_used: {report.get('no_future_data_used')}",
        "7. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Feature Rows",
    ]
    for row in report.get("feature_rows") or []:
        lines.append(
            f"- {row.get('feature_group')}: status={row.get('status')}; source={row.get('provenance', {}).get('source_id')}; blocker={row.get('blocked_reason') or 'none'}"
        )
    return "\n".join(lines) + "\n"


def write_cutoff_feature_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_cutoff_date_features_{uuid4().hex[:8]}"))
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
    parser.add_argument("--season", required=True)
    parser.add_argument("--cutoff-date", required=True)
    parser.add_argument("--team", default=None)
    parser.add_argument("--player-id", default=None)
    parser.add_argument("--allow-cutoff-sensitive-fields", action="store_true")
    parser.add_argument("--include-postseason", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_cutoff_feature_report(
        season=args.season,
        cutoff_date=args.cutoff_date,
        team=args.team,
        player_id=args.player_id,
        allow_cutoff_sensitive_fields=args.allow_cutoff_sensitive_fields,
        include_postseason=args.include_postseason,
    )
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_cutoff_feature_report(report)
        report.update(paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
