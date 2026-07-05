from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

class AutomationRunOnceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    run_key: Optional[str] = None
    injected_data: dict[str, Any] = Field(default_factory=dict)


class AutomationOutcomeIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist: bool = False
    source: str = "local_manual"
    records: list[dict[str, Any]] = Field(default_factory=list)


class AutomationOutcomeLocalSettlementImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist: bool = False
    source: str = "local_repo_migration"
    migration_version: str = "kalshi_outcome_migration_v1"
    records: list[dict[str, Any]] = Field(default_factory=list)
    supporting_paper_decisions: list[dict[str, Any]] = Field(default_factory=list)


class AutomationSettlementDiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    pending_rows: list[dict[str, Any]] = Field(default_factory=list)
    imported_rows: list[dict[str, Any]] = Field(default_factory=list)
    use_kalshi_snapshot: bool = True
    write_local_report: bool = False


class AutomationCalibrationCollectorRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist_outcomes: bool = False
    max_new_contracts: Optional[int] = 50
    target_daily_new_contracts: Optional[int] = 250
    hard_cap_daily_new_contracts: Optional[int] = 500
    max_markets_scanned: Optional[int] = 25000
    include_short_term: bool = True
    include_medium_term: bool = True
    include_long_term: bool = True
    adaptive_throttle: bool = True
    deepseek_review: bool = False


class AutomationCalibrationCollectorScheduledRunRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    trigger_type: Optional[str] = "scheduled_endpoint"
    target_daily_new_contracts: Optional[int] = 250
    hard_cap_daily_new_contracts: Optional[int] = 500
    max_new_contracts_per_cycle: Optional[int] = 50
    max_markets_scanned: Optional[int] = 25000
    adaptive_throttle: bool = True
    include_short_term: bool = True
    include_medium_term: bool = True
    include_long_term: bool = True
    deepseek_review: bool = False


class AutomationDeepSeekReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    collector_cycle_report: dict[str, Any] = Field(default_factory=dict)
    daily_report: dict[str, Any] = Field(default_factory=dict)
    calibration_report: dict[str, Any] = Field(default_factory=dict)
    sampled_contracts: list[dict[str, Any]] = Field(default_factory=list)
    candidate: dict[str, Any] = Field(default_factory=dict)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    core_model_action: Optional[str] = None
    enabled: Optional[bool] = None
    review_queue_summary: dict[str, Any] = Field(default_factory=dict)
    outcome_summary: dict[str, Any] = Field(default_factory=dict)
    provider_health_summary: dict[str, Any] = Field(default_factory=dict)
    manifold_cluster_summary: dict[str, Any] = Field(default_factory=dict)
    markov_hmm_summary: dict[str, Any] = Field(default_factory=dict)
    sportsbook_full_board_summary: dict[str, Any] = Field(default_factory=dict)
    stock_crypto_pattern_summary: dict[str, Any] = Field(default_factory=dict)
    kalshi_prediction_market_summary: dict[str, Any] = Field(default_factory=dict)
    small_account_summary: dict[str, Any] = Field(default_factory=dict)
    security_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    strategy_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    trap_no_bet_summary: dict[str, Any] = Field(default_factory=dict)


class AutomationDeepSeekRedTeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    candidate: dict[str, Any] = Field(default_factory=dict)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    enabled: Optional[bool] = None
    review_queue_summary: dict[str, Any] = Field(default_factory=dict)
    calibration_summary: dict[str, Any] = Field(default_factory=dict)
    outcome_summary: dict[str, Any] = Field(default_factory=dict)
    provider_health_summary: dict[str, Any] = Field(default_factory=dict)
    manifold_cluster_summary: dict[str, Any] = Field(default_factory=dict)
    markov_hmm_summary: dict[str, Any] = Field(default_factory=dict)
    sportsbook_full_board_summary: dict[str, Any] = Field(default_factory=dict)
    stock_crypto_pattern_summary: dict[str, Any] = Field(default_factory=dict)
    kalshi_prediction_market_summary: dict[str, Any] = Field(default_factory=dict)
    small_account_summary: dict[str, Any] = Field(default_factory=dict)
    security_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    strategy_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    trap_no_bet_summary: dict[str, Any] = Field(default_factory=dict)


class AutomationAdvancedShapeDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    candidate: dict[str, Any] = Field(default_factory=dict)
    historical_records: list[dict[str, Any]] = Field(default_factory=list)
    labeled_records: list[dict[str, Any]] = Field(default_factory=list)
    calibration_records: list[dict[str, Any]] = Field(default_factory=list)
    sequences: dict[str, Any] = Field(default_factory=dict)
    provider: Optional[str] = None
    persist: bool = False


class AutomationBasketballPlayerImpactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    candidate: dict[str, Any] = Field(default_factory=dict)
    outcome_records: list[dict[str, Any]] = Field(default_factory=list)
    red_team_provider: Optional[str] = None


class AutomationExtremeSignalDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    candidate: dict[str, Any] = Field(default_factory=dict)
    baseline_values: list[Any] = Field(default_factory=list)
    matrix_payload: dict[str, Any] = Field(default_factory=dict)


class AutomationFootballImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "americanfootball_nfl"
    market_type: str = "spread"
    dry_run: bool = True
    team_context: dict[str, Any] = Field(default_factory=dict)
    player_context: dict[str, Any] = Field(default_factory=dict)
    play_drive_context: dict[str, Any] = Field(default_factory=dict)
    personnel_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationHockeyImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "icehockey_nhl"
    market_type: str = "moneyline"
    dry_run: bool = True
    game_context: dict[str, Any] = Field(default_factory=dict)
    team_context: dict[str, Any] = Field(default_factory=dict)
    skater_context: dict[str, Any] = Field(default_factory=dict)
    goalie_context: dict[str, Any] = Field(default_factory=dict)
    line_context: dict[str, Any] = Field(default_factory=dict)
    pair_context: dict[str, Any] = Field(default_factory=dict)
    special_teams_context: dict[str, Any] = Field(default_factory=dict)
    transition_context: dict[str, Any] = Field(default_factory=dict)
    shot_quality_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationSoccerImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "soccer"
    market_type: str = "three_way_moneyline"
    dry_run: bool = True
    game_context: dict[str, Any] = Field(default_factory=dict)
    team_context: dict[str, Any] = Field(default_factory=dict)
    player_context: dict[str, Any] = Field(default_factory=dict)
    lineup_context: dict[str, Any] = Field(default_factory=dict)
    tactical_context: dict[str, Any] = Field(default_factory=dict)
    possession_value_context: dict[str, Any] = Field(default_factory=dict)
    shot_quality_context: dict[str, Any] = Field(default_factory=dict)
    pressing_context: dict[str, Any] = Field(default_factory=dict)
    transition_context: dict[str, Any] = Field(default_factory=dict)
    set_piece_context: dict[str, Any] = Field(default_factory=dict)
    goalkeeper_context: dict[str, Any] = Field(default_factory=dict)
    referee_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationBaseballImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "baseball_mlb"
    market_type: str = "moneyline"
    dry_run: bool = True
    game_context: dict[str, Any] = Field(default_factory=dict)
    team_context: dict[str, Any] = Field(default_factory=dict)
    pitcher_context: dict[str, Any] = Field(default_factory=dict)
    batter_context: dict[str, Any] = Field(default_factory=dict)
    lineup_context: dict[str, Any] = Field(default_factory=dict)
    bullpen_context: dict[str, Any] = Field(default_factory=dict)
    catcher_context: dict[str, Any] = Field(default_factory=dict)
    defense_context: dict[str, Any] = Field(default_factory=dict)
    baserunning_context: dict[str, Any] = Field(default_factory=dict)
    park_weather_context: dict[str, Any] = Field(default_factory=dict)
    umpire_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationGolfImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "golf"
    market_type: str = "top_20"
    dry_run: bool = True
    tournament_context: dict[str, Any] = Field(default_factory=dict)
    player_context: dict[str, Any] = Field(default_factory=dict)
    strokes_gained_context: dict[str, Any] = Field(default_factory=dict)
    off_tee_context: dict[str, Any] = Field(default_factory=dict)
    approach_context: dict[str, Any] = Field(default_factory=dict)
    around_green_context: dict[str, Any] = Field(default_factory=dict)
    putting_context: dict[str, Any] = Field(default_factory=dict)
    course_context: dict[str, Any] = Field(default_factory=dict)
    weather_context: dict[str, Any] = Field(default_factory=dict)
    wave_context: dict[str, Any] = Field(default_factory=dict)
    field_context: dict[str, Any] = Field(default_factory=dict)
    form_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    simulation_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationCombatImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "combat_sports"
    market_type: str = "moneyline"
    dry_run: bool = True
    bout_context: dict[str, Any] = Field(default_factory=dict)
    fighter_a_context: dict[str, Any] = Field(default_factory=dict)
    fighter_b_context: dict[str, Any] = Field(default_factory=dict)
    striking_context: dict[str, Any] = Field(default_factory=dict)
    grappling_context: dict[str, Any] = Field(default_factory=dict)
    phase_context: dict[str, Any] = Field(default_factory=dict)
    damage_context: dict[str, Any] = Field(default_factory=dict)
    pace_cardio_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    ruleset_context: dict[str, Any] = Field(default_factory=dict)
    judging_referee_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    film_tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationTennisImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "tennis"
    market_type: str = "moneyline"
    dry_run: bool = True
    match_context: dict[str, Any] = Field(default_factory=dict)
    player_a_context: dict[str, Any] = Field(default_factory=dict)
    player_b_context: dict[str, Any] = Field(default_factory=dict)
    serve_context: dict[str, Any] = Field(default_factory=dict)
    return_context: dict[str, Any] = Field(default_factory=dict)
    surface_context: dict[str, Any] = Field(default_factory=dict)
    format_context: dict[str, Any] = Field(default_factory=dict)
    pressure_context: dict[str, Any] = Field(default_factory=dict)
    tiebreak_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    conditions_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    point_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationManifoldMapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    item: dict[str, Any] = Field(default_factory=dict)
    historical_records: list[dict[str, Any]] = Field(default_factory=list)


class AutomationCrossAssetManifoldReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist: bool = True
    max_items: int = 250
    items: list[dict[str, Any]] = Field(default_factory=list)
    historical_records: list[dict[str, Any]] = Field(default_factory=list)


class AutomationPatternDetectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    items: list[dict[str, Any]] = Field(default_factory=list)


class AutomationSmallAccountReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist_queue: bool = False
    session_state: dict[str, Any] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)


class DataSourceVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    module: Optional[str] = None
    persist_report: bool = True


class NcaafCfbdVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    season: Optional[int] = None
    week: Optional[int] = None
    max_records: int = 5
    fetch_live_sample: bool = False
    sample_profile: str = "games_tiny"
    max_provider_calls: int = 1
    include_games: bool = True
    include_team_stats: bool = False
    include_advanced_stats: bool = False
    include_rankings: bool = False
    include_lines: bool = False


class InstitutionalLabRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    asset_classes: list[str] = Field(default_factory=lambda: ["prediction_market", "stock", "bond", "major_asset", "sportsbook"])
    read_existing_outputs_only: bool = True
    persist_lab_report: bool = True
    persist_outcomes: bool = False
    deepseek_review: bool = False
    execution_simulation: bool = False


class InstitutionalDeepSeekReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    report: dict[str, Any] = Field(default_factory=dict)
    enabled: Optional[bool] = None


class InstitutionalExecutionSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    simulation_only: Optional[bool] = None
    live_execution_requested: bool = False
    candidate_id: Optional[str] = None
    asset_class: Optional[str] = None
    provider: Optional[str] = None
    human_command: str = "simulate_only"
    max_theoretical_risk: float = 0
    submit_live_order: bool = False
    provider_write: bool = False
    execution_allowed: bool = False
    live_execution_enabled: bool = False
    auto_execution_enabled: bool = False
    auto_bet_enabled: bool = False
    auto_trade_enabled: bool = False
    kalshi_order_execution_enabled: bool = False
    sportsbook_bet_execution_enabled: bool = False
    broker_order_execution_enabled: bool = False
