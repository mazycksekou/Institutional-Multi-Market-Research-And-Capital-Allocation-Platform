"""NFL open-data feature readiness report (availability only, no predictive claims).

Re-seeds the field catalog from the fully backfilled compact outputs, diffs it
against the previously persisted catalog, and combines feature-builder
availability, derived-feature availability flags, pattern-lab expanded
readiness, and the holdout validation guard summary into one compact report.

No provider calls and no downloads occur here; only local compact outputs are
read. No raw provider payloads or full source URLs are persisted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from src.providers.nfl_open_data_feature_builders import (
    build_expanded_feature_readiness,
    build_nfl_feature_builder_report,
)
from src.data.nfl_open_data_field_catalog import build_nfl_open_data_field_catalog
from src.data.nfl_historical_pattern_lab import build_validation_guard_summary
from src.data.open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_FEATURE_READINESS_SCHEMA_VERSION = "nfl_open_data_feature_readiness_v1"
NFL_MODULE = "americanfootball_nfl"


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _verified_field_keys(entries: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {
        (str(entry.get("source_id")), str(entry.get("field_name")))
        for entry in entries
        if entry.get("source_status") == "verified"
    }


def _records_scanned_by_lane(base: Path, source_ids: list[str]) -> dict[str, int]:
    scanned: dict[str, int] = {}
    for source_id in source_ids:
        path = base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
        payload = _read_json(path)
        if isinstance(payload, dict):
            scanned[source_id] = int(payload.get("records_validated", 0) or 0)
    return scanned


def _nfl_derived_availability_flags(report: dict[str, Any]) -> dict[str, Any]:
    flags = dict(report.get("feature_availability") or {})
    flags["nfl_feature_builder_count"] = report.get("feature_builder_count", 0)
    flags["nfl_feature_builder_blockers"] = [row.get("blocked_reason") for row in report.get("feature_builders_blocked") or []]
    flags["nfl_cutoff_sensitive_feature_count"] = report.get("cutoff_sensitive_feature_count", 0)
    flags["nfl_leakage_sensitive_feature_count"] = report.get("leakage_sensitive_feature_count", 0)
    return flags


def build_nfl_feature_readiness_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    before = _read_json(base / "data_sources" / "nfl_open_data" / "field_catalog" / "latest.json")
    before = before if isinstance(before, dict) else {}
    before_entries = list(before.get("entries") or [])
    before_keys = _verified_field_keys(before_entries)
    before_verified = int(before.get("verified_field_count", len(before_keys)) or 0)
    before_unverified = int(before.get("unverified_field_count", 0) or 0)
    before_total = int(before.get("field_entries_created", len(before_entries)) or 0)

    catalog = build_nfl_open_data_field_catalog(base_data_dir=base)
    after_entries = list(catalog.get("entries") or [])
    after_keys = _verified_field_keys(after_entries)
    new_field_keys = sorted(after_keys - before_keys)
    new_fields_discovered = [{"source_id": source_id, "field_name": field_name} for source_id, field_name in new_field_keys]

    builder_report = build_nfl_feature_builder_report(base_data_dir=base)
    expanded = build_expanded_feature_readiness(base_data_dir=base)
    guard_summary = build_validation_guard_summary(base_data_dir=base)
    derived_availability = _nfl_derived_availability_flags(builder_report)

    source_lanes_scanned = list(catalog.get("verified_sources") or [])
    records_scanned_by_lane = _records_scanned_by_lane(base, source_lanes_scanned)

    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_FEATURE_READINESS_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_feature_readiness_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "runtime_data_dir": str(base),
        "source_lanes_scanned": source_lanes_scanned,
        "records_scanned_by_lane": records_scanned_by_lane,
        "field_catalog_entries_before": before_total,
        "field_catalog_entries_after": int(catalog.get("field_entries_created", len(after_entries)) or 0),
        "verified_fields_before": before_verified,
        "verified_fields_after": int(catalog.get("verified_field_count", len(after_keys)) or 0),
        "unverified_fields_before": before_unverified,
        "unverified_fields_after": int(catalog.get("unverified_field_count", 0) or 0),
        "new_fields_discovered": new_fields_discovered,
        "new_fields_discovered_count": len(new_fields_discovered),
        "fields_by_feature_family": catalog.get("fields_by_feature_family") or {},
        "cutoff_sensitive_fields": int(catalog.get("cutoff_sensitive_field_count", 0) or 0),
        "leakage_sensitive_fields": int(catalog.get("leakage_sensitive_field_count", 0) or 0),
        "feature_builders_added": builder_report.get("feature_builders_added") or [],
        "feature_builders_blocked": builder_report.get("feature_builders_blocked") or [],
        "derived_feature_availability": derived_availability,
        "pattern_lab_availability": expanded,
        "validation_guard_summary": guard_summary,
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
    root = base / "nfl_open_data" / "feature_readiness"
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


def render_nfl_feature_readiness_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Open Data Feature Readiness",
        "",
        f"1. source_lanes_scanned: {len(report.get('source_lanes_scanned') or [])}",
        f"2. field_catalog_entries: before={report.get('field_catalog_entries_before')}; after={report.get('field_catalog_entries_after')}",
        f"3. verified_fields: before={report.get('verified_fields_before')}; after={report.get('verified_fields_after')}",
        f"4. unverified_fields: before={report.get('unverified_fields_before')}; after={report.get('unverified_fields_after')}",
        f"5. new_fields_discovered: {report.get('new_fields_discovered_count')}",
        f"6. cutoff_sensitive_fields: {report.get('cutoff_sensitive_fields')}; leakage_sensitive_fields: {report.get('leakage_sensitive_fields')}",
        f"7. feature_builders_added: {', '.join(report.get('feature_builders_added') or []) if report.get('feature_builders_added') else 'none'}",
        f"8. feature_builders_blocked: {len(report.get('feature_builders_blocked') or [])}",
        f"9. fields_by_feature_family: {json.dumps(report.get('fields_by_feature_family') or {}, sort_keys=True)}",
        "10. no_predictive_claim=true; no_fabricated_values=true",
        "11. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
    ]
    return "\n".join(lines)


def write_nfl_feature_readiness_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_feature_readiness_{uuid4().hex[:8]}"))
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
    markdown = render_nfl_feature_readiness_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_feature_readiness_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_feature_readiness_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "source_lanes_scanned": len(report.get("source_lanes_scanned") or []),
                "field_catalog_entries_before": report.get("field_catalog_entries_before"),
                "field_catalog_entries_after": report.get("field_catalog_entries_after"),
                "verified_fields_before": report.get("verified_fields_before"),
                "verified_fields_after": report.get("verified_fields_after"),
                "unverified_fields_after": report.get("unverified_fields_after"),
                "new_fields_discovered_count": report.get("new_fields_discovered_count"),
                "feature_builders_added": report.get("feature_builders_added"),
                "cutoff_sensitive_fields": report.get("cutoff_sensitive_fields"),
                "leakage_sensitive_fields": report.get("leakage_sensitive_fields"),
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
