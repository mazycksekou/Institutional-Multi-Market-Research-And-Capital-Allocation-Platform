from __future__ import annotations

from pathlib import Path
from typing import Any

from .source_policy_review_common import parse_csv_rows
from .ncaaf_oxylabs_common import REPORT_ROOT, current_utc, fetch_public_page_text, stable_hash, url_hash, write_json, write_md
from .ncaaf_source_policy_review import ncaaf_candidate_source_catalog


ACCEPTED_SAMPLE_DECISIONS = {
    "accepted_for_automated_normalized_backfill",
    "accepted_for_postgame_training_only",
    "accepted_for_metadata_only",
}


def _metadata_row(candidate: dict[str, Any], decision: str) -> list[dict[str, Any]]:
    row: dict[str, Any] = {
        "sport": candidate["sport"],
        "source_id": candidate["source_id"],
        "source_name": candidate["source_name"],
        "source_url_hash": url_hash(candidate["source_url"]),
        "field_group": candidate["field_group"],
        "policy_decision": decision,
        "captured_at": current_utc(),
        "metadata_only": True,
    }
    for field in candidate.get("repo_field_mapping") or []:
        row[field] = f"metadata_only:{field}"
    return [row]


def sample_ncaaf_source(candidate: dict[str, Any], matrix_row: dict[str, Any]) -> dict[str, Any]:
    decision = str(matrix_row.get("path_level_decision") or "")
    if decision not in ACCEPTED_SAMPLE_DECISIONS:
        return {
            "sport": candidate["sport"],
            "source_id": candidate["source_id"],
            "source_name": candidate["source_name"],
            "source_path_hash": stable_hash(candidate["source_path_or_path_pattern"]),
            "policy_decision": decision,
            "sample_scope": "not_sampled_blocked_or_unresolved",
            "records_tested": 0,
            "fields_found": [],
            "repo_fields_mapped": list(candidate.get("repo_field_mapping") or []),
            "normalized_records_found": 0,
            "normalized_records_added": 0,
            "final_action": "not_sampled",
            "sample_rows": [],
        }
    if decision == "accepted_for_metadata_only":
        rows = _metadata_row(candidate, decision)
    elif str(candidate.get("sample_strategy") or "") == "csv_rows" and str(candidate.get("sample_url") or ""):
        response = fetch_public_page_text(
            source_id=candidate["source_id"],
            domain="raw.githubusercontent.com" if "raw.githubusercontent.com" in str(candidate.get("sample_url") or "") else candidate["source_domain"],
            url=str(candidate.get("sample_url") or ""),
            transport="residential_proxy" if str(candidate.get("sample_url") or "").endswith(".csv") else str(candidate.get("primary_transport") or "web_scraper_api"),
            headers={"Accept": "text/csv,text/plain,*/*"},
            timeout=45,
        )
        rows = parse_csv_rows(response.get("text") or "", max_records=3)
    else:
        rows = []
    fields_found = sorted({key for row in rows for key in row.keys()})
    return {
        "sport": candidate["sport"],
        "source_id": candidate["source_id"],
        "source_name": candidate["source_name"],
        "source_path_hash": stable_hash(candidate["source_path_or_path_pattern"]),
        "policy_decision": decision,
        "sample_scope": "tiny_safe_sample" if rows else "no_safe_rows_returned",
        "records_tested": len(rows),
        "fields_found": fields_found,
        "repo_fields_mapped": list(candidate.get("repo_field_mapping") or []),
        "normalized_records_found": len(rows),
        "normalized_records_added": len(rows),
        "final_action": "sampled_and_ready_for_policy_state",
        "sample_rows": rows,
    }


def build_ncaaf_safe_source_sample_report(
    *,
    policy_matrix: dict[str, Any],
    candidate_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidate_rows = candidate_rows or ncaaf_candidate_source_catalog()
    index = {candidate["source_id"]: candidate for candidate in candidate_rows}
    rows = [
        sample_ncaaf_source(index[row["source_id"]], row)
        for row in policy_matrix.get("policy_matrix_rows") or []
        if row.get("source_id") in index
    ]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NCAAF_SAFE_SOURCE_SAMPLE_REPORT",
        "schema_version": "NCAAF_safe_source_sample_report_v1",
        "created_at": current_utc(),
        "sample_rows": rows,
        "sample_row_count": len(rows),
        "sampled_source_count": sum(1 for row in rows if row["records_tested"] > 0),
        "normalized_records_added": sum(int(row["normalized_records_added"]) for row in rows),
        "metadata_only_records_added": sum(int(row["normalized_records_added"]) for row in rows if row["policy_decision"] == "accepted_for_metadata_only"),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_ncaaf_safe_source_sample_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NCAAF_SAFE_SOURCE_SAMPLE_REPORT.json"
    md_path = root / "NCAAF_SAFE_SOURCE_SAMPLE_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# NCAAF Safe Source Sample Report",
        "",
        f"1. sample_row_count: {report.get('sample_row_count')}",
        f"2. sampled_source_count: {report.get('sampled_source_count')}",
        f"3. normalized_records_added: {report.get('normalized_records_added')}",
        f"4. metadata_only_records_added: {report.get('metadata_only_records_added')}",
        "",
        "## Sources",
    ]
    for row in report.get("sample_rows") or []:
        lines.append(f"- {row.get('source_name')} decision={row.get('policy_decision')} records={row.get('records_tested')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}



