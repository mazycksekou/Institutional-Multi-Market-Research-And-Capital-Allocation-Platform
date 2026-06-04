from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_open_data_adapters import FIELD_HINTS, adapter_by_id
from .nfl_open_data_sources import NFL_MODULE, nfl_open_data_sources
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


NFL_OPEN_DATA_FIELD_CATALOG_SCHEMA_VERSION = "nfl_open_data_field_catalog_v1"

FEATURE_FAMILIES = [
    "schedule_results",
    "scoring_profile",
    "defensive_profile",
    "pace_play_volume",
    "play_by_play_efficiency",
    "roster_continuity",
    "player_availability",
    "injury_lineup",
    "depth_chart",
    "coaching_staff",
    "officials",
    "stadium_weather",
    "market_odds",
    "draft_capital",
    "combine_athletic_profile",
    "transactions",
    "postseason_labels",
    "rest_travel",
    "team_identity",
]

LEAKAGE_MARKERS = ("score", "result", "winner", "spread", "moneyline", "total_line", "postseason", "playoff", "super_bowl")


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "field_catalog"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _validated_latest_path(source_id: str, base: Path) -> Path:
    return base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


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


def _canonical_field_name(field: str) -> str:
    text = str(field).strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "gameday": "event_date",
        "game_date": "event_date",
        "home_points": "home_score",
        "away_points": "away_score",
        "recent_team": "team",
        "team_abbr": "team",
        "gsis_id": "player_id",
        "player_gsis_id": "player_id",
    }
    return aliases.get(text, text)


def _family_for(source: dict[str, Any], field: str) -> str:
    category = str(source.get("data_category"))
    lower = field.lower()
    if category == "schedules_results":
        if "game_type" in lower or "playoff" in lower or "super_bowl" in lower:
            return "postseason_labels"
        if "rest" in lower or "travel" in lower:
            return "rest_travel"
        return "schedule_results"
    if category == "play_by_play":
        return "play_by_play_efficiency" if any(token in lower for token in ("epa", "success", "wpa", "yard")) else "pace_play_volume"
    if category == "team_stats":
        return "defensive_profile" if "against" in lower or "def" in lower else "scoring_profile"
    if category == "player_stats":
        return "player_availability" if any(token in lower for token in ("player", "position", "team")) else "scoring_profile"
    if category in {"rosters", "weekly_rosters", "roster_continuity", "snap_counts", "participation"}:
        return "roster_continuity" if category != "snap_counts" else "player_availability"
    if category == "injuries":
        return "injury_lineup"
    if category == "depth_charts":
        return "depth_chart"
    if category == "transactions":
        return "transactions"
    if category == "draft":
        return "draft_capital"
    if category == "combine":
        return "combine_athletic_profile"
    if category == "officials":
        return "officials"
    if category in {"stadiums", "weather"}:
        return "stadium_weather"
    if category == "betting_lines_or_market_odds":
        return "market_odds"
    if category == "coaching":
        return "coaching_staff"
    if category in {"advanced_efficiency", "pace_or_play_volume"}:
        return "pace_play_volume" if category == "pace_or_play_volume" else "play_by_play_efficiency"
    return "team_identity"


def _leakage_risk(field: str, family: str) -> str:
    lower = field.lower()
    if family == "market_odds":
        return "market_timing_cutoff_required"
    if any(marker in lower for marker in LEAKAGE_MARKERS):
        return "target_or_postgame_field_requires_cutoff"
    return "low"


def _field_entry(
    *,
    source: dict[str, Any],
    field_name: str,
    verified: bool,
    data_type: str | None = None,
    seasons_available: list[str] | None = None,
) -> dict[str, Any]:
    family = _family_for(source, field_name)
    leakage = _leakage_risk(field_name, family)
    verified_and_allowed = bool(verified and source.get("current_phase_allowed"))
    return {
        "field_name": field_name,
        "canonical_field_name": _canonical_field_name(field_name),
        "source_id": source["source_id"],
        "source_family": source.get("source_family"),
        "data_category": source.get("data_category"),
        "module": NFL_MODULE,
        "description": "verified source field" if verified else "expected candidate field pending source sample verification",
        "granularity": source.get("expected_granularity"),
        "join_keys": source.get("expected_join_keys") or [],
        "seasons_available": seasons_available or [],
        "nullable": True,
        "data_type": data_type or "unknown",
        "raw_field_allowed": bool(verified),
        "normalized_field_supported": bool(verified_and_allowed),
        "model_feature_family": family,
        "pattern_feature_family": family,
        "validation_use_case": "coverage_and_ingestion_only",
        "leakage_risk": leakage,
        "target_leakage_safe": leakage == "low",
        "requires_season_cutoff": leakage != "low",
        "source_status": "verified" if verified else "unverified",
        "implementation_status": "available" if verified_and_allowed else "research_required",
        "current_phase_allowed": bool(verified_and_allowed),
        "blocker": None if verified_and_allowed else "field_not_verified_by_sample",
    }


def build_nfl_open_data_field_catalog(
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    entries: list[dict[str, Any]] = []
    verified_sources: list[str] = []
    for source in nfl_open_data_sources():
        latest = _read_json(_validated_latest_path(source["source_id"], base))
        verified_fields = list((latest or {}).get("fields_available") or [])
        field_types = dict((latest or {}).get("field_types") or {})
        seasons = [str(item) for item in list((latest or {}).get("seasons_available") or [])]
        if verified_fields:
            verified_sources.append(source["source_id"])
            for field in verified_fields:
                entries.append(
                    _field_entry(
                        source=source,
                        field_name=str(field),
                        verified=True,
                        data_type=str(field_types.get(field) or "unknown"),
                        seasons_available=seasons,
                    )
                )
        else:
            adapter = adapter_by_id(source["source_id"])
            fields = adapter.list_expected_fields() if adapter else FIELD_HINTS.get(str(source.get("data_category")), [])
            for field in fields:
                entries.append(_field_entry(source=source, field_name=str(field), verified=False))
    families = sorted({entry["model_feature_family"] for entry in entries})
    unverified = sum(1 for entry in entries if entry["source_status"] == "unverified")
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_OPEN_DATA_FIELD_CATALOG_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_field_catalog_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "field_entries_created": len(entries),
        "verified_source_count": len(verified_sources),
        "verified_sources": verified_sources,
        "unverified_field_count": unverified,
        "feature_families_covered": families,
        "entries": entries,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def render_nfl_open_data_field_catalog_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Open Data Field Catalog",
        "",
        f"1. field_entries_created: {report.get('field_entries_created')}",
        f"2. verified_source_count: {report.get('verified_source_count')}",
        f"3. unverified_field_count: {report.get('unverified_field_count')}",
        f"4. feature_families_covered: {', '.join(report.get('feature_families_covered') or [])}",
        "5. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Fields",
    ]
    for entry in list(report.get("entries") or [])[:300]:
        lines.append(
            f"- {entry.get('source_id')}.{entry.get('field_name')}: status={entry.get('source_status')}; implementation={entry.get('implementation_status')}; family={entry.get('model_feature_family')}; leakage={entry.get('leakage_risk')}"
        )
    return "\n".join(lines) + "\n"


def write_nfl_open_data_field_catalog(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_field_catalog_{uuid4().hex[:8]}"))
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
    markdown = render_nfl_open_data_field_catalog_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_open_data_field_catalog()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_open_data_field_catalog(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "field_entries_created": report.get("field_entries_created"),
                "verified_source_count": report.get("verified_source_count"),
                "unverified_field_count": report.get("unverified_field_count"),
                "feature_families_covered": report.get("feature_families_covered"),
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
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
