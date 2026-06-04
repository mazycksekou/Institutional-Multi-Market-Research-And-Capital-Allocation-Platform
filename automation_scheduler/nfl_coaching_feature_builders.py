"""NFL coaching/staff feature builders (availability + provenance only).

Builds source-supported coaching features from already-validated compact
coaching rows. No fabrication: continuity features are only computed when the
required adjacent seasons are source-supported, ambiguous roles
(role_group=unknown) are never used for coordinator continuity, and a feature is
blocked when season/team are missing. No predictive claims, no calibration, no
betting outputs. No provider calls and no downloads occur here.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_coaching_adapters import build_nfl_coaching_ingestion_report, load_validated_coaching_rows
from .nfl_coaching_sources import COACHING_TARGET_FIELDS, build_nfl_coaching_source_report
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


COACHING_READINESS_FLAG_DEFAULTS = {
    "nfl_coaching_data_available": False,
    "nfl_coaching_sources_checked": 0,
    "nfl_coaching_sources_allowed": [],
    "nfl_coaching_sources_blocked": [],
    "nfl_coaching_records_validated": 0,
    "nfl_coaching_teams_covered": [],
    "nfl_coaching_seasons_covered": [],
    "nfl_coaching_feature_builders_available": [],
    "nfl_coaching_feature_builder_blockers": [],
    "nfl_coaching_leakage_guard_status": "active_offseason_cutoff_required",
}


def coaching_readiness_flags(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    source_report = build_nfl_coaching_source_report(base_data_dir=base)
    feature_summary = coaching_feature_availability_summary(base_data_dir=base)
    return {
        "nfl_coaching_data_available": int(feature_summary["nfl_coaching_records_validated"]) > 0,
        "nfl_coaching_sources_checked": source_report["coaching_sources_audited"],
        "nfl_coaching_sources_allowed": source_report["approved_coaching_sources"],
        "nfl_coaching_sources_blocked": source_report["blocked_coaching_sources"],
        "nfl_coaching_records_validated": feature_summary["nfl_coaching_records_validated"],
        "nfl_coaching_teams_covered": feature_summary["nfl_coaching_teams_covered"],
        "nfl_coaching_seasons_covered": feature_summary["nfl_coaching_seasons_covered"],
        "nfl_coaching_feature_builders_available": feature_summary["nfl_coaching_feature_builders_available"],
        "nfl_coaching_feature_builder_blockers": feature_summary["nfl_coaching_feature_builder_blockers"],
        "nfl_coaching_leakage_guard_status": feature_summary["nfl_coaching_leakage_guard_status"],
    }


NFL_COACHING_FEATURE_SCHEMA_VERSION = "nfl_coaching_feature_builders_v1"
NFL_MODULE = "americanfootball_nfl"

COACHING_FEATURE_BUILDERS = [
    "head_coach_by_team_season",
    "coordinator_by_team_season",
    "coaching_staff_by_team_season",
    "coaching_continuity_candidates",
    "coordinator_continuity_candidates",
    "staff_turnover_candidates",
]


def _season_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _provenance(rows: list[dict[str, Any]], *, fields_used: list[str], cutoff_required: bool, leakage_risk: str) -> dict[str, Any]:
    return {
        "source_id": sorted({str(row.get("source_id")) for row in rows if row.get("source_id")}),
        "source_fields_used": list(fields_used),
        "seasons_supported": sorted({str(row.get("season")) for row in rows if row.get("season")}),
        "teams_supported": sorted({str(row.get("team")) for row in rows if row.get("team")}),
        "granularity": "team_season",
        "cutoff_required": cutoff_required,
        "leakage_risk": leakage_risk,
    }


def _blocked(name: str, reason: str, *, confidence: str = "none") -> dict[str, Any]:
    return {
        "feature_name": name,
        "status": "blocked",
        "blocked_reason": reason,
        "provenance": {
            "source_id": [],
            "source_fields_used": [],
            "seasons_supported": [],
            "teams_supported": [],
            "granularity": "team_season",
            "cutoff_required": True,
            "leakage_risk": "offseason_known_requires_cutoff",
        },
        "confidence": confidence,
        "values": {},
        "no_fabricated_values": True,
    }


def _available(name: str, rows: list[dict[str, Any]], *, fields_used: list[str], values: dict[str, Any], cutoff_required: bool = True, leakage_risk: str = "offseason_known_requires_cutoff", confidence: str = "source_reported") -> dict[str, Any]:
    return {
        "feature_name": name,
        "status": "available",
        "blocked_reason": None,
        "provenance": _provenance(rows, fields_used=fields_used, cutoff_required=cutoff_required, leakage_risk=leakage_risk),
        "confidence": confidence,
        "values": values,
        "no_fabricated_values": True,
    }


def _has_team_season(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("team") and row.get("season") for row in rows)


def build_head_coach_by_team_season(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _blocked("head_coach_by_team_season", "no_coaching_records_available")
    if not _has_team_season(rows):
        return _blocked("head_coach_by_team_season", "missing_team_or_season")
    hc = [row for row in rows if row.get("head_coach_flag")]
    if not hc:
        return _blocked("head_coach_by_team_season", "no_head_coach_rows")
    return _available(
        "head_coach_by_team_season",
        hc,
        fields_used=["team", "season", "staff_name", "head_coach_flag"],
        values={"head_coach_team_seasons": len({(row["team"], row["season"]) for row in hc})},
    )


def build_coordinator_by_team_season(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _blocked("coordinator_by_team_season", "no_coaching_records_available")
    coords = [row for row in rows if row.get("role_group") in {"offensive_coordinator", "defensive_coordinator", "special_teams_coordinator"}]
    if not coords:
        return _blocked("coordinator_by_team_season", "no_coordinator_rows")
    return _available(
        "coordinator_by_team_season",
        coords,
        fields_used=["team", "season", "staff_name", "role_group"],
        values={"coordinator_team_seasons": len({(row["team"], row["season"], row["role_group"]) for row in coords})},
    )


def build_coaching_staff_by_team_season(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _blocked("coaching_staff_by_team_season", "no_coaching_records_available")
    if not _has_team_season(rows):
        return _blocked("coaching_staff_by_team_season", "missing_team_or_season")
    return _available(
        "coaching_staff_by_team_season",
        rows,
        fields_used=["team", "season", "staff_name", "staff_role", "role_group"],
        values={"staff_team_seasons": len({(row["team"], row["season"]) for row in rows if row.get("team") and row.get("season")})},
    )


def _adjacent_continuity(rows: list[dict[str, Any]], *, role_predicate, name: str) -> dict[str, Any]:
    eligible = [row for row in rows if role_predicate(row) and row.get("team") and _season_int(row.get("season")) is not None and row.get("staff_name")]
    if not eligible:
        return _blocked(name, "no_eligible_role_rows")
    by_team_season: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in eligible:
        by_team_season[row["team"]][_season_int(row["season"])].add(str(row["staff_name"]).strip().lower())
    pairs_evaluated = 0
    continuous = 0
    teams_with_gap = 0
    for team, seasons in by_team_season.items():
        ordered = sorted(seasons)
        has_pair = False
        for season in ordered:
            if (season - 1) in seasons:
                has_pair = True
                pairs_evaluated += 1
                if seasons[season] & seasons[season - 1]:
                    continuous += 1
        if not has_pair:
            teams_with_gap += 1
    if pairs_evaluated == 0:
        return _blocked(name, "adjacent_season_missing")
    return _available(
        name,
        eligible,
        fields_used=["team", "season", "staff_name", "role_group"],
        values={
            "adjacent_season_pairs_evaluated": pairs_evaluated,
            "continuous_pairs": continuous,
            "teams_without_adjacent_pair": teams_with_gap,
        },
    )


def build_coaching_continuity_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _blocked("coaching_continuity_candidates", "no_coaching_records_available")
    return _adjacent_continuity(rows, role_predicate=lambda r: bool(r.get("head_coach_flag")), name="coaching_continuity_candidates")


def build_coordinator_continuity_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _blocked("coordinator_continuity_candidates", "no_coaching_records_available")
    # Ambiguous coordinators (role_group=unknown) are never used for continuity.
    return _adjacent_continuity(
        rows,
        role_predicate=lambda r: r.get("role_group") in {"offensive_coordinator", "defensive_coordinator", "special_teams_coordinator"},
        name="coordinator_continuity_candidates",
    )


def build_staff_turnover_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _blocked("staff_turnover_candidates", "no_coaching_records_available")
    eligible = [row for row in rows if row.get("team") and _season_int(row.get("season")) is not None and row.get("staff_name")]
    if not eligible:
        return _blocked("staff_turnover_candidates", "missing_team_or_season")
    by_team: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in eligible:
        by_team[row["team"]][_season_int(row["season"])].add(str(row["staff_name"]).strip().lower())
    pairs = 0
    for seasons in by_team.values():
        for season in seasons:
            if (season - 1) in seasons:
                pairs += 1
    if pairs == 0:
        return _blocked("staff_turnover_candidates", "adjacent_season_missing")
    return _available(
        "staff_turnover_candidates",
        eligible,
        fields_used=["team", "season", "staff_name"],
        values={"adjacent_season_pairs_evaluated": pairs},
    )


def build_nfl_coaching_features(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        build_head_coach_by_team_season(rows),
        build_coordinator_by_team_season(rows),
        build_coaching_staff_by_team_season(rows),
        build_coaching_continuity_candidates(rows),
        build_coordinator_continuity_candidates(rows),
        build_staff_turnover_candidates(rows),
    ]


def build_nfl_coaching_feature_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    rows = load_validated_coaching_rows(base_data_dir=base)
    features = build_nfl_coaching_features(rows)
    available = [row["feature_name"] for row in features if row["status"] == "available"]
    blocked = [{"feature_name": row["feature_name"], "blocked_reason": row["blocked_reason"]} for row in features if row["status"] != "available"]
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_COACHING_FEATURE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_coaching_features_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "coaching_records_loaded": len(rows),
        "feature_builders": features,
        "coaching_feature_builders_available": available,
        "coaching_feature_builder_blockers": blocked,
        "teams_covered": sorted({str(row.get("team")) for row in rows if row.get("team")}),
        "seasons_covered": sorted({str(row.get("season")) for row in rows if row.get("season")}),
        "role_groups_covered": sorted({str(row.get("role_group")) for row in rows if row.get("role_group")}),
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
        "raw_html_persisted": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def coaching_feature_availability_summary(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_nfl_coaching_feature_report(base_data_dir=base_data_dir)
    return {
        "nfl_coaching_records_validated": report["coaching_records_loaded"],
        "nfl_coaching_teams_covered": report["teams_covered"],
        "nfl_coaching_seasons_covered": report["seasons_covered"],
        "nfl_coaching_feature_builders_available": report["coaching_feature_builders_available"],
        "nfl_coaching_feature_builder_blockers": [row["blocked_reason"] for row in report["coaching_feature_builder_blockers"]],
        "nfl_coaching_leakage_guard_status": "active_offseason_cutoff_required",
    }


def _coaching_fields_status(rows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    present: set[str] = set()
    for row in rows:
        for field in COACHING_TARGET_FIELDS:
            if str(row.get(field) or "").strip():
                present.add(field)
    available = sorted(present)
    blocked = sorted(set(COACHING_TARGET_FIELDS) - present)
    return available, blocked


def build_nfl_coaching_acquisition_report(
    *,
    allow_crawl: bool = False,
    allow_manual_import: bool = False,
    input_csv: str | None = None,
    persist_preview: bool = False,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    ingestion = build_nfl_coaching_ingestion_report(
        allow_crawl=allow_crawl,
        allow_manual_import=allow_manual_import,
        input_csv=input_csv,
        persist_preview=persist_preview,
        base_data_dir=base,
    )
    feature_report = build_nfl_coaching_feature_report(base_data_dir=base)
    rows = load_validated_coaching_rows(base_data_dir=base)
    fields_available, fields_blocked = _coaching_fields_status(rows)
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_COACHING_FEATURE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_coaching_acquisition_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "sources_checked": ingestion["sources_checked"],
        "sources_allowed": ingestion["sources_allowed"],
        "sources_blocked": ingestion["sources_blocked"],
        "robots_allowed_count": ingestion["robots_allowed_count"],
        "robots_blocked_count": ingestion["robots_blocked_count"],
        "terms_allowed_count": ingestion["terms_allowed_count"],
        "terms_blocked_count": ingestion["terms_blocked_count"],
        "records_validated": ingestion["records_validated"],
        "records_rejected": ingestion["records_rejected"],
        "seasons_covered": feature_report["seasons_covered"],
        "teams_covered": feature_report["teams_covered"],
        "role_groups_covered": feature_report["role_groups_covered"],
        "coaching_fields_available": fields_available,
        "coaching_fields_blocked": fields_blocked,
        "feature_builders_available": feature_report["coaching_feature_builders_available"],
        "feature_builders_blocked": feature_report["coaching_feature_builder_blockers"],
        "nfl_coaching_data_available": ingestion["nfl_coaching_data_available"],
        "nfl_coaching_data_blocked_reason": ingestion["nfl_coaching_data_blocked_reason"],
        "spoofing_used": False,
        "browser_impersonation_used": False,
        "raw_html_persisted": False,
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
        "storage_health": get_storage_health(),
    }


def _coaching_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "coaching"
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


def render_coaching_acquisition_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Coaching Acquisition",
        "",
        f"1. sources_checked: {report.get('sources_checked')}",
        f"2. sources_allowed: {', '.join(report.get('sources_allowed') or []) if report.get('sources_allowed') else 'none'}",
        f"3. robots_allowed_count: {report.get('robots_allowed_count')}; robots_blocked_count: {report.get('robots_blocked_count')}",
        f"4. terms_allowed_count: {report.get('terms_allowed_count')}; terms_blocked_count: {report.get('terms_blocked_count')}",
        f"5. records_validated: {report.get('records_validated')}; records_rejected: {report.get('records_rejected')}",
        f"6. teams_covered: {len(report.get('teams_covered') or [])}; seasons_covered: {len(report.get('seasons_covered') or [])}",
        f"7. role_groups_covered: {', '.join(report.get('role_groups_covered') or []) if report.get('role_groups_covered') else 'none'}",
        f"8. feature_builders_available: {', '.join(report.get('feature_builders_available') or []) if report.get('feature_builders_available') else 'none'}",
        "9. spoofing_used=false; browser_impersonation_used=false; raw_html_persisted=false",
        "10. safety: provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false; no_predictive_claim=true",
        "",
    ]
    return "\n".join(lines)


def write_nfl_coaching_acquisition_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _coaching_root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_coaching_acquisition_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    coverage_json = root / "coverage_matrix" / "latest.json"
    coverage_md = root / "coverage_matrix" / "latest.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
        "coverage_latest_json_path": _rel(coverage_json, base_data_dir),
        "coverage_latest_markdown_path": _rel(coverage_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False, "raw_html_persisted": False}
    markdown = render_coaching_acquisition_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    _atomic_write_json(coverage_json, payload)
    _atomic_write_text(coverage_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    from .nfl_coaching_adapters import adapter_by_id, ManualCsvCoachingImportAdapter

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        default="coverage_report",
        choices=[
            "metadata_check",
            "tiny_sample",
            "crawl_staff_pages",
            "crawl_press_releases",
            "wikidata_seed",
            "wikipedia_seed",
            "manual_import",
            "coverage_report",
        ],
    )
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--input-csv", default=None)
    parser.add_argument("--allow-crawl", action="store_true")
    parser.add_argument("--allow-manual-import", action="store_true")
    parser.add_argument("--max-pages-per-domain", type=int, default=None)
    parser.add_argument("--crawl-delay-seconds", type=int, default=None)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)

    mode_to_source = {
        "crawl_staff_pages": "official_team_staff_pages",
        "crawl_press_releases": "official_team_press_releases",
        "wikidata_seed": "wikidata_coaching_seed",
        "wikipedia_seed": "wikipedia_coaching_seed",
    }
    summary: dict[str, Any]
    if args.mode == "coverage_report":
        report = build_nfl_coaching_acquisition_report(
            allow_crawl=args.allow_crawl,
            allow_manual_import=args.allow_manual_import,
            input_csv=args.input_csv,
            persist_preview=args.persist,
        )
        if args.persist:
            report.update(write_nfl_coaching_acquisition_report(report))
        summary = {
            "ok": report["ok"],
            "mode": args.mode,
            "sources_checked": report["sources_checked"],
            "sources_allowed": report["sources_allowed"],
            "records_validated": report["records_validated"],
            "feature_builders_available": report["feature_builders_available"],
            "nfl_coaching_data_available": report["nfl_coaching_data_available"],
            "latest_json_path": report.get("latest_json_path"),
        }
    elif args.mode == "manual_import":
        adapter = ManualCsvCoachingImportAdapter(adapter_by_id("manual_csv_import").source)
        run = adapter.run_manual_import(
            input_csv=args.input_csv,
            allow_manual_import=args.allow_manual_import,
            max_records=args.max_records,
            persist_preview=args.persist,
        )
        summary = {"mode": args.mode, **{k: run.get(k) for k in ("ok", "status", "records_validated", "records_rejected", "blocked_reason")}}
    else:
        source_id = args.source_id or mode_to_source.get(args.mode)
        adapter = adapter_by_id(source_id) if source_id else None
        if adapter is None:
            summary = {"mode": args.mode, "ok": False, "status": "unknown_source", "source_id": source_id}
        elif args.mode == "tiny_sample":
            summary = {"mode": args.mode, **adapter.run_tiny_sample(allow_crawl=args.allow_crawl)}
        else:
            summary = {"mode": args.mode, **adapter.run_metadata_check()}
    summary.update(
        {
            "no_predictive_claim": True,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "raw_html_persisted": False,
            "secrets_included": False,
        }
    )
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
