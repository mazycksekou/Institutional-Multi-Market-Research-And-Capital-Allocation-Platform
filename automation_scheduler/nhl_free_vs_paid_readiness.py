from __future__ import annotations

from pathlib import Path
from typing import Any

from .nhl_oxylabs_common import current_utc, lane_source_spec, url_hash, write_json, write_md


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"
RUN_MODE = "nhl_final_mandatory_oxylabs_free_open_exhaustion_backfill_finality"

FREE_VS_PAID_CATEGORIES = (
    "free_open_populated",
    "free_open_partial",
    "free_open_sample_required",
    "free_open_loader_needed",
    "free_open_manual_import_needed",
    "user_approved_paid_transport_needed",
    "paid_data_subscription_required",
    "policy_blocked",
    "license_terms_unclear",
    "blocked_reference_or_restricted_source",
    "unavailable_after_max_effort",
    "obsolete_or_duplicate",
    "needs_manual_review",
)

GAP_ACTIONS = (
    "sample_verify_one_game",
    "sample_verify_one_team",
    "sample_verify_one_player",
    "sample_verify_one_goalie",
    "implement_loader",
    "backfill_approved_scope",
    "backfill_approved_seasons",
    "create_manual_import_template",
    "mark_paid_subscription_required",
    "mark_policy_blocked",
    "mark_license_terms_unclear",
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
    "AllowSchemaExpansion": True,
    "AllowSampleVerification": True,
    "AllowOneSeasonValidation": True,
    "AllowFreeVsPaidAudit": True,
    "AllowCalibrationReadinessAudit": True,
    "AllowBackfill": True,
    "AllowOxylabsAudit": True,
    "AllowFinalityAudit": True,
}

SPORTS = {
    "icehockey_nhl": {
        "display_name": "NHL",
        "module": "icehockey_nhl",
        "model": "poisson_bivariate_goalie_special_teams_model",
        "readiness_recommendation": "ready_but_paid_data_would_improve",
    }
}


def _safety() -> dict[str, Any]:
    return dict(SAFETY_FLAGS)


def _lane(
    lane_name: str,
    field_group: str,
    *,
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
    future_leakage_risk: str = "low_if_joined_by_game_start",
    model_eligible: bool | None = None,
    duplicate_or_obsolete_candidate: bool = False,
    coverage_start: str = "official_public_current_sample_scope",
    coverage_end: str = "official_public_current_sample_scope",
    loader_exists: bool = True,
    manual_template_required: bool = False,
    manual_import_possible: bool = True,
    paid_priority: str | None = None,
) -> dict[str, Any]:
    if category not in FREE_VS_PAID_CATEGORIES:
        raise ValueError(f"Unsupported NHL free-vs-paid category: {category}")
    if next_action not in GAP_ACTIONS:
        raise ValueError(f"Unsupported NHL action: {next_action}")
    source = lane_source_spec({"lane_name": lane_name, "free_or_paid_category": category})
    return {
        "sport": "icehockey_nhl",
        "sport_name": "NHL",
        "module": "icehockey_nhl",
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
        "sample_required": bool(category in {"free_open_populated", "free_open_partial", "free_open_loader_needed", "free_open_sample_required"}),
        "sample_attempted": False,
        "loader_exists": bool(loader_exists),
        "manual_template_exists": bool(manual_template_required or category in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear"}),
        "manual_template_required": bool(manual_template_required),
        "policy_status": source.policy_status,
        "license_or_terms_note": source.license_or_terms_note,
        "cutoff_safe": bool(cutoff_safe),
        "future_leakage_risk": future_leakage_risk,
        "model_eligible": bool(category in {"free_open_populated", "free_open_partial"} and cutoff_safe) if model_eligible is None else bool(model_eligible),
        "calibration_impact": calibration_impact,
        "next_action": next_action,
        "final_reason": final_reason,
        "duplicate_or_obsolete_candidate": duplicate_or_obsolete_candidate,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "manual_import_possible": bool(manual_import_possible),
        "paid_priority": paid_priority,
    }


def nhl_lane_catalog() -> list[dict[str, Any]]:
    return [
        _lane(
            "schedule_results",
            "schedule/results",
            entity_level="game",
            fields=["game_id", "season", "game_date", "start_time_utc", "home_team_id", "home_team_abbrev", "away_team_id", "away_team_abbrev", "home_score", "away_score", "game_state", "venue_name", "venue_timezone"],
            table="nhl_games",
            source_id="nhl_official_api",
            source_family="official_nhl_schedule_api",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="anchors stable event identity, final scores, dates, venue context, and downstream label joins",
            next_action="backfill_approved_scope",
            final_reason="Official NHL public schedule payload exposes stable identifiers, timestamps, teams, scores, and venue metadata.",
        ),
        _lane(
            "team_box_scores",
            "team box scores",
            entity_level="team_game",
            fields=["game_id", "team_id", "team_abbrev", "team_score", "shots_on_goal"],
            table="nhl_team_box_scores",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_boxscore",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports core team-level scoring, shot volume, and game-total context",
            next_action="backfill_approved_scope",
            final_reason="Official Gamecenter boxscore payload contains direct team-game score and shot totals.",
        ),
        _lane(
            "player_box_scores",
            "player box scores",
            entity_level="player_game",
            fields=["game_id", "player_id", "team_id", "position", "goals", "assists", "points", "shots_on_goal", "time_on_ice"],
            table="nhl_player_box_scores",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_boxscore",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports player-prop proxies, player usage, and scoring involvement context",
            next_action="backfill_approved_scope",
            final_reason="Official Gamecenter boxscore payload contains structured skater game statistics.",
        ),
        _lane(
            "goalie_box_scores",
            "goalie box scores",
            entity_level="goalie_game",
            fields=["game_id", "player_id", "team_id", "starter", "decision", "save_pct", "shots_against", "saves", "goals_against", "time_on_ice"],
            table="nhl_goalie_box_scores",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_boxscore",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports goalie adjustment quality, save-rate context, and goalie decision history",
            next_action="backfill_approved_scope",
            final_reason="Official Gamecenter boxscore payload contains structured goalie game statistics including starter flags and save percentage.",
        ),
        _lane(
            "play_by_play",
            "play-by-play",
            entity_level="play",
            fields=["game_id", "event_id", "period_number", "time_in_period", "time_remaining", "type_desc_key", "situation_code", "event_owner_team_id"],
            table="nhl_play_by_play",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_play_by_play",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports event-level tempo, first-period context, penalty context, and shot-location derivations",
            next_action="backfill_approved_scope",
            final_reason="Official Gamecenter play-by-play payload contains event-by-event structured logs.",
        ),
        _lane(
            "shot_events",
            "shot events and shot-quality proxies",
            entity_level="shot",
            fields=["game_id", "event_id", "shooting_player_id", "goalie_in_net_id", "x_coord", "y_coord", "shot_type", "zone_code", "shot_quality_proxy"],
            table="nhl_shot_events",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_play_by_play",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="improves shot-quality proxy coverage when a fully approved public xG feed is unavailable",
            next_action="backfill_approved_scope",
            final_reason="Shot events are directly exposed in official play-by-play details with coordinates and shot types.",
        ),
        _lane(
            "penalty_events",
            "penalty events",
            entity_level="penalty_event",
            fields=["game_id", "event_id", "committed_by_player_id", "drawn_by_player_id", "penalty_type_code", "penalty_desc_key", "duration", "zone_code"],
            table="nhl_penalty_events",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_play_by_play",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports special-teams context, penalty environment proxies, and first-period volatility checks",
            next_action="backfill_approved_scope",
            final_reason="Official play-by-play details expose committed penalties, drawn penalties, duration, and zone context.",
        ),
        _lane(
            "power_play_penalty_kill_stats",
            "power-play / penalty-kill form",
            entity_level="team_season",
            fields=["team_id", "season", "power_play_goals", "shots", "power_play_recent_rate", "penalty_kill_recent_rate", "special_teams_form"],
            table="nhl_special_teams_context",
            source_id="nhl_official_api",
            source_family="official_nhl_club_stats_and_gamecenter",
            category="free_open_partial",
            current_status="official_public_api_partial_loader_ready",
            calibration_impact="supports special_teams_adjustment_applied with proxy-quality team form instead of a fully approved historical percentage feed",
            next_action="backfill_approved_scope",
            final_reason="Official club stats plus gamecenter events support special-teams proxies, but the approved free/open path is still proxy-quality rather than a full historical rate warehouse.",
        ),
        _lane(
            "goalie_starts",
            "goalie starts",
            entity_level="goalie_game",
            fields=["game_id", "team_id", "goalie_player_id", "goalie_start_confirmed", "goalie_name", "backup_goalie_flag"],
            table="nhl_goalie_starts",
            source_id="nhl_official_api",
            source_family="official_nhl_gamecenter_boxscore",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="material for goalie-adjustment readiness and confirmed-starter confidence capping",
            next_action="backfill_approved_scope",
            final_reason="Official Gamecenter goalie entries expose starter flags and backup context.",
        ),
        _lane(
            "goalie_workload_rest",
            "goalie workload and rest",
            entity_level="goalie_game",
            fields=["game_id", "team_id", "goalie_player_id", "goalie_rest_days", "goalie_recent_games_started", "goalie_recent_save_pct", "backup_goalie_flag"],
            table="nhl_goalie_workload_context",
            source_id="nhl_official_api",
            source_family="official_nhl_schedule_and_club_stats",
            category="free_open_partial",
            current_status="official_public_api_partial_loader_ready",
            calibration_impact="improves goalie workload and fatigue awareness with public-game and club-stat proxies",
            next_action="backfill_approved_scope",
            final_reason="Official schedule history plus club goalie stats support usable workload/rest proxies, though not a full public GSAx-quality workload feed.",
        ),
        _lane(
            "rest_travel_features",
            "rest / travel / back-to-back features",
            entity_level="team_game",
            fields=["game_id", "team_id", "rest_days", "back_to_back_flag", "three_in_four_nights_flag", "rest_disadvantage", "travel_distance_estimate"],
            table="nhl_rest_travel_context",
            source_id="nhl_official_api",
            source_family="official_nhl_schedule_api",
            category="free_open_partial",
            current_status="derived_from_verified_schedule",
            calibration_impact="supports fatigue-sensitive team markets and first-period volatility assessment",
            next_action="backfill_approved_scope",
            final_reason="Official dated schedules are sufficient for rest windows and back-to-back flags; travel distance remains an explicit estimate.",
        ),
        _lane(
            "venue_rink_timezone_features",
            "venue / rink / timezone context",
            entity_level="game",
            fields=["game_id", "venue_name", "venue_location", "venue_timezone", "venue_utc_offset", "rink_home_ice_context"],
            table="nhl_venue_context",
            source_id="nhl_official_api",
            source_family="official_nhl_schedule_api",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports rink-context, timezone joins, and travel-aware model modifiers",
            next_action="backfill_approved_scope",
            final_reason="Official schedule payload exposes venue name, location, timezone, and offset fields.",
        ),
        _lane(
            "roster_records",
            "roster records",
            entity_level="player_team",
            fields=["team_id", "player_id", "position_code", "sweater_number", "shoots_catches", "roster_continuity"],
            table="nhl_rosters",
            source_id="nhl_official_api",
            source_family="official_nhl_roster_api",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports roster continuity, position context, and player-availability joins",
            next_action="backfill_approved_scope",
            final_reason="Official roster endpoint exposes current team rosters with player identifiers, positions, and handedness.",
        ),
        _lane(
            "overtime_shootout_context",
            "overtime / shootout context",
            entity_level="game",
            fields=["game_id", "game_outcome_last_period_type", "ot_in_use", "shootout_in_use", "overtime_experience", "shootout_context"],
            table="nhl_overtime_shootout_context",
            source_id="nhl_official_api",
            source_family="official_nhl_schedule_and_landing",
            category="free_open_populated",
            current_status="official_public_api_loader_ready",
            calibration_impact="supports three-way/regulation market context and overtime/shootout aware diagnostics",
            next_action="backfill_approved_scope",
            final_reason="Official schedule and landing payloads expose overtime and shootout outcome indicators.",
        ),
        _lane(
            "first_period_scoring_context",
            "first-period scoring context",
            entity_level="game",
            fields=["game_id", "first_period_goals_total", "first_period_shots_total", "first_period_scoring_tendency"],
            table="nhl_first_period_context",
            source_id="nhl_official_api",
            source_family="official_nhl_play_by_play",
            category="free_open_populated",
            current_status="derived_from_verified_play_by_play",
            calibration_impact="directly supports first-period total and first-period moneyline readiness",
            next_action="backfill_approved_scope",
            final_reason="Official play-by-play provides enough event timing to derive first-period scoring and shot totals.",
        ),
        _lane(
            "team_totals_context",
            "team totals context",
            entity_level="team_game",
            fields=["game_id", "team_id", "team_goals", "total_goals", "special_teams_goals_for", "first_period_goals_for"],
            table="nhl_team_totals_context",
            source_id="nhl_official_api",
            source_family="official_nhl_boxscore_and_play_by_play",
            category="free_open_populated",
            current_status="derived_from_verified_official_api",
            calibration_impact="supports team totals, game totals, and team-goal distribution features",
            next_action="backfill_approved_scope",
            final_reason="Official gamecenter boxscore and play-by-play are sufficient to derive team-total context features.",
        ),
        _lane(
            "player_prop_feature_candidates",
            "player prop feature candidates",
            entity_level="player_game",
            fields=["game_id", "player_id", "shots_on_goal_rate_proxy", "point_rate_proxy", "power_play_goal_count", "blocked_shots", "player_prop_feature_quality"],
            table="nhl_player_prop_context",
            source_id="nhl_official_api",
            source_family="official_nhl_boxscore_and_play_by_play",
            category="free_open_partial",
            current_status="official_public_api_partial_loader_ready",
            calibration_impact="supports shots/points/blocked-shots proxy readiness while injuries, line combinations, and public xG remain weaker",
            next_action="backfill_approved_scope",
            final_reason="Official player-game and event data support solid player-prop proxies, but line-combination and injury certainty remain incomplete.",
        ),
        _lane(
            "injuries_availability",
            "injuries / availability",
            entity_level="player_game",
            fields=["player_id", "injury_status", "availability_status", "injury_volatility", "source_snapshot_date"],
            table="nhl_injuries_availability",
            source_id="nhl_team_roster_page",
            source_family="official_team_public_pages_manual_review",
            category="free_open_manual_import_needed",
            current_status="manual_template_ready",
            calibration_impact="important for player props, goalie confidence, and late-scratch volatility, but still fragmented in the public free/open path",
            next_action="create_manual_import_template",
            final_reason="Public team and league pages can support manual availability snapshots, but no policy-safe standardized automated historical injury feed was validated in this pass.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_timestamped_pregame_snapshot",
            model_eligible=False,
        ),
        _lane(
            "officials_referee_assignments",
            "officials / referee assignments",
            entity_level="official_game",
            fields=["game_id", "official_name", "official_role", "referee_crew_id", "referee_penalty_tendency_candidate"],
            table="nhl_official_assignments",
            source_id="nhl_official_reports_page",
            source_family="official_nhl_reports_manual_review",
            category="free_open_manual_import_needed",
            current_status="manual_template_ready",
            calibration_impact="moderate for penalty-environment context after enough historical samples, but still manual in this pass",
            next_action="create_manual_import_template",
            final_reason="Public NHL reports and team pages may contain officials context, but a clean policy-safe structured automated path was not validated here.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_timestamped_game_report_snapshot",
            model_eligible=False,
        ),
        _lane(
            "lineup_line_combinations",
            "line combinations / defensive pairings",
            entity_level="line_pair",
            fields=["line_combination_stability", "defense_pairing_stability", "confirmed_lines_source"],
            table="nhl_line_combination_context",
            source_id="nhl_natural_stat_trick_home",
            source_family="public_line_combination_pages_terms_review",
            category="license_terms_unclear",
            current_status="terms_review_required",
            calibration_impact="high for player props and line-driven matchup context, but exact public automated path remains unconfirmed",
            next_action="mark_license_terms_unclear",
            final_reason="Public line-combination sources exist, but the exact policy-safe automated path was not confirmed conservatively in this pass.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_timestamped_confirmation",
            model_eligible=False,
        ),
        _lane(
            "public_expected_goals_dataset",
            "public expected-goals / shot-quality sources",
            entity_level="team_game",
            fields=["xg_source_status", "shot_quality_source_name", "expected_goals_for_proxy", "expected_goals_against_proxy"],
            table="nhl_public_xg_context",
            source_id="nhl_natural_stat_trick_home",
            source_family="public_xg_pages_terms_review",
            category="license_terms_unclear",
            current_status="terms_review_required",
            calibration_impact="high for shot-quality and goalie-quality calibration, but exact public automated retrieval remains unclear",
            next_action="mark_license_terms_unclear",
            final_reason="Useful public xG-style sources appear to exist, but the exact allowed automated data path was not safely confirmed in this pass.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_snapshot_and_terms_review",
            model_eligible=False,
        ),
        _lane(
            "goalie_gsaax_dataset",
            "goalie GSAx / licensed advanced goalie feeds",
            entity_level="goalie_season",
            fields=["goalie_recent_goals_saved_above_expected_proxy", "goalie_gsaax_source_status"],
            table="nhl_goalie_advanced_context",
            source_id="nhl_paid_vendor_page",
            source_family="licensed_nhl_advanced_goalie_feed",
            category="paid_data_subscription_required",
            current_status="paid_classified_no_free_safe_feed",
            calibration_impact="high for goalie adjustment quality, especially when confirmed starter quality is the main edge lever",
            next_action="mark_paid_subscription_required",
            final_reason="No compliant free/open structured public GSAx feed was validated; a licensed vendor or paid advanced feed is still required.",
            loader_exists=False,
            manual_template_required=True,
            paid_priority="high",
            model_eligible=False,
        ),
        _lane(
            "restricted_reference_tables",
            "Hockey Reference / restricted reference tables",
            entity_level="game_player_team",
            fields=["reference_duplicate_box_score", "reference_duplicate_goalie_table"],
            table="nhl_blocked_reference_sources",
            source_id="nhl_official_reports_page",
            source_family="blocked_reference_or_restricted_source",
            category="blocked_reference_or_restricted_source",
            current_status="hard_policy_blocked",
            calibration_impact="not needed once official public API and Gamecenter free lanes are normalized",
            next_action="mark_policy_blocked",
            final_reason="Hockey Reference and Sports Reference scraping are explicitly blocked in this pass.",
            loader_exists=False,
            manual_import_possible=False,
            cutoff_safe=False,
            future_leakage_risk="policy_blocked",
            model_eligible=False,
        ),
        _lane(
            "community_open_mirror_datasets",
            "community open mirror datasets",
            entity_level="game_player_team",
            fields=["mirror_schedule_duplicate", "mirror_boxscore_duplicate"],
            table="nhl_duplicate_source_registry",
            source_id="nhl_github_open_docs",
            source_family="github_open_mirror_sources",
            category="obsolete_or_duplicate",
            current_status="duplicate_not_pursued",
            calibration_impact="low because the official public API already covers the same core surfaces with better provenance",
            next_action="mark_obsolete_or_duplicate",
            final_reason="Community open mirrors are redundant once the official public NHL API and Gamecenter paths are normalized.",
            loader_exists=False,
            model_eligible=False,
            duplicate_or_obsolete_candidate=True,
        ),
    ]


def _lane_sample_index(sample_verification_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not sample_verification_results:
        return {}
    return dict(sample_verification_results.get("source_result_index") or {})


def _new_fields_for_lane(lane: dict[str, Any]) -> list[str]:
    recommended = {
        "shot_events": ["shot_quality_proxy"],
        "power_play_penalty_kill_stats": ["power_play_recent_rate", "penalty_kill_recent_rate", "special_teams_form"],
        "goalie_starts": ["goalie_start_confirmed", "backup_goalie_flag"],
        "goalie_workload_rest": ["goalie_rest_days", "goalie_recent_save_pct"],
        "rest_travel_features": ["rest_disadvantage", "back_to_back_flag", "three_in_four_nights_flag", "travel_distance_estimate"],
        "venue_rink_timezone_features": ["rink_home_ice_context", "venue_altitude_or_timezone_context"],
        "roster_records": ["roster_continuity"],
        "overtime_shootout_context": ["overtime_experience", "shootout_context"],
        "first_period_scoring_context": ["first_period_scoring_tendency"],
        "player_prop_feature_candidates": ["shots_on_goal_rate_proxy", "point_rate_proxy", "player_prop_feature_quality"],
    }
    if lane["free_or_paid_category"] not in {"free_open_populated", "free_open_partial"}:
        return []
    return recommended.get(lane["lane_name"], [])


def build_nhl_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries: list[dict[str, Any]] = []
    for lane in nhl_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        records = int(sample.get("records_tested", 0) or 0)
        if lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"} and records > 0:
            population_status = "populated" if lane["free_or_paid_category"] == "free_open_populated" else "partial"
        elif lane["free_or_paid_category"] == "obsolete_or_duplicate":
            population_status = "obsolete_or_duplicate"
        elif lane["free_or_paid_category"] in {"free_open_manual_import_needed", "paid_data_subscription_required", "license_terms_unclear", "blocked_reference_or_restricted_source"}:
            population_status = "blocked"
        else:
            population_status = "manual_or_review_required"
        for field in lane["fields"]:
            entries.append(
                {
                    "sport": lane["sport"],
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
        "report_name": "NHL_ARCHITECTURE_INVENTORY",
        "schema_version": "nhl_architecture_inventory_v1",
        "created_at": current_utc(),
        "sports_included": ["icehockey_nhl"],
        "inventory_entries": entries,
        "field_inventory_entries": entries,
        "fields_total": len(entries),
        "fields_populated_count": sum(1 for row in entries if row["current_population_status"] == "populated"),
        "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"),
        "fields_missing_count": sum(1 for row in entries if row["current_population_status"] not in {"populated", "partial"}),
        **_safety(),
    }


def build_nhl_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows: list[dict[str, Any]] = []
    for lane in nhl_lane_catalog():
        sample = sample_index.get(f"{lane['sport']}::{lane['lane_name']}", {})
        rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane["field_or_feature_group"],
                "entity_level": lane["entity_level"],
                "current_status": lane["current_status"],
                "current_record_count": int(sample.get("records_tested", 0) or 0),
                "source_family": lane["source_family"],
                "candidate_source_name": lane["candidate_source_name"],
                "source_type": lane["source_type"],
                "free_or_paid_category": lane["free_or_paid_category"],
                "retrieval_method": lane["retrieval_method"],
                "sample_required": bool(lane["sample_required"]),
                "sample_attempted": bool(sample.get("sample_attempted", False)),
                "loader_exists": bool(lane["loader_exists"]),
                "manual_template_exists": bool(lane["manual_template_exists"]),
                "policy_status": lane["policy_status"],
                "license_or_terms_note": lane["license_or_terms_note"],
                "cutoff_safe": lane["cutoff_safe"],
                "future_leakage_risk": lane["future_leakage_risk"],
                "model_eligible": lane["model_eligible"],
                "calibration_impact": lane["calibration_impact"],
                "next_action": lane["next_action"],
                "final_reason": lane["final_reason"],
            }
        )
    category_counts = {category: sum(1 for row in rows if row["free_or_paid_category"] == category) for category in FREE_VS_PAID_CATEGORIES}
    return {
        "ok": True,
        "status": "ok",
        "report_name": "NHL_FREE_VS_PAID_SOURCE_LEDGER",
        "schema_version": "nhl_free_vs_paid_source_ledger_v1",
        "created_at": current_utc(),
        "source_ledger_rows": rows,
        "ledger_rows": rows,
        "summary": {
            "source_count": len(rows),
            **category_counts,
            "sample_attempted_count": sum(1 for row in rows if row["sample_attempted"]),
            "manual_template_count": sum(1 for row in rows if row["manual_template_exists"]),
            "loader_ready_count": sum(1 for row in rows if row["loader_exists"] and row["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}),
        },
        **category_counts,
        **_safety(),
    }


def write_nhl_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_ARCHITECTURE_INVENTORY.json"
    md_path = root / "NHL_ARCHITECTURE_INVENTORY.md"
    write_json(json_path, report)
    lines = [
        "# NHL Architecture Inventory",
        "",
        f"1. fields_total: {report.get('fields_total')}",
        f"2. fields_populated_count: {report.get('fields_populated_count')}",
        f"3. fields_partial_count: {report.get('fields_partial_count')}",
        f"4. fields_missing_count: {report.get('fields_missing_count')}",
        "",
        "## Fields",
    ]
    for row in report.get("inventory_entries") or []:
        lines.append(
            f"- {row.get('lane_name')}::{row.get('field_name')} status={row.get('current_population_status')} source={row.get('source_family')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def write_nhl_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "NHL_FREE_VS_PAID_SOURCE_LEDGER.json"
    md_path = root / "NHL_FREE_VS_PAID_SOURCE_LEDGER.md"
    write_json(json_path, report)
    lines = [
        "# NHL Free vs Paid Source Ledger",
        "",
        f"1. source_count: {report.get('summary', {}).get('source_count')}",
        f"2. loader_ready_count: {report.get('summary', {}).get('loader_ready_count')}",
        f"3. manual_template_count: {report.get('summary', {}).get('manual_template_count')}",
        "",
        "## Lanes",
    ]
    for row in report.get("source_ledger_rows") or []:
        lines.append(
            f"- {row.get('lane_name')} category={row.get('free_or_paid_category')} loader={row.get('loader_exists')} next_action={row.get('next_action')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}
