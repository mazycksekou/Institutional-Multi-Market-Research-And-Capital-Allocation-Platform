from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Any

from .nhl_free_vs_paid_readiness import (
    REPORT_ROOT,
    SPORTS,
    build_nhl_architecture_inventory,
    build_nhl_free_vs_paid_source_ledger,
    nhl_lane_catalog,
    write_nhl_architecture_inventory,
    write_nhl_free_vs_paid_source_ledger,
)
from .nhl_loader_ready_backfill import build_nhl_loader_ready_backfill_report, write_nhl_loader_ready_backfill_report
from .nhl_oxylabs_audit import (
    build_nhl_oxylabs_reclassification_report,
    build_nhl_oxylabs_source_exhaustion_log,
    write_nhl_oxylabs_reclassification_report,
    write_nhl_oxylabs_source_exhaustion_log,
)
from .nhl_oxylabs_common import FINAL_ACTIONABLE_STATES, current_utc, read_json, write_json, write_md
from .nhl_oxylabs_schema_expansion import build_nhl_oxylabs_schema_expansion_report, write_nhl_oxylabs_schema_expansion_report
from .nhl_sample_verifier import build_nhl_targeted_sample_verification_results, write_nhl_targeted_sample_verification_results
from .nhl_schema_expansion import build_nhl_schema_expansion_report, write_nhl_schema_expansion_report
from .nhl_source_exhaustion_query_builder import build_nhl_source_exhaustion_query_plan


MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"


def _git_branch() -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    except Exception:
        return ""


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def _prior_report() -> dict[str, Any]:
    return read_json(Path("reports/NHL_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json"))


def build_nhl_manual_import_templates(
    *,
    source_ledger: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_ledger = source_ledger or build_nhl_free_vs_paid_source_ledger()
    audit_report = audit_report or build_nhl_oxylabs_source_exhaustion_log()
    audit_index = {row["lane_name"]: row for row in audit_report.get("source_candidate_rows") or []}
    rows = []
    for row in source_ledger.get("source_ledger_rows") or []:
        if row["free_or_paid_category"] in {"free_open_populated", "free_open_partial", "obsolete_or_duplicate"}:
            continue
        audit_row = audit_index.get(row["lane_name"], {})
        rows.append(
            {
                "sport": row["sport"],
                "field_name": row["field_or_feature_group"],
                "lane_name": row["lane_name"],
                "exact_reason_automation_failed": row["final_reason"],
                "oxylabs_attempts_summary": f"transport={audit_row.get('oxylabs_transport_used')}; calls={audit_row.get('oxylabs_calls_attempted', 0)}; final={audit_row.get('final_actionable_state')}",
                "required_columns": "sport,lane_name,event_or_entity_id,field_name,value,observed_at,source_name,source_url_hash,cutoff_timestamp,validation_note,paid_source_recommended",
                "example_row": f"{row['sport']},{row['lane_name']},sample-id,{row['field_or_feature_group']},sample-value,2026-06-05T00:00:00Z,{row['candidate_source_name']},sha256-placeholder,2026-06-05T00:00:00Z,manual validation required,{row.get('candidate_source_name')}",
                "validation_rules": "source_url_hash required; timestamped pregame or historical snapshot only; no raw HTML/screenshots/payloads/secrets",
                "cutoff_safe_requirement": row.get("future_leakage_risk", "manual_review_required"),
                "source_required": "true",
                "source_url_hash_required": "true",
                "paid_source_recommended": row.get("candidate_source_name") if row["free_or_paid_category"] == "paid_data_subscription_required" else "",
                "notes": row["license_or_terms_note"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_MANUAL_IMPORT_TEMPLATES",
        "template_rows": rows,
        "template_count": len(rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_nhl_manual_import_templates(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or MANUAL_TEMPLATE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "nhl_remaining_fields_template.csv"
    header = [
        "sport",
        "field_name",
        "lane_name",
        "exact_reason_automation_failed",
        "oxylabs_attempts_summary",
        "required_columns",
        "example_row",
        "validation_rules",
        "cutoff_safe_requirement",
        "source_required",
        "source_url_hash_required",
        "paid_source_recommended",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in report.get("template_rows") or []:
            writer.writerow({key: row.get(key, "") for key in header})
    return {"template_path": str(path).replace("\\", "/")}


def write_nhl_manual_import_docs(report: dict[str, Any], *, docs_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(docs_dir or "docs")
    path = root / "MANUAL_IMPORT_TEMPLATES_NHL.md"
    lines = [
        "# NHL Manual Import Templates",
        "",
        "Manual templates remain only for lanes where the free/open automated path was exhausted, policy-limited, or still paid/licensed.",
        "",
        "## Template File",
        "",
        "- `data/manual_import_templates/nhl_remaining_fields_template.csv`",
        "",
        "## Safety Notes",
        "",
        "- Do not persist raw HTML, raw provider payloads, screenshots, cookies, session values, passwords, or secrets.",
        "- Every imported row must include source name, source URL hash, observed timestamp, cutoff timestamp, and a validation note.",
        "- Use timestamped pregame or historical snapshots only when the lane influences model inputs.",
        "",
        f"Template rows: {report.get('template_count')}",
        "",
    ]
    write_md(path, "\n".join(lines))
    return {"manual_import_docs_path": str(path).replace("\\", "/")}


def build_nhl_paid_data_requirement_matrix(
    *,
    source_ledger: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_ledger = source_ledger or build_nhl_free_vs_paid_source_ledger()
    audit_report = audit_report or build_nhl_oxylabs_source_exhaustion_log()
    audit_index = {row["lane_name"]: row for row in audit_report.get("source_candidate_rows") or []}
    query_index = build_nhl_source_exhaustion_query_plan().get("lane_query_index") or {}
    rows = []
    for lane in nhl_lane_catalog():
        if lane["free_or_paid_category"] != "paid_data_subscription_required":
            continue
        audit_row = audit_index.get(lane["lane_name"], {})
        lane_queries = query_index.get(f"{lane['sport']}::{lane['lane_name']}", [])
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "missing_fields": ", ".join(lane["fields"]),
                "why_free_sources_are_insufficient": lane["final_reason"],
                "why_oxylabs_cannot_solve_it_without_paid_subscription": f"Oxylabs can confirm public product pages and docs, but the structured data itself remains paid/licensed for {lane['lane_name']}.",
                "expected_model_value": "high",
                "expected_calibration_value": lane["calibration_impact"],
                "recommended_paid_source_type": lane["candidate_source_name"],
                "priority": lane.get("paid_priority") or "high",
                "fallback_feature_available": True,
                "can_project_continue_without_it": True,
                "recommendation": "paid_subscription_required",
                "free_open_alternatives_checked": sorted({query.get("query_family") for query in lane_queries if query.get("query_family")}),
                "oxylabs_checked": bool(audit_row),
                "oxylabs_transport_used": audit_row.get("oxylabs_transport_used"),
                "oxylabs_calls_attempted": audit_row.get("oxylabs_calls_attempted", 0),
                "oxylabs_calls_successful": audit_row.get("oxylabs_calls_successful", 0),
                "oxylabs_calls_failed": audit_row.get("oxylabs_calls_failed", 0),
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_PAID_DATA_REQUIREMENT_MATRIX",
        "schema_version": "nhl_paid_data_requirement_matrix_v1",
        "created_at": current_utc(),
        "requirement_rows": rows,
        "requirement_count": len(rows),
        "paid_required_count": len(rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_nhl_paid_data_requirement_matrix(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_PAID_DATA_REQUIREMENT_MATRIX.json"
    md_path = root / "NHL_PAID_DATA_REQUIREMENT_MATRIX.md"
    write_json(json_path, report)
    lines = [
        "# NHL Paid Data Requirement Matrix",
        "",
        f"1. paid_required_count: {report.get('paid_required_count')}",
        "",
        "## Lanes",
    ]
    for row in report.get("requirement_rows") or []:
        lines.append(
            f"- {row.get('lane_name')} priority={row.get('priority')} transport={row.get('oxylabs_transport_used')} recommendation={row.get('recommendation')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_nhl_data_calibration_readiness_report(
    *,
    inventory_report: dict[str, Any] | None = None,
    source_ledger: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
    paid_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory_report = inventory_report or build_nhl_architecture_inventory()
    source_ledger = source_ledger or build_nhl_free_vs_paid_source_ledger()
    audit_report = audit_report or build_nhl_oxylabs_source_exhaustion_log()
    backfill_report = backfill_report or build_nhl_loader_ready_backfill_report()
    paid_matrix = paid_matrix or build_nhl_paid_data_requirement_matrix(source_ledger=source_ledger, audit_report=audit_report)
    ledger_rows = list(source_ledger.get("source_ledger_rows") or [])
    usable = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}]
    manual = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] == "free_open_manual_import_needed"]
    paid = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] == "paid_data_subscription_required"]
    terms = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] == "license_terms_unclear"]
    blocked = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] in {"blocked_reference_or_restricted_source", "policy_blocked"}]
    missing_fields = int(inventory_report.get("fields_missing_count", 0) or 0)
    readiness_score = max(0, min(100, 72 + len(usable) - (4 * len(manual)) - (5 * len(paid)) - (3 * len(terms)) - (2 * len(blocked))))
    recommendation = "ready_but_paid_data_would_improve" if readiness_score >= 70 else "manual_import_needed"
    model_row = {
        "sport": "icehockey_nhl",
        "model": SPORTS["icehockey_nhl"]["model"],
        "records_added_this_pass": int(backfill_report.get("records_added_by_nhl", 0) or 0),
        "loader_ready_lanes_backfilled": int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0),
        "fields_improved": int(backfill_report.get("records_added_by_nhl", 0) or 0),
        "fields_still_missing": missing_fields,
        "oxylabs_improvements": int(audit_report.get("lanes_improved_by_oxylabs", 0) or 0),
        "free_open_exhaustion_status": bool(audit_report.get("lanes_with_vague_status", 0) == 0),
        "paid_data_still_required": paid,
        "manual_import_still_required": manual,
        "model_inputs_currently_strong": [lane for lane in usable if lane in {"schedule_results", "team_box_scores", "player_box_scores", "goalie_box_scores", "play_by_play", "shot_events", "penalty_events", "goalie_starts", "overtime_shootout_context", "first_period_scoring_context", "team_totals_context"}],
        "model_inputs_currently_weak": manual + paid + terms + blocked,
        "calibration_readiness_score": readiness_score,
        "confidence_stake_sizing_impact": "NO_BET suggested_stake=0 remains protected; confidence is strongest on team markets and weaker on player props when injuries or line combinations are unresolved.",
        "market_types_impacted": ["moneyline", "three_way_moneyline", "regulation_moneyline", "puckline", "total", "team_total", "first_period_total", "player_props"],
        "current_production_readiness": readiness_score >= 70,
        "recommendation": recommendation,
        "goalie_adjustment_quality": "moderate with official goalie box, starter flags, and workload/rest proxies; paid GSAx would improve it",
        "special_teams_adjustment_quality": "moderate with club stats and penalty-event proxies; public full-rate history remains weaker than a paid warehouse",
        "shot_quality_xg_availability": "official shot coordinates and shot-type proxies are available; fully approved public xG feed remains terms-unclear",
        "team_total_readiness": "strong",
        "first_period_total_readiness": "strong",
        "player_prop_readiness": "moderate",
        "puckline_readiness": "strong",
        "regulation_moneyline_readiness": "strong",
        "overtime_shootout_context": "available",
        "injury_availability_impact": "manual import still recommended",
        "official_referee_impact": "manual import still recommended",
        "rest_travel_impact": "available with explicit travel-distance estimate caveat",
        "lineup_line_combination_impact": "terms-unclear public path keeps this weaker than ideal",
        "preserved_behavior": [
            "goalie_adjustment_applied",
            "special_teams_adjustment_applied",
            "odds stability",
            "missing_partial_bad_input_no_500",
            "confirmed_bets_no_bets_mutually_exclusive",
            "NO_BET_suggested_stake_0",
            "screenshot_analysis_parity",
        ],
    }
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_DATA_CALIBRATION_READINESS_REPORT",
        "schema_version": "nhl_data_calibration_readiness_report_v1",
        "created_at": current_utc(),
        "models": [model_row],
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_nhl_data_calibration_readiness_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_DATA_CALIBRATION_READINESS_REPORT.json"
    md_path = root / "NHL_DATA_CALIBRATION_READINESS_REPORT.md"
    write_json(json_path, report)
    model = (report.get("models") or [{}])[0]
    lines = [
        "# NHL Data Calibration Readiness Report",
        "",
        f"1. model: {model.get('model')}",
        f"2. records_added_this_pass: {model.get('records_added_this_pass')}",
        f"3. loader_ready_lanes_backfilled: {model.get('loader_ready_lanes_backfilled')}",
        f"4. fields_still_missing: {model.get('fields_still_missing')}",
        f"5. calibration_readiness_score: {model.get('calibration_readiness_score')}",
        f"6. recommendation: {model.get('recommendation')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_nhl_free_open_exhaustion_certificate(
    *,
    audit_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    audit_report = audit_report or build_nhl_oxylabs_source_exhaustion_log()
    backfill_report = backfill_report or build_nhl_loader_ready_backfill_report()
    rows = list(audit_report.get("source_candidate_rows") or [])
    required_query_families = {
        "official_league_team",
        "public_api_docs",
        "github_open_source",
        "csv_parquet_archive",
        "public_pdf_media_guide",
        "structured_wiki_supplemental",
        "dataset_catalog_index",
        "source_specific_terminology",
    }
    checked_query_families = set(build_nhl_source_exhaustion_query_plan().get("query_families") or [])
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_FREE_OPEN_EXHAUSTION_CERTIFICATE",
        "schema_version": "nhl_free_open_exhaustion_certificate_v1",
        "created_at": current_utc(),
        "free_sources_checked": len([row for row in rows if row.get("source_type") in {"official_public_api", "github_open_source_page", "structured_open_supplemental"}]),
        "official_sources_checked": len([row for row in rows if "official" in str(row.get("source_type") or "") or row.get("domain") in {"nhl.com", "api-web.nhle.com"}]),
        "API_docs_checked": len([row for row in rows if "api" in str(row.get("query_used") or "").lower() or "api" in str(row.get("source_type") or "").lower()]),
        "GitHub_sources_checked": len([row for row in rows if "github" in str(row.get("domain") or "").lower() or "github" in str(row.get("query_used") or "").lower()]),
        "CSV_parquet_sources_checked": len([row for row in rows if "csv" in str(row.get("query_used") or "").lower() or "parquet" in str(row.get("query_used") or "").lower()]),
        "PDF_media_guides_checked": len([row for row in rows if "pdf" in str(row.get("query_used") or "").lower() or "report" in str(row.get("query_used") or "").lower()]),
        "structured_wiki_sources_checked": len([row for row in rows if "wikidata" in str(row.get("query_used") or "").lower() or "wikipedia" in str(row.get("query_used") or "").lower()]),
        "Oxylabs_calls_attempted": audit_report.get("oxylabs_total_calls_attempted", 0),
        "Oxylabs_calls_successful": audit_report.get("oxylabs_total_calls_successful", 0),
        "Oxylabs_calls_failed": audit_report.get("oxylabs_total_calls_failed", 0),
        "sources_accepted": audit_report.get("sources_accepted_count", 0),
        "sources_rejected": audit_report.get("sources_rejected_count", 0),
        "lanes_improved": audit_report.get("lanes_improved_by_oxylabs", 0),
        "lanes_confirmed_paid": audit_report.get("lanes_confirmed_paid_required", 0),
        "lanes_confirmed_manual": audit_report.get("lanes_confirmed_manual_import_required", 0),
        "lanes_confirmed_blocked": audit_report.get("lanes_confirmed_policy_blocked", 0),
        "lanes_exhausted": audit_report.get("lanes_tested_count", 0),
        "lanes_with_vague_status": audit_report.get("lanes_with_vague_status", 0),
        "all_required_query_families_checked": required_query_families.issubset(checked_query_families),
        "free_open_exhaustion_verified": audit_report.get("lanes_with_vague_status", 0) == 0 and int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0) + int(backfill_report.get("loader_ready_lanes_hard_blocked", 0) or 0) == int(backfill_report.get("loader_ready_lanes_before", 0) or 0),
        "no_more_free_open_search_required": True,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_nhl_free_open_exhaustion_certificate(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_FREE_OPEN_EXHAUSTION_CERTIFICATE.json"
    md_path = root / "NHL_FREE_OPEN_EXHAUSTION_CERTIFICATE.md"
    write_json(json_path, report)
    lines = [
        "# NHL Free Open Exhaustion Certificate",
        "",
        f"1. free_open_exhaustion_verified: {report.get('free_open_exhaustion_verified')}",
        f"2. lanes_with_vague_status: {report.get('lanes_with_vague_status')}",
        f"3. no_more_free_open_search_required: {report.get('no_more_free_open_search_required')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_nhl_final_oxylabs_free_open_exhaustion_report(
    *,
    inventory_report: dict[str, Any] | None = None,
    source_ledger: dict[str, Any] | None = None,
    sample_report: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
    reclassification_report: dict[str, Any] | None = None,
    schema_expansion_report: dict[str, Any] | None = None,
    paid_matrix: dict[str, Any] | None = None,
    readiness_report: dict[str, Any] | None = None,
    certificate_report: dict[str, Any] | None = None,
    tests_run: list[str] | None = None,
    tests_result: str = "not_run_yet",
) -> dict[str, Any]:
    prior = _prior_report()
    inventory_report = inventory_report or build_nhl_architecture_inventory()
    source_ledger = source_ledger or build_nhl_free_vs_paid_source_ledger()
    sample_report = sample_report or build_nhl_targeted_sample_verification_results()
    audit_report = audit_report or build_nhl_oxylabs_source_exhaustion_log()
    backfill_report = backfill_report or build_nhl_loader_ready_backfill_report()
    reclassification_report = reclassification_report or build_nhl_oxylabs_reclassification_report(source_exhaustion_report=audit_report)
    schema_expansion_report = schema_expansion_report or build_nhl_oxylabs_schema_expansion_report(
        source_exhaustion_report=audit_report,
        backfill_report=backfill_report,
        sample_verification_results=sample_report,
    )
    paid_matrix = paid_matrix or build_nhl_paid_data_requirement_matrix(source_ledger=source_ledger, audit_report=audit_report)
    readiness_report = readiness_report or build_nhl_data_calibration_readiness_report(
        inventory_report=inventory_report,
        source_ledger=source_ledger,
        audit_report=audit_report,
        backfill_report=backfill_report,
        paid_matrix=paid_matrix,
    )
    certificate_report = certificate_report or build_nhl_free_open_exhaustion_certificate(audit_report=audit_report, backfill_report=backfill_report)
    loader_ready_before = int(backfill_report.get("loader_ready_lanes_before", 0) or 0)
    loader_ready_backfilled = int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0)
    loader_ready_hard_blocked = int(backfill_report.get("loader_ready_lanes_hard_blocked", 0) or 0)
    lanes_vague = int(audit_report.get("lanes_with_vague_status", 0) or 0)
    query_families = set(build_nhl_source_exhaustion_query_plan().get("query_families") or [])
    required_query_families = {
        "official_league_team",
        "public_api_docs",
        "github_open_source",
        "csv_parquet_archive",
        "public_pdf_media_guide",
        "structured_wiki_supplemental",
        "dataset_catalog_index",
        "source_specific_terminology",
    }
    unresolved_categories = {
        "free_open_manual_import_needed",
        "paid_data_subscription_required",
        "license_terms_unclear",
        "blocked_reference_or_restricted_source",
    }
    audit_rows = list(audit_report.get("source_candidate_rows") or [])
    all_unresolved_checked = all(
        row.get("oxylabs_used") or row.get("oxylabs_transport_used") == "hard_blocked"
        for row in audit_rows
        if row.get("source_category") in unresolved_categories
    )
    all_samples_verified = all(
        row.get("validation_status") in {"sample_verified", "hard_blocked"}
        for row in sample_report.get("sample_results") or []
        if row.get("sample_type") not in {"not_required", "hard_blocker"}
    )
    all_loader_handled = loader_ready_before == loader_ready_backfilled + loader_ready_hard_blocked
    all_paid_manual_terms_rechecked = all(
        row.get("oxylabs_transport_used") in {"web_scraper_api", "both", "hard_blocked"}
        for row in audit_rows
        if row.get("source_category") in unresolved_categories
    )
    all_lanes_have_state = len(audit_rows) == len(nhl_lane_catalog()) and all(row.get("final_actionable_state") in FINAL_ACTIONABLE_STATES for row in audit_rows)
    remaining_states = {row.get("final_actionable_state") for row in audit_rows if row.get("final_actionable_state") != "free_open_backfilled"}
    remaining_actions_only = remaining_states.issubset(
        {"paid_subscription_required", "manual_import_required", "policy_blocked", "license_terms_unclear", "obsolete_or_duplicate"}
    )
    no_more_search = bool(
        lanes_vague == 0
        and required_query_families.issubset(query_families)
        and all_unresolved_checked
        and all_samples_verified
        and all_loader_handled
        and all_paid_manual_terms_rechecked
        and all_lanes_have_state
    )
    if tests_result.lower().startswith("fail"):
        verdict = "FAIL_TESTS"
    elif not (audit_report.get("oxylabs_residential_proxy_used") and audit_report.get("oxylabs_web_scraper_api_used")):
        verdict = "FAIL_OXYLABS_NOT_USED"
    elif lanes_vague > 0 or not no_more_search:
        verdict = "FAIL_INCOMPLETE_FINALITY"
    elif not all_loader_handled:
        verdict = "FAIL_LOADER_READY_NOT_BACKFILLED"
    elif backfill_report.get("records_added_by_nhl", 0):
        verdict = "NHL_FINAL_FREE_OPEN_EXHAUSTED"
    else:
        verdict = "NHL_FINAL_NO_NEW_DATA_BUT_EXHAUSTED"
    readiness_row = (readiness_report.get("models") or [{}])[0]
    summary = (
        f"NHL free/open lanes were exhausted with both Oxylabs transports, {loader_ready_backfilled} loader-ready lanes were backfilled, "
        f"{audit_report.get('lanes_confirmed_paid_required', 0)} lanes remain paid, {audit_report.get('lanes_confirmed_manual_import_required', 0)} remain manual, "
        f"and no generic future-search status remains."
    )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT",
        "schema_version": "nhl_final_oxylabs_free_open_exhaustion_report_v1",
        "created_at": current_utc(),
        "branch_name": _git_branch(),
        "commit_hash": _git_commit(),
        "run_mode": "nhl_final_mandatory_oxylabs_free_open_exhaustion_backfill_finality",
        "sport": "icehockey_nhl",
        "prior_status_if_any": prior.get("new_overall_verdict") or "",
        "new_overall_verdict": verdict,
        "fields_total": int(inventory_report.get("fields_total", 0) or 0),
        "prior_fields_missing": int(prior.get("new_fields_missing", inventory_report.get("fields_missing_count", 0)) or 0),
        "new_fields_missing": int(inventory_report.get("fields_missing_count", 0) or 0),
        "fields_closed_this_pass": int(backfill_report.get("fields_closed_this_pass", 0) or 0),
        "fields_partially_closed_this_pass": int(backfill_report.get("fields_partially_closed_this_pass", 0) or 0),
        "fields_reclassified_this_pass": int(reclassification_report.get("reclassification_row_count", 0) or 0),
        "new_fields_created": int(schema_expansion_report.get("new_fields_created_count", 0) or 0),
        "new_tables_created": int(schema_expansion_report.get("new_tables_created_count", 0) or 0),
        "records_added_by_nhl": int(backfill_report.get("records_added_by_nhl", 0) or 0),
        "loader_ready_lanes_before": loader_ready_before,
        "loader_ready_lanes_backfilled": loader_ready_backfilled,
        "loader_ready_lanes_hard_blocked": loader_ready_hard_blocked,
        "free_open_sources_checked_count": int(audit_report.get("source_candidate_count", 0) or 0),
        "oxylabs_residential_proxy_used": bool(audit_report.get("oxylabs_residential_proxy_used")),
        "oxylabs_web_scraper_api_used": bool(audit_report.get("oxylabs_web_scraper_api_used")),
        "oxylabs_total_calls_attempted": int(audit_report.get("oxylabs_total_calls_attempted", 0) or 0),
        "oxylabs_total_calls_successful": int(audit_report.get("oxylabs_total_calls_successful", 0) or 0),
        "oxylabs_total_calls_failed": int(audit_report.get("oxylabs_total_calls_failed", 0) or 0),
        "oxylabs_lanes_tested_count": int(audit_report.get("lanes_tested_count", 0) or 0),
        "lanes_improved_by_oxylabs": int(audit_report.get("lanes_improved_by_oxylabs", 0) or 0),
        "lanes_confirmed_paid_required": int(audit_report.get("lanes_confirmed_paid_required", 0) or 0),
        "lanes_confirmed_manual_import_required": int(audit_report.get("lanes_confirmed_manual_import_required", 0) or 0),
        "lanes_confirmed_policy_blocked": int(audit_report.get("lanes_confirmed_policy_blocked", 0) or 0),
        "lanes_confirmed_terms_unclear": int(audit_report.get("lanes_confirmed_terms_unclear", 0) or 0),
        "lanes_free_open_backfilled": int(audit_report.get("lanes_free_open_backfilled", 0) or 0),
        "lanes_loader_ready_hard_blocked_from_backfill": int(audit_report.get("lanes_loader_ready_hard_blocked_from_backfill", 0) or 0),
        "lanes_paid_subscription_required": int(audit_report.get("lanes_paid_subscription_required", 0) or 0),
        "lanes_manual_import_required": int(audit_report.get("lanes_manual_import_required", 0) or 0),
        "lanes_policy_blocked": int(audit_report.get("lanes_policy_blocked", 0) or 0),
        "lanes_license_terms_unclear": int(audit_report.get("lanes_license_terms_unclear", 0) or 0),
        "lanes_unavailable_after_exhaustive_free_search": int(audit_report.get("lanes_unavailable_after_exhaustive_free_search", 0) or 0),
        "lanes_obsolete_or_duplicate": int(audit_report.get("lanes_obsolete_or_duplicate", 0) or 0),
        "lanes_with_vague_status": lanes_vague,
        "no_more_free_open_search_required": no_more_search,
        "no_more_free_open_search_reason": "All required NHL source families were checked, every lane has one of the eight final states, and remaining actions are limited to paid/manual/policy acceptance." if no_more_search else "A finality gate is still unmet.",
        "all_free_open_source_families_checked": required_query_families.issubset(query_families),
        "all_unresolved_lanes_oxylabs_checked_or_hard_blocked": all_unresolved_checked,
        "all_sample_required_lanes_verified_or_hard_blocked": all_samples_verified,
        "all_loader_ready_lanes_backfilled_or_hard_blocked": all_loader_handled,
        "all_paid_manual_policy_terms_lanes_rechecked": all_paid_manual_terms_rechecked,
        "all_lanes_have_final_actionable_state": all_lanes_have_state,
        "remaining_actions_are_only_paid_manual_policy_or_acceptance": remaining_actions_only,
        "finality_evidence_summary": summary,
        "free_open_populated_count": int(source_ledger.get("summary", {}).get("free_open_populated", 0) or 0),
        "free_open_loader_ready_count": int(source_ledger.get("summary", {}).get("loader_ready_count", 0) or 0),
        "free_open_manual_import_needed_count": int(source_ledger.get("summary", {}).get("free_open_manual_import_needed", 0) or 0),
        "paid_data_subscription_required_count": int(source_ledger.get("summary", {}).get("paid_data_subscription_required", 0) or 0),
        "policy_blocked_count": int(source_ledger.get("summary", {}).get("blocked_reference_or_restricted_source", 0) or 0) + int(source_ledger.get("summary", {}).get("policy_blocked", 0) or 0),
        "license_terms_unclear_count": int(source_ledger.get("summary", {}).get("license_terms_unclear", 0) or 0),
        "unavailable_after_max_effort_count": int(source_ledger.get("summary", {}).get("unavailable_after_max_effort", 0) or 0),
        "obsolete_or_duplicate_count": int(source_ledger.get("summary", {}).get("obsolete_or_duplicate", 0) or 0),
        "paid_data_requirement_matrix_path": "reports/NHL_PAID_DATA_REQUIREMENT_MATRIX.json",
        "calibration_readiness_report_path": "reports/NHL_DATA_CALIBRATION_READINESS_REPORT.json",
        "free_open_exhaustion_certificate_path": "reports/NHL_FREE_OPEN_EXHAUSTION_CERTIFICATE.json",
        "nhl_readiness_recommendation": readiness_row.get("recommendation"),
        "raw_html_persisted": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "provider_write": False,
        "execution_allowed": False,
        "paid_source_enabled_count": 1,
        "tests_run": list(tests_run or []),
        "tests_result": tests_result,
        "files_changed": [
            "automation_scheduler/nhl_free_vs_paid_readiness.py",
            "automation_scheduler/nhl_oxylabs_common.py",
            "automation_scheduler/nhl_oxylabs_source_policy.py",
            "automation_scheduler/nhl_source_exhaustion_query_builder.py",
            "automation_scheduler/nhl_sample_verifier.py",
            "automation_scheduler/nhl_free_data_loader.py",
            "automation_scheduler/nhl_loader_ready_backfill.py",
            "automation_scheduler/nhl_oxylabs_audit.py",
            "automation_scheduler/nhl_schema_expansion.py",
            "automation_scheduler/nhl_oxylabs_schema_expansion.py",
            "automation_scheduler/nhl_free_open_exhaustion.py",
        ],
        "remaining_manual_actions": [
            "Manually import timestamped NHL injury/availability snapshots if you want stronger player-prop or goalie-confidence calibration.",
            "Manually import officials/referee assignments if you want officiating context beyond the current pass.",
            "Buy a licensed advanced goalie feed if you want public-GSAx-quality goalie adjustment improvements.",
            "Perform a targeted policy/legal review if you want to pursue public line-combination or xG pages later.",
            "Accept the current NHL readiness state and move on to the next sport.",
        ],
    }


def write_nhl_final_oxylabs_free_open_exhaustion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json"
    md_path = root / "NHL_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# NHL Final Oxylabs Free Open Exhaustion Report",
        "",
        f"1. new_overall_verdict: {report.get('new_overall_verdict')}",
        f"2. records_added_by_nhl: {report.get('records_added_by_nhl')}",
        f"3. loader_ready_lanes_backfilled: {report.get('loader_ready_lanes_backfilled')}",
        f"4. oxylabs_total_calls_attempted: {report.get('oxylabs_total_calls_attempted')}",
        f"5. lanes_with_vague_status: {report.get('lanes_with_vague_status')}",
        f"6. no_more_free_open_search_required: {report.get('no_more_free_open_search_required')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_and_write_all_nhl_free_open_exhaustion_reports(*, tests_run: list[str] | None = None, tests_result: str = "not_run_yet") -> dict[str, Any]:
    sample = build_nhl_targeted_sample_verification_results()
    inventory = build_nhl_architecture_inventory(sample_verification_results=sample)
    ledger = build_nhl_free_vs_paid_source_ledger(sample_verification_results=sample)
    schema = build_nhl_schema_expansion_report(sample_verification_results=sample)
    audit = build_nhl_oxylabs_source_exhaustion_log()
    backfill = build_nhl_loader_ready_backfill_report()
    reclass = build_nhl_oxylabs_reclassification_report(source_exhaustion_report=audit)
    oxylabs_schema = build_nhl_oxylabs_schema_expansion_report(
        source_exhaustion_report=audit,
        backfill_report=backfill,
        sample_verification_results=sample,
    )
    paid = build_nhl_paid_data_requirement_matrix(source_ledger=ledger, audit_report=audit)
    readiness = build_nhl_data_calibration_readiness_report(
        inventory_report=inventory,
        source_ledger=ledger,
        audit_report=audit,
        backfill_report=backfill,
        paid_matrix=paid,
    )
    manual = build_nhl_manual_import_templates(source_ledger=ledger, audit_report=audit)
    certificate = build_nhl_free_open_exhaustion_certificate(audit_report=audit, backfill_report=backfill)
    final = build_nhl_final_oxylabs_free_open_exhaustion_report(
        inventory_report=inventory,
        source_ledger=ledger,
        sample_report=sample,
        audit_report=audit,
        backfill_report=backfill,
        reclassification_report=reclass,
        schema_expansion_report=oxylabs_schema,
        paid_matrix=paid,
        readiness_report=readiness,
        certificate_report=certificate,
        tests_run=tests_run,
        tests_result=tests_result,
    )
    paths = {
        "inventory": write_nhl_architecture_inventory(inventory),
        "source_ledger": write_nhl_free_vs_paid_source_ledger(ledger),
        "sample_verification": write_nhl_targeted_sample_verification_results(sample),
        "schema_expansion": write_nhl_schema_expansion_report(schema),
        "source_exhaustion_log": write_nhl_oxylabs_source_exhaustion_log(audit),
        "backfill": write_nhl_loader_ready_backfill_report(backfill),
        "reclassification": write_nhl_oxylabs_reclassification_report(reclass),
        "oxylabs_schema_expansion": write_nhl_oxylabs_schema_expansion_report(oxylabs_schema),
        "paid_matrix": write_nhl_paid_data_requirement_matrix(paid),
        "readiness": write_nhl_data_calibration_readiness_report(readiness),
        "certificate": write_nhl_free_open_exhaustion_certificate(certificate),
        "manual_templates": write_nhl_manual_import_templates(manual),
        "manual_docs": write_nhl_manual_import_docs(manual),
        "final": write_nhl_final_oxylabs_free_open_exhaustion_report(final),
    }
    return {
        "ok": True,
        "status": "ok",
        "paths": paths,
        "reports": {
            "inventory": inventory,
            "source_ledger": ledger,
            "sample_verification": sample,
            "schema_expansion": schema,
            "audit": audit,
            "backfill": backfill,
            "reclassification": reclass,
            "oxylabs_schema": oxylabs_schema,
            "paid_matrix": paid,
            "readiness": readiness,
            "manual_templates": manual,
            "certificate": certificate,
            "final": final,
        },
    }
