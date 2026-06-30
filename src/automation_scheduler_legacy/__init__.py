from __future__ import annotations

import json
from pathlib import Path

from src.data.data_paths import get_storage_health, resolve_base_data_dir
from .scheduler_runner import run_scheduler_once
from .system_health import get_system_health
from .review_queue import filter_review_items, list_active_review_items, load_review_queue_state, summarize_review_items
from src.services.scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .backtesting_engine import generate_backtest_report, run_backtest, run_paper_summary
from .calibration import build_calibration_report
from .outcome_store import ingest_outcome_records, load_outcome_records, load_outcome_state, summarize_outcomes
from .outcome_migration import import_local_settlement_records
from .model_performance_report import build_compact_performance_report
from .candlestick_pattern_detector import detect_candlestick_patterns
from .micro_outcome_calibration import build_micro_calibration_report
from .pattern_calibration import build_pattern_calibration_report
from .pattern_review_queue import load_pattern_review_queue
try:
    from .cross_asset_manifold_router import (
        get_manifold_calibration_snapshot,
        get_manifold_cluster_snapshot,
        get_manifold_trap_snapshot,
        map_manifold_endpoint_item,
        run_cross_asset_manifold_review,
    )
except ModuleNotFoundError:
    def get_manifold_calibration_snapshot(*, base_data_dir: str | None = None, limit: int = 25):
        return {
            "ok": True,
            "status": "disabled",
            "items": [],
            "sample_items": [],
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        }

    def get_manifold_cluster_snapshot(*, base_data_dir: str | None = None, limit: int = 25):
        return {
            "ok": True,
            "status": "disabled",
            "items": [],
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        }

    def get_manifold_trap_snapshot(*, base_data_dir: str | None = None, limit: int = 25):
        return {
            "ok": True,
            "status": "disabled",
            "items": [],
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        }

    def map_manifold_endpoint_item(
        item: dict | None = None,
        *,
        historical_records: list[dict] | None = None,
        base_data_dir: str | None = None,
    ):
        return {
            "ok": True,
            "status": "disabled",
            "item": item or {},
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        }

    def run_cross_asset_manifold_review(
        items: list[dict] | None,
        *,
        historical_records: list[dict] | None = None,
        persist: bool = True,
        base_data_dir: str | None = None,
        max_items: int = 250,
    ):
        return {
            "ok": True,
            "status": "disabled",
            "items_scanned": len([row for row in (items or []) if isinstance(row, dict)]),
            "items_mapped": 0,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        }

def build_security_readiness_report(*, base_data_dir: str | None = None):
    from src.services.security_readiness import build_security_readiness_report as _build_security_readiness_report

    return _build_security_readiness_report(base_data_dir=base_data_dir)


def _data_dir(base_data_dir: str | None = None) -> str:
    return str(resolve_base_data_dir(base_data_dir))


def run_small_account_pattern_detection(
    items: list[dict] | None = None,
    *,
    base_data_dir: str | None = None,
):
    from src.services.execution_service import SAFETY_FLAGS

    rows = [row for row in (items or []) if isinstance(row, dict)]
    detections = []
    for row in rows:
        context = {
            "asset_symbol": row.get("asset_symbol") or row.get("symbol") or row.get("ticker") or "UNKNOWN",
            "asset_type": row.get("asset_type") or "stock",
            "timeframe": row.get("timeframe") or "unknown",
            "detected_at": row.get("detected_at"),
            "vwap": row.get("vwap"),
            "opening_range_high": row.get("opening_range_high"),
            "previous_close": row.get("previous_close"),
            "pullback_high": row.get("pullback_high"),
            "prior_high": row.get("prior_high"),
            "breakout_confirmation_score": row.get("breakout_confirmation_score", 50.0),
        }
        detections.extend(detect_candlestick_patterns(row.get("candles") or [], context))
    return {
        "ok": True,
        "status": "patterns_detected",
        "items_scanned": len(rows),
        "detections_created": len(detections),
        "detections": detections,
        **SAFETY_FLAGS,
    }


def run_small_account_review_cycle(
    items: list[dict] | None = None,
    *,
    session_state: dict | None = None,
    persist_queue: bool = False,
    base_data_dir: str | None = None,
):
    from src.services.execution_service import run_small_account_review

    return run_small_account_review(
        items,
        session_state=session_state,
        persist_queue=persist_queue,
        base_data_dir=_data_dir(base_data_dir),
    )


def get_small_account_pattern_review_queue(base_data_dir: str | None = None, limit: int | None = None):
    return load_pattern_review_queue(base_data_dir=_data_dir(base_data_dir), limit=limit)


def get_small_account_pattern_calibration(records: list[dict] | None = None, base_data_dir: str | None = None):
    return build_pattern_calibration_report(records=records or [])


def get_small_account_micro_outcome_calibration(records: list[dict] | None = None, base_data_dir: str | None = None):
    return build_micro_calibration_report(records=records or [])


def get_broker_quality(base_data_dir: str | None = None):
    from src.services.execution_service import build_broker_quality_report

    return build_broker_quality_report()


def get_balance_sheet_risk(symbol: str, base_data_dir: str | None = None):
    from .balance_sheet_risk import evaluate_balance_sheet
    from src.services.execution_service import SAFETY_FLAGS

    base = resolve_base_data_dir(base_data_dir)
    sample_path = base / "small_account_review" / "balance_sheet_samples.json"
    samples = {}
    if sample_path.exists():
        try:
            payload = json.loads(sample_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                samples = payload
        except Exception:
            samples = {}
    key = str(symbol or "").upper()
    row = samples.get(key) if isinstance(samples, dict) else None
    result = evaluate_balance_sheet(row if isinstance(row, dict) else {})
    return {
        "ok": True,
        "status": "DATA_INSUFFICIENT" if result["data_insufficient"] else "ok",
        "symbol": key,
        "source": "local_sample" if isinstance(row, dict) else "local_sample_missing",
        "balance_sheet_risk": result,
        "storage_health": get_storage_health(),
        **SAFETY_FLAGS,
    }


def get_security_readiness(base_data_dir: str | None = None):
    return build_security_readiness_report(base_data_dir=_data_dir(base_data_dir))


def get_intelligence_readiness(base_data_dir: str | None = None):
    from .intelligence_readiness_report import build_intelligence_readiness_report

    return build_intelligence_readiness_report(base_data_dir=_data_dir(base_data_dir))


def get_data_intelligence_registry_snapshot(base_data_dir: str | None = None):
    from .data_intelligence_registry import build_data_intelligence_registry
    from .intelligence_readiness_report import _outcome_coverage

    base = _data_dir(base_data_dir)
    records = load_outcome_records(base)
    coverage = _outcome_coverage(records)
    coverage_values = {
        asset_type: payload.get("outcome_coverage", 0.0)
        for asset_type, payload in coverage.items()
        if isinstance(payload, dict)
    }
    return build_data_intelligence_registry(
        total_labeled_outcomes=len(records),
        outcome_coverage_by_asset_type=coverage_values,
    )


def get_model_maturity_registry_snapshot(base_data_dir: str | None = None):
    from .intelligence_readiness_report import _outcome_coverage
    from src.research import build_model_maturity_registry

    base = _data_dir(base_data_dir)
    records = load_outcome_records(base)
    coverage = _outcome_coverage(records)
    coverage_values = {
        asset_type: payload.get("outcome_coverage", 0.0)
        for asset_type, payload in coverage.items()
        if isinstance(payload, dict)
    }
    return build_model_maturity_registry(
        total_labeled_outcomes=len(records),
        outcome_coverage_by_asset_type=coverage_values,
    )


def build_cross_asset_representation_vector(item: dict | None = None):
    from .representation_feature_builder import build_representation_vector

    return build_representation_vector(item or {})


def map_market_state_graph(item: dict | None = None):
    from .graph_relationship_mapper import map_graph_relationships

    return map_graph_relationships(item or {})


def build_causal_effect_scaffold(records: list[dict] | None = None, hypotheses: list[dict] | None = None):
    from .causal_scaffold import build_causal_scaffold_report

    return build_causal_scaffold_report(records=records or [], hypotheses=hypotheses)


def get_tabular_ml_research_lanes(base_data_dir: str | None = None):
    from src.research import build_tabular_ml_research_lanes

    base = _data_dir(base_data_dir)
    records = load_outcome_records(base)
    label_coverage = min(1.0, len(records) / 1000.0)
    return build_tabular_ml_research_lanes(total_labeled_outcomes=len(records), label_coverage=label_coverage)


def get_deep_learning_research_lanes():
    from src.research import build_deep_learning_research_lanes

    return build_deep_learning_research_lanes()


def get_mdp_review_policy_scaffold(base_data_dir: str | None = None):
    from src.research import build_mdp_review_policy_scaffold

    base = _data_dir(base_data_dir)
    records = load_outcome_records(base)
    return build_mdp_review_policy_scaffold(current_sample_size=len(records))


def route_cross_asset_intelligence_item(
    item: dict | None = None,
    *,
    historical_records: list[dict] | None = None,
    base_data_dir: str | None = None,
):
    from .cross_asset_intelligence_router import route_cross_asset_intelligence
    from .intelligence_readiness_report import _outcome_coverage

    base = _data_dir(base_data_dir)
    records = load_outcome_records(base)
    coverage = _outcome_coverage(records)
    coverage_values = {
        asset_type: payload.get("outcome_coverage", 0.0)
        for asset_type, payload in coverage.items()
        if isinstance(payload, dict)
    }
    return route_cross_asset_intelligence(
        item or {},
        historical_records=historical_records,
        total_labeled_outcomes=len(records),
        outcome_coverage_by_asset_type=coverage_values,
        base_data_dir=base,
    )


def run_extreme_randomness_diagnostics(
    candidate: dict | None = None,
    *,
    baseline_values: list | None = None,
    matrix_payload: dict | None = None,
):
    from .extreme_randomness_diagnostics import diagnose_extreme_randomness

    return diagnose_extreme_randomness(candidate or {}, baseline_values=baseline_values, matrix_payload=matrix_payload)


def get_extreme_randomness_report(
    *,
    recent_events: list[dict] | None = None,
    base_data_dir: str | None = None,
):
    from .extreme_randomness_report import build_extreme_randomness_report

    return build_extreme_randomness_report(recent_events=recent_events or [], base_data_dir=_data_dir(base_data_dir))


def compare_random_baseline(candidate: dict | None = None, *, baseline_values: list | None = None):
    from .random_baseline_comparison import compare_to_random_baseline

    return compare_to_random_baseline(candidate or {}, baseline_values=baseline_values)


def classify_tail_event(candidate: dict | None = None):
    from .tail_event_classifier import classify_tail_event as _classify

    return _classify(candidate or {})


def evaluate_random_matrix_risk(payload: dict | None = None):
    from .random_matrix_risk import evaluate_random_matrix_risk as _evaluate

    return _evaluate(payload or {})


def evaluate_tracy_widom_research(payload: dict | None = None):
    from .tracy_widom_research import evaluate_tracy_widom_research as _evaluate

    return _evaluate(payload or {})


def get_universality_research_lane(events: list[dict] | None = None):
    from .universality_research_lanes import build_universality_research_lane

    return build_universality_research_lane(events or [])


def get_football_impact_readiness():
    from .football_impact_report import build_football_impact_readiness

    return build_football_impact_readiness()


def run_football_impact_diagnostics(
    *,
    sport: str = "americanfootball_nfl",
    market_type: str = "spread",
    team_context: dict | None = None,
    player_context: dict | None = None,
    play_drive_context: dict | None = None,
    personnel_context: dict | None = None,
    matchup_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .football_impact_report import build_football_impact_diagnostics

    return build_football_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        team_context=team_context or {},
        player_context=player_context or {},
        play_drive_context=play_drive_context or {},
        personnel_context=personnel_context or {},
        matchup_context=matchup_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        tracking_context=tracking_context or {},
        dry_run=dry_run,
    )


def get_soccer_impact_readiness():
    from .soccer_impact_readiness import build_soccer_impact_readiness

    return build_soccer_impact_readiness()


def run_soccer_impact_diagnostics(
    *,
    sport: str = "soccer",
    market_type: str = "three_way_moneyline",
    game_context: dict | None = None,
    team_context: dict | None = None,
    player_context: dict | None = None,
    lineup_context: dict | None = None,
    tactical_context: dict | None = None,
    possession_value_context: dict | None = None,
    shot_quality_context: dict | None = None,
    pressing_context: dict | None = None,
    transition_context: dict | None = None,
    set_piece_context: dict | None = None,
    goalkeeper_context: dict | None = None,
    referee_context: dict | None = None,
    matchup_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .soccer_impact_report import build_soccer_impact_diagnostics

    return build_soccer_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        game_context=game_context or {},
        team_context=team_context or {},
        player_context=player_context or {},
        lineup_context=lineup_context or {},
        tactical_context=tactical_context or {},
        possession_value_context=possession_value_context or {},
        shot_quality_context=shot_quality_context or {},
        pressing_context=pressing_context or {},
        transition_context=transition_context or {},
        set_piece_context=set_piece_context or {},
        goalkeeper_context=goalkeeper_context or {},
        referee_context=referee_context or {},
        matchup_context=matchup_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        tracking_context=tracking_context or {},
        dry_run=dry_run,
    )


def get_hockey_impact_readiness():
    from .hockey_impact_readiness import build_hockey_impact_readiness

    return build_hockey_impact_readiness()


def run_hockey_impact_diagnostics(
    *,
    sport: str = "icehockey_nhl",
    market_type: str = "moneyline",
    game_context: dict | None = None,
    team_context: dict | None = None,
    skater_context: dict | None = None,
    goalie_context: dict | None = None,
    line_context: dict | None = None,
    pair_context: dict | None = None,
    special_teams_context: dict | None = None,
    transition_context: dict | None = None,
    shot_quality_context: dict | None = None,
    matchup_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .hockey_impact_report import build_hockey_impact_diagnostics

    return build_hockey_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        game_context=game_context or {},
        team_context=team_context or {},
        skater_context=skater_context or {},
        goalie_context=goalie_context or {},
        line_context=line_context or {},
        pair_context=pair_context or {},
        special_teams_context=special_teams_context or {},
        transition_context=transition_context or {},
        shot_quality_context=shot_quality_context or {},
        matchup_context=matchup_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        tracking_context=tracking_context or {},
        dry_run=dry_run,
    )


def get_baseball_impact_readiness():
    from .baseball_impact_readiness import build_baseball_impact_readiness

    return build_baseball_impact_readiness()


def run_baseball_impact_diagnostics(
    *,
    sport: str = "baseball_mlb",
    market_type: str = "moneyline",
    game_context: dict | None = None,
    team_context: dict | None = None,
    pitcher_context: dict | None = None,
    batter_context: dict | None = None,
    lineup_context: dict | None = None,
    bullpen_context: dict | None = None,
    catcher_context: dict | None = None,
    defense_context: dict | None = None,
    baserunning_context: dict | None = None,
    park_weather_context: dict | None = None,
    umpire_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .baseball_impact_report import build_baseball_impact_diagnostics

    return build_baseball_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        game_context=game_context or {},
        team_context=team_context or {},
        pitcher_context=pitcher_context or {},
        batter_context=batter_context or {},
        lineup_context=lineup_context or {},
        bullpen_context=bullpen_context or {},
        catcher_context=catcher_context or {},
        defense_context=defense_context or {},
        baserunning_context=baserunning_context or {},
        park_weather_context=park_weather_context or {},
        umpire_context=umpire_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        tracking_context=tracking_context or {},
        dry_run=dry_run,
    )


def get_golf_impact_readiness():
    from .golf_impact_readiness import build_golf_impact_readiness

    return build_golf_impact_readiness()


def run_golf_impact_diagnostics(
    *,
    sport: str = "golf",
    market_type: str = "top_20",
    tournament_context: dict | None = None,
    player_context: dict | None = None,
    strokes_gained_context: dict | None = None,
    off_tee_context: dict | None = None,
    approach_context: dict | None = None,
    around_green_context: dict | None = None,
    putting_context: dict | None = None,
    course_context: dict | None = None,
    weather_context: dict | None = None,
    wave_context: dict | None = None,
    field_context: dict | None = None,
    form_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    simulation_context: dict | None = None,
    tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .golf_impact_report import build_golf_impact_diagnostics

    return build_golf_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        tournament_context=tournament_context or {},
        player_context=player_context or {},
        strokes_gained_context=strokes_gained_context or {},
        off_tee_context=off_tee_context or {},
        approach_context=approach_context or {},
        around_green_context=around_green_context or {},
        putting_context=putting_context or {},
        course_context=course_context or {},
        weather_context=weather_context or {},
        wave_context=wave_context or {},
        field_context=field_context or {},
        form_context=form_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        simulation_context=simulation_context or {},
        tracking_context=tracking_context or {},
        dry_run=dry_run,
    )


def get_combat_impact_readiness():
    from .combat_impact_readiness import build_combat_impact_readiness

    return build_combat_impact_readiness()


def run_combat_impact_diagnostics(
    *,
    sport: str = "combat_sports",
    market_type: str = "moneyline",
    bout_context: dict | None = None,
    fighter_a_context: dict | None = None,
    fighter_b_context: dict | None = None,
    striking_context: dict | None = None,
    grappling_context: dict | None = None,
    phase_context: dict | None = None,
    damage_context: dict | None = None,
    pace_cardio_context: dict | None = None,
    matchup_context: dict | None = None,
    ruleset_context: dict | None = None,
    judging_referee_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    film_tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .combat_impact_report import build_combat_impact_diagnostics

    return build_combat_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        bout_context=bout_context or {},
        fighter_a_context=fighter_a_context or {},
        fighter_b_context=fighter_b_context or {},
        striking_context=striking_context or {},
        grappling_context=grappling_context or {},
        phase_context=phase_context or {},
        damage_context=damage_context or {},
        pace_cardio_context=pace_cardio_context or {},
        matchup_context=matchup_context or {},
        ruleset_context=ruleset_context or {},
        judging_referee_context=judging_referee_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        film_tracking_context=film_tracking_context or {},
        dry_run=dry_run,
    )


def get_tennis_impact_readiness():
    from .tennis_impact_readiness import build_tennis_impact_readiness

    return build_tennis_impact_readiness()


def run_tennis_impact_diagnostics(
    *,
    sport: str = "tennis",
    market_type: str = "moneyline",
    match_context: dict | None = None,
    player_a_context: dict | None = None,
    player_b_context: dict | None = None,
    serve_context: dict | None = None,
    return_context: dict | None = None,
    surface_context: dict | None = None,
    format_context: dict | None = None,
    pressure_context: dict | None = None,
    tiebreak_context: dict | None = None,
    matchup_context: dict | None = None,
    conditions_context: dict | None = None,
    availability_context: dict | None = None,
    incentive_context: dict | None = None,
    calibration_context: dict | None = None,
    point_context: dict | None = None,
    tracking_context: dict | None = None,
    dry_run: bool = True,
):
    from .tennis_impact_report import build_tennis_impact_diagnostics

    return build_tennis_impact_diagnostics(
        sport=sport,
        market_type=market_type,
        match_context=match_context or {},
        player_a_context=player_a_context or {},
        player_b_context=player_b_context or {},
        serve_context=serve_context or {},
        return_context=return_context or {},
        surface_context=surface_context or {},
        format_context=format_context or {},
        pressure_context=pressure_context or {},
        tiebreak_context=tiebreak_context or {},
        matchup_context=matchup_context or {},
        conditions_context=conditions_context or {},
        availability_context=availability_context or {},
        incentive_context=incentive_context or {},
        calibration_context=calibration_context or {},
        point_context=point_context or {},
        tracking_context=tracking_context or {},
        dry_run=dry_run,
    )


def get_strategy_registry_snapshot(base_data_dir: str | None = None):
    from .strategy_registry import compact_strategy_registry

    return compact_strategy_registry()


def route_strategy_candidate(candidate: dict | None = None, *, base_data_dir: str | None = None):
    from .strategy_router import route_strategies

    return route_strategies(candidate or {})


def aggregate_strategy_candidate(
    candidate: dict | None = None,
    *,
    routed: dict | None = None,
    strategy_outputs: dict | list | None = None,
    create_disagreements: bool = False,
    base_data_dir: str | None = None,
):
    from .strategy_score_aggregator import aggregate_strategy_scores

    return aggregate_strategy_scores(
        candidate or {},
        routed=routed,
        strategy_outputs=strategy_outputs,
        create_disagreements=create_disagreements,
        base_data_dir=_data_dir(base_data_dir),
    )


def evaluate_strategy_promotion_decision(
    strategy: dict,
    evidence: dict | None = None,
    *,
    context_candidate: dict | None = None,
    actor_type: str = "system",
    base_data_dir: str | None = None,
):
    from .strategy_promotion import evaluate_strategy_promotion

    return evaluate_strategy_promotion(strategy, evidence or {}, context_candidate=context_candidate, actor_type=actor_type)


def evaluate_strategy_execution_gate(
    candidate: dict | None = None,
    *,
    owner_approval: dict | None = None,
    risk_limits: dict | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    base_data_dir: str | None = None,
):
    from src.security.hard_gate_policy import evaluate_hard_gates

    return evaluate_hard_gates(
        candidate or {},
        owner_approval=owner_approval,
        risk_limits=risk_limits,
        idempotency_key=idempotency_key,
        execution_mode=execution_mode,
        base_data_dir=_data_dir(base_data_dir),
        persist_audit=False,
    )


def get_strategy_readiness(base_data_dir: str | None = None):
    try:
        from .strategy_readiness_report import build_strategy_readiness_report
    except ModuleNotFoundError:
        def build_strategy_readiness_report(*, base_data_dir: str | None = None):
            return {
                "ok": True,
                "status": "strategy_readiness",
                "provider_write": False,
                "execution_allowed": False,
                "live_execution_enabled": False,
                "auto_execution": False,
                "auto_execution_enabled": False,
                "human_approval_required": True,
                "owner_approval_required": True,
                "actual_orders_submitted": 0,
                "actual_bets_submitted": 0,
                "actual_trades_submitted": 0,
            }

    return build_strategy_readiness_report(base_data_dir=_data_dir(base_data_dir))


def get_basketball_player_impact_readiness(base_data_dir: str | None = None):
    from .basketball_player_impact_readiness import build_basketball_player_impact_readiness

    return build_basketball_player_impact_readiness(base_data_dir=_data_dir(base_data_dir))


def run_automation_basketball_player_impact(
    candidate: dict | None = None,
    *,
    outcome_records: list[dict] | None = None,
    red_team_provider: str | None = None,
    base_data_dir: str | None = None,
):
    from .basketball_player_impact import run_basketball_player_impact

    return run_basketball_player_impact(
        candidate or {},
        outcome_records=outcome_records or [],
        red_team_provider=red_team_provider,
    )


def get_strategy_disagreements(*, base_data_dir: str | None = None, limit: int = 100):
    from .strategy_disagreement import load_strategy_disagreements

    return load_strategy_disagreements(base_data_dir=_data_dir(base_data_dir), limit=limit)


def get_advanced_diagnostic_registry_snapshot(base_data_dir: str | None = None):
    from .advanced_shape_diagnostics import get_advanced_diagnostic_registry
    from src.security.policy import locked_safety_flags

    registry = get_advanced_diagnostic_registry()
    return {
        "ok": True,
        "status": "advanced_diagnostic_registry",
        "total_diagnostics": len(registry),
        "diagnostics": list(registry.values()),
        "red_team_only": True,
        **locked_safety_flags(),
    }


def run_automation_advanced_shape_diagnostics(
    *,
    candidate: dict | None = None,
    historical_records: list[dict] | None = None,
    labeled_records: list[dict] | None = None,
    calibration_records: list[dict] | None = None,
    sequences: dict | None = None,
    provider: str | None = None,
    persist: bool = False,
    base_data_dir: str | None = None,
):
    from .advanced_red_team_report import write_advanced_diagnostics
    from .advanced_shape_diagnostics import run_advanced_shape_diagnostics

    result = run_advanced_shape_diagnostics(
        candidate or {},
        historical_records=historical_records or [],
        labeled_records=labeled_records or [],
        calibration_records=calibration_records or [],
        sequences=sequences or {},
        provider=provider,
    )
    if persist and bool(result.get("ok", True)):
        result["persistence"] = write_advanced_diagnostics(result, base_data_dir=_data_dir(base_data_dir))
    return result


def get_automation_advanced_red_team_report(
    *,
    candidate: dict | None = None,
    candidates: list[dict] | None = None,
    historical_records: list[dict] | None = None,
    labeled_records: list[dict] | None = None,
    calibration_records: list[dict] | None = None,
    sequences: dict | None = None,
    provider: str | None = None,
    persist_report: bool = True,
    base_data_dir: str | None = None,
    max_items: int = 25,
):
    from .advanced_red_team_report import build_advanced_red_team_report

    return build_advanced_red_team_report(
        candidate=candidate,
        candidates=candidates or [],
        historical_records=historical_records or [],
        labeled_records=labeled_records or [],
        calibration_records=calibration_records or [],
        sequences=sequences or {},
        provider=provider,
        persist_report=persist_report,
        base_data_dir=_data_dir(base_data_dir),
        max_items=max_items,
    )


def get_automation_advanced_red_team_latest(base_data_dir: str | None = None):
    from .advanced_red_team_report import load_advanced_red_team_latest

    return load_advanced_red_team_latest(base_data_dir=_data_dir(base_data_dir))


def evaluate_ai_analyst_provider(
    provider: str | None = None,
    *,
    provider_type: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
):
    from src.security.ai_provider_security import evaluate_ai_provider

    return evaluate_ai_provider(provider, provider_type=provider_type, base_data_dir=_data_dir(base_data_dir), persist_audit=persist_audit)


def enforce_ai_analysis_boundaries(payload: dict | list | None = None, *, actor_provider: str | None = None):
    from src.security.policy import enforce_ai_capability_boundary

    return enforce_ai_capability_boundary(payload or {}, actor_provider=actor_provider)


def evaluate_owner_approval_gate(
    approval: dict | None = None,
    *,
    requested_scope: dict | None = None,
    actor_type: str = "system",
    signing_secret: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
):
    from src.security.owner_approval_gate import evaluate_owner_approval

    return evaluate_owner_approval(
        approval,
        requested_scope=requested_scope,
        actor_type=actor_type,
        signing_secret=signing_secret,
        base_data_dir=_data_dir(base_data_dir),
        persist_audit=persist_audit,
    )


def check_provider_write_firewall(
    *,
    provider: str | None = None,
    action: str | None = None,
    request_payload: dict | None = None,
    owner_approval: dict | None = None,
    risk_limits: dict | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
):
    from src.providers.policy.write_firewall import check_provider_write_attempt

    return check_provider_write_attempt(
        provider=provider,
        action=action,
        request_payload=request_payload,
        owner_approval=owner_approval,
        risk_limits=risk_limits,
        idempotency_key=idempotency_key,
        execution_mode=execution_mode,
        base_data_dir=_data_dir(base_data_dir),
        persist_audit=persist_audit,
    )


def evaluate_execution_security_authorization(
    request: dict | None = None,
    *,
    owner_approval: dict | None = None,
    risk_limits: dict | None = None,
    idempotency_key: str | None = None,
    execution_mode: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
):
    from src.brokerage.readiness import evaluate_execution_authorization

    return evaluate_execution_authorization(
        request,
        owner_approval=owner_approval,
        risk_limits=risk_limits,
        idempotency_key=idempotency_key,
        execution_mode=execution_mode,
        base_data_dir=_data_dir(base_data_dir),
        persist_audit=persist_audit,
    )


def get_security_audit_records(base_data_dir: str | None = None, limit: int = 100):
    from src.services.ledger_service import load_security_audit_records

    return load_security_audit_records(base_data_dir=_data_dir(base_data_dir), limit=limit)


def get_scheduler_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return get_system_health(config)


def get_scheduler_review_queue(
    base_data_dir: str | None = None,
    *,
    provider: str = "all",
    market_type: str = "all",
    reason: str | None = None,
    limit: int | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    queue_state = load_review_queue_state(config)
    items = list(queue_state.get("items", []))
    storage_backend = str(queue_state.get("storage_backend") or "unknown")
    if not items:
        active_items = list_active_review_items(config)
        if active_items:
            items = active_items
            storage_backend = "in_memory"
            queue_state = {
                **queue_state,
                "storage_backend": storage_backend,
                "queue_read_ok": True,
                "queue_error_category": queue_state.get("queue_error_category"),
                "items_read_count": len(active_items),
            }
    filtered_all = filter_review_items(items, provider=provider, market_type=market_type, reason=reason)
    filtered = list(filtered_all)
    applied_limit = False
    if isinstance(limit, int) and limit > 0:
        applied_limit = len(filtered) > limit
        filtered = filtered[:limit]
    rejected_reason_counts: dict[str, int] = {}
    health_path = Path(config["paths"]["system_health"]) / "health.json"
    if health_path.exists():
        try:
            health_payload = json.loads(health_path.read_text(encoding="utf-8"))
            rejected_reason_counts = dict(health_payload.get("kalshi_rejected_reason_counts", {}))
        except Exception:
            rejected_reason_counts = {}
    summary = summarize_review_items(filtered_all, rejected_reason_counts=rejected_reason_counts)
    return {
        "ok": True,
        "status": "ok",
        "count": len(filtered),
        "items": filtered,
        "summary": summary,
        "storage_backend": storage_backend,
        "last_updated_at": queue_state.get("last_updated_at"),
        "latest_run_id": queue_state.get("latest_run_id"),
        "queue_read_ok": bool(queue_state.get("queue_read_ok", True)),
        "queue_error_category": queue_state.get("queue_error_category"),
        "queue_read_path": queue_state.get("queue_read_path"),
        "items_read_count": int(queue_state.get("items_read_count", len(items))),
        "compact_filter_applied": bool(applied_limit or str(provider).lower() != "all" or str(market_type).lower() != "all" or bool(reason)),
        "storage_health": get_storage_health(),
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }


def get_performance_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return get_system_health(config)


def run_performance_backtest(model_id: str, historical_rows_path: str | None = None, rows: list[dict] | None = None, base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    return generate_backtest_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
        rows=rows,
        base_data_dir=base,
    )


def get_performance_report(model_id: str, historical_rows_path: str | None = None, rows: list[dict] | None = None, base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    result = generate_backtest_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
        rows=rows,
        base_data_dir=base,
    )
    return result["compact_report"]


def get_paper_summary(base_data_dir: str | None = None):
    return run_paper_summary(base_data_dir=_data_dir(base_data_dir))


def get_automation_calibration_report(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return build_calibration_report(base_data_dir=base, write_report=True)


def map_automation_manifold_item(
    item: dict,
    *,
    historical_records: list[dict] | None = None,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return map_manifold_endpoint_item(item, historical_records=historical_records, base_data_dir=base)


def get_automation_manifold_clusters(*, base_data_dir: str | None = None, limit: int = 25):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return get_manifold_cluster_snapshot(base_data_dir=base, limit=limit)


def get_automation_manifold_calibration(*, base_data_dir: str | None = None, limit: int = 25):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return get_manifold_calibration_snapshot(base_data_dir=base, limit=limit)


def get_automation_manifold_no_bet_traps(*, base_data_dir: str | None = None, limit: int = 25):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return get_manifold_trap_snapshot(base_data_dir=base, limit=limit)


def run_automation_cross_asset_manifold_review(
    items: list[dict] | None,
    *,
    historical_records: list[dict] | None = None,
    persist: bool = True,
    max_items: int = 250,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return run_cross_asset_manifold_review(
        items,
        historical_records=historical_records,
        persist=persist,
        max_items=max_items,
        base_data_dir=base,
    )


def ingest_automation_outcomes(
    records: list[dict],
    *,
    source: str = "local_manual",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return ingest_outcome_records(
        records,
        source=source,
        dry_run=dry_run,
        persist=persist,
        base_data_dir=base,
    )


def import_local_settlement_outcomes(
    records: list[dict],
    *,
    supporting_paper_decisions: list[dict] | None = None,
    source: str = "local_repo_migration",
    migration_version: str = "kalshi_outcome_migration_v1",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return import_local_settlement_records(
        records,
        supporting_paper_decisions=supporting_paper_decisions,
        source=source,
        migration_version=migration_version,
        dry_run=dry_run,
        persist=persist,
        base_data_dir=base,
    )


def get_automation_outcomes(base_data_dir: str | None = None, limit: int | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    state = load_outcome_state(base)
    records = list(state.get("items", []))
    summary = summarize_outcomes(records)
    cap = limit if isinstance(limit, int) and limit > 0 else len(records)
    return {
        "ok": True,
        "status": "ok",
        "total_count": len(records),
        "records": records[:cap],
        "summary": summary,
        "storage_backend": state.get("storage_backend", "file"),
        "latest_batch_id": state.get("latest_batch_id"),
        "last_updated_at": state.get("last_updated_at"),
        "outcome_read_ok": bool(state.get("outcome_read_ok", True)),
        "outcome_error_category": state.get("outcome_error_category"),
        "storage_health": get_storage_health(),
    }


def discover_automation_outcome_completions(
    *,
    pending_rows: list[dict] | None = None,
    imported_rows: list[dict] | None = None,
    use_kalshi_snapshot: bool = True,
    write_local_report: bool = False,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter
    from src.services.settlement_service import build_outcome_completion_report, write_outcome_completion_candidates

    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    adapter = KalshiReadonlyAdapter(contract) if use_kalshi_snapshot else None
    report = build_outcome_completion_report(
        pending_rows=pending_rows,
        imported_rows=imported_rows,
        adapter=adapter,
        base_data_dir=base,
        use_kalshi_snapshot=use_kalshi_snapshot,
    )
    if write_local_report:
        report.update(write_outcome_completion_candidates(report, base_data_dir=base))
    return report


def run_automation_calibration_collector(
    *,
    dry_run: bool = True,
    persist_outcomes: bool = False,
    max_new_contracts: int | None = None,
    target_daily_new_contracts: int | None = None,
    hard_cap_daily_new_contracts: int | None = None,
    max_markets_scanned: int | None = None,
    include_short_term: bool = True,
    include_medium_term: bool = True,
    include_long_term: bool = True,
    adaptive_throttle: bool | None = None,
    deepseek_review: bool = False,
    base_data_dir: str | None = None,
):
    from .calibration_collector import run_collector_cycle

    base = _data_dir(base_data_dir)
    return run_collector_cycle(
        dry_run=dry_run,
        persist_outcomes=persist_outcomes,
        max_new_contracts=max_new_contracts,
        target_daily_new_contracts=target_daily_new_contracts,
        hard_cap_daily_new_contracts=hard_cap_daily_new_contracts,
        max_markets_scanned=max_markets_scanned,
        include_short_term=include_short_term,
        include_medium_term=include_medium_term,
        include_long_term=include_long_term,
        adaptive_throttle=adaptive_throttle,
        deepseek_review=deepseek_review,
        base_data_dir=base,
    )


def run_automation_calibration_collector_scheduled(payload: dict | None = None, *, base_data_dir: str | None = None):
    from .collector_scheduled_runner import run_scheduled_collector_cycle

    return run_scheduled_collector_cycle(payload, base_data_dir=_data_dir(base_data_dir))


def get_automation_collector_daily_report(base_data_dir: str | None = None):
    from .calibration_collector import write_daily_report

    return write_daily_report(base_data_dir=_data_dir(base_data_dir))


def run_automation_deepseek_review(
    *,
    collector_cycle_report: dict | None = None,
    daily_report: dict | None = None,
    calibration_report: dict | None = None,
    sampled_contracts: list[dict] | None = None,
    candidate: dict | None = None,
    candidates: list[dict] | None = None,
    core_model_action: str | None = None,
    enabled: bool | None = None,
    base_data_dir: str | None = None,
    **summary_inputs,
):
    from .deepseek_profit_lab import run_candidate_review

    selected_candidate = candidate
    if selected_candidate is None and candidates:
        selected_candidate = candidates[0]
    if selected_candidate is None and sampled_contracts:
        selected_candidate = sampled_contracts[0]
    if selected_candidate is None:
        selected_candidate = {"candidate_id": "deepseek_profit_lab_review", "asset_type": "unknown", "market_type": "unknown"}
    summaries = {
        "review_queue_summary": summary_inputs.get("review_queue_summary") or collector_cycle_report or {},
        "calibration_summary": summary_inputs.get("calibration_summary") or calibration_report or {},
        "outcome_summary": summary_inputs.get("outcome_summary") or {},
        "provider_health_summary": summary_inputs.get("provider_health_summary") or {},
        "trap_no_bet_summary": summary_inputs.get("trap_no_bet_summary") or {},
        "security_readiness_summary": summary_inputs.get("security_readiness_summary") or {},
        "strategy_readiness_summary": summary_inputs.get("strategy_readiness_summary") or {},
        "small_account_summary": summary_inputs.get("small_account_summary") or {},
        "stock_crypto_pattern_summary": summary_inputs.get("stock_crypto_pattern_summary") or {},
        "sportsbook_full_board_summary": summary_inputs.get("sportsbook_full_board_summary") or {},
        "kalshi_prediction_market_summary": summary_inputs.get("kalshi_prediction_market_summary") or daily_report or {},
        "manifold_cluster_summary": summary_inputs.get("manifold_cluster_summary") or {},
        "markov_hmm_summary": summary_inputs.get("markov_hmm_summary") or {},
        "disagreement_summary": summary_inputs.get("disagreement_summary") or {},
    }
    return run_candidate_review(
        candidate=selected_candidate,
        core_model_action=core_model_action,
        enabled=enabled,
        base_data_dir=_data_dir(base_data_dir),
        summaries=summaries,
    )


def run_automation_deepseek_red_team(
    *,
    candidates: list[dict] | None = None,
    candidate: dict | None = None,
    enabled: bool | None = None,
    base_data_dir: str | None = None,
    **summary_inputs,
):
    from .deepseek_profit_lab import run_red_team_review

    return run_red_team_review(
        candidates=candidates,
        candidate=candidate,
        enabled=enabled,
        base_data_dir=_data_dir(base_data_dir),
        **summary_inputs,
    )


def get_deepseek_disagreements(*, base_data_dir: str | None = None, limit: int = 100):
    from .deepseek_disagreement_queue import load_disagreement_queue

    return load_disagreement_queue(base_data_dir=_data_dir(base_data_dir), limit=limit)


def get_deepseek_daily_report(
    *,
    report_date: str | None = None,
    enabled: bool | None = None,
    persist_report: bool = True,
    base_data_dir: str | None = None,
):
    from .deepseek_profit_lab import run_daily_report

    return run_daily_report(
        report_date=report_date,
        enabled=enabled,
        persist_report=persist_report,
        base_data_dir=_data_dir(base_data_dir),
    )


def get_provider_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    from src.providers.health import summarize_provider_health

    return summarize_provider_health(config["providers"])


def get_provider_registry_snapshot(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    from src.providers.registry import get_provider_registry

    providers = list(get_provider_registry(include_legacy_aliases=True).values())
    blocked_count = sum(
        1
        for item in providers
        if (not bool(item.get("enabled", False))) or (not bool(item.get("live_calls_enabled", False)))
    )
    return {
        "ok": True,
        "status": "ok",
        "timestamp": None,
        "provider_count": len(providers),
        "enabled_provider_count": sum(1 for item in providers if item.get("enabled")),
        "live_calls_enabled_count": sum(1 for item in providers if item.get("live_calls_enabled")),
        "blocked_count": blocked_count,
        "dry_run": True,
        "blockers": ["dry_run_placeholder", "live_calls_disabled"],
        "providers": providers,
    }


def get_sharp_provider_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    from src.services.odds_runtime_bridge import SharpSportsbookAdapter, summarize_sportsbook_snapshot

    adapter = SharpSportsbookAdapter(contract)
    payload = adapter.health_check()
    return summarize_sportsbook_snapshot(payload)


def run_sharp_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    from src.services.odds_runtime_bridge import (
        SharpSportsbookAdapter,
        get_sportsbook_snapshot,
        summarize_sportsbook_snapshot,
        validate_sportsbook_snapshot,
        write_sportsbook_snapshot,
    )

    adapter = SharpSportsbookAdapter(contract)
    snapshot = get_sportsbook_snapshot(adapter)
    validation = validate_sportsbook_snapshot(snapshot)
    snapshot_path = None
    if write_snapshot and int(snapshot.get("records_received", 0)) > 0:
        snapshot_path = write_sportsbook_snapshot(snapshot, base_data_dir=base)
    summary = summarize_sportsbook_snapshot(snapshot, snapshot_path=snapshot_path)
    summary["validation_status"] = validation["status"]
    summary["validation_errors"] = validation["errors"][:10]
    return summary


def get_kalshi_provider_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter, summarize_kalshi_snapshot

    adapter = KalshiReadonlyAdapter(contract)
    payload = adapter.health_check()
    return summarize_kalshi_snapshot(payload)


def run_kalshi_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    from src.services.prediction_market_runtime_bridge import (
        KalshiReadonlyAdapter,
        get_kalshi_snapshot,
        summarize_kalshi_snapshot,
        validate_kalshi_snapshot,
        write_kalshi_snapshot,
    )

    adapter = KalshiReadonlyAdapter(contract)
    snapshot = get_kalshi_snapshot(adapter)
    validation = validate_kalshi_snapshot(snapshot)
    snapshot_path = None
    if write_snapshot and int(snapshot.get("records_received", 0)) > 0:
        snapshot_path = write_kalshi_snapshot(snapshot, base_data_dir=base)
    summary = summarize_kalshi_snapshot(snapshot, snapshot_path=snapshot_path)
    summary["validation_status"] = validation["status"]
    summary["validation_errors"] = validation["errors"][:10]
    return summary


def get_institutional_lab_health(base_data_dir: str | None = None):
    from .institutional_cross_asset_lab import get_institutional_lab_health as _health

    return _health(base_data_dir=_data_dir(base_data_dir))


def run_institutional_lab(
    *,
    dry_run: bool = True,
    asset_classes: list[str] | None = None,
    read_existing_outputs_only: bool = True,
    persist_lab_report: bool = True,
    persist_outcomes: bool = False,
    deepseek_review: bool = False,
    execution_simulation: bool = False,
    base_data_dir: str | None = None,
):
    from .institutional_cross_asset_lab import run_institutional_lab as _run

    return _run(
        dry_run=dry_run,
        asset_classes=asset_classes,
        read_existing_outputs_only=read_existing_outputs_only,
        persist_lab_report=persist_lab_report,
        persist_outcomes=persist_outcomes,
        deepseek_review=deepseek_review,
        execution_simulation=execution_simulation,
        base_data_dir=_data_dir(base_data_dir),
    )


def get_institutional_lab_report(base_data_dir: str | None = None):
    from .institutional_cross_asset_lab import get_institutional_lab_report as _report

    return _report(base_data_dir=_data_dir(base_data_dir))


def get_institutional_lab_daily_report(base_data_dir: str | None = None, report_date: str | None = None):
    from .institutional_cross_asset_lab import get_institutional_lab_daily_report as _daily

    return _daily(base_data_dir=_data_dir(base_data_dir), report_date=report_date)


def run_institutional_deepseek_review(*, report: dict | None = None, enabled: bool | None = None, base_data_dir: str | None = None):
    from .institutional_deepseek_review import run_deepseek_sidecar_review

    return run_deepseek_sidecar_review(report=report or {}, enabled=enabled, base_data_dir=_data_dir(base_data_dir))


def simulate_institutional_execution(payload: dict, *, base_data_dir: str | None = None):
    from src.services.execution_service import simulate_execution

    return simulate_execution(payload, base_data_dir=_data_dir(base_data_dir))


def get_institutional_lab_audit(base_data_dir: str | None = None, limit: int = 100):
    from .institutional_cross_asset_lab import get_institutional_lab_audit as _audit

    return _audit(base_data_dir=_data_dir(base_data_dir), limit=limit)


def get_data_source_registry_snapshot(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_registry_report

    return build_registry_report(module=module)


def get_data_source_coverage_snapshot(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_registry
    from .model_input_coverage import build_coverage_report

    registry = build_registry(module=module)
    return build_coverage_report(registry=registry)


def get_data_source_research_lanes_snapshot(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_registry
    from .data_source_research_lanes import build_research_tasks

    registry = build_registry(module=module)
    return build_research_tasks(registry.get("lanes", []))


def get_data_source_env_var_registry(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_env_var_registry

    return build_env_var_registry(module=module)


def get_data_source_priorities_snapshot(*, module: str | None = None, limit: int = 50, base_data_dir: str | None = None):
    from .data_source_registry import build_source_priorities

    return build_source_priorities(module=module, limit=limit)


def get_public_apis_expansion_report(*, module: str | None = None, persist_report: bool = False, base_data_dir: str | None = None):
    from .data_source_registry import build_public_apis_expansion_report, write_public_apis_expansion_report

    report = build_public_apis_expansion_report(module=module)
    if persist_report:
        report.update(write_public_apis_expansion_report(report, base_data_dir=_data_dir(base_data_dir)))
    return report


def get_data_availability_tiers_report(*, module: str | None = None, persist_report: bool = False, base_data_dir: str | None = None):
    from .data_availability_tiers import build_data_availability_report, write_data_availability_report
    from .data_source_registry import build_registry

    report = build_data_availability_report(registry=build_registry(module=module), module=module)
    if persist_report:
        report.update(write_data_availability_report(report, base_data_dir=_data_dir(base_data_dir)))
    return report


def get_data_source_registry_health(base_data_dir: str | None = None):
    from .data_source_registry import build_registry_report, summarize_registry

    report = build_registry_report()
    summary = summarize_registry(report)
    return {
        "ok": True,
        "status": "ok",
        "schema_version": report.get("schema_version"),
        "total_lanes": summary["total_lanes"],
        "total_sources": summary["total_sources"],
        "enabled_source_count": summary.get("enabled_source_count", 0),
        "source_counts_by_category": summary.get("source_counts_by_category", {}),
        "key_required_source_count": summary.get("key_required_source_count", 0),
        "oauth_required_source_count": summary.get("oauth_required_source_count", 0),
        "provider_write_enabled_count": summary.get("provider_write_enabled_count", 0),
        "execution_allowed_count": summary.get("execution_allowed_count", 0),
        "lanes_with_candidate_sources": summary["lanes_with_candidate_sources"],
        "lanes_needing_external_research": summary["lanes_needing_external_research"],
        "needs_terms_review_count": summary["needs_terms_review_count"],
        "future_source_candidate_count": summary["future_source_candidate_count"],
        "storage_health": get_storage_health(),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def verify_data_source_registry(*, module: str | None = None, persist_report: bool = True, base_data_dir: str | None = None):
    from .data_source_registry import verify_registry

    return verify_registry(module=module, persist_report=persist_report, base_data_dir=_data_dir(base_data_dir))


def verify_ncaaf_cfbd_adapter(
    *,
    dry_run: bool = True,
    season: int | None = None,
    week: int | None = None,
    max_records: int = 5,
    fetch_live_sample: bool = False,
    sample_profile: str = "games_tiny",
    max_provider_calls: int | None = None,
    include_games: bool = True,
    include_team_stats: bool = False,
    include_advanced_stats: bool = False,
    include_rankings: bool = False,
    include_lines: bool = False,
    base_data_dir: str | None = None,
):
    from .ncaaf_collegefootballdata_adapter import verify_ncaaf_cfbd_adapter as _verify

    return _verify(
        dry_run=dry_run,
        season=season,
        week=week,
        max_records=max_records,
        fetch_live_sample=fetch_live_sample,
        sample_profile=sample_profile,
        max_provider_calls=max_provider_calls,
        include_games=include_games,
        include_team_stats=include_team_stats,
        include_advanced_stats=include_advanced_stats,
        include_rankings=include_rankings,
        include_lines=include_lines,
        base_data_dir=_data_dir(base_data_dir),
    )
