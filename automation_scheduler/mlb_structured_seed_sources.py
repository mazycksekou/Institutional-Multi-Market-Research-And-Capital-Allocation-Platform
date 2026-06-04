from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from .mlb_open_data_common import MLB_MODULE, mlb_atomic_write_json, mlb_atomic_write_text, mlb_rel, mlb_report_root, mlb_safe_payload
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_STRUCTURED_SEED_SCHEMA_VERSION = "mlb_structured_seed_sources_v1"


def _source(
    *,
    source_id: str,
    source_name: str,
    source_family: str,
    source_access_type: str,
    source_kind: str,
    approval_status: str,
    terms_review_status: str,
    license_status: str,
    current_phase_allowed: bool,
    structured_seed_supported: bool = False,
    supplemental_only: bool = False,
    requires_auth: bool = False,
    requires_api_key: bool = False,
    raw_html_required: bool = False,
    spoofing_required: bool = False,
    automation_allowed: bool = True,
    expected_formats: list[str] | None = None,
    expected_join_keys: list[str] | None = None,
    likely_supported_features: list[str] | None = None,
    blockers: list[str] | None = None,
    safety_notes: str = "",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_name": source_name,
        "source_family": source_family,
        "module": MLB_MODULE,
        "source_access_type": source_access_type,
        "source_kind": source_kind,
        "approval_status": approval_status,
        "current_phase_allowed": bool(current_phase_allowed),
        "enabled": False,
        "terms_review_status": terms_review_status,
        "license_status": license_status,
        "structured_seed_supported": bool(structured_seed_supported),
        "supplemental_only": bool(supplemental_only),
        "requires_auth": bool(requires_auth),
        "requires_api_key": bool(requires_api_key),
        "raw_html_required": bool(raw_html_required),
        "spoofing_required": bool(spoofing_required),
        "automation_allowed": bool(automation_allowed),
        "expected_formats": list(expected_formats or ["json"]),
        "expected_join_keys": list(expected_join_keys or []),
        "likely_supported_features": list(likely_supported_features or []),
        "blockers": list(blockers or []),
        "safety_notes": safety_notes,
        "no_call_supported": True,
        "metadata_only_supported": True,
        "raw_html_persisted": False,
        "browser_impersonation_used": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def mlb_structured_seed_sources() -> list[dict[str, Any]]:
    return [
        _source(
            source_id="wikidata_mlb_seed",
            source_name="Wikidata MLB seed",
            source_family="wikidata_mlb_seed",
            source_access_type="structured_open_data",
            source_kind="structured_open_data",
            approval_status="approved_open_structured",
            terms_review_status="reviewed_open_allowed",
            license_status="cc0",
            current_phase_allowed=True,
            structured_seed_supported=True,
            expected_formats=["sparql_json", "json"],
            expected_join_keys=["wikidata_qid"],
            likely_supported_features=["team_identity", "franchises", "stadiums", "managers_coaches", "people_identifiers"],
            safety_notes="bounded structured seed only; no raw payload persistence; disabled by default until explicit AllowStructuredSeed",
        ),
        _source(
            source_id="wikipedia_mlb_seed",
            source_name="Wikipedia MLB supplemental seed",
            source_family="wikipedia_mlb_seed",
            source_access_type="structured_open_api",
            source_kind="structured_api",
            approval_status="approved_supplemental_only",
            terms_review_status="reviewed_open_allowed",
            license_status="cc_by_sa",
            current_phase_allowed=False,
            supplemental_only=True,
            expected_formats=["json"],
            expected_join_keys=["page_id", "title"],
            likely_supported_features=["page_title", "page_id", "canonical_label", "attribution"],
            blockers=["supplemental_only_no_record_ingestion"],
            safety_notes="supplemental metadata only; never parses prose or persists raw text",
        ),
    ]


def source_by_id(source_id: str) -> dict[str, Any] | None:
    for source in mlb_structured_seed_sources():
        if source["source_id"] == source_id:
            return source
    return None


def build_mlb_structured_seed_source_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    sources = mlb_structured_seed_sources()
    approved = [source["source_id"] for source in sources if source.get("current_phase_allowed")]
    blocked = [{"source_id": source["source_id"], "blocker": source.get("blockers", ["blocked"])[0]} for source in sources if not source.get("current_phase_allowed")]
    counts = Counter(str(source.get("approval_status") or "unknown") for source in sources)
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_STRUCTURED_SEED_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"mlb_structured_seed_sources_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
            "module": MLB_MODULE,
            "runtime_data_dir": str(base_data_dir) if base_data_dir is not None else None,
            "structured_seed_sources_checked": len(sources),
            "structured_seed_sources_used": approved,
            "structured_seed_sources_blocked": blocked,
            "approval_status_counts": dict(sorted(counts.items())),
            "sources": sources,
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "recommended_next_action": "run explicit AllowStructuredSeed with the Wikidata seed adapter; keep Wikipedia supplemental-only",
        }
    )


def render_mlb_structured_seed_source_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Structured Seed Sources",
        "",
        f"1. structured_seed_sources_checked: {report.get('structured_seed_sources_checked')}",
        f"2. structured_seed_sources_used: {', '.join(report.get('structured_seed_sources_used') or []) if report.get('structured_seed_sources_used') else 'none'}",
        f"3. structured_seed_sources_blocked: {', '.join(item.get('source_id') for item in report.get('structured_seed_sources_blocked') or []) if report.get('structured_seed_sources_blocked') else 'none'}",
        f"4. approval_status_counts: {json.dumps(report.get('approval_status_counts') or {}, sort_keys=True)}",
        "5. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Sources",
    ]
    for source in report.get("sources") or []:
        lines.append(
            f"- {source.get('source_id')}: approval={source.get('approval_status')}; allowed={str(source.get('current_phase_allowed')).lower()}; supplemental_only={str(source.get('supplemental_only')).lower()}"
        )
    return "\n".join(lines) + "\n"


def write_mlb_structured_seed_source_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    root = mlb_report_root(base_data_dir=base_data_dir, subdir="structured_seed")
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_structured_seed_sources_{uuid4().hex[:8]}"))
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
    mlb_atomic_write_text(latest_md, render_mlb_structured_seed_source_markdown(payload))
    mlb_atomic_write_json(item_json, payload)
    mlb_atomic_write_text(item_md, render_mlb_structured_seed_source_markdown(payload))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_mlb_structured_seed_source_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_mlb_structured_seed_source_report(report)
        report.update(paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
