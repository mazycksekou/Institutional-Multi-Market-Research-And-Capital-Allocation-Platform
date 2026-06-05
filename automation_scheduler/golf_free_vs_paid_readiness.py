from __future__ import annotations

from pathlib import Path
from typing import Any

from .golf_oxylabs_common import RUN_MODE, TOURS_INCLUDED, current_utc, lane_source_spec, url_hash, write_json, write_md


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"

FREE_VS_PAID_CATEGORIES = (
    "free_open_populated",
    "free_open_partial",
    "free_open_sample_required",
    "free_open_loader_needed",
    "free_open_manual_import_needed",
    "user_approved_paid_transport_needed",
    "paid_data_subscription_required",
    "policy_blocked",
    "robots_blocked",
    "terms_blocked",
    "login_paywall_captcha_blocked",
    "license_terms_unclear",
    "unavailable_after_max_effort",
    "obsolete_or_duplicate",
    "needs_manual_review",
)

SAFETY_FLAGS: dict[str, Any] = {
    "provider_write": False,
    "execution_allowed": False,
    "execution_allowed_count": 0,
    "live_execution_enabled": False,
    "auto_execution_enabled": False,
    "kalshi_order_execution_enabled": False,
    "sportsbook_bet_execution_enabled": False,
    "broker_order_execution_enabled": False,
    "stock_trade_execution_enabled": False,
    "crypto_trade_execution_enabled": False,
    "actual_orders_submitted": 0,
    "actual_bets_submitted": 0,
    "actual_trades_submitted": 0,
    "actual_crypto_swaps_submitted": 0,
    "raw_payload_included": False,
    "raw_html_persisted": False,
    "raw_screenshot_persisted": False,
    "secrets_included": False,
    "paid_source_enabled_count": 1,
    "AllowOxylabs": True,
    "AllowPaidRetrieval": True,
    "AllowActiveDiscovery": True,
    "AllowSearchDiscovery": True,
    "AllowSourcePolicyReview": True,
    "AllowRobotsReview": True,
    "AllowTermsReview": True,
    "AllowLicenseReview": True,
    "AllowApiDocsReview": True,
    "AllowDataDictionaryReview": True,
    "AllowSchemaExpansion": True,
    "AllowSampleVerification": True,
    "AllowOneTournamentValidation": True,
    "AllowOnePlayerValidation": True,
    "AllowOneCourseValidation": True,
    "AllowFreeVsPaidAudit": True,
    "AllowCalibrationReadinessAudit": True,
    "AllowBackfill": True,
    "AllowFinalityAudit": True,
}

SPORTS = {
    "golf": {
        "display_name": "Golf",
        "module": "golf",
        "model": "strokes_gained_course_fit_monte_carlo_model",
        "readiness_recommendation": "manual_import_needed",
    }
}


def _safety() -> dict[str, Any]:
    return dict(SAFETY_FLAGS)


def _lane(
    lane_name: str,
    field_group: str,
    *,
    tour: str,
    tournament_or_scope: str,
    entity_level: str,
    fields: list[str],
    table: str,
    source_id: str,
    source_family: str,
    category: str,
    current_status: str,
    calibration_impact: str,
    next_action: str,
    final_reason: str,
    data_type: str = "mixed",
    cutoff_safe: bool = True,
    future_leakage_risk: str = "low_if_joined_by_tournament_start",
    model_eligible: bool | None = None,
    coverage_start: str = "historical_public_sample_scope",
    coverage_end: str = "historical_public_sample_scope",
    loader_exists: bool = True,
    manual_template_required: bool = False,
    paid_priority: str | None = None,
) -> dict[str, Any]:
    if category not in FREE_VS_PAID_CATEGORIES:
        raise ValueError(f"Unsupported Golf category: {category}")
    source = lane_source_spec({"source_id": source_id})
    return {
        "sport": "golf",
        "sport_name": "Golf",
        "tour": tour,
        "tournament_or_scope": tournament_or_scope,
        "module": "golf",
        "table": table,
        "lane_name": lane_name,
        "field_or_feature_group": field_group,
        "fields": list(fields),
        "entity_level": entity_level,
        "data_type": data_type,
        "current_status": current_status,
        "source_id": source_id,
        "source_family": source_family,
        "candidate_source_name": source.source_name,
        "source_type": source.source_type,
        "source_url_hash": url_hash(source.url),
        "source_domain": source.domain,
        "free_or_paid_category": category,
        "retrieval_method": source.transport,
        "sample_required": category in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"},
        "loader_exists": bool(loader_exists),
        "manual_template_exists": bool(manual_template_required or category in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear"}),
        "manual_template_required": bool(manual_template_required),
        "policy_status": source.policy_status,
        "license_or_terms_note": source.license_or_terms_note,
        "cutoff_safe": bool(cutoff_safe),
        "future_leakage_risk": future_leakage_risk,
        "model_eligible": bool(category in {"free_open_populated", "free_open_partial", "free_open_loader_needed"} and cutoff_safe) if model_eligible is None else bool(model_eligible),
        "calibration_impact": calibration_impact,
        "next_action": next_action,
        "final_reason": final_reason,
        "duplicate_or_obsolete_candidate": False,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "manual_import_possible": True,
        "paid_priority": paid_priority,
    }


def golf_lane_catalog() -> list[dict[str, Any]]:
    return [
        _lane("course_identity_metadata", "course identity and location", tour="Majors", tournament_or_scope="course", entity_level="course", fields=["course_id", "course_name", "city", "region", "country"], table="golf_courses", source_id="golf_open_course_data", source_family="open_course_dataset", category="free_open_loader_needed", current_status="open_course_loader_needed", calibration_impact="anchors course-fit joins and tournament course identity", next_action="backfill_approved_scope", final_reason="OpenGolfAPI/Open Course data provides policy-approved normalized course metadata."),
        _lane("course_par_yardage", "course par and yardage", tour="Majors", tournament_or_scope="course", entity_level="course", fields=["course_id", "par", "yardage"], table="golf_course_specs", source_id="golf_open_course_data", source_family="open_course_dataset", category="free_open_loader_needed", current_status="open_course_loader_needed", calibration_impact="supports course difficulty and scoring baseline features", next_action="backfill_approved_scope", final_reason="Open course schema supports normalized par and yardage facts."),
        _lane("course_scorecard_context", "hole-level course scorecard", tour="Majors", tournament_or_scope="course", entity_level="hole", fields=["course_id", "hole", "hole_par", "hole_yardage", "nine"], table="golf_course_scorecards", source_id="golf_open_course_data", source_family="open_course_dataset", category="free_open_loader_needed", current_status="open_course_loader_needed", calibration_impact="supports course-fit, round-score, and player prop context", next_action="backfill_approved_scope", final_reason="Open course schema supports hole-level scorecard backfill."),
        _lane("golfer_metadata_entities", "golfer structured metadata", tour="PGA Tour/DPWT/LPGA", tournament_or_scope="player", entity_level="player", fields=["player_name", "country", "birth_date", "wikidata_id"], table="golf_player_metadata", source_id="golf_wikidata_player_entities", source_family="structured_open_metadata", category="free_open_partial", current_status="metadata_only_candidate", calibration_impact="supplemental player identity and country joins", next_action="sample_verify_one_player", final_reason="Wikidata remains metadata-only for golfer identity enrichment.", loader_exists=False, model_eligible=False),
        _lane("major_tournament_metadata", "major tournament metadata", tour="Majors", tournament_or_scope="major_championships", entity_level="tournament", fields=["tournament_name", "major_name", "founded", "host_course_note"], table="golf_major_metadata", source_id="golf_wikipedia_tournament_tables", source_family="structured_open_metadata", category="free_open_partial", current_status="metadata_only_candidate", calibration_impact="supplemental major identity context", next_action="sample_verify_one_tournament", final_reason="Wikipedia remains metadata-only supplemental context.", loader_exists=False, model_eligible=False),
        _lane("pga_tournament_results", "PGA tournament leaderboard and results", tour="PGA Tour", tournament_or_scope="tournament", entity_level="player_tournament", fields=["event_id", "player_name", "round_scores", "total_score", "finish_position", "cut_status"], table="golf_pga_results", source_id="golf_pga_tour_official_pages", source_family="official_tour_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="critical for winner, placement, matchup, and cut-risk calibration", next_action="create_manual_import_template", final_reason="PGA Tour pages remain manual-only unless exact automated terms approve extraction.", loader_exists=False, manual_template_required=True),
        _lane("dpwt_tournament_results", "DP World Tour tournament results", tour="DP World Tour", tournament_or_scope="tournament", entity_level="player_tournament", fields=["event_id", "player_name", "round_scores", "total_score", "finish_position"], table="golf_dpwt_results", source_id="golf_dp_world_tour_official_pages", source_family="official_tour_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="supports DPWT scope and field-strength transfer", next_action="create_manual_import_template", final_reason="DP World Tour pages remain manual-only in this pass.", loader_exists=False, manual_template_required=True),
        _lane("lpga_tournament_results", "LPGA tournament results", tour="LPGA", tournament_or_scope="tournament", entity_level="player_tournament", fields=["event_id", "player_name", "round_scores", "total_score", "finish_position"], table="golf_lpga_results", source_id="golf_lpga_official_pages", source_family="official_tour_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="supports LPGA only where repo scope accepts payload fields", next_action="create_manual_import_template", final_reason="LPGA public pages remain manual-only in this pass.", loader_exists=False, manual_template_required=True),
        _lane("major_field_tee_times", "major fields and tee times", tour="Majors", tournament_or_scope="major_championships", entity_level="player_round", fields=["field_player_name", "tee_time", "wave", "starting_hole", "observed_at"], table="golf_major_fields_tee_times", source_id="golf_major_championship_pages", source_family="official_major_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="tee-time wave and field context affect weather draw and matchup markets", next_action="create_manual_import_template", final_reason="Major tee times and fields remain manual-only with timestamp review.", loader_exists=False, manual_template_required=True),
        _lane("owgr_ranking_context", "world ranking context", tour="PGA Tour/DPWT/LPGA", tournament_or_scope="rankings", entity_level="player_week", fields=["world_rank", "ranking_date", "ranking_points", "ranking_source"], table="golf_world_rankings", source_id="golf_owgr_rankings", source_family="ranking_pages", category="policy_blocked", current_status="blocked_by_policy", calibration_impact="world ranking improves field strength and matchup priors", next_action="mark_policy_blocked", final_reason="OWGR automated extraction was reviewed but not approved.", loader_exists=False),
        _lane("strokes_gained_categories", "strokes-gained skill categories", tour="PGA Tour", tournament_or_scope="player_stat", entity_level="player_season", fields=["sg_total", "sg_off_tee", "sg_approach", "sg_around_green", "sg_putting"], table="golf_strokes_gained", source_id="golf_pgatour_shotlink", source_family="licensed_shotlink_stats", category="paid_data_subscription_required", current_status="paid_vendor_required", calibration_impact="core strokes-gained and player prop readiness", next_action="mark_paid_subscription_required", final_reason="ShotLink/strokes-gained production data remains paid/licensed after free/open search.", loader_exists=False, manual_template_required=True, paid_priority="high"),
        _lane("datagolf_model_context", "Data Golf model and skill context", tour="PGA Tour/DPWT/LIV", tournament_or_scope="analytics", entity_level="player_event", fields=["datagolf_skill_estimate", "course_fit_estimate", "field_strength_estimate"], table="golf_datagolf_context", source_id="golf_datagolf_public_pages", source_family="analytics_pages", category="license_terms_unclear", current_status="visible_but_terms_unclear", calibration_impact="would improve course-fit and field-strength estimates", next_action="mark_license_terms_unclear", final_reason="Data Golf requires exact licensed/API terms before automated use.", loader_exists=False, manual_template_required=True),
        _lane("community_golf_wrapper_context", "community golf API wrapper context", tour="PGA Tour", tournament_or_scope="wrapper", entity_level="reference", fields=["wrapper_name", "upstream_source", "license_note", "api_surface_note"], table="golf_reference_wrappers", source_id="golf_golfastr_repo", source_family="community_wrapper_repo", category="license_terms_unclear", current_status="visible_but_upstream_rights_unclear", calibration_impact="community wrappers show technical availability but upstream rights remain unclear", next_action="mark_license_terms_unclear", final_reason="golfastr is public, but upstream ESPN/PGA rights remain unclear.", loader_exists=False, manual_template_required=True, model_eligible=False),
        _lane("pgatour_api_wrapper_context", "community PGA Tour API wrapper context", tour="PGA Tour", tournament_or_scope="wrapper", entity_level="reference", fields=["wrapper_name", "upstream_source", "license_note", "stat_surface_note"], table="golf_reference_wrappers", source_id="golf_pgatour_api_wrapper_repo", source_family="community_wrapper_repo", category="license_terms_unclear", current_status="visible_but_upstream_rights_unclear", calibration_impact="technical path visible but upstream PGA API rights remain unclear", next_action="mark_license_terms_unclear", final_reason="pgatouR/related wrappers require legal review before automated use.", loader_exists=False, manual_template_required=True, model_eligible=False),
        _lane("espn_golf_results_context", "ESPN golf result pages", tour="PGA Tour", tournament_or_scope="reference", entity_level="player_tournament", fields=["leaderboard_reference", "round_score_reference", "result_reference"], table="golf_reference_results", source_id="golf_espn_golf_pages", source_family="reference_site", category="policy_blocked", current_status="blocked_by_policy", calibration_impact="would provide historical leaderboard context but automation is blocked", next_action="mark_policy_blocked", final_reason="ESPN Golf pages were reviewed but not approved for automated extraction.", loader_exists=False),
        _lane("kaggle_golf_catalog_context", "Kaggle golf dataset catalog", tour="PGA Tour", tournament_or_scope="dataset_catalog", entity_level="reference", fields=["dataset_name", "license_note", "catalog_url_hash"], table="golf_dataset_catalog", source_id="golf_kaggle_catalog", source_family="dataset_catalog", category="login_paywall_captcha_blocked", current_status="account_gated_catalog", calibration_impact="catalog may identify datasets but cannot be automated here", next_action="mark_login_paywall_captcha_blocked", final_reason="Kaggle catalog remains account-gated and not used for automated backfill.", loader_exists=False, model_eligible=False),
        _lane("weather_wind_course_context", "weather and wind course context", tour="PGA Tour/Majors", tournament_or_scope="weather", entity_level="course_date", fields=["weather_date", "wind_speed", "wind_gust", "precipitation", "weather_source"], table="golf_weather_context", source_id="golf_paid_tracking_vendor", source_family="paid_vendor_page", category="paid_data_subscription_required", current_status="paid_or_manual_required", calibration_impact="weather and wind are important to wave and scoring adjustments", next_action="mark_paid_subscription_required", final_reason="Production-grade timestamped weather/course feeds remain paid or manual after free/open search.", loader_exists=False, manual_template_required=True, paid_priority="medium"),
    ]


def _new_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    return {
        "course_identity_metadata": ["course_slug", "country_code_normalized"],
        "course_par_yardage": ["course_length_bucket", "par_adjusted_yardage"],
        "course_scorecard_context": ["par5_count", "long_par4_count", "scoring_hole_flag"],
        "golfer_metadata_entities": ["player_name_slug", "country_code_normalized"],
        "major_tournament_metadata": ["major_slug", "course_host_slug"],
    }.get(lane["lane_name"], []) if lane["free_or_paid_category"] in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"} else []


def default_golf_loader_lanes() -> list[dict[str, Any]]:
    return [lane for lane in golf_lane_catalog() if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"}]


def _lane_sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    return dict((sample_verification_results or {}).get("source_result_index") or {})


def build_golf_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries = []
    for lane in golf_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        records = int(sample.get("records_tested", 0) or 0)
        status = sample.get("validation_status")
        if status == "sample_verified" and records:
            population = "partial"
        elif lane["free_or_paid_category"] in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear", "policy_blocked", "login_paywall_captcha_blocked"}:
            population = "blocked"
        else:
            population = "manual_or_review_required"
        for field in lane["fields"]:
            entries.append({
                "sport": lane["sport"], "tour": lane["tour"], "tournament": lane["tournament_or_scope"], "module": lane["module"],
                "table": lane["table"], "schema": lane["table"], "field_name": field, "entity_level": lane["entity_level"],
                "current_population_status": population, "current_record_count": records, "current_source": lane["candidate_source_name"],
                "source_family": lane["source_family"], "data_type": lane["data_type"], "coverage_start": lane["coverage_start"],
                "coverage_end": lane["coverage_end"], "cutoff_safe": lane["cutoff_safe"], "future_leakage_risk": lane["future_leakage_risk"],
                "model_eligible": lane["model_eligible"], "calibration_impact": lane["calibration_impact"],
                "missing_reason": "" if population == "partial" else lane["final_reason"], "candidate_sources_to_fill": [lane["candidate_source_name"]],
                "duplicate_or_obsolete_candidate": lane["duplicate_or_obsolete_candidate"], "lane_name": lane["lane_name"],
                "free_or_paid_category": lane["free_or_paid_category"],
            })
    return {"ok": True, "status": "ok", "report_name": "GOLF_ARCHITECTURE_INVENTORY", "schema_version": "golf_architecture_inventory_v1", "created_at": current_utc(), "sport": "golf", "tours_included": list(TOURS_INCLUDED), "inventory_entries": entries, "field_inventory_entries": entries, "fields_total": len(entries), "fields_populated_count": 0, "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"), "fields_missing_count": sum(1 for row in entries if row["current_population_status"] != "partial"), **_safety()}


def write_golf_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_ARCHITECTURE_INVENTORY.json"
    md_path = root / "GOLF_ARCHITECTURE_INVENTORY.md"
    write_json(json_path, report)
    lines = ["# Golf Architecture Inventory", "", f"1. fields_total: {report.get('fields_total')}", f"2. fields_partial_count: {report.get('fields_partial_count')}", f"3. fields_missing_count: {report.get('fields_missing_count')}", "", "## Lanes"]
    for lane in golf_lane_catalog():
        lines.append(f"- {lane['lane_name']} source={lane['candidate_source_name']} category={lane['free_or_paid_category']}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_golf_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows = []
    for lane in golf_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        rows.append({**lane, "sample_attempted": bool(sample), "sample_validation_status": sample.get("validation_status"), "sample_records_found": int(sample.get("records_tested", 0) or 0)})
    return {"ok": True, "status": "ok", "report_name": "GOLF_FREE_VS_PAID_SOURCE_LEDGER", "schema_version": "golf_free_vs_paid_source_ledger_v1", "created_at": current_utc(), "sport": "golf", "tours_included": list(TOURS_INCLUDED), "source_ledger_rows": rows, "source_ledger_row_count": len(rows), "free_open_loader_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_loader_needed"), "free_open_sample_required_count": 0, "free_open_manual_import_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_manual_import_needed"), "paid_data_subscription_required_count": sum(1 for row in rows if row["free_or_paid_category"] == "paid_data_subscription_required"), "license_terms_unclear_count": sum(1 for row in rows if row["free_or_paid_category"] == "license_terms_unclear"), **_safety()}


def write_golf_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "GOLF_FREE_VS_PAID_SOURCE_LEDGER.json"
    md_path = root / "GOLF_FREE_VS_PAID_SOURCE_LEDGER.md"
    write_json(json_path, report)
    lines = ["# Golf Free vs Paid Source Ledger", "", f"1. source_ledger_row_count: {report.get('source_ledger_row_count')}", f"2. free_open_loader_needed_count: {report.get('free_open_loader_needed_count')}", f"3. free_open_manual_import_needed_count: {report.get('free_open_manual_import_needed_count')}", f"4. paid_data_subscription_required_count: {report.get('paid_data_subscription_required_count')}", "", "## Lanes"]
    for row in report.get("source_ledger_rows") or []:
        lines.append(f"- {row.get('lane_name')} category={row.get('free_or_paid_category')} source={row.get('candidate_source_name')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
