from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .mlb_cutoff_date_features import cutoff_feature_availability_summary
from .mlb_open_data_feature_builders import (
    build_expanded_feature_readiness,
    build_mlb_feature_availability_flags,
    build_mlb_feature_builder_report,
)
from .mlb_open_data_field_catalog import build_mlb_open_data_field_catalog
from .mlb_open_data_source_exhaustion import build_source_exhaustion_report
from .mlb_structured_seed_sources import build_mlb_structured_seed_source_report
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_FEATURE_READINESS_SCHEMA_VERSION = "mlb_open_data_feature_readiness_v1"
MLB_MODULE = "baseball_mlb"


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
        path = base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
        payload = _read_json(path)
        if isinstance(payload, dict):
            scanned[source_id] = int(payload.get("records_validated", 0) or 0)
    return scanned


def build_mlb_feature_readiness_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    before = _read_json(base / "data_sources" / "mlb_open_data" / "field_catalog" / "latest.json")
    before = before if isinstance(before, dict) else {}
    before_entries = list(before.get("entries") or [])
    before_keys = _verified_field_keys(before_entries)
    before_verified = int(before.get("verified_field_count", len(before_keys)) or 0)
    before_unverified = int(before.get("unverified_field_count", 0) or 0)
    before_total = int(before.get("field_entries_created", len(before_entries)) or 0)

    catalog = build_mlb_open_data_field_catalog(base_data_dir=base)
    after_entries = list(catalog.get("entries") or [])
    after_keys = _verified_field_keys(after_entries)
    new_field_keys = sorted(after_keys - before_keys)
    new_fields_discovered = [{"source_id": source_id, "field_name": field_name} for source_id, field_name in new_field_keys]

    builder_report = build_mlb_feature_builder_report(base_data_dir=base)
    expanded = build_expanded_feature_readiness(base_data_dir=base)
    exhaustion = build_source_exhaustion_report(base_data_dir=base)
    structured_seed = build_mlb_structured_seed_source_report(base_data_dir=base)
    cutoff_summary = cutoff_feature_availability_summary()
    derived_availability = build_mlb_feature_availability_flags(base_data_dir=base)

    source_lanes_scanned = list(catalog.get("verified_sources") or [])
    records_scanned_by_lane = _records_scanned_by_lane(base, source_lanes_scanned)
    reports_consumed = [
        path
        for path in (
            "data_sources/mlb_open_data/field_catalog/latest.json",
            "data_sources/mlb_open_data/source_exhaustion/latest.json",
            "data_sources/mlb_open_data/feature_builders/latest.json",
            "data_sources/mlb_open_data/structured_seed/latest.json",
            "data_sources/mlb_open_data/cutoff_date_features/latest.json",
        )
        if (base / path).exists()
    ]

    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": MLB_FEATURE_READINESS_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"mlb_open_data_feature_readiness_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": MLB_MODULE,
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
        "feature_builder_count": builder_report.get("feature_builder_count", 0),
        "feature_builder_blocked_count": builder_report.get("feature_builder_blocked_count", 0),
        "derived_feature_availability": derived_availability,
        "expanded_feature_readiness": expanded,
        "source_exhaustion": exhaustion,
        "structured_seed_summary": structured_seed,
        "cutoff_feature_availability": cutoff_summary,
        "reports_consumed": reports_consumed,
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
    root = base / "mlb_open_data" / "feature_readiness"
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


def render_mlb_feature_readiness_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Open Data Feature Readiness",
        "",
        f"1. source_lanes_scanned: {len(report.get('source_lanes_scanned') or [])}",
        f"2. field_catalog_entries: before={report.get('field_catalog_entries_before')}; after={report.get('field_catalog_entries_after')}",
        f"3. verified_fields: before={report.get('verified_fields_before')}; after={report.get('verified_fields_after')}",
        f"4. unverified_fields: before={report.get('unverified_fields_before')}; after={report.get('unverified_fields_after')}",
        f"5. new_fields_discovered: {report.get('new_fields_discovered_count')}",
        f"6. cutoff_sensitive_fields: {report.get('cutoff_sensitive_fields')}; leakage_sensitive_fields: {report.get('leakage_sensitive_fields')}",
        f"7. feature_builders_added: {', '.join(report.get('feature_builders_added') or []) if report.get('feature_builders_added') else 'none'}",
        f"8. feature_builders_blocked: {len(report.get('feature_builders_blocked') or [])}",
        f"9. cutoff_feature_groups_available: {', '.join((report.get('cutoff_feature_availability') or {}).get('mlb_cutoff_date_feature_groups_available') or [])}",
        f"10. structured_seed_sources_used: {', '.join((report.get('structured_seed_summary') or {}).get('structured_seed_sources_used') or []) if (report.get('structured_seed_summary') or {}).get('structured_seed_sources_used') else 'none'}",
        f"11. source_exhaustion_safe_sources: {', '.join((report.get('source_exhaustion') or {}).get('mlb_new_safe_sources_found') or []) if (report.get('source_exhaustion') or {}).get('mlb_new_safe_sources_found') else 'none'}",
        f"12. feature_availability: {json.dumps(report.get('derived_feature_availability') or {}, sort_keys=True)}",
        "13. no_predictive_claim=true; no_fabricated_values=true",
        "14. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_mlb_feature_readiness_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_open_data_feature_readiness_{uuid4().hex[:8]}"))
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
    markdown = render_mlb_feature_readiness_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_mlb_feature_readiness_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_mlb_feature_readiness_report(report)
        report.update(paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
