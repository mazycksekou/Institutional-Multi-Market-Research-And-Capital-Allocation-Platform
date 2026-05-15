from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

from quant_engine import (
    american_to_decimal,
    edge_percentage,
    expected_value_per_100,
    fair_odds_american_from_probability,
    fractional_kelly_percent,
    full_kelly_percent,
    implied_probability_from_american,
    risk_profile_settings,
    suggested_stake_with_risk_controls,
)


COMPONENT_STATUS_INACTIVE = "inactive_missing_data"
COMPONENT_STATUS_RESEARCH = "research_mode_not_bettable"
COMPONENT_STATUS_ACTIVE = "active"
COMPONENT_STATUSES = frozenset({
    COMPONENT_STATUS_INACTIVE,
    COMPONENT_STATUS_RESEARCH,
    COMPONENT_STATUS_ACTIVE,
})

MODEL_LEVEL_NOT_BUILT = "not_built"
MODEL_LEVEL_MARKET_DERIVED_ONLY = "market_derived_only"
MODEL_LEVEL_PROJECTION_READY = "projection_ready"
MODEL_LEVEL_BLENDED_READY = "blended_ready"
MODEL_LEVEL_FULLY_INDEPENDENT = "fully_independent"

CONFIRMED_BET_ELIGIBLE_LEVELS = frozenset({
    MODEL_LEVEL_PROJECTION_READY,
    MODEL_LEVEL_BLENDED_READY,
    MODEL_LEVEL_FULLY_INDEPENDENT,
})

OFFICIAL_SPORT_KEYS = [
    "baseball_mlb",
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "soccer",
    "icehockey_nhl",
    "tennis",
    "mma_mixed_martial_arts",
    "boxing",
    "golf",
    "formula1",
    "cricket",
    "esports",
]

SPORT_ALIASES = {"egaming": "esports"}

GLOBAL_MODEL_REGISTRY_RULES = [
    "Market-derived-only probabilities cannot create confirmed bets.",
    "Confirmed bets require independent projection inputs.",
    "Confirmed bets require backtest proof, risk approval, and clear no-bet flags.",
    "No sport may be promoted without backtesting and logging.",
    "Provider abstractions are registered but live external APIs are not connected here.",
    "Direct B2B bet execution and sportsbook scraping are disabled.",
]

BASE_COMPONENT_FIELDS = (
    "component_name",
    "component_status",
    "required_inputs",
    "optional_inputs",
    "missing_inputs",
    "data_provider_needs",
    "backtest_requirements",
    "calibration_requirements",
    "no_bet_flags",
    "output_fields",
    "notes",
)

BASE_LOG_FIELDS_REQUIRED = [
    "timestamp",
    "sport_key",
    "event_id",
    "market",
    "selection",
    "sportsbook",
    "odds_american",
    "model_level",
    "probability_type",
    "final_probability",
    "decision",
    "stake",
    "risk_profile",
]

STANDARD_PROVIDER_NEEDS = [
    "sportsbook odds provider for events and prices",
    "independent projection provider",
    "injury or availability provider",
    "historical odds and closing-line dataset",
    "backtesting dataset with settled outcomes",
]

STANDARD_BACKTEST_REQUIREMENTS = [
    "settled outcomes by sport, market, and prop type",
    "closing line value history",
    "probability bucket calibration",
    "minimum sample size by market before activation",
]

STANDARD_CALIBRATION_REQUIREMENTS = [
    "probability calibration by confidence bucket",
    "sport-specific baseline validation",
    "market-specific error tracking",
    "social sentiment calibration",
    "crowdsourced signal calibration",
    "public bias adjustment",
    "rumor risk review",
    "news velocity check",
    "market narrative check",
    "sentiment versus odds movement comparison",
    "sentiment versus model probability comparison",
    "crowd consensus versus sharp market comparison",
]

STANDARD_NO_BET_RULES = [
    "required inputs missing",
    "no independent model probability",
    "no backtest proof",
    "risk controller rejects exposure",
    "correlation check fails",
]

SOCIAL_CROWD_OPTIONAL_INPUTS = [
    "social media sentiment score",
    "crowd consensus percentage",
    "public betting percentage",
    "money percentage",
    "news velocity score",
    "injury rumor flag",
    "lineup rumor flag",
    "beat writer signal",
    "Reddit or forum sentiment",
    "Discord or community signal",
    "Google Trends style interest score",
    "media hype score",
]

SOCIAL_CROWD_MODEL_COMPONENTS = [
    "social_sentiment_engine",
    "crowdsourced_signal_engine",
    "public_bias_detector",
    "news_velocity_detector",
    "rumor_risk_filter",
    "market_narrative_tracker",
]

SOCIAL_CROWD_NO_BET_FLAGS = [
    "social sentiment is extreme but model edge is weak",
    "crowd consensus conflicts with model probability",
    "rumor not confirmed",
    "news velocity spike without verified source",
    "public bias likely inflated price",
    "sentiment data unavailable",
    "crowdsourced signal unavailable",
    "sentiment source quality too low",
    "social signal not backtested",
    "crowd signal not calibrated",
]

SPORT_PROP_INPUTS = {
    "baseball_mlb": ["player projection", "lineup status", "opponent matchup", "park factor", "weather"],
    "basketball_nba": ["minutes projection", "usage", "pace", "defensive matchup", "injury report"],
    "basketball_wnba": ["WNBA minutes projection", "WNBA usage baseline", "pace", "defensive matchup", "injury report"],
    "basketball_ncaab": ["player projection where available", "tempo", "team role", "opponent matchup"],
    "americanfootball_nfl": ["player projection", "snap share", "pace", "injury report", "trench matchup"],
    "americanfootball_ncaaf": ["player projection where available", "team pace", "depth chart", "matchup"],
    "soccer": ["player role", "expected minutes", "xG or xA", "field tilt", "opponent matchup"],
    "icehockey_nhl": ["line assignment", "power play role", "shot projection", "goalie matchup"],
    "tennis": ["serve profile", "return profile", "surface", "fatigue"],
    "mma_mixed_martial_arts": ["fighter stats", "style matchup", "finish history", "fight duration history"],
    "boxing": ["fighter stats", "style matchup", "finish history", "fight duration history"],
    "golf": ["strokes gained splits", "course fit", "weather", "field strength"],
    "formula1": ["driver pace", "constructor strength", "track profile", "weather"],
    "cricket": ["batting order", "bowler matchup", "venue", "pitch condition"],
    "esports": ["game title", "player rating", "team rating", "map pool", "patch or meta version"],
}


def _component(
    name: str,
    required_inputs: list[str],
    *,
    optional_inputs: Optional[list[str]] = None,
    output_fields: Optional[list[str]] = None,
    notes: Optional[list[str]] = None,
    status: str = COMPONENT_STATUS_INACTIVE,
) -> dict[str, Any]:
    if status not in COMPONENT_STATUSES:
        raise ValueError(f"Unsupported component_status: {status}")
    return {
        "component_name": name,
        "component_status": status,
        "required_inputs": list(required_inputs),
        "optional_inputs": list(optional_inputs or []),
        "missing_inputs": list(required_inputs) if status == COMPONENT_STATUS_INACTIVE else [],
        "data_provider_needs": list(STANDARD_PROVIDER_NEEDS),
        "backtest_requirements": list(STANDARD_BACKTEST_REQUIREMENTS),
        "calibration_requirements": list(STANDARD_CALIBRATION_REQUIREMENTS),
        "no_bet_flags": list(STANDARD_NO_BET_RULES) if status != COMPONENT_STATUS_ACTIVE else [],
        "output_fields": list(output_fields or ["watchlist", "target_line", "target_price", "no_bet_flags"]),
        "notes": list(notes or ["Registered architecture component only; live data is not connected."]),
    }


def _props_registry_entry(sport: str, categories: list[str]) -> dict[str, Any]:
    return {
        "sport": sport,
        "prop_categories": list(categories),
        "required_inputs": list(SPORT_PROP_INPUTS[sport]),
        "missing_data_flags": list(SPORT_PROP_INPUTS[sport]),
        "component_status": COMPONENT_STATUS_INACTIVE,
        "notes": "Prop registry is defined, but individual prop models are not activated.",
    }


def _sport(
    sport: str,
    display_name: str,
    model_used: str,
    model_family: str,
    primary_model_type: str,
    supported_markets: list[str],
    supported_prop_categories: list[str],
    required_inputs: list[str],
    optional_inputs: list[str],
    model_components: list[str],
    simulation_method: str,
    correlation_notes: list[str],
    *,
    status: str = "architecture_registered",
    model_level: str = MODEL_LEVEL_NOT_BUILT,
    component_status: str = COMPONENT_STATUS_INACTIVE,
    sport_parameters: Optional[dict[str, Any]] = None,
    supported_game_titles: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "sport_key": sport,
        "sport": sport,
        "display_name": display_name,
        "status": status,
        "model_level": model_level,
        "component_status": component_status,
        "confirmed_bets_allowed": False,
        "model_used": model_used,
        "model_family": model_family,
        "primary_model_type": primary_model_type,
        "supported_markets": list(supported_markets),
        "supported_props": list(supported_prop_categories),
        "supported_prop_categories": list(supported_prop_categories),
        "required_inputs": list(required_inputs),
        "required_independent_inputs": list(required_inputs),
        "optional_inputs": list(optional_inputs) + list(SOCIAL_CROWD_OPTIONAL_INPUTS),
        "optional_independent_inputs": list(optional_inputs) + list(SOCIAL_CROWD_OPTIONAL_INPUTS),
        "missing_inputs": list(required_inputs),
        "data_provider_needs": list(STANDARD_PROVIDER_NEEDS),
        "provider_needs": list(STANDARD_PROVIDER_NEEDS),
        "recommended_providers": [],
        "model_components": list(model_components) + list(SOCIAL_CROWD_MODEL_COMPONENTS),
        "simulation_method": simulation_method,
        "correlation_notes": list(correlation_notes),
        "correlation_rules": list(correlation_notes),
        "backtest_requirements": list(STANDARD_BACKTEST_REQUIREMENTS),
        "calibration_requirements": list(STANDARD_CALIBRATION_REQUIREMENTS),
        "no_bet_rules": list(STANDARD_NO_BET_RULES) + list(SOCIAL_CROWD_NO_BET_FLAGS),
        "risk_notes": [
            "Confirmed bets disabled until independent inputs, backtests, calibration, and risk approval exist."
        ],
        "output_fields": [
            "target_lines",
            "target_props",
            "target_alt_lines",
            "no_bets",
            "missing_inputs",
            "manual_review_required",
        ],
        "props_registry": _props_registry_entry(sport, supported_prop_categories),
        "sport_parameters": deepcopy(sport_parameters or {}),
        "supported_game_titles": list(supported_game_titles or []),
        "log_fields_required": list(BASE_LOG_FIELDS_REQUIRED),
    }


SPORT_MODEL_REGISTRY = [
    _sport(
        "baseball_mlb",
        "MLB",
        "negative_binomial_run_model",
        "Negative Binomial run model family",
        "negative_binomial",
        ["moneyline", "run line", "totals", "team totals", "first 5 moneyline", "first 5 run line", "first 5 totals"],
        ["pitcher strikeouts", "pitcher outs recorded", "pitcher earned runs", "hits allowed", "batter hits", "total bases", "RBIs", "runs", "home runs", "stolen bases"],
        ["team run distribution", "probable pitchers", "bullpen usage", "park factor", "weather", "lineups"],
        ["umpire assignment", "Markov run expectancy", "bat tracking", "pitch physics"],
        ["first 5 model", "full game model", "pitcher adjustment", "bullpen adjustment", "park factor", "weather adjustment", "lineup adjustment", "umpire adjustment placeholder", "optional Markov run expectancy later"],
        "negative binomial run simulation",
        ["Correlate pitcher strikeouts with opponent team total and first 5 markets."],
        model_level=MODEL_LEVEL_MARKET_DERIVED_ONLY,
    ),
    _sport(
        "basketball_nba",
        "NBA",
        "possession_expected_score_model",
        "Possession based expected score model",
        "possession_expected_score",
        ["moneyline", "spread", "totals", "team totals", "first half", "first quarter", "live markets"],
        ["points", "rebounds", "assists", "PRA", "threes", "steals", "blocks", "turnovers", "double double", "triple double"],
        ["pace", "offensive rating", "defensive rating", "Four Factors", "player usage", "minutes projection", "injury report"],
        ["on off adjustment", "shot quality", "fatigue", "rest", "travel"],
        ["pace", "offensive rating", "defensive rating", "Four Factors", "player usage", "minutes projection", "injury and on off adjustment", "shot quality engine registered now", "fatigue and rest adjustment"],
        "possession simulation",
        ["Correlate player PRA, team totals, pace, and same-game spread scripts."],
        sport_parameters={"league_baseline": "NBA", "pace_assumption": "NBA specific", "rotation_assumption": "NBA rotation depth"},
    ),
    _sport(
        "basketball_wnba",
        "WNBA",
        "wnba_possession_expected_score_model",
        "Basketball possession based expected score model",
        "possession_expected_score",
        ["moneyline", "spread", "totals", "team totals", "first half", "first quarter", "live markets"],
        ["points", "rebounds", "assists", "PRA", "threes", "steals", "blocks", "turnovers"],
        ["WNBA pace baseline", "WNBA offensive rating", "WNBA defensive rating", "Four Factors", "WNBA usage distribution", "WNBA minutes projection", "injury report"],
        ["shot quality", "fatigue", "rest", "travel", "market liquidity"],
        ["WNBA specific baselines", "WNBA specific pace assumptions", "WNBA specific rotation assumptions", "WNBA specific usage distribution", "WNBA specific injury sensitivity", "WNBA specific prop volatility", "WNBA specific market liquidity flags", "Four Factors", "minutes projection", "shot quality engine registered now"],
        "WNBA possession simulation",
        ["WNBA props require liquidity flags before staking because limits and price quality differ from NBA."],
        sport_parameters={
            "league_baseline": "WNBA",
            "pace_assumption": "WNBA specific pace baseline",
            "rotation_assumption": "WNBA specific rotation depth",
            "usage_distribution": "WNBA specific usage distribution",
            "injury_sensitivity": "WNBA specific injury sensitivity",
            "prop_volatility": "WNBA specific prop volatility",
            "market_liquidity": "WNBA specific market liquidity flags",
        },
    ),
    _sport(
        "basketball_ncaab",
        "College Basketball",
        "possession_tempo_model",
        "Possession based tempo model",
        "possession_tempo",
        ["moneyline", "spread", "totals", "team totals", "first half", "live markets"],
        ["points", "rebounds", "assists", "threes where available"],
        ["tempo", "Four Factors", "home court", "conference strength", "schedule strength", "team experience"],
        ["Bayesian shrinkage", "travel", "rest"],
        ["tempo", "Four Factors", "home court", "conference strength", "schedule strength", "Bayesian shrinkage", "team experience", "travel and rest"],
        "tempo-adjusted possession simulation",
        ["Team totals and spreads depend heavily on tempo and conference strength."],
    ),
    _sport(
        "americanfootball_nfl",
        "NFL",
        "drive_expected_points_model",
        "Drive based expected points model",
        "drive_expected_points",
        ["moneyline", "spread", "totals", "team totals", "first half", "first quarter", "live markets"],
        ["passing yards", "passing touchdowns", "interceptions", "completions", "attempts", "rushing yards", "rushing attempts", "receiving yards", "receptions", "anytime touchdown", "first touchdown", "sacks", "kicking points"],
        ["EPA", "success rate", "pace", "QB adjustment", "red zone efficiency", "weather", "injuries"],
        ["garbage time filtering", "offensive line adjustment", "defensive line adjustment"],
        ["EPA", "success rate", "pace", "QB adjustment", "red zone efficiency", "weather", "injuries", "garbage time filtering", "offensive line adjustment registered now", "defensive line adjustment registered now", "football trench engine registered now"],
        "drive simulation",
        ["QB passing over with WR receiving over; bad offensive line with opposing sacks over."],
    ),
    _sport(
        "americanfootball_ncaaf",
        "College Football",
        "college_drive_expected_points_model",
        "College drive based expected points model",
        "drive_expected_points",
        ["moneyline", "spread", "totals", "team totals", "first half", "first quarter", "live markets"],
        ["passing yards", "rushing yards", "receiving yards", "touchdowns where available"],
        ["college EPA or EPA proxy", "power ratings", "pace", "explosiveness", "success rate", "conference strength", "QB adjustment"],
        ["variance controls", "weather", "injuries where available"],
        ["college EPA or EPA proxy", "power ratings", "pace", "explosiveness", "success rate", "conference strength", "variance controls", "QB adjustment", "weather", "injuries where available", "football trench engine registered now"],
        "college drive simulation",
        ["College variance requires tighter exposure caps for correlated sides, totals, and player props."],
    ),
    _sport(
        "soccer",
        "Soccer",
        "dixon_coles_bivariate_poisson_model",
        "Poisson with Dixon Coles and Bivariate Poisson components",
        "poisson_with_score_dependence",
        ["1x2", "moneyline where applicable", "draw no bet", "double chance", "Asian handicap", "totals", "team totals", "both teams to score", "correct score", "next goal", "live markets"],
        ["anytime scorer", "first goal scorer", "shots", "shots on target", "assists", "cards", "corners", "saves"],
        ["team attack strength", "team defense strength", "time decay weights", "league baseline"],
        ["xG adjustment", "field tilt", "post shot xG"],
        ["Poisson baseline", "Dixon Coles low score correction", "Bivariate Poisson score dependence", "time decay weighting", "optional xG adjustment", "field tilt engine registered now", "post shot xG engine registered now", "Monte Carlo simulation"],
        "Monte Carlo simulation",
        ["Field tilt with soccer corners; xG pressure with team total and next goal markets."],
    ),
    _sport(
        "icehockey_nhl",
        "NHL",
        "correlated_goal_model",
        "Poisson or correlated Poisson goal model",
        "correlated_poisson",
        ["moneyline", "puck line", "totals", "team totals", "periods", "live markets"],
        ["goals", "assists", "points", "shots on goal", "blocked shots", "goalie saves", "anytime goal scorer", "first goal scorer"],
        ["team goal rates", "goalie starter", "special teams", "period lambdas", "time decay weights"],
        ["Royal Road pass data", "pre shot movement", "goalie stress"],
        ["Poisson or correlated Poisson goal model", "Bivariate Poisson or correlated goal dependence", "goalie adjustment", "special teams adjustment", "period specific lambdas", "time decay weighting", "Royal Road and pre shot movement engine registered now", "Monte Carlo simulation"],
        "Monte Carlo simulation",
        ["Royal Road offense with NHL team total over and player shots."],
    ),
    _sport(
        "tennis",
        "Tennis",
        "serve_return_point_simulation",
        "Serve return model",
        "point_game_set_simulation",
        ["moneyline", "game spread", "total games", "set betting", "first set winner", "live markets"],
        ["aces", "double faults", "total games", "player games", "set handicap", "break points where available"],
        ["serve hold percentage", "return points won", "surface", "fatigue", "Elo", "recent form"],
        ["tournament context", "weather where relevant"],
        ["serve return model", "point game set simulation", "surface adjustment", "fatigue adjustment", "Elo", "player form", "tournament context"],
        "point game set simulation",
        ["Aces, service holds, and total games are strongly related."],
    ),
    _sport(
        "mma_mixed_martial_arts",
        "MMA",
        "combat_classification_model",
        "Combat classification model family",
        "classification",
        ["moneyline", "method", "round props", "goes distance", "does not go distance"],
        ["KO TKO", "submission", "decision", "round group", "fight duration"],
        ["striking stats", "grappling stats", "takedown defense", "reach", "stance", "age", "fight duration history", "finish history", "style matchup"],
        ["cardio", "camp context"],
        ["moneyline classifier", "finish method classifier", "KO TKO probability", "submission probability", "decision probability", "round props", "fight duration", "fighter style matchup", "reach, stance, age, cardio, grappling, striking, takedown defense placeholders"],
        "classification with duration model",
        ["Method, distance, and round group are highly correlated."],
    ),
    _sport(
        "boxing",
        "Boxing",
        "boxing_combat_classification_model",
        "Combat classification model family",
        "classification",
        ["moneyline", "method", "round props", "goes distance", "does not go distance"],
        ["KO TKO", "decision", "draw", "round group", "fight duration"],
        ["striking stats", "reach", "stance", "age", "power", "durability", "pace", "fight duration history", "finish history", "style matchup"],
        ["draw prior", "judging context"],
        ["moneyline classifier", "KO TKO probability", "decision probability", "draw probability placeholder", "round props", "fight duration", "fighter style matchup", "reach, stance, age, power, durability, pace placeholders"],
        "classification with duration model",
        ["Decision, draw, and distance prices require correlated review."],
    ),
    _sport(
        "golf",
        "Golf",
        "strokes_gained_simulation",
        "Strokes gained simulation",
        "strokes_gained",
        ["outrights", "matchups", "top 5", "top 10", "top 20", "make cut", "first round leader"],
        ["top finish", "make cut", "matchup", "round score", "birdies where available"],
        ["strokes gained off tee", "strokes gained approach", "strokes gained around green", "strokes gained putting", "course fit", "weather", "field strength"],
        ["recent form", "course history"],
        ["course fit", "driving distance", "accuracy", "approach", "around the green", "putting", "recent form", "weather", "field strength"],
        "strokes gained simulation",
        ["Outrights, top finish ladders, and matchup exposure should be grouped by golfer."],
    ),
    _sport(
        "formula1",
        "Formula 1",
        "race_simulation_model",
        "Race simulation",
        "race_simulation",
        ["race winner", "podium", "points finish", "driver head to head", "qualifying head to head", "fastest lap", "outrights"],
        ["podium", "top six", "points finish", "qualifying head to head", "race head to head", "fastest lap"],
        ["qualifying pace", "race pace", "tire degradation", "pit strategy", "track position", "safety car probability", "weather"],
        ["constructor strength", "driver form"],
        ["qualifying pace", "race pace", "tire degradation", "pit strategy", "safety car probability", "track position", "constructor strength", "driver form", "weather"],
        "race simulation",
        ["Podium, top six, and points finish ladders are positively correlated."],
    ),
    _sport(
        "cricket",
        "Cricket",
        "pitch_toss_venue_model",
        "Pitch toss innings model family",
        "pitch_toss_innings",
        ["match winner", "innings runs", "totals", "team totals", "player runs", "player wickets"],
        ["player runs", "player wickets", "sixes", "fours", "top batter", "innings runs"],
        ["venue", "pitch condition", "toss result", "batting order", "bowling matchup", "run rate", "wicket rate", "weather"],
        ["format", "dew point", "boundary dimensions"],
        ["run rate model", "wicket rate model", "innings simulation", "toss impact", "venue impact", "pitch condition", "weather", "batting order", "bowler matchup"],
        "innings simulation",
        ["Toss, pitch, innings runs, and player runs can change together."],
    ),
    _sport(
        "esports",
        "Esports",
        "game_specific_esports_router",
        "Game specific esports model family",
        "game_title_routing",
        ["match winner", "map winner", "map handicap", "total maps", "round handicap", "round totals", "live markets"],
        ["kills", "assists", "deaths", "KDA", "headshots", "objectives", "first blood", "maps played", "rounds won where available"],
        ["game title", "team rating", "player rating", "roster changes", "patch or meta version", "map pool", "pick ban or veto data", "recent form", "region strength", "server region or latency placeholder"],
        ["side selection", "opponent matchup", "market liquidity"],
        ["game title routing placeholder", "team rating", "player rating", "roster changes", "patch or meta changes", "map pool", "side selection", "pick ban or veto process", "recent form", "opponent matchup", "region strength", "latency or server region placeholder", "market liquidity warning"],
        "game-specific simulation or classification by title",
        ["Do not use one generic esports model for every game title; route by game title first."],
        supported_game_titles=["Counter Strike", "League of Legends", "Dota 2", "Valorant", "Call of Duty", "Overwatch", "Rocket League", "Rainbow Six Siege", "EA FC", "NBA 2K", "Madden"],
    ),
]

_REGISTRY_BY_KEY = {sport["sport_key"]: sport for sport in SPORT_MODEL_REGISTRY}


ADVANCED_EDGE_COMPONENTS = {
    "football_trench_engine": _component(
        "football_trench_engine",
        ["offensive line grades", "defensive line grades", "pressure rate", "sack rate", "pass block win rate", "run block win rate", "injury reports", "backup lineman status"],
        optional_inputs=["tracking coordinates", "pocket time", "pocket area", "defensive line penetration"],
        notes=["For NFL and NCAAF."],
    ),
    "basketball_shot_quality_fatigue_engine": _component(
        "basketball_shot_quality_fatigue_engine",
        ["shot location", "defender distance", "closest defender", "pace", "rest days", "travel", "minutes load", "injury report", "usage"],
        optional_inputs=["optical tracking", "closeout speed", "biomechanical load"],
        notes=["For NBA and WNBA."],
    ),
    "mlb_pitch_physics_bat_tracking_engine": _component(
        "mlb_pitch_physics_bat_tracking_engine",
        ["pitcher handedness", "pitch mix", "velocity", "spin rate", "movement", "release point", "batter handedness", "barrel rate", "hard hit rate", "park factor", "weather"],
        optional_inputs=["bat speed", "seam shifted wake indicators"],
    ),
    "soccer_field_tilt_post_shot_xg_engine": _component(
        "soccer_field_tilt_post_shot_xg_engine",
        ["final third possession", "final third passes", "xG", "shots", "shots on target", "keeper data"],
        optional_inputs=["post shot xG", "field tilt", "progressive passes", "pressure data"],
    ),
    "nhl_royal_road_goalie_stress_engine": _component(
        "nhl_royal_road_goalie_stress_engine",
        ["shot location", "pre shot movement", "goalie starter", "goalie rest", "power play rate", "penalty kill rate"],
        optional_inputs=["Royal Road pass data", "slot passes", "rebound chances"],
    ),
    "tennis_serve_return_engine": _component(
        "tennis_serve_return_engine",
        ["serve hold percentage", "return points won", "surface", "fatigue", "Elo", "recent form"],
    ),
    "combat_sports_phase_engine": _component(
        "combat_sports_phase_engine",
        ["striking stats", "grappling stats", "takedown defense", "reach", "stance", "age", "fight duration history", "finish history", "style matchup"],
        notes=["For UFC and boxing."],
    ),
    "golf_strokes_gained_engine": _component(
        "golf_strokes_gained_engine",
        ["strokes gained off tee", "strokes gained approach", "strokes gained around green", "strokes gained putting", "course fit", "weather", "field strength"],
    ),
    "formula1_race_simulation_engine": _component(
        "formula1_race_simulation_engine",
        ["qualifying pace", "race pace", "tire degradation", "pit strategy", "track position", "safety car probability", "weather"],
    ),
    "cricket_pitch_toss_innings_engine": _component(
        "cricket_pitch_toss_innings_engine",
        ["venue", "pitch condition", "toss result", "batting order", "bowling matchup", "run rate", "wicket rate", "weather"],
    ),
    "esports_game_specific_engine": _component(
        "esports_game_specific_engine",
        ["game title", "team rating", "player rating", "roster changes", "patch or meta version", "map pool", "pick ban or veto data", "recent form", "region strength", "server region or latency placeholder"],
    ),
}

PROVIDER_ABSTRACTIONS = [
    {
        "provider_name": provider_type,
        "provider_type": provider_type,
        "status": "not_configured",
        "supported_sports": list(OFFICIAL_SPORT_KEYS),
        "supported_markets": ["architecture_placeholder"],
        "latency_placeholder": None,
        "last_update_timestamp": None,
        "odds_normalization_status": "not_connected",
        "best_price_status": "not_connected",
        "consensus_status": "not_connected",
        "no_vig_status": "not_connected",
        "provider_health_status": "not_connected",
        "missing_credentials_flag": True,
        "data_provider_needs": list(STANDARD_PROVIDER_NEEDS),
    }
    for provider_type in [
        "sportsbook_odds",
        "sharp_reference",
        "exchange",
        "projection_provider",
        "injury_provider",
        "weather_provider",
        "tracking_data_provider",
        "historical_odds_provider",
        "backtesting_dataset",
    ]
]

ALT_LINE_LADDER_REGISTRY = {
    "alternate_spreads": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["spread ladder prices", "base spread probability"]},
    "alternate_totals": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["total ladder prices", "base total probability"]},
    "team_total_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["team total ladder prices", "team scoring distribution"]},
    "player_prop_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["player prop ladder prices", "player projection distribution"]},
    "strikeout_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["strikeout ladder prices", "pitcher strikeout distribution"]},
    "points_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["points ladder prices", "player points distribution"]},
    "receiving_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["receiving ladder prices", "receiver yardage distribution"]},
    "shots_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["shots ladder prices", "shot attempt distribution"]},
    "top_finish_ladders": {"component_status": COMPONENT_STATUS_INACTIVE, "required_inputs": ["top finish prices", "finish position simulation"]},
}

CORRELATION_SGP_FOUNDATION = {
    "correlation_group": None,
    "same_game_flag": False,
    "positive_correlation_notes": [
        "QB passing over with WR receiving over",
        "bad offensive line with opposing sacks over",
        "pitcher strikeouts over with opponent team total under",
        "field tilt with soccer corners",
        "Royal Road offense with NHL team total over",
    ],
    "negative_correlation_notes": [],
    "conflict_flags": ["correlation model not calibrated"],
    "sgp_allowed": False,
    "sgp_no_bet_reason": "Live SGP pricing and correlation scoring are not connected.",
    "max_correlated_exposure": 0,
}

BACKTESTING_CALIBRATION_FOUNDATION = {
    "backtest_status": "not_started",
    "calibration_status": "not_started",
    "sample_size": 0,
    "roi": None,
    "yield": None,
    "clv": None,
    "closing_line_available": False,
    "probability_bucket": None,
    "confidence_bucket": None,
    "sport": None,
    "market": None,
    "prop_type": None,
    "model_version": "architecture_foundation_v1",
    "not_enough_data_flag": True,
}


def normalize_sport_key(sport_key: str) -> str:
    raw = (sport_key or "").strip()
    return SPORT_ALIASES.get(raw, raw)


def _validate_registry() -> None:
    if len(_REGISTRY_BY_KEY) != len(SPORT_MODEL_REGISTRY):
        raise ValueError("SPORT_MODEL_REGISTRY contains duplicate sport_key values")
    if [sport["sport_key"] for sport in SPORT_MODEL_REGISTRY] != OFFICIAL_SPORT_KEYS:
        raise ValueError("SPORT_MODEL_REGISTRY must match official sport order")
    for sport in SPORT_MODEL_REGISTRY:
        for required_field in (
            "sport",
            "display_name",
            "model_used",
            "model_family",
            "primary_model_type",
            "supported_markets",
            "supported_prop_categories",
            "required_inputs",
            "optional_inputs",
            "model_components",
            "simulation_method",
            "correlation_notes",
            "backtest_requirements",
            "calibration_requirements",
            "no_bet_rules",
        ):
            if required_field not in sport:
                raise ValueError(f"{sport.get('sport_key')} is missing {required_field}")


def get_sport_model_config(sport_key: str) -> Optional[dict[str, Any]]:
    config = _REGISTRY_BY_KEY.get(normalize_sport_key(sport_key))
    return deepcopy(config) if config else None


def is_supported_sport(sport_key: str) -> bool:
    return normalize_sport_key(sport_key) in _REGISTRY_BY_KEY


def confirmed_bets_allowed(sport_key: str) -> bool:
    config = _REGISTRY_BY_KEY.get(normalize_sport_key(sport_key))
    return bool(config and config.get("confirmed_bets_allowed"))


def get_required_inputs(sport_key: str) -> Optional[list[str]]:
    config = _REGISTRY_BY_KEY.get(normalize_sport_key(sport_key))
    return deepcopy(config.get("required_inputs")) if config else None


def get_supported_markets(sport_key: str) -> Optional[list[str]]:
    config = _REGISTRY_BY_KEY.get(normalize_sport_key(sport_key))
    return deepcopy(config.get("supported_markets")) if config else None


def classify_model_level(sport_key: str) -> Optional[str]:
    config = _REGISTRY_BY_KEY.get(normalize_sport_key(sport_key))
    return str(config.get("model_level")) if config else None


def get_registered_architecture_components() -> dict[str, Any]:
    return {
        "advanced_edge_components": deepcopy(ADVANCED_EDGE_COMPONENTS),
        "social_crowd_calibration_components": build_social_crowd_calibration_layer({}),
        "provider_abstractions": deepcopy(PROVIDER_ABSTRACTIONS),
        "risk_controller": build_risk_controller(),
        "correlation_sgp": deepcopy(CORRELATION_SGP_FOUNDATION),
        "alt_line_ladder_registry": deepcopy(ALT_LINE_LADDER_REGISTRY),
        "backtesting_calibration": deepcopy(BACKTESTING_CALIBRATION_FOUNDATION),
        "wee_willie_market_weakness_detector": build_wee_willie_market_weakness_detector({}),
    }


def get_sports_model_registry_response() -> dict[str, Any]:
    sports = deepcopy(SPORT_MODEL_REGISTRY)
    return {
        "ok": True,
        "endpoint": "getSportsModelRegistry",
        "sports": sports,
        "summary": {
            "total_sports": len(sports),
            "confirmed_bet_enabled_sports": 0,
            "market_derived_only_sports": sum(
                1 for sport in sports if sport["model_level"] == MODEL_LEVEL_MARKET_DERIVED_ONLY
            ),
            "not_built_sports": sum(1 for sport in sports if sport["model_level"] == MODEL_LEVEL_NOT_BUILT),
        },
        "global_rules": list(GLOBAL_MODEL_REGISTRY_RULES),
        "architecture_components": get_registered_architecture_components(),
        "error": None,
        "detail": None,
    }


def build_risk_controller(
    bankroll: Optional[float] = None,
    unit_size: Optional[float] = None,
    risk_profile: str = "conservative",
) -> dict[str, Any]:
    bankroll_value = float(bankroll or 0)
    unit_value = float(unit_size or 0)
    profile = risk_profile_settings(risk_profile)
    recommended_unit = unit_value if unit_value > 0 else round(bankroll_value * 0.01, 2) if bankroll_value else 0
    return {
        "bankroll": bankroll_value,
        "unit_size": unit_value,
        "max_stake_cap": round(bankroll_value * profile["max_bankroll_pct"], 2) if bankroll_value else 0,
        "sport_exposure_cap": round(bankroll_value * 0.08, 2) if bankroll_value else 0,
        "market_exposure_cap": round(bankroll_value * 0.04, 2) if bankroll_value else 0,
        "event_exposure_cap": round(bankroll_value * 0.03, 2) if bankroll_value else 0,
        "correlation_group_exposure_cap": round(bankroll_value * 0.02, 2) if bankroll_value else 0,
        "drawdown_status": "unknown",
        "risk_profile": profile["risk_profile"],
        "recommended_unit_size": recommended_unit,
        "risk_flags": ["risk controller foundation only", "no exposure ledger connected"],
        "manual_override_flag": False,
        "no_bet_if_over_limit": True,
    }


def _calibration_component(name: str, input_stats: dict[str, Any], required_inputs: list[str]) -> dict[str, Any]:
    missing = [field for field in required_inputs if input_stats.get(field) is None]
    status = COMPONENT_STATUS_INACTIVE if missing else COMPONENT_STATUS_RESEARCH
    return _component(
        name,
        required_inputs,
        optional_inputs=SOCIAL_CROWD_OPTIONAL_INPUTS,
        output_fields=["signal_status", "signal_summary", "calibration_status", "no_bet_flags", "manual_review_required"],
        notes=[
            "Calibration check and balance only.",
            "Social sentiment and crowdsourcing cannot independently create confirmed bets.",
        ],
        status=status,
    ) | {
        "missing_inputs": missing,
        "signal_status": "manual_review_required" if missing else "available_for_calibration_only",
        "calibration_status": "not_calibrated",
    }


def build_social_crowd_calibration_layer(input_stats: dict[str, Any]) -> dict[str, Any]:
    sentiment_score = input_stats.get("social media sentiment score")
    crowd_consensus = input_stats.get("crowd consensus percentage")
    public_pct = input_stats.get("public betting percentage")
    money_pct = input_stats.get("money percentage")
    news_velocity = input_stats.get("news velocity score")
    model_probability = input_stats.get("sport_model_probability") or input_stats.get("true_probability")
    edge = input_stats.get("edge")
    flags: list[str] = []

    if sentiment_score is None:
        flags.append("sentiment data unavailable")
    if crowd_consensus is None:
        flags.append("crowdsourced signal unavailable")
    if input_stats.get("sentiment source quality") == "low":
        flags.append("sentiment source quality too low")
    if not input_stats.get("social_signal_backtested"):
        flags.append("social signal not backtested")
    if not input_stats.get("crowd_signal_calibrated"):
        flags.append("crowd signal not calibrated")
    if input_stats.get("injury rumor flag") or input_stats.get("lineup rumor flag"):
        if not input_stats.get("rumor_verified"):
            flags.append("rumor not confirmed")
    if news_velocity is not None and float(news_velocity) >= 80 and not input_stats.get("verified_news_source"):
        flags.append("news velocity spike without verified source")
    if public_pct is not None and money_pct is not None and float(public_pct) >= 70 and float(money_pct) < float(public_pct):
        flags.append("public bias likely inflated price")
    if sentiment_score is not None and edge is not None and abs(float(sentiment_score)) >= 80 and float(edge) < 2:
        flags.append("social sentiment is extreme but model edge is weak")
    if crowd_consensus is not None and model_probability is not None:
        crowd_probability = float(crowd_consensus) / 100 if float(crowd_consensus) > 1 else float(crowd_consensus)
        if abs(crowd_probability - float(model_probability)) >= 0.12:
            flags.append("crowd consensus conflicts with model probability")

    if any(flag in flags for flag in [
        "crowd consensus conflicts with model probability",
        "public bias likely inflated price",
        "social sentiment is extreme but model edge is weak",
    ]):
        support_status = "conflicts_with_model"
    elif flags:
        support_status = "requires_manual_review"
    else:
        support_status = "supports_model"

    explanation = {
        "support_status": support_status,
        "summary": (
            "Social and crowd data conflict with model/risk assumptions."
            if support_status == "conflicts_with_model"
            else "Social and crowd data require manual review before any promotion."
            if support_status == "requires_manual_review"
            else "Social and crowd data are available and do not create a calibration red flag."
        ),
        "standalone_bet_reason_allowed": False,
    }

    components = {
        "social_sentiment_engine": _calibration_component("social_sentiment_engine", input_stats, ["social media sentiment score"]),
        "crowdsourced_signal_engine": _calibration_component("crowdsourced_signal_engine", input_stats, ["crowd consensus percentage"]),
        "public_bias_detector": _calibration_component("public_bias_detector", input_stats, ["public betting percentage", "money percentage"]),
        "news_velocity_detector": _calibration_component("news_velocity_detector", input_stats, ["news velocity score", "verified_news_source"]),
        "rumor_risk_filter": _calibration_component("rumor_risk_filter", input_stats, ["injury rumor flag", "lineup rumor flag", "rumor_verified"]),
        "market_narrative_tracker": _calibration_component("market_narrative_tracker", input_stats, ["media hype score", "beat writer signal"]),
    }
    for component in components.values():
        component["signal_explanation"] = explanation
        component["no_bet_flags"] = list(flags)
    return {
        **components,
        "sentiment_calibration_status": "not_calibrated" if "social signal not backtested" in flags else "calibration_check_available",
        "crowd_signal_calibration_status": "not_calibrated" if "crowd signal not calibrated" in flags else "calibration_check_available",
        "sentiment_no_bet_flags": flags,
        "social_crowd_signal_explanation": explanation,
    }


def build_manual_ticket(payload: dict[str, Any], suggested_stake: Optional[float]) -> dict[str, Any]:
    event = payload.get("event_id") or "manual_review_event"
    market = payload.get("market")
    selection = payload.get("selection") or payload.get("player_name") or payload.get("home_team")
    return {
        "manual_ticket_id": f"manual-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "sportsbook": payload.get("sportsbook"),
        "event": event,
        "market": market,
        "selection": selection,
        "line": payload.get("line"),
        "odds": payload.get("odds_american"),
        "minimum_playable_odds": payload.get("odds_american"),
        "suggested_stake": suggested_stake or 0,
        "expires_at": "placeholder",
        "status": "manual_review_required",
        "logbook_ready_row": {
            "event": event,
            "market": market,
            "selection": selection,
            "odds_american": payload.get("odds_american"),
            "stake": suggested_stake or 0,
            "status": "manual_review_required",
        },
    }


def build_wee_willie_market_weakness_detector(payload: dict[str, Any]) -> dict[str, Any]:
    required = [
        "sportsbook odds",
        "market type",
        "selection",
        "line",
        "price",
        "market consensus",
        "no vig probability",
        "sport model probability",
        "injury or availability context",
        "team or player context",
        "recent form",
        "market movement",
        "closing line reference if available",
    ]
    key_map = {
        "sportsbook odds": "odds_american",
        "market type": "market",
        "selection": "selection",
        "line": "line",
        "price": "odds_american",
        "market consensus": "market_consensus",
        "no vig probability": "no_vig_probability",
        "sport model probability": "sport_model_probability",
        "injury or availability context": "injury_or_availability_context",
        "team or player context": "team_or_player_context",
        "recent form": "recent_form",
        "market movement": "market_movement",
        "closing line reference if available": "closing_line_reference",
    }
    missing = [label for label in required if payload.get(key_map[label]) is None]
    status = COMPONENT_STATUS_INACTIVE if missing else COMPONENT_STATUS_RESEARCH
    no_bet_flags = []
    if missing:
        no_bet_flags.append("required inputs missing")
    if payload.get("sport_model_probability") is None:
        no_bet_flags.append("no independent model probability")
    no_bet_flags.extend([
        "line movement alone cannot confirm bet",
        "mismatch explanation required",
        "backtest proof required",
        "risk controller approval required",
        "correlation check required",
    ])
    return {
        "component_name": "wee_willie_market_weakness_detector",
        "component_status": status,
        "required_inputs": required,
        "optional_inputs": [
            "sharp book reference",
            "public book reference",
            "bet percentage",
            "money percentage",
            "steam move data",
            "injury timing",
            "news timing",
            "lineup confirmation",
            "weather",
            "pace",
            "matchup weakness",
            "derivative market prices",
            "alt line ladder prices",
            "prop prices",
        ],
        "missing_inputs": missing,
        "data_provider_needs": list(STANDARD_PROVIDER_NEEDS),
        "backtest_requirements": list(STANDARD_BACKTEST_REQUIREMENTS),
        "calibration_requirements": list(STANDARD_CALIBRATION_REQUIREMENTS),
        "no_bet_flags": no_bet_flags,
        "output_fields": [
            "watchlist",
            "target_line",
            "target_price",
            "market_weakness_reason",
            "affected_markets",
            "do_not_bet_reason",
            "manual_review_required",
        ],
        "notes": [
            "Detects when the broad market assumption does not fit specific game conditions.",
            "Must not return confirmed_bet unless inputs, model probability, backtest proof, risk approval, and correlation checks pass.",
        ],
        "book_assumption": payload.get("book_assumption"),
        "specific_mismatch": payload.get("specific_mismatch"),
        "affected_market": payload.get("market"),
        "affected_derivative_markets": [],
        "affected_props": [],
        "affected_alt_lines": [],
        "market_consensus": payload.get("market_consensus"),
        "sharp_reference_price": payload.get("sharp_reference_price"),
        "public_price": payload.get("public_price"),
        "no_vig_probability": payload.get("no_vig_probability"),
        "model_probability": payload.get("sport_model_probability"),
        "true_probability": payload.get("true_probability"),
        "implied_probability": payload.get("implied_probability"),
        "edge": payload.get("edge"),
        "confidence": payload.get("confidence"),
        "risk_level": payload.get("risk_level"),
        "unit_size": payload.get("unit_size"),
        "correlation_notes": list(CORRELATION_SGP_FOUNDATION["positive_correlation_notes"]),
        "logbook_ready_row": {},
        "watchlist": [] if missing else [payload.get("selection")],
        "target_line": None,
        "target_price": None,
        "market_weakness_reason": None,
        "affected_markets": [],
        "do_not_bet_reason": "; ".join(no_bet_flags),
        "manual_review_required": True,
    }


def _component_status(required_inputs: list[str], input_stats: dict[str, Any]) -> tuple[str, list[str]]:
    missing = [field for field in required_inputs if input_stats.get(field) is None]
    if missing:
        return COMPONENT_STATUS_INACTIVE, missing
    if not input_stats.get("backtest_proof"):
        return COMPONENT_STATUS_RESEARCH, []
    return COMPONENT_STATUS_ACTIVE, []


def analyze_sport_model(payload: dict[str, Any]) -> dict[str, Any]:
    sport = normalize_sport_key(payload.get("sport", ""))
    config = get_sport_model_config(sport)
    market = payload.get("market")
    input_stats = payload.get("input_stats") or {}
    if not config:
        return _unsupported_sport_response(payload)

    component_status, missing_inputs = _component_status(config["required_inputs"], input_stats)
    backtest_status = "passed" if input_stats.get("backtest_proof") else "not_started"
    calibration_status = "passed" if input_stats.get("calibration_proof") else "not_started"
    implied_probability = None
    true_probability = input_stats.get("true_probability") or input_stats.get("sport_model_probability")
    edge = None
    suggested = 0.0
    no_bet_flags = list(config["no_bet_rules"])
    if payload.get("odds_american") is not None:
        implied_probability = implied_probability_from_american(payload["odds_american"])
    if implied_probability is not None and true_probability is not None:
        edge = edge_percentage(float(true_probability), implied_probability)
        suggested = suggested_stake_with_risk_controls(
            bankroll=float(payload.get("bankroll") or 0),
            american_odds=payload["odds_american"],
            true_probability=float(true_probability),
            risk_profile=payload.get("risk_profile") or "conservative",
        )
    if missing_inputs:
        no_bet_flags = ["required inputs missing", "confirmed bets disabled"] + missing_inputs
    elif component_status == COMPONENT_STATUS_RESEARCH:
        no_bet_flags = ["no backtest proof", "research mode only", "confirmed bets disabled"]

    social_input_stats = dict(input_stats)
    social_input_stats["edge"] = edge
    social_layer = build_social_crowd_calibration_layer(social_input_stats)
    if social_layer["sentiment_no_bet_flags"]:
        no_bet_flags = list(dict.fromkeys(no_bet_flags + social_layer["sentiment_no_bet_flags"]))

    risk_controller = build_risk_controller(payload.get("bankroll"), payload.get("unit_size"), payload.get("risk_profile") or "conservative")
    detector_payload = dict(payload)
    detector_payload.update({
        "sport_model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "risk_level": payload.get("risk_profile") or "conservative",
        "selection": payload.get("selection") or payload.get("player_name") or payload.get("home_team"),
    })
    wee_willie = build_wee_willie_market_weakness_detector(detector_payload)
    manual_ticket = build_manual_ticket(detector_payload, suggested)
    full_board = {
        "confirmed_bets": [],
        "target_lines": [] if component_status == COMPONENT_STATUS_INACTIVE else [{"market": market, "target_price": payload.get("odds_american")}],
        "target_props": [],
        "target_alt_lines": [],
        "no_bets": [{"reason": flag} for flag in no_bet_flags],
        "best_correlated_parlay": None,
        "value_ranking": [],
        "risk_ranking": [],
        "missing_inputs": missing_inputs,
        "manual_review_required": [manual_ticket],
        "logbook_ready_rows": [manual_ticket["logbook_ready_row"]],
    }
    return {
        "ok": True,
        "endpoint": "analyzeSportModel",
        "sport": sport,
        "model_used": config["model_used"],
        "model_family": config["model_family"],
        "market": market,
        "projected_score": input_stats.get("projected_score"),
        "true_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": input_stats.get("confidence"),
        "risk_level": payload.get("risk_profile") or "conservative",
        "recommended_unit_size": risk_controller["recommended_unit_size"],
        "no_bet_flags": no_bet_flags,
        "correlation_notes": config["correlation_notes"],
        "model_components": config["model_components"],
        "missing_inputs": missing_inputs,
        "backtest_status": backtest_status,
        "calibration_status": calibration_status,
        "logbook_ready_row": manual_ticket["logbook_ready_row"],
        "component_statuses": {config["model_used"]: component_status},
        "advanced_edge_components": deepcopy(ADVANCED_EDGE_COMPONENTS),
        "provider_needs": config["provider_needs"],
        "risk_controller": risk_controller,
        "wee_willie_market_weakness_detector": wee_willie,
        "social_sentiment_engine": social_layer["social_sentiment_engine"],
        "crowdsourced_signal_engine": social_layer["crowdsourced_signal_engine"],
        "public_bias_detector": social_layer["public_bias_detector"],
        "news_velocity_detector": social_layer["news_velocity_detector"],
        "rumor_risk_filter": social_layer["rumor_risk_filter"],
        "market_narrative_tracker": social_layer["market_narrative_tracker"],
        "sentiment_calibration_status": social_layer["sentiment_calibration_status"],
        "crowd_signal_calibration_status": social_layer["crowd_signal_calibration_status"],
        "sentiment_no_bet_flags": social_layer["sentiment_no_bet_flags"],
        "social_crowd_signal_explanation": social_layer["social_crowd_signal_explanation"],
        "manual_ticket_preview": manual_ticket,
        "full_board_preview": full_board,
        "confirmed_bets": [],
        "error": None,
        "detail": None,
    }


def _unsupported_sport_response(payload: dict[str, Any]) -> dict[str, Any]:
    sport = payload.get("sport")
    risk_controller = build_risk_controller(payload.get("bankroll"), payload.get("unit_size"), payload.get("risk_profile") or "conservative")
    social_layer = build_social_crowd_calibration_layer({})
    return {
        "ok": False,
        "endpoint": "analyzeSportModel",
        "sport": sport,
        "model_used": None,
        "model_family": None,
        "market": payload.get("market"),
        "projected_score": None,
        "true_probability": None,
        "implied_probability": None,
        "edge": None,
        "confidence": None,
        "risk_level": payload.get("risk_profile") or "conservative",
        "recommended_unit_size": risk_controller["recommended_unit_size"],
        "no_bet_flags": ["unsupported sport", "confirmed bets disabled"],
        "correlation_notes": [],
        "model_components": [],
        "missing_inputs": [],
        "backtest_status": "not_started",
        "calibration_status": "not_started",
        "logbook_ready_row": {},
        "component_statuses": {},
        "advanced_edge_components": deepcopy(ADVANCED_EDGE_COMPONENTS),
        "provider_needs": list(STANDARD_PROVIDER_NEEDS),
        "risk_controller": risk_controller,
        "wee_willie_market_weakness_detector": build_wee_willie_market_weakness_detector({}),
        "social_sentiment_engine": social_layer["social_sentiment_engine"],
        "crowdsourced_signal_engine": social_layer["crowdsourced_signal_engine"],
        "public_bias_detector": social_layer["public_bias_detector"],
        "news_velocity_detector": social_layer["news_velocity_detector"],
        "rumor_risk_filter": social_layer["rumor_risk_filter"],
        "market_narrative_tracker": social_layer["market_narrative_tracker"],
        "sentiment_calibration_status": social_layer["sentiment_calibration_status"],
        "crowd_signal_calibration_status": social_layer["crowd_signal_calibration_status"],
        "sentiment_no_bet_flags": social_layer["sentiment_no_bet_flags"],
        "social_crowd_signal_explanation": social_layer["social_crowd_signal_explanation"],
        "manual_ticket_preview": None,
        "full_board_preview": {
            "confirmed_bets": [],
            "target_lines": [],
            "target_props": [],
            "target_alt_lines": [],
            "no_bets": [{"reason": "unsupported sport"}],
            "best_correlated_parlay": None,
            "value_ranking": [],
            "risk_ranking": [],
            "missing_inputs": [],
            "manual_review_required": [],
            "logbook_ready_rows": [],
        },
        "confirmed_bets": [],
        "error": "UNSUPPORTED_SPORT",
        "detail": f"Unsupported sport key: {sport}",
    }


_validate_registry()
