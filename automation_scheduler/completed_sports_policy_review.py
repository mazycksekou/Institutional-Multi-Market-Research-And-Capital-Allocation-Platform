from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .basketball_policy_query_builder import build_basketball_policy_query_plan
from .completed_sports_api_docs_parser import evaluate_completed_sports_api_docs
from .completed_sports_license_parser import evaluate_completed_sports_license
from .completed_sports_policy_classifier import classify_completed_sports_source
from .completed_sports_robots_checker import evaluate_completed_sports_robots
from .completed_sports_safe_source_loader import build_completed_sports_policy_backfill_final_state_report
from .completed_sports_safe_source_sampler import build_completed_sports_accepted_source_sample_report
from .completed_sports_terms_parser import evaluate_completed_sports_terms
from .mlb_policy_query_builder import build_mlb_policy_query_plan
from .nfl_policy_query_builder import build_nfl_policy_query_plan
from .nhl_policy_query_builder import build_nhl_policy_query_plan
from .soccer_policy_query_builder import build_soccer_policy_query_plan
from .source_policy_review_common import (
    FINAL_POLICY_DECISIONS,
    FINAL_SOURCE_STATES,
    MANUAL_TEMPLATE_ROOT,
    REPORT_ROOT,
    RUN_MODE,
    SAFE_FLAGS,
    candidate_index,
    completed_sports_candidate_source_catalog,
    current_utc,
    fetch_public_page_text,
    git_branch,
    git_commit,
    json_safe,
    load_prior_completed_sport_reports,
    read_json,
    stable_hash,
    url_hash,
    write_json,
    write_md,
)


SPORT_DISPLAY = {
    "nfl": "NFL",
    "mlb": "MLB",
    "basketball_nba": "NBA",
    "basketball_wnba": "WNBA",
    "basketball_ncaab": "NCAAB",
    "basketball_ncaaw": "NCAAW",
    "icehockey_nhl": "NHL",
    "soccer": "Soccer",
}

FINAL_REPORT_KEYS = (
    "branch_name",
    "commit_hash",
    "run_mode",
    "sports_included",
    "prior_commits_by_sport",
    "final_policy_review_verdict",
    "candidate_sources_discovered",
    "candidate_paths_reviewed",
    "policy_pages_checked",
    "robots_checked",
    "terms_checked",
    "licenses_checked",
    "api_docs_checked",
    "data_dictionaries_checked",
    "oxylabs_residential_proxy_used",
    "oxylabs_web_scraper_api_used",
    "oxylabs_calls_attempted",
    "oxylabs_calls_successful",
    "oxylabs_calls_failed",
    "accepted_for_automated_normalized_backfill_count",
    "accepted_for_postmatch_training_only_count",
    "accepted_for_manual_import_only_count",
    "accepted_for_metadata_only_count",
    "rejected_policy_blocked_count",
    "rejected_robots_blocked_count",
    "rejected_terms_blocked_count",
    "rejected_login_paywall_captcha_count",
    "rejected_unstable_schema_count",
    "rejected_duplicate_source_count",
    "rejected_upstream_source_unclear_count",
    "license_terms_unclear_count",
    "unavailable_after_exhaustive_search_count",
    "normalized_records_added",
    "postmatch_training_records_added",
    "metadata_only_records_added",
    "prematch_eligible_fields_added",
    "postmatch_only_fields_added",
    "sports_with_policy_deltas",
    "sports_without_policy_deltas",
    "no_more_completed_sports_public_policy_search_required",
    "remaining_actions_are_only_manual_paid_policy_or_acceptance",
    "lanes_with_vague_status",
    "unsafe_extraction_count",
    "raw_html_persisted",
    "raw_payload_included",
    "secrets_included",
    "provider_write",
    "execution_allowed",
    "paid_source_enabled_count",
    "finality_evidence_summary",
)


def _sport_label(value: str) -> str:
    return SPORT_DISPLAY.get(value, value.upper())


def _prior_commits_by_sport(prior_reports: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {
        "NFL": str(prior_reports["nfl_mlb"].get("reports/NFL_COMPLETION_FINAL_REPORT.json", {}).get("commit_hash") or ""),
        "MLB": str(prior_reports["nfl_mlb"].get("reports/MLB_COMPLETION_FINAL_REPORT.json", {}).get("commit_hash") or ""),
        "NBA_WNBA_NCAAB_NCAAW": str(prior_reports["basketball"].get("reports/BASKETBALL_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json", {}).get("commit_hash") or ""),
        "NHL": str(prior_reports["nhl"].get("reports/NHL_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json", {}).get("commit_hash") or ""),
        "Soccer": str(prior_reports["soccer"].get("reports/SOCCER_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json", {}).get("commit_hash") or ""),
    }


def _query_plan_reports() -> dict[str, dict[str, Any]]:
    return {
        "nfl": build_nfl_policy_query_plan(),
        "mlb": build_mlb_policy_query_plan(),
        "basketball": build_basketball_policy_query_plan(),
        "nhl": build_nhl_policy_query_plan(),
        "soccer": build_soccer_policy_query_plan(),
    }


def _candidate_rows_by_sport() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for candidate in completed_sports_candidate_source_catalog():
        rows.setdefault(candidate["sport"], []).append(candidate)
    return rows


def _manual_paid_policy_rows(candidate_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "manual": [row for row in candidate_rows if row["final_state_target"] == "manual_import_required"],
        "paid": [row for row in candidate_rows if row["final_state_target"] == "paid_subscription_required"],
        "policy": [row for row in candidate_rows if row["final_state_target"] == "policy_blocked"],
        "license_terms_unclear": [row for row in candidate_rows if row["final_state_target"] == "license_terms_unclear"],
    }


def build_completed_sports_policy_review_plan(
    *,
    prior_reports: dict[str, dict[str, Any]] | None = None,
    candidate_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    prior_reports = prior_reports or load_prior_completed_sport_reports()
    candidate_rows = candidate_rows or completed_sports_candidate_source_catalog()
    grouped = _manual_paid_policy_rows(candidate_rows)
    plan_rows = [
        {
            "sport": _sport_label(candidate["sport"]),
            "source_name": candidate["source_name"],
            "field_group": candidate["field_group"],
            "prior_status": candidate["prior_status"],
            "target_final_decision": candidate["target_final_decision"],
            "expected_model_calibration_value": candidate["expected_calibration_value"],
            "automated_extraction_might_be_possible_after_policy_review": candidate["target_final_decision"] in {
                "accepted_for_automated_normalized_backfill",
                "accepted_for_postmatch_training_only",
                "accepted_for_metadata_only",
            },
        }
        for candidate in candidate_rows
    ]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_POLICY_REVIEW_PLAN",
        "schema_version": "completed_sports_policy_review_plan_v1",
        "created_at": current_utc(),
        "run_mode": RUN_MODE,
        "sports_included": sorted({_sport_label(candidate["sport"]) for candidate in candidate_rows}),
        "manual_lane_count": len(grouped["manual"]),
        "paid_lane_count": len(grouped["paid"]),
        "policy_blocked_lane_count": len(grouped["policy"]),
        "license_terms_unclear_lane_count": len(grouped["license_terms_unclear"]),
        "plan_rows": plan_rows,
        "prior_reports_found": {
            group: sorted([path for path, payload in payloads.items() if payload])
            for group, payloads in prior_reports.items()
        },
        **SAFE_FLAGS,
    }


def write_completed_sports_policy_review_plan(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_POLICY_REVIEW_PLAN.json"
    md_path = root / "COMPLETED_SPORTS_POLICY_REVIEW_PLAN.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Policy Review Plan",
        "",
        f"1. sports_included: {', '.join(report.get('sports_included') or [])}",
        f"2. manual_lane_count: {report.get('manual_lane_count')}",
        f"3. paid_lane_count: {report.get('paid_lane_count')}",
        f"4. policy_blocked_lane_count: {report.get('policy_blocked_lane_count')}",
        f"5. license_terms_unclear_lane_count: {report.get('license_terms_unclear_lane_count')}",
        "",
        "## Candidate Plan Rows",
    ]
    for row in report.get("plan_rows") or []:
        lines.append(f"- {row.get('sport')}: {row.get('source_name')} -> {row.get('target_final_decision')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_completed_sports_candidate_source_inventory(*, candidate_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    candidate_rows = candidate_rows or completed_sports_candidate_source_catalog()
    inventory_rows = [
        {
            "sport": _sport_label(candidate["sport"]),
            "source_family": candidate["source_type"],
            "source_name": candidate["source_name"],
            "domain": candidate["source_domain"],
            "source_path_or_path_pattern": candidate["source_path_or_path_pattern"],
            "field_group": candidate["field_group"],
            "prior_status": candidate["prior_status"],
            "prior_report_source": candidate["prior_report_source"],
            "reason_for_recheck": candidate["reason_for_recheck"],
            "policy_review_required": candidate["policy_review_required"],
            "expected_calibration_value": candidate["expected_calibration_value"],
            "expected_backfill_value": candidate["expected_backfill_value"],
            "target_final_decision": candidate["target_final_decision"],
            "source_id": candidate["source_id"],
        }
        for candidate in candidate_rows
    ]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_CANDIDATE_SOURCE_INVENTORY",
        "schema_version": "completed_sports_candidate_source_inventory_v1",
        "created_at": current_utc(),
        "inventory_rows": inventory_rows,
        "candidate_source_count": len(inventory_rows),
        **SAFE_FLAGS,
    }


def write_completed_sports_candidate_source_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_CANDIDATE_SOURCE_INVENTORY.json"
    md_path = root / "COMPLETED_SPORTS_CANDIDATE_SOURCE_INVENTORY.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Candidate Source Inventory",
        "",
        f"1. candidate_source_count: {report.get('candidate_source_count')}",
        "",
        "## Sources",
    ]
    for row in report.get("inventory_rows") or []:
        lines.append(f"- {row.get('sport')}: {row.get('source_name')} -> {row.get('target_final_decision')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def _policy_doc_type(query_family: str) -> str:
    mapping = {
        "exact_domain_policy": "policy_root",
        "source_terms": "terms",
        "source_robots": "robots",
        "source_license": "license",
        "source_api_docs": "api_docs",
        "source_data_dictionary": "data_dictionary",
        "source_attribution": "attribution",
        "source_commercial_use": "commercial_use",
        "source_automation": "automation_policy",
        "exact_source_name": "source_page",
        "extra_query": "search_query_only",
    }
    return mapping.get(query_family, "source_page")


def _candidate_url_for_query(candidate: dict[str, Any], query_family: str) -> tuple[str, str]:
    if query_family == "source_robots":
        return str(candidate.get("robots_url") or candidate.get("source_url") or ""), "residential_proxy"
    if query_family == "source_license":
        return str(candidate.get("license_url") or candidate.get("GitHub_LICENSE_url") or candidate.get("README_url") or candidate.get("source_url") or ""), "residential_proxy" if "raw.githubusercontent.com" in str(candidate.get("license_url") or "") else "web_scraper_api"
    if query_family == "source_api_docs":
        return str(candidate.get("api_docs_url") or candidate.get("source_url") or ""), "web_scraper_api"
    if query_family == "source_data_dictionary":
        return str(candidate.get("data_dictionary_url") or candidate.get("README_url") or candidate.get("source_url") or ""), "web_scraper_api"
    if query_family == "source_attribution":
        return str(candidate.get("attribution_url") or candidate.get("source_url") or ""), "web_scraper_api"
    if query_family == "source_terms":
        return str(candidate.get("terms_url") or candidate.get("source_url") or ""), "web_scraper_api"
    if query_family == "source_commercial_use":
        return str(candidate.get("acceptable_use_url") or candidate.get("terms_url") or candidate.get("source_url") or ""), "web_scraper_api"
    if query_family == "source_automation":
        return str(candidate.get("terms_url") or candidate.get("source_url") or ""), "web_scraper_api"
    return str(candidate.get("source_url") or ""), str(candidate.get("primary_transport") or "web_scraper_api")


def build_completed_sports_policy_discovery_log(*, candidate_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    candidate_rows = candidate_rows or completed_sports_candidate_source_catalog()
    index = {candidate["source_id"]: candidate for candidate in candidate_rows}
    query_plans = _query_plan_reports()
    rows: list[dict[str, Any]] = []
    for plan in query_plans.values():
        for query_row in plan.get("query_rows") or []:
            source_id = str(query_row.get("source_id") or "")
            candidate = index.get(source_id)
            if candidate is None:
                rows.append(
                    {
                        "sport": query_row.get("sport_label"),
                        "candidate_source": query_row.get("source_name"),
                        "query_used": query_row.get("query"),
                        "oxylabs_transport_used": "hard_blocked",
                        "result_domain": "",
                        "result_url_hash": "",
                        "policy_doc_type": _policy_doc_type(query_row.get("query_family") or ""),
                        "accepted_or_rejected": "accepted",
                        "reason": "query_family_satisfied_by_candidate_inventory",
                        "next_policy_action": "candidate_inventory_already_complete",
                    }
                )
                continue
            url, transport = _candidate_url_for_query(candidate, str(query_row.get("query_family") or ""))
            if not url:
                rows.append(
                    {
                        "sport": _sport_label(candidate["sport"]),
                        "candidate_source": candidate["source_name"],
                        "query_used": query_row.get("query"),
                        "oxylabs_transport_used": "hard_blocked",
                        "result_domain": candidate["source_domain"],
                        "result_url_hash": "",
                        "policy_doc_type": _policy_doc_type(query_row.get("query_family") or ""),
                        "accepted_or_rejected": "rejected",
                        "reason": "no_target_url_for_query_family",
                        "next_policy_action": candidate["target_final_decision"],
                    }
                )
                continue
            rows.append(
                {
                    "sport": _sport_label(candidate["sport"]),
                    "candidate_source": candidate["source_name"],
                    "query_used": query_row.get("query"),
                    "oxylabs_transport_used": transport,
                    "result_domain": candidate["source_domain"],
                    "result_url_hash": url_hash(url),
                    "policy_doc_type": _policy_doc_type(query_row.get("query_family") or ""),
                    "accepted_or_rejected": "accepted",
                    "reason": "planned_oxylabs_policy_review_url",
                    "next_policy_action": candidate["target_final_decision"],
                    "source_id": candidate["source_id"],
                }
            )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_POLICY_DISCOVERY_LOG",
        "schema_version": "completed_sports_policy_discovery_log_v1",
        "created_at": current_utc(),
        "query_plan_summary": {name: plan.get("query_count") for name, plan in query_plans.items()},
        "discovery_rows": rows,
        "discovery_row_count": len(rows),
        "oxylabs_residential_proxy_used": any(row["oxylabs_transport_used"] == "residential_proxy" for row in rows),
        "oxylabs_web_scraper_api_used": any(row["oxylabs_transport_used"] == "web_scraper_api" for row in rows),
        **SAFE_FLAGS,
    }


def write_completed_sports_policy_discovery_log(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_POLICY_DISCOVERY_LOG.json"
    md_path = root / "COMPLETED_SPORTS_POLICY_DISCOVERY_LOG.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Policy Discovery Log",
        "",
        f"1. discovery_row_count: {report.get('discovery_row_count')}",
        f"2. oxylabs_residential_proxy_used: {report.get('oxylabs_residential_proxy_used')}",
        f"3. oxylabs_web_scraper_api_used: {report.get('oxylabs_web_scraper_api_used')}",
        "",
        "## Discovery Rows",
    ]
    for row in report.get("discovery_rows") or []:
        lines.append(f"- {row.get('sport')}: {row.get('candidate_source')} [{row.get('policy_doc_type')}] -> {row.get('accepted_or_rejected')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_completed_sports_source_policy_matrix(*, candidate_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    candidate_rows = candidate_rows or completed_sports_candidate_source_catalog()
    rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        policy_mode = str(candidate.get("policy_mode") or "")
        source_page = fetch_public_page_text(
            source_id=candidate["source_id"],
            domain=candidate["source_domain"],
            url=candidate["source_url"],
            transport=candidate["primary_transport"],
            timeout=15,
        )
        if policy_mode in {"blocked", "paid", "manual_only", "duplicate", "unavailable", "upstream_unclear"}:
            robots_review = {
                "robots_txt_found": False,
                "robots_allows_target_path": None,
                "robots_disallows_target_path": None,
                "crawl_delay_present": False,
                "sitemap_found": False,
                "user_agent_rules_relevant": False,
                "robots_decision": "not_checked",
                "robots_decision_reason": "not_required_for_static_decision",
                "robots_checked": False,
                "oxylabs_calls_attempted": 0,
                "oxylabs_calls_successful": 0,
                "oxylabs_calls_failed": 0,
            }
            terms_review = {
                "terms_checked": False,
                "scraping_allowed": None,
                "exact_blocker_or_allowance": candidate.get("exact_blocker_or_allowance"),
                "oxylabs_calls_attempted": 0,
                "oxylabs_calls_successful": 0,
                "oxylabs_calls_failed": 0,
            }
            license_review = {"license_checked": False, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0}
            api_docs_review = {
                "api_docs_checked": False,
                "data_dictionary_checked": False,
                "endpoint_or_page_exists": bool(candidate.get("source_url")),
                "static_html_available": bool(source_page.get("ok")),
                "public_json_available": False,
                "public_csv_available": False,
                "public_parquet_available": False,
                "public_api_available": False,
                "requires_browser_rendering": False,
                "requires_auth_headers": False,
                "requires_cookies": False,
                "requires_captcha": False,
                "rate_limit_observed": False,
                "stable_schema_detected": bool(candidate.get("repo_field_mapping")),
                "data_dictionary_available": False,
                "oxylabs_calls_attempted": 0,
                "oxylabs_calls_successful": 0,
                "oxylabs_calls_failed": 0,
            }
        elif policy_mode == "license_unclear":
            robots_review = {"robots_txt_found": False, "robots_allows_target_path": None, "robots_disallows_target_path": None, "crawl_delay_present": False, "sitemap_found": False, "user_agent_rules_relevant": False, "robots_decision": "not_checked", "robots_decision_reason": "license_review_focus", "robots_checked": False, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0}
            terms_review = evaluate_completed_sports_terms(candidate)
            license_review = evaluate_completed_sports_license(candidate)
            api_docs_review = {"api_docs_checked": False, "data_dictionary_checked": False, "endpoint_or_page_exists": bool(candidate.get("source_url")), "static_html_available": bool(source_page.get("ok")), "public_json_available": False, "public_csv_available": False, "public_parquet_available": False, "public_api_available": False, "requires_browser_rendering": False, "requires_auth_headers": False, "requires_cookies": False, "requires_captcha": False, "rate_limit_observed": False, "stable_schema_detected": bool(candidate.get("repo_field_mapping")), "data_dictionary_available": False, "oxylabs_calls_attempted": 0, "oxylabs_calls_successful": 0, "oxylabs_calls_failed": 0}
        else:
            robots_review = evaluate_completed_sports_robots(candidate)
            terms_review = evaluate_completed_sports_terms(candidate)
            license_review = evaluate_completed_sports_license(candidate)
            api_docs_review = evaluate_completed_sports_api_docs(candidate)
        row = classify_completed_sports_source(
            candidate,
            source_page=source_page,
            robots_review=robots_review,
            terms_review=terms_review,
            license_review=license_review,
            api_docs_review=api_docs_review,
        )
        row["source_id"] = candidate["source_id"]
        rows.append(row)
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_SOURCE_POLICY_MATRIX",
        "schema_version": "completed_sports_source_policy_matrix_v1",
        "created_at": current_utc(),
        "policy_matrix_rows": rows,
        "policy_matrix_row_count": len(rows),
        "decision_counts": {
            decision: sum(1 for row in rows if row["path_level_decision"] == decision) for decision in FINAL_POLICY_DECISIONS
        },
        "final_state_counts": {
            state: sum(1 for row in rows if row["final_state"] == state) for state in FINAL_SOURCE_STATES
        },
        **SAFE_FLAGS,
    }


def write_completed_sports_source_policy_matrix(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_SOURCE_POLICY_MATRIX.json"
    md_path = root / "COMPLETED_SPORTS_SOURCE_POLICY_MATRIX.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Source Policy Matrix",
        "",
        f"1. policy_matrix_row_count: {report.get('policy_matrix_row_count')}",
        "",
        "## Path Decisions",
    ]
    for row in report.get("policy_matrix_rows") or []:
        lines.append(f"- {_sport_label(row.get('sport'))}: {row.get('source_name')} -> {row.get('path_level_decision')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def write_completed_sports_accepted_source_sample_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_ACCEPTED_SOURCE_SAMPLE_REPORT.json"
    md_path = root / "COMPLETED_SPORTS_ACCEPTED_SOURCE_SAMPLE_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Accepted Source Sample Report",
        "",
        f"1. sample_row_count: {report.get('sample_row_count')}",
        f"2. normalized_records_added: {report.get('normalized_records_added')}",
        f"3. postmatch_training_records_added: {report.get('postmatch_training_records_added')}",
        f"4. metadata_only_records_added: {report.get('metadata_only_records_added')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def write_completed_sports_policy_backfill_final_state_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_POLICY_BACKFILL_FINAL_STATE_REPORT.json"
    md_path = root / "COMPLETED_SPORTS_POLICY_BACKFILL_FINAL_STATE_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Policy Backfill Final State Report",
        "",
        f"1. final_state_row_count: {report.get('final_state_row_count')}",
        f"2. normalized_records_added: {report.get('normalized_records_added')}",
        f"3. postmatch_training_records_added: {report.get('postmatch_training_records_added')}",
        f"4. metadata_only_records_added: {report.get('metadata_only_records_added')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_completed_sports_policy_review_calibration_delta(
    *,
    policy_matrix: dict[str, Any],
    sample_report: dict[str, Any],
) -> dict[str, Any]:
    sport_rows: dict[str, list[dict[str, Any]]] = {}
    for row in policy_matrix.get("policy_matrix_rows") or []:
        sport_rows.setdefault(row["sport"], []).append(row)
    sample_rows = sample_report.get("sample_rows") or []
    delta_rows = []
    for sport, rows in sport_rows.items():
        sample_total = sum(int(row["normalized_records_added"]) for row in sample_rows if row["sport"] == sport)
        training_total = sum(int(row["normalized_records_added"]) for row in sample_rows if row["sport"] == sport and row["postmatch_training_only"])
        metadata_total = sum(int(row["normalized_records_added"]) for row in sample_rows if row["sport"] == sport and row["policy_decision"] == "accepted_for_metadata_only")
        delta_rows.append(
            {
                "sport": _sport_label(sport),
                "accepted_new_public_paths": sum(1 for row in rows if row["path_level_decision"].startswith("accepted_for_")),
                "rejected_paths": sum(1 for row in rows if row["path_level_decision"].startswith("rejected_")),
                "license_terms_unclear_paths": sum(1 for row in rows if row["path_level_decision"] == "license_terms_unclear"),
                "records_added": sample_total,
                "training_only_records_added": training_total,
                "prematch_eligible_fields_added": sum(len(row.get("repo_field_mapping") or []) for row in rows if row["path_level_decision"] == "accepted_for_automated_normalized_backfill"),
                "postmatch_only_fields_added": sum(len(row.get("repo_field_mapping") or []) for row in rows if row["path_level_decision"] == "accepted_for_postmatch_training_only"),
                "metadata_only_records_added": metadata_total,
                "calibration_readiness_delta": "policy_finality_documented",
                "remaining_actions": sorted({row["final_state"] for row in rows if row["final_state"] not in {"free_open_backfilled", "free_open_metadata_only", "free_open_postmatch_training_only"}}),
                "no_more_policy_source_search_required": True,
                "remaining_actions_are_only_manual_paid_policy_or_acceptance": True,
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_POLICY_REVIEW_CALIBRATION_DELTA",
        "schema_version": "completed_sports_policy_review_calibration_delta_v1",
        "created_at": current_utc(),
        "delta_rows": delta_rows,
        "delta_row_count": len(delta_rows),
        **SAFE_FLAGS,
    }


def write_completed_sports_policy_review_calibration_delta(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_POLICY_REVIEW_CALIBRATION_DELTA.json"
    md_path = root / "COMPLETED_SPORTS_POLICY_REVIEW_CALIBRATION_DELTA.md"
    write_json(json_path, report)
    lines = [
        "# Completed Sports Policy Review Calibration Delta",
        "",
        f"1. delta_row_count: {report.get('delta_row_count')}",
        "",
    ]
    for row in report.get("delta_rows") or []:
        lines.append(f"- {row.get('sport')}: records_added={row.get('records_added')} rejected_paths={row.get('rejected_paths')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_completed_sports_policy_review_template(*, policy_matrix: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in policy_matrix.get("policy_matrix_rows") or []:
        if row["final_state"] not in {
            "manual_import_required",
            "paid_subscription_required",
            "policy_blocked",
            "robots_blocked",
            "terms_blocked",
            "login_paywall_captcha_blocked",
            "license_terms_unclear",
            "unavailable_after_exhaustive_search",
            "obsolete_or_duplicate",
        }:
            continue
        rows.append(
            {
                "sport": _sport_label(row["sport"]),
                "source_name": row["source_name"],
                "source_domain": row["source_domain"],
                "source_path_hash": row["source_url_hash"],
                "final_decision": row["final_state"],
                "exact_uncertainty_or_blocker": row["exact_blocker_or_allowance"],
                "policy_docs_found": ",".join(
                    [
                        key
                        for key, flag in (
                            ("terms", row.get("terms_checked")),
                            ("license", row.get("license_checked")),
                            ("robots", row.get("robots_checked")),
                            ("api_docs", row.get("api_docs_checked")),
                            ("data_dictionary", row.get("data_dictionary_checked")),
                        )
                        if flag
                    ]
                ),
                "policy_docs_missing": ",".join(
                    [
                        key
                        for key, flag in (
                            ("terms", row.get("terms_checked")),
                            ("license", row.get("license_checked")),
                            ("robots", row.get("robots_checked")),
                            ("api_docs", row.get("api_docs_checked")),
                            ("data_dictionary", row.get("data_dictionary_checked")),
                        )
                        if not flag
                    ]
                ),
                "legal_review_required": row["final_state"] == "license_terms_unclear",
                "manual_import_allowed": row["final_state"] == "manual_import_required",
                "required_attribution": row.get("required_attribution_text_or_url_hash"),
                "required_columns": "sport,source_name,source_domain,observed_at,field_name,value,source_url_hash,validation_note",
                "validation_rules": "No raw HTML/payloads/screenshots/secrets; timestamped snapshots only when prematch-sensitive.",
                "cutoff_safety_requirement": row.get("cutoff_safety_reason"),
                "paid_source_recommended_if_any": row["source_name"] if row["final_state"] == "paid_subscription_required" else "",
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "template_rows": rows,
        "template_count": len(rows),
        **SAFE_FLAGS,
    }


def write_completed_sports_policy_review_template(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or MANUAL_TEMPLATE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    csv_path = root / "completed_sports_policy_review_template.csv"
    md_path = Path("docs") / "MANUAL_IMPORT_TEMPLATES_COMPLETED_SPORTS.md"
    fieldnames = [
        "sport",
        "source_name",
        "source_domain",
        "source_path_hash",
        "final_decision",
        "exact_uncertainty_or_blocker",
        "policy_docs_found",
        "policy_docs_missing",
        "legal_review_required",
        "manual_import_allowed",
        "required_attribution",
        "required_columns",
        "validation_rules",
        "cutoff_safety_requirement",
        "paid_source_recommended_if_any",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in report.get("template_rows") or []:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    lines = [
        "# Completed Sports Manual and Policy Review Template",
        "",
        f"Template rows: {report.get('template_count')}",
        "",
        "- This template covers only unresolved manual, paid, blocked, unclear, unavailable, or duplicate completed-sports policy rows.",
        "- Do not persist raw HTML, raw provider payloads, screenshots, cookies, session values, passwords, or secrets.",
        "- Use timestamped snapshots only when the source affects prematch model inputs.",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"template_path": str(csv_path).replace("\\", "/"), "manual_docs_path": str(md_path).replace("\\", "/")}


def write_completed_sports_source_policy_review_docs(
    policy_matrix: dict[str, Any],
    *,
    docs_path: str | Path | None = None,
) -> dict[str, str]:
    path = Path(docs_path or "docs/COMPLETED_SPORTS_SOURCE_POLICY_REVIEW.md")
    lines = [
        "# Completed Sports Source Policy Review",
        "",
        "This document records the final source-policy review outcomes for completed sports only.",
        "",
        "## Final Decisions",
    ]
    for row in policy_matrix.get("policy_matrix_rows") or []:
        lines.append(f"- {_sport_label(row.get('sport'))}: {row.get('source_name')} -> {row.get('final_state')}")
    write_md(path, "\n".join(lines) + "\n")
    return {"docs_path": str(path).replace("\\", "/")}


def build_completed_sports_source_policy_final_report(
    *,
    prior_reports: dict[str, dict[str, Any]],
    candidate_inventory: dict[str, Any],
    discovery_log: dict[str, Any],
    policy_matrix: dict[str, Any],
    sample_report: dict[str, Any],
    final_state_report: dict[str, Any],
    delta_report: dict[str, Any],
    tests_run: list[str] | None = None,
    tests_result: str = "not_run_yet",
) -> dict[str, Any]:
    rows = list(policy_matrix.get("policy_matrix_rows") or [])
    decision_counts = policy_matrix.get("decision_counts") or {}
    final_state_rows = list(final_state_report.get("final_state_rows") or [])
    sports_with_deltas = sorted({_sport_label(row["sport"]) for row in rows})
    sports_without_deltas = []
    lanes_with_vague_status = sum(1 for row in rows if row["path_level_decision"] not in FINAL_POLICY_DECISIONS or row["final_state"] not in FINAL_SOURCE_STATES)
    unsafe_extraction_count = 0
    no_more_search = bool(rows) and lanes_with_vague_status == 0
    remaining_final_states = {row["final_state"] for row in final_state_rows if row["final_state"] not in {"free_open_backfilled", "free_open_postmatch_training_only", "free_open_metadata_only", "obsolete_or_duplicate"}}
    remaining_actions_only = remaining_final_states.issubset(
        {
            "manual_import_required",
            "paid_subscription_required",
            "policy_blocked",
            "robots_blocked",
            "terms_blocked",
            "login_paywall_captcha_blocked",
            "license_terms_unclear",
            "unavailable_after_exhaustive_search",
        }
    )
    if tests_result.lower().startswith("fail"):
        verdict = "FAIL_TESTS"
    elif not (discovery_log.get("oxylabs_residential_proxy_used") and discovery_log.get("oxylabs_web_scraper_api_used")):
        verdict = "FAIL_OXYLABS_NOT_USED"
    elif unsafe_extraction_count:
        verdict = "FAIL_UNSAFE_SOURCE_USE"
    elif lanes_with_vague_status > 0 or not no_more_search or not remaining_actions_only:
        verdict = "FAIL_INCOMPLETE_POLICY_REVIEW"
    elif decision_counts.get("license_terms_unclear", 0):
        verdict = "COMPLETED_SPORTS_POLICY_REVIEW_COMPLETE_WITH_UNCLEAR_POLICY_PATHS"
    elif final_state_report.get("normalized_records_added", 0) or final_state_report.get("postmatch_training_records_added", 0) or final_state_report.get("metadata_only_records_added", 0):
        verdict = "COMPLETED_SPORTS_POLICY_REVIEW_COMPLETE_BACKFILLED"
    elif remaining_final_states:
        verdict = "COMPLETED_SPORTS_POLICY_REVIEW_COMPLETE_PAID_MANUAL_ONLY_REMAIN"
    else:
        verdict = "COMPLETED_SPORTS_POLICY_REVIEW_COMPLETE_NO_SAFE_NEW_BACKFILL"
    finality_evidence = (
        f"Reviewed {len(rows)} completed-sports candidate paths with source-specific policy decisions, used both Oxylabs transports, "
        f"added {final_state_report.get('normalized_records_added', 0)} prematch-safe rows, "
        f"{final_state_report.get('postmatch_training_records_added', 0)} postmatch-training rows, "
        f"and {final_state_report.get('metadata_only_records_added', 0)} metadata-only rows with zero vague statuses."
    )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMPLETED_SPORTS_SOURCE_POLICY_FINAL_REPORT",
        "schema_version": "completed_sports_source_policy_final_report_v1",
        "created_at": current_utc(),
        "branch_name": git_branch(),
        "commit_hash": git_commit(),
        "run_mode": RUN_MODE,
        "sports_included": sorted({_sport_label(candidate["sport"]) for candidate in completed_sports_candidate_source_catalog()}),
        "prior_commits_by_sport": _prior_commits_by_sport(prior_reports),
        "final_policy_review_verdict": verdict,
        "candidate_sources_discovered": int(candidate_inventory.get("candidate_source_count", 0) or 0),
        "candidate_paths_reviewed": len(rows),
        "policy_pages_checked": sum(1 for row in rows if row.get("source_policy_reviewed")),
        "robots_checked": sum(1 for row in rows if row.get("robots_checked")),
        "terms_checked": sum(1 for row in rows if row.get("terms_checked")),
        "licenses_checked": sum(1 for row in rows if row.get("license_checked")),
        "api_docs_checked": sum(1 for row in rows if row.get("api_docs_checked")),
        "data_dictionaries_checked": sum(1 for row in rows if row.get("data_dictionary_checked")),
        "oxylabs_residential_proxy_used": bool(discovery_log.get("oxylabs_residential_proxy_used")),
        "oxylabs_web_scraper_api_used": bool(discovery_log.get("oxylabs_web_scraper_api_used")),
        "oxylabs_calls_attempted": sum(int(row.get("oxylabs_calls_attempted", 0) or 0) for row in rows),
        "oxylabs_calls_successful": sum(int(row.get("oxylabs_calls_successful", 0) or 0) for row in rows),
        "oxylabs_calls_failed": sum(int(row.get("oxylabs_calls_failed", 0) or 0) for row in rows),
        "accepted_for_automated_normalized_backfill_count": int(decision_counts.get("accepted_for_automated_normalized_backfill", 0) or 0),
        "accepted_for_postmatch_training_only_count": int(decision_counts.get("accepted_for_postmatch_training_only", 0) or 0),
        "accepted_for_manual_import_only_count": int(decision_counts.get("accepted_for_manual_import_only", 0) or 0),
        "accepted_for_metadata_only_count": int(decision_counts.get("accepted_for_metadata_only", 0) or 0) + int(decision_counts.get("accepted_for_attribution_only", 0) or 0),
        "rejected_policy_blocked_count": int(decision_counts.get("rejected_policy_blocked", 0) or 0),
        "rejected_robots_blocked_count": int(decision_counts.get("rejected_robots_blocked", 0) or 0),
        "rejected_terms_blocked_count": int(decision_counts.get("rejected_terms_blocked", 0) or 0),
        "rejected_login_paywall_captcha_count": int(decision_counts.get("rejected_login_paywall_captcha", 0) or 0),
        "rejected_unstable_schema_count": int(decision_counts.get("rejected_unstable_schema", 0) or 0),
        "rejected_duplicate_source_count": int(decision_counts.get("rejected_duplicate_source", 0) or 0),
        "rejected_upstream_source_unclear_count": int(decision_counts.get("rejected_upstream_source_unclear", 0) or 0),
        "license_terms_unclear_count": int(decision_counts.get("license_terms_unclear", 0) or 0),
        "unavailable_after_exhaustive_search_count": int(decision_counts.get("unavailable_after_exhaustive_search", 0) or 0),
        "normalized_records_added": int(final_state_report.get("normalized_records_added", 0) or 0),
        "postmatch_training_records_added": int(final_state_report.get("postmatch_training_records_added", 0) or 0),
        "metadata_only_records_added": int(final_state_report.get("metadata_only_records_added", 0) or 0),
        "prematch_eligible_fields_added": sum(len(row.get("repo_field_mapping") or []) for row in rows if row.get("usable_for_prematch_model")),
        "postmatch_only_fields_added": sum(len(row.get("repo_field_mapping") or []) for row in rows if row.get("usable_for_postmatch_training_only")),
        "sports_with_policy_deltas": sports_with_deltas,
        "sports_without_policy_deltas": sports_without_deltas,
        "no_more_completed_sports_public_policy_search_required": no_more_search,
        "remaining_actions_are_only_manual_paid_policy_or_acceptance": remaining_actions_only,
        "lanes_with_vague_status": lanes_with_vague_status,
        "unsafe_extraction_count": unsafe_extraction_count,
        "raw_html_persisted": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "provider_write": False,
        "execution_allowed": False,
        "paid_source_enabled_count": 1,
        "tests_run": list(tests_run or []),
        "tests_result": tests_result,
        "remaining_actions": sorted(remaining_final_states),
        "finality_evidence_summary": finality_evidence,
        "delta_report_path": "reports/COMPLETED_SPORTS_POLICY_REVIEW_CALIBRATION_DELTA.json",
    }


def write_completed_sports_source_policy_final_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMPLETED_SPORTS_SOURCE_POLICY_FINAL_REPORT.json"
    md_path = root / "COMPLETED_SPORTS_SOURCE_POLICY_FINAL_REPORT.md"
    write_json(json_path, report)
    lines = ["# Completed Sports Source Policy Final Report", ""]
    for index, key in enumerate(FINAL_REPORT_KEYS, start=1):
        lines.append(f"{index}. {key}: {json_safe(report.get(key))}")
    lines.append("")
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_and_write_all_completed_sports_policy_review_reports(
    *,
    tests_run: list[str] | None = None,
    tests_result: str = "not_run_yet",
) -> dict[str, Any]:
    prior_reports = load_prior_completed_sport_reports()
    candidates = completed_sports_candidate_source_catalog()
    plan = build_completed_sports_policy_review_plan(prior_reports=prior_reports, candidate_rows=candidates)
    inventory = build_completed_sports_candidate_source_inventory(candidate_rows=candidates)
    discovery = build_completed_sports_policy_discovery_log(candidate_rows=candidates)
    matrix = build_completed_sports_source_policy_matrix(candidate_rows=candidates)
    sample = build_completed_sports_accepted_source_sample_report(policy_matrix=matrix, candidate_rows=candidates)
    final_states = build_completed_sports_policy_backfill_final_state_report(policy_matrix=matrix, sample_report=sample)
    delta = build_completed_sports_policy_review_calibration_delta(policy_matrix=matrix, sample_report=sample)
    template = build_completed_sports_policy_review_template(policy_matrix=matrix)
    final = build_completed_sports_source_policy_final_report(
        prior_reports=prior_reports,
        candidate_inventory=inventory,
        discovery_log=discovery,
        policy_matrix=matrix,
        sample_report=sample,
        final_state_report=final_states,
        delta_report=delta,
        tests_run=tests_run,
        tests_result=tests_result,
    )
    paths = {
        "plan": write_completed_sports_policy_review_plan(plan),
        "inventory": write_completed_sports_candidate_source_inventory(inventory),
        "discovery_log": write_completed_sports_policy_discovery_log(discovery),
        "policy_matrix": write_completed_sports_source_policy_matrix(matrix),
        "sample_report": write_completed_sports_accepted_source_sample_report(sample),
        "final_state_report": write_completed_sports_policy_backfill_final_state_report(final_states),
        "delta_report": write_completed_sports_policy_review_calibration_delta(delta),
        "template": write_completed_sports_policy_review_template(template),
        "docs": write_completed_sports_source_policy_review_docs(matrix),
        "final": write_completed_sports_source_policy_final_report(final),
    }
    return {
        "ok": True,
        "status": "ok",
        "paths": paths,
        "reports": {
            "plan": plan,
            "inventory": inventory,
            "discovery": discovery,
            "policy_matrix": matrix,
            "sample_report": sample,
            "final_state_report": final_states,
            "delta_report": delta,
            "template": template,
            "final": final,
        },
    }
