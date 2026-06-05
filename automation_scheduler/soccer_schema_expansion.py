from __future__ import annotations

from pathlib import Path
from typing import Any

from .soccer_free_vs_paid_readiness import _new_fields_for_lane, soccer_lane_catalog
from .soccer_oxylabs_common import current_utc, write_json, write_md
from .soccer_sample_verifier import build_soccer_targeted_sample_verification_results


REPORT_ROOT = Path("reports")


def _sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not sample_verification_results:
        sample_verification_results = build_soccer_targeted_sample_verification_results()
    return dict(sample_verification_results.get("source_result_index") or {})


def _schema_entry(lane: dict[str, Any], field_name: str, sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "sport": lane["sport"],
        "league_or_competition": "Bundesliga",
        "field_name": field_name,
        "description": f"{field_name} derived from {lane['field_or_feature_group']} for Soccer",
        "entity_level": lane["entity_level"],
        "table": lane["table"],
        "data_type": "boolean" if field_name.endswith(("_flag", "_context")) else "float" if field_name.endswith(("_rate", "_rating", "_strength", "_days", "_distance", "_tendency")) else "string",
        "source_id": lane["source_id"],
        "source_url_hash": sample.get("source_url_hash") or lane["source_url_hash"],
        "retrieval_method": lane["retrieval_method"],
        "license_or_terms_note": lane["license_or_terms_note"],
        "validation_status": sample.get("validation_status", "sample_verified"),
        "coverage_start": lane["coverage_start"],
        "coverage_end": lane["coverage_end"],
        "cutoff_safe": lane["cutoff_safe"],
        "future_leakage_risk": lane["future_leakage_risk"],
        "model_eligible": lane["model_eligible"],
        "confidence": "high" if sample.get("validation_status") == "sample_verified" else "medium",
        "field_catalog_entry": {"module": lane["module"], "table": lane["table"], "field_name": field_name, "source_family": lane["source_family"]},
        "tests": ["tests/test_soccer_schema_expansion.py"],
        "report_entry": True,
    }


def build_soccer_schema_expansion_report(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _sample_index(sample_verification_results)
    entries = []
    for lane in soccer_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        if sample.get("validation_status") != "sample_verified":
            continue
        for field in _new_fields_for_lane(lane):
            entries.append(_schema_entry(lane, field, sample))
    tables = sorted({entry["table"] for entry in entries})
    return {
        "ok": True,
        "status": "ok",
        "report_name": "SOCCER_SCHEMA_EXPANSION_REPORT",
        "schema_version": "soccer_schema_expansion_v1",
        "created_at": current_utc(),
        "sport": "soccer",
        "new_fields_created": entries,
        "new_fields_created_count": len(entries),
        "new_tables_created": tables,
        "new_tables_created_count": len(tables),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def write_soccer_schema_expansion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "SOCCER_SCHEMA_EXPANSION_REPORT.json"
    md_path = root / "SOCCER_SCHEMA_EXPANSION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Soccer Schema Expansion Report",
        "",
        f"1. new_fields_created_count: {report.get('new_fields_created_count')}",
        f"2. new_tables_created_count: {report.get('new_tables_created_count')}",
        "",
        "## Fields",
    ]
    for row in report.get("new_fields_created") or []:
        lines.append(f"- {row.get('field_name')} table={row.get('table')} validation={row.get('validation_status')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
