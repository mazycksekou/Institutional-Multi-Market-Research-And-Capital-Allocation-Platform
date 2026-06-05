from __future__ import annotations

from pathlib import Path
from typing import Any

from .combat_oxylabs_common import RUN_MODE, COMBAT_TYPES_INCLUDED, current_utc, lane_source_spec, url_hash, write_json, write_md


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

GAP_ACTIONS = (
    "sample_verify_one_event",
    "sample_verify_one_bout",
    "sample_verify_one_fighter",
    "sample_verify_one_promotion",
    "implement_loader",
    "backfill_approved_scope",
    "create_manual_import_template",
    "mark_paid_subscription_required",
    "mark_policy_blocked",
    "mark_terms_blocked",
    "mark_license_terms_unclear",
    "mark_login_paywall_captcha_blocked",
    "mark_unavailable_after_max_effort",
    "mark_obsolete_or_duplicate",
    "update_model_readiness_only",
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
    "AllowOneEventValidation": True,
    "AllowOneFighterValidation": True,
    "AllowFreeVsPaidAudit": True,
    "AllowCalibrationReadinessAudit": True,
    "AllowBackfill": True,
    "AllowFinalityAudit": True,
}

SPORTS = {
    "combat": {
        "display_name": "Combat",
        "module": "combat",
        "model": "fighter_striking_grappling_finish_model",
        "readiness_recommendation": "blocked_by_policy",
    }
}


def _safety() -> dict[str, Any]:
    return dict(SAFETY_FLAGS)


def _lane(
    lane_name: str,
    field_group: str,
    *,
    combat_type: str,
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
    future_leakage_risk: str = "low_if_joined_by_event_start",
    model_eligible: bool | None = None,
    duplicate_or_obsolete_candidate: bool = False,
    coverage_start: str = "historical_public_sample_scope",
    coverage_end: str = "historical_public_sample_scope",
    loader_exists: bool = True,
    manual_template_required: bool = False,
    manual_import_possible: bool = True,
    paid_priority: str | None = None,
) -> dict[str, Any]:
    if category not in FREE_VS_PAID_CATEGORIES:
        raise ValueError(f"Unsupported Combat free-vs-paid category: {category}")
    if next_action not in GAP_ACTIONS:
        raise ValueError(f"Unsupported Combat action: {next_action}")
    source = lane_source_spec({"source_id": source_id, "free_or_paid_category": category, "lane_name": lane_name})
    return {
        "sport": "combat",
        "sport_name": "Combat",
        "combat_type": combat_type,
        "module": "combat",
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
        "sample_required": bool(category in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"}),
        "sample_attempted": False,
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
        "duplicate_or_obsolete_candidate": duplicate_or_obsolete_candidate,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "manual_import_possible": bool(manual_import_possible),
        "paid_priority": paid_priority,
    }


def combat_lane_catalog() -> list[dict[str, Any]]:
    return [
        _lane(
            "boxing_bout_results",
            "boxing bout results and labels",
            combat_type="Boxing",
            entity_level="bout",
            fields=["bout_id", "date", "boxer_a_name", "boxer_b_name", "status", "winner", "method_of_victory", "total_rounds", "scheduled_rounds", "weight_class"],
            table="combat_boxing_bouts",
            source_id="combat_open_boxing_data_repo",
            source_family="open_github_csv",
            category="free_open_loader_needed",
            current_status="open_boxing_repo_visible_loader_needed",
            calibration_impact="anchors historical boxing labels, outcomes, and distance/finish splits",
            next_action="backfill_approved_scope",
            final_reason="Open Boxing provides licensable bout-level boxing history suitable for normalized backfill.",
        ),
        _lane(
            "boxing_fighter_identity_birthdates",
            "boxing fighter identity and birthdates",
            combat_type="Boxing",
            entity_level="fighter",
            fields=["champion_id", "first_name", "last_name", "short_name", "born"],
            table="combat_boxing_fighters",
            source_id="combat_open_boxing_data_repo",
            source_family="open_github_csv",
            category="free_open_loader_needed",
            current_status="open_boxing_repo_visible_loader_needed",
            calibration_impact="supports fighter identity joins and age-derived boxing context",
            next_action="backfill_approved_scope",
            final_reason="Open Boxing exposes fighter identity and birthdate rows in the licensed GitHub data repository.",
        ),
        _lane(
            "boxing_finish_round_context",
            "boxing finish and round context",
            combat_type="Boxing",
            entity_level="bout",
            fields=["method_of_victory", "winner", "status", "total_rounds", "scheduled_rounds", "weight_class", "titles"],
            table="combat_boxing_finish_context",
            source_id="combat_open_boxing_data_repo",
            source_family="open_github_csv",
            category="free_open_loader_needed",
            current_status="open_boxing_repo_visible_loader_needed",
            calibration_impact="supports finish probability, distance markets, and method-style boxing context",
            next_action="backfill_approved_scope",
            final_reason="Open Boxing provides finished bout and scheduled-round context that is safe to normalize.",
        ),
        _lane(
            "boxing_title_reign_context",
            "boxing title and reign context",
            combat_type="Boxing",
            entity_level="title_reign",
            fields=["reign_id", "begins", "ends", "champion_id", "name", "current", "title", "org_abbreviation"],
            table="combat_boxing_title_reigns",
            source_id="combat_open_boxing_data_repo",
            source_family="open_github_csv",
            category="free_open_loader_needed",
            current_status="open_boxing_repo_visible_loader_needed",
            calibration_impact="improves title-fight and sanctioning-body context for boxing-specific readiness",
            next_action="backfill_approved_scope",
            final_reason="Open Boxing includes title and reign tables that can be normalized safely.",
        ),
        _lane(
            "boxing_location_context",
            "boxing venue and geography context",
            combat_type="Boxing",
            entity_level="location",
            fields=["location_id", "venue", "locality", "country", "latitude", "longitude"],
            table="combat_boxing_locations",
            source_id="combat_open_boxing_data_repo",
            source_family="open_github_csv",
            category="free_open_loader_needed",
            current_status="open_boxing_repo_visible_loader_needed",
            calibration_impact="supports boxing venue and geography joins without introducing execution or market risk",
            next_action="backfill_approved_scope",
            final_reason="Open Boxing exposes location rows in a structured open CSV form.",
        ),
        _lane(
            "mma_bout_results_context",
            "mma bout result and outcome context",
            combat_type="UFC/MMA",
            entity_level="bout",
            fields=["event_id", "bout_id", "fight_date", "promotion", "weight_class", "scheduled_rounds", "result", "method_of_victory", "finish_round", "finish_time"],
            table="combat_mma_bouts",
            source_id="combat_ufcstats_round_stats",
            source_family="official_stats_site",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="would anchor UFC/MMA result labels, finish timing, and round/total markets",
            next_action="backfill_approved_scope",
            final_reason="UFC Stats is technically reachable, but no compliant automated extraction path was approved for this pass.",
        ),
        _lane(
            "mma_fighter_physical_profile",
            "mma fighter physical profile",
            combat_type="UFC/MMA",
            entity_level="fighter_pre_match",
            fields=["fighter_age", "opponent_age", "fighter_reach", "opponent_reach", "fighter_height", "opponent_height", "fighter_stance", "opponent_stance"],
            table="combat_mma_fighter_profiles",
            source_id="combat_ufcstats_round_stats",
            source_family="official_stats_site",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="would strengthen fighter identity, physical-profile, and matchup-adjustment features for UFC/MMA",
            next_action="backfill_approved_scope",
            final_reason="Physical-profile fields exist on UFC-owned stats pages, but automated normalized extraction was not approved.",
        ),
        _lane(
            "mma_striking_summary_stats",
            "mma striking summary statistics",
            combat_type="UFC/MMA",
            entity_level="fighter_pre_match",
            fields=["fighter_strikes_landed_per_min", "opponent_strikes_landed_per_min", "fighter_strikes_absorbed_per_min", "opponent_strikes_absorbed_per_min", "fighter_striking_accuracy", "opponent_striking_accuracy", "fighter_striking_defense", "opponent_striking_defense"],
            table="combat_mma_striking_summary",
            source_id="combat_ufcstats_round_stats",
            source_family="official_stats_site",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="would materially improve striking, method, and prop-market readiness for UFC/MMA",
            next_action="backfill_approved_scope",
            final_reason="Public MMA striking surfaces were reviewed, but automation remains blocked under the current policy floor.",
        ),
        _lane(
            "mma_grappling_control_stats",
            "mma grappling and control statistics",
            combat_type="UFC/MMA",
            entity_level="fighter_pre_match",
            fields=["fighter_takedown_average", "opponent_takedown_average", "fighter_takedown_accuracy", "opponent_takedown_accuracy", "fighter_takedown_defense", "opponent_takedown_defense", "fighter_submission_average", "opponent_submission_average", "control_time_average"],
            table="combat_mma_grappling_summary",
            source_id="combat_ufcstats_round_stats",
            source_family="official_stats_site",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="would materially improve grappling, decision, distance, and prop-market readiness for UFC/MMA",
            next_action="backfill_approved_scope",
            final_reason="Public MMA grappling/control surfaces were reviewed, but automated normalized extraction was not approved.",
        ),
        _lane(
            "mma_finish_history_context",
            "mma finish history and timing context",
            combat_type="UFC/MMA",
            entity_level="fighter_pre_match",
            fields=["fighter_finish_rate", "opponent_finish_rate", "fighter_ko_tko_rate", "opponent_ko_tko_rate", "fighter_submission_rate", "opponent_submission_rate", "fighter_decision_rate", "opponent_decision_rate"],
            table="combat_mma_finish_history",
            source_id="combat_ufcstats_round_stats",
            source_family="official_stats_site",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="would improve finish, distance, and method-of-victory splits for UFC/MMA",
            next_action="backfill_approved_scope",
            final_reason="Public MMA finish-history surfaces were reviewed, but automated normalized extraction was not approved.",
        ),
        _lane(
            "mma_weighin_weight_miss_context",
            "mma weigh-in and missed-weight context",
            combat_type="UFC/MMA",
            entity_level="fighter_event",
            fields=["weigh_in_status", "missed_weight_flag", "official_weight", "observed_at"],
            table="combat_mma_weighins",
            source_id="combat_ufc_official_weighins",
            source_family="official_news_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="weigh-in context affects no-bet gating and late confidence modifiers",
            next_action="create_manual_import_template",
            final_reason="Official weigh-in context remains manual-only because UFC terms restrict automation and timing matters.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "mma_injury_withdrawal_availability",
            "mma injury, withdrawal, and availability context",
            combat_type="UFC/MMA",
            entity_level="fighter_event",
            fields=["injury_status", "withdrawal_note", "availability_status", "observed_at"],
            table="combat_mma_availability",
            source_id="combat_ufc_official_event_pages",
            source_family="official_event_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="availability context affects no-bet gating and volatility management",
            next_action="create_manual_import_template",
            final_reason="Availability and cancellation context remains manual-only under the current policy floor.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "mma_medical_suspension_context",
            "mma medical suspension context",
            combat_type="UFC/MMA",
            entity_level="fighter_event",
            fields=["medical_suspension_context", "suspension_days", "commission_name", "observed_at"],
            table="combat_mma_medical_suspensions",
            source_id="combat_commission_medical_records",
            source_family="official_commission_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="medical suspension context is useful for availability and layoff risk controls",
            next_action="create_manual_import_template",
            final_reason="Commission suspension records remain manual-only because timestamped review is required.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "mma_referee_judging_assignments",
            "mma referee and judging assignments",
            combat_type="UFC/MMA",
            entity_level="event_officials",
            fields=["referee_name", "judge_names", "commission_name", "official_assignment_source", "observed_at"],
            table="combat_mma_official_assignments",
            source_id="combat_commission_medical_records",
            source_family="official_commission_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="referee and judging context is moderate-signal enrichment that still requires manual capture here",
            next_action="create_manual_import_template",
            final_reason="Public officiating assignments remain manual-only in this pass.",
            loader_exists=False,
            manual_template_required=True,
            model_eligible=False,
        ),
        _lane(
            "mma_cancellation_short_notice_context",
            "mma cancellation and short-notice context",
            combat_type="UFC/MMA",
            entity_level="event_bout",
            fields=["short_notice_flag", "opponent_change_context", "cancellation_note", "observed_at"],
            table="combat_mma_short_notice_context",
            source_id="combat_ufc_official_event_pages",
            source_family="official_event_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="short-notice and opponent-change context matters for volatility and fatigue flags",
            next_action="create_manual_import_template",
            final_reason="Short-notice and cancellation context remains manual-only because source timing must be reviewed.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "opponent_strength_rankings_context",
            "mma opponent strength and rankings context",
            combat_type="UFC/MMA",
            entity_level="fighter_pre_match",
            fields=["opponent_strength_rating", "division_rank", "promotion_rank", "ranking_snapshot_date", "ranking_source"],
            table="combat_mma_rankings",
            source_id="combat_tapology_event_pages",
            source_family="reference_rankings_pages",
            category="policy_blocked",
            current_status="blocked_by_policy",
            calibration_impact="rankings context would help opponent-strength and confidence features, but automation remains blocked",
            next_action="mark_policy_blocked",
            final_reason="Reference rankings sites were reviewed, but no compliant automated path was approved in this pass.",
            loader_exists=False,
        ),
        _lane(
            "boxing_record_depth_context",
            "boxing record depth and sanctioning reference context",
            combat_type="Boxing",
            entity_level="fighter_reference",
            fields=["pro_record_summary", "title_challenge_count", "last_six_bouts", "record_reference_source"],
            table="combat_boxing_record_depth",
            source_id="combat_boxrec_records",
            source_family="record_database",
            category="login_paywall_captcha_blocked",
            current_status="login_or_terms_blocked",
            calibration_impact="deeper boxing record context would help boxing-specific readiness, but automation remains blocked",
            next_action="mark_login_paywall_captcha_blocked",
            final_reason="BoxRec remains login/terms blocked for automated use in this pass.",
            loader_exists=False,
            model_eligible=False,
        ),
        _lane(
            "fighter_metadata_entities",
            "fighter metadata entities",
            combat_type="UFC/MMA/Boxing",
            entity_level="fighter",
            fields=["entity_name", "country", "birth_date", "wikidata_id"],
            table="combat_fighter_metadata",
            source_id="combat_wikidata_fighter_entities",
            source_family="structured_open_metadata",
            category="free_open_partial",
            current_status="metadata_only_candidate",
            calibration_impact="supplemental identity metadata helps lightweight joins and alias normalization",
            next_action="sample_verify_one_fighter",
            final_reason="Wikidata remains metadata-only for this pass.",
            loader_exists=False,
            model_eligible=False,
        ),
        _lane(
            "promotion_roster_metadata",
            "promotion and roster metadata",
            combat_type="UFC/MMA/Boxing",
            entity_level="promotion_fighter",
            fields=["promotion_name", "fighter_name", "country", "roster_note"],
            table="combat_promotion_roster_metadata",
            source_id="combat_wikipedia_combat_entities",
            source_family="structured_open_metadata",
            category="free_open_partial",
            current_status="metadata_only_candidate",
            calibration_impact="supplemental promotion/roster metadata helps alias normalization and manual review context",
            next_action="sample_verify_one_fighter",
            final_reason="Wikipedia remains metadata-only for this pass.",
            loader_exists=False,
            model_eligible=False,
        ),
        _lane(
            "community_api_wrapper_context",
            "community UFC stats wrapper context",
            combat_type="UFC/MMA",
            entity_level="reference",
            fields=["wrapper_repo_name", "upstream_source", "license_note", "api_surface_note"],
            table="combat_reference_wrappers",
            source_id="combat_ufc_stats_api_wrapper_repo",
            source_family="community_wrapper_repo",
            category="license_terms_unclear",
            current_status="visible_but_upstream_rights_unclear",
            calibration_impact="community wrappers show technically useful paths, but rights remain unclear",
            next_action="mark_license_terms_unclear",
            final_reason="Public wrappers exist, but they inherit UFC-owned upstream rights ambiguity.",
            loader_exists=False,
            model_eligible=False,
            manual_template_required=True,
        ),
        _lane(
            "community_scraper_bundle_context",
            "community mma scraper bundle context",
            combat_type="UFC/MMA",
            entity_level="reference",
            fields=["repo_name", "upstream_sources", "scrape_scope", "license_note"],
            table="combat_reference_scrapers",
            source_id="combat_mma_data_scraper_repo",
            source_family="community_scraper_repo",
            category="license_terms_unclear",
            current_status="visible_but_upstream_rights_unclear",
            calibration_impact="community scrapers demonstrate technical availability, but rights remain unclear",
            next_action="mark_license_terms_unclear",
            final_reason="Public scraper bundles combine restricted upstream sources and remain legally unclear for automated use.",
            loader_exists=False,
            model_eligible=False,
            manual_template_required=True,
        ),
        _lane(
            "tracking_punch_pattern_context",
            "tracking, punch pattern, and round microdata context",
            combat_type="UFC/MMA/Boxing",
            entity_level="round_sequence",
            fields=["punch_location_split", "power_vs_jab_split", "round_micro_events", "tracking_feed_reference"],
            table="combat_tracking_context",
            source_id="combat_paid_tracking_vendor",
            source_family="paid_tracking_vendor",
            category="paid_data_subscription_required",
            current_status="paid_vendor_required",
            calibration_impact="would materially improve fighter props, distance markets, and style-adjusted tracking context",
            next_action="mark_paid_subscription_required",
            final_reason="Deeper tracking and punch-level context remains a paid/licensed vendor lane after exhausting free/open paths.",
            loader_exists=False,
            manual_template_required=True,
            paid_priority="high",
        ),
    ]


def _new_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    recommended = {
        "boxing_bout_results": ["winner_name_normalized", "finished_flag", "weight_class_slug"],
        "boxing_fighter_identity_birthdates": ["fighter_birth_year", "fighter_name_slug"],
        "boxing_finish_round_context": ["inside_distance_flag", "decision_flag", "stoppage_flag"],
        "boxing_title_reign_context": ["title_count_on_line", "current_champion_flag", "sanctioning_body_abbreviation"],
        "boxing_location_context": ["country_code_normalized", "venue_slug"],
        "fighter_metadata_entities": ["entity_alias_hash", "country_code_normalized"],
        "promotion_roster_metadata": ["promotion_slug", "fighter_name_slug"],
    }
    if lane["free_or_paid_category"] not in {"free_open_populated", "free_open_partial", "free_open_loader_needed", "free_open_sample_required"}:
        return []
    return recommended.get(lane["lane_name"], [])


def _lane_sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not sample_verification_results:
        return {}
    return dict(sample_verification_results.get("source_result_index") or {})


def default_combat_loader_lanes() -> list[dict[str, Any]]:
    return [
        lane
        for lane in combat_lane_catalog()
        if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"}
    ]


def build_combat_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries: list[dict[str, Any]] = []
    for lane in combat_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        records = int(sample.get("records_tested", 0) or 0)
        validation_status = str(sample.get("validation_status") or "")
        if validation_status == "sample_verified" and records > 0:
            population_status = "partial" if lane["free_or_paid_category"] != "free_open_populated" else "populated"
        elif lane["free_or_paid_category"] == "obsolete_or_duplicate":
            population_status = "obsolete_or_duplicate"
        elif lane["free_or_paid_category"] in {
            "free_open_manual_import_needed",
            "paid_data_subscription_required",
            "license_terms_unclear",
            "policy_blocked",
            "robots_blocked",
            "terms_blocked",
            "login_paywall_captcha_blocked",
        }:
            population_status = "blocked"
        else:
            population_status = "manual_or_review_required"
        for field in lane["fields"]:
            entries.append(
                {
                    "sport": lane["sport"],
                    "combat_type": lane["combat_type"],
                    "module": lane["module"],
                    "table": lane["table"],
                    "schema": lane["table"],
                    "field_name": field,
                    "entity_level": lane["entity_level"],
                    "current_population_status": population_status,
                    "current_record_count": records,
                    "current_source": lane["candidate_source_name"],
                    "source_family": lane["source_family"],
                    "data_type": lane["data_type"],
                    "coverage_start": lane["coverage_start"],
                    "coverage_end": lane["coverage_end"],
                    "cutoff_safe": lane["cutoff_safe"],
                    "future_leakage_risk": lane["future_leakage_risk"],
                    "model_eligible": lane["model_eligible"],
                    "calibration_impact": lane["calibration_impact"],
                    "missing_reason": "" if population_status in {"populated", "partial"} else lane["final_reason"],
                    "candidate_sources_to_fill": [lane["candidate_source_name"]],
                    "duplicate_or_obsolete_candidate": lane["duplicate_or_obsolete_candidate"],
                    "lane_name": lane["lane_name"],
                    "free_or_paid_category": lane["free_or_paid_category"],
                }
            )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMBAT_ARCHITECTURE_INVENTORY",
        "schema_version": "combat_architecture_inventory_v1",
        "created_at": current_utc(),
        "sport": "combat",
        "combat_types_included": list(COMBAT_TYPES_INCLUDED),
        "inventory_entries": entries,
        "field_inventory_entries": entries,
        "fields_total": len(entries),
        "fields_populated_count": sum(1 for row in entries if row["current_population_status"] == "populated"),
        "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"),
        "fields_missing_count": sum(1 for row in entries if row["current_population_status"] not in {"populated", "partial"}),
        **_safety(),
    }


def write_combat_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMBAT_ARCHITECTURE_INVENTORY.json"
    md_path = root / "COMBAT_ARCHITECTURE_INVENTORY.md"
    write_json(json_path, report)
    lines = [
        "# Combat Architecture Inventory",
        "",
        f"1. sport: {report.get('sport')}",
        f"2. combat_types_included: {', '.join(report.get('combat_types_included') or [])}",
        f"3. fields_total: {report.get('fields_total')}",
        f"4. fields_partial_count: {report.get('fields_partial_count')}",
        f"5. fields_missing_count: {report.get('fields_missing_count')}",
        "",
        "## Lanes",
    ]
    seen = set()
    for row in report.get("inventory_entries") or []:
        key = row.get("lane_name")
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {row.get('lane_name')} source={row.get('current_source')} status={row.get('current_population_status')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_combat_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows: list[dict[str, Any]] = []
    for lane in combat_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        rows.append(
            {
                "sport": lane["sport"],
                "combat_type": lane["combat_type"],
                "module": lane["module"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane["field_or_feature_group"],
                "fields": list(lane["fields"]),
                "entity_level": lane["entity_level"],
                "free_or_paid_category": lane["free_or_paid_category"],
                "current_status": lane["current_status"],
                "source_id": lane["source_id"],
                "candidate_source_name": lane["candidate_source_name"],
                "source_domain": lane["source_domain"],
                "source_url_hash": lane["source_url_hash"],
                "source_family": lane["source_family"],
                "retrieval_method": lane["retrieval_method"],
                "policy_status": lane["policy_status"],
                "license_or_terms_note": lane["license_or_terms_note"],
                "sample_required": lane["sample_required"],
                "sample_attempted": bool(sample),
                "sample_validation_status": sample.get("validation_status"),
                "sample_records_found": int(sample.get("records_tested", 0) or 0),
                "loader_exists": lane["loader_exists"],
                "manual_template_exists": lane["manual_template_exists"],
                "manual_template_required": lane["manual_template_required"],
                "cutoff_safe": lane["cutoff_safe"],
                "future_leakage_risk": lane["future_leakage_risk"],
                "model_eligible": lane["model_eligible"],
                "calibration_impact": lane["calibration_impact"],
                "next_action": lane["next_action"],
                "final_reason": lane["final_reason"],
                "duplicate_or_obsolete_candidate": lane["duplicate_or_obsolete_candidate"],
                "coverage_start": lane["coverage_start"],
                "coverage_end": lane["coverage_end"],
                "manual_import_possible": lane["manual_import_possible"],
                "paid_priority": lane["paid_priority"],
            }
        )
    return {
        "ok": True,
        "status": "ok",
        "report_name": "COMBAT_FREE_VS_PAID_SOURCE_LEDGER",
        "schema_version": "combat_free_vs_paid_source_ledger_v1",
        "created_at": current_utc(),
        "sport": "combat",
        "combat_types_included": list(COMBAT_TYPES_INCLUDED),
        "source_ledger_rows": rows,
        "source_ledger_row_count": len(rows),
        "free_open_loader_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_loader_needed"),
        "free_open_sample_required_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_sample_required"),
        "free_open_manual_import_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_manual_import_needed"),
        "paid_data_subscription_required_count": sum(1 for row in rows if row["free_or_paid_category"] == "paid_data_subscription_required"),
        "license_terms_unclear_count": sum(1 for row in rows if row["free_or_paid_category"] == "license_terms_unclear"),
        **_safety(),
    }


def write_combat_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "COMBAT_FREE_VS_PAID_SOURCE_LEDGER.json"
    md_path = root / "COMBAT_FREE_VS_PAID_SOURCE_LEDGER.md"
    write_json(json_path, report)
    lines = [
        "# Combat Free vs Paid Source Ledger",
        "",
        f"1. source_ledger_row_count: {report.get('source_ledger_row_count')}",
        f"2. free_open_loader_needed_count: {report.get('free_open_loader_needed_count')}",
        f"3. free_open_manual_import_needed_count: {report.get('free_open_manual_import_needed_count')}",
        f"4. paid_data_subscription_required_count: {report.get('paid_data_subscription_required_count')}",
        f"5. license_terms_unclear_count: {report.get('license_terms_unclear_count')}",
        "",
        "## Lanes",
    ]
    for row in report.get("source_ledger_rows") or []:
        lines.append(f"- {row.get('lane_name')} category={row.get('free_or_paid_category')} source={row.get('candidate_source_name')}")
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
