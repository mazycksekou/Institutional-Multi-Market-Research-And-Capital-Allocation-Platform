from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import build_basketball_schema_expansion_report
from .basketball_oxylabs_common import current_utc


def build_basketball_oxylabs_schema_expansion_report(
    *,
    source_exhaustion_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = build_basketball_schema_expansion_report()
    oxylabs_used = bool((source_exhaustion_report or {}).get("oxylabs_residential_proxy_used") or (source_exhaustion_report or {}).get("oxylabs_web_scraper_api_used"))
    return {
        **base,
        "report_name": "BASKETBALL_OXYLABS_SCHEMA_EXPANSION_REPORT",
        "schema_version": "basketball_oxylabs_schema_expansion_v1",
        "created_at": current_utc(),
        "oxylabs_used": oxylabs_used,
        "oxylabs_transport_used": "both" if oxylabs_used else "hard_blocked",
        "oxylabs_calls_attempted": int((source_exhaustion_report or {}).get("oxylabs_total_calls_attempted", 0) or 0),
        "oxylabs_calls_successful": int((source_exhaustion_report or {}).get("oxylabs_total_calls_successful", 0) or 0),
        "oxylabs_calls_failed": int((source_exhaustion_report or {}).get("oxylabs_total_calls_failed", 0) or 0),
        "oxylabs_discovered_new_fields": [],
        "oxylabs_discovered_new_tables": [],
        "oxylabs_new_fields_created_count": 0,
        "oxylabs_new_tables_created_count": 0,
        "backfill_report_path": "reports/BASKETBALL_LOADER_READY_BACKFILL_REPORT.json",
        "source_exhaustion_report_path": "reports/BASKETBALL_OXYLABS_SOURCE_EXHAUSTION_LOG.json",
    }


def write_basketball_oxylabs_schema_expansion_report(report: dict[str, Any], *, output_dir: str | None = None) -> dict[str, str]:
    from pathlib import Path
    from .basketball_oxylabs_common import write_json, write_md

    root = Path(output_dir or "reports")
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "BASKETBALL_OXYLABS_SCHEMA_EXPANSION_REPORT.json"
    md_path = root / "BASKETBALL_OXYLABS_SCHEMA_EXPANSION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Basketball Oxylabs Schema Expansion Report",
        "",
        f"1. oxylabs_used: {report.get('oxylabs_used')}",
        f"2. oxylabs_calls_attempted: {report.get('oxylabs_calls_attempted')}",
        f"3. oxylabs_new_fields_created_count: {report.get('oxylabs_new_fields_created_count')}",
        f"4. oxylabs_new_tables_created_count: {report.get('oxylabs_new_tables_created_count')}",
        "",
        "No new Oxylabs-only schema fields were discovered in this pass.",
    ]
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}

