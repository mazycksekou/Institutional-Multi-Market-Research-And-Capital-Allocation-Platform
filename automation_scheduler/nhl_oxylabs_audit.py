from __future__ import annotations

from pathlib import Path
from typing import Any

from .nhl_free_data_loader import load_nhl_lane_records
from .nhl_free_vs_paid_readiness import _new_fields_for_lane, nhl_lane_catalog
from .nhl_oxylabs_common import (
    FINAL_ACTIONABLE_STATES,
    current_utc,
    discover_nhl_sample_context,
    fetch_public_page_text,
    lane_final_state,
    lane_source_spec,
    write_json,
    write_md,
)
from .nhl_oxylabs_source_policy import evaluate_nhl_oxylabs_source_policy
from .nhl_source_exhaustion_query_builder import build_nhl_source_exhaustion_query_plan


REPORT_ROOT = Path("reports")


def _query_index() -> dict[str, list[dict[str, Any]]]:
    return build_nhl_source_exhaustion_query_plan()["lane_query_index"]


def _official_page_confirmation() -> dict[str, Any]:
    context = discover_nhl_sample_context()
    game_id = int(context.get("sample_game_id") or 0)
    if not game_id:
        return {"ok": False, "status": "blocked", "blocked_reason": "no_public_page_or_endpoint_exists_after_oxylabs_search"}
    return fetch_public_page_text(
        source_id="nhl_official_gamecenter_page",
        domain="api-web.nhle.com",
        url=f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing",
        transport="web_scraper_api",
    )


def _lane_candidate_row(lane: dict[str, Any], query_index: dict[str, list[dict[str, Any]]], official_page: dict[str, Any], *, cache: dict[str, Any]) -> dict[str, Any]:
    lane_key = f"{lane['sport']}::{lane['lane_name']}"
    query_used = (query_index.get(lane_key) or [{}])[0].get("query") or f"NHL {lane['lane_name']}"
    source_spec = lane_source_spec(lane)
    policy = evaluate_nhl_oxylabs_source_policy(
        source_id=source_spec.source_id,
        domain=source_spec.domain,
        transport=source_spec.transport,
        allow_oxylabs=True,
        allow_paid_retrieval=True,
        source_type=source_spec.source_type,
    )
    if lane["free_or_paid_category"] in {"blocked_reference_or_restricted_source", "policy_blocked"}:
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "query_used": query_used,
            "source_name": source_spec.source_name,
            "source_url_hash": lane["source_url_hash"],
            "domain": source_spec.domain,
            "source_type": source_spec.source_type,
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_call_status": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "oxylabs_lanes_tested": 1,
            "policy_status": "blocked_reference_site",
            "license_or_terms_note": source_spec.license_or_terms_note,
            "accepted_or_rejected": "rejected",
            "rejection_reason": "hard_policy_blocker",
            "fields_it_can_fill": list(lane["fields"]),
            "new_fields_it_could_create": [],
            "sample_attempted": False,
            "normalized_records_found": 0,
            "normalized_records_added": 0,
            "final_actionable_state": "policy_blocked",
            "oxylabs_not_used_reason": "hard_policy_blocker",
            "source_category": lane["free_or_paid_category"],
        }
    if lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}:
        result = load_nhl_lane_records(lane, cache=cache)
        sample_attempted = True
        accepted = bool(result.get("ok"))
        final_state = lane_final_state(lane, backfill_written=accepted, hard_blocked=not accepted)
        web_ok = bool(official_page.get("ok"))
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "query_used": query_used,
            "source_name": result.get("source_name") or source_spec.source_name,
            "source_url_hash": lane["source_url_hash"],
            "domain": source_spec.domain,
            "source_type": source_spec.source_type,
            "oxylabs_used": True,
            "oxylabs_transport_used": "both" if web_ok else "residential_proxy",
            "oxylabs_call_status": "ok" if accepted else "blocked",
            "oxylabs_calls_attempted": int(result.get("oxylabs_calls_attempted", 0) or 0) + 1,
            "oxylabs_calls_successful": int(result.get("oxylabs_calls_successful", 0) or 0) + (1 if web_ok else 0),
            "oxylabs_calls_failed": int(result.get("oxylabs_calls_failed", 0) or 0) + (0 if web_ok else 1),
            "oxylabs_lanes_tested": 1,
            "policy_status": policy.get("policy_status"),
            "license_or_terms_note": source_spec.license_or_terms_note,
            "accepted_or_rejected": "accepted" if accepted else "rejected",
            "rejection_reason": "" if accepted else str(result.get("blocked_reason") or "retrieval_failed_after_documented_attempts"),
            "fields_it_can_fill": list(lane["fields"]),
            "new_fields_it_could_create": list(_new_fields_for_lane(lane)),
            "sample_attempted": sample_attempted,
            "normalized_records_found": int(result.get("normalized_record_count", 0) or 0),
            "normalized_records_added": int(result.get("normalized_record_count", 0) or 0),
            "final_actionable_state": final_state,
            "oxylabs_not_used_reason": None,
            "source_category": lane["free_or_paid_category"],
        }
    page_fetch = fetch_public_page_text(
        source_id=source_spec.source_id,
        domain=source_spec.domain,
        url=source_spec.url,
        transport=source_spec.transport,
    )
    if lane["free_or_paid_category"] == "free_open_manual_import_needed":
        final_state = "manual_import_required"
        accepted = True
        rejection_reason = ""
    elif lane["free_or_paid_category"] == "paid_data_subscription_required":
        final_state = "paid_subscription_required"
        accepted = True
        rejection_reason = ""
    elif lane["free_or_paid_category"] == "license_terms_unclear":
        final_state = "license_terms_unclear"
        accepted = True
        rejection_reason = ""
    else:
        final_state = "obsolete_or_duplicate"
        accepted = False
        rejection_reason = "duplicate_or_obsolete"
    return {
        "sport": lane["sport"],
        "lane_name": lane["lane_name"],
        "query_used": query_used,
        "source_name": source_spec.source_name,
        "source_url_hash": lane["source_url_hash"],
        "domain": source_spec.domain,
        "source_type": source_spec.source_type,
        "oxylabs_used": True,
        "oxylabs_transport_used": source_spec.transport,
        "oxylabs_call_status": "ok" if page_fetch.get("ok") else "blocked",
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1 if page_fetch.get("ok") else 0,
        "oxylabs_calls_failed": 0 if page_fetch.get("ok") else 1,
        "oxylabs_lanes_tested": 1,
        "policy_status": policy.get("policy_status"),
        "license_or_terms_note": source_spec.license_or_terms_note,
        "accepted_or_rejected": "accepted" if accepted else "rejected",
        "rejection_reason": rejection_reason,
        "fields_it_can_fill": list(lane["fields"]),
        "new_fields_it_could_create": list(_new_fields_for_lane(lane)),
        "sample_attempted": False,
        "normalized_records_found": 0,
        "normalized_records_added": 0,
        "final_actionable_state": final_state,
        "oxylabs_not_used_reason": None,
        "source_category": lane["free_or_paid_category"],
    }


def build_nhl_oxylabs_source_exhaustion_log() -> dict[str, Any]:
    query_index = _query_index()
    official_page = _official_page_confirmation()
    cache: dict[str, Any] = {}
    rows = [_lane_candidate_row(lane, query_index, official_page, cache=cache) for lane in nhl_lane_catalog()]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_OXYLABS_SOURCE_EXHAUSTION_LOG",
        "schema_version": "nhl_oxylabs_source_exhaustion_log_v1",
        "created_at": current_utc(),
        "sport": "icehockey_nhl",
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
        "lanes_confirmed_terms_unclear": sum(1 for row in rows if row["final_actionable_state"] == "license_terms_unclear"),
        "lanes_free_open_backfilled": sum(1 for row in rows if row["final_actionable_state"] == "free_open_backfilled"),
        "lanes_loader_ready_hard_blocked_from_backfill": sum(1 for row in rows if row["final_actionable_state"] == "free_open_loader_ready_hard_blocked_from_backfill"),
        "lanes_paid_subscription_required": sum(1 for row in rows if row["final_actionable_state"] == "paid_subscription_required"),
        "lanes_manual_import_required": sum(1 for row in rows if row["final_actionable_state"] == "manual_import_required"),
        "lanes_policy_blocked": sum(1 for row in rows if row["final_actionable_state"] == "policy_blocked"),
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


def write_nhl_oxylabs_source_exhaustion_log(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_OXYLABS_SOURCE_EXHAUSTION_LOG.json"
    md_path = root / "NHL_OXYLABS_SOURCE_EXHAUSTION_LOG.md"
    write_json(json_path, report)
    lines = [
        "# NHL Oxylabs Source Exhaustion Log",
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


def build_nhl_oxylabs_reclassification_report(*, source_exhaustion_report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = source_exhaustion_report or build_nhl_oxylabs_source_exhaustion_log()
    rows = []
    for row in report.get("source_candidate_rows") or []:
        if row["source_category"] not in {
            "paid_data_subscription_required",
            "blocked_reference_or_restricted_source",
            "license_terms_unclear",
            "free_open_manual_import_needed",
            "obsolete_or_duplicate",
        }:
            continue
        rows.append(
            {
                "sport": row["sport"],
                "lane_name": row["lane_name"],
                "prior_category": row["source_category"],
                "oxylabs_queries_run": 1 if row["oxylabs_transport_used"] != "hard_blocked" else 0,
                "oxylabs_sources_found": 1 if row["oxylabs_transport_used"] != "hard_blocked" else 0,
                "allowed_free_sources_found": 1 if row["accepted_or_rejected"] == "accepted" and row["final_actionable_state"] in {"manual_import_required", "license_terms_unclear"} else 0,
                "sample_verified": bool(row["sample_attempted"] and row["normalized_records_found"] > 0),
                "normalized_records_found": row["normalized_records_found"],
                "normalized_records_added": row["normalized_records_added"],
                "final_actionable_state": row["final_actionable_state"],
                "paid_still_required": row["final_actionable_state"] == "paid_subscription_required",
                "manual_import_still_required": row["final_actionable_state"] == "manual_import_required",
                "policy_blocker_still_applies": row["final_actionable_state"] == "policy_blocked",
                "exact_reason": row["rejection_reason"] or row["license_or_terms_note"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_OXYLABS_RECLASSIFICATION_REPORT",
        "schema_version": "nhl_oxylabs_reclassification_report_v1",
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


def write_nhl_oxylabs_reclassification_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_OXYLABS_RECLASSIFICATION_REPORT.json"
    md_path = root / "NHL_OXYLABS_RECLASSIFICATION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# NHL Oxylabs Reclassification Report",
        "",
        f"1. reclassification_row_count: {report.get('reclassification_row_count')}",
        f"2. paid_still_required_count: {report.get('paid_still_required_count')}",
        f"3. manual_import_still_required_count: {report.get('manual_import_still_required_count')}",
        f"4. policy_blocker_still_applies_count: {report.get('policy_blocker_still_applies_count')}",
        "",
        "## Lanes",
    ]
    for row in report.get("reclassification_rows") or []:
        lines.append(
            f"- {row.get('lane_name')} final={row.get('final_actionable_state')} reason={row.get('exact_reason')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
