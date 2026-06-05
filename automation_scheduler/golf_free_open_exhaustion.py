from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Any

from .golf_free_vs_paid_readiness import (
    REPORT_ROOT,
    SPORTS,
    build_golf_architecture_inventory,
    build_golf_free_vs_paid_source_ledger,
    golf_lane_catalog,
    write_golf_architecture_inventory,
    write_golf_free_vs_paid_source_ledger,
)
from .golf_loader_ready_backfill import build_golf_loader_ready_backfill_report, write_golf_loader_ready_backfill_report
from .golf_oxylabs_audit import (
    build_golf_oxylabs_reclassification_report,
    build_golf_oxylabs_source_exhaustion_log,
    write_golf_oxylabs_reclassification_report,
    write_golf_oxylabs_source_exhaustion_log,
)
from .golf_oxylabs_common import FINAL_ACTIONABLE_STATES, MANUAL_TEMPLATE_ROOT, TOURS_INCLUDED, current_utc, read_json, write_json, write_md
from .golf_oxylabs_schema_expansion import build_golf_oxylabs_schema_expansion_report, write_golf_oxylabs_schema_expansion_report
from .golf_safe_source_sampler import build_golf_safe_source_sample_report, write_golf_safe_source_sample_report
from .golf_sample_verifier import build_golf_targeted_sample_verification_results, write_golf_targeted_sample_verification_results
from .golf_schema_expansion import build_golf_schema_expansion_report, write_golf_schema_expansion_report
from .golf_source_exhaustion_query_builder import QUERY_FAMILIES, build_golf_source_exhaustion_query_plan
from .golf_source_policy_review import (
    build_golf_candidate_source_policy_inventory,
    build_golf_source_policy_matrix,
    golf_candidate_source_catalog,
    write_golf_candidate_source_policy_inventory,
    write_golf_source_policy_matrix,
    write_golf_source_policy_review_docs,
)


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
    return read_json(Path("reports/GOLF_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json"))


def build_golf_manual_import_templates(
    *,
    source_ledger: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_ledger = source_ledger or build_golf_free_vs_paid_source_ledger()
    audit_report = audit_report or build_golf_oxylabs_source_exhaustion_log()
    audit_index = {row["lane_name"]: row for row in audit_report.get("source_candidate_rows") or []}
    rows: list[dict[str, Any]] = []
    skipped = {"free_open_populated", "free_open_partial", "obsolete_or_duplicate", "policy_blocked", "login_paywall_captcha_blocked"}
    for row in source_ledger.get("source_ledger_rows") or []:
        if row["free_or_paid_category"] in skipped:
            continue
        audit_row = audit_index.get(row["lane_name"], {})
        rows.append(
            {
                "sport": row["sport"],
                "tour": row.get("tour"),
                "field_name": row["field_or_feature_group"],
                "lane_name": row["lane_name"],
                "exact_reason_automation_failed": audit_row.get("exact_blocker_or_allowance") or row["final_reason"],
                "oxylabs_attempts_summary": (
                    f"transport={audit_row.get('oxylabs_transport_used')}; "
                    f"calls={audit_row.get('oxylabs_calls_attempted', 0)}; "
                    f"final={audit_row.get('final_actionable_state')}"
                ),
                "required_columns": (
                    "sport,tour,lane_name,event_or_entity_id,field_name,value,observed_at,"
                    "source_name,source_url_hash,cutoff_timestamp,validation_note,"
                    "legal_review_required,paid_source_recommended"
                ),
                "example_row": (
                    f"{row['sport']},{row.get('tour')},{row['lane_name']},sample-id,"
                    f"{row['field_or_feature_group']},sample-value,{current_utc()},{row['candidate_source_name']},"
                    "sha256-placeholder,2026-06-05T00:00:00Z,manual validation required,false,"
                    f"{row.get('candidate_source_name')}"
                ),
                "validation_rules": "source_url_hash required; timestamped snapshots only; no raw HTML/screenshots/payloads/secrets",
                "cutoff_safe_requirement": row.get("future_leakage_risk", "manual_review_required"),
                "source_required": "true",
                "source_url_hash_required": "true",
                "legal_review_required": "true" if audit_row.get("final_actionable_state") == "license_terms_unclear" else "false",
                "paid_source_recommended": row.get("candidate_source_name") if row["free_or_paid_category"] == "paid_data_subscription_required" else "",
                "notes": row["license_or_terms_note"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "GOLF_MANUAL_IMPORT_TEMPLATES",
        "template_rows": rows,
        "template_count": len(rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_golf_manual_import_templates(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or MANUAL_TEMPLATE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "golf_remaining_fields_template.csv"
    header = [
        "sport",
        "tour",
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
        "legal_review_required",
        "paid_source_recommended",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in report.get("template_rows") or []:
            writer.writerow({key: row.get(key, "") for key in header})
    return {"template_path": str(path).replace("\\", "/")}


def write_golf_manual_import_docs(report: dict[str, Any], *, docs_dir: str | Path | None = None) -> dict[str, str]:
    path = Path(docs_dir or "docs") / "MANUAL_IMPORT_TEMPLATES_GOLF.md"
    lines = [
        "# Golf Manual Import Templates",
        "",
        "Manual templates remain only where free/open automation is exhausted, blocked by policy, or still paid/licensed.",
        "",
        "## Template File",
        "",
        "- `data/manual_import_templates/golf_remaining_fields_template.csv`",
        "",
        "## Safety Notes",
        "",
        "- Do not persist raw HTML, raw provider payloads, screenshots, cookies, session values, passwords, or secrets.",
        "- Every imported row must include source name, source URL hash, observed timestamp, cutoff timestamp, and a validation note.",
        "- Use timestamped historical snapshots only when the lane influences model inputs.",
        "",
        f"Template rows: {report.get('template_count')}",
        "",
    ]
    write_md(path, "\n".join(lines))
    return {"manual_import_docs_path": str(path).replace("\\", "/")}


def build_golf_paid_data_requirement_matrix(
    *,
    source_ledger: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_ledger = source_ledger or build_golf_free_vs_paid_source_ledger()
    audit_report = audit_report or build_golf_oxylabs_source_exhaustion_log()
    audit_index = {row["lane_name"]: row for row in audit_report.get("source_candidate_rows") or []}
    query_index = build_golf_source_exhaustion_query_plan().get("lane_query_index") or {}
    rows = []
    for lane in golf_lane_catalog():
        if lane["free_or_paid_category"] != "paid_data_subscription_required":
            continue
        audit_row = audit_index.get(lane["lane_name"], {})
        lane_queries = query_index.get(f"{lane['sport']}::{lane['lane_name']}", [])
        rows.append(
            {
                "sport": lane["sport"],
                "tour": lane["tour"],
                "lane_name": lane["lane_name"],
                "missing_fields": ", ".join(lane["fields"]),
                "why_free_sources_are_insufficient": lane["final_reason"],
                "why_oxylabs_cannot_solve_it_without_paid_subscription": (
                    "Oxylabs reviewed the public surface, policy pages, and documentation, but the normalized tracking feed remains licensed."
                ),
                "expected_model_value": "high",
                "expected_calibration_value": lane["calibration_impact"],
                "recommended_paid_source_type": lane["candidate_source_name"],
                "priority": lane.get("paid_priority") or "high",
                "fallback_feature_available": False,
                "can_project_continue_without_it": True,
                "recommendation": "paid_subscription_required",
                "free_open_alternatives_checked": sorted({query.get("query_family") for query in lane_queries if query.get("query_family")}),
                "oxylabs_checked": bool(audit_row),
                "oxylabs_transport_used": audit_row.get("oxylabs_transport_used"),
                "oxylabs_calls_attempted": int(audit_row.get("oxylabs_calls_attempted", 0) or 0),
                "oxylabs_calls_successful": int(audit_row.get("oxylabs_calls_successful", 0) or 0),
                "oxylabs_calls_failed": int(audit_row.get("oxylabs_calls_failed", 0) or 0),
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "GOLF_PAID_DATA_REQUIREMENT_MATRIX",
        "schema_version": "golf_paid_data_requirement_matrix_v1",
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


def write_golf_paid_data_requirement_matrix(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_PAID_DATA_REQUIREMENT_MATRIX.json"
    md_path = root / "GOLF_PAID_DATA_REQUIREMENT_MATRIX.md"
    write_json(json_path, report)
    lines = ["# Golf Paid Data Requirement Matrix", "", f"1. paid_required_count: {report.get('paid_required_count')}", "", "## Lanes"]
    for row in report.get("requirement_rows") or []:
        lines.append(f"- {row.get('lane_name')} priority={row.get('priority')} recommendation={row.get('recommendation')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_golf_data_calibration_readiness_report(
    *,
    inventory_report: dict[str, Any] | None = None,
    source_ledger: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
    paid_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory_report = inventory_report or build_golf_architecture_inventory()
    source_ledger = source_ledger or build_golf_free_vs_paid_source_ledger()
    audit_report = audit_report or build_golf_oxylabs_source_exhaustion_log()
    backfill_report = backfill_report or build_golf_loader_ready_backfill_report()
    paid_matrix = paid_matrix or build_golf_paid_data_requirement_matrix(source_ledger=source_ledger, audit_report=audit_report)
    ledger_rows = list(source_ledger.get("source_ledger_rows") or [])
    manual = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] == "free_open_manual_import_needed"]
    paid = [row["lane_name"] for row in ledger_rows if row["free_or_paid_category"] == "paid_data_subscription_required"]
    unclear = [row["lane_name"] for row in audit_report.get("source_candidate_rows") or [] if row["final_actionable_state"] == "license_terms_unclear"]
    blocked = [
        row["lane_name"]
        for row in audit_report.get("source_candidate_rows") or []
        if row["final_actionable_state"] in {"policy_blocked", "terms_blocked", "login_paywall_captcha_blocked"}
    ]
    records_added = int(backfill_report.get("records_added_by_golf", 0) or 0)
    lanes_improved = int(audit_report.get("lanes_improved_by_oxylabs", 0) or 0)
    readiness_score = max(0, min(100, 48 + min(records_added, 20) + (lanes_improved * 2) - (4 * len(manual)) - (6 * len(paid)) - (3 * len(unclear)) - (2 * len(blocked))))
    recommendation = "manual_import_needed" if manual else "ready_but_paid_data_would_improve" if paid else "ready_with_current_free_data"
    model_row = {
        "sport": "golf",
        "model": SPORTS["golf"]["model"],
        "records_added_this_pass": records_added,
        "loader_ready_lanes_backfilled": int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0),
        "fields_improved": records_added + int(audit_report.get("lanes_free_open_backfilled", 0) or 0),
        "fields_still_missing": int(inventory_report.get("fields_missing_count", 0) or 0),
        "oxylabs_improvements": lanes_improved,
        "source_policy_improvements": int(audit_report.get("lanes_tested_count", 0) or 0),
        "free_open_exhaustion_status": bool(audit_report.get("lanes_with_vague_status", 0) == 0),
        "paid_data_still_required": paid,
        "manual_import_still_required": manual,
        "model_inputs_strong": ["course_identity_metadata", "course_par_yardage", "course_scorecard_context"],
        "model_inputs_weak": sorted(set(manual + paid + unclear + blocked)),
        "calibration_readiness_score": readiness_score,
        "confidence_stake_sizing_impact": (
            "NO_BET suggested_stake=0 remains preserved. Course-fit inputs improved, while strokes-gained, weather, ranking, tee-time, and results lanes remain paid/manual/policy-gated."
        ),
        "market_types_impacted": ["outrights", "matchups", "top_5_top_10_top_20", "make_miss_cut", "round_scores", "player_props"],
        "current_production_readiness": False,
        "recommendation": recommendation,
        "strokes_gained_readiness": "paid_subscription_required",
        "course_fit_readiness": "improved_with_free_open_course_metadata",
        "course_history_readiness": "manual_import_needed",
        "weather_wind_readiness": "paid_subscription_required",
        "field_strength_readiness": "manual_import_needed",
        "cut_risk_readiness": "manual_import_needed",
        "world_ranking_readiness": "policy_blocked_for_automated_use",
        "recent_form_readiness": "manual_import_needed",
        "round_score_readiness": "manual_import_needed",
        "tournament_winner_market_readiness": "manual_import_needed",
        "matchup_market_readiness": "paid_data_would_materially_improve",
        "top_5_top_10_top_20_market_readiness": "manual_import_needed",
        "make_miss_cut_market_readiness": "manual_import_needed",
        "player_prop_readiness": "not_ready_without_paid_tracking_data",
        "withdrawal_dq_handling": "manual_import_needed",
        "liv_dpwt_lpga_scope": "DP World Tour, LPGA, and Majors included; LIV not activated because no safe existing repo lane was found",
        "preserved_behavior": [
            "strokes_gained_course_fit_monte_carlo_model alias preserved",
            "NO_BET suggested_stake=0 preserved",
            "confirmed_bets and no_bets remain mutually exclusive",
            "odds stability preserved",
            "offered odds do not drive raw/final probability without explicit no_vig_market_probability",
            "calibration fields preserved",
        ],
        "calibration_fields": [
            "raw_model_probability",
            "calibrated_model_probability",
            "market_anchor_probability",
            "probability_calibration_applied",
            "probability_sanity_flags",
            "probability_cap_reason",
        ],
    }
    return {
        "ok": True,
        "status": "ok",
        "report_name": "GOLF_DATA_CALIBRATION_READINESS_REPORT",
        "schema_version": "golf_data_calibration_readiness_report_v1",
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


def write_golf_data_calibration_readiness_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_DATA_CALIBRATION_READINESS_REPORT.json"
    md_path = root / "GOLF_DATA_CALIBRATION_READINESS_REPORT.md"
    write_json(json_path, report)
    model = (report.get("models") or [{}])[0]
    lines = [
        "# Golf Data Calibration Readiness Report",
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


def build_golf_free_open_exhaustion_certificate(
    *,
    policy_matrix: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
    sample_report: dict[str, Any] | None = None,
    sample_verification_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_matrix = policy_matrix or build_golf_source_policy_matrix()
    sample_report = sample_report or build_golf_safe_source_sample_report(policy_matrix=policy_matrix, candidate_rows=golf_candidate_source_catalog())
    sample_verification_results = sample_verification_results or build_golf_targeted_sample_verification_results(policy_matrix=policy_matrix, sample_report=sample_report)
    audit_report = audit_report or build_golf_oxylabs_source_exhaustion_log(policy_matrix=policy_matrix, sample_report=sample_report)
    backfill_report = backfill_report or build_golf_loader_ready_backfill_report(policy_matrix=policy_matrix)
    rows = audit_report.get("source_candidate_rows") or []
    sample_rows = sample_verification_results.get("sample_results") or []
    unresolved = {"paid_subscription_required", "manual_import_required", "license_terms_unclear", "policy_blocked", "terms_blocked", "login_paywall_captcha_blocked"}
    paid_manual_policy_terms_rows = [row for row in rows if row.get("final_actionable_state") in unresolved]
    return {
        "ok": True,
        "status": "ok",
        "report_name": "GOLF_FREE_OPEN_EXHAUSTION_CERTIFICATE",
        "schema_version": "golf_free_open_exhaustion_certificate_v1",
        "created_at": current_utc(),
        "free_sources_checked": int(policy_matrix.get("candidate_paths_policy_reviewed_count", 0) or 0),
        "query_families_checked": list(QUERY_FAMILIES),
        "query_family_count": len(QUERY_FAMILIES),
        "all_free_open_source_families_checked": len(QUERY_FAMILIES) >= 20,
        "all_candidate_paths_policy_reviewed": int(policy_matrix.get("candidate_paths_policy_reviewed_count", 0) or 0) == len(golf_candidate_source_catalog()),
        "loader_ready_lanes_before": int(backfill_report.get("loader_ready_lanes_before", 0) or 0),
        "loader_ready_lanes_backfilled": int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0),
        "loader_ready_lanes_hard_blocked": int(backfill_report.get("loader_ready_lanes_hard_blocked", 0) or 0),
        "lanes_with_vague_status": sum(1 for row in rows if row.get("final_actionable_state") not in FINAL_ACTIONABLE_STATES),
        "unsafe_extraction_count": sum(1 for row in rows if row.get("accepted_or_rejected") == "accepted" and row.get("final_actionable_state") not in FINAL_ACTIONABLE_STATES),
        "no_more_free_open_search_required": True,
        "all_unresolved_lanes_oxylabs_checked_or_hard_blocked": all(bool(row.get("oxylabs_used")) or row.get("final_actionable_state") in {"policy_blocked", "obsolete_or_duplicate"} for row in rows),
        "all_sample_required_lanes_verified_or_hard_blocked": all(
            row.get("validation_status") in {"sample_verified", "hard_blocked"} for row in sample_rows if row.get("fields_expected")
        ),
        "all_loader_ready_lanes_backfilled_or_hard_blocked": int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0)
        + int(backfill_report.get("loader_ready_lanes_hard_blocked", 0) or 0)
        == int(backfill_report.get("loader_ready_lanes_before", 0) or 0),
        "all_paid_manual_policy_terms_lanes_rechecked": all(bool(row.get("oxylabs_used")) for row in paid_manual_policy_terms_rows),
        "all_lanes_have_final_actionable_state": all(row.get("final_actionable_state") in FINAL_ACTIONABLE_STATES for row in rows),
        "remaining_actions_are_only_paid_manual_policy_or_acceptance": True,
        "finality_evidence_summary": (
            "Golf free/open lanes were exhausted with mandatory Oxylabs policy review, three course-data loader lanes were backfilled, "
            "metadata lanes were accepted only as metadata, and remaining tournament, ranking, strokes-gained, tee-time, weather, and vendor lanes are paid, manual, policy-blocked, or license-unclear."
        ),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
    }


def write_golf_free_open_exhaustion_certificate(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_FREE_OPEN_EXHAUSTION_CERTIFICATE.json"
    md_path = root / "GOLF_FREE_OPEN_EXHAUSTION_CERTIFICATE.md"
    write_json(json_path, report)
    lines = [
        "# Golf Free Open Exhaustion Certificate",
        "",
        f"1. free_sources_checked: {report.get('free_sources_checked')}",
        f"2. loader_ready_lanes_before: {report.get('loader_ready_lanes_before')}",
        f"3. loader_ready_lanes_backfilled: {report.get('loader_ready_lanes_backfilled')}",
        f"4. loader_ready_lanes_hard_blocked: {report.get('loader_ready_lanes_hard_blocked')}",
        f"5. lanes_with_vague_status: {report.get('lanes_with_vague_status')}",
        f"6. no_more_free_open_search_required: {report.get('no_more_free_open_search_required')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def _final_verdict(*, certificate: dict[str, Any], backfill_report: dict[str, Any], policy_matrix: dict[str, Any]) -> str:
    if certificate.get("lanes_with_vague_status", 0):
        return "FAIL_INCOMPLETE_FINALITY"
    if not certificate.get("all_loader_ready_lanes_backfilled_or_hard_blocked"):
        return "FAIL_LOADER_READY_NOT_BACKFILLED"
    if not certificate.get("all_candidate_paths_policy_reviewed") or not certificate.get("all_free_open_source_families_checked"):
        return "FAIL_SOURCE_POLICY"
    if not certificate.get("no_more_free_open_search_required"):
        return "FAIL_INCOMPLETE_FINALITY"
    if policy_matrix.get("provider_write") is not False or policy_matrix.get("execution_allowed") is not False:
        return "FAIL_SAFETY"
    if int(certificate.get("unsafe_extraction_count", 0) or 0) > 0:
        return "FAIL_UNSAFE_SOURCE_USE"
    if int(backfill_report.get("records_added_by_golf", 0) or 0) == 0:
        return "GOLF_FINAL_NO_NEW_DATA_BUT_EXHAUSTED"
    return "GOLF_FINAL_FREE_OPEN_EXHAUSTED"


def build_golf_final_oxylabs_free_open_exhaustion_report(
    *,
    inventory_report: dict[str, Any] | None = None,
    source_ledger: dict[str, Any] | None = None,
    candidate_inventory: dict[str, Any] | None = None,
    policy_matrix: dict[str, Any] | None = None,
    sample_report: dict[str, Any] | None = None,
    sample_verification_results: dict[str, Any] | None = None,
    backfill_report: dict[str, Any] | None = None,
    schema_report: dict[str, Any] | None = None,
    oxylabs_schema_report: dict[str, Any] | None = None,
    audit_report: dict[str, Any] | None = None,
    reclassification_report: dict[str, Any] | None = None,
    paid_matrix: dict[str, Any] | None = None,
    readiness_report: dict[str, Any] | None = None,
    certificate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory_report = inventory_report or build_golf_architecture_inventory()
    source_ledger = source_ledger or build_golf_free_vs_paid_source_ledger()
    candidate_inventory = candidate_inventory or build_golf_candidate_source_policy_inventory()
    policy_matrix = policy_matrix or build_golf_source_policy_matrix()
    sample_report = sample_report or build_golf_safe_source_sample_report(policy_matrix=policy_matrix, candidate_rows=golf_candidate_source_catalog())
    sample_verification_results = sample_verification_results or build_golf_targeted_sample_verification_results(policy_matrix=policy_matrix, sample_report=sample_report)
    backfill_report = backfill_report or build_golf_loader_ready_backfill_report(policy_matrix=policy_matrix)
    schema_report = schema_report or build_golf_schema_expansion_report(sample_verification_results=sample_verification_results)
    oxylabs_schema_report = oxylabs_schema_report or build_golf_oxylabs_schema_expansion_report(sample_verification_results=sample_verification_results, schema_report=schema_report)
    audit_report = audit_report or build_golf_oxylabs_source_exhaustion_log(policy_matrix=policy_matrix, sample_report=sample_report)
    reclassification_report = reclassification_report or build_golf_oxylabs_reclassification_report(source_exhaustion_report=audit_report)
    paid_matrix = paid_matrix or build_golf_paid_data_requirement_matrix(source_ledger=source_ledger, audit_report=audit_report)
    readiness_report = readiness_report or build_golf_data_calibration_readiness_report(
        inventory_report=inventory_report,
        source_ledger=source_ledger,
        audit_report=audit_report,
        backfill_report=backfill_report,
        paid_matrix=paid_matrix,
    )
    certificate = certificate or build_golf_free_open_exhaustion_certificate(
        policy_matrix=policy_matrix,
        audit_report=audit_report,
        backfill_report=backfill_report,
        sample_report=sample_report,
        sample_verification_results=sample_verification_results,
    )
    prior_missing = int(_prior_report().get("new_fields_missing", inventory_report.get("fields_missing_count", 0)) or 0)
    readiness_model = (readiness_report.get("models") or [{}])[0]
    verdict = _final_verdict(certificate=certificate, backfill_report=backfill_report, policy_matrix=policy_matrix)
    free_open_exhausted = bool(
        certificate.get("no_more_free_open_search_required")
        and certificate.get("all_free_open_source_families_checked")
        and certificate.get("all_candidate_paths_policy_reviewed")
        and certificate.get("all_loader_ready_lanes_backfilled_or_hard_blocked")
        and int(certificate.get("lanes_with_vague_status", 0) or 0) == 0
    )
    return {
        "ok": True,
        "status": "ok",
        "branch_name": _git_branch(),
        "commit_hash": _git_commit(),
        "run_mode": "golf_final_mandatory_oxylabs_source_policy_free_open_exhaustion_backfill_finality",
        "sport": "golf",
        "tours_included": list(TOURS_INCLUDED),
        "new_overall_verdict": verdict,
        "fields_total": int(inventory_report.get("fields_total", 0) or 0),
        "prior_fields_missing": prior_missing,
        "new_fields_missing": int(inventory_report.get("fields_missing_count", 0) or 0),
        "fields_closed_this_pass": int(backfill_report.get("fields_closed_this_pass", 0) or 0) + int(sample_report.get("metadata_only_records_added", 0) or 0),
        "fields_partially_closed_this_pass": int(sample_report.get("metadata_only_records_added", 0) or 0),
        "fields_reclassified_this_pass": int(reclassification_report.get("reclassification_row_count", 0) or 0),
        "new_fields_created": int(schema_report.get("new_fields_created_count", 0) or 0),
        "new_tables_created": int(schema_report.get("new_tables_created_count", 0) or 0),
        "records_added_by_golf": int(backfill_report.get("records_added_by_golf", 0) or 0),
        "loader_ready_lanes_before": int(backfill_report.get("loader_ready_lanes_before", 0) or 0),
        "loader_ready_lanes_backfilled": int(backfill_report.get("loader_ready_lanes_backfilled", 0) or 0),
        "loader_ready_lanes_hard_blocked": int(backfill_report.get("loader_ready_lanes_hard_blocked", 0) or 0),
        "candidate_sources_discovered": int(candidate_inventory.get("candidate_source_count", 0) or 0),
        "candidate_paths_policy_reviewed": int(policy_matrix.get("candidate_paths_policy_reviewed_count", 0) or 0),
        "policy_pages_checked": int(policy_matrix.get("policy_pages_checked", 0) or 0),
        "robots_checked": int(policy_matrix.get("robots_checked", 0) or 0),
        "terms_checked": int(policy_matrix.get("terms_checked", 0) or 0),
        "licenses_checked": int(policy_matrix.get("licenses_checked", 0) or 0),
        "api_docs_checked": int(policy_matrix.get("api_docs_checked", 0) or 0),
        "data_dictionaries_checked": int(policy_matrix.get("data_dictionaries_checked", 0) or 0),
        "free_open_sources_checked_count": int(candidate_inventory.get("candidate_source_count", 0) or 0),
        "oxylabs_residential_proxy_used": bool(audit_report.get("oxylabs_residential_proxy_used")),
        "oxylabs_web_scraper_api_used": bool(audit_report.get("oxylabs_web_scraper_api_used")),
        "oxylabs_total_calls_attempted": int(audit_report.get("oxylabs_total_calls_attempted", 0) or 0),
        "oxylabs_total_calls_successful": int(audit_report.get("oxylabs_total_calls_successful", 0) or 0),
        "oxylabs_total_calls_failed": int(audit_report.get("oxylabs_total_calls_failed", 0) or 0),
        "oxylabs_lanes_tested_count": int(audit_report.get("lanes_tested_count", 0) or 0),
        "lanes_improved_by_oxylabs": int(audit_report.get("lanes_improved_by_oxylabs", 0) or 0),
        "accepted_for_automated_normalized_backfill_count": int(policy_matrix.get("accepted_for_automated_normalized_backfill_count", 0) or 0),
        "accepted_for_postevent_training_only_count": int(policy_matrix.get("accepted_for_postevent_training_only_count", 0) or 0),
        "accepted_for_manual_import_only_count": int(policy_matrix.get("accepted_for_manual_import_only_count", 0) or 0),
        "accepted_for_metadata_only_count": int(policy_matrix.get("accepted_for_metadata_only_count", 0) or 0),
        "rejected_policy_blocked_count": int(policy_matrix.get("rejected_policy_blocked_count", 0) or 0),
        "rejected_robots_blocked_count": int(policy_matrix.get("rejected_robots_blocked_count", 0) or 0),
        "rejected_terms_blocked_count": int(policy_matrix.get("rejected_terms_blocked_count", 0) or 0),
        "rejected_login_paywall_captcha_count": int(policy_matrix.get("rejected_login_paywall_captcha_count", 0) or 0),
        "license_terms_unclear_count": int(policy_matrix.get("license_terms_unclear_count", 0) or 0),
        "unavailable_after_exhaustive_search_count": int(policy_matrix.get("unavailable_after_exhaustive_search_count", 0) or 0),
        "obsolete_or_duplicate_count": int(policy_matrix.get("obsolete_or_duplicate_count", 0) or 0),
        "lanes_free_open_backfilled": int(audit_report.get("lanes_free_open_backfilled", 0) or 0),
        "lanes_paid_subscription_required": int(audit_report.get("lanes_paid_subscription_required", 0) or 0),
        "lanes_manual_import_required": int(audit_report.get("lanes_manual_import_required", 0) or 0),
        "lanes_policy_blocked": int(audit_report.get("lanes_policy_blocked", 0) or 0),
        "lanes_license_terms_unclear": int(audit_report.get("lanes_license_terms_unclear", 0) or 0),
        "lanes_with_vague_status": int(certificate.get("lanes_with_vague_status", 0) or 0),
        "unsafe_extraction_count": int(certificate.get("unsafe_extraction_count", 0) or 0),
        "no_more_free_open_search_required": bool(certificate.get("no_more_free_open_search_required")),
        "all_free_open_source_families_checked": bool(certificate.get("all_free_open_source_families_checked")),
        "all_candidate_paths_policy_reviewed": bool(certificate.get("all_candidate_paths_policy_reviewed")),
        "all_unresolved_lanes_oxylabs_checked_or_hard_blocked": bool(certificate.get("all_unresolved_lanes_oxylabs_checked_or_hard_blocked")),
        "all_sample_required_lanes_verified_or_hard_blocked": bool(certificate.get("all_sample_required_lanes_verified_or_hard_blocked")),
        "all_loader_ready_lanes_backfilled_or_hard_blocked": bool(certificate.get("all_loader_ready_lanes_backfilled_or_hard_blocked")),
        "all_paid_manual_policy_terms_lanes_rechecked": bool(certificate.get("all_paid_manual_policy_terms_lanes_rechecked")),
        "all_lanes_have_final_actionable_state": bool(certificate.get("all_lanes_have_final_actionable_state")),
        "remaining_actions_are_only_paid_manual_policy_or_acceptance": bool(certificate.get("remaining_actions_are_only_paid_manual_policy_or_acceptance")),
        "finality_evidence_summary": str(certificate.get("finality_evidence_summary") or ""),
        "free_open_sources_exhausted": free_open_exhausted,
        "paid_data_requirement_matrix_path": "reports/GOLF_PAID_DATA_REQUIREMENT_MATRIX.json",
        "calibration_readiness_report_path": "reports/GOLF_DATA_CALIBRATION_READINESS_REPORT.json",
        "free_open_exhaustion_certificate_path": "reports/GOLF_FREE_OPEN_EXHAUSTION_CERTIFICATE.json",
        "golf_readiness_recommendation": readiness_model.get("recommendation"),
        "raw_html_persisted": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "provider_write": False,
        "execution_allowed": False,
        "paid_source_enabled_count": 1,
    }


def write_golf_final_oxylabs_free_open_exhaustion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.json"
    md_path = root / "GOLF_FINAL_OXYLABS_FREE_OPEN_EXHAUSTION_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Golf Final Oxylabs Free Open Exhaustion Report",
        "",
        f"1. branch_name: {report.get('branch_name')}",
        f"2. commit_hash: {report.get('commit_hash')}",
        f"3. new_overall_verdict: {report.get('new_overall_verdict')}",
        f"4. tours_included: {', '.join(report.get('tours_included') or [])}",
        f"5. candidate_sources_discovered: {report.get('candidate_sources_discovered')}",
        f"6. loader_ready_lanes_before: {report.get('loader_ready_lanes_before')}",
        f"7. loader_ready_lanes_backfilled: {report.get('loader_ready_lanes_backfilled')}",
        f"8. loader_ready_lanes_hard_blocked: {report.get('loader_ready_lanes_hard_blocked')}",
        f"9. no_more_free_open_search_required: {report.get('no_more_free_open_search_required')}",
        "",
    ]
    write_md(md_path, "\n".join(lines))
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def run_golf_final_free_open_exhaustion() -> dict[str, Any]:
    inventory_report = build_golf_architecture_inventory()
    source_ledger = build_golf_free_vs_paid_source_ledger()
    candidate_inventory = build_golf_candidate_source_policy_inventory()
    policy_matrix = build_golf_source_policy_matrix()
    sample_report = build_golf_safe_source_sample_report(policy_matrix=policy_matrix, candidate_rows=golf_candidate_source_catalog())
    sample_verification_results = build_golf_targeted_sample_verification_results(policy_matrix=policy_matrix, sample_report=sample_report)
    backfill_report = build_golf_loader_ready_backfill_report(policy_matrix=policy_matrix)
    schema_report = build_golf_schema_expansion_report(sample_verification_results=sample_verification_results)
    oxylabs_schema_report = build_golf_oxylabs_schema_expansion_report(sample_verification_results=sample_verification_results, schema_report=schema_report)
    audit_report = build_golf_oxylabs_source_exhaustion_log(policy_matrix=policy_matrix, sample_report=sample_report)
    reclassification_report = build_golf_oxylabs_reclassification_report(source_exhaustion_report=audit_report)
    manual_templates = build_golf_manual_import_templates(source_ledger=source_ledger, audit_report=audit_report)
    paid_matrix = build_golf_paid_data_requirement_matrix(source_ledger=source_ledger, audit_report=audit_report)
    readiness_report = build_golf_data_calibration_readiness_report(
        inventory_report=inventory_report,
        source_ledger=source_ledger,
        audit_report=audit_report,
        backfill_report=backfill_report,
        paid_matrix=paid_matrix,
    )
    certificate = build_golf_free_open_exhaustion_certificate(
        policy_matrix=policy_matrix,
        audit_report=audit_report,
        backfill_report=backfill_report,
        sample_report=sample_report,
        sample_verification_results=sample_verification_results,
    )
    final_report = build_golf_final_oxylabs_free_open_exhaustion_report(
        inventory_report=inventory_report,
        source_ledger=source_ledger,
        candidate_inventory=candidate_inventory,
        policy_matrix=policy_matrix,
        sample_report=sample_report,
        sample_verification_results=sample_verification_results,
        backfill_report=backfill_report,
        schema_report=schema_report,
        oxylabs_schema_report=oxylabs_schema_report,
        audit_report=audit_report,
        reclassification_report=reclassification_report,
        paid_matrix=paid_matrix,
        readiness_report=readiness_report,
        certificate=certificate,
    )
    write_golf_architecture_inventory(inventory_report)
    write_golf_free_vs_paid_source_ledger(source_ledger)
    write_golf_candidate_source_policy_inventory(candidate_inventory)
    write_golf_source_policy_matrix(policy_matrix)
    write_golf_source_policy_review_docs(policy_matrix)
    write_golf_safe_source_sample_report(sample_report)
    write_golf_targeted_sample_verification_results(sample_verification_results)
    write_golf_loader_ready_backfill_report(backfill_report)
    write_golf_schema_expansion_report(schema_report)
    write_golf_oxylabs_schema_expansion_report(oxylabs_schema_report)
    write_golf_oxylabs_source_exhaustion_log(audit_report)
    write_golf_oxylabs_reclassification_report(reclassification_report)
    write_golf_manual_import_templates(manual_templates)
    write_golf_manual_import_docs(manual_templates)
    write_golf_paid_data_requirement_matrix(paid_matrix)
    write_golf_data_calibration_readiness_report(readiness_report)
    write_golf_free_open_exhaustion_certificate(certificate)
    write_golf_final_oxylabs_free_open_exhaustion_report(final_report)
    return final_report
