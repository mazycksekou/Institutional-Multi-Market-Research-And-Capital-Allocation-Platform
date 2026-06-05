from __future__ import annotations

from pathlib import Path
from typing import Any

from .tennis_oxylabs_common import RUN_MODE, TOURS_INCLUDED, current_utc, lane_source_spec, url_hash, write_json, write_md


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
    "sample_verify_one_tour_season",
    "sample_verify_one_tournament",
    "sample_verify_one_match",
    "sample_verify_one_player",
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
    "AllowOneSeasonValidation": True,
    "AllowFreeVsPaidAudit": True,
    "AllowCalibrationReadinessAudit": True,
    "AllowBackfill": True,
    "AllowFinalityAudit": True,
}

SPORTS = {
    "tennis": {
        "display_name": "Tennis",
        "module": "tennis",
        "model": "elo_serve_return_markov_tennis_model",
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
    future_leakage_risk: str = "low_if_joined_by_match_start",
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
        raise ValueError(f"Unsupported Tennis free-vs-paid category: {category}")
    if next_action not in GAP_ACTIONS:
        raise ValueError(f"Unsupported Tennis action: {next_action}")
    source = lane_source_spec({"source_id": source_id, "free_or_paid_category": category, "lane_name": lane_name})
    return {
        "sport": "tennis",
        "sport_name": "Tennis",
        "tour": tour,
        "module": "tennis",
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


def tennis_lane_catalog() -> list[dict[str, Any]]:
    return [
        _lane(
            "atp_match_results",
            "ATP historical match results",
            tour="ATP",
            entity_level="match",
            fields=["tourney_id", "tourney_name", "tourney_date", "match_num", "winner_id", "winner_name", "loser_id", "loser_name", "score", "minutes"],
            table="tennis_matches_atp",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="anchors historical labels, winner/loser outcomes, and stable match identity for ATP markets",
            next_action="backfill_approved_scope",
            final_reason="Historical ATP result data is technically reachable but cannot be automated until source-license scope is cleared.",
        ),
        _lane(
            "wta_match_results",
            "WTA historical match results",
            tour="WTA",
            entity_level="match",
            fields=["tourney_id", "tourney_name", "tourney_date", "match_num", "winner_id", "winner_name", "loser_id", "loser_name", "score", "minutes"],
            table="tennis_matches_wta",
            source_id="tennis_jeff_sackmann_wta_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="anchors historical labels, winner/loser outcomes, and stable match identity for WTA markets",
            next_action="backfill_approved_scope",
            final_reason="Historical WTA result data is technically reachable but cannot be automated until source-license scope is cleared.",
        ),
        _lane(
            "player_identity_crosswalk",
            "player identity and crosswalk",
            tour="ATP/WTA",
            entity_level="player_match",
            fields=["winner_id", "winner_ioc", "winner_hand", "winner_ht", "loser_id", "loser_ioc", "loser_hand", "loser_ht"],
            table="tennis_player_crosswalk",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="supports player identity joins, handedness context, and longitudinal player features",
            next_action="backfill_approved_scope",
            final_reason="Crosswalk fields sit inside the Jeff Sackmann historical CSVs but inherit the same license-review blocker.",
        ),
        _lane(
            "tournament_surface_round_context",
            "tournament, surface, round, and level context",
            tour="ATP/WTA/Grand Slams",
            entity_level="match",
            fields=["surface", "draw_size", "tourney_level", "round", "best_of"],
            table="tennis_match_context",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="provides surface, round, and best-of context needed by the Markov simulation and Grand Slam handling",
            next_action="backfill_approved_scope",
            final_reason="Tournament context is technically present but blocked behind the same license-review decision as the upstream CSVs.",
        ),
        _lane(
            "serve_return_match_stats",
            "serve and return match stats",
            tour="ATP/WTA",
            entity_level="match_player",
            fields=["w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon", "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon", "l_2ndWon"],
            table="tennis_match_serve_return_stats",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="covers the core serve-return inputs behind hold/break, service points won, and return points won estimates",
            next_action="backfill_approved_scope",
            final_reason="Serve-return statistics are available in the historical CSVs but remain blocked until license scope is cleared.",
        ),
        _lane(
            "break_hold_derivations",
            "break and hold derivations",
            tour="ATP/WTA",
            entity_level="match_player",
            fields=["w_SvGms", "w_bpSaved", "w_bpFaced", "l_SvGms", "l_bpSaved", "l_bpFaced"],
            table="tennis_match_break_hold_stats",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="supports break points saved/faced and downstream hold-rate and break-rate derivations",
            next_action="backfill_approved_scope",
            final_reason="Break/hold derivations are technically feasible but inherit the unresolved reuse/license blocker.",
        ),
        _lane(
            "ranking_snapshot_history",
            "ranking snapshot history",
            tour="ATP/WTA",
            entity_level="match_player",
            fields=["winner_rank", "winner_rank_points", "loser_rank", "loser_rank_points"],
            table="tennis_ranking_snapshots",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="supports ranking priors, ranking deltas, and ranking-based market calibration features",
            next_action="backfill_approved_scope",
            final_reason="Historical rank snapshots exist in-source but remain blocked until license interpretation is accepted.",
        ),
        _lane(
            "recent_form_rest_fatigue",
            "recent form, rest, and fatigue context",
            tour="ATP/WTA",
            entity_level="player_pre_match",
            fields=["tourney_date", "minutes", "best_of", "round", "winner_age", "loser_age"],
            table="tennis_recent_form_fatigue",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="supports recent form, match-load, and rest/fatigue proxies used by confidence gating",
            next_action="backfill_approved_scope",
            final_reason="Recent-form and fatigue proxies are derivable but remain hard-blocked until source-license scope is cleared.",
        ),
        _lane(
            "head_to_head_context",
            "head-to-head context",
            tour="ATP/WTA",
            entity_level="player_pair",
            fields=["winner_id", "loser_id", "surface", "tourney_date", "score"],
            table="tennis_head_to_head",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="supports opponent-specific priors and surface-conditioned head-to-head features",
            next_action="backfill_approved_scope",
            final_reason="Head-to-head derivations are technically straightforward but remain blocked by the upstream license decision.",
        ),
        _lane(
            "retirement_walkover_context",
            "retirement and walkover context",
            tour="ATP/WTA",
            entity_level="match",
            fields=["score", "minutes", "round", "best_of"],
            table="tennis_retire_walkover_context",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="supports retirement, walkover, and incomplete-match handling for no-bet and volatility controls",
            next_action="backfill_approved_scope",
            final_reason="Retirement and walkover cues are embedded in scorelines but remain blocked by the same license-review issue.",
        ),
        _lane(
            "grand_slam_best_of_context",
            "Grand Slam best-of and format context",
            tour="Grand Slam men/Grand Slam women",
            entity_level="match",
            fields=["tourney_level", "best_of", "surface", "round"],
            table="tennis_grand_slam_format_context",
            source_id="tennis_jeff_sackmann_atp_matches",
            source_family="github_open_historical_csv",
            category="free_open_loader_needed",
            current_status="technical_source_exists_policy_review_required",
            calibration_impact="preserves best-of-three versus best-of-five handling across ATP and Grand Slam markets",
            next_action="backfill_approved_scope",
            final_reason="Grand Slam format context is technically available but still blocked by the unresolved reuse/license scope.",
        ),
        _lane(
            "point_by_point_charting_context",
            "point-by-point and charting context",
            tour="ATP/WTA",
            entity_level="point_sequence",
            fields=["match_id", "serve_direction_preference", "return_position_proxy", "rally_length_profile"],
            table="tennis_point_charting_context",
            source_id="tennis_match_charting_project_repo",
            source_family="github_open_charting_repo",
            category="free_open_sample_required",
            current_status="open_repo_visible_license_scope_needs_review",
            calibration_impact="would strengthen point-level, serve-placement, and rally-style features for advanced markets",
            next_action="sample_verify_one_match",
            final_reason="Detailed charting data is visible publicly but its downstream automation scope needs legal review before use.",
        ),
        _lane(
            "player_metadata_handedness_country",
            "player metadata, handedness, and country supplemental",
            tour="ATP/WTA",
            entity_level="player",
            fields=["player_name", "player_country", "handedness_metadata", "birth_year_metadata"],
            table="tennis_player_metadata",
            source_id="tennis_wikidata_player_entities",
            source_family="structured_open_metadata",
            category="free_open_partial",
            current_status="metadata_only_candidate",
            calibration_impact="provides low-risk metadata supplementation when the main historical feeds are blocked",
            next_action="sample_verify_one_player",
            final_reason="Metadata-only supplemental lane is suitable for attribution-preserving enrichment, not full model backfill.",
            loader_exists=False,
            model_eligible=False,
        ),
        _lane(
            "official_rankings_stats_pages",
            "official rankings and stats pages",
            tour="ATP/WTA",
            entity_level="player_snapshot",
            fields=["official_rank", "official_rank_points", "official_serve_stats", "official_return_stats"],
            table="tennis_official_rankings_stats",
            source_id="tennis_atp_official_rankings",
            source_family="official_rankings_pages",
            category="needs_manual_review",
            current_status="official_pages_visible_terms_restrictive",
            calibration_impact="would strengthen live official rankings and serve/return splits if a compliant path existed",
            next_action="mark_policy_blocked",
            final_reason="Official rankings/stats pages remain blocked because no compliant automated extraction path was approved.",
            loader_exists=False,
        ),
        _lane(
            "injury_withdrawal_availability",
            "injury, withdrawal, and availability context",
            tour="ATP/WTA/Grand Slams",
            entity_level="player_pre_match",
            fields=["injury_status", "withdrawal_risk", "availability_note", "observed_at"],
            table="tennis_injury_withdrawal_context",
            source_id="tennis_itf_withdrawal_news",
            source_family="official_news_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="availability context materially affects no-bet gating and confidence caps",
            next_action="create_manual_import_template",
            final_reason="Timestamped injury and withdrawal context still requires manual review and timestamp capture.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "chair_umpire_assignments",
            "chair umpire and officials assignments",
            tour="Grand Slams",
            entity_level="match_official",
            fields=["chair_umpire", "official_assignment_source", "observed_at"],
            table="tennis_match_officials",
            source_id="tennis_grand_slam_draw_pages",
            source_family="official_event_pages",
            category="free_open_manual_import_needed",
            current_status="manual_timestamped_capture_needed",
            calibration_impact="official tendencies are weaker-to-moderate context and can only be safely captured manually in this pass",
            next_action="create_manual_import_template",
            final_reason="Officials assignments require manual timestamped capture from official event pages.",
            loader_exists=False,
            manual_template_required=True,
            model_eligible=False,
        ),
        _lane(
            "court_speed_environment_context",
            "court speed and environment context",
            tour="ATP/WTA/Grand Slams",
            entity_level="event",
            fields=["court_speed_index", "indoor_outdoor", "roof_status", "weather_bucket"],
            table="tennis_court_environment_context",
            source_id="tennis_tennis_data_uk_history",
            source_family="public_tennis_stats_site",
            category="license_terms_unclear",
            current_status="visible_but_reuse_scope_unclear",
            calibration_impact="court-speed and environment context would improve totals, tiebreak, and surface-specific markets",
            next_action="mark_license_terms_unclear",
            final_reason="No clearly approved public source path was found for automated court-speed/environment backfill in this pass.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "historical_odds_context",
            "historical odds and market context",
            tour="ATP/WTA",
            entity_level="match_market",
            fields=["opening_odds", "closing_odds", "market_anchor_probability", "odds_timestamp"],
            table="tennis_historical_market_context",
            source_id="tennis_tennis_data_uk_history",
            source_family="public_tennis_stats_site",
            category="license_terms_unclear",
            current_status="visible_but_reuse_scope_unclear",
            calibration_impact="historical price anchors would materially improve market-anchor and CLV-style calibration fields",
            next_action="mark_license_terms_unclear",
            final_reason="Historical market files were found but reuse scope remains legally unclear for automated integration here.",
            loader_exists=False,
            manual_template_required=True,
        ),
        _lane(
            "tracking_shot_pattern_context",
            "tracking and shot-pattern context",
            tour="ATP/WTA/Grand Slams",
            entity_level="shot_sequence",
            fields=["serve_speed_distribution", "shot_pattern_profile", "return_position_tracking", "ball_striking_speed"],
            table="tennis_tracking_context",
            source_id="tennis_paid_tracking_vendor",
            source_family="paid_tracking_vendor",
            category="paid_data_subscription_required",
            current_status="paid_vendor_required",
            calibration_impact="would materially improve player props, shot-pattern, rally-style, and tracking-level confidence",
            next_action="mark_paid_subscription_required",
            final_reason="Broad tracking and shot-pattern context remains a paid vendor lane after exhausting free/open paths.",
            loader_exists=False,
            manual_template_required=True,
            paid_priority="high",
        ),
        _lane(
            "unofficial_reference_tables",
            "unofficial reference tables",
            tour="ATP/WTA",
            entity_level="reference",
            fields=["reference_table_name", "reference_metric_name"],
            table="tennis_reference_tables_blocked",
            source_id="tennis_ultimate_tennis_statistics",
            source_family="restricted_reference_sites",
            category="policy_blocked",
            current_status="blocked_by_repo_policy",
            calibration_impact="reference-only tables were checked and rejected for automation under the current policy floor",
            next_action="mark_policy_blocked",
            final_reason="Unofficial reference sites were checked but remain blocked under explicit repo/user policy.",
            loader_exists=False,
            model_eligible=False,
        ),
        _lane(
            "community_duplicate_mirror",
            "community duplicate mirror",
            tour="ATP",
            entity_level="reference",
            fields=["mirror_source", "upstream_source"],
            table="tennis_duplicate_sources",
            source_id="tennis_github_duplicate_mirror",
            source_family="community_duplicate_source",
            category="obsolete_or_duplicate",
            current_status="duplicate_mirror_no_new_rights",
            calibration_impact="duplicate mirrors add no new coverage or rights beyond the upstream source already reviewed",
            next_action="mark_obsolete_or_duplicate",
            final_reason="Community mirror duplicates the upstream dataset and offers no added compliance advantage.",
            loader_exists=False,
            model_eligible=False,
            duplicate_or_obsolete_candidate=True,
        ),
    ]


def _new_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    recommended = {
        "serve_return_match_stats": ["player_service_points_won_pct", "player_return_points_won_pct", "serve_return_edge"],
        "break_hold_derivations": ["player_hold_rate", "player_break_rate", "opponent_hold_rate", "opponent_break_rate"],
        "ranking_snapshot_history": ["ranking_delta_recent", "rank_points_delta_recent"],
        "recent_form_rest_fatigue": ["recent_match_minutes", "matches_last_7_days", "rest_days", "fatigue_proxy"],
        "head_to_head_context": ["h2h_win_rate", "h2h_surface_win_rate"],
        "retirement_walkover_context": ["retire_or_walkover_risk"],
        "grand_slam_best_of_context": ["best_of_five_flag", "grand_slam_main_draw_flag"],
        "point_by_point_charting_context": ["rally_length_profile", "serve_direction_preference", "return_position_proxy"],
        "player_metadata_handedness_country": ["country_code_normalized", "handedness_source"],
    }
    if lane["free_or_paid_category"] not in {"free_open_populated", "free_open_partial", "free_open_loader_needed", "free_open_sample_required"}:
        return []
    return recommended.get(lane["lane_name"], [])


def _lane_sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not sample_verification_results:
        return {}
    return dict(sample_verification_results.get("source_result_index") or {})


def default_tennis_loader_lanes() -> list[dict[str, Any]]:
    return [
        lane
        for lane in tennis_lane_catalog()
        if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_partial", "free_open_loader_needed", "free_open_sample_required"}
    ]


def build_tennis_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries: list[dict[str, Any]] = []
    for lane in tennis_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        records = int(sample.get("records_tested", 0) or 0)
        validation_status = str(sample.get("validation_status") or "")
        if validation_status == "sample_verified" and records > 0:
            population_status = "partial" if lane["free_or_paid_category"] != "free_open_populated" else "populated"
        elif lane["free_or_paid_category"] == "obsolete_or_duplicate":
            population_status = "obsolete_or_duplicate"
        elif lane["free_or_paid_category"] in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear", "policy_blocked", "robots_blocked", "terms_blocked", "login_paywall_captcha_blocked"}:
            population_status = "blocked"
        else:
            population_status = "manual_or_review_required"
        for field in lane["fields"]:
            entries.append(
                {
                    "sport": lane["sport"],
                    "tour": lane["tour"],
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
        "report_name": "TENNIS_ARCHITECTURE_INVENTORY",
        "schema_version": "tennis_architecture_inventory_v1",
        "created_at": current_utc(),
        "sport": "tennis",
        "tours_included": list(TOURS_INCLUDED),
        "inventory_entries": entries,
        "field_inventory_entries": entries,
        "fields_total": len(entries),
        "fields_populated_count": sum(1 for row in entries if row["current_population_status"] == "populated"),
        "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"),
        "fields_missing_count": sum(1 for row in entries if row["current_population_status"] not in {"populated", "partial"}),
        **_safety(),
    }


def write_tennis_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "TENNIS_ARCHITECTURE_INVENTORY.json"
    md_path = root / "TENNIS_ARCHITECTURE_INVENTORY.md"
    write_json(json_path, report)
    lines = [
        "# Tennis Architecture Inventory",
        "",
        f"1. sport: {report.get('sport')}",
        f"2. tours_included: {', '.join(report.get('tours_included') or [])}",
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


def build_tennis_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows: list[dict[str, Any]] = []
    for lane in tennis_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        rows.append(
            {
                "sport": lane["sport"],
                "tour": lane["tour"],
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
        "report_name": "TENNIS_FREE_VS_PAID_SOURCE_LEDGER",
        "schema_version": "tennis_free_vs_paid_source_ledger_v1",
        "created_at": current_utc(),
        "sport": "tennis",
        "tours_included": list(TOURS_INCLUDED),
        "source_ledger_rows": rows,
        "source_ledger_row_count": len(rows),
        "free_open_loader_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_loader_needed"),
        "free_open_sample_required_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_sample_required"),
        "free_open_manual_import_needed_count": sum(1 for row in rows if row["free_or_paid_category"] == "free_open_manual_import_needed"),
        "paid_data_subscription_required_count": sum(1 for row in rows if row["free_or_paid_category"] == "paid_data_subscription_required"),
        "license_terms_unclear_count": sum(1 for row in rows if row["free_or_paid_category"] == "license_terms_unclear"),
        **_safety(),
    }


def write_tennis_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "TENNIS_FREE_VS_PAID_SOURCE_LEDGER.json"
    md_path = root / "TENNIS_FREE_VS_PAID_SOURCE_LEDGER.md"
    write_json(json_path, report)
    lines = [
        "# Tennis Free vs Paid Source Ledger",
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
