from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EvaluateLineIn(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sportsbook: str
    market: str
    selection: str
    line: Optional[float] = None
    odds_american: int
    model_probability: Optional[float] = None
    correlation_group: Optional[str] = None
    opening_odds_american: Optional[int] = None


class EvaluateLinesRequest(BaseModel):
    sport: str = Field(..., description="Sport key (e.g., 'baseball_mlb', 'basketball_nba')")
    event: str = Field(..., description="Event description or identifier")
    bankroll: float = Field(..., gt=0, description="Total bankroll amount for stake calculations")
    unit_size: float = Field(..., gt=0, description="Base betting unit size")
    risk_profile: str = Field(default="standard", description="Risk profile: 'conservative', 'standard', or 'aggressive'")
    lines: list[EvaluateLineIn] = Field(..., min_length=1, description="List of betting lines to evaluate")
    max_stake_pct: float = Field(default=0.02, gt=0, le=0.25, description="Maximum stake percentage of bankroll per bet")


class PriceEventRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sport: str = Field(..., description="Sport key (e.g., 'baseball_mlb', 'basketball_nba')")
    event_id: str = Field(..., description="Unique event identifier")
    league: str = Field(..., description="League or sport key (e.g., 'mlb', 'baseball_mlb')")
    markets: str = Field(default="h2h,spreads,totals", description="Comma-separated list of markets to price")
    provider: Optional[str] = Field(None, description="Odds provider to use (defaults to configured provider)")
    bankroll: float = Field(default=1000, ge=0, description="Total bankroll amount for stake calculations")
    unit_size: float = Field(default=25, gt=0, description="Base betting unit size")
    risk_profile: str = Field(default="conservative", description="Risk profile: 'conservative', 'standard', or 'aggressive'")
    model_probabilities: Optional[dict[str, Any]] = Field(None, description="Optional model probabilities for pricing calculations")


class ModelProbabilityRequest(BaseModel):
    market_probability: Optional[float] = Field(None, gt=0, lt=1, description="Market probability (0-1), inferred from priced_rows if not provided")
    projection_probability: Optional[float] = Field(None, gt=0, lt=1, description="Model projection probability (0-1)")
    pitcher_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Pitcher-related probability adjustment (-0.1 to 0.1)")
    weather_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Weather-related probability adjustment (-0.1 to 0.1)")
    lineup_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Lineup-related probability adjustment (-0.1 to 0.1)")
    bullpen_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Bullpen-related probability adjustment (-0.1 to 0.1)")
    injury_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Injury-related probability adjustment (-0.1 to 0.1)")
    park_factor_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Park factor probability adjustment (-0.1 to 0.1)")
    umpire_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Umpire-related probability adjustment (-0.1 to 0.1)")
    player_prop_projection: Optional[float] = Field(None, gt=0, lt=1, description="Player prop projection probability (0-1)")
    sharp_market_probability: Optional[float] = Field(None, gt=0, lt=1, description="Sharp market probability (0-1)")
    closing_line_projection: Optional[float] = Field(None, gt=0, lt=1, description="Closing line projection probability (0-1)")
    priced_rows: Optional[list[dict[str, Any]]] = Field(None, description="List of priced rows with probability data for inference")


class AnalyzeEventRequest(BaseModel):
    sport: str = Field(..., description="Sport key (e.g., 'baseball_mlb', 'basketball_nba')")
    league: str = Field(..., description="League or sport key (e.g., 'mlb', 'baseball_mlb')")
    event_id: str = Field(..., description="Unique event identifier")
    markets: str = Field(default="h2h,spreads,totals", description="Comma-separated list of markets to analyze")
    provider: Optional[str] = Field(None, description="Odds provider to use (defaults to configured provider)")
    bankroll: float = Field(default=1000, ge=0, description="Total bankroll amount for stake calculations")
    unit_size: float = Field(default=25, gt=0, description="Base betting unit size")
    risk_profile: str = Field(default="conservative", description="Risk profile: 'conservative', 'standard', or 'aggressive'")
    max_stake_pct: float = Field(default=0.02, gt=0, le=0.25, description="Maximum stake percentage of bankroll per bet")
    independent_inputs: Optional[dict[str, Any]] = Field(None, description="Optional independent inputs for model probability calculations")


class SportAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    sport: Optional[Any] = Field(None, description="Official sport key. egaming is accepted as a backward-compatible alias for esports.")
    league: Optional[str] = Field(None, description="Optional league key.")
    market: Optional[Any] = Field(None, description="Market to analyze.")
    event_id: Optional[str] = Field(None, description="Optional event identifier.")
    home_team: Optional[str] = Field(None, description="Optional home team.")
    away_team: Optional[str] = Field(None, description="Optional away team.")
    player_name: Optional[str] = Field(None, description="Optional player name for prop analysis.")
    odds_american: Optional[Any] = Field(None, description="Optional American odds.")
    line: Optional[Any] = Field(None, description="Optional market line.")
    input_stats: Optional[Any] = Field(None, description="Optional model inputs. Missing required inputs force inactive_missing_data.")
    risk_profile: Optional[str] = Field("conservative", description="Risk profile: conservative, standard, or aggressive.")
    bankroll: Optional[Any] = Field(None, description="Optional bankroll.")
    unit_size: Optional[Any] = Field(None, description="Optional base unit size.")


class ScreenshotAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    source_type: Optional[str] = Field(None, description="parsed_fields, screenshot_text, ocr_text, or image_metadata.")
    sport: Optional[Any] = None
    league: Optional[Any] = None
    event: Optional[str] = None
    teams: Optional[list[str]] = None
    market: Optional[Any] = None
    selection: Optional[str] = None
    odds_american: Optional[Any] = None
    line: Optional[Any] = None
    total_line: Optional[Any] = None
    book: Optional[str] = None
    screenshot_text: Optional[str] = None
    visible_markets: Optional[list[Any]] = None
    visible_props: Optional[list[Any]] = None
    visible_alt_lines: Optional[list[Any]] = None
    bankroll: Optional[Any] = None
    unit_size: Optional[Any] = None
    risk_profile: Optional[str] = "conservative"
    input_stats: Optional[Any] = None


class ActionBetLogRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    sport_key: Optional[str] = None
    event_id: Optional[str] = None
    event: Optional[str] = None
    sportsbook: Optional[str] = None
    market: Optional[Any] = None
    selection: Optional[str] = None
    line: Optional[float] = None
    odds_american: Optional[int] = None
    stake: float = 0
    unit_size: Optional[float] = None
    bankroll_at_bet: Optional[float] = None
    model_level: Optional[str] = None
    probability_type: Optional[str] = None
    model_probability: Optional[float] = None
    market_probability: Optional[float] = None
    final_probability: Optional[float] = None
    implied_probability: Optional[float] = None
    edge_percent: Optional[float] = None
    ev_per_100: Optional[float] = None
    kelly_percent: Optional[float] = None
    suggested_stake: Optional[float] = None
    decision: Optional[str] = None
    minimum_playable_odds: Optional[int] = None
    actual_odds_taken: Optional[int] = None
    closing_odds: Optional[int] = None
    result: Optional[str] = "pending"
    status: Optional[str] = None
    risk_profile: Optional[str] = None
    confidence: Optional[float | str] = None
    correlation_group: Optional[str] = None
    user_action: Optional[str] = None
    manual_override: bool = False
    confirmed_bets_allowed: Optional[bool] = None
    notes: Optional[str] = None


class ActionBetResultRequest(BaseModel):
    bet_id: str
    result: str
    closing_odds: Optional[int] = None


class ActiveEventsResponse(BaseModel):
    ok: bool
    endpoint: str
    league: str
    provider: str
    count: int
    events: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None


class EventOddsResponse(BaseModel):
    ok: bool
    endpoint: str
    event_id: str
    league: str
    provider: str
    markets_requested: list[str]
    markets: list[dict[str, Any]]
    bookmakers: list[str]
    error: Optional[str] = None
    detail: Optional[str] = None


class FirstEventOddsResponse(BaseModel):
    ok: bool
    endpoint: str
    event_id: str
    league: str
    provider: str
    markets_requested: list[str]
    markets: list[dict[str, Any]]
    bookmakers: list[str]
    error: Optional[str] = None
    detail: Optional[str] = None


class PriceEventResponse(BaseModel):
    ok: bool
    endpoint: str
    event_id: str
    league: str
    provider: str
    markets_requested: list[str]
    markets: list[dict[str, Any]]
    bookmakers: list[str]
    pricing: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None


class ModelProbabilityResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    ok: bool
    endpoint: str
    final_probability: Optional[float] = None
    probability_type: Optional[str] = None
    market_probability: Optional[float] = None
    active_inputs: list[str] = []
    missing_inputs: list[str] = []
    applied_adjustments: dict[str, float] = {}
    adjustment_cap_warnings: list[str] = []
    model_limitations: list[str] = []
    data_quality_score: Optional[float] = None
    confidence: Optional[str] = None
    confidence_grade: Optional[str] = None
    provider_status: dict[str, str] = {}
    results: Optional[list[dict[str, Any]]] = None
    processed_rows: Optional[int] = None
    successful_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    error: Optional[str] = None
    detail: Optional[str] = None


class EvaluateLinesResponse(BaseModel):
    ok: bool
    endpoint: str
    results: list[dict[str, Any]]
    summary: dict[str, Any]
    error: Optional[str] = None
    detail: Optional[str] = None


class AnalyzeEventResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    ok: bool
    endpoint: str
    sport: str
    league: str
    event_id: str
    markets_requested: list[str]
    probability_type: Optional[str] = None
    confirmed_bets: list[dict[str, Any]] = []
    target_lines: list[dict[str, Any]] = []
    no_bets: list[dict[str, Any]] = []
    warnings: list[str] = []
    model_limitations: list[str] = []
    missing_inputs: list[str] = []
    active_inputs: list[str] = []
    market_summary: list[dict[str, Any]] = []
    evaluation_results: list[dict[str, Any]] = []
    log_ready_rows: list[dict[str, Any]] = []
    error: Optional[str] = None
    detail: Optional[str] = None
    step_failed: Optional[str] = None


class SportModelConfigResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sport_key: str = Field(..., description="Canonical registry sport key used by Action-safe betting routes and governance checks.")
    display_name: str = Field(..., description="Human-readable sport or league name.")
    status: str = Field(..., description="Current build status for this sport's model pipeline.")
    model_level: str = Field(..., description="Model maturity level: not_built, market_derived_only, projection_ready, blended_ready, or fully_independent.")
    confirmed_bets_allowed: bool = Field(..., description="Whether analyze-event may place qualifying results in confirmed_bets for this sport.")
    supported_markets: list[str] = Field(..., description="Markets the registry recognizes for this sport, such as h2h, spreads, totals, or outrights.")
    supported_props: list[str] = Field(..., description="Prop markets supported by this sport model; empty when props are not connected.")
    required_independent_inputs: list[str] = Field(..., description="Independent data inputs required before this sport can be promoted for confirmed bets.")
    optional_independent_inputs: list[str] = Field(..., description="Additional independent inputs that can improve model quality but are not mandatory.")
    provider_needs: list[str] = Field(..., description="Provider capabilities still needed for market data, projections, injuries, history, and backtesting.")
    recommended_providers: list[str] = Field(..., description="Configured or recommended provider IDs; empty when no provider has been selected.")
    model_components: list[str] = Field(..., description="Pipeline components currently represented by the sport model configuration.")
    officials_module: dict[str, Any] = Field(..., description="Shared officials-context module with the sport-specific official type and betting-edge strength.")
    risk_notes: list[str] = Field(..., description="Sport-specific limitations and governance notes.")
    correlation_rules: list[str] = Field(..., description="Rules for grouping correlated exposure within this sport.")
    log_fields_required: list[str] = Field(..., description="Fields that must be present in logs before model promotion or bet governance review.")
    input_normalizer: Optional[str] = Field(None, description="Shared screenshot/direct input normalizer registered for confirmed-capable sports.")
    screenshot_alias_test_payload: Optional[dict[str, Any]] = Field(None, description="Live-style alias payload used to enforce screenshot normalization parity.")


class SportsModelRegistrySummaryResponse(BaseModel):
    total_sports: int = Field(..., description="Total number of sport configurations returned by the registry.")
    confirmed_bet_enabled_sports: int = Field(..., description="Count of sports currently allowed to produce confirmed_bets.")
    market_derived_only_sports: int = Field(..., description="Count of sports using only market-derived probabilities.")
    not_built_sports: int = Field(..., description="Count of sports that are registered but not built.")


class SportsModelRegistryResponse(BaseModel):
    ok: bool = Field(..., description="True when the registry response was generated successfully.")
    endpoint: str = Field(..., description="Stable Action operation identifier for this registry response.")
    sports: list[SportModelConfigResponse] = Field(..., description="Ordered list of sport model registry configurations.")
    summary: SportsModelRegistrySummaryResponse = Field(..., description="Aggregate counts by eligibility and model level.")
    global_rules: list[str] = Field(..., description="Governance rules that apply to every sport in the registry.")
    error: Optional[str] = Field(None, description="Machine-readable error code, or null on success.")
    detail: Optional[str] = Field(None, description="Human-readable error detail, or null on success.")


class SportAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    ok: bool = False
    endpoint: str = "analyzeSportModel"
    error: Optional[str] = None
    detail: Optional[str] = None
    sport: Optional[Any] = None
    model_name: Optional[str] = None
    model_used: Optional[str] = None
    model_family: Optional[str] = None
    market: Optional[str] = None
    projected_score: Optional[Any] = None
    projected_margin: Optional[Any] = None
    projected_total: Optional[Any] = None
    projected_team_points: Optional[Any] = None
    projected_opponent_points: Optional[Any] = None
    true_probability: Optional[float] = None
    estimated_true_probability: Optional[float] = None
    final_probability: Optional[float] = None
    model_probability: Optional[float] = None
    raw_model_probability: Optional[float] = None
    calibrated_model_probability: Optional[float] = None
    market_anchor_probability: Optional[float] = None
    probability_calibration_applied: bool = False
    probability_sanity_flags: list[str] = []
    probability_cap_reason: Optional[str] = None
    implied_probability: Optional[float] = None
    edge: Optional[float] = None
    edge_percent: Optional[float] = None
    confidence: Optional[Any] = None
    risk: Optional[Any] = None
    risk_level: str
    model_status: Optional[Any] = None
    status: Optional[str] = None
    decision: Optional[str] = None
    partial_model_mode: bool = False
    recommended_unit_size: float
    no_bet_flags: list[str]
    correlation_notes: list[str]
    model_components: list[str]
    missing_inputs: list[str]
    backtest_status: str
    calibration_status: str
    logbook_ready_row: dict[str, Any]
    component_statuses: dict[str, Any]
    advanced_edge_components: dict[str, Any]
    provider_needs: list[str]
    risk_controller: dict[str, Any]
    wee_willie_market_weakness_detector: dict[str, Any]
    social_sentiment_engine: dict[str, Any]
    crowdsourced_signal_engine: dict[str, Any]
    public_bias_detector: dict[str, Any]
    news_velocity_detector: dict[str, Any]
    rumor_risk_filter: dict[str, Any]
    market_narrative_tracker: dict[str, Any]
    sentiment_calibration_status: str
    crowd_signal_calibration_status: str
    sentiment_no_bet_flags: list[str]
    officiating_analysis: dict[str, Any] = {}
    officiating_module_status: Optional[str] = None
    officiating_edge_detected: bool = False
    officiating_adjustment_probability_points: float = 0
    adjusted_true_probability: Optional[float] = None
    affected_markets: list[str] = []
    officiating_confidence: Optional[Any] = None
    officiating_risk_flags: list[str] = []
    officiating_summary: Optional[str] = None
    officiating_no_bet_reason: Optional[str] = None
    officiating_logbook_fields: dict[str, Any] = {}
    confirmed_bets: list[dict[str, Any]] = []
    target_lines: list[dict[str, Any]] = []
    target_props: list[dict[str, Any]] = []
    target_alt_lines: list[dict[str, Any]] = []
    no_bets: list[dict[str, Any]] = []
    best_correlated_parlay: Optional[Any] = None
    value_ranking: list[Any] = []
    risk_ranking: list[Any] = []
    provider_enrichment: dict[str, Any] = {}
    manual_review_required: Optional[Any] = None
    manual_ticket_preview: Optional[dict[str, Any]] = None
    full_board_preview: dict[str, Any]


class ScreenshotAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    ok: bool
    endpoint: str
    partial_model_mode: bool
    parsed_ticket: dict[str, Any]
    provider_enrichment: dict[str, Any]
    model_analysis: dict[str, Any]
    full_board_preview: dict[str, Any]
    missing_inputs: list[Any]
    no_bets: list[dict[str, Any]]
    confirmed_bets: list[dict[str, Any]]
    suggested_stake: Optional[Any] = None
    stake: Optional[Any] = None
    implied_probability: Optional[Any] = None
    confidence: Optional[Any] = None
    decision: Optional[str] = None
    status: Optional[str] = None
    logbook_ready_rows: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None
