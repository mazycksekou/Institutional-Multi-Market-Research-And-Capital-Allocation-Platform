from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .basketball_free_vs_paid_readiness import SPORTS, _new_fields_for_lane, basketball_lane_catalog
from .basketball_oxylabs_common import (
    FINAL_ACTIONABLE_STATES,
    current_utc,
    fetch_public_page_text,
    fetch_release_asset_rows,
    json_safe,
    lane_final_state,
    lane_source_spec,
    partial_lanes,
    read_json,
    release_page_url,
    stable_hash,
    unresolved_lanes,
    url_hash,
    write_json,
    write_md,
)
from .basketball_oxylabs_source_policy import evaluate_basketball_oxylabs_source_policy
from .basketball_source_exhaustion_query_builder import build_basketball_source_exhaustion_query_plan


REPORT_ROOT = Path("reports")


def _lane_query_index(sport: str | None = None) -> dict[str, dict[str, Any]]:
    plan = build_basketball_source_exhaustion_query_plan(sport=sport)
    return plan["lane_query_index"]


def _release_page_fetch() -> dict[str, Any]:
    return fetch_public_page_text(
        source_id="basketball_release_page",
        domain="github.com",
        url=release_page_url(),
        transport="web_scraper_api",
    )


def _lane_candidate_row(lane: dict[str, Any], query_index: dict[str, dict[str, Any]], release_page: dict[str, Any]) -> dict[str, Any]:
    lane_key = f"{lane['sport']}::{lane['lane_name']}"
    query_used = (query_index.get(lane_key) or [{}])[0].get("query") or f"{lane['sport']} {lane['lane_name']} data"
    source_spec = lane_source_spec(lane)
    policy = evaluate_basketball_oxylabs_source_policy(
        source_id=source_spec.source_id,
        domain=source_spec.domain,
        transport=source_spec.transport,
        allow_oxylabs=True,
        allow_paid_retrieval=True,
        source_type=source_spec.source_type,
    )
    allowed = bool(policy.get("allowed"))
    hard_blocked = lane["free_or_paid_category"] in {"blocked_reference_or_restricted_source", "policy_blocked"}
    if hard_blocked:
        return {
            "sport": lane["sport"],
            "lane_name": lane["lane_name"],
            "field_or_feature_group": lane["field_or_feature_group"],
            "query_used": query_used,
            "source_name": source_spec.source_name,
            "source_url_hash": url_hash(source_spec.url),
            "domain": source_spec.domain,
            "source_type": source_spec.source_type,
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_call_status": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "policy_status": "blocked_reference_site",
            "license_or_terms_note": source_spec.license_or_terms_note,
            "accepted_or_rejected": "rejected",
            "rejection_reason": "hard_policy_blocker",
            "fields_it_can_fill": list(lane.get("fields") or []),
            "new_fields_it_could_create": list(_new_fields_for_lane(lane)),
            "sample_attempted": False,
            "normalized_records_found": 0,
            "normalized_records_added": 0,
            "final_actionable_state": "policy_blocked",
            "oxylabs_not_used_reason": "hard_policy_blocker",
            "source_category": lane["free_or_paid_category"],
        }
    lane_state = lane_final_state(lane, backfill_written=lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}, hard_blocked=False)
    if lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}:
        asset_rows = fetch_release_asset_rows(
            tag=str((lane.get("sample") or {}).get("release_tag") or ""),
            asset_name=str((lane.get("sample") or {}).get("asset_name") or ""),
            max_bytes=250_000,
            max_records=10,
        )
        records_found = int(asset_rows.get("record_count", 0) or 0)
        records_added = min(records_found, 10)
        transport_used = "both" if release_page.get("ok") else "residential_proxy"
        call_attempted = 2 if release_page.get("ok") else 1
        call_success = 2 if release_page.get("ok") else 1
        call_failed = 0
        call_status = "ok" if call_success else "blocked"
        if bool(asset_rows.get("ok")) and records_found > 0:
            accepted = True
            rejection_reason = ""
            normalized_state = "free_open_backfilled"
            not_used_reason = None
        else:
            accepted = False
            rejection_reason = "no_free_records_found"
            normalized_state = "unavailable_after_exhaustive_free_search"
            not_used_reason = "no_free_records_found"
        sample_attempted = True
    elif lane["free_or_paid_category"] == "license_terms_unclear":
        page_fetch = fetch_public_page_text(
            source_id=source_spec.source_id,
            domain=source_spec.domain,
            url=source_spec.url,
            transport=source_spec.transport,
            allowed_domains=(source_spec.domain, f"*.{source_spec.domain}"),
            allowed_source_ids=(source_spec.source_id,),
        )
        records_found = 0
        records_added = 0
        transport_used = "both" if release_page.get("ok") else source_spec.transport
        call_attempted = 2 if release_page.get("ok") else 1
        call_success = 2 if release_page.get("ok") and page_fetch.get("ok") else 1 if page_fetch.get("ok") else 0
        call_failed = max(0, call_attempted - call_success)
        call_status = "ok" if call_success else "blocked"
        accepted = True
        rejection_reason = ""
        normalized_state = "license_terms_unclear"
        not_used_reason = None
        sample_attempted = True
    elif lane["free_or_paid_category"] == "free_open_manual_import_needed":
        page_fetch = fetch_public_page_text(
            source_id=source_spec.source_id,
            domain=source_spec.domain,
            url=source_spec.url,
            transport=source_spec.transport,
            allowed_domains=(source_spec.domain, f"*.{source_spec.domain}") if source_spec.domain else None,
            allowed_source_ids=(source_spec.source_id,),
        )
        records_found = 0
        records_added = 0
        transport_used = "both" if release_page.get("ok") else source_spec.transport
        call_attempted = 2 if release_page.get("ok") else 1
        call_success = 2 if release_page.get("ok") and page_fetch.get("ok") else 1 if page_fetch.get("ok") else 0
        call_failed = max(0, call_attempted - call_success)
        call_status = "ok" if call_success else "blocked"
        accepted = True
        rejection_reason = ""
        normalized_state = "manual_import_required"
        not_used_reason = None
        sample_attempted = True
    elif lane["free_or_paid_category"] == "paid_data_subscription_required":
        page_fetch = fetch_public_page_text(
            source_id=source_spec.source_id,
            domain=source_spec.domain,
            url=source_spec.url,
            transport=source_spec.transport,
            allowed_domains=(source_spec.domain, f"*.{source_spec.domain}") if source_spec.domain else None,
            allowed_source_ids=(source_spec.source_id,),
        )
        records_found = 0
        records_added = 0
        transport_used = "both" if release_page.get("ok") else source_spec.transport
        call_attempted = 2 if release_page.get("ok") else 1
        call_success = 2 if release_page.get("ok") and page_fetch.get("ok") else 1 if page_fetch.get("ok") else 0
        call_failed = max(0, call_attempted - call_success)
        call_status = "ok" if call_success else "blocked"
        accepted = True
        rejection_reason = ""
        normalized_state = "paid_subscription_required"
        not_used_reason = None
        sample_attempted = True
    elif lane["free_or_paid_category"] == "obsolete_or_duplicate":
        page_fetch = fetch_public_page_text(
            source_id=source_spec.source_id,
            domain=source_spec.domain,
            url=source_spec.url,
            transport=source_spec.transport,
            allowed_domains=(source_spec.domain, f"*.{source_spec.domain}") if source_spec.domain else None,
            allowed_source_ids=(source_spec.source_id,),
        )
        records_found = 0
        records_added = 0
        transport_used = "both" if release_page.get("ok") else source_spec.transport
        call_attempted = 2 if release_page.get("ok") else 1
        call_success = 2 if release_page.get("ok") and page_fetch.get("ok") else 1 if page_fetch.get("ok") else 0
        call_failed = max(0, call_attempted - call_success)
        call_status = "ok" if call_success else "blocked"
        accepted = False
        rejection_reason = "duplicate_or_obsolete"
        normalized_state = "obsolete_or_duplicate"
        not_used_reason = None
        sample_attempted = True
    else:
        page_fetch = fetch_public_page_text(
            source_id=source_spec.source_id,
            domain=source_spec.domain,
            url=source_spec.url,
            transport=source_spec.transport,
            allowed_domains=(source_spec.domain, f"*.{source_spec.domain}") if source_spec.domain else None,
            allowed_source_ids=(source_spec.source_id,),
        )
        records_found = int(page_fetch.get("text_length", 0) > 0)
        records_added = 0
        transport_used = source_spec.transport
        call_attempted = 1
        call_success = 1 if page_fetch.get("ok") else 0
        call_failed = 0 if page_fetch.get("ok") else 1
        call_status = "ok" if page_fetch.get("ok") else "blocked"
        accepted = bool(allowed)
        rejection_reason = "" if accepted else str(policy.get("blocked_reason") or "rejected")
        normalized_state = lane_state
        not_used_reason = None if accepted else str(policy.get("blocked_reason") or "blocked")
        sample_attempted = bool(allowed)
    return {
        "sport": lane["sport"],
        "lane_name": lane["lane_name"],
        "field_or_feature_group": lane["field_or_feature_group"],
        "query_used": query_used,
        "source_name": source_spec.source_name,
        "source_url_hash": url_hash(source_spec.url),
        "domain": source_spec.domain,
        "source_type": source_spec.source_type,
        "oxylabs_used": bool(allowed),
        "oxylabs_transport_used": transport_used,
        "oxylabs_call_status": call_status,
        "oxylabs_calls_attempted": call_attempted,
        "oxylabs_calls_successful": call_success,
        "oxylabs_calls_failed": call_failed,
        "policy_status": policy.get("policy_status"),
        "license_or_terms_note": source_spec.license_or_terms_note,
        "accepted_or_rejected": "accepted" if accepted else "rejected",
        "rejection_reason": rejection_reason,
        "fields_it_can_fill": list(lane.get("fields") or []),
        "new_fields_it_could_create": list(_new_fields_for_lane(lane)),
        "sample_attempted": sample_attempted,
        "normalized_records_found": records_found,
        "normalized_records_added": records_added,
        "final_actionable_state": normalized_state,
        "oxylabs_not_used_reason": not_used_reason,
        "source_category": lane["free_or_paid_category"],
    }


def build_basketball_oxylabs_source_exhaustion_log(*, sport: str | None = None) -> dict[str, Any]:
    query_index = _lane_query_index(sport=sport)
    release_page = _release_page_fetch()
    lanes = basketball_lane_catalog()
    if sport:
        lanes = [lane for lane in lanes if lane["sport"] == sport]
    rows = [_lane_candidate_row(lane, query_index, release_page) for lane in lanes]
    by_sport: dict[str, dict[str, Any]] = {}
    for sport_key in SPORTS:
        sport_rows = [row for row in rows if row["sport"] == sport_key]
        if not sport_rows:
            continue
        by_sport[sport_key] = {
            "lanes_tested": len(sport_rows),
            "oxylabs_used_count": sum(1 for row in sport_rows if row["oxylabs_used"]),
            "hard_blocked_count": sum(1 for row in sport_rows if row["oxylabs_transport_used"] == "hard_blocked"),
            "records_found": sum(int(row["normalized_records_found"]) for row in sport_rows),
            "records_added": sum(int(row["normalized_records_added"]) for row in sport_rows),
        }
    return {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_OXYLABS_SOURCE_EXHAUSTION_LOG",
        "schema_version": "basketball_oxylabs_source_exhaustion_log_v1",
        "created_at": current_utc(),
        "sport": sport or "all_basketball",
        "sports_included": [sport] if sport else list(SPORTS),
        "source_exhaustion_log_entries": rows,
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
        "source_families_checked": sorted({str(row["source_type"]) for row in rows}),
        "query_families_checked": sorted({str(row["query_used"])[:64] for row in rows}),
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
        "by_sport": by_sport,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_basketball_oxylabs_source_exhaustion_log(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "BASKETBALL_OXYLABS_SOURCE_EXHAUSTION_LOG.json"
    md_path = root / "BASKETBALL_OXYLABS_SOURCE_EXHAUSTION_LOG.md"
    write_json(json_path, report)
    lines = [
        "# Basketball Oxylabs Source Exhaustion Log",
        "",
        f"1. source_candidate_count: {report.get('source_candidate_count')}",
        f"2. lanes_tested_count: {report.get('lanes_tested_count')}",
        f"3. oxylabs_total_calls_attempted: {report.get('oxylabs_total_calls_attempted')}",
        f"4. oxylabs_total_calls_successful: {report.get('oxylabs_total_calls_successful')}",
        f"5. oxylabs_total_calls_failed: {report.get('oxylabs_total_calls_failed')}",
        f"6. lanes_improved_by_oxylabs: {report.get('lanes_improved_by_oxylabs')}",
        "",
        "## Candidates",
    ]
    for row in report.get("source_candidate_rows") or []:
        lines.append(
            f"- {row.get('sport')}::{row.get('lane_name')} {row.get('accepted_or_rejected')} state={row.get('final_actionable_state')} transport={row.get('oxylabs_transport_used')} records_added={row.get('normalized_records_added')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_basketball_oxylabs_reclassification_report(*, source_exhaustion_report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = source_exhaustion_report or build_basketball_oxylabs_source_exhaustion_log()
    rows = []
    for row in report.get("source_candidate_rows") or []:
        if row["source_category"] not in {
            "paid_data_subscription_required",
            "policy_blocked",
            "license_terms_unclear",
            "free_open_manual_import_needed",
            "obsolete_or_duplicate",
            "blocked_reference_or_restricted_source",
        }:
            continue
        rows.append(
            {
                "sport": row["sport"],
                "lane_name": row["lane_name"],
                "prior_category": row["source_category"],
                "oxylabs_queries_run": 1 if row["oxylabs_used"] else 0,
                "oxylabs_sources_found": 1 if row["oxylabs_used"] else 0,
                "allowed_free_sources_found": 1 if row["accepted_or_rejected"] == "accepted" and row["oxylabs_used"] else 0,
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
        "report_name": "BASKETBALL_OXYLABS_RECLASSIFICATION_REPORT",
        "schema_version": "basketball_oxylabs_reclassification_report_v1",
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


def write_basketball_oxylabs_reclassification_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "BASKETBALL_OXYLABS_RECLASSIFICATION_REPORT.json"
    md_path = root / "BASKETBALL_OXYLABS_RECLASSIFICATION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Basketball Oxylabs Reclassification Report",
        "",
        f"1. reclassification_row_count: {report.get('reclassification_row_count')}",
        f"2. paid_still_required_count: {report.get('paid_still_required_count')}",
        f"3. manual_import_still_required_count: {report.get('manual_import_still_required_count')}",
        f"4. policy_blocker_still_applies_count: {report.get('policy_blocker_still_applies_count')}",
        "",
        "## Rows",
    ]
    for row in report.get("reclassification_rows") or []:
        lines.append(
            f"- {row.get('sport')}::{row.get('lane_name')} final={row.get('final_actionable_state')} reason={row.get('exact_reason')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
