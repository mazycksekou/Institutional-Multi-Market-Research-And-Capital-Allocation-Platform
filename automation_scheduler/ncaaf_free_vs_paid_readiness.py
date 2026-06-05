from __future__ import annotations

from pathlib import Path
from typing import Any

from .ncaaf_oxylabs_common import RUN_MODE, SUBDIVISIONS_INCLUDED, current_utc, lane_source_spec, url_hash, write_json, write_md


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
    "AllowOneSeasonValidation": True,
    "AllowOneTeamValidation": True,
    "AllowOneGameValidation": True,
    "AllowOneDriveValidation": True,
    "AllowFreeVsPaidAudit": True,
    "AllowCalibrationReadinessAudit": True,
    "AllowBackfill": True,
    "AllowFinalityAudit": True,
}

SPORTS = {
    "americanfootball_ncaaf": {
        "display_name": "NCAAF",
        "module": "americanfootball_ncaaf",
        "model": "college_football_epa_drive_rating_monte_carlo_model",
        "readiness_recommendation": "manual_import_needed",
    }
}


def _safety() -> dict[str, Any]:
    return dict(SAFETY_FLAGS)


def _lane(
    lane_name: str,
    field_group: str,
    *,
    subdivision: str,
    conference: str,
    team: str,
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
    future_leakage_risk: str = "low_if_joined_by_game_start_or_postgame_training_only",
    model_eligible: bool | None = None,
    coverage_start: str = "historical_public_sample_scope",
    coverage_end: str = "historical_public_sample_scope",
    loader_exists: bool = True,
    manual_template_required: bool = False,
    paid_priority: str | None = None,
) -> dict[str, Any]:
    if category not in FREE_VS_PAID_CATEGORIES:
        raise ValueError(f"Unsupported NCAAF category: {category}")
    source = lane_source_spec({"source_id": source_id})
    return {
        "sport": "americanfootball_ncaaf",
        "sport_name": "NCAAF",
        "subdivision": subdivision,
        "conference": conference,
        "team": team,
        "module": "americanfootball_ncaaf",
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


def ncaaf_lane_catalog() -> list[dict[str, Any]]:
    return [
        _lane("team_identity_crosswalk", "team identity and conference crosswalk", subdivision="FBS", conference="all", team="all", entity_level="team", fields=["team_id", "team_name", "subdivision", "conference", "mascot"], table="ncaaf_teams", source_id="ncaaf_cfbd_api_docs", source_family="cfbd_api_docs", category="free_open_loader_needed", current_status="cfbd_loader_needed", calibration_impact="anchors team joins for every NCAAF market", next_action="backfill_approved_scope", final_reason="CFBD-style normalized public sample supports team identity/crosswalk backfill."),
        _lane("schedule_game_results", "schedule and final results", subdivision="FBS", conference="all", team="all", entity_level="game", fields=["game_id", "season", "week", "season_type", "home_team", "away_team", "home_points", "away_points", "final_margin", "total_points"], table="ncaaf_games", source_id="ncaaf_cfbd_api_docs", source_family="cfbd_api_docs", category="free_open_loader_needed", current_status="cfbd_loader_needed", calibration_impact="supports moneyline, spread, total, and outcome calibration", next_action="backfill_approved_scope", final_reason="CFBD-style normalized public sample supports game result backfill."),
        _lane("drive_summary_epa", "drive-level EPA and efficiency", subdivision="FBS", conference="all", team="all", entity_level="drive", fields=["drive_id", "offense", "defense", "drive_number", "plays", "yards", "drive_result", "drive_points", "drive_epa"], table="ncaaf_drives", source_id="ncaaf_cfbd_api_docs", source_family="cfbd_api_docs", category="free_open_loader_needed", current_status="cfbd_loader_needed", calibration_impact="core drive/EPA rating model input", next_action="backfill_approved_scope", final_reason="CFBD-style normalized public sample supports one-drive validation and backfill."),
        _lane("play_by_play_epa", "play-by-play EPA candidates", subdivision="FBS", conference="all", team="all", entity_level="play", fields=["play_id", "down", "distance", "yard_line", "play_type", "yards_gained", "epa", "success", "explosive"], table="ncaaf_plays", source_id="ncaaf_cfbd_api_docs", source_family="cfbd_api_docs", category="free_open_loader_needed", current_status="cfbd_loader_needed", calibration_impact="supports EPA, success rate, explosiveness, and total-market model features", next_action="backfill_approved_scope", final_reason="CFBD-style normalized public sample supports one-play validation and backfill."),
        _lane("venue_stadium_metadata", "venue and stadium context", subdivision="FBS", conference="all", team="all", entity_level="venue", fields=["venue_id", "venue_name", "city", "state", "capacity", "surface", "indoor"], table="ncaaf_venues", source_id="ncaaf_cfbd_api_docs", source_family="cfbd_api_docs", category="free_open_loader_needed", current_status="cfbd_loader_needed", calibration_impact="supports venue/weather/neutral-site joins", next_action="backfill_approved_scope", final_reason="CFBD-style normalized public sample supports venue backfill."),
        _lane("team_metadata_entities", "team structured metadata", subdivision="FBS/FCS", conference="all", team="all", entity_level="team", fields=["team_name", "wikidata_id", "conference", "subdivision"], table="ncaaf_team_metadata", source_id="ncaaf_wikidata_team_entities", source_family="structured_open_metadata", category="free_open_partial", current_status="metadata_only_candidate", calibration_impact="supplemental team identity and conference joins", next_action="sample_verify_one_team", final_reason="Wikidata remains metadata-only for college football team identity enrichment.", loader_exists=False, model_eligible=False),
        _lane("postseason_metadata", "bowl CFP and conference championship metadata", subdivision="FBS", conference="postseason", team="all", entity_level="game", fields=["postseason_game_name", "bowl_name", "cfp_round", "neutral_site", "championship_game_flag"], table="ncaaf_postseason_metadata", source_id="ncaaf_wikipedia_bowl_tables", source_family="structured_open_metadata", category="free_open_partial", current_status="metadata_only_candidate", calibration_impact="supplemental bowl/CFP/conference championship context", next_action="sample_verify_one_postseason_entity", final_reason="Wikipedia bowl/CFP tables remain supplemental metadata only.", loader_exists=False, model_eligible=False),
        _lane("official_ncaa_stats_pages", "NCAA official stats and standings", subdivision="FBS", conference="all", team="all", entity_level="team_game", fields=["official_stat_reference", "ranking_reference", "standings_reference"], table="ncaaf_official_references", source_id="ncaaf_ncaa_official_pages", source_family="official_ncaa_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="can validate official standings/stats but automation is not approved", next_action="create_manual_import_template", final_reason="NCAA public pages remain manual-only unless exact terms approve automated extraction.", loader_exists=False, manual_template_required=True),
        _lane("conference_official_context", "conference official schedules and championships", subdivision="FBS", conference="all", team="all", entity_level="conference_game", fields=["conference", "conference_game", "championship_game_flag", "conference_standings_reference"], table="ncaaf_conference_context", source_id="ncaaf_conference_official_pages", source_family="official_conference_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="conference championship and schedule context affects priors", next_action="create_manual_import_template", final_reason="Official conference pages remain manual-only in this pass.", loader_exists=False, manual_template_required=True),
        _lane("school_roster_depth_chart", "school roster and depth chart context", subdivision="FBS/FCS", conference="all", team="single_team", entity_level="player_team", fields=["player_name", "position", "class_year", "depth_chart_role", "availability_note"], table="ncaaf_rosters_depth_charts", source_id="ncaaf_school_official_pages", source_family="official_school_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="roster/depth-chart status affects team strength and props", next_action="create_manual_import_template", final_reason="School roster/depth-chart pages remain manual-only unless exact site policy approves automation.", loader_exists=False, manual_template_required=True),
        _lane("bowl_cfp_official_context", "official bowl and CFP context", subdivision="FBS", conference="postseason", team="all", entity_level="game", fields=["bowl_name", "cfp_round", "neutral_site", "travel_distance_proxy", "rest_days"], table="ncaaf_bowl_cfp_context", source_id="ncaaf_bowl_cfp_official_pages", source_family="official_postseason_pages", category="free_open_manual_import_needed", current_status="manual_timestamped_capture_needed", calibration_impact="bowl, CFP, neutral-site, travel, and rest context affects spread/totals", next_action="create_manual_import_template", final_reason="Bowl/CFP pages remain manual-only for timestamped validation.", loader_exists=False, manual_template_required=True),
        _lane("espn_scoreboard_context", "ESPN college football scoreboards", subdivision="FBS", conference="all", team="all", entity_level="game", fields=["scoreboard_reference", "box_score_reference", "team_stat_reference"], table="ncaaf_reference_results", source_id="ncaaf_espn_pages", source_family="reference_site", category="policy_blocked", current_status="blocked_by_policy", calibration_impact="could validate box scores but automation is blocked", next_action="mark_policy_blocked", final_reason="ESPN extraction is not approved in this pass.", loader_exists=False),
        _lane("sports_reference_context", "Sports Reference college football pages", subdivision="FBS", conference="all", team="all", entity_level="game", fields=["historical_result_reference", "advanced_stat_reference"], table="ncaaf_reference_results", source_id="ncaaf_sports_reference_pages", source_family="reference_site", category="policy_blocked", current_status="blocked_by_policy", calibration_impact="would add historical context but scraping is prohibited", next_action="mark_policy_blocked", final_reason="Sports Reference / College Football Reference scraping is explicitly prohibited.", loader_exists=False),
        _lane("cfbfastr_sportsdataverse_context", "cfbfastR and SportsDataverse upstream context", subdivision="FBS", conference="all", team="all", entity_level="reference", fields=["package_name", "upstream_source", "license_note", "api_surface_note"], table="ncaaf_reference_wrappers", source_id="ncaaf_cfbfastr_repo", source_family="community_wrapper_repo", category="license_terms_unclear", current_status="visible_but_terms_unclear", calibration_impact="technical paths exist but license/upstream reuse must be reviewed", next_action="mark_license_terms_unclear", final_reason="cfbfastR/SportsDataverse requires exact license and upstream-source legal review before automated broad reuse.", loader_exists=False, manual_template_required=True, model_eligible=False),
        _lane("public_weather_stadium_context", "weather wind and stadium game context", subdivision="FBS", conference="all", team="all", entity_level="game_weather", fields=["weather_date", "temperature", "wind_speed", "wind_gust", "precipitation", "weather_source"], table="ncaaf_weather_context", source_id="ncaaf_weather_archive", source_family="dataset_search", category="unavailable_after_max_effort", current_status="not_found_policy_approved", calibration_impact="weather and wind matter for totals and tempo", next_action="mark_unavailable_after_exhaustive_search", final_reason="No policy-approved normalized free/open NCAAF weather archive was accepted in this pass.", loader_exists=False, manual_template_required=True),
        _lane("injury_availability_depth_chart_feed", "injury availability and depth chart feed", subdivision="FBS", conference="all", team="all", entity_level="player_week", fields=["player_name", "injury_status", "availability_status", "depth_chart_position"], table="ncaaf_injury_availability", source_id="ncaaf_paid_vendor", source_family="paid_vendor_page", category="paid_data_subscription_required", current_status="paid_vendor_required", calibration_impact="critical for team strength, props, and risk gating", next_action="mark_paid_subscription_required", final_reason="Production injury/depth-chart feeds remain paid/licensed after free/open search.", loader_exists=False, manual_template_required=True, paid_priority="high"),
        _lane("advanced_team_player_stats_feed", "advanced team player and special teams stats", subdivision="FBS", conference="all", team="all", entity_level="team_player_season", fields=["offensive_efficiency", "defensive_efficiency", "special_teams_rating", "turnover_rate", "penalty_rate", "red_zone_rate", "third_down_rate", "fourth_down_rate", "pace_plays_per_game"], table="ncaaf_advanced_stats", source_id="ncaaf_paid_vendor", source_family="paid_vendor_page", category="paid_data_subscription_required", current_status="paid_vendor_required", calibration_impact="materially improves EPA drive-rating and spread/total calibration", next_action="mark_paid_subscription_required", final_reason="Production advanced NCAAF stat feeds remain paid/licensed.", loader_exists=False, manual_template_required=True, paid_priority="high"),
        _lane("kaggle_dataset_catalog_context", "Kaggle NCAAF dataset catalog", subdivision="FBS", conference="all", team="all", entity_level="reference", fields=["dataset_name", "license_note", "catalog_url_hash"], table="ncaaf_dataset_catalog", source_id="ncaaf_kaggle_catalog", source_family="dataset_catalog", category="login_paywall_captcha_blocked", current_status="account_gated_catalog", calibration_impact="catalog may identify datasets but cannot be automated here", next_action="mark_login_paywall_captcha_blocked", final_reason="Kaggle catalog remains account-gated and not used for automated backfill.", loader_exists=False, model_eligible=False),
    ]


def _new_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    return {
        "team_identity_crosswalk": ["team_slug", "conference_slug"],
        "schedule_game_results": ["final_margin_bucket", "total_points_bucket", "postgame_training_join_key"],
        "drive_summary_epa": ["drive_success_rate_proxy", "drive_points_per_opportunity"],
        "play_by_play_epa": ["play_success_flag", "explosive_play_flag", "epa_bucket"],
        "venue_stadium_metadata": ["venue_slug", "altitude_bucket"],
        "team_metadata_entities": ["team_wikidata_slug"],
        "postseason_metadata": ["postseason_context_slug"],
    }.get(lane["lane_name"], []) if lane["free_or_paid_category"] in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"} else []


def default_ncaaf_loader_lanes() -> list[dict[str, Any]]:
    return [lane for lane in ncaaf_lane_catalog() if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"}]


def _lane_sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    return dict((sample_verification_results or {}).get("source_result_index") or {})


def build_ncaaf_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries = []
    for lane in ncaaf_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        records = int(sample.get("records_tested", 0) or 0)
        status = sample.get("validation_status")
        if status == "sample_verified" and records:
            population = "partial"
        elif lane["free_or_paid_category"] in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear", "policy_blocked", "login_paywall_captcha_blocked", "unavailable_after_max_effort"}:
            population = "blocked"
        else:
            population = "manual_or_review_required"
        for field in lane["fields"]:
            entries.append({
                "sport": lane["sport"], "subdivision": lane["subdivision"], "conference": lane["conference"], "team": lane["team"],
                "module": lane["module"], "table": lane["table"], "schema": lane["table"], "field_name": field,
                "entity_level": lane["entity_level"], "current_population_status": population, "current_record_count": records,
                "current_source": lane["candidate_source_name"], "source_family": lane["source_family"], "data_type": lane["data_type"],
                "coverage_start": lane["coverage_start"], "coverage_end": lane["coverage_end"], "cutoff_safe": lane["cutoff_safe"],
                "future_leakage_risk": lane["future_leakage_risk"], "model_eligible": lane["model_eligible"],
                "calibration_impact": lane["calibration_impact"], "missing_reason": "" if population == "partial" else lane["final_reason"],
                "candidate_sources_to_fill": [lane["candidate_source_name"]], "duplicate_or_obsolete_candidate": lane["duplicate_or_obsolete_candidate"],
                "lane_name": lane["lane_name"], "free_or_paid_category": lane["free_or_paid_category"],
            })
    return {"ok": True, "status": "ok", "report_name": "NCAAF_ARCHITECTURE_INVENTORY", "schema_version": "ncaaf_architecture_inventory_v1", "created_at": current_utc(), "sport": "americanfootball_ncaaf", "subdivisions_included": list(SUBDIVISIONS_INCLUDED), "inventory_entries": entries, "field_inventory_entries": entries, "fields_total": len(entries), "fields_populated_count": 0, "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"), "fields_missing_count": sum(1 for row in entries if row["current_population_status"] != "partial"), **_safety()}


def write_ncaaf_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NCAAF_ARCHITECTURE_INVENTORY.json"
    md_path = root / "NCAAF_ARCHITECTURE_INVENTORY.md"
    write_json(json_path, report)
    lines = ["# NCAAF Architecture Inventory", "", f"1. fields_total: {report.get('fields_total')}", f"2. fields_partial_count: {report.get('fields_partial_count')}", f"3. fields_missing_count: {report.get('fields_missing_count')}", "", "## Lanes"]
    for lane in ncaaf_lane_catalog():
        lines.append(f"- {lane['lane_name']} source={lane['candidate_source_name']} category={lane['free_or_paid_category']}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_ncaaf_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows = []
    for lane in ncaaf_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        rows.append({**lane, "sample_attempted": bool(sample), "sample_validation_status": sample.get("validation_status"), "sample_records_found": int(sample.get("records_tested", 0) or 0)})
    return {"ok": True, "status": "ok", "report_name": "NCAAF_FREE_VS_PAID_SOURCE_LEDGER", "schema_version": "ncaaf_free_vs_paid_source_ledger_v1", "created_at": current_utc(), "sport": "americanfootball_ncaaf", "subdivisions_included": list(SUBDIVISIONS_INCLUDED), "source_ledger_rows": rows, "source_ledger_row_count": len(rows), "free_open_loader_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_loader_needed"), "free_open_sample_required_count": 0, "free_open_manual_import_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_manual_import_needed"), "paid_data_subscription_required_count": sum(1 for row in rows if row["free_or_paid_category"] == "paid_data_subscription_required"), "license_terms_unclear_count": sum(1 for row in rows if row["free_or_paid_category"] == "license_terms_unclear"), **_safety()}


def write_ncaaf_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NCAAF_FREE_VS_PAID_SOURCE_LEDGER.json"
    md_path = root / "NCAAF_FREE_VS_PAID_SOURCE_LEDGER.md"
    write_json(json_path, report)
    lines = ["# NCAAF Free vs Paid Source Ledger", "", f"1. source_ledger_row_count: {report.get('source_ledger_row_count')}", f"2. free_open_loader_needed_count: {report.get('free_open_loader_needed_count')}", f"3. free_open_manual_import_needed_count: {report.get('free_open_manual_import_needed_count')}", f"4. paid_data_subscription_required_count: {report.get('paid_data_subscription_required_count')}", "", "## Lanes"]
    for row in report.get("source_ledger_rows") or []:
        lines.append(f"- {row.get('lane_name')} category={row.get('free_or_paid_category')} source={row.get('candidate_source_name')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}

