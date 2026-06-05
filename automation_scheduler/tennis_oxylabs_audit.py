from __future__ import annotations

from pathlib import Path
from typing import Any

from .tennis_free_vs_paid_readiness import tennis_lane_catalog
from .tennis_oxylabs_common import FINAL_ACTIONABLE_STATES, current_utc, write_json, write_md
from .tennis_safe_source_sampler import build_tennis_safe_source_sample_report
from .tennis_source_exhaustion_query_builder import build_tennis_source_exhaustion_query_plan
from .tennis_source_policy_review import build_tennis_source_policy_matrix, tennis_candidate_source_catalog


REPORT_ROOT = Path("reports")


def _query_index() -> dict[str, list[dict[str, Any]]]:
    return build_tennis_source_exhaustion_query_plan()["lane_query_index"]


def _policy_index(policy_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in policy_matrix.get("policy_matrix_rows") or []}


def _sample_index(sample_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in sample_report.get("sample_rows") or []}


def _lane_final_state(lane: dict[str, Any], policy_row: dict[str, Any], sample_row: dict[str, Any]) -> tuple[str, int]:
    source_final_state = str(policy_row.get("final_state") or "")
    if lane["loader_exists"] and source_final_state != "free_open_backfilled":
        return "free_open_loader_ready_hard_blocked_from_backfill", 0
    if source_final_state == "free_open_metadata_only" and lane["lane_name"] == "player_metadata_handedness_country":
        return "free_open_metadata_only", int(sample_row.get("normalized_records_added", 0) or 0)
    return source_final_state or "unavailable_after_exhaustive_free_search", 0


def build_tennis_oxylabs_source_exhaustion_log(
    *,
    policy_matrix: dict[str, Any] | None = None,
    sample_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_matrix = policy_matrix or build_tennis_source_policy_matrix()
    sample_report = sample_report or build_tennis_safe_source_sample_report(
        policy_matrix=policy_matrix,
        candidate_rows=tennis_candidate_source_catalog(),
    )
    policy_index = _policy_index(policy_matrix)
    sample_index = _sample_index(sample_report)
    query_index = _query_index()
    rows = []
    for lane in tennis_lane_catalog():
        lane_key = f"{lane['sport']}::{lane['lane_name']}"
        query_used = (query_index.get(lane_key) or [{}])[0].get("query") or f"Tennis {lane['lane_name']}"
        policy_row = policy_index.get(lane["source_id"], {})
        sample_row = sample_index.get(lane["source_id"], {})
        final_state, records_added = _lane_final_state(lane, policy_row, sample_row)
        accepted = final_state in {
            "free_open_backfilled",
            "free_open_postmatch_training_only",
            "free_open_metadata_only",
            "manual_import_required",
            "paid_subscription_required",
            "license_terms_unclear",
            "free_open_loader_ready_hard_blocked_from_backfill",
        }
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "query_used": query_used,
                "source_name": lane["candidate_source_name"],
                "source_url_hash": lane["source_url_hash"],
                "domain": lane["source_domain"],
                "source_type": lane["source_type"],
                "oxylabs_used": bool(policy_row.get("oxylabs_used")),
                "oxylabs_transport_used": policy_row.get("oxylabs_transport_used", "hard_blocked"),
                "oxylabs_call_status": "ok" if policy_row.get("oxylabs_calls_successful", 0) else "blocked",
                "oxylabs_calls_attempted": int(policy_row.get("oxylabs_calls_attempted", 0) or 0),
                "oxylabs_calls_successful": int(policy_row.get("oxylabs_calls_successful", 0) or 0),
                "oxylabs_calls_failed": int(policy_row.get("oxylabs_calls_failed", 0) or 0),
                "oxylabs_lanes_tested": 1,
                "policy_status": lane["policy_status"],
                "license_or_terms_note": lane["license_or_terms_note"],
                "accepted_or_rejected": "accepted" if accepted else "rejected",
                "rejection_reason": "" if accepted else str(policy_row.get("exact_blocker_or_allowance") or lane["final_reason"]),
                "fields_it_can_fill": list(lane["fields"]),
                "new_fields_it_could_create": [],
                "sample_attempted": int(sample_row.get("records_tested", 0) or 0) > 0,
                "normalized_records_found": int(sample_row.get("normalized_records_found", 0) or 0) if final_state == "free_open_metadata_only" else 0,
                "normalized_records_added": records_added,
                "final_actionable_state": final_state,
                "oxylabs_not_used_reason": None if policy_row else "policy_row_missing",
                "source_category": lane["free_or_paid_category"],
                "exact_blocker_or_allowance": policy_row.get("exact_blocker_or_allowance") or lane["final_reason"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "TENNIS_OXYLABS_SOURCE_EXHAUSTION_LOG",
        "schema_version": "tennis_oxylabs_source_exhaustion_log_v1",
        "created_at": current_utc(),
        "sport": "tennis",
        "source_candidate_rows": rows,
        "source_candidate_count": len(rows),
        "lanes_tested_count": len(rows),
        "oxylabs_residential_proxy_used": any(row["oxylabs_transport_used"] in {"residential_proxy", "both"} for row in rows),
        "oxylabs_web_scraper_api_used": any(row["oxylabs_transport_used"] in {"web_scraper_api", "both"} for row in rows),
        "oxylabs_total_calls_attempted": sum(int(row["oxylabs_calls_attempted"]) for row in rows),
        "oxylabs_total_calls_successful": sum(int(row["oxylabs_calls_successful"]) for row in rows),
        "oxylabs_total_calls_failed": sum(int(row["oxylabs_calls_failed"]) for row in rows),
        "sources_accepted_count": sum(1 for row in rows if row["accepted_or_rejected"] == "accepted"),
        "sources_rejected_count": sum(1 for row in rows if row["accepted_or_rejected"] == "rejected"),
        "lanes_improved_by_oxylabs": sum(1 for row in rows if row["normalized_records_added"] > 0),
        "lanes_confirmed_paid_required": sum(1 for row in rows if row["final_actionable_state"] == "paid_subscription_required"),
        "lanes_confirmed_manual_import_required": sum(1 for row in rows if row["final_actionable_state"] == "manual_import_required"),
        "lanes_confirmed_policy_blocked": sum(1 for row in rows if row["final_actionable_state"] == "policy_blocked"),
        "lanes_confirmed_terms_blocked": sum(1 for row in rows if row["final_actionable_state"] == "terms_blocked"),
        "lanes_confirmed_license_terms_unclear": sum(1 for row in rows if row["final_actionable_state"] == "license_terms_unclear"),
        "lanes_free_open_backfilled": sum(1 for row in rows if row["final_actionable_state"] == "free_open_backfilled"),
        "lanes_loader_ready_hard_blocked_from_backfill": sum(1 for row in rows if row["final_actionable_state"] == "free_open_loader_ready_hard_blocked_from_backfill"),
        "lanes_paid_subscription_required": sum(1 for row in rows if row["final_actionable_state"] == "paid_subscription_required"),
        "lanes_manual_import_required": sum(1 for row in rows if row["final_actionable_state"] == "manual_import_required"),
        "lanes_policy_blocked": sum(1 for row in rows if row["final_actionable_state"] == "policy_blocked"),
        "lanes_terms_blocked": sum(1 for row in rows if row["final_actionable_state"] == "terms_blocked"),
        "lanes_license_terms_unclear": sum(1 for row in rows if row["final_actionable_state"] == "license_terms_unclear"),
        "lanes_unavailable_after_exhaustive_free_search": sum(1 for row in rows if row["final_actionable_state"] == "unavailable_after_exhaustive_free_search"),
        "lanes_obsolete_or_duplicate": sum(1 for row in rows if row["final_actionable_state"] == "obsolete_or_duplicate"),
        "lanes_with_vague_status": sum(1 for row in rows if row["final_actionable_state"] not in FINAL_ACTIONABLE_STATES),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_tennis_oxylabs_source_exhaustion_log(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "TENNIS_OXYLABS_SOURCE_EXHAUSTION_LOG.json"
    md_path = root / "TENNIS_OXYLABS_SOURCE_EXHAUSTION_LOG.md"
    write_json(json_path, report)
    lines = [
        "# Tennis Oxylabs Source Exhaustion Log",
        "",
        f"1. source_candidate_count: {report.get('source_candidate_count')}",
        f"2. lanes_tested_count: {report.get('lanes_tested_count')}",
        f"3. oxylabs_total_calls_attempted: {report.get('oxylabs_total_calls_attempted')}",
        f"4. oxylabs_total_calls_successful: {report.get('oxylabs_total_calls_successful')}",
        f"5. oxylabs_total_calls_failed: {report.get('oxylabs_total_calls_failed')}",
        "",
        "## Lanes",
    ]
    for row in report.get("source_candidate_rows") or []:
        lines.append(
            f"- {row.get('lane_name')} final={row.get('final_actionable_state')} transport={row.get('oxylabs_transport_used')} records={row.get('normalized_records_added')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_tennis_oxylabs_reclassification_report(*, source_exhaustion_report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = source_exhaustion_report or build_tennis_oxylabs_source_exhaustion_log()
    rows = []
    for row in report.get("source_candidate_rows") or []:
        if row["source_category"] not in {
            "paid_data_subscription_required",
            "policy_blocked",
            "license_terms_unclear",
            "free_open_manual_import_needed",
            "obsolete_or_duplicate",
            "needs_manual_review",
        }:
            continue
        rows.append(
            {
                "sport": row["sport"],
                "lane_name": row["lane_name"],
                "prior_category": row["source_category"],
                "oxylabs_queries_run": 1 if row["oxylabs_transport_used"] != "hard_blocked" else 0,
                "oxylabs_sources_found": 1 if row["oxylabs_transport_used"] != "hard_blocked" else 0,
                "allowed_free_sources_found": 1 if row["final_actionable_state"] in {"manual_import_required", "license_terms_unclear"} else 0,
                "sample_verified": bool(row["sample_attempted"] and row["normalized_records_found"] > 0),
                "normalized_records_found": row["normalized_records_found"],
                "normalized_records_added": row["normalized_records_added"],
                "final_actionable_state": row["final_actionable_state"],
                "paid_still_required": row["final_actionable_state"] == "paid_subscription_required",
                "manual_import_still_required": row["final_actionable_state"] == "manual_import_required",
                "policy_blocker_still_applies": row["final_actionable_state"] == "policy_blocked",
                "exact_reason": row["exact_blocker_or_allowance"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "TENNIS_OXYLABS_RECLASSIFICATION_REPORT",
        "schema_version": "tennis_oxylabs_reclassification_report_v1",
        "created_at": current_utc(),
        "reclassification_rows": rows,
        "reclassification_row_count": len(rows),
        "paid_still_required_count": sum(1 for row in rows if row["paid_still_required"]),
        "manual_import_still_required_count": sum(1 for row in rows if row["manual_import_still_required"]),
        "policy_blocker_still_applies_count": sum(1 for row in rows if row["policy_blocker_still_applies"]),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_tennis_oxylabs_reclassification_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "TENNIS_OXYLABS_RECLASSIFICATION_REPORT.json"
    md_path = root / "TENNIS_OXYLABS_RECLASSIFICATION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Tennis Oxylabs Reclassification Report",
        "",
        f"1. reclassification_row_count: {report.get('reclassification_row_count')}",
        f"2. paid_still_required_count: {report.get('paid_still_required_count')}",
        f"3. manual_import_still_required_count: {report.get('manual_import_still_required_count')}",
        f"4. policy_blocker_still_applies_count: {report.get('policy_blocker_still_applies_count')}",
        "",
        "## Lanes",
    ]
    for row in report.get("reclassification_rows") or []:
        lines.append(f"- {row.get('lane_name')} final={row.get('final_actionable_state')} reason={row.get('exact_reason')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
