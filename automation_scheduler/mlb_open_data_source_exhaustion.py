from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from .mlb_open_data_common import MLB_MODULE, mlb_atomic_write_json, mlb_atomic_write_text, mlb_rel, mlb_report_root, mlb_safe_payload
from .mlb_open_data_field_catalog import (
    build_existing_mlb_field_index,
    compare_candidate_fields_to_existing_catalog,
)
from .mlb_open_data_sources import mlb_open_data_sources
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_SOURCE_EXHAUSTION_SCHEMA_VERSION = "mlb_open_data_source_exhaustion_v1"

CANDIDATE_SOURCE_FAMILIES = [
    "retrosheet_open_dataset",
    "lahman_database",
    "mlb_stats_api",
    "statcast_public_data",
    "chadwick_register",
    "wikidata_mlb_seed",
    "wikipedia_mlb_seed",
    "official_public_web",
    "manual_csv_import",
    "market_odds_blocked",
]


def audit_candidate_source_families() -> list[dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    for source in mlb_open_data_sources():
        family = str(source.get("source_family") or "unknown")
        bucket = families.setdefault(
            family,
            {
                "source_family": family,
                "source_ids": [],
                "candidate_data_categories": [],
                "current_phase_allowed": False,
                "terms_review_statuses": set(),
                "license_statuses": set(),
            },
        )
        bucket["source_ids"].append(source["source_id"])
        bucket["candidate_data_categories"].append(source["data_category"])
        bucket["current_phase_allowed"] = bool(bucket["current_phase_allowed"] or source.get("current_phase_allowed"))
        bucket["terms_review_statuses"].add(str(source.get("terms_review_status") or "unknown"))
        bucket["license_statuses"].add(str(source.get("license_status") or "unknown"))
    out: list[dict[str, Any]] = []
    for family in sorted(families):
        row = families[family]
        out.append(
            {
                "source_family": family,
                "source_ids": row["source_ids"],
                "candidate_data_categories": sorted(set(row["candidate_data_categories"])),
                "current_phase_allowed": row["current_phase_allowed"],
                "terms_review_statuses": sorted(row["terms_review_statuses"]),
                "license_statuses": sorted(row["license_statuses"]),
            }
        )
    return out


def _candidate_fields_for_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    fields = []
    for field in list(source.get("expected_fields") or []):
        fields.append(
            {
                "field_name": field,
                "join_key": field in set(source.get("expected_join_keys") or []),
                "new_entity_coverage": source.get("data_category") in {"franchises", "people_identifiers", "structured_wiki_seed"},
                "higher_quality_replacement": False,
                "new_granularity": False,
            }
        )
    return fields


def classify_candidate_field_novelty(
    candidate_field: dict[str, Any],
    existing_index: dict[str, Any],
) -> dict[str, Any]:
    return compare_candidate_fields_to_existing_catalog([candidate_field], existing_index=existing_index)[0]


def build_source_field_diff_report(
    *,
    source_id: str,
    candidate_fields: list[dict[str, Any]],
    base_data_dir: str | Path | None = None,
    existing_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    classifications = compare_candidate_fields_to_existing_catalog(candidate_fields, base_data_dir=base_data_dir, existing_index=existing_index)
    ingestible = [row["field_name"] for row in classifications if row["ingestible"]]
    duplicates = [row["field_name"] for row in classifications if not row["ingestible"]]
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_SOURCE_EXHAUSTION_SCHEMA_VERSION,
            "source_id": source_id,
            "candidate_field_count": len(candidate_fields),
            "ingestible_field_count": len(ingestible),
            "ingestible_fields": ingestible,
            "duplicate_field_count": len(duplicates),
            "duplicate_fields": duplicates,
            "field_classifications": classifications,
        }
    )


def build_source_exhaustion_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    existing_index = build_existing_mlb_field_index(base_data_dir=base_data_dir)
    candidates = mlb_open_data_sources()
    families = audit_candidate_source_families()
    source_diffs: list[dict[str, Any]] = []
    new_safe: list[str] = []
    redundant: list[str] = []
    blocked: list[dict[str, Any]] = []
    source_status_counts = Counter()
    for source in candidates:
        diff = build_source_field_diff_report(
            source_id=source["source_id"],
            candidate_fields=_candidate_fields_for_source(source),
            base_data_dir=base_data_dir,
            existing_index=existing_index,
        )
        diff["source_name"] = source["source_name"]
        diff["source_family"] = source["source_family"]
        diff["data_category"] = source["data_category"]
        diff["approval_status"] = source.get("approval_status")
        diff["current_phase_allowed"] = bool(source.get("current_phase_allowed"))
        diff["terms_review_status"] = source.get("terms_review_status")
        diff["license_status"] = source.get("license_status")
        diff["blocker"] = None
        if not source.get("current_phase_allowed"):
            blocker = source.get("blockers", ["blocked"])[0]
            diff["blocker"] = blocker
            blocked.append({"source_id": source["source_id"], "blocker": blocker})
            source_status_counts["blocked"] += 1
        elif diff["ingestible_field_count"] > 0:
            new_safe.append(source["source_id"])
            source_status_counts["new_safe"] += 1
        else:
            redundant.append(source["source_id"])
            source_status_counts["redundant"] += 1
            diff["blocker"] = "redundant_with_existing_fields"
        source_diffs.append(diff)
    blocker_counts = Counter(item["blocker"] for item in blocked if item.get("blocker"))
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_SOURCE_EXHAUSTION_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"mlb_open_data_source_exhaustion_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
            "module": MLB_MODULE,
            "runtime_data_dir": str(base_data_dir) if base_data_dir is not None else None,
            "mlb_source_exhaustion_checked": True,
            "candidate_source_families_audited": CANDIDATE_SOURCE_FAMILIES,
            "candidate_source_families_present": [row["source_family"] for row in families],
            "candidate_sources_found": len(candidates),
            "mlb_new_safe_sources_found": new_safe,
            "mlb_new_safe_source_count": len(new_safe),
            "mlb_redundant_sources_skipped": redundant,
            "mlb_redundant_source_count": len(redundant),
            "mlb_blocked_sources": blocked,
            "mlb_blocked_source_count": len(blocked),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "source_status_counts": dict(sorted(source_status_counts.items())),
            "source_field_diffs": source_diffs,
            "families": families,
            "existing_verified_field_count": int(existing_index.get("verified_field_count", 0) or 0),
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "recommended_next_action": "review new safe fields, then run bounded downloads or structured seed imports for approved lanes",
        }
    )


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Open Data Source Exhaustion Audit",
        "",
        f"1. candidate_sources_found: {report.get('candidate_sources_found')}",
        f"2. new_safe_sources_found: {', '.join(report.get('mlb_new_safe_sources_found') or []) if report.get('mlb_new_safe_sources_found') else 'none'}",
        f"3. redundant_sources_skipped: {', '.join(report.get('mlb_redundant_sources_skipped') or []) if report.get('mlb_redundant_sources_skipped') else 'none'}",
        f"4. blocked_sources: {report.get('mlb_blocked_source_count')}",
        f"5. blocker_counts: {json.dumps(report.get('blocker_counts') or {}, sort_keys=True)}",
        "6. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Candidate Families",
    ]
    for family in report.get("families") or []:
        lines.append(
            f"- {family.get('source_family')}: source_ids={', '.join(family.get('source_ids') or [])}; allowed={str(family.get('current_phase_allowed')).lower()}"
        )
    return "\n".join(lines) + "\n"


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = Path(base_data_dir) if base_data_dir is not None else None
    root = (base / "data_sources" / "mlb_open_data" / "source_exhaustion") if base is not None else mlb_report_root(subdir="source_exhaustion")
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_source_exhaustion_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_open_data_source_exhaustion_{uuid4().hex[:8]}"))
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
    report = build_source_exhaustion_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_source_exhaustion_report(report)
        report.update(paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
