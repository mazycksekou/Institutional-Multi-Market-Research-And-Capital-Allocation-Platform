from __future__ import annotations

from pathlib import Path
from typing import Any

from .nhl_free_vs_paid_readiness import nhl_lane_catalog
from .nhl_oxylabs_common import current_utc, write_json, write_md
from .nhl_schema_expansion import build_nhl_schema_expansion_report


REPORT_ROOT = Path("reports")


def build_nhl_oxylabs_schema_expansion_report(
    *,
    source_exhaustion_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
    sample_verification_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = build_nhl_schema_expansion_report(sample_verification_results=sample_verification_results)
    audit_index = {row["lane_name"]: row for row in (source_exhaustion_report or {}).get("source_candidate_rows") or []}
    backfill_index = {row["lane_name"]: row for row in (backfill_report or {}).get("backfill_rows") or []}
    lane_index = {lane["lane_name"]: lane for lane in nhl_lane_catalog()}
    rows = []
    for entry in base.get("new_fields_created") or []:
        lane_name = next((lane["lane_name"] for lane in nhl_lane_catalog() if lane["table"] == entry["table"]), "")
        audit_row = audit_index.get(lane_name, {})
        backfill_row = backfill_index.get(lane_name, {})
        lane = lane_index.get(lane_name, {})
        rows.append(
            {
                **entry,
                "source_id": lane.get("source_id") or entry.get("source_id"),
                "source_url_hash": backfill_row.get("source_url_hash") or audit_row.get("source_url_hash") or entry.get("source_url_hash"),
                "retrieval_method": lane.get("retrieval_method") or entry.get("retrieval_method"),
                "oxylabs_transport_used": backfill_row.get("oxylabs_transport_used") or audit_row.get("oxylabs_transport_used") or "residential_proxy",
                "license_or_terms_note": lane.get("license_or_terms_note") or entry.get("license_or_terms_note"),
                "tests": ["tests/test_nhl_schema_expansion.py", "tests/test_nhl_oxylabs_schema_expansion.py"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_OXYLABS_SCHEMA_EXPANSION_REPORT",
        "schema_version": "nhl_oxylabs_schema_expansion_v1",
        "created_at": current_utc(),
        "new_fields_created": rows,
        "new_fields_created_count": len(rows),
        "new_tables_created": base.get("new_tables_created") or [],
        "new_tables_created_count": int(base.get("new_tables_created_count", 0) or 0),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_nhl_oxylabs_schema_expansion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_OXYLABS_SCHEMA_EXPANSION_REPORT.json"
    md_path = root / "NHL_OXYLABS_SCHEMA_EXPANSION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# NHL Oxylabs Schema Expansion Report",
        "",
        f"1. new_fields_created_count: {report.get('new_fields_created_count')}",
        f"2. new_tables_created_count: {report.get('new_tables_created_count')}",
        "",
        "## Fields",
    ]
    for row in report.get("new_fields_created") or []:
        lines.append(
            f"- {row.get('field_name')} table={row.get('table')} transport={row.get('oxylabs_transport_used')} validation={row.get('validation_status')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
