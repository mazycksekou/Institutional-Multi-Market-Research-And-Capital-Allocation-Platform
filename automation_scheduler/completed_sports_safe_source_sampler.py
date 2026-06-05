from __future__ import annotations

from typing import Any

from .source_policy_review_common import current_utc, fetch_public_json, fetch_public_page_text, parse_csv_rows, stable_hash, url_hash


ACCEPTED_SAMPLE_DECISIONS = {
    "accepted_for_automated_normalized_backfill",
    "accepted_for_postmatch_training_only",
    "accepted_for_metadata_only",
}


def _metadata_row(candidate: dict[str, Any], decision: str) -> list[dict[str, Any]]:
    return [
        {
            "sport": candidate["sport"],
            "source_id": candidate["source_id"],
            "source_name": candidate["source_name"],
            "source_url_hash": url_hash(candidate["source_url"]),
            "field_group": candidate["field_group"],
            "policy_decision": decision,
            "captured_at": current_utc(),
            "repo_field_mapping_count": len(candidate.get("repo_field_mapping") or []),
            "required_attribution_text_or_url_hash": candidate.get("required_attribution_text_or_url_hash"),
            "metadata_only": True,
        }
    ]


def sample_completed_sports_source(candidate: dict[str, Any], matrix_row: dict[str, Any]) -> dict[str, Any]:
    decision = str(matrix_row.get("path_level_decision") or "")
    if decision not in ACCEPTED_SAMPLE_DECISIONS:
        return {
            "sport": candidate["sport"],
            "source_name": candidate["source_name"],
            "source_path_hash": stable_hash(candidate["source_path_or_path_pattern"]),
            "policy_decision": decision,
            "sample_scope": "not_sampled_blocked_or_unresolved",
            "records_tested": 0,
            "fields_found": [],
            "repo_fields_mapped": list(candidate.get("repo_field_mapping") or []),
            "cutoff_safe": bool(candidate.get("cutoff_safe")),
            "prematch_eligible": bool(candidate.get("usable_for_prematch_model")),
            "postmatch_training_only": bool(candidate.get("usable_for_postmatch_training_only")),
            "normalized_records_found": 0,
            "normalized_records_added": 0,
            "duplicate_status": "duplicate" if candidate.get("duplicate_existing_source") else "not_duplicate",
            "calibration_value": candidate.get("expected_calibration_value"),
            "final_action": "not_sampled",
            "sample_rows": [],
        }
    strategy = str(candidate.get("sample_strategy") or "none")
    sample_url = str(candidate.get("sample_url") or candidate.get("source_url") or "")
    transport = "residential_proxy" if sample_url.endswith(".csv") or sample_url.endswith(".json") or "/api/" in sample_url else candidate.get("primary_transport", "web_scraper_api")
    rows: list[dict[str, Any]] = []
    if strategy == "csv_rows":
        response = fetch_public_page_text(
            source_id=candidate["source_id"],
            domain=candidate["source_domain"],
            url=sample_url,
            transport=transport,
            headers={"Accept": "text/csv,text/plain,*/*"},
            timeout=45,
        )
        rows = parse_csv_rows(response.get("text") or "", max_records=3)
    elif strategy == "json_list":
        response = fetch_public_json(
            source_id=candidate["source_id"],
            domain=candidate["source_domain"],
            url=sample_url,
            transport=transport,
            timeout=45,
        )
        payload = response.get("json_payload") or []
        if isinstance(payload, list):
            for row in payload[:3]:
                if isinstance(row, dict):
                    rows.append(row)
    else:
        rows = _metadata_row(candidate, decision)
    fields_found = sorted({key for row in rows for key in row.keys()})
    return {
        "sport": candidate["sport"],
        "source_name": candidate["source_name"],
        "source_path_hash": stable_hash(candidate["source_path_or_path_pattern"]),
        "policy_decision": decision,
        "sample_scope": "tiny_safe_sample" if rows else "no_safe_rows_returned",
        "records_tested": len(rows),
        "fields_found": fields_found,
        "repo_fields_mapped": list(candidate.get("repo_field_mapping") or []),
        "cutoff_safe": bool(candidate.get("cutoff_safe")),
        "prematch_eligible": bool(candidate.get("usable_for_prematch_model")),
        "postmatch_training_only": bool(candidate.get("usable_for_postmatch_training_only")),
        "normalized_records_found": len(rows),
        "normalized_records_added": len(rows),
        "duplicate_status": "duplicate" if candidate.get("duplicate_existing_source") else "not_duplicate",
        "calibration_value": candidate.get("expected_calibration_value"),
        "final_action": "sampled_and_ready_for_safe_state",
        "sample_rows": rows,
    }


def build_completed_sports_accepted_source_sample_report(
    *,
    policy_matrix: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    index = {candidate["source_id"]: candidate for candidate in candidate_rows}
    rows = [
        sample_completed_sports_source(index[row["source_id"]], row)
        for row in policy_matrix.get("policy_matrix_rows") or []
        if row.get("source_id") in index
    ]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_ACCEPTED_SOURCE_SAMPLE_REPORT",
        "schema_version": "completed_sports_accepted_source_sample_report_v1",
        "created_at": current_utc(),
        "sample_rows": rows,
        "sample_row_count": len(rows),
        "sampled_source_count": sum(1 for row in rows if row["records_tested"] > 0),
        "normalized_records_added": sum(int(row["normalized_records_added"]) for row in rows),
        "postmatch_training_records_added": sum(int(row["normalized_records_added"]) for row in rows if row["postmatch_training_only"]),
        "metadata_only_records_added": sum(int(row["normalized_records_added"]) for row in rows if row["policy_decision"] == "accepted_for_metadata_only"),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }

