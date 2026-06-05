from __future__ import annotations

from pathlib import Path
from typing import Any

from .golf_oxylabs_common import current_utc, write_json, write_md
from .golf_sample_verifier import build_golf_targeted_sample_verification_results
from .golf_schema_expansion import build_golf_schema_expansion_report


REPORT_ROOT = Path("reports")


def build_golf_oxylabs_schema_expansion_report(
    *,
    sample_verification_results: dict[str, Any] | None = None,
    schema_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sample_verification_results = sample_verification_results or build_golf_targeted_sample_verification_results()
    schema_report = schema_report or build_golf_schema_expansion_report(sample_verification_results=sample_verification_results)
    sample_index = dict(sample_verification_results.get("source_result_index") or {})
    rows = []
    for entry in schema_report.get("new_fields_created") or []:
        lane_name = ""
        for sample in sample_index.values():
            if sample.get("validation_status") != "sample_verified":
                continue
            if sample.get("lane_name") and sample.get("lane_name") in entry.get("table", ""):
                lane_name = str(sample.get("lane_name") or "")
                break
        rows.append({**entry, "lane_name": lane_name, "oxylabs_used": True})
    return {
        "ok": True,
        "status": "ok",
        "report_name": "golf_OXYLABS_SCHEMA_EXPANSION_REPORT",
        "schema_version": "golf_oxylabs_schema_expansion_v1",
        "created_at": current_utc(),
        "sport": "golf",
        "new_fields_created": rows,
        "new_fields_created_count": len(rows),
        "new_tables_created_count": int(schema_report.get("new_tables_created_count", 0) or 0),
        "oxylabs_verified_field_count": len(rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_golf_oxylabs_schema_expansion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_OXYLABS_SCHEMA_EXPANSION_REPORT.json"
    md_path = root / "GOLF_OXYLABS_SCHEMA_EXPANSION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Golf Oxylabs Schema Expansion Report",
        "",
        f"1. new_fields_created_count: {report.get('new_fields_created_count')}",
        f"2. new_tables_created_count: {report.get('new_tables_created_count')}",
        f"3. oxylabs_verified_field_count: {report.get('oxylabs_verified_field_count')}",
        "",
    ]
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}

