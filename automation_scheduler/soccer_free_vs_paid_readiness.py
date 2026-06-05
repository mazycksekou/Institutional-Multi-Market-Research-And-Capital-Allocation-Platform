from __future__ import annotations

from pathlib import Path
from typing import Any

from .soccer_oxylabs_common import current_utc, lane_source_spec, url_hash, write_json, write_md


REPORT_ROOT = Path("reports")
MANUAL_TEMPLATE_ROOT = Path("data") / "manual_import_templates"
RUN_MODE = "soccer_final_mandatory_oxylabs_free_open_exhaustion_backfill_finality"

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
    "sample_verify_one_match",
    "sample_verify_one_team",
    "sample_verify_one_player",
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
    "soccer": {
        "display_name": "Soccer",
        "module": "soccer",
        "model": "poisson_dixon_coles_bivariate_goal_model",
        "readiness_recommendation": "manual_import_needed",
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
    future_leakage_risk: str = "low_if_joined_pregame_or_historical",
    model_eligible: bool | None = None,
    duplicate_or_obsolete_candidate: bool = False,
    coverage_start: str = "bundesliga_2023_2024_sample_scope",
    coverage_end: str = "bundesliga_2023_2024_sample_scope",
    loader_exists: bool = True,
    manual_template_required: bool = False,
    manual_import_possible: bool = True,
    paid_priority: str | None = None,
) -> dict[str, Any]:
    if category not in FREE_VS_PAID_CATEGORIES:
        raise ValueError(f"Unsupported Soccer free-vs-paid category: {category}")
    if next_action not in GAP_ACTIONS:
        raise ValueError(f"Unsupported Soccer action: {next_action}")
    source = lane_source_spec({"lane_name": lane_name, "source_id": source_id, "free_or_paid_category": category})
    return {
        "sport": "soccer",
        "sport_name": "Soccer",
        "module": "soccer",
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


def soccer_lane_catalog() -> list[dict[str, Any]]:
    return [
        _lane(
            "schedule_results",
            "fixtures and final results",
            entity_level="match",
            fields=["division", "season", "match_date", "kickoff_local", "home_team", "away_team", "home_goals", "away_goals", "result_code", "stable_match_key"],
            table="soccer_matches",
            source_id="soccer_football_data_csv",
            source_family="football_data_open_csv",
            category="free_open_populated",
            current_status="open_csv_loader_ready",
            calibration_impact="anchors event identity, home/away context, and settled outcomes for three-way, draw-no-bet, and totals calibration.",
            next_action="backfill_approved_scope",
            final_reason="Bundesliga historical public CSV exposes stable match identity, teams, dates, kickoff time, and full-time results.",
        ),
        _lane(
            "first_half_scoring_context",
            "first-half goals and result context",
            entity_level="match",
            fields=["stable_match_key", "home_first_half_goals", "away_first_half_goals", "first_half_result_code", "first_half_total_goals"],
            table="soccer_first_half_context",
            source_id="soccer_football_data_csv",
            source_family="football_data_open_csv",
            category="free_open_populated",
            current_status="open_csv_loader_ready",
            calibration_impact="supports first-half totals and first-half scoring-rate calibration.",
            next_action="backfill_approved_scope",
            final_reason="The same public CSV exposes halftime goal and result fields suitable for normalized first-half context.",
        ),
        _lane(
            "shots_corners_cards_context",
            "shots, corners, cards, and fouls",
            entity_level="match",
            fields=["stable_match_key", "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target", "home_corners", "away_corners", "home_yellow_cards", "away_yellow_cards", "home_red_cards", "away_red_cards"],
            table="soccer_match_stats_context",
            source_id="soccer_football_data_csv",
            source_family="football_data_open_csv",
            category="free_open_partial",
            current_status="open_csv_partial_loader_ready",
            calibration_impact="supports totals, BTTS, correct-score, corners, and cards context while possession and richer tactical telemetry remain weaker.",
            next_action="backfill_approved_scope",
            final_reason="Public CSV match stats cover shots, shots on target, corners, cards, and fouls, but not full possession-value coverage.",
        ),
        _lane(
            "referee_history_context",
            "historical referee context",
            entity_level="match",
            fields=["stable_match_key", "referee_name", "home_fouls", "away_fouls", "referee_total_cards", "referee_card_tendency_candidate"],
            table="soccer_referee_history",
            source_id="soccer_football_data_csv",
            source_family="football_data_open_csv",
            category="free_open_partial",
            current_status="open_csv_partial_loader_ready",
            calibration_impact="supports historical officiating proxies for cards and match control, while future assignments remain unresolved.",
            next_action="backfill_approved_scope",
            final_reason="Public CSV rows include referee names and foul/card context suitable for historical referee proxy features.",
        ),
        _lane(
            "statsbomb_match_metadata",
            "StatsBomb match metadata",
            entity_level="match",
            fields=["match_id", "match_date", "home_team_name", "away_team_name", "competition_stage", "stadium_name", "stadium_country", "referee_name", "home_manager_name", "away_manager_name"],
            table="soccer_statsbomb_matches",
            source_id="soccer_statsbomb_open_data",
            source_family="statsbomb_open_data_github",
            category="free_open_partial",
            current_status="open_json_partial_loader_ready",
            calibration_impact="improves stadium, manager, referee, and competition-stage context where open coverage exists.",
            next_action="backfill_approved_scope",
            final_reason="StatsBomb open-data match files expose structured metadata, but only for limited competition-season coverage.",
        ),
        _lane(
            "statsbomb_event_xg_shots",
            "StatsBomb event xG and shot context",
            entity_level="event",
            fields=["match_id", "event_id", "team_name", "player_name", "period", "minute", "shot_xg", "shot_outcome", "shot_body_part", "play_pattern", "possession_team_name"],
            table="soccer_statsbomb_events",
            source_id="soccer_statsbomb_open_data",
            source_family="statsbomb_open_data_github",
            category="free_open_partial",
            current_status="open_json_partial_loader_ready",
            calibration_impact="provides validated public xG and shot-event context for partial competitions, directly improving goal-distribution calibration.",
            next_action="backfill_approved_scope",
            final_reason="StatsBomb open-data event files expose structured shot events with xG for public sample competitions, but not full broad-league coverage.",
        ),
        _lane(
            "statsbomb_lineups_minutes",
            "StatsBomb lineups and minutes",
            entity_level="player_match",
            fields=["match_id", "team_name", "player_name", "jersey_number", "position_name", "starting_xi_flag", "minutes_played", "lineup_continuity"],
            table="soccer_statsbomb_lineups",
            source_id="soccer_statsbomb_open_data",
            source_family="statsbomb_open_data_github",
            category="free_open_partial",
            current_status="open_json_partial_loader_ready",
            calibration_impact="supports player-prop candidate quality, lineup continuity, and role/minutes stability in covered competitions.",
            next_action="backfill_approved_scope",
            final_reason="StatsBomb open-data lineups expose structured player positions and minute spans, but only for limited public competitions.",
        ),
        _lane(
            "team_strength_ratings",
            "derived team strength and form ratings",
            entity_level="team_season",
            fields=["team_name", "matches_played", "points_per_match", "goal_diff_per_match", "attack_strength", "defense_strength", "team_form_rating"],
            table="soccer_team_strength_context",
            source_id="soccer_football_data_csv",
            source_family="football_data_open_csv",
            category="free_open_populated",
            current_status="derived_from_verified_public_csv",
            calibration_impact="supports Poisson/Dixon-Coles team-strength priors and stronger market anchoring without depending on a third-party paid feed.",
            next_action="backfill_approved_scope",
            final_reason="Public historical results and scoring data are sufficient to derive team form, attack strength, and defense strength safely.",
        ),
        _lane(
            "rest_travel_fixture_congestion",
            "rest and fixture congestion context",
            entity_level="team_match",
            fields=["stable_match_key", "team_name", "rest_days", "fixture_congestion_score", "home_or_away", "travel_distance_estimate"],
            table="soccer_rest_travel_context",
            source_id="soccer_football_data_csv",
            source_family="football_data_open_csv",
            category="free_open_partial",
            current_status="derived_from_verified_public_csv",
            calibration_impact="supports fatigue-sensitive pricing for moneyline, totals, team totals, and BTTS while travel remains an explicit estimate.",
            next_action="backfill_approved_scope",
            final_reason="Public dated fixtures are enough to derive rest windows and congestion scores; travel distance is approximated conservatively.",
        ),
        _lane(
            "competition_context",
            "competition and stage context",
            entity_level="match",
            fields=["match_id", "competition_name", "season_name", "competition_stage", "regular_season_flag", "tournament_knockout_context"],
            table="soccer_competition_context",
            source_id="soccer_statsbomb_open_data",
            source_family="statsbomb_open_data_github",
            category="free_open_partial",
            current_status="open_json_partial_loader_ready",
            calibration_impact="supports tournament-vs-league context, draw incentives, and stage-aware priors in covered public competitions.",
            next_action="backfill_approved_scope",
            final_reason="StatsBomb match metadata exposes competition and stage context for public sample competitions.",
        ),
        _lane(
            "stadium_timezone_context",
            "stadium, timezone, and home-edge context",
            entity_level="match",
            fields=["match_id", "stadium_name", "stadium_country", "stadium_timezone_context", "home_advantage_context", "neutral_site_flag"],
            table="soccer_stadium_context",
            source_id="soccer_statsbomb_open_data",
            source_family="statsbomb_open_data_github",
            category="free_open_partial",
            current_status="open_json_partial_loader_ready",
            calibration_impact="supports home-field, neutral-site, and timezone-aware modifiers in covered competitions.",
            next_action="backfill_approved_scope",
            final_reason="Public match metadata exposes stadium names and countries, and timezone can be conservatively normalized from stadium country.",
        ),
        _lane(
            "player_prop_feature_candidates",
            "player prop feature candidates",
            entity_level="player_match",
            fields=["match_id", "player_name", "team_name", "minutes_played", "shot_count", "xg_total", "player_minutes_stability", "player_prop_data_status"],
            table="soccer_player_prop_context",
            source_id="soccer_statsbomb_open_data",
            source_family="statsbomb_open_data_github",
            category="free_open_partial",
            current_status="open_json_partial_loader_ready",
            calibration_impact="supports public player-prop candidate features where lineups and event data overlap, while injuries remain manual.",
            next_action="backfill_approved_scope",
            final_reason="Public lineups plus event data support player minutes and shot/xG candidate features for covered matches.",
        ),
        _lane(
            "injuries_availability",
            "injuries and availability snapshots",
            entity_level="player_match",
            fields=["team_name", "player_name", "availability_status", "source_snapshot_date", "injury_volatility"],
            table="soccer_injuries_availability",
            source_id="soccer_official_league_page",
            source_family="official_league_or_team_public_pages",
            category="free_open_manual_import_needed",
            current_status="manual_template_ready",
            calibration_impact="important for player props, team news, and late confidence capping, but no stable policy-safe automated historical public feed was validated.",
            next_action="create_manual_import_template",
            final_reason="Public official and team pages can support timestamped manual availability snapshots, but no standardized safe automated feed was validated here.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_timestamped_pregame_snapshot",
            model_eligible=False,
        ),
        _lane(
            "upcoming_referee_assignments",
            "upcoming referee assignments",
            entity_level="match",
            fields=["match_date", "home_team", "away_team", "referee_name", "assignment_source_snapshot_date"],
            table="soccer_referee_assignments",
            source_id="soccer_official_league_page",
            source_family="official_league_or_team_public_pages",
            category="free_open_manual_import_needed",
            current_status="manual_template_ready",
            calibration_impact="useful for cards and penalty environments, but future assignments remain safer as manual timestamped imports.",
            next_action="create_manual_import_template",
            final_reason="Official league public pages may publish referee assignments, but no stable structured automated path was validated in this pass.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_timestamped_assignment_snapshot",
            model_eligible=False,
        ),
        _lane(
            "broad_public_xg_mirror_coverage",
            "broader public xG mirror coverage",
            entity_level="team_match",
            fields=["xg_source_status", "coverage_scope", "source_name"],
            table="soccer_public_xg_context",
            source_id="soccer_understat_public_page",
            source_family="public_xg_mirror_pages_terms_review",
            category="license_terms_unclear",
            current_status="terms_review_required",
            calibration_impact="high for broader league-wide shot-quality coverage beyond current open StatsBomb scope.",
            next_action="mark_license_terms_unclear",
            final_reason="Useful public xG-style pages exist, but the exact automated path was not conservatively approved in this pass.",
            loader_exists=False,
            manual_template_required=True,
            future_leakage_risk="medium_requires_terms_review_and_timestamping",
            model_eligible=False,
        ),
        _lane(
            "tracking_360_context",
            "tracking and full 360 context",
            entity_level="player_match",
            fields=["tracking_available", "freeze_frame_density", "off_ball_runs", "pitch_control_proxy"],
            table="soccer_tracking_context",
            source_id="soccer_statsbomb_paid_vendor_page",
            source_family="paid_tracking_or_360_vendor",
            category="paid_data_subscription_required",
            current_status="paid_classified_no_free_broad_feed",
            calibration_impact="high for player props, pressing, spacing, and tactical context beyond limited public samples.",
            next_action="mark_paid_subscription_required",
            final_reason="Broad structured tracking and enriched 360 coverage remain paid/licensed beyond the limited public open-data sample.",
            loader_exists=False,
            manual_template_required=True,
            paid_priority="high",
            model_eligible=False,
        ),
        _lane(
            "restricted_reference_tables",
            "FBref and Sports Reference tables",
            entity_level="match_player_team",
            fields=["restricted_duplicate_stats"],
            table="soccer_restricted_reference_sources",
            source_id="soccer_fbref_blocked",
            source_family="blocked_reference_or_restricted_source",
            category="blocked_reference_or_restricted_source",
            current_status="hard_policy_blocked",
            calibration_impact="not needed once approved public CSV and open event data lanes are normalized.",
            next_action="mark_policy_blocked",
            final_reason="FBref and Sports Reference scraping are explicitly blocked in this pass.",
            loader_exists=False,
            manual_import_possible=False,
            cutoff_safe=False,
            future_leakage_risk="policy_blocked",
            model_eligible=False,
        ),
        _lane(
            "openfootball_historical_results_mirror",
            "openfootball historical results mirror",
            entity_level="match",
            fields=["duplicate_schedule_results"],
            table="soccer_duplicate_source_registry",
            source_id="soccer_openfootball_repo",
            source_family="github_open_results_mirror",
            category="obsolete_or_duplicate",
            current_status="duplicate_not_pursued",
            calibration_impact="low because football-data.co.uk already covers the selected historical result and stat lane with richer match columns.",
            next_action="mark_obsolete_or_duplicate",
            final_reason="OpenFootball remains a useful public backup, but it is redundant for this pass once football-data.co.uk is normalized.",
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
        "shots_corners_cards_context": ["first_half_goal_tendency", "btts_tendency", "clean_sheet_tendency"],
        "referee_history_context": ["referee_card_tendency_candidate"],
        "statsbomb_event_xg_shots": ["xg_source_status", "xg_for_recent", "xg_against_recent", "shots_for_recent", "shots_against_recent"],
        "statsbomb_lineups_minutes": ["lineup_continuity", "rotation_risk", "player_minutes_stability"],
        "team_strength_ratings": ["team_form_rating", "attack_strength", "defense_strength"],
        "rest_travel_fixture_congestion": ["rest_days", "fixture_congestion_score", "travel_distance_estimate"],
        "competition_context": ["tournament_knockout_context"],
        "stadium_timezone_context": ["stadium_timezone_context", "home_advantage_context", "neutral_site_flag"],
        "player_prop_feature_candidates": ["player_prop_data_status"],
    }
    if lane["free_or_paid_category"] not in {"free_open_populated", "free_open_partial"}:
        return []
    return recommended.get(lane["lane_name"], [])


def build_soccer_architecture_inventory(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    entries: list[dict[str, Any]] = []
    for lane in soccer_lane_catalog():
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
        "report_name": "SOCCER_ARCHITECTURE_INVENTORY",
        "schema_version": "soccer_architecture_inventory_v1",
        "created_at": current_utc(),
        "sports_included": ["soccer"],
        "inventory_entries": entries,
        "field_inventory_entries": entries,
        "fields_total": len(entries),
        "fields_populated_count": sum(1 for row in entries if row["current_population_status"] == "populated"),
        "fields_partial_count": sum(1 for row in entries if row["current_population_status"] == "partial"),
        "fields_missing_count": sum(1 for row in entries if row["current_population_status"] not in {"populated", "partial"}),
        **_safety(),
    }


def build_soccer_free_vs_paid_source_ledger(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    sample_index = _lane_sample_index(sample_verification_results)
    rows: list[dict[str, Any]] = []
    for lane in soccer_lane_catalog():
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
        "report_name": "SOCCER_FREE_VS_PAID_SOURCE_LEDGER",
        "schema_version": "soccer_free_vs_paid_source_ledger_v1",
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


def write_soccer_architecture_inventory(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "SOCCER_ARCHITECTURE_INVENTORY.json"
    md_path = root / "SOCCER_ARCHITECTURE_INVENTORY.md"
    write_json(json_path, report)
    lines = [
        "# Soccer Architecture Inventory",
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


def write_soccer_free_vs_paid_source_ledger(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    json_path = root / "SOCCER_FREE_VS_PAID_SOURCE_LEDGER.json"
    md_path = root / "SOCCER_FREE_VS_PAID_SOURCE_LEDGER.md"
    write_json(json_path, report)
    lines = [
        "# Soccer Free vs Paid Source Ledger",
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
