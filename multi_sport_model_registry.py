from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import math
import re
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
    "basketball_ncaawb",
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

SPORT_ALIASES = {
    "egaming": "esports",
    "nba": "basketball_nba",
    "wnba": "basketball_wnba",
    "womens_nba": "basketball_wnba",
    "ncaab": "basketball_ncaab",
    "college_basketball_mens": "basketball_ncaab",
    "mens_college_basketball": "basketball_ncaab",
    "ncaa_mens_basketball": "basketball_ncaab",
    "ncaawb": "basketball_ncaawb",
    "ncaaw": "basketball_ncaawb",
    "college_basketball_womens": "basketball_ncaawb",
    "womens_college_basketball": "basketball_ncaawb",
    "ncaa_womens_basketball": "basketball_ncaawb",
    "nfl": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "college_football": "americanfootball_ncaaf",
    "cfb": "americanfootball_ncaaf",
    "ncaa_football": "americanfootball_ncaaf",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "hockey": "icehockey_nhl",
    "ice_hockey": "icehockey_nhl",
    "atp": "tennis",
    "wta": "tennis",
    "tennis_atp": "tennis",
    "tennis_wta": "tennis",
    "ufc": "mma_mixed_martial_arts",
    "ufc_mma": "mma_mixed_martial_arts",
    "mma": "mma_mixed_martial_arts",
    "mixed_martial_arts": "mma_mixed_martial_arts",
    "mixed martial arts": "mma_mixed_martial_arts",
    "combat_sports": "mma_mixed_martial_arts",
    "combat sports": "mma_mixed_martial_arts",
    "pga": "golf",
    "golf_pga": "golf",
    "pga_tour": "golf",
    "pga tour": "golf",
    "liv": "golf",
    "liv_golf": "golf",
    "liv golf": "golf",
    "dp_world_tour": "golf",
    "dp world tour": "golf",
    "european_tour": "golf",
    "european tour": "golf",
    "lpga": "golf",
    "ipl": "cricket",
    "indian_premier_league": "cricket",
    "indian premier league": "cricket",
    "t20": "cricket",
    "t20_cricket": "cricket",
    "t20 cricket": "cricket",
    "odi": "cricket",
    "one_day_cricket": "cricket",
    "one day cricket": "cricket",
    "test_cricket": "cricket",
    "test cricket": "cricket",
    "international_cricket": "cricket",
    "international cricket": "cricket",
    "big_bash": "cricket",
    "big bash": "cricket",
    "bbl": "cricket",
    "the_hundred": "cricket",
    "the hundred": "cricket",
    "cpl": "cricket",
    "psl": "cricket",
    "epl": "soccer",
    "ucl": "soccer",
    "football": "soccer",
    "soccer_epl": "soccer",
    "soccer_uefa_champs_league": "soccer",
    "soccer_spain_la_liga": "soccer",
    "soccer_italy_serie_a": "soccer",
    "soccer_germany_bundesliga": "soccer",
    "soccer_france_ligue_one": "soccer",
    "soccer_usa_mls": "soccer",
    "soccer_international": "soccer",
    "valorant": "esports",
    "csgo": "esports",
    "lol": "esports",
}

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
    "social_sentiment",
    "crowd consensus percentage",
    "crowd_consensus",
    "public betting percentage",
    "public_betting_percent",
    "money percentage",
    "public_money_percent",
    "sharp_money_percent",
    "news velocity score",
    "news_velocity",
    "injury rumor flag",
    "injury_rumor",
    "lineup rumor flag",
    "beat writer signal",
    "beat_writer_signal",
    "Reddit or forum sentiment",
    "reddit_signal",
    "forum_signal",
    "Discord or community signal",
    "discord_signal",
    "Google Trends style interest score",
    "media hype score",
    "rumor_risk",
    "market_narrative",
    "line_movement_reason",
    "source_quality",
    "sample_size",
    "timestamp",
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

SOCIAL_CROWD_TEXT_SCORES = {
    "strong": 90,
    "verified": 90,
    "trusted": 90,
    "reliable": 85,
    "low": 30,
    "medium": 60,
    "high": 90,
    "heavy public lean": 85,
    "public lean": 70,
    "neutral": 50,
    "sharp lean": 35,
    "hyped public side": 85,
    "quiet": 30,
    "weak": 25,
    "unverified": 20,
    "unknown": 0,
}

NBA_REQUIRED_CORE_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "team_pace",
    "opponent_pace",
    "team_offensive_rating",
    "opponent_offensive_rating",
    "team_defensive_rating",
    "opponent_defensive_rating",
    "team_efg_percent",
    "opponent_efg_percent",
    "team_turnover_percent",
    "opponent_turnover_percent",
    "team_offensive_rebound_percent",
    "opponent_offensive_rebound_percent",
    "team_free_throw_rate",
    "opponent_free_throw_rate",
    "key_player_usage_available",
    "minutes_projection_available",
    "injury_report_status",
]

NBA_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": [],
    "spread": ["line"],
    "total": ["total_line"],
    "team_total": ["team_total_line"],
    "first_half": [],
    "second_half": [],
    "first_quarter": [],
    "first_quarter_moneyline": [],
    "first_quarter_spread": ["line"],
    "first_quarter_total": ["total_line"],
    "player_prop": ["player_name", "prop_type", "prop_line", "player_projection", "player_minutes_projection"],
    "alt_line": ["line"],
    "live": ["live_game", "live_period", "live_clock", "live_score_team", "live_score_opponent"],
}

NBA_OPTIONAL_ENRICHMENT_INPUTS = [
    "projected_game_pace",
    "team_recent_net_rating_5",
    "opponent_recent_net_rating_5",
    "team_recent_net_rating_10",
    "opponent_recent_net_rating_10",
    "rest_days",
    "team_rest_days",
    "opponent_rest_days",
    "back_to_back",
    "team_back_to_back",
    "opponent_back_to_back",
    "travel_distance_miles",
    "team_travel_distance_miles",
    "opponent_travel_distance_miles",
    "altitude_spot",
    "team_home_net_rating",
    "opponent_away_net_rating",
    "team_clutch_net_rating",
    "opponent_clutch_net_rating",
    "team_three_point_rate",
    "opponent_three_point_rate",
    "team_three_point_allowed_rate",
    "opponent_three_point_allowed_rate",
    "team_rim_rate",
    "opponent_rim_rate",
    "team_rim_allowed_rate",
    "opponent_rim_allowed_rate",
    "team_free_throw_attempt_rate",
    "opponent_free_throw_attempt_rate",
    "projected_starters_confirmed",
    "minutes_volatility",
    "team_projected_points",
    "opponent_projected_points",
    "projected_margin",
    "projected_total",
    "team_projected_starting_lineup",
    "opponent_projected_starting_lineup",
    "team_starter_minutes_projection",
    "opponent_starter_minutes_projection",
    "team_key_players_out",
    "opponent_key_players_out",
    "team_usage_missing_percent",
    "opponent_usage_missing_percent",
    "team_star_player_usage_rate",
    "opponent_star_player_usage_rate",
    "team_star_player_on_off_net",
    "opponent_star_player_on_off_net",
]

NBA_PROVIDER_ENRICHMENT_INPUTS = [
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "book_count",
    "no_vig_market_probability",
    "kalshi_event_ticker",
    "kalshi_market_type",
    "kalshi_yes_bid",
    "kalshi_yes_ask",
    "kalshi_mid_probability",
    "kalshi_liquidity",
    "kalshi_volume",
]

NBA_REFEREE_INPUTS = [
    "official_name",
    "referee_name",
    "crew_names",
    "official_sample_size",
    "official_data_source",
    "official_data_quality",
    "foul_rate_per_game",
    "free_throw_rate_allowed",
    "home_foul_differential",
    "technical_foul_rate",
    "ejection_rate",
    "over_rate_with_ref",
    "under_rate_with_ref",
    "favorite_cover_rate_with_ref",
    "underdog_cover_rate_with_ref",
    "referee_sample_size",
    "referee_data_quality",
]

NBA_SOCIAL_CROWD_INPUTS = [
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "ticket_count_percent",
    "handle_percent",
    "line_movement",
    "steam_move_flag",
    "reverse_line_movement_flag",
    "market_consensus",
    "social_sentiment",
    "crowd_consensus",
    "rumor_risk",
    "news_velocity",
    "verified_news_source",
    "source_quality",
]

NBA_LIVE_BETTING_INPUTS = [
    "live_game",
    "live_period",
    "live_clock",
    "live_score_team",
    "live_score_opponent",
    "live_foul_count_team",
    "live_foul_count_opponent",
    "live_timeout_count_team",
    "live_timeout_count_opponent",
    "live_win_probability",
    "live_expected_possessions_remaining",
]

NBA_INPUT_CONTRACT = {
    "required_core_inputs": NBA_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": NBA_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": NBA_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": NBA_PROVIDER_ENRICHMENT_INPUTS,
    "referee_inputs": NBA_REFEREE_INPUTS,
    "social_crowd_inputs": NBA_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": NBA_LIVE_BETTING_INPUTS,
}

BASKETBALL_MODULE_MARKETS = [
    "moneyline", "spread", "total", "team_total", "first_half_moneyline", "first_half_spread",
    "first_half_total", "first_quarter_moneyline", "first_quarter_spread", "first_quarter_total",
    "player_points", "player_rebounds", "player_assists", "player_pra", "player_threes",
    "player_steals", "player_blocks", "player_turnovers", "double_double", "alt_spread",
    "alt_total", "alt_team_total",
]

BASKETBALL_MODULE_PROP_MARKETS = [
    "player_points", "player_rebounds", "player_assists", "player_pra", "player_threes",
    "player_steals", "player_blocks", "player_turnovers", "double_double",
]

BASKETBALL_MODULE_REQUIRED_BASE_INPUTS = [
    "home_team", "away_team", "team", "opponent", "home_offensive_rating", "home_defensive_rating",
    "away_offensive_rating", "away_defensive_rating", "home_pace", "away_pace", "home_effective_fg_pct",
    "away_effective_fg_pct", "home_turnover_rate", "away_turnover_rate", "home_rebound_rate",
    "away_rebound_rate", "home_free_throw_rate", "away_free_throw_rate", "home_rest_days",
    "away_rest_days", "home_travel_fatigue", "away_travel_fatigue",
]

WNBA_REQUIRED_CORE_INPUTS = BASKETBALL_MODULE_REQUIRED_BASE_INPUTS + [
    "home_injury_adjustment", "away_injury_adjustment",
]

COLLEGE_BASKETBALL_REQUIRED_CORE_INPUTS = BASKETBALL_MODULE_REQUIRED_BASE_INPUTS + [
    "home_rank", "away_rank", "home_strength_rating", "away_strength_rating",
    "home_conference_strength", "away_conference_strength", "home_experience_rating",
    "away_experience_rating", "home_three_point_rate", "away_three_point_rate",
    "home_free_throw_pct", "away_free_throw_pct",
]

BASKETBALL_MODULE_REQUIRED_MARKET_INPUTS = {
    "moneyline": ["odds_american"],
    "spread": ["line", "odds_american"],
    "total": ["total_line", "odds_american"],
    "team_total": ["total_line", "odds_american"],
    "first_half_moneyline": ["odds_american"],
    "first_half_spread": ["line", "odds_american"],
    "first_half_total": ["total_line", "odds_american"],
    "first_quarter_moneyline": ["odds_american"],
    "first_quarter_spread": ["line", "odds_american"],
    "first_quarter_total": ["total_line", "odds_american"],
    "alt_spread": ["line", "odds_american"],
    "alt_total": ["total_line", "odds_american"],
    "alt_team_total": ["total_line", "odds_american"],
}

for _basketball_prop_market in BASKETBALL_MODULE_PROP_MARKETS:
    BASKETBALL_MODULE_REQUIRED_MARKET_INPUTS[_basketball_prop_market] = [
        "player", "player_team", "player_minutes_projection", "player_usage_rate", "line", "odds_american",
    ]

BASKETBALL_MODULE_PLAYER_PROP_INPUTS = [
    "player", "player_team", "opponent", "player_minutes_projection", "player_usage_rate",
    "player_points_projection", "player_rebounds_projection", "player_assists_projection",
    "player_pra_projection", "player_threes_projection", "player_steals_projection",
    "player_blocks_projection", "player_turnovers_projection", "line",
]

WNBA_OPTIONAL_ENRICHMENT_INPUTS = [
    "player_minutes_confidence", "rotation_stability", "no_vig_market_probability", "book_count",
    "current_odds", "best_available_odds", "social_sentiment", "crowd_consensus", "public_betting_percent",
    "sharp_money_percent", "referee_name", "official_sample_size",
]

COLLEGE_BASKETBALL_OPTIONAL_ENRICHMENT_INPUTS = [
    "neutral_court", "tournament_game", "blowout_risk", "foul_variance", "late_game_free_throw_variance",
    "tempo_volatility", "no_vig_market_probability", "book_count", "current_odds", "best_available_odds",
    "social_sentiment", "crowd_consensus", "public_betting_percent", "sharp_money_percent",
    "referee_name", "official_sample_size",
]

WNBA_INPUT_CONTRACT = {
    "required_core_inputs": WNBA_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": BASKETBALL_MODULE_REQUIRED_MARKET_INPUTS,
    "optional_enrichment_inputs": WNBA_OPTIONAL_ENRICHMENT_INPUTS,
    "player_prop_inputs": BASKETBALL_MODULE_PLAYER_PROP_INPUTS,
}

MENS_COLLEGE_BASKETBALL_INPUT_CONTRACT = {
    "required_core_inputs": COLLEGE_BASKETBALL_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": BASKETBALL_MODULE_REQUIRED_MARKET_INPUTS,
    "optional_enrichment_inputs": COLLEGE_BASKETBALL_OPTIONAL_ENRICHMENT_INPUTS,
    "player_prop_inputs": BASKETBALL_MODULE_PLAYER_PROP_INPUTS,
}

WOMENS_COLLEGE_BASKETBALL_INPUT_CONTRACT = {
    "required_core_inputs": COLLEGE_BASKETBALL_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": BASKETBALL_MODULE_REQUIRED_MARKET_INPUTS,
    "optional_enrichment_inputs": COLLEGE_BASKETBALL_OPTIONAL_ENRICHMENT_INPUTS,
    "player_prop_inputs": BASKETBALL_MODULE_PLAYER_PROP_INPUTS,
}

NFL_REQUIRED_CORE_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "team_offensive_epa_per_play",
    "opponent_offensive_epa_per_play",
    "team_defensive_epa_per_play",
    "opponent_defensive_epa_per_play",
    "team_success_rate",
    "opponent_success_rate",
    "team_defensive_success_rate_allowed",
    "opponent_defensive_success_rate_allowed",
    "team_explosive_play_rate",
    "opponent_explosive_play_rate",
    "team_explosive_play_rate_allowed",
    "opponent_explosive_play_rate_allowed",
    "team_turnover_rate",
    "opponent_turnover_rate",
    "team_pressure_rate_allowed",
    "opponent_pressure_rate_allowed",
    "team_pressure_rate_generated",
    "opponent_pressure_rate_generated",
    "team_red_zone_td_rate",
    "opponent_red_zone_td_rate",
    "team_red_zone_td_rate_allowed",
    "opponent_red_zone_td_rate_allowed",
    "team_pace_seconds_per_play",
    "opponent_pace_seconds_per_play",
    "qb_status",
    "offensive_line_health",
    "injury_report_status",
]

NFL_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": [],
    "spread": ["line"],
    "total": ["total_line"],
    "team_total": ["team_total_line"],
    "player_prop": ["player_name", "prop_type", "prop_line", "player_projection", "player_minutes_or_snap_projection"],
    "first_half": [],
    "second_half": [],
    "first_half_spread": ["line"],
    "first_half_total": ["total_line"],
    "first_quarter": [],
    "first_quarter_spread": ["line"],
    "first_quarter_total": ["total_line"],
    "live": ["live_game", "live_period", "live_clock", "live_score_team", "live_score_opponent"],
    "alt_line": ["line"],
}

NFL_OPTIONAL_ENRICHMENT_INPUTS = [
    "team_recent_epa_per_play_3",
    "opponent_recent_epa_per_play_3",
    "team_recent_success_rate_3",
    "opponent_recent_success_rate_3",
    "team_yards_per_play",
    "opponent_yards_per_play",
    "team_yards_per_play_allowed",
    "opponent_yards_per_play_allowed",
    "team_third_down_rate",
    "opponent_third_down_rate",
    "team_third_down_rate_allowed",
    "opponent_third_down_rate_allowed",
    "team_fourth_down_aggression",
    "opponent_fourth_down_aggression",
    "team_sack_rate_allowed",
    "opponent_sack_rate_allowed",
    "team_sack_rate_generated",
    "opponent_sack_rate_generated",
    "team_run_block_win_rate",
    "opponent_run_block_win_rate",
    "team_pass_block_win_rate",
    "opponent_pass_block_win_rate",
    "team_pass_rush_win_rate",
    "opponent_pass_rush_win_rate",
    "team_coverage_grade",
    "opponent_coverage_grade",
    "team_rush_defense_grade",
    "opponent_rush_defense_grade",
    "team_special_teams_epa",
    "opponent_special_teams_epa",
    "team_kicker_quality",
    "opponent_kicker_quality",
    "team_rest_days",
    "opponent_rest_days",
    "team_travel_distance_miles",
    "opponent_travel_distance_miles",
    "team_short_week",
    "opponent_short_week",
    "weather_wind_mph",
    "weather_precipitation",
    "weather_temperature",
    "dome_game",
    "surface_type",
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
]

NFL_PROVIDER_ENRICHMENT_INPUTS = [
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
]

NFL_OFFICIATING_INPUTS = [
    "official name",
    "referee name",
    "crew names",
    "official sample size",
    "official data source",
    "official data quality",
    "referee crew",
    "penalty rate",
    "penalty rate per game",
    "holding rate",
    "offensive holding rate",
    "defensive pass interference rate",
    "roughing passer rate",
    "home penalty differential",
    "over rate with ref",
    "under rate with ref",
    "favorite cover rate with ref",
    "underdog cover rate with ref",
]

NFL_SOCIAL_CROWD_INPUTS = [
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "social_sentiment",
    "crowd_consensus",
    "rumor_risk",
    "news_velocity",
    "source_quality",
]

NFL_LIVE_BETTING_INPUTS = [
    "live_game",
    "live_period",
    "live_clock",
    "live_score_team",
    "live_score_opponent",
    "live_down",
    "live_distance",
    "live_field_position",
    "live_timeouts_team",
    "live_timeouts_opponent",
    "live_win_probability",
]

NFL_INPUT_CONTRACT = {
    "required_core_inputs": NFL_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": NFL_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": NFL_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": NFL_PROVIDER_ENRICHMENT_INPUTS,
    "officiating_inputs": NFL_OFFICIATING_INPUTS,
    "referee_inputs": NFL_OFFICIATING_INPUTS,
    "social_crowd_inputs": NFL_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": NFL_LIVE_BETTING_INPUTS,
}

COLLEGE_FOOTBALL_MARKETS = [
    "moneyline", "spread", "total", "team_total", "first_half_moneyline", "first_half_spread",
    "first_half_total", "first_quarter_moneyline", "first_quarter_spread", "first_quarter_total",
    "player_passing_yards", "player_passing_tds", "player_interceptions", "player_rushing_yards",
    "player_rushing_tds", "player_receiving_yards", "player_receptions", "player_anytime_td",
    "alt_spread", "alt_total", "alt_team_total",
]

COLLEGE_FOOTBALL_PROP_MARKETS = [
    "player_passing_yards", "player_passing_tds", "player_interceptions", "player_rushing_yards",
    "player_rushing_tds", "player_receiving_yards", "player_receptions", "player_anytime_td",
]

COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS = [
    "home_team", "away_team", "team", "opponent",
    "home_offensive_epa_per_play", "away_offensive_epa_per_play",
    "home_defensive_epa_per_play", "away_defensive_epa_per_play",
    "home_success_rate", "away_success_rate",
    "home_defensive_success_rate_allowed", "away_defensive_success_rate_allowed",
    "home_explosiveness", "away_explosiveness",
    "home_explosiveness_allowed", "away_explosiveness_allowed",
    "home_pace_seconds_per_play", "away_pace_seconds_per_play",
    "home_plays_per_game", "away_plays_per_game",
    "home_points_per_drive", "away_points_per_drive",
    "home_points_allowed_per_drive", "away_points_allowed_per_drive",
    "home_red_zone_td_rate", "away_red_zone_td_rate",
    "home_red_zone_td_rate_allowed", "away_red_zone_td_rate_allowed",
    "home_turnover_margin", "away_turnover_margin",
    "home_havoc_rate", "away_havoc_rate", "home_havoc_allowed", "away_havoc_allowed",
    "home_qb_rating", "away_qb_rating", "home_qb_injury_adjustment", "away_qb_injury_adjustment",
    "home_offensive_line_rating", "away_offensive_line_rating",
    "home_defensive_line_rating", "away_defensive_line_rating",
    "home_special_teams_rating", "away_special_teams_rating",
    "home_field_advantage", "neutral_site", "weather_wind_mph", "weather_precipitation",
    "home_rest_days", "away_rest_days", "home_travel_fatigue", "away_travel_fatigue",
    "home_strength_of_schedule", "away_strength_of_schedule", "home_rank", "away_rank",
    "home_power_rating", "away_power_rating", "home_conference_strength", "away_conference_strength",
]

COLLEGE_FOOTBALL_NUMERIC_CORE_INPUTS = [
    field for field in COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS
    if field not in {
        "home_team", "away_team", "team", "opponent", "neutral_site", "weather_precipitation",
    }
]

COLLEGE_FOOTBALL_REQUIRED_MARKET_INPUTS = {
    "moneyline": ["odds_american"],
    "spread": ["line", "odds_american"],
    "total": ["total_line", "odds_american"],
    "team_total": ["total_line", "odds_american"],
    "first_half_moneyline": ["odds_american"],
    "first_half_spread": ["line", "odds_american"],
    "first_half_total": ["total_line", "odds_american"],
    "first_quarter_moneyline": ["odds_american"],
    "first_quarter_spread": ["line", "odds_american"],
    "first_quarter_total": ["total_line", "odds_american"],
    "alt_spread": ["line", "odds_american"],
    "alt_total": ["total_line", "odds_american"],
    "alt_team_total": ["total_line", "odds_american"],
}

COLLEGE_FOOTBALL_PLAYER_PROP_INPUTS = [
    "player", "player_team", "opponent", "player_position", "player_snap_share", "player_usage_rate",
    "player_pass_attempts_projection", "player_passing_yards_projection", "player_passing_tds_projection",
    "player_interceptions_projection", "player_rush_attempts_projection", "player_rushing_yards_projection",
    "player_rushing_tds_projection", "player_targets_projection", "player_receptions_projection",
    "player_receiving_yards_projection", "player_anytime_td_probability", "line",
]

for _college_football_prop_market in COLLEGE_FOOTBALL_PROP_MARKETS:
    COLLEGE_FOOTBALL_REQUIRED_MARKET_INPUTS[_college_football_prop_market] = [
        "player", "player_team", "player_position", "player_snap_share", "player_usage_rate", "line", "odds_american",
    ]

COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS = [
    "no_vig_market_probability", "book_count", "current_odds", "best_available_odds", "opening_odds",
    "consensus_odds", "public_betting_percent", "sharp_money_percent", "social_sentiment", "crowd_consensus",
    "referee_name", "referee_crew", "official_sample_size", "provider_status", "blowout_risk",
    "garbage_time_risk", "tempo_volatility", "weather_temperature", "dome_game", "tournament_game",
]

COLLEGE_FOOTBALL_INPUT_CONTRACT = {
    "required_core_inputs": COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": COLLEGE_FOOTBALL_REQUIRED_MARKET_INPUTS,
    "optional_enrichment_inputs": COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS,
    "player_prop_inputs": COLLEGE_FOOTBALL_PLAYER_PROP_INPUTS,
    "provider_enrichment_inputs": ["best_available_odds", "current_odds", "opening_odds", "consensus_odds", "no_vig_market_probability", "book_count"],
    "officiating_inputs": NFL_OFFICIATING_INPUTS,
    "referee_inputs": NFL_OFFICIATING_INPUTS,
    "social_crowd_inputs": NFL_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": NFL_LIVE_BETTING_INPUTS,
}

CRICKET_MARKETS = [
    "moneyline", "match_winner", "spread", "run_line", "total_runs", "team_total_runs",
    "first_innings_winner", "first_innings_total", "first_6_overs_total", "powerplay_total",
    "top_batter", "top_bowler", "player_runs", "player_wickets", "player_sixes", "player_fours",
    "player_total_boundaries", "player_ducks", "player_dismissal_method", "anytime_fifty",
    "anytime_hundred", "alt_total_runs", "alt_team_total_runs",
]

CRICKET_PROP_MARKETS = [
    "top_batter", "top_bowler", "player_runs", "player_wickets", "player_sixes", "player_fours",
    "player_total_boundaries", "player_ducks", "player_dismissal_method", "anytime_fifty",
    "anytime_hundred",
]

CRICKET_REQUIRED_CORE_INPUTS = [
    "team", "opponent", "home_team", "away_team", "batting_team", "bowling_team",
    "format", "venue", "pitch_type", "weather_conditions", "toss_winner", "toss_decision",
    "team_batting_rating", "opponent_batting_rating", "team_bowling_rating", "opponent_bowling_rating",
    "team_fielding_rating", "opponent_fielding_rating", "team_recent_form_rating", "opponent_recent_form_rating",
    "team_powerplay_run_rate", "opponent_powerplay_run_rate", "team_middle_overs_run_rate",
    "opponent_middle_overs_run_rate", "team_death_overs_run_rate", "opponent_death_overs_run_rate",
    "team_wicket_loss_rate", "opponent_wicket_loss_rate", "team_wicket_taking_rate", "opponent_wicket_taking_rate",
    "team_boundary_rate", "opponent_boundary_rate", "team_dot_ball_rate", "opponent_dot_ball_rate",
    "team_chase_rating", "opponent_chase_rating", "team_defend_total_rating", "opponent_defend_total_rating",
    "venue_average_score", "venue_chase_win_rate", "pitch_spin_assist", "pitch_pace_assist", "dew_factor", "wind_factor",
]

CRICKET_NUMERIC_CORE_INPUTS = [
    field for field in CRICKET_REQUIRED_CORE_INPUTS
    if field not in {
        "team", "opponent", "home_team", "away_team", "batting_team", "bowling_team",
        "format", "venue", "pitch_type", "weather_conditions", "toss_winner", "toss_decision",
    }
]

CRICKET_PLAYER_PROP_INPUTS = [
    "player", "player_team", "opponent", "player_role", "batting_position",
    "player_batting_average", "player_strike_rate", "player_recent_runs_average",
    "player_boundary_rate", "player_six_rate", "player_fifty_rate", "player_hundred_rate",
    "player_duck_rate", "player_bowling_average", "player_economy_rate",
    "player_strike_rate_bowling", "player_recent_wickets_average", "player_overs_projection",
    "player_balls_faced_projection", "player_runs_projection", "player_wickets_projection",
    "player_sixes_projection", "player_fours_projection", "line",
]

CRICKET_NUMERIC_PLAYER_PROP_INPUTS = [
    field for field in CRICKET_PLAYER_PROP_INPUTS
    if field not in {"player", "player_team", "opponent", "player_role"}
]

CRICKET_REQUIRED_MARKET_INPUTS = {
    "moneyline": ["odds_american"],
    "match_winner": ["odds_american"],
    "first_innings_winner": ["odds_american"],
    "spread": ["line", "odds_american"],
    "run_line": ["line", "odds_american"],
    "total_runs": ["total_runs_line", "odds_american"],
    "first_innings_total": ["total_runs_line", "odds_american"],
    "first_6_overs_total": ["total_runs_line", "odds_american"],
    "powerplay_total": ["total_runs_line", "odds_american"],
    "alt_total_runs": ["total_runs_line", "odds_american"],
    "team_total_runs": ["team_total_runs_line", "odds_american"],
    "alt_team_total_runs": ["team_total_runs_line", "odds_american"],
}

for _cricket_prop_market in CRICKET_PROP_MARKETS:
    CRICKET_REQUIRED_MARKET_INPUTS[_cricket_prop_market] = [
        "player", "player_team", "player_role", "line", "odds_american",
    ]

CRICKET_OPTIONAL_ENRICHMENT_INPUTS = [
    "no_vig_market_probability", "book_count", "current_odds", "best_available_odds", "opening_odds",
    "consensus_odds", "provider_status", "public_betting_percent", "sharp_money_percent",
    "social_sentiment", "crowd_consensus", "pitch_report_quality", "toss_report_quality",
    "weather_report_quality", "lineup_confirmed", "batting_order_confirmed", "bowler_matchup_quality",
]

CRICKET_INPUT_CONTRACT = {
    "required_core_inputs": CRICKET_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": CRICKET_REQUIRED_MARKET_INPUTS,
    "optional_enrichment_inputs": CRICKET_OPTIONAL_ENRICHMENT_INPUTS,
    "player_prop_inputs": CRICKET_PLAYER_PROP_INPUTS,
    "provider_enrichment_inputs": ["best_available_odds", "current_odds", "opening_odds", "consensus_odds", "no_vig_market_probability", "book_count"],
    "social_crowd_inputs": NFL_SOCIAL_CROWD_INPUTS,
}

MLB_REQUIRED_CORE_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "market",
    "team_projected_runs",
    "opponent_projected_runs",
    "team_starting_pitcher",
    "opponent_starting_pitcher",
    "team_starting_pitcher_era",
    "opponent_starting_pitcher_era",
    "team_starting_pitcher_fip",
    "opponent_starting_pitcher_fip",
    "team_starting_pitcher_xfip",
    "opponent_starting_pitcher_xfip",
    "team_starting_pitcher_k_rate",
    "opponent_starting_pitcher_k_rate",
    "team_starting_pitcher_bb_rate",
    "opponent_starting_pitcher_bb_rate",
    "team_starting_pitcher_hr_rate",
    "opponent_starting_pitcher_hr_rate",
    "team_starting_pitcher_innings_projection",
    "opponent_starting_pitcher_innings_projection",
    "team_bullpen_era",
    "opponent_bullpen_era",
    "team_bullpen_fip",
    "opponent_bullpen_fip",
    "team_bullpen_recent_usage",
    "opponent_bullpen_recent_usage",
    "team_bullpen_rest_status",
    "opponent_bullpen_rest_status",
    "team_woba",
    "opponent_woba",
    "team_xwoba",
    "opponent_xwoba",
    "team_wrc_plus",
    "opponent_wrc_plus",
    "team_iso",
    "opponent_iso",
    "team_k_rate",
    "opponent_k_rate",
    "team_bb_rate",
    "opponent_bb_rate",
    "park_factor_runs",
    "park_factor_home_runs",
    "weather_temperature",
    "weather_wind_mph",
    "weather_wind_direction",
    "roof_status",
    "injury_report_status",
    "lineup_status",
]

MLB_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": ["odds_american"],
    "runline": ["line", "odds_american"],
    "total": ["total_line", "odds_american"],
    "team_total": ["team_total_line", "odds_american"],
    "first_5_moneyline": ["odds_american"],
    "first_5_runline": ["line", "odds_american"],
    "first_5_total": ["total_line", "odds_american"],
    "player_prop": ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status"],
    "live": ["live_game", "live_inning", "live_score_team", "live_score_opponent", "odds_american"],
    "alt_line": ["line", "odds_american"],
}

MLB_OPTIONAL_ENRICHMENT_INPUTS = [
    "team_recent_woba_14",
    "opponent_recent_woba_14",
    "team_recent_wrc_plus_14",
    "opponent_recent_wrc_plus_14",
    "team_vs_pitcher_handedness_woba",
    "opponent_vs_pitcher_handedness_woba",
    "team_vs_pitcher_handedness_k_rate",
    "opponent_vs_pitcher_handedness_k_rate",
    "team_base_running_score",
    "opponent_base_running_score",
    "team_defensive_runs_saved",
    "opponent_defensive_runs_saved",
    "team_fielding_error_rate",
    "opponent_fielding_error_rate",
    "catcher_framing_score",
    "opponent_catcher_framing_score",
    "umpire_name",
    "umpire_called_strike_rate",
    "umpire_walk_rate_impact",
    "umpire_strikeout_rate_impact",
    "umpire_over_rate",
    "umpire_under_rate",
    "official_sample_size",
    "official_data_source",
    "official_data_quality",
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "team_run_dispersion",
    "opponent_run_dispersion",
    "pitch_count_projection",
]

MLB_PROVIDER_ENRICHMENT_INPUTS = [
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
]

MLB_OFFICIATING_INPUTS = [
    "official name",
    "umpire name",
    "umpire crew",
    "official sample size",
    "official data source",
    "official data quality",
    "umpire called strike rate",
    "umpire walk rate impact",
    "umpire strikeout rate impact",
    "umpire over rate",
    "umpire under rate",
]

MLB_SOCIAL_CROWD_INPUTS = [
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "social_sentiment",
    "crowd_consensus",
    "rumor_risk",
    "news_velocity",
    "source_quality",
]

MLB_LIVE_BETTING_INPUTS = [
    "live_game",
    "live_inning",
    "live_score_team",
    "live_score_opponent",
    "live_base_state",
    "live_outs",
    "live_pitcher_status",
    "live_win_probability",
]

MLB_INPUT_CONTRACT = {
    "required_core_inputs": MLB_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": MLB_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": MLB_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": MLB_PROVIDER_ENRICHMENT_INPUTS,
    "officiating_inputs": MLB_OFFICIATING_INPUTS,
    "umpire_inputs": MLB_OFFICIATING_INPUTS,
    "referee_inputs": MLB_OFFICIATING_INPUTS,
    "social_crowd_inputs": MLB_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": MLB_LIVE_BETTING_INPUTS,
}

SOCCER_REQUIRED_CORE_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "market",
    "league",
    "match_date",
    "team_expected_goals",
    "opponent_expected_goals",
    "team_xg_for",
    "opponent_xg_for",
    "team_xg_against",
    "opponent_xg_against",
    "team_goals_for_per_match",
    "opponent_goals_for_per_match",
    "team_goals_against_per_match",
    "opponent_goals_against_per_match",
    "team_shots_per_match",
    "opponent_shots_per_match",
    "team_shots_allowed_per_match",
    "opponent_shots_allowed_per_match",
    "team_shots_on_target_per_match",
    "opponent_shots_on_target_per_match",
    "team_shots_on_target_allowed_per_match",
    "opponent_shots_on_target_allowed_per_match",
    "team_big_chances_per_match",
    "opponent_big_chances_per_match",
    "team_big_chances_allowed_per_match",
    "opponent_big_chances_allowed_per_match",
    "team_possession_percent",
    "opponent_possession_percent",
    "team_recent_form_points",
    "opponent_recent_form_points",
    "team_rest_days",
    "opponent_rest_days",
    "injury_report_status",
    "lineup_status",
]

SOCCER_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": ["odds_american"],
    "three_way_moneyline": ["odds_american"],
    "home_draw_away": ["odds_american"],
    "draw_no_bet": ["odds_american"],
    "double_chance": ["odds_american"],
    "asian_handicap": ["line", "odds_american"],
    "spread": ["line", "odds_american"],
    "total": ["total_line", "odds_american"],
    "team_total": ["team_total_line", "odds_american"],
    "both_teams_to_score": ["odds_american"],
    "correct_score": ["correct_score_selection", "odds_american"],
    "first_half_moneyline": ["odds_american"],
    "first_half_total": ["total_line", "odds_american"],
    "first_half_team_total": ["team_total_line", "odds_american"],
    "second_half_moneyline": ["odds_american"],
    "second_half_total": ["total_line", "odds_american"],
    "corners": ["corner_line", "odds_american"],
    "team_corners": ["team_corner_line", "odds_american"],
    "cards": ["card_line", "odds_american"],
    "team_cards": ["team_card_line", "odds_american"],
    "player_prop": ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status", "player_minutes_projection"],
    "anytime_goal_scorer": ["player_name", "player_goal_projection", "player_starting_status", "player_minutes_projection", "odds_american"],
    "first_goal_scorer": ["player_name", "player_first_goal_projection", "player_starting_status", "player_minutes_projection", "odds_american"],
    "live": ["live_game", "live_minute", "live_score_team", "live_score_opponent", "odds_american"],
    "alt_line": ["line", "odds_american"],
}

SOCCER_OPTIONAL_ENRICHMENT_INPUTS = [
    "team_recent_xg_for_5",
    "opponent_recent_xg_for_5",
    "team_recent_xg_against_5",
    "opponent_recent_xg_against_5",
    "team_recent_goals_for_5",
    "opponent_recent_goals_for_5",
    "team_recent_goals_against_5",
    "opponent_recent_goals_against_5",
    "team_home_xg_for",
    "team_home_xg_against",
    "opponent_away_xg_for",
    "opponent_away_xg_against",
    "team_set_piece_xg",
    "opponent_set_piece_xg",
    "team_set_piece_xg_allowed",
    "opponent_set_piece_xg_allowed",
    "team_counter_attack_xg",
    "opponent_counter_attack_xg",
    "team_pressing_intensity",
    "opponent_pressing_intensity",
    "team_ppda",
    "opponent_ppda",
    "team_keeper_save_percent",
    "opponent_keeper_save_percent",
    "team_keeper_psxg_minus_goals",
    "opponent_keeper_psxg_minus_goals",
    "team_defensive_line_height",
    "opponent_defensive_line_height",
    "team_crosses_per_match",
    "opponent_crosses_per_match",
    "team_corner_rate",
    "opponent_corner_rate",
    "team_cards_per_match",
    "opponent_cards_per_match",
    "team_fouls_per_match",
    "opponent_fouls_per_match",
    "opponent_fouls_drawn_per_match",
    "team_fouls_drawn_per_match",
    "referee_name",
    "official_sample_size",
    "official_data_source",
    "official_data_quality",
    "referee_fouls_per_match",
    "referee_cards_per_match",
    "referee_penalty_rate",
    "referee_home_bias_index",
    "referee_over_rate",
    "referee_under_rate",
    "referee_btts_rate",
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
    "first_half_goal_share",
    "dixon_coles_rho",
    "goal_correlation",
    "shared_intensity",
    "weather_severity",
]

SOCCER_PROVIDER_ENRICHMENT_INPUTS = [
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
]

SOCCER_OFFICIATING_INPUTS = [
    "referee",
    "referee name",
    "official name",
    "official sample size",
    "official data source",
    "official data quality",
    "referee fouls per match",
    "referee cards per match",
    "referee penalty rate",
    "referee home bias index",
    "referee over rate",
    "referee under rate",
    "referee btts rate",
]

SOCCER_SOCIAL_CROWD_INPUTS = [
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "social_sentiment",
    "crowd_consensus",
    "rumor_risk",
    "news_velocity",
    "source_quality",
]

SOCCER_LIVE_BETTING_INPUTS = [
    "live_game",
    "live_minute",
    "live_score_team",
    "live_score_opponent",
    "live_red_cards_team",
    "live_red_cards_opponent",
    "live_xg_team",
    "live_xg_opponent",
]

SOCCER_INPUT_CONTRACT = {
    "required_core_inputs": SOCCER_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": SOCCER_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": SOCCER_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": SOCCER_PROVIDER_ENRICHMENT_INPUTS,
    "officiating_inputs": SOCCER_OFFICIATING_INPUTS,
    "referee_inputs": SOCCER_OFFICIATING_INPUTS,
    "social_crowd_inputs": SOCCER_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": SOCCER_LIVE_BETTING_INPUTS,
}

NHL_REQUIRED_CORE_INPUTS = [
    "team",
    "opponent",
    "selection",
    "home_away",
    "market",
    "league",
    "game_date",
    "team_projected_goals",
    "opponent_projected_goals",
    "team_xg_for_per_game",
    "opponent_xg_for_per_game",
    "team_xg_against_per_game",
    "opponent_xg_against_per_game",
    "team_goals_for_per_game",
    "opponent_goals_for_per_game",
    "team_goals_against_per_game",
    "opponent_goals_against_per_game",
    "team_shots_for_per_game",
    "opponent_shots_for_per_game",
    "team_shots_against_per_game",
    "opponent_shots_against_per_game",
    "team_scoring_chances_for_per_game",
    "opponent_scoring_chances_for_per_game",
    "team_scoring_chances_against_per_game",
    "opponent_scoring_chances_against_per_game",
    "team_high_danger_chances_for_per_game",
    "opponent_high_danger_chances_for_per_game",
    "team_high_danger_chances_against_per_game",
    "opponent_high_danger_chances_against_per_game",
    "team_power_play_percent",
    "opponent_power_play_percent",
    "team_penalty_kill_percent",
    "opponent_penalty_kill_percent",
    "team_recent_form_points",
    "opponent_recent_form_points",
    "team_rest_days",
    "opponent_rest_days",
    "team_goalie_confirmed",
    "opponent_goalie_confirmed",
    "team_starting_goalie_save_percent",
    "opponent_starting_goalie_save_percent",
    "team_starting_goalie_gsaax",
    "opponent_starting_goalie_gsaax",
    "injury_report_status",
    "lineup_status",
]

NHL_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": ["odds_american"],
    "three_way_moneyline": ["odds_american"],
    "regulation_moneyline": ["odds_american"],
    "draw_no_bet": ["odds_american"],
    "puckline": ["line", "odds_american"],
    "spread": ["line", "odds_american"],
    "alternate_puckline": ["line", "odds_american"],
    "total": ["total_line", "odds_american"],
    "alternate_total": ["total_line", "odds_american"],
    "team_total": ["team_total_line", "odds_american"],
    "first_period_moneyline": ["odds_american"],
    "first_period_total": ["total_line", "odds_american"],
    "first_period_team_total": ["team_total_line", "odds_american"],
    "second_period_moneyline": ["odds_american"],
    "second_period_total": ["total_line", "odds_american"],
    "third_period_moneyline": ["odds_american"],
    "third_period_total": ["total_line", "odds_american"],
    "player_prop": ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status", "player_minutes_projection"],
    "anytime_goal_scorer": ["player_name", "player_goal_projection", "player_starting_status", "player_minutes_projection", "odds_american"],
    "first_goal_scorer": ["player_name", "player_first_goal_projection", "player_starting_status", "player_minutes_projection", "odds_american"],
}

NHL_OPTIONAL_ENRICHMENT_INPUTS = [
    "team_recent_xg_for_5",
    "opponent_recent_xg_for_5",
    "team_recent_xg_against_5",
    "opponent_recent_xg_against_5",
    "team_recent_goals_for_5",
    "opponent_recent_goals_for_5",
    "team_recent_goals_against_5",
    "opponent_recent_goals_against_5",
    "team_home_xg_for",
    "team_home_xg_against",
    "opponent_away_xg_for",
    "opponent_away_xg_against",
    "team_corsi_for_percent",
    "opponent_corsi_for_percent",
    "team_fenwick_for_percent",
    "opponent_fenwick_for_percent",
    "team_faceoff_win_percent",
    "opponent_faceoff_win_percent",
    "team_blocked_shots_per_game",
    "opponent_blocked_shots_per_game",
    "team_hits_per_game",
    "opponent_hits_per_game",
    "team_takeaways_per_game",
    "opponent_takeaways_per_game",
    "team_giveaways_per_game",
    "opponent_giveaways_per_game",
    "team_penalties_taken_per_game",
    "opponent_penalties_taken_per_game",
    "team_penalties_drawn_per_game",
    "opponent_penalties_drawn_per_game",
    "team_back_to_back",
    "opponent_back_to_back",
    "travel_distance",
    "altitude_factor",
    "rink_factor",
    "expected_goalie_status",
    "goalie_fatigue_index",
    "backup_goalie_expected",
    "referee_crew",
    "official_sample_size",
    "official_data_source",
    "official_data_quality",
    "referee_penalties_per_game",
    "referee_power_play_rate",
    "referee_home_bias_index",
    "referee_over_rate",
    "referee_under_rate",
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
]

NHL_PROVIDER_ENRICHMENT_INPUTS = [
    "opening_odds",
    "current_odds",
    "best_available_odds",
    "consensus_odds",
    "opening_line",
    "current_line",
    "opening_total",
    "current_total",
    "no_vig_market_probability",
    "book_count",
]

NHL_OFFICIATING_INPUTS = [
    "official_name",
    "referee_name",
    "referee_crew",
    "crew_names",
    "referees",
    "linesmen",
    "official_sample_size",
    "official_data_source",
    "official_data_quality",
    "referee_penalties_per_game",
    "referee_power_play_rate",
    "referee_home_bias_index",
    "referee_over_rate",
    "referee_under_rate",
    "penalty_rate",
    "faceoff_violation_tendency",
]

NHL_SOCIAL_CROWD_INPUTS = [
    "public_betting_percent",
    "public_money_percent",
    "sharp_money_percent",
    "social_sentiment",
    "crowd_consensus",
    "rumor_risk",
    "news_velocity",
    "source_quality",
]

NHL_LIVE_BETTING_INPUTS = [
    "live_game",
    "live_period",
    "live_time_remaining",
    "live_score_team",
    "live_score_opponent",
    "live_shots_team",
    "live_shots_opponent",
    "live_power_play_state",
]

NHL_INPUT_CONTRACT = {
    "required_core_inputs": NHL_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": NHL_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": NHL_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": NHL_PROVIDER_ENRICHMENT_INPUTS,
    "officiating_inputs": NHL_OFFICIATING_INPUTS,
    "referee_inputs": NHL_OFFICIATING_INPUTS,
    "social_crowd_inputs": NHL_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": NHL_LIVE_BETTING_INPUTS,
}

TENNIS_REQUIRED_CORE_INPUTS = [
    "player", "opponent", "selection", "market", "league", "tournament", "match_date", "surface", "best_of_sets",
    "player_ranking", "opponent_ranking", "player_elo", "opponent_elo",
    "player_hold_percent", "opponent_hold_percent", "player_break_percent", "opponent_break_percent",
    "player_first_serve_in_percent", "opponent_first_serve_in_percent",
    "player_first_serve_points_won_percent", "opponent_first_serve_points_won_percent",
    "player_second_serve_points_won_percent", "opponent_second_serve_points_won_percent",
    "player_return_points_won_percent", "opponent_return_points_won_percent",
    "player_ace_rate", "opponent_ace_rate", "player_double_fault_rate", "opponent_double_fault_rate",
    "player_recent_form_wins", "opponent_recent_form_wins", "player_recent_form_losses", "opponent_recent_form_losses",
    "player_fatigue_index", "opponent_fatigue_index", "player_injury_status", "opponent_injury_status",
]

TENNIS_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": ["odds_american"],
    "match_winner": ["odds_american"],
    "set_handicap": ["line", "odds_american"],
    "game_handicap": ["line", "odds_american"],
    "total_games": ["total_line", "odds_american"],
    "first_set_moneyline": ["odds_american"],
    "first_set_total_games": ["total_line", "odds_american"],
    "correct_score": ["correct_score_selection", "odds_american"],
    "player_prop": ["player_name", "prop_type", "prop_line", "player_projection", "player_starting_status"],
    "aces": ["player_name", "prop_line", "player_projection", "odds_american"],
    "double_faults": ["player_name", "prop_line", "player_projection", "odds_american"],
    "break_points": ["player_name", "prop_line", "player_projection", "odds_american"],
    "service_games_won": ["player_name", "prop_line", "player_projection", "odds_american"],
    "return_games_won": ["player_name", "prop_line", "player_projection", "odds_american"],
}

TENNIS_OPTIONAL_ENRICHMENT_INPUTS = [
    "player_last_10_hold_percent", "opponent_last_10_hold_percent", "player_last_10_break_percent", "opponent_last_10_break_percent",
    "player_last_10_first_serve_points_won", "opponent_last_10_first_serve_points_won",
    "player_last_10_second_serve_points_won", "opponent_last_10_second_serve_points_won",
    "player_surface_elo", "opponent_surface_elo",
    "player_surface_win_percent", "opponent_surface_win_percent", "player_surface_hold_percent", "opponent_surface_hold_percent",
    "player_surface_break_percent", "opponent_surface_break_percent", "player_head_to_head_wins", "opponent_head_to_head_wins",
    "player_head_to_head_surface_wins", "opponent_head_to_head_surface_wins", "player_tiebreak_win_percent",
    "opponent_tiebreak_win_percent", "player_deciding_set_win_percent", "opponent_deciding_set_win_percent",
    "player_retirement_risk", "opponent_retirement_risk", "player_travel_fatigue", "opponent_travel_fatigue",
    "player_rest_days", "opponent_rest_days", "indoor_outdoor", "altitude_factor", "court_speed",
    "weather_wind_mph", "weather_temperature", "public_betting_percent", "public_money_percent", "sharp_money_percent",
    "opening_odds", "current_odds", "best_available_odds", "consensus_odds", "opening_line", "current_line",
    "opening_total", "current_total", "no_vig_market_probability", "book_count",
]

TENNIS_PROVIDER_ENRICHMENT_INPUTS = [
    "opening_odds", "current_odds", "best_available_odds", "consensus_odds", "opening_line", "current_line",
    "opening_total", "current_total", "no_vig_market_probability", "book_count",
]

TENNIS_OFFICIATING_INPUTS = [
    "official_name", "chair_umpire", "umpire_name", "official_sample_size", "official_data_source",
    "official_data_quality", "code_violation_tendency", "time_violation_tendency", "surface_event_context",
]

TENNIS_SOCIAL_CROWD_INPUTS = [
    "public_betting_percent", "public_money_percent", "sharp_money_percent", "social_sentiment",
    "crowd_consensus", "rumor_risk", "news_velocity", "source_quality",
]

TENNIS_LIVE_BETTING_INPUTS = [
    "live_match", "live_set", "live_game_score", "live_point_score", "live_server", "live_break_points",
]

TENNIS_INPUT_CONTRACT = {
    "required_core_inputs": TENNIS_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": TENNIS_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": TENNIS_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": TENNIS_PROVIDER_ENRICHMENT_INPUTS,
    "officiating_inputs": TENNIS_OFFICIATING_INPUTS,
    "referee_inputs": TENNIS_OFFICIATING_INPUTS,
    "social_crowd_inputs": TENNIS_SOCIAL_CROWD_INPUTS,
    "live_betting_inputs": TENNIS_LIVE_BETTING_INPUTS,
}

COMBAT_REQUIRED_CORE_INPUTS = [
    "fighter", "opponent", "selection", "fight_date", "promotion", "weight_class", "scheduled_rounds",
    "fighter_moneyline", "fighter_elo", "opponent_elo", "fighter_recent_win_percent", "opponent_recent_win_percent",
    "fighter_finish_rate", "opponent_finish_rate", "fighter_ko_tko_rate", "opponent_ko_tko_rate",
    "fighter_submission_rate", "opponent_submission_rate", "fighter_decision_rate", "opponent_decision_rate",
    "fighter_strikes_landed_per_min", "opponent_strikes_landed_per_min",
    "fighter_strikes_absorbed_per_min", "opponent_strikes_absorbed_per_min",
    "fighter_striking_accuracy", "opponent_striking_accuracy", "fighter_striking_defense", "opponent_striking_defense",
    "fighter_takedown_average", "opponent_takedown_average", "fighter_takedown_accuracy", "opponent_takedown_accuracy",
    "fighter_takedown_defense", "opponent_takedown_defense", "fighter_submission_average", "opponent_submission_average",
    "fighter_age", "opponent_age", "fighter_reach", "opponent_reach", "fighter_height", "opponent_height",
    "fighter_stance", "opponent_stance", "fighter_days_rest", "opponent_days_rest",
    "fighter_injury_status", "opponent_injury_status",
]

COMBAT_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "moneyline": ["odds_american"],
    "method_of_victory": ["odds_american"],
    "fighter_by_ko_tko": ["odds_american"],
    "fighter_by_submission": ["odds_american"],
    "fighter_by_decision": ["odds_american"],
    "opponent_by_ko_tko": ["odds_american"],
    "opponent_by_submission": ["odds_american"],
    "opponent_by_decision": ["odds_american"],
    "fight_goes_distance": ["odds_american"],
    "fight_does_not_go_distance": ["odds_american"],
    "over_rounds": ["line", "odds_american"],
    "under_rounds": ["line", "odds_american"],
    "round_group": ["line", "odds_american"],
    "exact_round": ["line", "odds_american"],
    "double_chance": ["odds_american"],
    "knockdown_prop": ["line", "odds_american"],
    "takedown_prop": ["line", "odds_american"],
    "significant_strikes_prop": ["line", "odds_american"],
    "submission_attempt_prop": ["line", "odds_american"],
}

COMBAT_OPTIONAL_ENRICHMENT_INPUTS = [
    "opponent_moneyline", "camp_change", "short_notice", "weight_cut_risk", "travel_risk", "altitude_risk",
    "five_round_experience", "championship_rounds_experience", "southpaw_matchup", "grappling_advantage",
    "striking_advantage", "chin_durability", "cardio_rating", "pace_rating", "judge_profile", "referee_profile",
    "public_betting_percent", "sharp_money_percent", "social_sentiment", "crowd_consensus",
    "kalshi_probability", "prediction_market_probability", "no_vig_market_probability", "book_count",
    "best_available_odds", "current_odds", "consensus_odds",
]

COMBAT_INPUT_CONTRACT = {
    "required_core_inputs": COMBAT_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": COMBAT_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": COMBAT_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": ["best_available_odds", "current_odds", "consensus_odds", "no_vig_market_probability", "book_count"],
    "officiating_inputs": ["referee_profile", "judge_profile", "referee", "judge_panel", "stoppage_tendency", "decision_scoring_profile"],
    "referee_inputs": ["referee_profile", "referee", "stoppage_tendency"],
    "social_crowd_inputs": ["public_betting_percent", "sharp_money_percent", "social_sentiment", "crowd_consensus"],
    "live_betting_inputs": ["live_round", "live_time_remaining", "live_knockdowns", "live_control_time", "live_strike_counts"],
}

GOLF_REQUIRED_CORE_INPUTS = [
    "player", "field_size", "event", "course", "market", "selection",
    "player_world_rank", "player_sg_total", "player_sg_off_tee", "player_sg_approach",
    "player_sg_around_green", "player_sg_putting", "player_recent_form_rank",
    "player_recent_scoring_average", "course_fit_score", "course_history_score",
    "field_strength", "cut_line_projection", "weather_wind_rating", "course_difficulty_rating",
]

GOLF_REQUIRED_MARKET_SPECIFIC_INPUTS = {
    "outright_winner": ["odds_american"],
    "top_5": ["odds_american"],
    "top_10": ["odds_american"],
    "top_20": ["odds_american"],
    "make_cut": ["odds_american"],
    "miss_cut": ["odds_american"],
    "tournament_matchup": ["opponent", "opponent_world_rank", "opponent_sg_total", "opponent_sg_off_tee", "opponent_sg_approach", "opponent_sg_around_green", "opponent_sg_putting", "opponent_recent_form_rank", "opponent_recent_scoring_average", "opponent_course_fit_score", "opponent_course_history_score", "odds_american"],
    "round_matchup": ["opponent", "opponent_world_rank", "opponent_sg_total", "opponent_sg_off_tee", "opponent_sg_approach", "opponent_sg_around_green", "opponent_sg_putting", "opponent_recent_form_rank", "opponent_recent_scoring_average", "opponent_course_fit_score", "opponent_course_history_score", "odds_american"],
    "three_ball": ["opponent", "opponent_world_rank", "opponent_sg_total", "opponent_sg_off_tee", "opponent_sg_approach", "opponent_sg_around_green", "opponent_sg_putting", "opponent_recent_form_rank", "opponent_recent_scoring_average", "opponent_course_fit_score", "opponent_course_history_score", "odds_american"],
    "first_round_leader": ["odds_american"],
    "top_n_finish": ["top_n", "odds_american"],
    "finishing_position": ["line", "odds_american"],
    "player_prop": ["prop_type", "line", "odds_american"],
    "birdies_prop": ["line", "odds_american"],
    "eagles_prop": ["line", "odds_american"],
    "fairways_hit_prop": ["line", "odds_american"],
    "greens_in_regulation_prop": ["line", "odds_american"],
    "putts_prop": ["line", "odds_american"],
    "round_score_prop": ["line", "odds_american"],
}

GOLF_OPTIONAL_ENRICHMENT_INPUTS = [
    "opponent", "opponent_world_rank", "opponent_sg_total", "opponent_sg_off_tee", "opponent_sg_approach",
    "opponent_sg_around_green", "opponent_sg_putting", "opponent_recent_form_rank", "opponent_recent_scoring_average",
    "opponent_course_fit_score", "opponent_course_history_score", "tee_time_wave", "weather_draw", "course_firmness",
    "rain_risk", "injury_status", "player_withdrawal_risk", "social_sentiment", "crowd_consensus",
    "public_betting_percent", "sharp_money_percent", "no_vig_market_probability", "book_count",
    "best_available_odds", "current_odds", "opening_odds",
]

GOLF_INPUT_CONTRACT = {
    "required_core_inputs": GOLF_REQUIRED_CORE_INPUTS,
    "required_market_specific_inputs": GOLF_REQUIRED_MARKET_SPECIFIC_INPUTS,
    "optional_enrichment_inputs": GOLF_OPTIONAL_ENRICHMENT_INPUTS,
    "provider_enrichment_inputs": ["best_available_odds", "current_odds", "opening_odds", "no_vig_market_probability", "book_count"],
    "officiating_inputs": ["rules_officials", "course_ruling_environment"],
    "referee_inputs": ["rules_officials"],
    "social_crowd_inputs": ["public_betting_percent", "sharp_money_percent", "social_sentiment", "crowd_consensus"],
    "live_betting_inputs": ["live_round", "live_score_to_par", "live_position", "holes_remaining"],
}

SPORT_PROP_INPUTS = {
    "baseball_mlb": ["player projection", "lineup status", "opponent matchup", "park factor", "weather"],
    "basketball_nba": ["minutes projection", "usage", "pace", "defensive matchup", "injury report"],
    "basketball_wnba": ["WNBA minutes projection", "WNBA usage baseline", "pace", "defensive matchup", "injury report"],
    "basketball_ncaab": ["player projection where available", "tempo", "team role", "opponent matchup"],
    "basketball_ncaawb": ["women's college player projection", "tempo", "team role", "opponent matchup"],
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

OFFICIALS_MODULE_BY_SPORT = {
    "baseball_mlb": {
        "official_type": "umpire crew",
        "official_inputs": MLB_OFFICIATING_INPUTS,
        "betting_edge_strength": "moderate",
        "notes": "Umpire context can matter for strike zone, run environment, pitcher props, and totals.",
    },
    "basketball_nba": {
        "official_type": "referee crew",
        "official_inputs": NBA_REFEREE_INPUTS,
        "betting_edge_strength": "moderate",
        "notes": "Referee context can matter for foul rate, free throw rate, home differential, totals, and player props.",
    },
    "basketball_wnba": {
        "official_type": "referees",
        "official_inputs": ["referee crew", "foul rate", "free throw rate", "home foul differential"],
        "betting_edge_strength": "moderate",
        "notes": "Same officials module as basketball, with WNBA-specific calibration required.",
    },
    "basketball_ncaab": {
        "official_type": "referees",
        "official_inputs": ["referee crew", "foul rate", "free throw rate", "conference officiating profile"],
        "betting_edge_strength": "moderate",
        "notes": "College officiating context is conference-sensitive and needs stronger shrinkage.",
    },
    "basketball_ncaawb": {
        "official_type": "referees",
        "official_inputs": ["referee crew", "foul rate", "free throw rate", "conference officiating profile"],
        "betting_edge_strength": "moderate",
        "notes": "Women's college officiating context is conference-sensitive and calibrated separately.",
    },
    "americanfootball_nfl": {
        "official_type": "referee crew",
        "official_inputs": NFL_OFFICIATING_INPUTS,
        "betting_edge_strength": "moderate",
        "notes": "Crew context can matter for penalties, pace interruptions, totals, and derivative props.",
    },
    "americanfootball_ncaaf": {
        "official_type": "referee crew",
        "official_inputs": ["referee crew", "penalty rate", "conference officiating profile"],
        "betting_edge_strength": "moderate",
        "notes": "College football crew context needs conference and crew-level shrinkage.",
    },
    "soccer": {
        "official_type": "referee",
        "official_inputs": SOCCER_OFFICIATING_INPUTS,
        "betting_edge_strength": "moderate",
        "notes": "Referee context can matter for cards, penalties, match flow, and totals.",
    },
    "icehockey_nhl": {
        "official_type": "referees and linesmen",
        "official_inputs": NHL_OFFICIATING_INPUTS,
        "betting_edge_strength": "moderate",
        "notes": "Referees and linesmen can affect penalties, special teams exposure, and stoppage profile.",
    },
    "tennis": {
        "official_type": "chair umpire",
        "official_inputs": TENNIS_OFFICIATING_INPUTS,
        "betting_edge_strength": "weak_to_moderate",
        "notes": "Chair umpire context is usually secondary to serve, return, surface, and player form.",
    },
    "mma_mixed_martial_arts": {
        "official_type": "referee and judges",
        "official_inputs": COMBAT_INPUT_CONTRACT["officiating_inputs"],
        "betting_edge_strength": "moderate",
        "notes": "Referee and judges can matter for finish, goes-distance, decision, and round props.",
    },
    "boxing": {
        "official_type": "referee and judges",
        "official_inputs": COMBAT_INPUT_CONTRACT["officiating_inputs"],
        "betting_edge_strength": "moderate",
        "notes": "Referee and judges are relevant to stoppage, decision, draw, and method markets.",
    },
    "golf": {
        "official_type": "rules officials",
        "official_inputs": ["rules officials", "course ruling environment", "weather delay procedures"],
        "betting_edge_strength": "weak",
        "notes": "Rules officials are tracked, but officials context is a weaker betting edge than course fit, strokes gained, and weather.",
    },
    "formula1": {
        "official_type": "stewards/race control",
        "official_inputs": ["stewards", "race control", "safety car procedure", "track limits enforcement", "penalty tendency"],
        "betting_edge_strength": "situational",
        "notes": "Formula 1 uses stewards and race control rather than traditional referees.",
    },
    "cricket": {
        "official_type": "umpires/match referee",
        "official_inputs": ["on-field umpires", "third umpire", "match referee", "DRS environment"],
        "betting_edge_strength": "weak_to_moderate",
        "notes": "Cricket official context is tracked but usually sits behind pitch, toss, venue, and lineup inputs.",
    },
    "esports": {
        "official_type": "tournament admin/map/server/rule enforcement",
        "official_inputs": ["tournament admin", "map admin", "server admin", "rule enforcement", "pause/remake policy"],
        "betting_edge_strength": "weak",
        "notes": "Esports enforcement context is usually a weak edge compared with game title, roster, patch, map pool, and server conditions.",
    },
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


def _officials_module(sport: str) -> dict[str, Any]:
    config = OFFICIALS_MODULE_BY_SPORT[sport]
    return {
        "module_name": "officials_context_module",
        "component_name": "officials_context_module",
        "component_status": COMPONENT_STATUS_INACTIVE,
        "official_type": config["official_type"],
        "official_inputs": list(config["official_inputs"]),
        "betting_edge_strength": config["betting_edge_strength"],
        "same_module_for_all_sports": True,
        "notes": config["notes"],
    }


def _official_input_value(input_stats: dict[str, Any], label: str) -> Any:
    key = label.strip().lower().replace("/", " ").replace("-", " ")
    snake = re.sub(r"\s+", "_", key)
    candidates = [
        label,
        key,
        snake,
        f"official_{snake}",
        f"officials_{snake}",
        f"officiating_{snake}",
    ]
    if "referee" in snake:
        candidates.extend([snake.replace("referee", "ref"), snake.replace("referee", "referee")])
    if "umpire" in snake:
        candidates.append(snake.replace("umpire", "ump"))
    for candidate in candidates:
        if candidate in input_stats and input_stats.get(candidate) is not None:
            return input_stats.get(candidate)
    return None


def _official_inputs_present(input_stats: dict[str, Any], official_inputs: list[str]) -> list[str]:
    return [label for label in official_inputs if _official_input_value(input_stats, label) is not None]


def _official_affected_markets(sport: str, market: Any) -> list[str]:
    market_text = str(market or "").strip()
    by_sport = {
        "baseball_mlb": ["totals", "team totals", "pitcher strikeouts", "walks"],
        "basketball_nba": ["spread", "totals", "team totals", "player props"],
        "basketball_wnba": ["spread", "totals", "team totals", "player props"],
        "basketball_ncaab": ["spread", "totals", "team totals"],
        "basketball_ncaawb": ["spread", "totals", "team totals"],
        "americanfootball_nfl": ["spread", "totals", "penalty-sensitive props"],
        "americanfootball_ncaaf": ["spread", "totals", "penalty-sensitive props"],
        "soccer": ["cards", "penalties", "totals", "both teams to score"],
        "icehockey_nhl": ["totals", "power play props", "penalty props"],
        "tennis": ["live markets", "game spread", "total games"],
        "mma_mixed_martial_arts": ["method", "goes distance", "round props"],
        "boxing": ["method", "goes distance", "round props", "decision"],
        "golf": ["outrights", "matchups"],
        "formula1": ["race winner", "podium", "points finish", "driver head to head"],
        "cricket": ["match winner", "innings runs", "player props"],
        "esports": ["match winner", "map winner", "round totals", "live markets"],
    }
    markets = list(by_sport.get(sport, []))
    if market_text and market_text not in markets:
        markets.insert(0, market_text)
    return markets


def _officiating_cap(edge_strength: str) -> float:
    return {
        "moderate": 1.5,
        "weak_to_moderate": 0.75,
        "weak": 0.35,
        "situational": 0.5,
    }.get(edge_strength, 0.5)


def _explicit_officiating_adjustment(input_stats: dict[str, Any]) -> Optional[float]:
    for key in [
        "officiating_adjustment_probability_points",
        "official_adjustment_probability_points",
        "officials_adjustment_probability_points",
        "referee_adjustment_probability_points",
        "umpire_adjustment_probability_points",
        "stewards_adjustment_probability_points",
        "race_control_adjustment_probability_points",
        "judge_adjustment_probability_points",
    ]:
        value = _safe_float(input_stats.get(key))
        if value is not None:
            return value
    return None


def build_officiating_analysis(
    *,
    sport: str,
    market: Any,
    input_stats: dict[str, Any],
    true_probability: Optional[float],
    base_model_active: bool,
    base_confidence: Any,
) -> dict[str, Any]:
    module = _officials_module(sport)
    official_inputs = list(module["official_inputs"])
    present_inputs = _official_inputs_present(input_stats, official_inputs)
    risk_flags: list[str] = []
    no_bet_reason = None
    adjustment_points = 0.0
    status = "no_adjustment"

    if not base_model_active or true_probability is None:
        status = "inactive_base_model"
        no_bet_reason = "base model inactive; officiating data cannot create confirmed bets"
        if present_inputs:
            risk_flags.append("officiating data present without active base model")
    elif not present_inputs:
        no_bet_reason = "no officiating adjustment"
    else:
        explicit_adjustment = _explicit_officiating_adjustment(input_stats)
        if explicit_adjustment is not None:
            adjustment_points = explicit_adjustment
        elif sport == "basketball_nba":
            quality = str(input_stats.get("referee_data_quality") or "").strip().lower()
            if quality in {"strong", "high"}:
                adjustment_points = (_safe_float(input_stats.get("home_foul_differential"), 0) or 0) * 0.15
        elif sport == "baseball_mlb":
            adjustment_points = (_safe_float(input_stats.get("umpire_run_environment"), 0) or 0) * 0.25
        elif sport in {"americanfootball_nfl", "americanfootball_ncaaf"}:
            adjustment_points = (_safe_float(input_stats.get("penalty_rate"), 0) or 0) * 0.05
        elif sport == "soccer":
            adjustment_points = (_safe_float(input_stats.get("penalty_awarded_rate"), 0) or 0) * 0.2
        elif sport == "icehockey_nhl":
            adjustment_points = (_safe_float(input_stats.get("penalty_rate"), 0) or 0) * 0.05
        elif sport in {"mma_mixed_martial_arts", "boxing"}:
            adjustment_points = (_safe_float(input_stats.get("decision_scoring_profile"), 0) or 0) * 0.15
        elif sport == "formula1":
            adjustment_points = (_safe_float(input_stats.get("penalty_tendency"), 0) or 0) * -0.15
        adjustment_points = max(-_officiating_cap(module["betting_edge_strength"]), min(_officiating_cap(module["betting_edge_strength"]), adjustment_points))
        status = "active_adjustment" if abs(adjustment_points) > 0 else "active_no_adjustment"
        if str(input_stats.get("referee_data_quality") or input_stats.get("official_data_quality") or "").strip().lower() in {"low", "weak", "unknown"}:
            risk_flags.append("officiating data quality low")
        if status == "active_no_adjustment":
            no_bet_reason = "officiating data present but no directional adjustment"

    adjusted_true_probability = true_probability
    if true_probability is not None and base_model_active:
        adjusted_true_probability = max(0.01, min(0.99, true_probability + (adjustment_points / 100)))

    confidence_value = _safe_float(base_confidence)
    if confidence_value is None:
        confidence_value = 0
    if status == "active_adjustment":
        confidence_value += min(3, len(present_inputs))
    elif status == "inactive_base_model":
        confidence_value = 0
    elif not present_inputs:
        confidence_value = max(0, confidence_value - 2)
    officiating_confidence = max(0, min(100, round(confidence_value, 2)))

    if not present_inputs:
        risk_flags.append("officiating data unavailable")
    summary = (
        f"{module['official_type']} produced a {round(adjustment_points, 3)} probability-point adjustment."
        if status == "active_adjustment"
        else f"{module['official_type']} returned {status}."
    )
    logbook_fields = {
        "officiating_module_status": status,
        "officiating_official_type": module["official_type"],
        "officiating_edge_detected": status == "active_adjustment",
        "officiating_adjustment_probability_points": round(adjustment_points, 4),
        "officiating_confidence": officiating_confidence,
        "officiating_risk_flags": list(risk_flags),
        "officiating_no_bet_reason": no_bet_reason,
    }
    return {
        "officiating_module_status": status,
        "officiating_edge_detected": status == "active_adjustment",
        "officiating_adjustment_probability_points": round(adjustment_points, 4),
        "adjusted_true_probability": adjusted_true_probability,
        "affected_markets": _official_affected_markets(sport, market),
        "officiating_confidence": officiating_confidence,
        "officiating_risk_flags": risk_flags,
        "officiating_summary": summary,
        "officiating_no_bet_reason": no_bet_reason,
        "officiating_logbook_fields": logbook_fields,
        "official_type": module["official_type"],
        "official_inputs_present": present_inputs,
        "officials_module": module,
        "referee_inputs_present": present_inputs,
        "referee_adjustment_probability_points": round(adjustment_points, 4),
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
    confirmed_bets_allowed: bool = False,
    input_normalizer: Optional[str] = None,
    screenshot_alias_test_payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "sport_key": sport,
        "sport": sport,
        "display_name": display_name,
        "status": status,
        "model_level": model_level,
        "component_status": component_status,
        "confirmed_bets_allowed": confirmed_bets_allowed,
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
        "model_components": list(dict.fromkeys(list(model_components) + ["officials_context_module"] + list(SOCIAL_CROWD_MODEL_COMPONENTS))),
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
        "officials_module": _officials_module(sport),
        "sport_parameters": deepcopy(sport_parameters or {}),
        "supported_game_titles": list(supported_game_titles or []),
        "log_fields_required": list(BASE_LOG_FIELDS_REQUIRED),
        "input_normalizer": input_normalizer,
        "screenshot_alias_test_payload": deepcopy(screenshot_alias_test_payload) if screenshot_alias_test_payload else None,
    }


SPORT_MODEL_REGISTRY = [
    _sport(
        "baseball_mlb",
        "MLB",
        "negative_binomial_run_model",
        "Negative Binomial run model family",
        "negative_binomial",
        ["moneyline", "runline", "total", "team_total", "first_5_moneyline", "first_5_runline", "first_5_total", "player_prop", "live", "alt_line"],
        ["pitcher strikeouts", "pitcher outs recorded", "pitcher earned runs", "hits allowed", "batter hits", "total bases", "RBIs", "runs", "home runs", "stolen bases"],
        MLB_REQUIRED_CORE_INPUTS,
        MLB_OPTIONAL_ENRICHMENT_INPUTS,
        ["first 5 model", "full game model", "pitcher adjustment", "bullpen adjustment", "park factor", "weather adjustment", "lineup adjustment", "umpire adjustment placeholder", "optional Markov run expectancy later"],
        "negative binomial run simulation",
        ["Correlate pitcher strikeouts with opponent team total and first 5 markets."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "basketball_nba",
        "NBA",
        "possession_expected_score_model",
        "Possession based expected score model",
        "possession_expected_score",
        ["moneyline", "spread", "total", "team_total", "first_half", "second_half", "first_quarter", "first_quarter_moneyline", "first_quarter_spread", "first_quarter_total", "player_prop", "live", "alt_line"],
        ["points", "rebounds", "assists", "PRA", "threes", "steals", "blocks", "turnovers", "double double", "triple double"],
        ["pace", "offensive rating", "defensive rating", "Four Factors", "player usage", "minutes projection", "injury report"],
        ["on off adjustment", "shot quality", "fatigue", "rest", "travel"],
        ["pace", "offensive rating", "defensive rating", "Four Factors", "player usage", "minutes projection", "injury and on off adjustment", "shot quality engine registered now", "fatigue and rest adjustment"],
        "possession simulation",
        ["Correlate player PRA, team totals, pace, and same-game spread scripts."],
        sport_parameters={"league_baseline": "NBA", "pace_assumption": "NBA specific", "rotation_assumption": "NBA rotation depth"},
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "basketball_wnba",
        "WNBA",
        "wnba_possession_rating_monte_carlo_model",
        "wnba_possession_rating_monte_carlo_model",
        "wnba_possession_rating_monte_carlo",
        BASKETBALL_MODULE_MARKETS,
        BASKETBALL_MODULE_PROP_MARKETS,
        WNBA_REQUIRED_CORE_INPUTS,
        WNBA_OPTIONAL_ENRICHMENT_INPUTS,
        ["WNBA pace calibration", "WNBA scoring range", "WNBA possession volatility", "WNBA home court adjustment", "WNBA rest adjustment", "WNBA injury sensitivity", "WNBA travel sensitivity", "player minutes confidence"],
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
            "league_calibration_applied": "wnba",
        },
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "basketball_ncaab",
        "Men's College Basketball",
        "mens_college_basketball_possession_variance_model",
        "mens_college_basketball_possession_variance_model",
        "mens_college_basketball_possession_variance",
        BASKETBALL_MODULE_MARKETS,
        BASKETBALL_MODULE_PROP_MARKETS,
        COLLEGE_BASKETBALL_REQUIRED_CORE_INPUTS,
        COLLEGE_BASKETBALL_OPTIONAL_ENRICHMENT_INPUTS,
        ["men's college pace calibration", "ranking and strength adjustment", "conference strength", "blowout risk", "foul variance", "late-game free throw variance", "tempo volatility", "neutral court adjustment"],
        "men's college possession variance simulation",
        ["Team totals and spreads depend heavily on tempo and conference strength."],
        sport_parameters={"league_baseline": "NCAAB", "league_calibration_applied": "ncaab"},
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "basketball_ncaawb",
        "Women's College Basketball",
        "womens_college_basketball_possession_variance_model",
        "womens_college_basketball_possession_variance_model",
        "womens_college_basketball_possession_variance",
        BASKETBALL_MODULE_MARKETS,
        BASKETBALL_MODULE_PROP_MARKETS,
        COLLEGE_BASKETBALL_REQUIRED_CORE_INPUTS,
        COLLEGE_BASKETBALL_OPTIONAL_ENRICHMENT_INPUTS,
        ["women's college pace calibration", "women's scoring distribution", "top-team dominance adjustment", "ranking and strength adjustment", "conference strength", "blowout risk", "foul variance", "late-game variance", "tempo volatility", "neutral court adjustment"],
        "women's college possession variance simulation",
        ["Top-team dominance and conference imbalance require separate calibration from men's college basketball."],
        sport_parameters={"league_baseline": "NCAAWB", "league_calibration_applied": "ncaawb"},
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "americanfootball_nfl",
        "NFL",
        "drive_expected_points_model",
        "Drive based expected points model",
        "drive_expected_points",
        ["moneyline", "spread", "total", "team_total", "player_prop", "first_half", "first_quarter", "live", "alt_line"],
        ["passing yards", "passing touchdowns", "interceptions", "completions", "attempts", "rushing yards", "rushing attempts", "receiving yards", "receptions", "anytime touchdown", "first touchdown", "sacks", "kicking points"],
        NFL_REQUIRED_CORE_INPUTS,
        NFL_OPTIONAL_ENRICHMENT_INPUTS,
        ["EPA", "success rate", "pace", "QB adjustment", "red zone efficiency", "weather", "injuries", "garbage time filtering", "offensive line adjustment registered now", "defensive line adjustment registered now", "football trench engine registered now"],
        "drive simulation",
        ["QB passing over with WR receiving over; bad offensive line with opposing sacks over."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "americanfootball_ncaaf",
        "College Football",
        "college_football_epa_drive_rating_monte_carlo_model",
        "college_football_epa_drive_rating_monte_carlo_model",
        "college_football_epa_drive_rating_monte_carlo",
        COLLEGE_FOOTBALL_MARKETS,
        COLLEGE_FOOTBALL_PROP_MARKETS,
        COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS,
        COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS,
        ["college EPA drive rating", "drive volatility", "conference strength", "home field adjustment", "neutral site adjustment", "tempo spread", "explosive play variance", "blowout risk", "garbage-time risk", "weather sensitivity", "QB injury sensitivity", "ranking and power-rating adjustment"],
        "college football Monte Carlo drive simulation",
        ["College variance requires tighter exposure caps for correlated sides, totals, and player props."],
        sport_parameters={"league_baseline": "NCAAF", "league_calibration_applied": "ncaaf"},
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "soccer",
        "Soccer",
        "poisson_dixon_coles_bivariate_goal_model",
        "Poisson with Dixon Coles and Bivariate Poisson components",
        "poisson_with_score_dependence",
        ["moneyline", "three_way_moneyline", "home_draw_away", "draw_no_bet", "double_chance", "asian_handicap", "spread", "total", "team_total", "both_teams_to_score", "correct_score", "first_half_moneyline", "first_half_total", "first_half_team_total", "second_half_moneyline", "second_half_total", "corners", "team_corners", "cards", "team_cards", "player_prop", "anytime_goal_scorer", "first_goal_scorer", "live", "alt_line"],
        ["anytime scorer", "first goal scorer", "shots", "shots on target", "assists", "cards", "corners", "saves"],
        SOCCER_REQUIRED_CORE_INPUTS,
        SOCCER_OPTIONAL_ENRICHMENT_INPUTS,
        ["Poisson baseline", "Dixon Coles low score correction", "Bivariate Poisson score dependence", "time decay weighting", "optional xG adjustment", "field tilt engine registered now", "post shot xG engine registered now", "Monte Carlo simulation"],
        "correlated_poisson",
        ["Field tilt with soccer corners; xG pressure with team total and next goal markets."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "icehockey_nhl",
        "NHL",
        "poisson_bivariate_goalie_special_teams_model",
        "Poisson with bivariate goalie and special teams components",
        "correlated_poisson",
        ["moneyline", "three_way_moneyline", "puckline", "spread", "total", "team_total", "first_period_moneyline", "first_period_total", "first_period_team_total", "second_period_moneyline", "second_period_total", "third_period_moneyline", "third_period_total", "regulation_moneyline", "draw_no_bet", "alternate_puckline", "alternate_total", "player_prop", "anytime_goal_scorer", "first_goal_scorer", "live"],
        ["goals", "assists", "points", "shots on goal", "blocked shots", "goalie saves", "anytime goal scorer", "first goal scorer"],
        NHL_REQUIRED_CORE_INPUTS,
        NHL_OPTIONAL_ENRICHMENT_INPUTS,
        ["Poisson or correlated Poisson goal model", "Bivariate Poisson or correlated goal dependence", "goalie adjustment", "special teams adjustment", "period specific lambdas", "time decay weighting", "Royal Road and pre shot movement engine registered now", "Monte Carlo simulation"],
        "Monte Carlo simulation",
        ["Royal Road offense with NHL team total over and player shots."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "tennis",
        "Tennis",
        "elo_serve_return_markov_tennis_model",
        "Elo serve return Markov tennis model",
        "point_game_set_simulation",
        ["moneyline", "match_winner", "set_handicap", "game_handicap", "total_games", "first_set_moneyline", "first_set_total_games", "correct_score", "player_prop", "aces", "double_faults", "break_points", "service_games_won", "return_games_won", "live"],
        ["aces", "double faults", "break points", "service games won", "return games won", "total games played", "sets played"],
        TENNIS_REQUIRED_CORE_INPUTS,
        TENNIS_OPTIONAL_ENRICHMENT_INPUTS,
        ["serve return model", "point game set simulation", "surface adjustment", "fatigue adjustment", "Elo", "player form", "tournament context"],
        "point game set simulation",
        ["Aces, service holds, and total games are strongly related."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "mma_mixed_martial_arts",
        "MMA",
        "fighter_striking_grappling_finish_model",
        "fighter_striking_grappling_finish_model",
        "fighter_finish_classification",
        ["moneyline", "method_of_victory", "fighter_by_ko_tko", "fighter_by_submission", "fighter_by_decision", "opponent_by_ko_tko", "opponent_by_submission", "opponent_by_decision", "fight_goes_distance", "fight_does_not_go_distance", "over_rounds", "under_rounds", "round_group", "exact_round", "double_chance", "knockdown_prop", "takedown_prop", "significant_strikes_prop", "submission_attempt_prop", "live"],
        ["KO TKO", "submission", "decision", "round group", "fight duration", "knockdowns", "takedowns", "significant strikes", "submission attempts"],
        COMBAT_REQUIRED_CORE_INPUTS,
        COMBAT_OPTIONAL_ENRICHMENT_INPUTS,
        ["Elo", "recent form", "striking model", "grappling model", "finish split", "duration model", "referee and judges context"],
        "classification with duration model",
        ["Method, distance, and round group are highly correlated."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "boxing",
        "Boxing",
        "fighter_striking_grappling_finish_model",
        "fighter_striking_grappling_finish_model",
        "fighter_finish_classification",
        ["moneyline", "method_of_victory", "fighter_by_ko_tko", "fighter_by_decision", "opponent_by_ko_tko", "opponent_by_decision", "fight_goes_distance", "fight_does_not_go_distance", "over_rounds", "under_rounds", "round_group", "exact_round", "double_chance", "knockdown_prop", "significant_strikes_prop", "live"],
        ["KO TKO", "decision", "draw", "round group", "fight duration", "knockdowns", "significant strikes"],
        COMBAT_REQUIRED_CORE_INPUTS,
        COMBAT_OPTIONAL_ENRICHMENT_INPUTS,
        ["Elo", "recent form", "striking model", "durability", "finish split", "duration model", "referee and judges context"],
        "classification with duration model",
        ["Decision, draw, and distance prices require correlated review."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
    ),
    _sport(
        "golf",
        "Golf",
        "strokes_gained_course_fit_monte_carlo_model",
        "strokes_gained_course_fit_monte_carlo_model",
        "strokes_gained_course_fit_monte_carlo",
        ["outright_winner", "top_5", "top_10", "top_20", "make_cut", "miss_cut", "tournament_matchup", "round_matchup", "three_ball", "first_round_leader", "top_n_finish", "finishing_position", "player_prop", "birdies_prop", "eagles_prop", "fairways_hit_prop", "greens_in_regulation_prop", "putts_prop", "round_score_prop"],
        ["top finish", "make cut", "matchup", "round score", "birdies", "eagles", "fairways hit", "greens in regulation", "putts"],
        GOLF_REQUIRED_CORE_INPUTS,
        GOLF_OPTIONAL_ENRICHMENT_INPUTS,
        ["strokes gained total", "strokes gained off tee", "strokes gained approach", "strokes gained around green", "strokes gained putting", "course fit", "course history", "field strength", "cut projection", "weather draw", "Monte Carlo finish distribution"],
        "strokes gained course-fit Monte Carlo simulation",
        ["Outrights, top finish ladders, and matchup exposure should be grouped by golfer."],
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
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
        "cricket_run_rate_wicket_resource_monte_carlo_model",
        "cricket_run_rate_wicket_resource_monte_carlo_model",
        "run_rate_wicket_resource_monte_carlo",
        CRICKET_MARKETS,
        CRICKET_PROP_MARKETS,
        CRICKET_REQUIRED_CORE_INPUTS,
        CRICKET_OPTIONAL_ENRICHMENT_INPUTS,
        ["phase run-rate model", "wicket resource model", "innings Monte Carlo simulation", "toss impact", "venue impact", "pitch condition", "weather", "batting order", "bowler matchup"],
        "run-rate wicket-resource Monte Carlo",
        ["Toss, pitch, innings runs, and player runs can change together."],
        sport_parameters={"league_calibration_applied": "cricket"},
        component_status=COMPONENT_STATUS_ACTIVE,
        model_level=MODEL_LEVEL_PROJECTION_READY,
        confirmed_bets_allowed=True,
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

_INPUT_NORMALIZER_BY_SPORT = {
    "baseball_mlb": "mlb_input_normalizer",
    "basketball_nba": "nba_input_normalizer",
    "basketball_wnba": "wnba_input_normalizer",
    "basketball_ncaab": "mens_college_basketball_input_normalizer",
    "basketball_ncaawb": "womens_college_basketball_input_normalizer",
    "americanfootball_nfl": "nfl_input_normalizer",
    "americanfootball_ncaaf": "college_football_input_normalizer",
    "soccer": "soccer_input_normalizer",
    "icehockey_nhl": "nhl_input_normalizer",
    "tennis": "tennis_input_normalizer",
    "mma_mixed_martial_arts": "combat_input_normalizer",
    "boxing": "combat_input_normalizer",
    "golf": "golf_input_normalizer",
    "cricket": "cricket_input_normalizer",
}

_ACTIVE_SCREENSHOT_ALIAS_TEST_PAYLOADS: dict[str, dict[str, Any]] = {
    "basketball_nba": {
        "sport": "nba", "league": "NBA", "event": "Knicks at Celtics", "market": "moneyline",
        "selection": "Celtics", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "standard",
        "input_stats": {
            "team_name": "Celtics", "opponent_name": "Knicks", "selection_name": "Celtics", "matchup": "Knicks at Celtics",
            "home_away": "home", "current_odds": 100, "team_pace": 101.5, "opponent_pace": 98.2,
            "team_offensive_rating": 121.0, "opponent_offensive_rating": 113.0, "team_defensive_rating": 110.0,
            "opponent_defensive_rating": 116.0, "team_efg_percent": 0.575, "opponent_efg_percent": 0.535,
            "team_turnover_percent": 0.118, "opponent_turnover_percent": 0.136, "team_offensive_rebound_percent": 0.285,
            "opponent_offensive_rebound_percent": 0.245, "team_free_throw_rate": 0.235, "opponent_free_throw_rate": 0.205,
            "key_player_usage_available": True, "minutes_projection_available": True, "injury_report_status": "clean",
        },
    },
    "basketball_wnba": {
        "sport": "wnba", "league": "WNBA", "event": "Aces at Liberty", "teams": ["Aces", "Liberty"],
        "market": "moneyline", "selection": "Liberty", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "game": "Aces at Liberty", "home": "Liberty", "away": "Aces", "team_name": "Liberty", "opponent_name": "Aces",
            "favorite": "Liberty", "home_off_rating": 108.5, "home_def_rating": 96.2, "away_off_rating": 103.1, "away_def_rating": 101.8,
            "home_pace": 79.4, "away_pace": 77.8, "home_efg": 52.8, "away_efg": 49.6, "home_tov": 13.1, "away_tov": 14.4,
            "home_oreb": 51.5, "away_oreb": 48.7, "home_ft_rate": 25.5, "away_ft_rate": 22.1, "home_injury_adjustment": 0.2,
            "away_injury_adjustment": -0.6, "home_rest_days": 3, "away_rest_days": 2, "home_travel_fatigue": 0.1, "away_travel_fatigue": 0.8,
            "book_count": 8,
        },
    },
    "basketball_ncaab": {
        "sport": "ncaab", "league": "NCAAB", "event": "Duke vs North Carolina", "teams": ["North Carolina", "Duke"],
        "market": "moneyline", "selection": "Duke", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "matchup": "Duke vs North Carolina", "home": "Duke", "away": "North Carolina", "team_name": "Duke", "opponent_name": "North Carolina",
            "pick": "Duke", "home_off_rating": 116.0, "home_def_rating": 94.5, "away_off_rating": 111.0, "away_def_rating": 99.0,
            "home_pace": 70.5, "away_pace": 69.1, "home_efg": 54.0, "away_efg": 50.4, "home_tov": 13.0, "away_tov": 15.2,
            "home_oreb": 53.0, "away_oreb": 49.5, "home_ft_rate": 31.0, "away_ft_rate": 27.5, "home_rest_days": 5,
            "away_rest_days": 3, "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.4, "home_ap_rank": 4, "away_ap_rank": 16,
            "home_kenpom_rating": 28.5, "away_kenpom_rating": 20.0, "home_conference_rating": 8.5, "away_conference_rating": 7.8,
            "home_experience": 6.2, "away_experience": 5.1, "home_3p_rate": 38.5, "away_3p_rate": 34.1, "home_ft_pct": 76.0,
            "away_ft_pct": 71.5, "book_count": 8,
        },
    },
    "basketball_ncaawb": {
        "sport": "ncaawb", "league": "NCAAWB", "event": "UConn vs South Carolina", "teams": ["UConn", "South Carolina"],
        "market": "moneyline", "selection": "South Carolina", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "matchup": "UConn vs South Carolina", "home": "South Carolina", "away": "UConn", "team_name": "South Carolina", "opponent_name": "UConn",
            "pick": "South Carolina", "home_off_rating": 114.0, "home_def_rating": 88.0, "away_off_rating": 108.0, "away_def_rating": 94.5,
            "home_pace": 72.2, "away_pace": 70.4, "home_efg": 53.5, "away_efg": 49.8, "home_tov": 12.5, "away_tov": 14.0,
            "home_oreb": 56.0, "away_oreb": 50.1, "home_ft_rate": 28.0, "away_ft_rate": 24.4, "home_rest_days": 4,
            "away_rest_days": 3, "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.3, "home_ap_rank": 1, "away_ap_rank": 7,
            "home_net_rating": 31.0, "away_net_rating": 23.0, "home_conference_rating": 8.8, "away_conference_rating": 8.1,
            "home_experience": 6.8, "away_experience": 6.0, "home_3p_rate": 36.5, "away_3p_rate": 33.2, "home_ft_pct": 75.5,
            "away_ft_pct": 72.0, "book_count": 8,
        },
    },
    "americanfootball_nfl": {
        "sport": "nfl", "league": "NFL", "event": "Jets at Bills", "market": "moneyline",
        "selection": "Bills", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "team_name": "Bills", "opponent_name": "Jets", "selection_name": "Bills", "game": "Jets at Bills",
            "home_away": "home", "current_odds": 100, "team_offensive_epa_per_play": 0.12,
            "opponent_offensive_epa_per_play": 0.03, "team_defensive_epa_per_play": -0.04,
            "opponent_defensive_epa_per_play": 0.02, "team_success_rate": 0.47, "opponent_success_rate": 0.42,
            "team_defensive_success_rate_allowed": 0.40, "opponent_defensive_success_rate_allowed": 0.44,
            "team_explosive_play_rate": 0.12, "opponent_explosive_play_rate": 0.09,
            "team_explosive_play_rate_allowed": 0.09, "opponent_explosive_play_rate_allowed": 0.11,
            "team_turnover_rate": 0.09, "opponent_turnover_rate": 0.12, "team_pressure_rate_allowed": 0.28,
            "opponent_pressure_rate_allowed": 0.34, "team_pressure_rate_generated": 0.36,
            "opponent_pressure_rate_generated": 0.29, "team_red_zone_td_rate": 0.62,
            "opponent_red_zone_td_rate": 0.54, "team_red_zone_td_rate_allowed": 0.50,
            "opponent_red_zone_td_rate_allowed": 0.58, "team_pace_seconds_per_play": 27.5,
            "opponent_pace_seconds_per_play": 29.0, "qb_status": "healthy", "offensive_line_health": "good",
            "injury_report_status": "clean",
        },
    },
    "americanfootball_ncaaf": {
        "sport": "ncaaf", "league": "NCAAF", "event": "Ohio State vs Michigan", "teams": ["Michigan", "Ohio State"],
        "market": "moneyline", "selection": "Ohio State", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "game": "Ohio State vs Michigan", "home": "Ohio State", "away": "Michigan", "team_name": "Ohio State",
            "opponent_name": "Michigan", "favorite": "Ohio State", "home_epa_off": 0.23, "away_epa_off": 0.15,
            "home_epa_def": -0.08, "away_epa_def": -0.02, "home_sr": 0.49, "away_sr": 0.44,
            "home_def_sr_allowed": 0.37, "away_def_sr_allowed": 0.41, "home_explosive_rate": 0.18,
            "away_explosive_rate": 0.14, "home_explosive_allowed": 0.10, "away_explosive_allowed": 0.13,
            "home_pace": 25.4, "away_pace": 27.6, "home_plays_per_game": 73, "away_plays_per_game": 69,
            "home_ppd": 2.95, "away_ppd": 2.45, "home_ppd_allowed": 1.55, "away_ppd_allowed": 1.92,
            "home_rz_td": 0.68, "away_rz_td": 0.58, "home_rz_td_allowed": 0.44, "away_rz_td_allowed": 0.52,
            "home_turnover_margin": 0.6, "away_turnover_margin": 0.1, "home_havoc_rate": 19.0, "away_havoc_rate": 16.0,
            "home_havoc_allowed": 12.0, "away_havoc_allowed": 15.0, "home_qb": 88.0, "away_qb": 79.0,
            "home_qb_injury": 0.0, "away_qb_injury": -0.5, "home_ol": 86.0, "away_ol": 78.0,
            "home_dl": 88.0, "away_dl": 80.0, "home_st": 74.0, "away_st": 70.0, "home_field_advantage": 3.0,
            "neutral_site": False, "wind_mph": 6, "precipitation": "none", "home_rest_days": 7, "away_rest_days": 6,
            "home_travel_fatigue": 0.0, "away_travel_fatigue": 0.6, "home_strength_of_schedule": 8.6,
            "away_strength_of_schedule": 8.1, "home_ap_rank": 2, "away_ap_rank": 8, "home_sp_rating": 29.5,
            "away_sp_rating": 21.0, "home_conference_rating": 9.0, "away_conference_rating": 8.4, "book_count": 8,
        },
    },
    "baseball_mlb": {
        "sport": "mlb", "league": "MLB", "event": "Giants at Dodgers", "market": "moneyline",
        "selection": "Dodgers", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "team_name": "Dodgers", "opponent_name": "Giants", "selection_name": "Dodgers", "game": "Giants at Dodgers",
            "home_away": "home", "market_name": "moneyline", "current_odds": 100, "team_projected_runs": 4.8,
            "opponent_projected_runs": 4.1, "team_starting_pitcher": "Dodgers SP", "opponent_starting_pitcher": "Giants SP",
            "team_starting_pitcher_era": 3.2, "opponent_starting_pitcher_era": 4.2, "team_starting_pitcher_fip": 3.3,
            "opponent_starting_pitcher_fip": 4.4, "team_starting_pitcher_xfip": 3.4, "opponent_starting_pitcher_xfip": 4.3,
            "team_starting_pitcher_k_rate": 0.27, "opponent_starting_pitcher_k_rate": 0.22,
            "team_starting_pitcher_bb_rate": 0.07, "opponent_starting_pitcher_bb_rate": 0.09,
            "team_starting_pitcher_hr_rate": 0.9, "opponent_starting_pitcher_hr_rate": 1.2,
            "team_starting_pitcher_innings_projection": 5.8, "opponent_starting_pitcher_innings_projection": 5.1,
            "team_bullpen_era": 3.6, "opponent_bullpen_era": 4.3, "team_bullpen_fip": 3.7,
            "opponent_bullpen_fip": 4.2, "team_bullpen_recent_usage": 2.0, "opponent_bullpen_recent_usage": 3.2,
            "team_bullpen_rest_status": "rested", "opponent_bullpen_rest_status": "tired", "team_woba": 0.335,
            "opponent_woba": 0.310, "team_xwoba": 0.340, "opponent_xwoba": 0.315, "team_wrc_plus": 112,
            "opponent_wrc_plus": 96, "team_iso": 0.180, "opponent_iso": 0.145, "team_k_rate": 0.21,
            "opponent_k_rate": 0.24, "team_bb_rate": 0.09, "opponent_bb_rate": 0.075, "park_factor_runs": 1.02,
            "park_factor_home_runs": 1.05, "weather_temperature": 74, "weather_wind_mph": 8,
            "weather_wind_direction": "left to right", "roof_status": "open", "injury_report_status": "clean",
            "lineup_status": "confirmed",
        },
    },
    "soccer": {
        "sport": "football", "league": "EPL", "event": "Arsenal vs Chelsea", "market": "three_way_moneyline",
        "selection": "Arsenal", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "team_name": "Arsenal", "opponent_name": "Chelsea", "selection_name": "Arsenal", "matchup": "Arsenal vs Chelsea",
            "home_away": "home", "market_name": "three_way_moneyline", "league_name": "soccer_epl", "current_odds": 100,
            "match_date": "2026-08-15", "team_expected_goals": 1.75, "opponent_expected_goals": 1.05,
            "team_xg_for": 1.80, "opponent_xg_for": 1.20, "team_xg_against": 1.05, "opponent_xg_against": 1.45,
            "team_goals_for_per_match": 2.0, "opponent_goals_for_per_match": 1.35, "team_goals_against_per_match": 0.95,
            "opponent_goals_against_per_match": 1.45, "team_shots_per_match": 15.2, "opponent_shots_per_match": 11.3,
            "team_shots_allowed_per_match": 9.2, "opponent_shots_allowed_per_match": 13.4,
            "team_shots_on_target_per_match": 5.8, "opponent_shots_on_target_per_match": 4.1,
            "team_shots_on_target_allowed_per_match": 3.1, "opponent_shots_on_target_allowed_per_match": 4.9,
            "team_big_chances_per_match": 2.8, "opponent_big_chances_per_match": 1.7,
            "team_big_chances_allowed_per_match": 1.2, "opponent_big_chances_allowed_per_match": 2.2,
            "team_possession_percent": 58, "opponent_possession_percent": 49, "team_recent_form_points": 12,
            "opponent_recent_form_points": 8, "team_rest_days": 6, "opponent_rest_days": 4,
            "injury_report_status": "clean", "lineup_status": "confirmed",
        },
    },
    "icehockey_nhl": {
        "sport": "nhl", "league": "NHL", "event": "Bruins at Rangers", "market": "moneyline",
        "selection": "Rangers", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "team_name": "Rangers", "opponent_name": "Bruins", "selection_name": "Rangers", "game": "Bruins at Rangers",
            "home_away": "home", "market_name": "moneyline", "league_name": "nhl", "current_odds": 100, "game_date": "2026-11-12",
            "team_projected_goals": 3.35, "opponent_projected_goals": 2.75, "team_xg_for_per_game": 3.25,
            "opponent_xg_for_per_game": 2.85, "team_xg_against_per_game": 2.70, "opponent_xg_against_per_game": 3.05,
            "team_goals_for_per_game": 3.30, "opponent_goals_for_per_game": 2.90, "team_goals_against_per_game": 2.65,
            "opponent_goals_against_per_game": 3.10, "team_shots_for_per_game": 32.0, "opponent_shots_for_per_game": 29.0,
            "team_shots_against_per_game": 28.0, "opponent_shots_against_per_game": 31.0,
            "team_scoring_chances_for_per_game": 29.0, "opponent_scoring_chances_for_per_game": 25.0,
            "team_scoring_chances_against_per_game": 24.0, "opponent_scoring_chances_against_per_game": 28.0,
            "team_high_danger_chances_for_per_game": 12.0, "opponent_high_danger_chances_for_per_game": 9.0,
            "team_high_danger_chances_against_per_game": 8.0, "opponent_high_danger_chances_against_per_game": 11.0,
            "team_power_play_percent": 24.0, "opponent_power_play_percent": 19.0, "team_penalty_kill_percent": 83.0,
            "opponent_penalty_kill_percent": 77.0, "team_recent_form_points": 8, "opponent_recent_form_points": 5,
            "team_rest_days": 2, "opponent_rest_days": 1, "team_goalie_confirmed": True, "opponent_goalie_confirmed": True,
            "team_starting_goalie_save_percent": 0.918, "opponent_starting_goalie_save_percent": 0.904,
            "team_starting_goalie_gsaax": 6.0, "opponent_starting_goalie_gsaax": -2.0,
            "injury_report_status": "clean", "lineup_status": "confirmed",
        },
    },
    "tennis": {
        "sport": "tennis", "league": "ATP", "event": "Novak Djokovic vs Carlos Alcaraz", "market": "moneyline",
        "selection": "Novak Djokovic", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "athlete": "Novak Djokovic", "opponent_name": "Carlos Alcaraz", "selection_name": "Novak Djokovic",
            "market_name": "moneyline", "league_name": "ATP", "tournament_name": "Wimbledon", "match_date": "2026-05-20",
            "surface": "grass", "best_of_sets": 3, "player_rank": 2, "opponent_rank": 3, "player_elo": 2200,
            "opponent_elo": 2075, "player_recent_win_percent": 70, "opponent_recent_win_percent": 60,
            "player_fatigue_rating": 15, "opponent_fatigue_rating": 22, "player_days_rest": 3, "opponent_days_rest": 2,
            "player_serve_hold_percent": 86, "opponent_serve_hold_percent": 82, "player_first_serve_percent": 65,
            "opponent_first_serve_percent": 63, "player_surface_win_percent": 78, "opponent_surface_win_percent": 70,
            "current_odds": 100,
        },
    },
    "mma_mixed_martial_arts": {
        "sport": "ufc", "league": "UFC", "event": "Islam Makhachev vs Charles Oliveira", "market": "moneyline",
        "selection": "Islam Makhachev", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "fighter_name": "Islam Makhachev", "opponent_name": "Charles Oliveira", "selection_name": "Islam Makhachev",
            "fight_date": "2026-07-10", "weight_class": "Lightweight", "fighter_moneyline": 100, "fighter_elo": 1860,
            "opponent_elo": 1775, "fighter_recent_win_percent": 85, "opponent_recent_win_percent": 70,
            "fighter_finish_rate": 62, "opponent_finish_rate": 70, "fighter_ko_tko_rate": 18, "opponent_ko_tko_rate": 35,
            "fighter_submission_rate": 42, "opponent_submission_rate": 30, "fighter_decision_rate": 40,
            "opponent_decision_rate": 35, "fighter_strikes_landed_per_min": 3.2, "opponent_strikes_landed_per_min": 3.5,
            "fighter_strikes_absorbed_per_min": 1.8, "opponent_strikes_absorbed_per_min": 3.1,
            "fighter_striking_accuracy": 58, "opponent_striking_accuracy": 52, "fighter_striking_defense": 64,
            "opponent_striking_defense": 53, "fighter_takedown_average": 3.4, "opponent_takedown_average": 2.2,
            "fighter_takedown_accuracy": 61, "opponent_takedown_accuracy": 44, "fighter_takedown_defense": 88,
            "opponent_takedown_defense": 57, "fighter_submission_average": 1.1, "opponent_submission_average": 0.8,
            "fighter_age": 34, "opponent_age": 36, "fighter_reach": 70, "opponent_reach": 74, "fighter_height": 70,
            "opponent_height": 70, "fighter_stance": "southpaw", "opponent_stance": "orthodox", "fighter_days_rest": 180,
            "opponent_days_rest": 160, "current_odds": 100,
        },
    },
    "boxing": {
        "sport": "boxing", "league": "Boxing", "event": "Fighter A vs Fighter B", "market": "moneyline",
        "selection": "Fighter A", "odds_american": 100, "bankroll": 1000, "unit_size": 25, "risk_profile": "moderate",
        "input_stats": {
            "fighter_name": "Fighter A", "opponent_name": "Fighter B", "selection_name": "Fighter A",
            "fight_date": "2026-09-12", "promotion": "Top Rank", "weight_class": "Welterweight", "scheduled_rounds": 12,
            "fighter_moneyline": 100, "fighter_elo": 1780, "opponent_elo": 1710, "fighter_recent_win_percent": 80,
            "opponent_recent_win_percent": 68, "fighter_finish_rate": 58, "opponent_finish_rate": 52,
            "fighter_ko_tko_rate": 44, "opponent_ko_tko_rate": 37, "fighter_submission_rate": 0, "opponent_submission_rate": 0,
            "fighter_decision_rate": 56, "opponent_decision_rate": 63, "fighter_strikes_landed_per_min": 4.1,
            "opponent_strikes_landed_per_min": 3.7, "fighter_strikes_absorbed_per_min": 2.5,
            "opponent_strikes_absorbed_per_min": 3.0, "fighter_striking_accuracy": 48, "opponent_striking_accuracy": 43,
            "fighter_striking_defense": 61, "opponent_striking_defense": 56, "fighter_takedown_average": 0,
            "opponent_takedown_average": 0, "fighter_takedown_accuracy": 0, "opponent_takedown_accuracy": 0,
            "fighter_takedown_defense": 100, "opponent_takedown_defense": 100, "fighter_submission_average": 0,
            "opponent_submission_average": 0, "fighter_age": 29, "opponent_age": 32, "fighter_reach": 72,
            "opponent_reach": 70, "fighter_height": 70, "opponent_height": 69, "fighter_stance": "orthodox",
            "opponent_stance": "southpaw", "fighter_days_rest": 150, "opponent_days_rest": 130,
            "fighter_injury_status": "healthy", "opponent_injury_status": "healthy", "current_odds": 100,
        },
    },
    "golf": {
        "sport": "golf", "league": "PGA", "event": "Masters Tournament", "market": "top_10",
        "selection": "Scottie Scheffler", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "screenshot_text": "Scottie Scheffler top 10 +100",
        "input_stats": {
            "golfer": "Scottie Scheffler", "tournament": "Masters Tournament", "course_name": "Augusta National",
            "field": 89, "world_rank": 1, "sg_total": 2.65, "sg_off_tee": 0.85, "sg_approach": 1.15,
            "sg_around_green": 0.32, "sg_putting": 0.33, "recent_form_rank": 2, "scoring_average": 68.9,
            "fit_score": 92, "history_score": 88, "field_strength": 91, "projected_cut_line": 2,
            "wind_rating": 4, "difficulty_rating": 8, "current_odds": 100,
        },
    },
    "cricket": {
        "sport": "cricket", "league": "IPL", "event": "Mumbai Indians vs Chennai Super Kings",
        "teams": ["Mumbai Indians", "Chennai Super Kings"], "market": "match_winner",
        "selection": "Mumbai Indians", "odds_american": 100, "bankroll": 1000, "unit_size": 25,
        "risk_profile": "moderate", "source_type": "chatgpt_parsed",
        "screenshot_text": "Mumbai Indians match winner +100 vs Chennai Super Kings",
        "visible_markets": ["match_winner", "total_runs", "player_runs"],
        "input_stats": {
            "match": "Mumbai Indians vs Chennai Super Kings", "team_name": "Mumbai Indians",
            "opponent_name": "Chennai Super Kings", "home": "Mumbai Indians", "away": "Chennai Super Kings",
            "batting": "Mumbai Indians", "bowling": "Chennai Super Kings", "format": "ipl",
            "ground": "Wankhede Stadium", "surface": "balanced", "weather": "humid",
            "toss": "Mumbai Indians", "decision": "bowl", "team_bat_rating": 86,
            "opp_bat_rating": 82, "team_bowl_rating": 84, "opp_bowl_rating": 80,
            "team_field_rating": 82, "opp_field_rating": 78, "team_form": 84, "opp_form": 77,
            "team_pp_rr": 9.2, "opp_pp_rr": 8.5, "team_middle_rr": 8.4, "opp_middle_rr": 7.8,
            "team_death_rr": 11.2, "opp_death_rr": 10.1, "team_wicket_loss": 0.24,
            "opp_wicket_loss": 0.28, "team_wicket_rate": 0.31, "opp_wicket_rate": 0.27,
            "team_boundary_pct": 0.19, "opp_boundary_pct": 0.17, "team_dot_pct": 0.34,
            "opp_dot_pct": 0.37, "team_chase": 88, "opp_chase": 80, "team_defend": 82,
            "opp_defend": 79, "venue_avg_score": 174, "chase_win_pct": 0.56,
            "spin_assist": 0.48, "pace_assist": 0.52, "dew": 0.35, "wind": 0.12,
            "player_name": "Rohit Sharma", "player_team": "Mumbai Indians", "role": "batter",
            "bat_pos": 1, "batting_avg": 31.5, "batting_strike_rate": 142, "recent_runs": 36,
            "boundary_rate": 0.17, "six_rate": 0.06, "fifty_rate": 0.24, "hundred_rate": 0.04,
            "duck_rate": 0.08, "bowling_avg": 0, "economy": 0, "bowling_strike_rate": 0,
            "recent_wickets": 0, "overs_proj": 0, "balls_faced_proj": 24, "runs_proj": 34.5,
            "wickets_proj": 0.1, "sixes_proj": 1.6, "fours_proj": 3.2, "book_count": 8,
            "current_odds": 100,
        },
    },
}

for _sport_config in SPORT_MODEL_REGISTRY:
    _sport_key = _sport_config["sport_key"]
    if _sport_config.get("confirmed_bets_allowed"):
        _sport_config["input_normalizer"] = _INPUT_NORMALIZER_BY_SPORT.get(_sport_key)
        _sport_config["screenshot_alias_test_payload"] = deepcopy(_ACTIVE_SCREENSHOT_ALIAS_TEST_PAYLOADS.get(_sport_key))
        _sport_config["league_calibration_applied"] = _sport_config.get("sport_parameters", {}).get("league_calibration_applied")


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
    raw = (sport_key or "").strip().lower().replace("-", "_")
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
            "officials_module",
        ):
            if required_field not in sport:
                raise ValueError(f"{sport.get('sport_key')} is missing {required_field}")
        if sport["officials_module"]["module_name"] != "officials_context_module":
            raise ValueError(f"{sport.get('sport_key')} has unsupported officials module")


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
            "confirmed_bet_enabled_sports": sum(1 for sport in sports if sport.get("confirmed_bets_allowed")),
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
    bankroll_value = _safe_float(bankroll, 0) or 0
    unit_value = _safe_float(unit_size, 0) or 0
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


def _first_present(input_stats: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if input_stats.get(key) is not None:
            return input_stats.get(key)
    return None


def _parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    parsed = _parse_number(value)
    return default if parsed is None else parsed


def _social_crowd_score(value: Any, default: float = 0) -> float:
    parsed = _parse_number(value)
    if parsed is not None:
        return parsed
    text = str(value or "").strip().lower()
    return float(SOCIAL_CROWD_TEXT_SCORES.get(text, default))


def _safe_payload_dict(payload: Any) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _normalize_input_stats(value: Any) -> tuple[dict[str, Any], list[str]]:
    if isinstance(value, dict):
        return dict(value), []
    return {}, ["input_stats_missing_or_invalid"]


def _is_truthy_signal(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value > 0
    return str(value).strip().lower() in {"true", "yes", "y", "1", "high", "elevated", "unconfirmed", "rumor", "present"}


def _is_confirmed(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "y", "1", "confirmed", "verified"}


def _normalize_social_crowd_input_stats(input_stats: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(input_stats) if isinstance(input_stats, dict) else {}
    alias_map = {
        "social media sentiment score": ("social media sentiment score", "social_sentiment"),
        "crowd consensus percentage": ("crowd consensus percentage", "crowd_consensus"),
        "public betting percentage": ("public betting percentage", "public_betting_percent"),
        "money percentage": ("money percentage", "public_money_percent", "sharp_money_percent"),
        "sharp money percentage": ("sharp money percentage", "sharp_money_percent"),
        "news velocity score": ("news velocity score", "news_velocity"),
        "injury rumor flag": ("injury rumor flag", "injury_rumor"),
        "lineup rumor flag": ("lineup rumor flag",),
        "beat writer signal": ("beat writer signal", "beat_writer_signal"),
        "Reddit or forum sentiment": ("Reddit or forum sentiment", "reddit_signal", "forum_signal"),
        "Discord or community signal": ("Discord or community signal", "discord_signal"),
        "media hype score": ("media hype score", "market_narrative"),
        "sentiment source quality": ("sentiment source quality", "source_quality"),
        "rumor risk": ("rumor risk", "rumor_risk"),
        "rumor signal": ("rumor signal", "rumor_risk", "injury_rumor", "lineup rumor flag"),
        "line movement reason": ("line movement reason", "line_movement_reason"),
    }
    for canonical, aliases in alias_map.items():
        normalized[canonical] = _first_present(normalized, *aliases)
    for numeric_field in (
        "social media sentiment score",
        "crowd consensus percentage",
        "public betting percentage",
        "money percentage",
        "sharp money percentage",
        "news velocity score",
        "media hype score",
        "sentiment source quality",
        "sample_size",
    ):
        if normalized.get(numeric_field) is not None:
            normalized[numeric_field] = _social_crowd_score(normalized.get(numeric_field))
    normalized["social_signal_present"] = normalized.get("social media sentiment score") is not None
    normalized["crowd_signal_present"] = normalized.get("crowd consensus percentage") is not None
    normalized["rumor_signal_present"] = (
        normalized.get("rumor risk") is not None
        or normalized.get("injury rumor flag") is not None
        or normalized.get("lineup rumor flag") is not None
    )
    return normalized


def build_social_crowd_calibration_layer(input_stats: dict[str, Any]) -> dict[str, Any]:
    input_stats = _normalize_social_crowd_input_stats(input_stats)
    sentiment_score = input_stats.get("social media sentiment score")
    crowd_consensus = input_stats.get("crowd consensus percentage")
    public_pct = input_stats.get("public betting percentage")
    money_pct = input_stats.get("money percentage")
    sharp_money_pct = input_stats.get("sharp money percentage")
    news_velocity = input_stats.get("news velocity score")
    model_probability = input_stats.get("sport_model_probability") or input_stats.get("true_probability")
    edge = input_stats.get("edge")
    flags: list[str] = []

    if sentiment_score is None:
        flags.append("sentiment data unavailable")
    if crowd_consensus is None:
        flags.append("crowdsourced signal unavailable")
    source_quality = input_stats.get("sentiment source quality")
    source_quality_score = _social_crowd_score(source_quality, 0) if source_quality is not None else None
    if source_quality_score is not None and source_quality_score <= 30:
        flags.append("sentiment source quality too low")
    if not input_stats.get("social_signal_backtested"):
        flags.append("social signal not backtested")
    if not input_stats.get("crowd_signal_calibrated"):
        flags.append("crowd signal not calibrated")
    rumor_risk = input_stats.get("rumor risk")
    if _is_truthy_signal(rumor_risk) or _is_truthy_signal(input_stats.get("injury rumor flag")) or _is_truthy_signal(input_stats.get("lineup rumor flag")):
        if not _is_confirmed(input_stats.get("rumor_verified")):
            flags.append("rumor not confirmed")
    news_velocity_value = _social_crowd_score(news_velocity, 0) if news_velocity is not None else None
    if news_velocity_value is not None and news_velocity_value >= 80 and not _is_confirmed(input_stats.get("verified_news_source")):
        flags.append("news velocity spike without verified source")
    sharp_or_money_pct = sharp_money_pct if sharp_money_pct is not None else money_pct
    public_pct_value = _social_crowd_score(public_pct, 0) if public_pct is not None else None
    sharp_or_money_pct_value = _social_crowd_score(sharp_or_money_pct, 0) if sharp_or_money_pct is not None else None
    if public_pct_value is not None and sharp_or_money_pct_value is not None and public_pct_value >= 70 and sharp_or_money_pct_value < public_pct_value:
        flags.append("public bias likely inflated price")
    if crowd_consensus is not None and source_quality is not None:
        crowd_value = _social_crowd_score(crowd_consensus, 0)
        strong_crowd = crowd_value >= 70 if crowd_value > 1 else crowd_value >= 0.7
        if strong_crowd and source_quality_score is not None and source_quality_score <= 30:
            if "sentiment source quality too low" not in flags:
                flags.append("sentiment source quality too low")
    sentiment_score_value = _social_crowd_score(sentiment_score, 0) if sentiment_score is not None else None
    edge_value = _safe_float(edge)
    if sentiment_score_value is not None and edge_value is not None and abs(sentiment_score_value) >= 80 and edge_value < 2:
        flags.append("social sentiment is extreme but model edge is weak")
    if crowd_consensus is not None and model_probability is not None:
        crowd_value = _social_crowd_score(crowd_consensus, 0)
        model_probability_value = _safe_float(model_probability)
        crowd_probability = None
        crowd_probability = crowd_value / 100 if crowd_value > 1 else crowd_value
        if crowd_probability is not None and model_probability_value is not None and abs(crowd_probability - model_probability_value) >= 0.12:
            flags.append("crowd consensus conflicts with model probability")

    manual_review_flags = {
        "sentiment data unavailable",
        "crowdsourced signal unavailable",
        "sentiment source quality too low",
        "rumor not confirmed",
        "news velocity spike without verified source",
        "social signal not backtested",
        "crowd signal not calibrated",
    }
    neutral_social = sentiment_score is not None and sentiment_score_value is not None and 40 <= sentiment_score_value <= 60
    neutral_crowd = crowd_consensus is not None and _social_crowd_score(crowd_consensus, 0) >= 40 and _social_crowd_score(crowd_consensus, 0) <= 60
    verified_news = _is_confirmed(input_stats.get("verified_news_source"))
    trusted_source = source_quality_score is not None and source_quality_score >= 80
    no_rumor = not _is_truthy_signal(rumor_risk) and not _is_truthy_signal(input_stats.get("injury rumor flag")) and not _is_truthy_signal(input_stats.get("lineup rumor flag"))
    neutral_verified_social = neutral_social and neutral_crowd and verified_news and trusted_source and no_rumor

    if neutral_verified_social:
        flags = [flag for flag in flags if flag not in {"social signal not backtested", "crowd signal not calibrated"}]

    if any(flag in flags for flag in [
        "crowd consensus conflicts with model probability",
        "public bias likely inflated price",
        "social sentiment is extreme but model edge is weak",
    ]):
        support_status = "conflicts_with_model"
    elif any(flag in manual_review_flags for flag in flags):
        support_status = "requires_manual_review"
    elif neutral_verified_social:
        support_status = "neutral_calibrated"
    else:
        support_status = "supports_model"

    explanation = {
        "support_status": support_status,
        "summary": (
            "Social and crowd data conflict with model/risk assumptions."
            if support_status == "conflicts_with_model"
            else "Social and crowd data require manual review before any promotion."
            if support_status == "requires_manual_review"
            else "Social and crowd data are neutral, verified, and do not create a manual-review flag."
            if support_status == "neutral_calibrated"
            else "Social and crowd data are available and do not create a calibration red flag."
        ),
        "standalone_bet_reason_allowed": False,
        "detected_inputs": {
            "social_sentiment": sentiment_score,
            "crowd_consensus": crowd_consensus,
            "public_betting_percent": public_pct,
            "public_money_percent": money_pct,
            "sharp_money_percent": sharp_money_pct,
            "news_velocity": news_velocity,
            "rumor_risk": rumor_risk,
            "source_quality": source_quality,
        },
    }

    components = {
        "social_sentiment_engine": _calibration_component("social_sentiment_engine", input_stats, ["social media sentiment score"]),
        "crowdsourced_signal_engine": _calibration_component("crowdsourced_signal_engine", input_stats, ["crowd consensus percentage"]),
        "public_bias_detector": _calibration_component("public_bias_detector", input_stats, ["public betting percentage", "sharp money percentage"]),
        "news_velocity_detector": _calibration_component("news_velocity_detector", input_stats, ["news velocity score"]),
        "rumor_risk_filter": _calibration_component("rumor_risk_filter", input_stats, ["rumor signal"]),
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


def sport_analysis_failed_response(sport: Any = None, detail: str = "Sport analysis failed safely.") -> dict[str, Any]:
    social_layer = build_social_crowd_calibration_layer({})
    risk_controller = build_risk_controller()
    officiating_analysis = {
        "officiating_module_status": "no_adjustment",
        "officiating_edge_detected": False,
        "officiating_adjustment_probability_points": 0.0,
        "adjusted_true_probability": None,
        "affected_markets": [],
        "officiating_confidence": 0,
        "officiating_risk_flags": ["internal error handled"],
        "officiating_summary": "officiating layer skipped after handled error",
        "officiating_no_bet_reason": "sport analysis failed safely",
        "officiating_logbook_fields": {},
    }
    return {
        "ok": False,
        "endpoint": "analyzeSportModel",
        "error": "sport_analysis_failed",
        "detail": str(detail)[:300],
        "sport": sport,
        "model_used": None,
        "model_family": None,
        "market": None,
        "projected_score": None,
        "true_probability": None,
        "implied_probability": None,
        "edge": None,
        "confidence": None,
        "risk_level": "conservative",
        "recommended_unit_size": 0,
        "confirmed_bets": [],
        "target_lines": [],
        "no_bets": [],
        "no_bet_flags": ["internal_error_handled"],
        "supported_sport_keys": list(OFFICIAL_SPORT_KEYS),
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
        "officiating_analysis": officiating_analysis,
        **{key: officiating_analysis[key] for key in [
            "officiating_module_status",
            "officiating_edge_detected",
            "officiating_adjustment_probability_points",
            "adjusted_true_probability",
            "affected_markets",
            "officiating_confidence",
            "officiating_risk_flags",
            "officiating_summary",
            "officiating_no_bet_reason",
            "officiating_logbook_fields",
        ]},
        "manual_ticket_preview": None,
        "full_board_preview": {
            "confirmed_bets": [],
            "target_lines": [],
            "target_props": [],
            "target_alt_lines": [],
            "no_bets": [],
            "best_correlated_parlay": None,
            "value_ranking": [],
            "risk_ranking": [],
            "missing_inputs": [],
            "manual_review_required": [],
            "logbook_ready_rows": [],
        },
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


def _evaluated_ticket_status(
    *,
    component_status: str,
    missing_inputs: list[str],
    confirmed_bets: list[dict[str, Any]],
    no_bet_flags: list[str],
    edge: Optional[float],
    confidence: Any,
    confidence_threshold: float = 70,
) -> str:
    if missing_inputs or component_status != COMPONENT_STATUS_ACTIVE:
        return "manual_review_required"
    if confirmed_bets:
        return "confirmed_bet"
    if edge is not None and edge <= 0:
        return "evaluated_no_bet"
    if "edge too small" in no_bet_flags:
        return "evaluated_no_bet_edge_too_small"
    if "low confidence" in no_bet_flags:
        return "evaluated_no_bet_low_confidence"
    confidence_value = _safe_float(confidence)
    if confidence_value is not None and confidence_value < confidence_threshold:
        return "evaluated_no_bet_low_confidence"
    if "risk too high" in no_bet_flags:
        return "evaluated_no_bet_risk_too_high"
    return "evaluated_no_bet"


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


def _safe_probability(value: Any) -> Optional[float]:
    number = _safe_float(value)
    if number is None:
        return None
    if number > 1:
        number = number / 100
    return max(0.01, min(0.99, number))


def _truthy_available(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "available", "active", "cleared", "confirmed", "full"}


def _nba_full_inputs_missing(input_stats: dict[str, Any]) -> list[str]:
    return [field for field in NBA_REQUIRED_CORE_INPUTS if input_stats.get(field) is None]


def _normal_market_key(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "h2h": "moneyline",
        "ml": "moneyline",
        "spreads": "spread",
        "totals": "total",
        "over_under": "total",
        "team_totals": "team_total",
        "props": "player_prop",
        "prop": "player_prop",
        "alternate_line": "alt_line",
        "alternate_spread": "alt_line",
        "alternate_total": "alternate_total",
        "puck_line": "puckline",
        "puck_line_spread": "puckline",
        "alternate_puck_line": "alternate_puckline",
        "alt_puckline": "alternate_puckline",
        "alt_total": "alternate_total",
        "regulation_ml": "regulation_moneyline",
        "regulation_money_line": "regulation_moneyline",
        "first_period": "first_period_moneyline",
        "1st_period": "first_period_moneyline",
        "first_period_ml": "first_period_moneyline",
        "first_period_team_totals": "first_period_team_total",
        "second_period": "second_period_moneyline",
        "second_period_ml": "second_period_moneyline",
        "third_period": "third_period_moneyline",
        "third_period_ml": "third_period_moneyline",
        "match_winner": "match_winner",
        "game_spread": "game_handicap",
        "games_spread": "game_handicap",
        "set_spread": "set_handicap",
        "set_betting": "correct_score",
        "first_set_winner": "first_set_moneyline",
        "first_set_total": "first_set_total_games",
        "total_games_played": "total_games",
        "run_line": "runline",
        "run_line_spread": "runline",
        "first_5": "first_5_moneyline",
        "f5": "first_5_moneyline",
        "first_5_run_line": "first_5_runline",
        "f5_runline": "first_5_runline",
        "first_5_total": "first_5_total",
        "f5_total": "first_5_total",
        "1x2": "three_way_moneyline",
        "home_draw_away": "home_draw_away",
        "draw_no_action": "draw_no_bet",
        "dnb": "draw_no_bet",
        "asian_spread": "asian_handicap",
        "handicap": "asian_handicap",
        "btts": "both_teams_to_score",
        "both_teams_score": "both_teams_to_score",
        "anytime_scorer": "anytime_goal_scorer",
        "first_scorer": "first_goal_scorer",
        "first_half_spread": "first_half_spread",
        "first_half_total": "first_half_total",
        "first_quarter_moneyline": "first_quarter_moneyline",
        "first_quarter_spread": "first_quarter_spread",
        "first_quarter_total": "first_quarter_total",
        "in_play": "live",
    }
    return aliases.get(text, text or "moneyline")


def _nba_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = NBA_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "total_line", "team_total_line"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _basketball_module_required_inputs(sport: str) -> list[str]:
    if sport == "basketball_wnba":
        return WNBA_REQUIRED_CORE_INPUTS
    return COLLEGE_BASKETBALL_REQUIRED_CORE_INPUTS


def _basketball_module_full_inputs_missing(sport: str, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in _basketball_module_required_inputs(sport):
        value = input_stats.get(field)
        if value is None and field in {"event", "league"}:
            value = payload.get(field) or payload.get("event_id")
        if value is None:
            missing.append(field)
    return missing


def _basketball_module_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = BASKETBALL_MODULE_REQUIRED_MARKET_INPUTS.get(market_key, ["odds_american"])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "total_line", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _nfl_full_inputs_missing(input_stats: dict[str, Any]) -> list[str]:
    return [field for field in NFL_REQUIRED_CORE_INPUTS if input_stats.get(field) is None]


def _nfl_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = NFL_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field == "player_minutes_or_snap_projection":
            value = input_stats.get("player_snap_projection")
        if value is None and field in {"line", "total_line", "team_total_line", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _college_football_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field in {"event", "league"}:
            value = payload.get(field) or payload.get("event_id")
        if value is None:
            missing.append(field)
    for field in COLLEGE_FOOTBALL_NUMERIC_CORE_INPUTS:
        value = input_stats.get(field)
        if value is not None and _safe_float(value) is None:
            missing.append(f"{field}_invalid")
    return missing


def _college_football_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = COLLEGE_FOOTBALL_REQUIRED_MARKET_INPUTS.get(market_key, ["odds_american"])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "total_line", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
        elif field in {"line", "total_line", "odds_american"} and _safe_float(value) is None:
            missing.append(f"{field}_invalid")
    return missing


def _mlb_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in MLB_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field == "market":
            value = payload.get("market")
        if value is None:
            missing.append(field)
    return missing


def _mlb_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = MLB_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "total_line", "team_total_line", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _soccer_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in SOCCER_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field in {"market", "league"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _soccer_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = SOCCER_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {
            "line",
            "total_line",
            "team_total_line",
            "corner_line",
            "team_corner_line",
            "card_line",
            "team_card_line",
            "correct_score_selection",
            "odds_american",
        }:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _nhl_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in NHL_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field in {"market", "league"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _nhl_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = NHL_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {
            "line",
            "total_line",
            "team_total_line",
            "odds_american",
        }:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _tennis_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in TENNIS_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field == "market":
            value = payload.get("market")
        if value is None and field == "league":
            value = payload.get("league")
        if value is None:
            missing.append(field)
    return missing


def _tennis_fatigue_rating_to_index(value: Any) -> Optional[float]:
    rating = _safe_float(value)
    if rating is None:
        return None
    if rating > 10:
        return max(0.0, min(1.0, rating / 100))
    if rating > 1:
        return max(0.0, min(1.0, rating / 10))
    return max(0.0, min(1.0, rating))


def _tennis_recent_win_percent_to_record(value: Any) -> tuple[Optional[int], Optional[int]]:
    percent = _safe_float(value)
    if percent is None:
        return None, None
    win_rate = percent / 100 if percent > 1 else percent
    win_rate = max(0.0, min(1.0, win_rate))
    wins = int(round(win_rate * 10))
    return wins, max(0, 10 - wins)


def _normalize_tennis_input_aliases(input_stats: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(input_stats)
    alias_pairs = {
        "player_ranking": ("player_rank", _safe_float),
        "opponent_ranking": ("opponent_rank", _safe_float),
        "player_fatigue_index": ("player_fatigue_rating", _tennis_fatigue_rating_to_index),
        "opponent_fatigue_index": ("opponent_fatigue_rating", _tennis_fatigue_rating_to_index),
        "player_rest_days": ("player_days_rest", _safe_float),
        "opponent_rest_days": ("opponent_days_rest", _safe_float),
        "player_hold_percent": ("player_serve_hold_percent", _safe_float),
        "opponent_hold_percent": ("opponent_serve_hold_percent", _safe_float),
        "player_first_serve_in_percent": ("player_first_serve_percent", _safe_float),
        "opponent_first_serve_in_percent": ("opponent_first_serve_percent", _safe_float),
    }
    for canonical, (alias, normalizer) in alias_pairs.items():
        if normalized.get(canonical) is None and normalized.get(alias) is not None:
            normalized[canonical] = normalizer(normalized.get(alias))
    recent_aliases = (
        ("player_recent_win_percent", "player_recent_form_wins", "player_recent_form_losses"),
        ("opponent_recent_win_percent", "opponent_recent_form_wins", "opponent_recent_form_losses"),
    )
    for alias, wins_key, losses_key in recent_aliases:
        if normalized.get(alias) is None:
            continue
        wins, losses = _tennis_recent_win_percent_to_record(normalized.get(alias))
        if normalized.get(wins_key) is None:
            normalized[wins_key] = wins
        if normalized.get(losses_key) is None:
            normalized[losses_key] = losses
    player_hold = _safe_float(normalized.get("player_hold_percent"))
    opponent_hold = _safe_float(normalized.get("opponent_hold_percent"))
    if normalized.get("player_break_percent") is None and opponent_hold is not None:
        normalized["player_break_percent"] = round(max(0, min(100, 100 - opponent_hold)), 2)
    if normalized.get("opponent_break_percent") is None and player_hold is not None:
        normalized["opponent_break_percent"] = round(max(0, min(100, 100 - player_hold)), 2)
    normalized.setdefault("player_injury_status", "healthy")
    normalized.setdefault("opponent_injury_status", "healthy")
    for prefix in ("player", "opponent"):
        hold = _safe_float(normalized.get(f"{prefix}_hold_percent"))
        break_percent = _safe_float(normalized.get(f"{prefix}_break_percent"))
        first_in = _safe_float(normalized.get(f"{prefix}_first_serve_in_percent"))
        if normalized.get(f"{prefix}_first_serve_points_won_percent") is None and hold is not None:
            normalized[f"{prefix}_first_serve_points_won_percent"] = round(max(58, min(82, hold * 0.72 + 10)), 2)
        if normalized.get(f"{prefix}_second_serve_points_won_percent") is None:
            first_won = _safe_float(normalized.get(f"{prefix}_first_serve_points_won_percent"))
            if first_won is not None:
                normalized[f"{prefix}_second_serve_points_won_percent"] = round(max(38, min(62, first_won - 16)), 2)
        if normalized.get(f"{prefix}_return_points_won_percent") is None and break_percent is not None:
            normalized[f"{prefix}_return_points_won_percent"] = round(max(28, min(48, break_percent * 0.55 + 25)), 2)
        if normalized.get(f"{prefix}_ace_rate") is None and (hold is not None or first_in is not None):
            serve_strength = ((hold or 78) - 72) * 0.12 + ((first_in or 63) - 60) * 0.05
            normalized[f"{prefix}_ace_rate"] = round(max(2.0, min(12.0, 5.0 + serve_strength)), 2)
        if normalized.get(f"{prefix}_double_fault_rate") is None and first_in is not None:
            normalized[f"{prefix}_double_fault_rate"] = round(max(1.5, min(6.0, 4.0 - ((first_in or 63) - 60) * 0.06)), 2)
    if normalized.get("tournament") is None:
        normalized["tournament"] = normalized.get("tournament_name") or normalized.get("event")
    has_tennis_quality = any(
        normalized.get(field) is not None
        for field in (
            "player_elo",
            "opponent_elo",
            "player_ranking",
            "opponent_ranking",
            "player_hold_percent",
            "opponent_hold_percent",
            "player_recent_form_wins",
            "opponent_recent_form_wins",
        )
    )
    if has_tennis_quality and normalized.get("selection") is None and normalized.get("player") is not None:
        normalized["selection"] = normalized.get("player")
    return normalized


def _combat_recent_win_percent_to_record(value: Any) -> tuple[Optional[int], Optional[int]]:
    percent = _safe_float(value)
    if percent is None:
        return None, None
    win_rate = percent / 100 if percent > 1 else percent
    win_rate = max(0.0, min(1.0, win_rate))
    wins = int(round(win_rate * 10))
    return wins, max(0, 10 - wins)


def _normalize_combat_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = dict(input_stats or {})
    payload = payload or {}
    sport_key = normalize_sport_key(str(sport or payload.get("sport") or payload.get("league") or ""))

    def first_present(*keys: str) -> Any:
        for key in keys:
            value = normalized.get(key)
            if value is not None:
                return value
        return None

    def copy_first(target: str, *sources: str, transform: Any = None) -> None:
        if normalized.get(target) is not None:
            return
        for source in sources:
            value = normalized.get(source)
            if value is not None:
                normalized[target] = transform(value) if transform else value
                return

    two_way_aliases = {
        "fighter_strikes_landed_per_min": ["fighter_sig_strikes_landed_per_min", "fighter_sig_strikes_landed_pm", "fighter_slpm"],
        "opponent_strikes_landed_per_min": ["opponent_sig_strikes_landed_per_min", "opponent_sig_strikes_landed_pm", "opponent_slpm"],
        "fighter_strikes_absorbed_per_min": ["fighter_sig_strikes_absorbed_per_min", "fighter_sig_strikes_absorbed_pm", "fighter_sapm"],
        "opponent_strikes_absorbed_per_min": ["opponent_sig_strikes_absorbed_per_min", "opponent_sig_strikes_absorbed_pm", "opponent_sapm"],
        "fighter_striking_accuracy": ["fighter_sig_strike_accuracy", "fighter_sig_striking_accuracy"],
        "opponent_striking_accuracy": ["opponent_sig_strike_accuracy", "opponent_sig_striking_accuracy"],
        "fighter_striking_defense": ["fighter_sig_strike_defense", "fighter_sig_striking_defense"],
        "opponent_striking_defense": ["opponent_sig_strike_defense", "opponent_sig_striking_defense"],
        "fighter_takedown_average": ["fighter_takedowns_per_15", "fighter_td_avg"],
        "opponent_takedown_average": ["opponent_takedowns_per_15", "opponent_td_avg"],
        "fighter_submission_average": ["fighter_submission_attempts_per_15", "fighter_sub_attempts_per_15"],
        "opponent_submission_average": ["opponent_submission_attempts_per_15", "opponent_sub_attempts_per_15"],
        "fighter_reach": ["fighter_reach_inches"],
        "opponent_reach": ["opponent_reach_inches"],
        "fighter_height": ["fighter_height_inches"],
        "opponent_height": ["opponent_height_inches"],
    }
    for canonical, aliases in two_way_aliases.items():
        copy_first(canonical, *aliases, transform=_safe_float)
        for alias in aliases:
            copy_first(alias, canonical, transform=_safe_float)

    if normalized.get("fighter") is None:
        normalized["fighter"] = first_present("fighter_name", "participant_name", "competitor_name")
    if normalized.get("opponent") is None:
        normalized["opponent"] = first_present("opponent_name", "opposing_fighter", "opponent_fighter")
    if normalized.get("selection") is None:
        normalized["selection"] = payload.get("selection") or normalized.get("fighter")

    for percent_key, wins_key, losses_key in (
        ("fighter_recent_win_percent", "fighter_recent_wins", "fighter_recent_losses"),
        ("opponent_recent_win_percent", "opponent_recent_wins", "opponent_recent_losses"),
    ):
        wins, losses = _combat_recent_win_percent_to_record(normalized.get(percent_key))
        if wins is not None:
            normalized.setdefault(wins_key, wins)
            normalized.setdefault(losses_key, losses)
            normalized.setdefault(wins_key.replace("_recent_", "_recent_form_"), wins)
            normalized.setdefault(losses_key.replace("_recent_", "_recent_form_"), losses)
        elif normalized.get(wins_key) is not None and normalized.get(losses_key) is not None:
            wins_float = _safe_float(normalized.get(wins_key), 0) or 0
            losses_float = _safe_float(normalized.get(losses_key), 0) or 0
            total = wins_float + losses_float
            if total > 0:
                normalized[percent_key] = round((wins_float / total) * 100, 2)

    live_quality_fields = {
        "fighter_sig_strikes_landed_per_min", "fighter_strikes_landed_per_min",
        "opponent_sig_strikes_landed_per_min", "opponent_strikes_landed_per_min",
        "fighter_takedowns_per_15", "fighter_takedown_average",
        "opponent_takedowns_per_15", "opponent_takedown_average",
        "fighter_submission_attempts_per_15", "fighter_submission_average",
        "opponent_submission_attempts_per_15", "opponent_submission_average",
        "fighter_recent_win_percent", "opponent_recent_win_percent",
        "fighter_elo", "opponent_elo",
    }
    has_live_quality = any(normalized.get(field) is not None for field in live_quality_fields)
    if not has_live_quality:
        return normalized

    if normalized.get("fighter") is None:
        normalized["fighter"] = payload.get("selection") or payload.get("fighter")
    if normalized.get("opponent") is None:
        normalized["opponent"] = payload.get("opponent")
    is_boxing = sport_key == "boxing"
    normalized.setdefault("fighter_injury_status", "healthy")
    normalized.setdefault("opponent_injury_status", "healthy")
    if normalized.get("scheduled_rounds") is None:
        five_round_signal = any(bool(normalized.get(key) or payload.get(key)) for key in (
            "title_fight", "championship_fight", "main_event", "five_round_fight",
        ))
        normalized["scheduled_rounds"] = 5 if five_round_signal else 3
    if normalized.get("promotion") is None and sport_key in {"mma_mixed_martial_arts", ""}:
        normalized["promotion"] = "UFC"

    safe_defaults = {
        "fight_date": payload.get("fight_date") or payload.get("event_date") or "unknown",
        "weight_class": payload.get("weight_class") or "unknown",
        "fighter_moneyline": payload.get("odds_american") if payload.get("odds_american") is not None else 0,
        "fighter_elo": 1500,
        "opponent_elo": 1500,
        "fighter_recent_win_percent": 50,
        "opponent_recent_win_percent": 50,
        "fighter_finish_rate": 45,
        "opponent_finish_rate": 45,
        "fighter_ko_tko_rate": 30 if is_boxing else 25,
        "opponent_ko_tko_rate": 30 if is_boxing else 25,
        "fighter_submission_rate": 0 if is_boxing else 15,
        "opponent_submission_rate": 0 if is_boxing else 15,
        "fighter_decision_rate": 55 if is_boxing else 35,
        "opponent_decision_rate": 55 if is_boxing else 35,
        "fighter_strikes_landed_per_min": 3.0,
        "opponent_strikes_landed_per_min": 3.0,
        "fighter_strikes_absorbed_per_min": 3.0,
        "opponent_strikes_absorbed_per_min": 3.0,
        "fighter_striking_accuracy": 50,
        "opponent_striking_accuracy": 50,
        "fighter_striking_defense": 55,
        "opponent_striking_defense": 55,
        "fighter_takedown_average": 0.0 if is_boxing else 1.0,
        "opponent_takedown_average": 0.0 if is_boxing else 1.0,
        "fighter_takedown_accuracy": 0 if is_boxing else 35,
        "opponent_takedown_accuracy": 0 if is_boxing else 35,
        "fighter_takedown_defense": 0 if is_boxing else 65,
        "opponent_takedown_defense": 0 if is_boxing else 65,
        "fighter_submission_average": 0.0 if is_boxing else 0.4,
        "opponent_submission_average": 0.0 if is_boxing else 0.4,
        "fighter_age": 30,
        "opponent_age": 30,
        "fighter_reach": 72,
        "opponent_reach": 72,
        "fighter_height": 70,
        "opponent_height": 70,
        "fighter_stance": "orthodox",
        "opponent_stance": "orthodox",
        "fighter_days_rest": 90,
        "opponent_days_rest": 90,
    }
    for key, value in safe_defaults.items():
        if normalized.get(key) is None:
            normalized[key] = value
    return normalized


def _tennis_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = TENNIS_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "total_line", "correct_score_selection", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _combat_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in COMBAT_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field == "selection":
            value = payload.get("selection")
        if value is None:
            missing.append(field)
    return missing


def _combat_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = COMBAT_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _normalize_golf_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = dict(input_stats or {})
    payload = payload or {}

    alias_pairs = {
        "player": ["golfer", "player_name", "golfer_name"],
        "event": ["tournament", "tournament_name", "event_name"],
        "course": ["course_name", "venue"],
        "field_size": ["field", "field_total", "players_in_field", "field_count"],
        "player_world_rank": ["player_rank", "world_rank", "rank", "owgr_rank", "player_owgr"],
        "player_sg_total": ["sg_total", "strokes_gained_total"],
        "player_sg_off_tee": ["sg_off_tee", "strokes_gained_off_tee"],
        "player_sg_approach": ["sg_approach", "strokes_gained_approach"],
        "player_sg_around_green": ["sg_around_green", "strokes_gained_around_green"],
        "player_sg_putting": ["sg_putting", "strokes_gained_putting"],
        "player_recent_form_rank": ["recent_form_rank", "form_rank"],
        "player_recent_scoring_average": ["recent_scoring_average", "scoring_average"],
        "course_fit_score": ["fit_score", "course_fit"],
        "course_history_score": ["history_score", "course_history"],
        "field_strength": ["field_strength_rating", "field_rating"],
        "cut_line_projection": ["projected_cut_line", "cut_projection", "cut_probability", "projected_cut_probability", "make_cut_probability"],
        "weather_wind_rating": ["wind_rating", "weather_rating"],
        "course_difficulty_rating": ["difficulty_rating", "course_difficulty"],
        "opponent": ["opponent_name", "matchup_opponent"],
        "opponent_world_rank": ["opponent_rank", "opponent_owgr_rank", "opponent_owgr"],
        "opponent_sg_total": ["opponent_strokes_gained_total"],
        "opponent_recent_form_rank": ["opponent_form_rank"],
        "opponent_recent_scoring_average": ["opponent_scoring_average"],
        "opponent_course_fit_score": ["opponent_course_fit"],
        "opponent_course_history_score": ["opponent_history_score", "opponent_course_history"],
        "top_n": ["placement_n", "finish_n"],
    }
    for canonical, aliases in alias_pairs.items():
        if normalized.get(canonical) is not None:
            continue
        for alias in aliases:
            if normalized.get(alias) is not None:
                normalized[canonical] = normalized.get(alias)
                break

    if normalized.get("cut_line_projection") is not None:
        cut = _safe_float(normalized.get("cut_line_projection"))
        if cut is not None and cut <= 1:
            normalized["cut_line_projection"] = round(cut * 100, 2)
    golf_quality_fields = {
        "player_world_rank", "player_sg_total", "player_sg_off_tee", "player_sg_approach",
        "player_sg_around_green", "player_sg_putting", "player_recent_form_rank",
        "player_recent_scoring_average", "course_fit_score", "course_history_score",
        "field_strength", "cut_line_projection", "course_difficulty_rating",
    }
    has_golf_quality = any(normalized.get(field) is not None for field in golf_quality_fields)
    has_player_strength = normalized.get("player_world_rank") is not None and normalized.get("player_sg_total") is not None
    if has_player_strength and normalized.get("player_sg_total") is not None:
        sg_total = _safe_float(normalized.get("player_sg_total"))
        if sg_total is not None:
            normalized.setdefault("player_sg_off_tee", round(sg_total * 0.28, 3))
            normalized.setdefault("player_sg_approach", round(sg_total * 0.42, 3))
            normalized.setdefault("player_sg_around_green", round(sg_total * 0.14, 3))
            normalized.setdefault("player_sg_putting", round(sg_total * 0.16, 3))
    if has_golf_quality and normalized.get("field_size") is None:
        league_text = str(payload.get("league") or normalized.get("league") or "").lower()
        event_text = str(payload.get("event") or normalized.get("event") or "").lower()
        if any(token in f"{league_text} {event_text}" for token in ("pga", "major", "masters", "u.s. open", "us open", "open championship", "pga championship")):
            normalized["field_size"] = 89
    if has_golf_quality and normalized.get("course_fit_score") is None and normalized.get("course_history_score") is not None:
        normalized["course_fit_score"] = normalized.get("course_history_score")
    if has_golf_quality and normalized.get("course_history_score") is None and normalized.get("course_fit_score") is not None:
        normalized["course_history_score"] = normalized.get("course_fit_score")
    if has_player_strength and normalized.get("cut_line_projection") is None:
        normalized["cut_line_projection"] = 2
    if has_golf_quality:
        if normalized.get("player") is None:
            normalized["player"] = payload.get("selection") or payload.get("player_name")
        normalized.setdefault("event", payload.get("event") or payload.get("event_id"))
    normalized.setdefault("selection", payload.get("selection") or normalized.get("player"))
    normalized.setdefault("market", payload.get("market"))
    return normalized


def _golf_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    missing = []
    for field in GOLF_REQUIRED_CORE_INPUTS:
        value = input_stats.get(field)
        if value is None and field in {"selection", "market", "odds_american", "bankroll", "unit_size", "risk_profile"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _golf_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = GOLF_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, [])
    missing = []
    for field in required:
        value = input_stats.get(field)
        if value is None and field in {"line", "odds_american"}:
            value = payload.get(field)
        if value is None:
            missing.append(field)
    return missing


def _cricket_value_missing(field: str, input_stats: dict[str, Any], payload: dict[str, Any]) -> bool:
    value = input_stats.get(field)
    if value is None and field in {"sport", "league", "event", "teams", "market", "selection", "odds_american", "bankroll", "unit_size", "risk_profile"}:
        value = payload.get(field)
    if value is None and field == "event":
        value = payload.get("event_id")
    if value in (None, ""):
        return True
    if field in CRICKET_NUMERIC_CORE_INPUTS or field in CRICKET_NUMERIC_PLAYER_PROP_INPUTS or field in {"line", "odds_american", "total_runs_line", "team_total_runs_line"}:
        return _safe_float(value) is None
    return False


def _cricket_full_inputs_missing(input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    base_fields = ["sport", "league", "event", "market", "selection", "odds_american", "bankroll", "unit_size", "risk_profile"]
    missing = [field for field in base_fields if _cricket_value_missing(field, input_stats, payload)]
    for field in CRICKET_REQUIRED_CORE_INPUTS:
        if _cricket_value_missing(field, input_stats, payload):
            missing.append(field)
    return list(dict.fromkeys(missing))


def _cricket_market_specific_missing(market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    market_key = _normal_market_key(input_stats.get("market_type") or market)
    required = list(CRICKET_REQUIRED_MARKET_INPUTS.get(market_key, []))
    if market_key in CRICKET_PROP_MARKETS:
        required = list(dict.fromkeys(required + CRICKET_PLAYER_PROP_INPUTS))
    missing = []
    for field in required:
        if _cricket_value_missing(field, input_stats, payload):
            missing.append(field)
    return missing


def _missing_inputs_for_sport(sport: str, market: Any, input_stats: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    if sport == "basketball_nba":
        return _nba_full_inputs_missing(input_stats) + _nba_market_specific_missing(market, input_stats, payload)
    if sport in {"basketball_wnba", "basketball_ncaab", "basketball_ncaawb"}:
        return _basketball_module_full_inputs_missing(sport, input_stats, payload) + _basketball_module_market_specific_missing(market, input_stats, payload)
    if sport == "americanfootball_ncaaf":
        return _college_football_full_inputs_missing(input_stats, payload) + _college_football_market_specific_missing(market, input_stats, payload)
    if sport == "americanfootball_nfl":
        return _nfl_full_inputs_missing(input_stats) + _nfl_market_specific_missing(market, input_stats, payload)
    if sport == "baseball_mlb":
        return _mlb_full_inputs_missing(input_stats, payload) + _mlb_market_specific_missing(market, input_stats, payload)
    if sport == "soccer":
        return _soccer_full_inputs_missing(input_stats, payload) + _soccer_market_specific_missing(market, input_stats, payload)
    if sport == "icehockey_nhl":
        return _nhl_full_inputs_missing(input_stats, payload) + _nhl_market_specific_missing(market, input_stats, payload)
    if sport == "tennis":
        return _tennis_full_inputs_missing(input_stats, payload) + _tennis_market_specific_missing(market, input_stats, payload)
    if sport in {"mma_mixed_martial_arts", "boxing"}:
        return _combat_full_inputs_missing(input_stats, payload) + _combat_market_specific_missing(market, input_stats, payload)
    if sport == "golf":
        return _golf_full_inputs_missing(input_stats, payload) + _golf_market_specific_missing(market, input_stats, payload)
    if sport == "cricket":
        return _cricket_full_inputs_missing(input_stats, payload) + _cricket_market_specific_missing(market, input_stats, payload)
    config = get_sport_model_config(sport)
    if not config:
        return []
    status, missing = _component_status(config["required_inputs"], input_stats)
    return missing if status == COMPONENT_STATUS_INACTIVE else []


def _copy_alias_if_missing(data: dict[str, Any], canonical: str, aliases: list[str]) -> None:
    if data.get(canonical) is not None:
        return
    for alias in aliases:
        if data.get(alias) is not None:
            data[canonical] = data.get(alias)
            return


def _normalize_generic_betting_aliases(
    input_stats: dict[str, Any],
    *,
    market: Any = None,
    selection: Any = None,
    ticket: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    normalized = dict(input_stats or {})
    ticket = ticket or {}
    generic_aliases = {
        "player": ["player_name", "athlete"],
        "team": ["team_name"],
        "selection": ["selection_name"],
        "opponent": ["opponent_name"],
        "event": ["game", "matchup", "tournament", "tournament_name"],
        "league": ["league_name"],
        "line": ["line_value"],
        "total_line": ["total_line"],
        "market": ["market_name"],
        "sportsbook": ["book_name", "book"],
    }
    for canonical, aliases in generic_aliases.items():
        _copy_alias_if_missing(normalized, canonical, aliases)
    if normalized.get("odds_american") is None:
        for alias in ("current_odds", "best_available_odds"):
            if normalized.get(alias) is not None:
                normalized["odds_american"] = normalized.get(alias)
                break
    market_key = _normal_market_key(market or normalized.get("market") or ticket.get("market"))
    if normalized.get("line") is None and normalized.get("prop_line") is not None and ("prop" in market_key or market_key in {"aces", "double_faults", "birdies_prop", "putts_prop"}):
        normalized["line"] = normalized.get("prop_line")
    if normalized.get("market") is None and (market or ticket.get("market")) is not None:
        normalized["market"] = market or ticket.get("market")
    if normalized.get("league") is None and ticket.get("league") is not None:
        normalized["league"] = ticket.get("league")
    return normalized


def _normalize_team_sport_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = dict(input_stats or {})
    payload = payload or {}
    if normalized.get("selection") is None and normalized.get("team") is not None:
        normalized["selection"] = normalized.get("team")
    if normalized.get("market") is None:
        normalized["market"] = payload.get("market")
    if normalized.get("league") is None:
        normalized["league"] = payload.get("league")
    return normalized


def _normalize_basketball_module_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = _normalize_team_sport_input_aliases(input_stats, payload, sport)
    alias_pairs = {
        "event": ["game", "matchup"],
        "selection": ["favorite", "pick"],
        "line": ["line_value", "spread_line"],
        "team": ["team_name"],
        "opponent": ["opponent_name"],
        "home_team": ["home"],
        "away_team": ["away"],
        "home_offensive_rating": ["home_off_rating"],
        "away_offensive_rating": ["away_off_rating"],
        "home_defensive_rating": ["home_def_rating"],
        "away_defensive_rating": ["away_def_rating"],
        "home_effective_fg_pct": ["home_efg"],
        "away_effective_fg_pct": ["away_efg"],
        "home_turnover_rate": ["home_tov"],
        "away_turnover_rate": ["away_tov"],
        "home_rebound_rate": ["home_oreb"],
        "away_rebound_rate": ["away_oreb"],
        "home_free_throw_rate": ["home_ft_rate"],
        "away_free_throw_rate": ["away_ft_rate"],
        "player_minutes_projection": ["player_minutes"],
        "player_usage_rate": ["usage"],
        "player_points_projection": ["points_proj"],
        "player_rebounds_projection": ["rebounds_proj"],
        "player_assists_projection": ["assists_proj"],
        "player_pra_projection": ["pra_proj"],
        "player_threes_projection": ["threes_proj"],
        "home_rank": ["home_ap_rank"],
        "away_rank": ["away_ap_rank"],
        "home_strength_rating": ["home_net_rating", "home_kenpom_rating"],
        "away_strength_rating": ["away_net_rating", "away_kenpom_rating"],
        "home_conference_strength": ["home_conference_rating"],
        "away_conference_strength": ["away_conference_rating"],
        "home_experience_rating": ["home_experience"],
        "away_experience_rating": ["away_experience"],
        "home_three_point_rate": ["home_3p_rate"],
        "away_three_point_rate": ["away_3p_rate"],
        "home_free_throw_pct": ["home_ft_pct"],
        "away_free_throw_pct": ["away_ft_pct"],
    }
    for canonical, aliases in alias_pairs.items():
        _copy_alias_if_missing(normalized, canonical, aliases)
    teams = payload.get("teams") if isinstance(payload, dict) else None
    if normalized.get("home_team") is None and isinstance(teams, list) and teams:
        normalized["home_team"] = teams[-1]
    if normalized.get("away_team") is None and isinstance(teams, list) and teams:
        normalized["away_team"] = teams[0]
    if normalized.get("team") is None and normalized.get("selection") is not None:
        normalized["team"] = normalized.get("selection")
    if normalized.get("opponent") is None:
        if normalized.get("team") == normalized.get("home_team"):
            normalized["opponent"] = normalized.get("away_team")
        elif normalized.get("team") == normalized.get("away_team"):
            normalized["opponent"] = normalized.get("home_team")
    if normalized.get("selection") is None and normalized.get("team") is not None:
        normalized["selection"] = normalized.get("team")
    if normalized.get("player_team") is None and normalized.get("team") is not None:
        normalized["player_team"] = normalized.get("team")
    if normalized.get("player_pra_projection") is None:
        pts = _safe_float(normalized.get("player_points_projection"))
        reb = _safe_float(normalized.get("player_rebounds_projection"))
        ast = _safe_float(normalized.get("player_assists_projection"))
        if pts is not None and reb is not None and ast is not None:
            normalized["player_pra_projection"] = round(pts + reb + ast, 2)
    if sport == "basketball_wnba":
        normalized.setdefault("home_injury_adjustment", 0)
        normalized.setdefault("away_injury_adjustment", 0)
    return normalized


def _normalize_mlb_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    return _normalize_team_sport_input_aliases(input_stats, payload, sport)


def _normalize_nba_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    return _normalize_team_sport_input_aliases(input_stats, payload, sport)


def _normalize_wnba_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    return _normalize_basketball_module_input_aliases(input_stats, payload, sport)


def _normalize_mens_college_basketball_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    return _normalize_basketball_module_input_aliases(input_stats, payload, sport)


def _normalize_womens_college_basketball_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    return _normalize_basketball_module_input_aliases(input_stats, payload, sport)


def _normalize_nfl_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    return _normalize_team_sport_input_aliases(input_stats, payload, sport)


def _normalize_college_football_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = _normalize_team_sport_input_aliases(input_stats, payload, sport)
    alias_pairs = {
        "event": ["game", "matchup"],
        "selection": ["favorite", "pick"],
        "line": ["line_value", "spread_line"],
        "total_line": ["total_line"],
        "team": ["team_name"],
        "opponent": ["opponent_name"],
        "home_team": ["home"],
        "away_team": ["away"],
        "home_offensive_epa_per_play": ["home_epa_off"],
        "away_offensive_epa_per_play": ["away_epa_off"],
        "home_defensive_epa_per_play": ["home_epa_def"],
        "away_defensive_epa_per_play": ["away_epa_def"],
        "home_success_rate": ["home_sr"],
        "away_success_rate": ["away_sr"],
        "home_defensive_success_rate_allowed": ["home_def_sr_allowed"],
        "away_defensive_success_rate_allowed": ["away_def_sr_allowed"],
        "home_explosiveness": ["home_explosive_rate"],
        "away_explosiveness": ["away_explosive_rate"],
        "home_explosiveness_allowed": ["home_explosive_allowed"],
        "away_explosiveness_allowed": ["away_explosive_allowed"],
        "home_pace_seconds_per_play": ["home_pace"],
        "away_pace_seconds_per_play": ["away_pace"],
        "home_points_per_drive": ["home_ppd"],
        "away_points_per_drive": ["away_ppd"],
        "home_points_allowed_per_drive": ["home_ppd_allowed"],
        "away_points_allowed_per_drive": ["away_ppd_allowed"],
        "home_red_zone_td_rate": ["home_rz_td"],
        "away_red_zone_td_rate": ["away_rz_td"],
        "home_red_zone_td_rate_allowed": ["home_rz_td_allowed"],
        "away_red_zone_td_rate_allowed": ["away_rz_td_allowed"],
        "home_qb_rating": ["home_qb"],
        "away_qb_rating": ["away_qb"],
        "home_qb_injury_adjustment": ["home_qb_injury"],
        "away_qb_injury_adjustment": ["away_qb_injury"],
        "home_offensive_line_rating": ["home_ol"],
        "away_offensive_line_rating": ["away_ol"],
        "home_defensive_line_rating": ["home_dl"],
        "away_defensive_line_rating": ["away_dl"],
        "home_special_teams_rating": ["home_st"],
        "away_special_teams_rating": ["away_st"],
        "weather_wind_mph": ["wind_mph"],
        "weather_precipitation": ["precipitation"],
        "home_rank": ["home_ap_rank"],
        "away_rank": ["away_ap_rank"],
        "home_power_rating": ["home_sp_rating", "home_fpi_rating"],
        "away_power_rating": ["away_sp_rating", "away_fpi_rating"],
        "home_conference_strength": ["home_conference_rating"],
        "away_conference_strength": ["away_conference_rating"],
        "player": ["player_name"],
        "player_position": ["position"],
        "player_snap_share": ["snap_share"],
        "player_usage_rate": ["usage"],
        "player_pass_attempts_projection": ["pass_attempts_proj"],
        "player_passing_yards_projection": ["passing_yards_proj"],
        "player_passing_tds_projection": ["passing_tds_proj"],
        "player_interceptions_projection": ["interceptions_proj"],
        "player_rush_attempts_projection": ["rush_attempts_proj"],
        "player_rushing_yards_projection": ["rushing_yards_proj"],
        "player_rushing_tds_projection": ["rushing_tds_proj"],
        "player_targets_projection": ["targets_proj"],
        "player_receptions_projection": ["receptions_proj"],
        "player_receiving_yards_projection": ["receiving_yards_proj"],
        "player_anytime_td_probability": ["td_probability"],
    }
    for canonical, aliases in alias_pairs.items():
        _copy_alias_if_missing(normalized, canonical, aliases)
    teams = payload.get("teams") if isinstance(payload, dict) else None
    if normalized.get("home_team") is None and isinstance(teams, list) and teams:
        normalized["home_team"] = teams[-1]
    if normalized.get("away_team") is None and isinstance(teams, list) and teams:
        normalized["away_team"] = teams[0]
    if normalized.get("team") is None and normalized.get("selection") is not None:
        normalized["team"] = normalized.get("selection")
    if normalized.get("opponent") is None:
        if normalized.get("team") == normalized.get("home_team"):
            normalized["opponent"] = normalized.get("away_team")
        elif normalized.get("team") == normalized.get("away_team"):
            normalized["opponent"] = normalized.get("home_team")
    if normalized.get("selection") is None and normalized.get("team") is not None:
        normalized["selection"] = normalized.get("team")
    if normalized.get("player_team") is None and normalized.get("team") is not None:
        normalized["player_team"] = normalized.get("team")
    normalized.setdefault("home_field_advantage", 3.0)
    normalized.setdefault("neutral_site", False)
    normalized.setdefault("weather_wind_mph", 0)
    normalized.setdefault("weather_precipitation", "none")
    normalized.setdefault("home_plays_per_game", 72)
    normalized.setdefault("away_plays_per_game", 70)
    normalized.setdefault("home_turnover_margin", 0)
    normalized.setdefault("away_turnover_margin", 0)
    normalized.setdefault("home_havoc_rate", 17.0)
    normalized.setdefault("away_havoc_rate", 16.0)
    normalized.setdefault("home_havoc_allowed", 15.0)
    normalized.setdefault("away_havoc_allowed", 16.0)
    return normalized


def _normalize_soccer_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = _normalize_team_sport_input_aliases(input_stats, payload, sport)
    alias_pairs = {
        "team": ["home_team", "home", "team_name"],
        "opponent": ["away_team", "away", "opponent_name"],
        "selection": ["favorite", "pick", "selection_name"],
        "home_away": ["team_home_away"],
        "team_expected_goals": ["home_expected_goals_for", "home_xg_for"],
        "opponent_expected_goals": ["away_expected_goals_for", "away_xg_for"],
        "team_xg_for": ["home_recent_xg", "home_xg_for", "home_expected_goals_for"],
        "opponent_xg_for": ["away_recent_xg", "away_xg_for", "away_expected_goals_for"],
        "team_xg_against": ["home_recent_xga", "home_xg_against", "home_xga", "home_expected_goals_against"],
        "opponent_xg_against": ["away_recent_xga", "away_xg_against", "away_xga", "away_expected_goals_against"],
        "team_recent_form_points": ["home_form_rating", "home_form"],
        "opponent_recent_form_points": ["away_form_rating", "away_form"],
        "team_rest_days": ["home_rest_days"],
        "opponent_rest_days": ["away_rest_days"],
        "injury_report_status": ["injury_status"],
        "league_goal_rate": ["league_average_goals", "avg_goals"],
        "low_score_correlation": ["dc_low_score"],
        "draw_adjustment": ["draw_adj"],
    }
    for canonical, aliases in alias_pairs.items():
        _copy_alias_if_missing(normalized, canonical, aliases)
    if normalized.get("home_away") is None and normalized.get("team") is not None and normalized.get("opponent") is not None:
        normalized["home_away"] = "home"
    if normalized.get("selection") is None and normalized.get("team") is not None:
        normalized["selection"] = normalized.get("team")
    if normalized.get("market") is None:
        normalized["market"] = payload.get("market")
    if normalized.get("league") is None:
        normalized["league"] = payload.get("league")
    return normalized


def _normalize_nhl_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = _normalize_team_sport_input_aliases(input_stats, payload, sport)
    alias_pairs = {
        "team": ["team_name", "home_team", "home"],
        "opponent": ["opponent_name", "away_team", "away"],
        "selection": ["selection_name", "favorite", "pick"],
        "game_date": ["date", "match_date"],
        "team_projected_goals": ["home_projected_goals", "team_goals_projection"],
        "opponent_projected_goals": ["away_projected_goals", "opponent_goals_projection"],
        "team_xg_for_per_game": ["team_xg_for", "home_xg_for"],
        "opponent_xg_for_per_game": ["opponent_xg_for", "away_xg_for"],
        "team_xg_against_per_game": ["team_xg_against", "home_xg_against", "home_xga"],
        "opponent_xg_against_per_game": ["opponent_xg_against", "away_xg_against", "away_xga"],
        "team_shots_for_per_game": ["team_shots_for", "home_shots_for"],
        "opponent_shots_for_per_game": ["opponent_shots_for", "away_shots_for"],
        "team_shots_against_per_game": ["team_shots_against", "home_shots_against"],
        "opponent_shots_against_per_game": ["opponent_shots_against", "away_shots_against"],
        "team_power_play_percent": ["team_power_play_pct", "home_power_play_pct"],
        "opponent_power_play_percent": ["opponent_power_play_pct", "away_power_play_pct"],
        "team_penalty_kill_percent": ["team_penalty_kill_pct", "home_penalty_kill_pct"],
        "opponent_penalty_kill_percent": ["opponent_penalty_kill_pct", "away_penalty_kill_pct"],
        "team_starting_goalie_save_percent": ["team_goalie_save_pct", "home_goalie_save_pct"],
        "opponent_starting_goalie_save_percent": ["opponent_goalie_save_pct", "away_goalie_save_pct"],
        "team_starting_goalie_gsaax": ["team_goalie_gsaax", "home_goalie_gsaax"],
        "opponent_starting_goalie_gsaax": ["opponent_goalie_gsaax", "away_goalie_gsaax"],
    }
    for canonical, aliases in alias_pairs.items():
        _copy_alias_if_missing(normalized, canonical, aliases)
    if normalized.get("home_away") is None and normalized.get("team") is not None and normalized.get("opponent") is not None:
        normalized["home_away"] = "home"
    if normalized.get("selection") is None and normalized.get("team") is not None:
        normalized["selection"] = normalized.get("team")
    if normalized.get("market") is None:
        normalized["market"] = payload.get("market")
    if normalized.get("league") is None:
        normalized["league"] = payload.get("league")
    return normalized


def _normalize_cricket_input_aliases(input_stats: dict[str, Any], payload: Optional[dict[str, Any]] = None, sport: Optional[str] = None) -> dict[str, Any]:
    normalized = _normalize_team_sport_input_aliases(input_stats, payload, sport)
    payload = payload or {}
    alias_pairs = {
        "event": ["game", "match", "matchup"],
        "selection": ["pick", "favorite"],
        "line": ["line_value"],
        "total_runs_line": ["total_line"],
        "team_total_runs_line": ["team_total_line"],
        "team": ["team_name"],
        "opponent": ["opponent_name"],
        "home_team": ["home"],
        "away_team": ["away"],
        "batting_team": ["batting"],
        "bowling_team": ["bowling"],
        "venue": ["ground", "stadium"],
        "pitch_type": ["surface"],
        "weather_conditions": ["weather"],
        "toss_winner": ["toss"],
        "toss_decision": ["decision"],
        "team_batting_rating": ["team_bat_rating"],
        "opponent_batting_rating": ["opp_bat_rating"],
        "team_bowling_rating": ["team_bowl_rating"],
        "opponent_bowling_rating": ["opp_bowl_rating"],
        "team_fielding_rating": ["team_field_rating"],
        "opponent_fielding_rating": ["opp_field_rating"],
        "team_recent_form_rating": ["team_form"],
        "opponent_recent_form_rating": ["opp_form"],
        "team_powerplay_run_rate": ["team_pp_rr"],
        "opponent_powerplay_run_rate": ["opp_pp_rr"],
        "team_middle_overs_run_rate": ["team_middle_rr"],
        "opponent_middle_overs_run_rate": ["opp_middle_rr"],
        "team_death_overs_run_rate": ["team_death_rr"],
        "opponent_death_overs_run_rate": ["opp_death_rr"],
        "team_wicket_loss_rate": ["team_wicket_loss"],
        "opponent_wicket_loss_rate": ["opp_wicket_loss"],
        "team_wicket_taking_rate": ["team_wicket_rate"],
        "opponent_wicket_taking_rate": ["opp_wicket_rate"],
        "team_boundary_rate": ["team_boundary_pct"],
        "opponent_boundary_rate": ["opp_boundary_pct"],
        "team_dot_ball_rate": ["team_dot_pct"],
        "opponent_dot_ball_rate": ["opp_dot_pct"],
        "team_chase_rating": ["team_chase"],
        "opponent_chase_rating": ["opp_chase"],
        "team_defend_total_rating": ["team_defend"],
        "opponent_defend_total_rating": ["opp_defend"],
        "venue_average_score": ["venue_avg_score"],
        "venue_chase_win_rate": ["chase_win_pct"],
        "pitch_spin_assist": ["spin_assist"],
        "pitch_pace_assist": ["pace_assist"],
        "dew_factor": ["dew"],
        "wind_factor": ["wind"],
        "player": ["player_name"],
        "player_role": ["role"],
        "batting_position": ["bat_pos"],
        "player_batting_average": ["batting_avg"],
        "player_strike_rate": ["batting_strike_rate"],
        "player_recent_runs_average": ["recent_runs"],
        "player_boundary_rate": ["boundary_rate"],
        "player_six_rate": ["six_rate"],
        "player_fifty_rate": ["fifty_rate"],
        "player_hundred_rate": ["hundred_rate"],
        "player_duck_rate": ["duck_rate"],
        "player_bowling_average": ["bowling_avg"],
        "player_economy_rate": ["economy"],
        "player_strike_rate_bowling": ["bowling_strike_rate"],
        "player_recent_wickets_average": ["recent_wickets"],
        "player_overs_projection": ["overs_proj"],
        "player_balls_faced_projection": ["balls_faced_proj"],
        "player_runs_projection": ["runs_proj"],
        "player_wickets_projection": ["wickets_proj"],
        "player_sixes_projection": ["sixes_proj"],
        "player_fours_projection": ["fours_proj"],
    }
    for canonical, aliases in alias_pairs.items():
        _copy_alias_if_missing(normalized, canonical, aliases)
    teams = payload.get("teams") if isinstance(payload, dict) else None
    if normalized.get("home_team") is None and isinstance(teams, list) and teams:
        normalized["home_team"] = teams[0]
    if normalized.get("away_team") is None and isinstance(teams, list) and len(teams) > 1:
        normalized["away_team"] = teams[1]
    if normalized.get("team") is None and normalized.get("selection") is not None:
        normalized["team"] = normalized.get("selection")
    if normalized.get("opponent") is None:
        if normalized.get("team") == normalized.get("home_team"):
            normalized["opponent"] = normalized.get("away_team")
        elif normalized.get("team") == normalized.get("away_team"):
            normalized["opponent"] = normalized.get("home_team")
    if normalized.get("batting_team") is None and normalized.get("team") is not None:
        normalized["batting_team"] = normalized.get("team")
    if normalized.get("bowling_team") is None and normalized.get("opponent") is not None:
        normalized["bowling_team"] = normalized.get("opponent")
    if normalized.get("player_team") is None and normalized.get("team") is not None:
        normalized["player_team"] = normalized.get("team")
    if normalized.get("selection") is None and normalized.get("team") is not None:
        normalized["selection"] = normalized.get("team")
    if normalized.get("format") is None:
        league_text = str(payload.get("league") or normalized.get("league") or "").strip().lower()
        if "ipl" in league_text:
            normalized["format"] = "ipl"
        elif "t20" in league_text or "bbl" in league_text or "hundred" in league_text or league_text in {"cpl", "psl"}:
            normalized["format"] = "t20"
        elif "odi" in league_text or "one day" in league_text:
            normalized["format"] = "odi"
        elif "test" in league_text:
            normalized["format"] = "test"
    if normalized.get("market") is None:
        normalized["market"] = payload.get("market")
    if normalized.get("league") is None:
        normalized["league"] = payload.get("league")
    if normalized.get("odds_american") is None:
        normalized["odds_american"] = payload.get("odds_american")
    if normalized.get("bankroll") is None:
        normalized["bankroll"] = payload.get("bankroll")
    if normalized.get("unit_size") is None:
        normalized["unit_size"] = payload.get("unit_size")
    if normalized.get("risk_profile") is None:
        normalized["risk_profile"] = payload.get("risk_profile")
    return normalized


def normalize_sport_inputs_for_model(
    sport: Any,
    market: Any,
    selection: Any,
    input_stats: Any,
    ticket: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    raw_input_stats, input_stats_flags = _normalize_input_stats(input_stats)
    payload = dict(ticket or {})
    sport_alias_resolved = normalize_sport_key(str(sport or payload.get("sport") or ""))
    effective_market = market or payload.get("market") or raw_input_stats.get("market") or raw_input_stats.get("market_name")
    before_missing = _missing_inputs_for_sport(sport_alias_resolved, effective_market, raw_input_stats, payload)
    normalized = _normalize_generic_betting_aliases(
        raw_input_stats,
        market=effective_market,
        selection=selection or payload.get("selection"),
        ticket=payload,
    )

    normalizer_used = "generic_betting_alias_normalizer"
    if sport_alias_resolved == "basketball_nba":
        normalized = _normalize_nba_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "nba_input_normalizer"
    elif sport_alias_resolved == "basketball_wnba":
        normalized = _normalize_wnba_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "wnba_input_normalizer"
    elif sport_alias_resolved == "basketball_ncaab":
        normalized = _normalize_mens_college_basketball_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "mens_college_basketball_input_normalizer"
    elif sport_alias_resolved == "basketball_ncaawb":
        normalized = _normalize_womens_college_basketball_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "womens_college_basketball_input_normalizer"
    elif sport_alias_resolved == "americanfootball_nfl":
        normalized = _normalize_nfl_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "nfl_input_normalizer"
    elif sport_alias_resolved == "americanfootball_ncaaf":
        normalized = _normalize_college_football_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "college_football_input_normalizer"
    elif sport_alias_resolved == "baseball_mlb":
        normalized = _normalize_mlb_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "mlb_input_normalizer"
    elif sport_alias_resolved == "soccer":
        normalized = _normalize_soccer_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "soccer_input_normalizer"
    elif sport_alias_resolved == "icehockey_nhl":
        normalized = _normalize_nhl_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "nhl_input_normalizer"
    elif sport_alias_resolved == "tennis":
        normalized = _normalize_tennis_input_aliases(normalized)
        normalizer_used = "tennis_input_normalizer"
    elif sport_alias_resolved in {"mma_mixed_martial_arts", "boxing"}:
        normalized = _normalize_combat_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "combat_input_normalizer"
    elif sport_alias_resolved == "golf":
        normalized = _normalize_golf_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "golf_input_normalizer"
    elif sport_alias_resolved == "cricket":
        normalized = _normalize_cricket_input_aliases(normalized, payload, sport_alias_resolved)
        normalizer_used = "cricket_input_normalizer"

    after_market = market or payload.get("market") or normalized.get("market")
    after_missing = _missing_inputs_for_sport(sport_alias_resolved, after_market, normalized, payload)
    diagnostics = {
        "raw_input_keys": sorted(raw_input_stats.keys()),
        "normalized_input_keys": sorted(normalized.keys()),
        "missing_inputs_before_normalization": list(dict.fromkeys(before_missing)),
        "missing_inputs_after_normalization": list(dict.fromkeys(after_missing)),
        "sport_alias_resolved": sport_alias_resolved,
        "normalizer_used": normalizer_used,
        "input_stats_flags": input_stats_flags,
    }
    return {
        "input_stats": normalized,
        "diagnostics": diagnostics,
        **diagnostics,
    }


def _nfl_thresholds(risk_profile: Any) -> tuple[float, float]:
    profile = str(risk_profile or "moderate").strip().lower()
    if profile == "standard":
        profile = "moderate"
    if profile == "aggressive":
        return 1.5, 60
    if profile == "conservative":
        return 3.0, 75
    return 2.0, 65


def _logistic_probability(value: float, scale: float) -> float:
    return max(0.03, min(0.97, 1 / (1 + 2.718281828 ** (-(value / scale)))))


def american_odds_to_implied_probability(odds: Optional[float]) -> Optional[float]:
    return implied_probability_from_american(odds) if odds is not None else None


def negative_binomial_pmf(k: int, mean: float, dispersion: float = 8.0) -> float:
    if k < 0:
        return 0.0
    mean = max(0.05, float(mean))
    dispersion = max(0.5, float(dispersion or 8.0))
    p = dispersion / (dispersion + mean)
    log_coeff = math.lgamma(k + dispersion) - math.lgamma(dispersion) - math.lgamma(k + 1)
    return math.exp(log_coeff + dispersion * math.log(p) + k * math.log(1 - p))


def negative_binomial_cdf(k: int, mean: float, dispersion: float = 8.0) -> float:
    if k < 0:
        return 0.0
    return min(1.0, sum(negative_binomial_pmf(i, mean, dispersion) for i in range(k + 1)))


def estimate_run_distribution(mean_runs: float, dispersion: float = 8.0, max_runs: int = 20) -> list[float]:
    probabilities = [negative_binomial_pmf(i, mean_runs, dispersion) for i in range(max_runs)]
    probabilities.append(max(0.0, 1.0 - sum(probabilities)))
    total = sum(probabilities) or 1.0
    return [p / total for p in probabilities]


def estimate_moneyline_probability_from_runs(team_dist: list[float], opponent_dist: list[float]) -> float:
    win = 0.0
    tie = 0.0
    for team_runs, team_prob in enumerate(team_dist):
        for opponent_runs, opponent_prob in enumerate(opponent_dist):
            probability = team_prob * opponent_prob
            if team_runs > opponent_runs:
                win += probability
            elif team_runs == opponent_runs:
                tie += probability
    return max(0.03, min(0.97, win + tie * 0.5))


def estimate_runline_cover_probability(team_dist: list[float], opponent_dist: list[float], line: float) -> float:
    cover = 0.0
    for team_runs, team_prob in enumerate(team_dist):
        for opponent_runs, opponent_prob in enumerate(opponent_dist):
            if (team_runs - opponent_runs) + line > 0:
                cover += team_prob * opponent_prob
    return max(0.03, min(0.97, cover))


def estimate_total_probability(team_dist: list[float], opponent_dist: list[float], total_line: float, selection: Any) -> float:
    over_probability = 0.0
    under_probability = 0.0
    push_probability = 0.0
    for team_runs, team_prob in enumerate(team_dist):
        for opponent_runs, opponent_prob in enumerate(opponent_dist):
            total = team_runs + opponent_runs
            probability = team_prob * opponent_prob
            if total > total_line:
                over_probability += probability
            elif total < total_line:
                under_probability += probability
            else:
                push_probability += probability
    probability = under_probability if "under" in str(selection or "").lower() else over_probability
    return max(0.03, min(0.97, probability + push_probability * 0.5))


def estimate_team_total_probability(team_dist: list[float], team_total_line: float, selection: Any) -> float:
    over_probability = 0.0
    under_probability = 0.0
    push_probability = 0.0
    for runs, probability in enumerate(team_dist):
        if runs > team_total_line:
            over_probability += probability
        elif runs < team_total_line:
            under_probability += probability
        else:
            push_probability += probability
    probability = under_probability if "under" in str(selection or "").lower() else over_probability
    return max(0.03, min(0.97, probability + push_probability * 0.5))


def poisson_pmf(k: int, lam: float) -> float:
    if k < 0:
        return 0.0
    lam = max(0.05, min(5.5, float(lam or 0.05)))
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def build_soccer_score_matrix(team_lambda: float, opponent_lambda: float, max_goals: int = 8) -> list[list[float]]:
    team_probs = [poisson_pmf(i, team_lambda) for i in range(max_goals)]
    opponent_probs = [poisson_pmf(i, opponent_lambda) for i in range(max_goals)]
    team_probs.append(max(0.0, 1.0 - sum(team_probs)))
    opponent_probs.append(max(0.0, 1.0 - sum(opponent_probs)))
    matrix = [[team_probs[i] * opponent_probs[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)]
    total = sum(sum(row) for row in matrix) or 1.0
    return [[cell / total for cell in row] for row in matrix]


def _normalize_score_matrix(matrix: list[list[float]]) -> list[list[float]]:
    total = sum(sum(row) for row in matrix) or 1.0
    return [[max(0.0, cell) / total for cell in row] for row in matrix]


def apply_dixon_coles_adjustment(matrix: list[list[float]], team_lambda: float, opponent_lambda: float, rho: float = -0.08) -> list[list[float]]:
    adjusted = [row[:] for row in matrix]
    rho = max(-0.18, min(0.12, float(rho or -0.08)))
    corrections = {
        (0, 0): 1 - (team_lambda * opponent_lambda * rho),
        (1, 0): 1 + (team_lambda * rho),
        (0, 1): 1 + (opponent_lambda * rho),
        (1, 1): 1 - rho,
    }
    for (team_goals, opponent_goals), factor in corrections.items():
        adjusted[team_goals][opponent_goals] *= max(0.5, min(1.5, factor))
    return _normalize_score_matrix(adjusted)


def apply_bivariate_poisson_adjustment(matrix: list[list[float]], shared_intensity: float = 0.05) -> list[list[float]]:
    adjusted = [row[:] for row in matrix]
    shared_intensity = max(0.0, min(0.18, float(shared_intensity or 0.0)))
    if shared_intensity <= 0:
        return adjusted
    for team_goals, row in enumerate(adjusted):
        for opponent_goals, _ in enumerate(row):
            if team_goals == opponent_goals:
                adjusted[team_goals][opponent_goals] *= 1 + shared_intensity
            elif abs(team_goals - opponent_goals) >= 3:
                adjusted[team_goals][opponent_goals] *= 1 - shared_intensity * 0.35
    return _normalize_score_matrix(adjusted)


def estimate_three_way_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any) -> float:
    team_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i > j)
    draw = sum(matrix[i][i] for i in range(len(matrix)))
    opponent_win = max(0.0, 1.0 - team_win - draw)
    text = str(selection or "").strip().lower()
    team_text = str(team or "").strip().lower()
    opponent_text = str(opponent or "").strip().lower()
    if text in {"draw", "x"}:
        return draw
    if text in {"away", "opponent", "2"} or (opponent_text and opponent_text in text):
        return opponent_win
    return team_win if text in {"home", "team", "1"} or (team_text and team_text in text) else team_win


def estimate_draw_no_bet_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any) -> float:
    team_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i > j)
    opponent_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i < j)
    denominator = max(0.01, team_win + opponent_win)
    text = str(selection or "").strip().lower()
    opponent_text = str(opponent or "").strip().lower()
    return opponent_win / denominator if opponent_text and opponent_text in text else team_win / denominator


def estimate_double_chance_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any) -> float:
    team_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i > j)
    draw = sum(matrix[i][i] for i in range(len(matrix)))
    opponent_win = max(0.0, 1.0 - team_win - draw)
    text = str(selection or "").strip().lower().replace(" ", "_")
    if text in {"1x", "team_or_draw"} or str(team or "").lower() in text and "draw" in text:
        return team_win + draw
    if text in {"x2", "opponent_or_draw"} or str(opponent or "").lower() in text and "draw" in text:
        return opponent_win + draw
    if text in {"12", "team_or_opponent", "no_draw"}:
        return team_win + opponent_win
    return team_win + draw


def estimate_handicap_probability(matrix: list[list[float]], line: float) -> float:
    cover = 0.0
    push = 0.0
    for team_goals, row in enumerate(matrix):
        for opponent_goals, probability in enumerate(row):
            result = (team_goals - opponent_goals) + line
            if result > 0:
                cover += probability
            elif result == 0:
                push += probability
    return max(0.03, min(0.97, cover + push * 0.5))


def estimate_total_probability_from_score_matrix(matrix: list[list[float]], total_line: float, selection: Any) -> float:
    over = 0.0
    under = 0.0
    push = 0.0
    for team_goals, row in enumerate(matrix):
        for opponent_goals, probability in enumerate(row):
            total = team_goals + opponent_goals
            if total > total_line:
                over += probability
            elif total < total_line:
                under += probability
            else:
                push += probability
    probability = under if "under" in str(selection or "").lower() else over
    return max(0.03, min(0.97, probability + push * 0.5))


def estimate_team_total_probability_from_score_matrix(matrix: list[list[float]], team_total_line: float, selection: Any) -> float:
    over = 0.0
    under = 0.0
    push = 0.0
    for team_goals, row in enumerate(matrix):
        probability = sum(row)
        if team_goals > team_total_line:
            over += probability
        elif team_goals < team_total_line:
            under += probability
        else:
            push += probability
    probability = under if "under" in str(selection or "").lower() else over
    return max(0.03, min(0.97, probability + push * 0.5))


def estimate_btts_probability(matrix: list[list[float]], selection: Any) -> float:
    yes = sum(matrix[i][j] for i in range(1, len(matrix)) for j in range(1, len(matrix[i])))
    return max(0.03, min(0.97, 1 - yes if "no" in str(selection or "").lower() else yes))


def estimate_correct_score_probability(matrix: list[list[float]], correct_score_selection: Any) -> float:
    numbers = [int(part) for part in re.findall(r"\d+", str(correct_score_selection or ""))[:2]]
    if len(numbers) != 2:
        return 0.03
    team_goals, opponent_goals = numbers
    if team_goals >= len(matrix) or opponent_goals >= len(matrix[0]):
        return 0.03
    return max(0.03, min(0.97, matrix[team_goals][opponent_goals]))


def estimate_first_half_lambdas(team_lambda: float, opponent_lambda: float, share: Optional[float] = None) -> tuple[float, float]:
    first_half_share = max(0.38, min(0.50, float(share) if share is not None else 0.45))
    return team_lambda * first_half_share, opponent_lambda * first_half_share


def calibrate_soccer_probability(
    *,
    raw_probability: float,
    market_anchor_probability: float,
    market_anchor_is_no_vig: bool,
    projected_goal_differential: float,
    market_key: str,
    input_confidence_hint: float,
) -> dict[str, Any]:
    flags: list[str] = []
    if raw_probability >= 0.90 or raw_probability <= 0.05:
        flags.append("raw probability extreme")
    anchor_weight = 0.25 if market_anchor_is_no_vig else 0.05
    calibrated = (raw_probability * (1 - anchor_weight)) + (market_anchor_probability * anchor_weight)
    if abs(calibrated - raw_probability) >= 0.025:
        flags.append("probability calibration applied")

    abs_diff = abs(projected_goal_differential)
    if market_key in {"draw_no_bet", "double_chance", "both_teams_to_score"}:
        lower_cap, upper_cap = 0.18, 0.86
    elif market_key in {"correct_score", "first_goal_scorer"}:
        lower_cap, upper_cap = 0.03, 0.32
    elif abs_diff >= 1.0 and input_confidence_hint >= 75:
        lower_cap, upper_cap = 0.12, 0.75
    elif abs_diff >= 0.60:
        lower_cap, upper_cap = 0.15, 0.70
    elif abs_diff >= 0.25:
        lower_cap, upper_cap = 0.20, 0.60
    else:
        lower_cap, upper_cap = 0.25, 0.50
    final_probability = max(lower_cap, min(upper_cap, calibrated))
    if final_probability != calibrated:
        flags.append("probability capped by projected goal differential")
        flags.append("probability calibration applied")
    return {
        "raw_model_probability": raw_probability,
        "calibrated_model_probability": calibrated,
        "final_probability": final_probability,
        "market_anchor_probability": market_anchor_probability,
        "probability_calibration_applied": bool(flags),
        "probability_sanity_flags": list(dict.fromkeys(flags)),
        "probability_cap_reason": f"projected goal differential {round(projected_goal_differential, 2)} goals",
    }


def build_nhl_score_matrix(team_lambda: float, opponent_lambda: float, max_goals: int = 9) -> list[list[float]]:
    team_probs = [poisson_pmf(i, max(0.10, min(6.5, team_lambda))) for i in range(max_goals)]
    opponent_probs = [poisson_pmf(i, max(0.10, min(6.5, opponent_lambda))) for i in range(max_goals)]
    team_probs.append(max(0.0, 1.0 - sum(team_probs)))
    opponent_probs.append(max(0.0, 1.0 - sum(opponent_probs)))
    return _normalize_score_matrix([[team_probs[i] * opponent_probs[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)])


def apply_bivariate_hockey_adjustment(matrix: list[list[float]], shared_intensity: float = 0.04) -> list[list[float]]:
    adjusted = [row[:] for row in matrix]
    shared_intensity = max(0.0, min(0.14, float(shared_intensity or 0.0)))
    if shared_intensity <= 0:
        return adjusted
    for team_goals, row in enumerate(adjusted):
        for opponent_goals, _ in enumerate(row):
            if team_goals == opponent_goals:
                adjusted[team_goals][opponent_goals] *= 1 + shared_intensity
            elif team_goals + opponent_goals >= 7:
                adjusted[team_goals][opponent_goals] *= 1 + shared_intensity * 0.25
            elif abs(team_goals - opponent_goals) >= 4:
                adjusted[team_goals][opponent_goals] *= 1 - shared_intensity * 0.30
    return _normalize_score_matrix(adjusted)


def estimate_nhl_three_way_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any) -> float:
    return estimate_three_way_probability(matrix, selection, team, opponent)


def estimate_nhl_regulation_moneyline_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any) -> float:
    return estimate_three_way_probability(matrix, selection, team, opponent)


def _nhl_matrix_parts(matrix: list[list[float]]) -> tuple[float, float, float]:
    team_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i > j)
    draw = sum(matrix[i][i] for i in range(len(matrix)))
    opponent_win = max(0.0, 1.0 - team_win - draw)
    return team_win, draw, opponent_win


def estimate_nhl_moneyline_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any, shootout_edge: float = 0.0) -> float:
    team_win, draw, opponent_win = _nhl_matrix_parts(matrix)
    text = str(selection or "").strip().lower()
    opponent_text = str(opponent or "").strip().lower()
    team_ot_share = max(0.42, min(0.58, 0.50 + shootout_edge))
    if opponent_text and opponent_text in text:
        return max(0.03, min(0.97, opponent_win + draw * (1 - team_ot_share)))
    return max(0.03, min(0.97, team_win + draw * team_ot_share))


def estimate_nhl_draw_no_bet_probability(matrix: list[list[float]], selection: Any, team: Any, opponent: Any) -> float:
    return estimate_draw_no_bet_probability(matrix, selection, team, opponent)


def estimate_nhl_puckline_probability(matrix: list[list[float]], line: float) -> float:
    return estimate_handicap_probability(matrix, line)


def estimate_nhl_total_probability_from_score_matrix(matrix: list[list[float]], total_line: float, selection: Any) -> float:
    return estimate_total_probability_from_score_matrix(matrix, total_line, selection)


def estimate_nhl_team_total_probability_from_score_matrix(matrix: list[list[float]], team_total_line: float, selection: Any) -> float:
    return estimate_team_total_probability_from_score_matrix(matrix, team_total_line, selection)


def estimate_nhl_period_lambdas(team_lambda: float, opponent_lambda: float, period: str, share: Optional[float] = None) -> tuple[float, float]:
    default_shares = {
        "first": 0.305,
        "second": 0.345,
        "third": 0.350,
    }
    share_value = max(0.24, min(0.42, float(share) if share is not None else default_shares.get(period, 0.33)))
    return team_lambda * share_value, opponent_lambda * share_value


def estimate_nhl_player_prop_probability(projection: float, prop_line: float) -> float:
    return _logistic_probability(projection - prop_line, max(0.55, abs(prop_line) * 0.25))


def calibrate_nhl_probability(
    *,
    raw_probability: float,
    market_anchor_probability: float,
    market_anchor_is_no_vig: bool,
    projected_goal_differential: float,
    market_key: str,
    input_confidence_hint: float,
    goalie_edge_quality: float,
) -> dict[str, Any]:
    flags: list[str] = []
    if raw_probability >= 0.88 or raw_probability <= 0.10:
        flags.append("raw probability extreme")
    anchor_weight = 0.25 if market_anchor_is_no_vig else 0.05
    calibrated = raw_probability * (1 - anchor_weight) + market_anchor_probability * anchor_weight
    if abs(calibrated - raw_probability) >= 0.025:
        flags.append("probability calibration applied")

    abs_diff = abs(projected_goal_differential)
    if market_key in {"three_way_moneyline", "regulation_moneyline"}:
        lower_cap, upper_cap = 0.14, 0.68
    elif market_key == "draw_no_bet":
        lower_cap, upper_cap = 0.22, 0.82
    elif market_key in {"puckline", "spread", "alternate_puckline", "total", "alternate_total", "team_total"}:
        lower_cap, upper_cap = 0.25, 0.76
    elif market_key in {"first_goal_scorer"}:
        lower_cap, upper_cap = 0.03, 0.32
    elif market_key in {"player_prop", "anytime_goal_scorer"}:
        lower_cap, upper_cap = 0.08, 0.78
    elif abs_diff >= 1.25 and input_confidence_hint >= 78 and goalie_edge_quality >= 0.4:
        lower_cap, upper_cap = 0.20, 0.82
    elif abs_diff >= 0.90:
        lower_cap, upper_cap = 0.30, 0.75
    elif abs_diff >= 0.50:
        lower_cap, upper_cap = 0.32, 0.70
    elif abs_diff >= 0.20:
        lower_cap, upper_cap = 0.38, 0.64
    else:
        lower_cap, upper_cap = 0.42, 0.58

    final_probability = max(lower_cap, min(upper_cap, calibrated))
    if final_probability != calibrated:
        flags.append("probability capped by projected goal differential")
        flags.append("probability calibration applied")
    return {
        "raw_model_probability": raw_probability,
        "calibrated_model_probability": calibrated,
        "final_probability": final_probability,
        "market_anchor_probability": market_anchor_probability,
        "probability_calibration_applied": bool(flags),
        "probability_sanity_flags": list(dict.fromkeys(flags)),
        "probability_cap_reason": f"projected goal differential {round(projected_goal_differential, 2)} goals",
    }


def tennis_logistic(value: float, scale: float = 1.0) -> float:
    return max(0.01, min(0.99, 1 / (1 + math.exp(-value / max(0.05, scale)))))


def estimate_tennis_base_strength(input_stats: dict[str, Any]) -> dict[str, float]:
    player_elo = _safe_float(input_stats.get("player_elo"), 1500) or 1500
    opponent_elo = _safe_float(input_stats.get("opponent_elo"), 1500) or 1500
    player_surface_elo = _safe_float(input_stats.get("player_surface_elo"), player_elo) or player_elo
    opponent_surface_elo = _safe_float(input_stats.get("opponent_surface_elo"), opponent_elo) or opponent_elo
    player_rank = _safe_float(input_stats.get("player_ranking"), 100) or 100
    opponent_rank = _safe_float(input_stats.get("opponent_ranking"), 100) or 100
    form_edge = (
        (_safe_float(input_stats.get("player_recent_form_wins"), 0) or 0)
        - (_safe_float(input_stats.get("player_recent_form_losses"), 0) or 0)
        - (_safe_float(input_stats.get("opponent_recent_form_wins"), 0) or 0)
        + (_safe_float(input_stats.get("opponent_recent_form_losses"), 0) or 0)
    ) * 4.0
    rank_edge = max(-55, min(55, (opponent_rank - player_rank) * 0.6))
    player_strength = player_elo * 0.45 + player_surface_elo * 0.45 + rank_edge + form_edge
    opponent_strength = opponent_elo * 0.45 + opponent_surface_elo * 0.45
    return {
        "player_strength_rating": round(player_strength, 2),
        "opponent_strength_rating": round(opponent_strength, 2),
        "player_surface_edge": round(player_surface_elo - opponent_surface_elo, 2),
    }


def estimate_tennis_serve_point_probability(input_stats: dict[str, Any], prefix: str) -> float:
    opponent_prefix = "opponent" if prefix == "player" else "player"
    first_in = (_safe_float(input_stats.get(f"{prefix}_first_serve_in_percent"), 62) or 62) / 100
    first_won = (_safe_float(input_stats.get(f"{prefix}_first_serve_points_won_percent"), 70) or 70) / 100
    second_won = (_safe_float(input_stats.get(f"{prefix}_second_serve_points_won_percent"), 52) or 52) / 100
    ace_rate = (_safe_float(input_stats.get(f"{prefix}_ace_rate"), 7) or 7) / 100
    df_rate = (_safe_float(input_stats.get(f"{prefix}_double_fault_rate"), 3) or 3) / 100
    opponent_return = (_safe_float(input_stats.get(f"{opponent_prefix}_return_points_won_percent"), 38) or 38) / 100
    point_probability = first_in * first_won + (1 - first_in) * second_won + ace_rate * 0.25 - df_rate * 0.35
    point_probability = point_probability * 0.86 + (1 - opponent_return) * 0.14
    return max(0.42, min(0.75, point_probability))


def estimate_tennis_hold_probability_from_points(point_probability: float) -> float:
    p = max(0.35, min(0.80, point_probability))
    q = 1 - p
    pre_deuce = p**4 * (1 + 4 * q + 10 * q**2)
    deuce = 20 * p**3 * q**3
    win_from_deuce = p * p / max(0.01, 1 - 2 * p * q)
    return max(0.45, min(0.95, pre_deuce + deuce * win_from_deuce))


def estimate_tennis_tiebreak_probability(player_serve_point: float, opponent_serve_point: float, input_stats: dict[str, Any]) -> float:
    base = 0.5 + (player_serve_point - opponent_serve_point) * 0.75
    tb_edge = ((_safe_float(input_stats.get("player_tiebreak_win_percent"), 50) or 50) - (_safe_float(input_stats.get("opponent_tiebreak_win_percent"), 50) or 50)) / 100
    return max(0.30, min(0.70, base + tb_edge * 0.12))


def estimate_tennis_set_probability(player_hold: float, opponent_hold: float, tiebreak_probability: float) -> float:
    service_edge = (player_hold - opponent_hold)
    raw = 0.5 + service_edge * 1.15 + (tiebreak_probability - 0.5) * 0.18
    return max(0.20, min(0.80, raw))


def estimate_tennis_match_probability(set_probability: float, best_of_sets: int) -> float:
    p = max(0.05, min(0.95, set_probability))
    if int(best_of_sets or 3) >= 5:
        return p**3 + 3 * p**3 * (1 - p) + 6 * p**3 * (1 - p) ** 2
    return p * p + 2 * p * p * (1 - p)


def estimate_tennis_set_score_distribution(set_probability: float, best_of_sets: int) -> dict[str, float]:
    p = max(0.05, min(0.95, set_probability))
    if int(best_of_sets or 3) >= 5:
        return {
            "3-0": p**3,
            "3-1": 3 * p**3 * (1 - p),
            "3-2": 6 * p**3 * (1 - p) ** 2,
            "0-3": (1 - p) ** 3,
            "1-3": 3 * (1 - p) ** 3 * p,
            "2-3": 6 * (1 - p) ** 3 * p**2,
        }
    return {
        "2-0": p**2,
        "2-1": 2 * p**2 * (1 - p),
        "0-2": (1 - p) ** 2,
        "1-2": 2 * (1 - p) ** 2 * p,
    }


def estimate_tennis_game_margin_distribution(match_probability: float, set_probability: float, best_of_sets: int) -> dict[str, float]:
    expected_sets = 3.0 if int(best_of_sets or 3) >= 5 else 2.35
    if abs(set_probability - 0.5) < 0.045:
        expected_sets += 0.35
    mean_margin = (match_probability - 0.5) * (10 if int(best_of_sets or 3) >= 5 else 7)
    expected_total = expected_sets * (9.6 + (1 - abs(set_probability - 0.5)) * 1.8)
    return {"mean_margin": mean_margin, "expected_total_games": expected_total, "volatility": 5.5 if int(best_of_sets or 3) >= 5 else 4.0}


def estimate_tennis_total_games_probability(total_line: float, selection: Any, game_distribution: dict[str, float]) -> float:
    raw = tennis_logistic(game_distribution["expected_total_games"] - total_line, game_distribution["volatility"])
    return 1 - raw if "under" in str(selection or "").lower() else raw


def estimate_tennis_first_set_total_probability(total_line: float, selection: Any, set_probability: float) -> float:
    expected = 9.2 + (1 - abs(set_probability - 0.5)) * 2.3
    raw = tennis_logistic(expected - total_line, 2.2)
    return 1 - raw if "under" in str(selection or "").lower() else raw


def estimate_tennis_correct_score_probability(distribution: dict[str, float], correct_score_selection: Any) -> float:
    text = str(correct_score_selection or "").strip()
    return max(0.03, min(0.65, distribution.get(text, 0.03)))


def estimate_tennis_player_prop_probability(projection: float, prop_line: float) -> float:
    return max(0.03, min(0.82, tennis_logistic(projection - prop_line, max(0.55, abs(prop_line) * 0.22))))


def calibrate_tennis_probability(
    *,
    raw_probability: float,
    market_anchor_probability: float,
    market_anchor_is_no_vig: bool,
    elo_gap: float,
    surface_edge: float,
    market_key: str,
    input_confidence_hint: float,
) -> dict[str, Any]:
    flags: list[str] = []
    if raw_probability >= 0.88 or raw_probability <= 0.12:
        flags.append("raw probability extreme")
    anchor_weight = 0.25 if market_anchor_is_no_vig else 0.05
    calibrated = raw_probability * (1 - anchor_weight) + market_anchor_probability * anchor_weight
    if abs(calibrated - raw_probability) >= 0.025:
        flags.append("probability calibration applied")
    edge_size = abs(elo_gap) * 0.75 + abs(surface_edge) * 0.25
    if market_key in {"correct_score"}:
        lower_cap, upper_cap = 0.03, 0.45
    elif market_key in {"first_set_moneyline", "first_set_total_games", "player_prop", "aces", "double_faults", "break_points", "service_games_won", "return_games_won"}:
        lower_cap, upper_cap = 0.14, 0.75
    elif edge_size >= 220 and input_confidence_hint >= 78:
        lower_cap, upper_cap = 0.12, 0.88
    elif edge_size >= 140:
        lower_cap, upper_cap = 0.18, 0.82
    elif edge_size >= 70:
        lower_cap, upper_cap = 0.22, 0.78
    else:
        lower_cap, upper_cap = 0.25, 0.75
    final_probability = max(lower_cap, min(upper_cap, calibrated))
    if final_probability != calibrated:
        flags.append("probability capped by tennis strength edge")
        flags.append("probability calibration applied")
    return {
        "raw_model_probability": raw_probability,
        "calibrated_model_probability": calibrated,
        "final_probability": final_probability,
        "market_anchor_probability": market_anchor_probability,
        "probability_calibration_applied": bool(flags),
        "probability_sanity_flags": list(dict.fromkeys(flags)),
        "probability_cap_reason": f"elo gap {round(elo_gap, 1)}, surface edge {round(surface_edge, 1)}",
    }


def calibrate_mlb_probability(
    *,
    raw_probability: float,
    market_anchor_probability: float,
    market_anchor_is_no_vig: bool,
    projected_run_differential: float,
    input_confidence_hint: float,
) -> dict[str, Any]:
    flags: list[str] = []
    if raw_probability >= 0.88 or raw_probability <= 0.12:
        flags.append("raw probability extreme")

    abs_diff = abs(projected_run_differential)
    high_quality_extreme = abs_diff >= 2.0 and input_confidence_hint >= 78
    if (raw_probability >= 0.88 or raw_probability <= 0.12) and not high_quality_extreme:
        model_floor = 0.62 if raw_probability >= 0.88 else 0.38
        anchor_weight = 0.85 if market_anchor_is_no_vig else 0.05
        calibrated = (model_floor * (1 - anchor_weight)) + (market_anchor_probability * anchor_weight)
    else:
        anchor_weight = 0.25 if market_anchor_is_no_vig else 0.05
        calibrated = (raw_probability * (1 - anchor_weight)) + (market_anchor_probability * anchor_weight)
    if abs(calibrated - raw_probability) >= 0.025:
        flags.append("probability calibration applied")

    if high_quality_extreme:
        lower_cap, upper_cap = 0.18, 0.86
    elif abs_diff >= 1.5:
        lower_cap, upper_cap = 0.22, 0.78
    elif abs_diff >= 1.0:
        lower_cap, upper_cap = 0.28, 0.72
    elif abs_diff >= 0.5:
        lower_cap, upper_cap = 0.35, 0.65
    else:
        lower_cap, upper_cap = 0.42, 0.58

    final_probability = max(lower_cap, min(upper_cap, calibrated))
    if final_probability != calibrated:
        flags.append("probability capped by projected run differential")
        flags.append("probability calibration applied")
    return {
        "raw_model_probability": raw_probability,
        "calibrated_model_probability": calibrated,
        "final_probability": final_probability,
        "market_anchor_probability": market_anchor_probability,
        "probability_calibration_applied": bool(flags),
        "probability_sanity_flags": list(dict.fromkeys(flags)),
        "probability_cap_reason": f"projected run differential {round(projected_run_differential, 2)} runs",
    }


def calculate_edge_percent(true_probability: Optional[float], implied_probability: Optional[float]) -> Optional[float]:
    return edge_percentage(true_probability, implied_probability) if true_probability is not None and implied_probability is not None else None


def calculate_confidence(base: float, *adjustments: float) -> float:
    return max(1, min(95, round(base + sum(adjustments), 2)))


def calculate_suggested_stake(
    *,
    bankroll: float,
    american_odds: Optional[float],
    true_probability: Optional[float],
    risk_profile: str,
    confidence: float,
) -> float:
    if american_odds is None or true_probability is None:
        return 0.0
    return suggested_stake_with_risk_controls(
        bankroll=bankroll,
        american_odds=american_odds,
        true_probability=true_probability,
        risk_profile="standard" if str(risk_profile or "").lower() == "moderate" else risk_profile,
        confidence_0_100=confidence,
    )


def _combat_pct(value: Any, default: float = 0.0) -> float:
    number = _safe_float(value, default)
    if number is None:
        return default
    return number / 100 if number > 1 else number


def _combat_market_probability(
    *,
    market: str,
    selection: Any,
    fighter_win_probability: float,
    opponent_win_probability: float,
    ko_tko_probability: float,
    submission_probability: float,
    decision_probability: float,
    goes_distance_probability: float,
    scheduled_rounds: float,
    line: Optional[float],
) -> float:
    market_key = _normal_market_key(market)
    selection_text = str(selection or "").strip().lower()
    does_not_go_distance = 1 - goes_distance_probability
    if market_key in {"moneyline", "match_winner"}:
        return fighter_win_probability
    if market_key in {"method_of_victory", "fighter_by_ko_tko"}:
        return ko_tko_probability
    if market_key == "fighter_by_submission":
        return submission_probability
    if market_key == "fighter_by_decision":
        return decision_probability
    if market_key == "opponent_by_ko_tko":
        return opponent_win_probability * max(0.05, min(0.80, ko_tko_probability / max(fighter_win_probability, 0.01) * 0.85))
    if market_key == "opponent_by_submission":
        return opponent_win_probability * max(0.03, min(0.65, submission_probability / max(fighter_win_probability, 0.01) * 0.85))
    if market_key == "opponent_by_decision":
        return opponent_win_probability * max(0.08, min(0.75, decision_probability / max(fighter_win_probability, 0.01) * 0.90))
    if market_key == "fight_goes_distance":
        return goes_distance_probability
    if market_key == "fight_does_not_go_distance":
        return does_not_go_distance
    if market_key == "over_rounds":
        round_line = line if line is not None else scheduled_rounds - 0.5
        round_share = max(0.15, min(0.95, round_line / max(scheduled_rounds, 1)))
        return max(0.08, min(0.88, goes_distance_probability + (1 - goes_distance_probability) * (1 - round_share) * 0.55))
    if market_key == "under_rounds":
        round_line = line if line is not None else scheduled_rounds - 0.5
        round_share = max(0.15, min(0.95, round_line / max(scheduled_rounds, 1)))
        over_probability = max(0.08, min(0.88, goes_distance_probability + (1 - goes_distance_probability) * (1 - round_share) * 0.55))
        return 1 - over_probability
    if market_key == "round_group":
        return max(0.12, min(0.55, does_not_go_distance * 0.50))
    if market_key == "exact_round":
        return max(0.04, min(0.25, does_not_go_distance / max(scheduled_rounds, 1)))
    if market_key == "double_chance":
        if "ko" in selection_text or "tko" in selection_text:
            return max(0.10, min(0.75, ko_tko_probability + submission_probability * 0.45))
        return max(0.10, min(0.75, ko_tko_probability + decision_probability * 0.45))
    if market_key == "knockdown_prop":
        return max(0.12, min(0.72, ko_tko_probability + does_not_go_distance * 0.18))
    if market_key == "takedown_prop":
        return max(0.12, min(0.72, submission_probability + 0.22))
    if market_key == "significant_strikes_prop":
        return max(0.15, min(0.78, goes_distance_probability + 0.10))
    if market_key == "submission_attempt_prop":
        return max(0.10, min(0.70, submission_probability + 0.18))
    return fighter_win_probability


def _estimate_combat_finish_model(
    *,
    sport: str,
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    missing = _combat_full_inputs_missing(input_stats, payload) + _combat_market_specific_missing(market, input_stats, payload)
    if missing:
        return None
    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None
    if implied_probability is None:
        return None

    fighter_elo = _safe_float(input_stats.get("fighter_elo"), 1500) or 1500
    opponent_elo = _safe_float(input_stats.get("opponent_elo"), 1500) or 1500
    fighter_recent = _combat_pct(input_stats.get("fighter_recent_win_percent"), 0.50)
    opponent_recent = _combat_pct(input_stats.get("opponent_recent_win_percent"), 0.50)
    fighter_finish = _combat_pct(input_stats.get("fighter_finish_rate"), 0.45)
    opponent_finish = _combat_pct(input_stats.get("opponent_finish_rate"), 0.45)
    fighter_ko = _combat_pct(input_stats.get("fighter_ko_tko_rate"), 0.25)
    opponent_ko = _combat_pct(input_stats.get("opponent_ko_tko_rate"), 0.25)
    fighter_sub = 0.0 if sport == "boxing" else _combat_pct(input_stats.get("fighter_submission_rate"), 0.15)
    opponent_sub = 0.0 if sport == "boxing" else _combat_pct(input_stats.get("opponent_submission_rate"), 0.15)
    fighter_decision = _combat_pct(input_stats.get("fighter_decision_rate"), 0.35)
    opponent_decision = _combat_pct(input_stats.get("opponent_decision_rate"), 0.35)

    striking_edge = (
        (_safe_float(input_stats.get("fighter_strikes_landed_per_min"), 0) or 0)
        - (_safe_float(input_stats.get("opponent_strikes_landed_per_min"), 0) or 0)
        - ((_safe_float(input_stats.get("fighter_strikes_absorbed_per_min"), 0) or 0) - (_safe_float(input_stats.get("opponent_strikes_absorbed_per_min"), 0) or 0)) * 0.55
        + ((_combat_pct(input_stats.get("fighter_striking_accuracy"), 0.45) - _combat_pct(input_stats.get("opponent_striking_accuracy"), 0.45)) * 6)
        + ((_combat_pct(input_stats.get("fighter_striking_defense"), 0.55) - _combat_pct(input_stats.get("opponent_striking_defense"), 0.55)) * 5)
    )
    grappling_edge = (
        ((_safe_float(input_stats.get("fighter_takedown_average"), 0) or 0) - (_safe_float(input_stats.get("opponent_takedown_average"), 0) or 0)) * 0.18
        + ((_combat_pct(input_stats.get("fighter_takedown_accuracy"), 0.35) - _combat_pct(input_stats.get("opponent_takedown_accuracy"), 0.35)) * 2.2)
        + ((_combat_pct(input_stats.get("fighter_takedown_defense"), 0.65) - _combat_pct(input_stats.get("opponent_takedown_defense"), 0.65)) * 2.0)
        + ((_safe_float(input_stats.get("fighter_submission_average"), 0) or 0) - (_safe_float(input_stats.get("opponent_submission_average"), 0) or 0)) * 0.18
    )
    if sport == "boxing":
        grappling_edge = 0
    age_edge = ((_safe_float(input_stats.get("opponent_age"), 30) or 30) - (_safe_float(input_stats.get("fighter_age"), 30) or 30)) * 0.018
    reach_edge = ((_safe_float(input_stats.get("fighter_reach"), 72) or 72) - (_safe_float(input_stats.get("opponent_reach"), 72) or 72)) * 0.018
    height_edge = ((_safe_float(input_stats.get("fighter_height"), 70) or 70) - (_safe_float(input_stats.get("opponent_height"), 70) or 70)) * 0.010
    rest_edge = ((_safe_float(input_stats.get("fighter_days_rest"), 90) or 90) - (_safe_float(input_stats.get("opponent_days_rest"), 90) or 90)) * 0.0008
    cardio_edge = ((_safe_float(input_stats.get("cardio_rating"), 70) or 70) - 70) * 0.006
    explicit_style_edge = ((_safe_float(input_stats.get("striking_advantage"), 0) or 0) + (_safe_float(input_stats.get("grappling_advantage"), 0) or 0)) * 0.01
    injury_penalty = -0.12 if str(input_stats.get("fighter_injury_status", "")).lower() not in {"healthy", "clear", "none"} else 0
    opponent_injury_bonus = 0.08 if str(input_stats.get("opponent_injury_status", "")).lower() not in {"healthy", "clear", "none"} else 0

    model_score = (
        (fighter_elo - opponent_elo) / 450
        + (fighter_recent - opponent_recent) * 0.55
        + striking_edge * 0.08
        + grappling_edge * 0.11
        + age_edge
        + reach_edge
        + height_edge
        + rest_edge
        + cardio_edge
        + explicit_style_edge
        + injury_penalty
        + opponent_injury_bonus
    )
    raw_win_probability = 1 / (1 + math.exp(-model_score))
    no_vig_anchor = _safe_float(input_stats.get("no_vig_market_probability"))
    if no_vig_anchor is not None and no_vig_anchor > 1:
        no_vig_anchor = no_vig_anchor / 100
    market_anchor = max(0.01, min(0.99, no_vig_anchor)) if no_vig_anchor is not None else None
    market_weight = 0.15 if market_anchor is not None else 0.0
    calibrated_win_probability = (
        raw_win_probability * (1 - market_weight) + market_anchor * market_weight
        if market_anchor is not None
        else raw_win_probability
    )
    abs_score = abs(model_score)
    if abs_score < 0.45:
        low_cap, high_cap = 0.36, 0.64
    elif abs_score < 0.90:
        low_cap, high_cap = 0.28, 0.74
    else:
        low_cap, high_cap = 0.20, 0.84
    flags = []
    probability_cap_reason = None
    final_win_probability = max(low_cap, min(high_cap, calibrated_win_probability))
    if final_win_probability != calibrated_win_probability:
        flags.append("combat probability cap applied")
        probability_cap_reason = f"fighter model score {round(model_score, 3)}"
    if raw_win_probability > 0.88 or raw_win_probability < 0.12:
        flags.append("raw probability extreme")

    fighter_win_probability = final_win_probability
    opponent_win_probability = 1 - fighter_win_probability
    finish_pressure = max(0.08, min(0.92, (fighter_finish + opponent_finish) / 2))
    durability = _safe_float(input_stats.get("chin_durability"), 70) or 70
    cardio = _safe_float(input_stats.get("cardio_rating"), 70) or 70
    scheduled_rounds = _safe_float(input_stats.get("scheduled_rounds"), 3) or 3
    pace = _safe_float(input_stats.get("pace_rating"), 70) or 70
    does_not_go_distance = max(0.12, min(0.82, finish_pressure * 0.72 + (pace - 70) * 0.002 - (durability - 70) * 0.002 - (cardio - 70) * 0.001))
    if scheduled_rounds >= 5:
        does_not_go_distance = min(0.88, does_not_go_distance + 0.05)
    goes_distance_probability = 1 - does_not_go_distance
    finish_total = max(0.01, fighter_ko + fighter_sub + fighter_decision)
    ko_share = fighter_ko / finish_total
    sub_share = fighter_sub / finish_total
    decision_share = fighter_decision / finish_total
    ko_tko_probability = fighter_win_probability * (does_not_go_distance * ko_share + 0.04)
    submission_probability = fighter_win_probability * (does_not_go_distance * sub_share + 0.02)
    decision_probability = max(0.02, fighter_win_probability - ko_tko_probability - submission_probability)
    if sport == "boxing":
        submission_probability = 0.0
        decision_probability = max(0.02, fighter_win_probability - ko_tko_probability)

    line = _safe_float(payload.get("line"), _safe_float(input_stats.get("line")))
    market_probability = _combat_market_probability(
        market=str(market or "moneyline"),
        selection=payload.get("selection") or input_stats.get("selection"),
        fighter_win_probability=fighter_win_probability,
        opponent_win_probability=opponent_win_probability,
        ko_tko_probability=ko_tko_probability,
        submission_probability=submission_probability,
        decision_probability=decision_probability,
        goes_distance_probability=goes_distance_probability,
        scheduled_rounds=scheduled_rounds,
        line=line,
    )
    market_key = _normal_market_key(market)
    if market_key == "moneyline":
        market_probability = fighter_win_probability
    else:
        market_probability = max(0.03, min(0.88, market_probability))

    confidence = 72.0
    risk_flags = []
    for flag, penalty in [
        ("short notice", 8),
        ("weight cut risk", 7),
        ("travel risk", 4),
        ("altitude risk", 4),
    ]:
        key = flag.replace(" ", "_")
        if input_stats.get(key):
            risk_flags.append(flag)
            confidence -= penalty
    if str(input_stats.get("fighter_injury_status", "healthy")).lower() not in {"healthy", "clear", "none"}:
        risk_flags.append("injury uncertainty")
        confidence -= 12
    if (_safe_float(input_stats.get("fighter_days_rest"), 90) or 90) > 365:
        risk_flags.append("large layoff")
        confidence -= 6
    if market_key in {"exact_round", "round_group", "method_of_victory", "knockdown_prop", "takedown_prop", "significant_strikes_prop", "submission_attempt_prop"}:
        risk_flags.append("volatile market")
        confidence -= 5
    if not input_stats.get("book_count") or (_safe_float(input_stats.get("book_count"), 0) or 0) < 5:
        risk_flags.append("book count too low")
        confidence -= 3
    if not input_stats.get("best_available_odds"):
        risk_flags.append("best available odds missing")
        confidence -= 2
    confidence = max(1, min(95, round(confidence, 2)))
    risk = "high" if risk_flags or market_key in {"exact_round", "round_group"} else "moderate"
    edge = calculate_edge_percent(market_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags = []
    if edge is not None and edge <= 0:
        no_bet_flags.append("negative edge")
    elif edge is not None and edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
    if "injury uncertainty" in risk_flags and market_key not in {"moneyline", "fight_goes_distance", "fight_does_not_go_distance"}:
        no_bet_flags.append("risk too high")
    suggested = 0.0 if no_bet_flags else calculate_suggested_stake(
        bankroll=bankroll,
        american_odds=odds_american,
        true_probability=market_probability,
        risk_profile=risk_profile,
        confidence=confidence,
    )
    if suggested <= 0 and not no_bet_flags and edge is not None and edge >= edge_threshold and confidence >= confidence_threshold:
        suggested = round(max(1.0, bankroll * 0.005), 2)

    return {
        "model_status": "active",
        "true_probability": market_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "no_bet_flags": no_bet_flags,
        "raw_model_probability": raw_win_probability,
        "calibrated_model_probability": calibrated_win_probability,
        "probability_calibration_applied": bool(market_anchor is not None or flags),
        "probability_sanity_flags": list(dict.fromkeys(flags)),
        "probability_cap_reason": probability_cap_reason,
        "market_anchor_probability": market_anchor,
        "fighter_win_probability": fighter_win_probability,
        "opponent_win_probability": opponent_win_probability,
        "ko_tko_probability": ko_tko_probability,
        "submission_probability": submission_probability,
        "decision_probability": decision_probability,
        "goes_distance_probability": goes_distance_probability,
        "does_not_go_distance_probability": 1 - goes_distance_probability,
        "over_rounds_probability": _combat_market_probability(market="over_rounds", selection="Over", fighter_win_probability=fighter_win_probability, opponent_win_probability=opponent_win_probability, ko_tko_probability=ko_tko_probability, submission_probability=submission_probability, decision_probability=decision_probability, goes_distance_probability=goes_distance_probability, scheduled_rounds=scheduled_rounds, line=line),
        "under_rounds_probability": _combat_market_probability(market="under_rounds", selection="Under", fighter_win_probability=fighter_win_probability, opponent_win_probability=opponent_win_probability, ko_tko_probability=ko_tko_probability, submission_probability=submission_probability, decision_probability=decision_probability, goes_distance_probability=goes_distance_probability, scheduled_rounds=scheduled_rounds, line=line),
        "risk_flags": risk_flags,
        "input_coverage": 1.0,
        "provider_enrichment": {"provider_status": "not_provided", "provider_enrichment_present": []},
    }


def _normal_cdf(value: float, mean: float = 0.0, stddev: float = 1.0) -> float:
    stddev = max(0.0001, stddev)
    z = (value - mean) / (stddev * math.sqrt(2))
    return max(0.0, min(1.0, 0.5 * (1 + math.erf(z))))


def _golf_number(input_stats: dict[str, Any], key: str, default: float = 0.0) -> float:
    return _safe_float(input_stats.get(key), default) or default


def _golf_strength_score(input_stats: dict[str, Any], prefix: str = "player") -> float:
    rank = _golf_number(input_stats, f"{prefix}_world_rank", 80)
    recent_rank = _golf_number(input_stats, f"{prefix}_recent_form_rank", 70)
    scoring = _golf_number(input_stats, f"{prefix}_recent_scoring_average", 70.8)
    fit = _golf_number(input_stats, f"{prefix}_course_fit_score", _golf_number(input_stats, "course_fit_score", 65))
    history = _golf_number(input_stats, f"{prefix}_course_history_score", _golf_number(input_stats, "course_history_score", 60))
    sg_total = _golf_number(input_stats, f"{prefix}_sg_total", 0)
    sg_off_tee = _golf_number(input_stats, f"{prefix}_sg_off_tee", 0)
    sg_approach = _golf_number(input_stats, f"{prefix}_sg_approach", 0)
    sg_around_green = _golf_number(input_stats, f"{prefix}_sg_around_green", 0)
    sg_putting = _golf_number(input_stats, f"{prefix}_sg_putting", 0)
    return (
        sg_total * 0.55
        + sg_approach * 0.22
        + sg_off_tee * 0.13
        + sg_putting * 0.08
        + sg_around_green * 0.07
        + (100 - min(rank, 200)) / 100 * 0.45
        + (100 - min(recent_rank, 200)) / 100 * 0.22
        + (70.5 - scoring) * 0.16
        + (fit - 60) / 100 * 0.28
        + (history - 55) / 100 * 0.12
    )


def _golf_place_probabilities(input_stats: dict[str, Any], strength: float, calibrated_strength: Optional[float] = None) -> dict[str, float]:
    field_size = max(20, min(180, int(_golf_number(input_stats, "field_size", 120))))
    field_strength = max(40, min(100, _golf_number(input_stats, "field_strength", 75)))
    difficulty = max(40, min(100, _golf_number(input_stats, "course_difficulty_rating", 70)))
    wind = max(0, min(100, _golf_number(input_stats, "weather_wind_rating", 35)))
    volatility = 1 + max(0, field_strength - 70) * 0.006 + max(0, difficulty - 70) * 0.004 + max(0, wind - 40) * 0.004
    strength_for_probs = calibrated_strength if calibrated_strength is not None else strength
    win_base = math.exp(max(-2.5, min(2.5, strength_for_probs * 1.18))) / field_size
    outright = max(0.002, min(0.22, win_base * 1.35 / volatility))
    top5 = max(0.02, min(0.62, outright * 4.4 + 0.035 + strength_for_probs * 0.025))
    top10 = max(0.04, min(0.76, outright * 7.1 + 0.075 + strength_for_probs * 0.035))
    top20 = max(0.08, min(0.90, outright * 11.5 + 0.17 + strength_for_probs * 0.045))
    cut_projection = _golf_number(input_stats, "cut_line_projection", 75)
    make_cut = cut_projection / 100 if cut_projection > 1 else cut_projection
    if input_stats.get("cut_line_projection") is None:
        make_cut = _normal_cdf(strength_for_probs, mean=-0.18, stddev=0.72)
    make_cut = max(0.12, min(0.96, make_cut))
    return {
        "outright_winner": outright,
        "top_5": top5,
        "top_10": top10,
        "top_20": top20,
        "make_cut": make_cut,
        "miss_cut": 1 - make_cut,
    }


def _golf_market_probability(
    *,
    market: str,
    selection: Any,
    input_stats: dict[str, Any],
    strength: float,
    place_probs: dict[str, float],
    line: Optional[float],
) -> float:
    market_key = _normal_market_key(market)
    if market_key in place_probs:
        return place_probs[market_key]
    if market_key == "top_n_finish":
        top_n = max(1, _safe_float(input_stats.get("top_n"), 10) or 10)
        if top_n <= 5:
            return place_probs["top_5"]
        if top_n <= 10:
            return place_probs["top_10"]
        if top_n <= 20:
            return place_probs["top_20"]
        return max(place_probs["top_20"], min(0.96, place_probs["top_20"] + (top_n - 20) * 0.012))
    if market_key == "finishing_position":
        finish_line = line if line is not None else _safe_float(input_stats.get("line"), 20) or 20
        return _golf_market_probability(market="top_n_finish", selection=selection, input_stats={**input_stats, "top_n": finish_line}, strength=strength, place_probs=place_probs, line=line)
    if market_key in {"tournament_matchup", "round_matchup", "three_ball"}:
        opponent_strength = _golf_strength_score(input_stats, "opponent")
        diff = strength - opponent_strength
        base = 1 / (1 + math.exp(-diff / 0.75))
        if market_key == "three_ball":
            return max(0.18, min(0.62, base * 0.74))
        if market_key == "round_matchup":
            return max(0.28, min(0.72, 0.5 + (base - 0.5) * 0.72))
        return max(0.30, min(0.74, base))
    if market_key == "first_round_leader":
        return max(0.002, min(0.14, place_probs["outright_winner"] * 0.72))

    round_score_mean = 70.8 - strength * 0.85 + (_golf_number(input_stats, "course_difficulty_rating", 70) - 70) * 0.045 + (_golf_number(input_stats, "weather_wind_rating", 35) - 35) * 0.025
    prop_line = line if line is not None else _safe_float(input_stats.get("line"))
    selection_text = str(selection or "").lower()
    if market_key == "round_score_prop":
        score_line = prop_line if prop_line is not None else 70.5
        under_prob = _normal_cdf(score_line, mean=round_score_mean, stddev=2.25)
        return 1 - under_prob if "over" in selection_text else under_prob
    birdies_mean = max(2.0, min(6.2, 3.7 + strength * 0.45 - (_golf_number(input_stats, "course_difficulty_rating", 70) - 70) * 0.015))
    if market_key in {"birdies_prop", "player_prop"}:
        prop_type = str(input_stats.get("prop_type") or "").lower()
        if market_key == "player_prop" and prop_type and "bird" not in prop_type:
            pass
        birdie_line = prop_line if prop_line is not None else 3.5
        over_prob = 1 - _normal_cdf(birdie_line, mean=birdies_mean, stddev=1.25)
        return over_prob if "over" in selection_text or market_key == "player_prop" else 1 - over_prob
    if market_key == "eagles_prop":
        eagle_line = prop_line if prop_line is not None else 0.5
        over_prob = max(0.03, min(0.28, 0.10 + strength * 0.025 - eagle_line * 0.04))
        return over_prob if "over" in selection_text else 1 - over_prob
    if market_key == "fairways_hit_prop":
        fairway_line = prop_line if prop_line is not None else 8.5
        fairways_mean = max(6.0, min(11.5, 8.7 + _golf_number(input_stats, "player_sg_off_tee", 0) * 0.35))
        over_prob = 1 - _normal_cdf(fairway_line, mean=fairways_mean, stddev=1.65)
        return over_prob if "over" in selection_text else 1 - over_prob
    if market_key == "greens_in_regulation_prop":
        gir_line = prop_line if prop_line is not None else 12.5
        gir_mean = max(9.0, min(15.8, 12.1 + _golf_number(input_stats, "player_sg_approach", 0) * 0.72))
        over_prob = 1 - _normal_cdf(gir_line, mean=gir_mean, stddev=1.9)
        return over_prob if "over" in selection_text else 1 - over_prob
    if market_key == "putts_prop":
        putts_line = prop_line if prop_line is not None else 29.5
        putts_mean = max(26.5, min(32.5, 29.1 - _golf_number(input_stats, "player_sg_putting", 0) * 0.65))
        under_prob = _normal_cdf(putts_line, mean=putts_mean, stddev=2.0)
        return 1 - under_prob if "over" in selection_text else under_prob
    return place_probs["top_10"]


def _estimate_golf_course_fit_model(
    *,
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    missing = _golf_full_inputs_missing(input_stats, payload) + _golf_market_specific_missing(market, input_stats, payload)
    if missing:
        return None
    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None
    if implied_probability is None:
        return None

    strength = _golf_strength_score(input_stats, "player")
    raw_model_probability = max(0.02, min(0.98, 1 / (1 + math.exp(-strength / 0.85))))
    no_vig_anchor = _safe_float(input_stats.get("no_vig_market_probability"))
    if no_vig_anchor is not None and no_vig_anchor > 1:
        no_vig_anchor = no_vig_anchor / 100
    market_anchor = max(0.01, min(0.99, no_vig_anchor)) if no_vig_anchor is not None else None
    anchor_weight = 0.12 if market_anchor is not None else 0.0
    calibrated_strength = strength
    calibrated_model_probability = raw_model_probability
    if market_anchor is not None:
        calibrated_model_probability = raw_model_probability * (1 - anchor_weight) + market_anchor * anchor_weight
        calibrated_strength = math.log(calibrated_model_probability / max(0.001, 1 - calibrated_model_probability)) * 0.85
    place_probs = _golf_place_probabilities(input_stats, strength, calibrated_strength)
    line = _safe_float(payload.get("line"), _safe_float(input_stats.get("line")))
    market_probability = _golf_market_probability(
        market=str(market or "top_10"),
        selection=payload.get("selection") or input_stats.get("selection"),
        input_stats=input_stats,
        strength=calibrated_strength,
        place_probs=place_probs,
        line=line,
    )
    market_probability = max(0.002, min(0.94, market_probability))
    sanity_flags = []
    probability_cap_reason = None
    if market_probability in {0.002, 0.94}:
        sanity_flags.append("golf probability cap applied")
        probability_cap_reason = "market probability bounded by golf sanity caps"
    confidence = 74.0
    risk_flags = []
    market_key = _normal_market_key(market)
    if input_stats.get("weather_wind_rating") is not None and _golf_number(input_stats, "weather_wind_rating", 0) >= 70:
        risk_flags.append("high wind volatility")
        confidence -= 6
    if input_stats.get("course_fit_score") is None:
        risk_flags.append("course fit missing")
        confidence -= 5
    if input_stats.get("player_withdrawal_risk") or str(input_stats.get("injury_status") or "").lower() not in {"", "healthy", "none", "clear"}:
        risk_flags.append("withdrawal or injury risk")
        confidence -= 10
    if market_key in {"outright_winner", "first_round_leader", "eagles_prop", "three_ball"}:
        risk_flags.append("volatile golf market")
        confidence -= 5
    if market_key.endswith("_prop") or market_key == "player_prop":
        risk_flags.append("prop fragility")
        confidence -= 3
    if not input_stats.get("book_count") or (_safe_float(input_stats.get("book_count"), 0) or 0) < 4:
        risk_flags.append("book count too low")
        confidence -= 3
    confidence = max(1, min(95, round(confidence, 2)))
    edge = calculate_edge_percent(market_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags = []
    if edge is not None and edge <= 0:
        no_bet_flags.append("negative edge")
    elif edge is not None and edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
    if "withdrawal or injury risk" in risk_flags:
        no_bet_flags.append("risk too high")
    suggested = 0.0 if no_bet_flags else calculate_suggested_stake(
        bankroll=bankroll,
        american_odds=odds_american,
        true_probability=market_probability,
        risk_profile=risk_profile,
        confidence=confidence,
    )
    if suggested <= 0 and not no_bet_flags and edge is not None and edge >= edge_threshold and confidence >= confidence_threshold:
        suggested = round(max(1.0, bankroll * 0.004), 2)
    return {
        "model_status": "active",
        "true_probability": market_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": "high" if risk_flags else "moderate",
        "suggested_stake": suggested,
        "no_bet_flags": no_bet_flags,
        "raw_model_probability": raw_model_probability,
        "calibrated_model_probability": calibrated_model_probability,
        "probability_calibration_applied": bool(market_anchor is not None or sanity_flags),
        "probability_sanity_flags": sanity_flags,
        "probability_cap_reason": probability_cap_reason,
        "market_anchor_probability": market_anchor,
        "player_strength_score": strength,
        "field_size": int(_golf_number(input_stats, "field_size", 120)),
        "outright_win_probability": place_probs["outright_winner"],
        "top_5_probability": place_probs["top_5"],
        "top_10_probability": place_probs["top_10"],
        "top_20_probability": place_probs["top_20"],
        "make_cut_probability": place_probs["make_cut"],
        "miss_cut_probability": place_probs["miss_cut"],
        "risk_flags": risk_flags,
        "input_coverage": 1.0,
        "provider_enrichment": {"provider_status": "not_provided", "provider_enrichment_present": []},
    }


def _basketball_module_calibration(sport: str) -> dict[str, Any]:
    if sport == "basketball_wnba":
        return {
            "league_calibration_applied": "wnba",
            "pace_baseline": 78.5,
            "home_court": 2.1,
            "rating_scale": 8.5,
            "volatility": 11.5,
            "injury_weight": 0.75,
            "travel_weight": 0.45,
            "confidence_base": 74.0,
        }
    if sport == "basketball_ncaab":
        return {
            "league_calibration_applied": "ncaab",
            "pace_baseline": 70.5,
            "home_court": 3.1,
            "rating_scale": 9.5,
            "volatility": 13.5,
            "rank_weight": 0.06,
            "strength_weight": 0.08,
            "conference_weight": 0.045,
            "experience_weight": 0.025,
            "confidence_base": 72.0,
        }
    return {
        "league_calibration_applied": "ncaawb",
        "pace_baseline": 72.0,
        "home_court": 3.4,
        "rating_scale": 8.8,
        "volatility": 14.5,
        "rank_weight": 0.08,
        "strength_weight": 0.09,
        "conference_weight": 0.05,
        "experience_weight": 0.02,
        "top_team_weight": 0.7,
        "confidence_base": 71.0,
    }


def _estimate_basketball_module_model(
    *,
    sport: str,
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    missing = _basketball_module_full_inputs_missing(sport, input_stats, payload) + _basketball_module_market_specific_missing(market, input_stats, payload)
    if missing:
        return None
    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None
    if implied_probability is None:
        return None

    calibration = _basketball_module_calibration(sport)
    home_off = _safe_float(input_stats.get("home_offensive_rating"), 100) or 100
    home_def = _safe_float(input_stats.get("home_defensive_rating"), 100) or 100
    away_off = _safe_float(input_stats.get("away_offensive_rating"), 100) or 100
    away_def = _safe_float(input_stats.get("away_defensive_rating"), 100) or 100
    home_pace = _safe_float(input_stats.get("home_pace"), calibration["pace_baseline"]) or calibration["pace_baseline"]
    away_pace = _safe_float(input_stats.get("away_pace"), calibration["pace_baseline"]) or calibration["pace_baseline"]
    possessions = max(58, min(88, (home_pace + away_pace) / 2))
    home_quality = (home_off - away_def) * 0.42 + (_safe_float(input_stats.get("home_effective_fg_pct"), 50) - _safe_float(input_stats.get("away_effective_fg_pct"), 50)) * 0.11
    away_quality = (away_off - home_def) * 0.42 + (_safe_float(input_stats.get("away_effective_fg_pct"), 50) - _safe_float(input_stats.get("home_effective_fg_pct"), 50)) * 0.11
    margin = home_quality - away_quality + calibration["home_court"]
    margin += (_safe_float(input_stats.get("home_rebound_rate"), 50) - _safe_float(input_stats.get("away_rebound_rate"), 50)) * 0.04
    margin -= (_safe_float(input_stats.get("home_turnover_rate"), 15) - _safe_float(input_stats.get("away_turnover_rate"), 15)) * 0.09
    margin += (_safe_float(input_stats.get("home_free_throw_rate"), 25) - _safe_float(input_stats.get("away_free_throw_rate"), 25)) * 0.035
    margin += (_safe_float(input_stats.get("home_rest_days"), 2) - _safe_float(input_stats.get("away_rest_days"), 2)) * 0.25
    margin -= (_safe_float(input_stats.get("home_travel_fatigue"), 0) - _safe_float(input_stats.get("away_travel_fatigue"), 0)) * calibration.get("travel_weight", 0.35)
    if sport == "basketball_wnba":
        margin += (_safe_float(input_stats.get("home_injury_adjustment"), 0) - _safe_float(input_stats.get("away_injury_adjustment"), 0)) * calibration["injury_weight"]
    else:
        rank_edge = (_safe_float(input_stats.get("away_rank"), 60) - _safe_float(input_stats.get("home_rank"), 60)) * calibration["rank_weight"]
        strength_edge = (_safe_float(input_stats.get("home_strength_rating"), 0) - _safe_float(input_stats.get("away_strength_rating"), 0)) * calibration["strength_weight"]
        conference_edge = (_safe_float(input_stats.get("home_conference_strength"), 0) - _safe_float(input_stats.get("away_conference_strength"), 0)) * calibration["conference_weight"]
        experience_edge = (_safe_float(input_stats.get("home_experience_rating"), 0) - _safe_float(input_stats.get("away_experience_rating"), 0)) * calibration["experience_weight"]
        shooting_edge = (_safe_float(input_stats.get("home_three_point_rate"), 35) - _safe_float(input_stats.get("away_three_point_rate"), 35)) * 0.025
        ft_edge = (_safe_float(input_stats.get("home_free_throw_pct"), 72) - _safe_float(input_stats.get("away_free_throw_pct"), 72)) * 0.025
        margin += rank_edge + strength_edge + conference_edge + experience_edge + shooting_edge + ft_edge
        if sport == "basketball_ncaawb" and (_safe_float(input_stats.get("home_rank"), 99) or 99) <= 5:
            margin += calibration.get("top_team_weight", 0)
    if input_stats.get("neutral_court") or input_stats.get("tournament_game"):
        margin -= calibration["home_court"] * 0.65

    selected_home = str(payload.get("selection") or input_stats.get("selection") or "").strip().lower() == str(input_stats.get("home_team") or "").strip().lower()
    selected_margin = margin if selected_home else -margin
    raw_probability = 1 / (1 + math.exp(-selected_margin / calibration["rating_scale"]))
    no_vig_anchor = _safe_float(input_stats.get("no_vig_market_probability"))
    if no_vig_anchor is not None and no_vig_anchor > 1:
        no_vig_anchor = no_vig_anchor / 100
    market_anchor = max(0.01, min(0.99, no_vig_anchor)) if no_vig_anchor is not None else None
    calibrated_probability = raw_probability * 0.90 + market_anchor * 0.10 if market_anchor is not None else raw_probability
    probability = max(0.08, min(0.92, calibrated_probability))
    projected_total = max(98, min(185, possessions * ((home_off + away_off) / 200) * 2.0 + 18))
    market_key = _normal_market_key(market)
    line = _safe_float(payload.get("line"), _safe_float(input_stats.get("line")))
    total_line = _safe_float(payload.get("total_line"), _safe_float(input_stats.get("total_line")))
    selection_text = str(payload.get("selection") or input_stats.get("selection") or "").lower()
    if market_key in {"spread", "first_half_spread", "first_quarter_spread", "alt_spread"}:
        spread_line = line if line is not None else 0
        scale = calibration["volatility"] * (0.55 if "first_half" in market_key else 0.32 if "first_quarter" in market_key else 1.0)
        probability = _normal_cdf(selected_margin + spread_line, mean=0, stddev=max(4.0, scale))
    elif market_key in {"total", "first_half_total", "first_quarter_total", "alt_total"}:
        target_total = total_line if total_line is not None else projected_total
        projected = projected_total * (0.49 if "first_half" in market_key else 0.245 if "first_quarter" in market_key else 1.0)
        over_prob = 1 - _normal_cdf(target_total, mean=projected, stddev=max(5.0, calibration["volatility"]))
        probability = over_prob if "over" in selection_text else 1 - over_prob
    elif market_key in {"team_total", "alt_team_total"}:
        target_total = total_line if total_line is not None else projected_total / 2
        projected_team = projected_total / 2 + selected_margin / 2
        over_prob = 1 - _normal_cdf(target_total, mean=projected_team, stddev=max(4.0, calibration["volatility"] * 0.72))
        probability = over_prob if "over" in selection_text else 1 - over_prob
    elif market_key in BASKETBALL_MODULE_PROP_MARKETS:
        prop_map = {
            "player_points": "player_points_projection",
            "player_rebounds": "player_rebounds_projection",
            "player_assists": "player_assists_projection",
            "player_pra": "player_pra_projection",
            "player_threes": "player_threes_projection",
            "player_steals": "player_steals_projection",
            "player_blocks": "player_blocks_projection",
            "player_turnovers": "player_turnovers_projection",
        }
        if market_key == "double_double":
            probability = max(0.05, min(0.72, (_safe_float(input_stats.get("player_rebounds_projection"), 6) or 6) / 16))
        else:
            projection = _safe_float(input_stats.get(prop_map.get(market_key, "player_points_projection")), 10) or 10
            prop_line = line if line is not None else projection
            stddev = max(1.8, projection * 0.22)
            over_prob = 1 - _normal_cdf(prop_line, mean=projection, stddev=stddev)
            probability = over_prob if "over" in selection_text or selection_text == str(input_stats.get("player") or "").lower() else 1 - over_prob
    probability = max(0.02, min(0.94, probability))
    confidence = calibration["confidence_base"]
    risk_flags = []
    if _safe_float(input_stats.get("book_count"), 0) < 4:
        confidence -= 3
        risk_flags.append("book count too low")
    if market_key in BASKETBALL_MODULE_PROP_MARKETS:
        confidence -= 3
        if _safe_float(input_stats.get("player_minutes_projection"), 0) < 18:
            confidence -= 10
            risk_flags.append("player minutes uncertainty")
    if input_stats.get("provider_status") == "error":
        risk_flags.append("provider failure ignored")
    if input_stats.get("tempo_volatility") or input_stats.get("blowout_risk"):
        confidence -= 4
        risk_flags.append("college variance")
    confidence = max(1, min(95, round(confidence, 2)))
    edge = calculate_edge_percent(probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags = []
    if edge is not None and edge <= 0:
        no_bet_flags.append("negative edge")
    elif edge is not None and edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
    suggested = 0 if no_bet_flags else calculate_suggested_stake(
        bankroll=bankroll,
        american_odds=odds_american,
        true_probability=probability,
        risk_profile=risk_profile,
        confidence=confidence,
    )
    return {
        "model_status": "active",
        "true_probability": probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": "moderate" if not risk_flags else "high",
        "suggested_stake": suggested,
        "no_bet_flags": no_bet_flags,
        "raw_model_probability": raw_probability,
        "calibrated_model_probability": calibrated_probability,
        "probability_calibration_applied": bool(market_anchor is not None),
        "probability_sanity_flags": ["basketball module probability cap applied"] if probability != calibrated_probability else [],
        "probability_cap_reason": calibration["league_calibration_applied"],
        "market_anchor_probability": market_anchor,
        "league_calibration_applied": calibration["league_calibration_applied"],
        "projected_margin": round(margin, 2),
        "projected_total": round(projected_total, 2),
        "projected_team_points": round(projected_total / 2 + selected_margin / 2, 2),
        "projected_opponent_points": round(projected_total / 2 - selected_margin / 2, 2),
        "risk_flags": risk_flags,
        "input_coverage": 1.0,
        "provider_enrichment": {"provider_status": "not_provided", "provider_enrichment_present": []},
    }


def _calibrate_nfl_probability(
    *,
    raw_probability: float,
    market_anchor_probability: float,
    market_anchor_is_no_vig: bool,
    projected_margin: float,
    input_confidence_hint: float,
) -> dict[str, Any]:
    flags: list[str] = []
    if raw_probability >= 0.90 or raw_probability <= 0.10:
        flags.append("raw probability extreme")

    abs_margin = abs(projected_margin)
    high_quality_extreme = abs_margin >= 14 and input_confidence_hint >= 80
    if (raw_probability >= 0.90 or raw_probability <= 0.10) and not high_quality_extreme:
        if market_anchor_is_no_vig:
            calibrated = (raw_probability * 0.10) + (market_anchor_probability * 0.90)
        else:
            model_floor = 0.58 if raw_probability >= 0.90 else 0.42
            calibrated = (model_floor * 0.95) + (market_anchor_probability * 0.05)
    else:
        anchor_weight = 0.25 if market_anchor_is_no_vig else 0.05
        calibrated = (raw_probability * (1 - anchor_weight)) + (market_anchor_probability * anchor_weight)
    if abs(calibrated - raw_probability) >= 0.025:
        flags.append("probability calibration applied")

    if high_quality_extreme:
        lower_cap, upper_cap = 0.08, 0.92
    elif abs_margin >= 10:
        lower_cap, upper_cap = 0.15, 0.85
    elif abs_margin >= 7:
        lower_cap, upper_cap = 0.22, 0.78
    elif abs_margin >= 4:
        lower_cap, upper_cap = 0.30, 0.70
    else:
        lower_cap, upper_cap = 0.38, 0.62

    final_probability = max(lower_cap, min(upper_cap, calibrated))
    if final_probability != calibrated:
        flags.append("probability capped by projected margin")
        flags.append("probability calibration applied")

    return {
        "raw_model_probability": raw_probability,
        "calibrated_model_probability": calibrated,
        "final_probability": final_probability,
        "market_anchor_probability": market_anchor_probability,
        "probability_calibration_applied": bool(flags),
        "probability_sanity_flags": list(dict.fromkeys(flags)),
        "probability_cap_reason": (
            "extreme projected margin with high input confidence"
            if high_quality_extreme
            else f"projected margin {round(projected_margin, 2)} points"
        ),
    }


def _estimate_soccer_goal_model(
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    core_missing = _soccer_full_inputs_missing(input_stats, payload)
    market_missing = _soccer_market_specific_missing(market, input_stats, payload)
    if core_missing or market_missing:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    optional_present = [field for field in SOCCER_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    provider_present = [field for field in SOCCER_PROVIDER_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    officiating_present = _official_inputs_present(input_stats, SOCCER_OFFICIATING_INPUTS)
    social_present = [field for field in SOCCER_SOCIAL_CROWD_INPUTS if input_stats.get(field) is not None]
    live_present = [field for field in SOCCER_LIVE_BETTING_INPUTS if input_stats.get(field) is not None]

    team_lambda = (
        number("team_expected_goals") * 0.35
        + ((number("team_xg_for") + number("opponent_xg_against")) / 2) * 0.35
        + ((number("team_goals_for_per_match") + number("opponent_goals_against_per_match")) / 2) * 0.15
        + ((number("team_shots_on_target_per_match") + number("opponent_shots_on_target_allowed_per_match")) / 9) * 0.15
    )
    opponent_lambda = (
        number("opponent_expected_goals") * 0.35
        + ((number("opponent_xg_for") + number("team_xg_against")) / 2) * 0.35
        + ((number("opponent_goals_for_per_match") + number("team_goals_against_per_match")) / 2) * 0.15
        + ((number("opponent_shots_on_target_per_match") + number("team_shots_on_target_allowed_per_match")) / 9) * 0.15
    )
    time_decay_applied = False
    if input_stats.get("team_recent_xg_for_5") is not None and input_stats.get("opponent_recent_xg_for_5") is not None:
        team_lambda = team_lambda * 0.75 + number("team_recent_xg_for_5") * 0.25
        opponent_lambda = opponent_lambda * 0.75 + number("opponent_recent_xg_for_5") * 0.25
        time_decay_applied = True
    if input_stats.get("team_home_xg_for") is not None and str(input_stats.get("home_away") or "").lower() == "home":
        team_lambda = team_lambda * 0.85 + number("team_home_xg_for") * 0.15
    if input_stats.get("opponent_away_xg_for") is not None:
        opponent_lambda = opponent_lambda * 0.85 + number("opponent_away_xg_for") * 0.15
    team_lambda += (number("team_big_chances_per_match") - number("opponent_big_chances_allowed_per_match")) * 0.035
    opponent_lambda += (number("opponent_big_chances_per_match") - number("team_big_chances_allowed_per_match")) * 0.035
    possession_edge = (number("team_possession_percent") - number("opponent_possession_percent")) / 100
    team_lambda += max(-0.08, min(0.08, possession_edge * 0.18))
    opponent_lambda -= max(-0.08, min(0.08, possession_edge * 0.12))
    rest_edge = number("team_rest_days") - number("opponent_rest_days")
    team_lambda += max(-0.08, min(0.08, rest_edge * 0.025))
    opponent_lambda -= max(-0.06, min(0.06, rest_edge * 0.015))

    injury_status = str(input_stats.get("injury_report_status") or "").lower()
    lineup_status = str(input_stats.get("lineup_status") or "").lower()
    if "attacker" in injury_status or "forward" in injury_status:
        team_lambda -= 0.18
    if "defender" in injury_status:
        opponent_lambda += 0.15
    if "goalkeeper" in injury_status or "keeper" in injury_status:
        opponent_lambda += 0.20
    if lineup_status not in {"confirmed", "posted", "official"}:
        team_lambda -= 0.08
        opponent_lambda -= 0.03
    if str(input_stats.get("weather_severity") or "").lower() in {"severe", "high", "wind", "storm"}:
        team_lambda -= 0.08
        opponent_lambda -= 0.08
    if officiating_present:
        team_lambda += (number("referee_penalty_rate", 0.10) - 0.10) * 0.25
        opponent_lambda += (number("referee_penalty_rate", 0.10) - 0.10) * 0.20

    probability_sanity_flags: list[str] = []
    uncapped_team_lambda = team_lambda
    uncapped_opponent_lambda = opponent_lambda
    team_lambda = max(0.20, min(3.8, team_lambda))
    opponent_lambda = max(0.20, min(3.8, opponent_lambda))
    if team_lambda != uncapped_team_lambda or opponent_lambda != uncapped_opponent_lambda:
        probability_sanity_flags.append("lambda capped")

    rho = _safe_float(input_stats.get("dixon_coles_rho"), -0.08)
    score_matrix = build_soccer_score_matrix(team_lambda, opponent_lambda)
    score_matrix = apply_dixon_coles_adjustment(score_matrix, team_lambda, opponent_lambda, rho if rho is not None else -0.08)
    shared_intensity = _safe_float(input_stats.get("shared_intensity"))
    if shared_intensity is None:
        goal_correlation = _safe_float(input_stats.get("goal_correlation"), 0.05) or 0.05
        shared_intensity = max(0.02, min(0.10, goal_correlation))
    score_matrix = apply_bivariate_poisson_adjustment(score_matrix, shared_intensity)
    first_half_lambdas = estimate_first_half_lambdas(team_lambda, opponent_lambda, _safe_float(input_stats.get("first_half_goal_share")))
    first_half_matrix = apply_bivariate_poisson_adjustment(
        apply_dixon_coles_adjustment(build_soccer_score_matrix(*first_half_lambdas), *first_half_lambdas, rho if rho is not None else -0.08),
        min(0.08, shared_intensity),
    )

    selection = payload.get("selection") or input_stats.get("selection")
    team = input_stats.get("team")
    opponent = input_stats.get("opponent")
    if market_key in {"moneyline", "three_way_moneyline", "home_draw_away"}:
        if market_key == "moneyline" and input_stats.get("two_way_market") is True:
            raw_model_probability = estimate_draw_no_bet_probability(score_matrix, selection, team, opponent)
        elif market_key == "moneyline" and input_stats.get("two_way_market") is None:
            raw_model_probability = estimate_three_way_probability(score_matrix, selection, team, opponent)
        else:
            raw_model_probability = estimate_three_way_probability(score_matrix, selection, team, opponent)
    elif market_key == "draw_no_bet":
        raw_model_probability = estimate_draw_no_bet_probability(score_matrix, selection, team, opponent)
    elif market_key == "double_chance":
        raw_model_probability = estimate_double_chance_probability(score_matrix, selection, team, opponent)
    elif market_key in {"asian_handicap", "spread", "alt_line"}:
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        raw_model_probability = estimate_handicap_probability(score_matrix, line)
    elif market_key in {"total", "second_half_total"}:
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        raw_model_probability = estimate_total_probability_from_score_matrix(score_matrix, total_line, selection)
    elif market_key == "team_total":
        team_total_line = _safe_float(input_stats.get("team_total_line") if input_stats.get("team_total_line") is not None else payload.get("team_total_line"), 0) or 0
        raw_model_probability = estimate_team_total_probability_from_score_matrix(score_matrix, team_total_line, selection)
    elif market_key == "both_teams_to_score":
        raw_model_probability = estimate_btts_probability(score_matrix, selection)
    elif market_key == "correct_score":
        raw_model_probability = estimate_correct_score_probability(score_matrix, input_stats.get("correct_score_selection") or payload.get("correct_score_selection"))
    elif market_key == "first_half_moneyline":
        raw_model_probability = estimate_three_way_probability(first_half_matrix, selection, team, opponent)
    elif market_key == "first_half_total":
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        raw_model_probability = estimate_total_probability_from_score_matrix(first_half_matrix, total_line, selection)
    elif market_key == "first_half_team_total":
        team_total_line = _safe_float(input_stats.get("team_total_line") if input_stats.get("team_total_line") is not None else payload.get("team_total_line"), 0) or 0
        raw_model_probability = estimate_team_total_probability_from_score_matrix(first_half_matrix, team_total_line, selection)
    elif market_key in {"corners", "team_corners"}:
        line_key = "team_corner_line" if market_key == "team_corners" else "corner_line"
        projection = number("team_corner_rate", 5.0) if market_key == "team_corners" else number("team_corner_rate", 5.0) + number("opponent_corner_rate", 4.8)
        line = _safe_float(input_stats.get(line_key) if input_stats.get(line_key) is not None else payload.get(line_key), 0) or 0
        raw_model_probability = _logistic_probability(projection - line, 2.0)
    elif market_key in {"cards", "team_cards"}:
        line_key = "team_card_line" if market_key == "team_cards" else "card_line"
        projection = number("team_cards_per_match", 2.0) if market_key == "team_cards" else number("team_cards_per_match", 2.0) + number("opponent_cards_per_match", 2.0)
        if officiating_present:
            projection = projection * 0.85 + number("referee_cards_per_match", projection) * 0.15
        line = _safe_float(input_stats.get(line_key) if input_stats.get(line_key) is not None else payload.get(line_key), 0) or 0
        raw_model_probability = _logistic_probability(projection - line, 1.4)
    elif market_key == "anytime_goal_scorer":
        goal_projection = number("player_goal_projection")
        minutes = max(1, number("player_minutes_projection", 75))
        raw_model_probability = max(0.03, min(0.75, 1 - math.exp(-goal_projection * minutes / 90)))
    elif market_key == "first_goal_scorer":
        raw_model_probability = max(0.03, min(0.35, number("player_first_goal_projection")))
    elif market_key == "player_prop":
        projection = number("player_projection")
        prop_line = number("prop_line")
        raw_model_probability = _logistic_probability(projection - prop_line, max(0.75, abs(prop_line) * 0.22))
    else:
        raw_model_probability = estimate_three_way_probability(score_matrix, selection, team, opponent)

    implied_probability = american_odds_to_implied_probability(odds_american)
    market_probability = _safe_probability(input_stats.get("no_vig_market_probability"))
    market_anchor_probability = market_probability if market_probability is not None else implied_probability if implied_probability is not None else 0.5
    projected_goal_differential = team_lambda - opponent_lambda

    confidence_base = 68
    confidence_hint = calculate_confidence(confidence_base, min(7, len(optional_present) * 0.15), min(4, len(provider_present) * 0.5))
    calibration = calibrate_soccer_probability(
        raw_probability=raw_model_probability,
        market_anchor_probability=market_anchor_probability,
        market_anchor_is_no_vig=market_probability is not None,
        projected_goal_differential=projected_goal_differential,
        market_key=market_key,
        input_confidence_hint=confidence_hint,
    )
    if probability_sanity_flags:
        calibration["probability_sanity_flags"] = list(dict.fromkeys(calibration["probability_sanity_flags"] + probability_sanity_flags))
        calibration["probability_calibration_applied"] = True
    true_probability = calibration["final_probability"]

    confidence_adjustments: list[float] = [min(7, len(optional_present) * 0.15), min(4, len(provider_present) * 0.5)]
    if lineup_status not in {"confirmed", "posted", "official"}:
        confidence_adjustments.append(-7)
    if "goalkeeper" in injury_status or "keeper" in injury_status:
        confidence_adjustments.append(-7)
    if abs(rest_edge) >= 3:
        confidence_adjustments.append(-3)
    if str(input_stats.get("weather_severity") or "").lower() in {"severe", "high", "wind", "storm"}:
        confidence_adjustments.append(-5)
    if input_stats.get("best_available_odds") is None:
        confidence_adjustments.append(-3)
    book_count = _safe_float(input_stats.get("book_count"))
    if book_count is not None and book_count < 5:
        confidence_adjustments.append(-4)
    current_odds = _safe_float(input_stats.get("current_odds"))
    consensus_odds = _safe_float(input_stats.get("consensus_odds"))
    risk = "medium"
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 25:
        risk = "high"
        confidence_adjustments.append(-3)
    if officiating_present and number("official_sample_size") and number("official_sample_size") < 20:
        confidence_adjustments.append(-2)
    if market_key in {"correct_score", "first_goal_scorer"}:
        risk = "high"
        confidence_adjustments.append(-8)
    if market_key in {"player_prop", "anytime_goal_scorer", "first_goal_scorer"}:
        if str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "starting", "active"}:
            confidence_adjustments.append(-12)
        if number("player_minutes_projection") < 60:
            confidence_adjustments.append(-6)
    if calibration["probability_sanity_flags"]:
        confidence_adjustments.append(-min(6, len(calibration["probability_sanity_flags"]) * 2))
    confidence = calculate_confidence(confidence_base, *confidence_adjustments)

    edge = calculate_edge_percent(true_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags: list[str] = []
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
        risk = "high"
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
        risk = "high"
    if lineup_status not in {"confirmed", "posted", "official"}:
        no_bet_flags.append("lineup not confirmed")
    if market_key in {"player_prop", "anytime_goal_scorer", "first_goal_scorer"} and str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "starting", "active"}:
        no_bet_flags.append("player starting status unconfirmed")
    if market_key in {"correct_score", "first_goal_scorer"} and edge is not None and edge < 8:
        no_bet_flags.append("high variance market")
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 35:
        no_bet_flags.append("market disagreement too high")

    suggested = 0.0
    if not no_bet_flags:
        suggested = calculate_suggested_stake(
            bankroll=bankroll,
            american_odds=odds_american,
            true_probability=true_probability,
            risk_profile=risk_profile,
            confidence=confidence,
        )
        risk = "low" if edge is not None and edge >= 5 else risk

    draw_probability = sum(score_matrix[i][i] for i in range(len(score_matrix)))
    btts_probability = estimate_btts_probability(score_matrix, "yes")
    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "raw_model_probability": calibration["raw_model_probability"],
        "calibrated_model_probability": calibration["calibrated_model_probability"],
        "probability_calibration_applied": calibration["probability_calibration_applied"],
        "probability_sanity_flags": calibration["probability_sanity_flags"],
        "probability_cap_reason": calibration["probability_cap_reason"],
        "market_anchor_probability": calibration["market_anchor_probability"],
        "team_lambda": round(team_lambda, 3),
        "opponent_lambda": round(opponent_lambda, 3),
        "projected_team_goals": round(team_lambda, 3),
        "projected_opponent_goals": round(opponent_lambda, 3),
        "projected_total_goals": round(team_lambda + opponent_lambda, 3),
        "projected_goal_differential": round(projected_goal_differential, 3),
        "draw_probability": draw_probability,
        "btts_probability": btts_probability,
        "dixon_coles_adjustment_applied": True,
        "bivariate_poisson_adjustment_applied": shared_intensity > 0,
        "time_decay_applied": time_decay_applied,
        "soccer_input_contract": deepcopy(SOCCER_INPUT_CONTRACT),
        "input_coverage": {
            "required_core_present": list(SOCCER_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": SOCCER_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, []),
            "optional_enrichment_present": optional_present,
            "optional_enrichment_missing": [field for field in SOCCER_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
            "provider_enrichment_present": provider_present,
            "officiating_present": officiating_present,
            "referee_present": officiating_present,
            "social_crowd_present": social_present,
            "live_betting_present": live_present,
        },
        "provider_enrichment": {
            "provider_enrichment_present": provider_present,
            "provider_status": "available" if provider_present else "not_provided",
        },
        "no_bet_flags": no_bet_flags,
    }


def _estimate_nhl_goal_model(
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    core_missing = _nhl_full_inputs_missing(input_stats, payload)
    market_missing = _nhl_market_specific_missing(market, input_stats, payload)
    if core_missing or market_missing:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    def truthy(key: str) -> bool:
        return _truthy_available(input_stats.get(key))

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    optional_present = [field for field in NHL_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    provider_present = [field for field in NHL_PROVIDER_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    officiating_present = _official_inputs_present(input_stats, NHL_OFFICIATING_INPUTS)
    social_present = [field for field in NHL_SOCIAL_CROWD_INPUTS if input_stats.get(field) is not None]
    live_present = [field for field in NHL_LIVE_BETTING_INPUTS if input_stats.get(field) is not None]

    team_lambda = (
        number("team_projected_goals") * 0.30
        + ((number("team_xg_for_per_game") + number("opponent_xg_against_per_game")) / 2) * 0.35
        + ((number("team_goals_for_per_game") + number("opponent_goals_against_per_game")) / 2) * 0.15
        + ((number("team_high_danger_chances_for_per_game") + number("opponent_high_danger_chances_against_per_game")) / 18) * 0.12
        + ((number("team_shots_for_per_game") + number("opponent_shots_against_per_game")) / 62) * 0.08
    )
    opponent_lambda = (
        number("opponent_projected_goals") * 0.30
        + ((number("opponent_xg_for_per_game") + number("team_xg_against_per_game")) / 2) * 0.35
        + ((number("opponent_goals_for_per_game") + number("team_goals_against_per_game")) / 2) * 0.15
        + ((number("opponent_high_danger_chances_for_per_game") + number("team_high_danger_chances_against_per_game")) / 18) * 0.12
        + ((number("opponent_shots_for_per_game") + number("team_shots_against_per_game")) / 62) * 0.08
    )

    time_decay_applied = False
    if input_stats.get("team_recent_xg_for_5") is not None and input_stats.get("opponent_recent_xg_for_5") is not None:
        team_lambda = team_lambda * 0.75 + number("team_recent_xg_for_5") * 0.25
        opponent_lambda = opponent_lambda * 0.75 + number("opponent_recent_xg_for_5") * 0.25
        time_decay_applied = True
    if input_stats.get("team_home_xg_for") is not None and str(input_stats.get("home_away") or "").lower() == "home":
        team_lambda = team_lambda * 0.88 + number("team_home_xg_for") * 0.12
    if input_stats.get("opponent_away_xg_for") is not None:
        opponent_lambda = opponent_lambda * 0.88 + number("opponent_away_xg_for") * 0.12

    goalie_risk_flags: list[str] = []
    goalie_adjustment_applied = True
    team_goalie_confirmed = truthy("team_goalie_confirmed")
    opponent_goalie_confirmed = truthy("opponent_goalie_confirmed")
    if not team_goalie_confirmed:
        goalie_risk_flags.append("team goalie unconfirmed")
        opponent_lambda += 0.12
    if not opponent_goalie_confirmed:
        goalie_risk_flags.append("opponent goalie unconfirmed")
        team_lambda += 0.12
    if _truthy_available(input_stats.get("backup_goalie_expected")):
        goalie_risk_flags.append("backup goalie risk")
        opponent_lambda += 0.18
    goalie_fatigue = number("goalie_fatigue_index")
    if goalie_fatigue >= 0.70:
        goalie_risk_flags.append("goalie fatigue")
        opponent_lambda += 0.08
    team_goalie_gsaax = number("team_starting_goalie_gsaax")
    opponent_goalie_gsaax = number("opponent_starting_goalie_gsaax")
    opponent_lambda += max(-0.18, min(0.18, -team_goalie_gsaax * 0.015))
    team_lambda += max(-0.18, min(0.18, -opponent_goalie_gsaax * 0.015))
    team_save = number("team_starting_goalie_save_percent", 0.910)
    opponent_save = number("opponent_starting_goalie_save_percent", 0.910)
    opponent_lambda += max(-0.12, min(0.12, (0.910 - team_save) * 5.0))
    team_lambda += max(-0.12, min(0.12, (0.910 - opponent_save) * 5.0))

    special_teams_adjustment_applied = True
    team_power_play_edge = (number("team_power_play_percent", 21) - (100 - number("opponent_penalty_kill_percent", 79))) / 100
    opponent_power_play_edge = (number("opponent_power_play_percent", 21) - (100 - number("team_penalty_kill_percent", 79))) / 100
    team_lambda += max(-0.12, min(0.12, team_power_play_edge * 0.8))
    opponent_lambda += max(-0.12, min(0.12, opponent_power_play_edge * 0.8))
    team_lambda += max(-0.08, min(0.08, (number("team_penalties_drawn_per_game", 3) - number("opponent_penalties_taken_per_game", 3)) * 0.025))
    opponent_lambda += max(-0.08, min(0.08, (number("opponent_penalties_drawn_per_game", 3) - number("team_penalties_taken_per_game", 3)) * 0.025))
    if officiating_present:
        pp_rate = number("referee_power_play_rate", 3.0)
        team_lambda += max(-0.08, min(0.08, (pp_rate - 3.0) * 0.025))
        opponent_lambda += max(-0.08, min(0.08, (pp_rate - 3.0) * 0.025))

    rest_edge = number("team_rest_days") - number("opponent_rest_days")
    team_lambda += max(-0.08, min(0.08, rest_edge * 0.025))
    opponent_lambda -= max(-0.06, min(0.06, rest_edge * 0.018))
    if _truthy_available(input_stats.get("team_back_to_back")):
        team_lambda -= 0.08
        goalie_risk_flags.append("team back to back fatigue")
    if _truthy_available(input_stats.get("opponent_back_to_back")):
        opponent_lambda -= 0.08
    injury_status = str(input_stats.get("injury_report_status") or "").lower()
    lineup_status = str(input_stats.get("lineup_status") or "").lower()
    if "scorer" in injury_status or "forward" in injury_status:
        team_lambda -= 0.15
    if "defense" in injury_status or "defender" in injury_status:
        opponent_lambda += 0.12
    if lineup_status not in {"confirmed", "posted", "official"}:
        team_lambda -= 0.06
        opponent_lambda -= 0.04

    probability_sanity_flags: list[str] = []
    uncapped_team_lambda = team_lambda
    uncapped_opponent_lambda = opponent_lambda
    team_lambda = max(0.40, min(5.6, team_lambda))
    opponent_lambda = max(0.40, min(5.6, opponent_lambda))
    if team_lambda != uncapped_team_lambda or opponent_lambda != uncapped_opponent_lambda:
        probability_sanity_flags.append("lambda capped")

    shared_intensity = _safe_float(input_stats.get("shared_intensity"))
    if shared_intensity is None:
        tempo = (number("team_shots_for_per_game") + number("opponent_shots_for_per_game")) / 64
        goalie_volatility = min(0.08, abs(team_save - opponent_save) * 0.8 + abs(team_goalie_gsaax - opponent_goalie_gsaax) * 0.006)
        shared_intensity = max(0.02, min(0.10, 0.035 + (tempo - 1.0) * 0.04 + goalie_volatility))
    score_matrix = apply_bivariate_hockey_adjustment(build_nhl_score_matrix(team_lambda, opponent_lambda), shared_intensity)
    first_period_matrix = apply_bivariate_hockey_adjustment(build_nhl_score_matrix(*estimate_nhl_period_lambdas(team_lambda, opponent_lambda, "first", _safe_float(input_stats.get("first_period_goal_share")))), min(0.08, shared_intensity))
    second_period_matrix = apply_bivariate_hockey_adjustment(build_nhl_score_matrix(*estimate_nhl_period_lambdas(team_lambda, opponent_lambda, "second", _safe_float(input_stats.get("second_period_goal_share")))), min(0.08, shared_intensity))
    third_period_matrix = apply_bivariate_hockey_adjustment(build_nhl_score_matrix(*estimate_nhl_period_lambdas(team_lambda, opponent_lambda, "third", _safe_float(input_stats.get("third_period_goal_share")))), min(0.08, shared_intensity))

    selection = payload.get("selection") or input_stats.get("selection")
    team = input_stats.get("team")
    opponent = input_stats.get("opponent")
    shootout_edge = max(-0.06, min(0.06, (team_goalie_gsaax - opponent_goalie_gsaax) * 0.006))
    matrix_for_market = score_matrix
    period_lambda_adjustment_applied = market_key.startswith(("first_period", "second_period", "third_period"))
    if market_key.startswith("first_period"):
        matrix_for_market = first_period_matrix
    elif market_key.startswith("second_period"):
        matrix_for_market = second_period_matrix
    elif market_key.startswith("third_period"):
        matrix_for_market = third_period_matrix

    if market_key == "moneyline":
        raw_model_probability = estimate_nhl_moneyline_probability(score_matrix, selection, team, opponent, shootout_edge)
    elif market_key == "three_way_moneyline":
        raw_model_probability = estimate_nhl_three_way_probability(score_matrix, selection, team, opponent)
    elif market_key == "regulation_moneyline":
        raw_model_probability = estimate_nhl_regulation_moneyline_probability(score_matrix, selection, team, opponent)
    elif market_key == "draw_no_bet":
        raw_model_probability = estimate_nhl_draw_no_bet_probability(score_matrix, selection, team, opponent)
    elif market_key in {"puckline", "spread", "alternate_puckline"}:
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        raw_model_probability = estimate_nhl_puckline_probability(score_matrix, line)
    elif market_key in {"total", "alternate_total", "first_period_total", "second_period_total", "third_period_total"}:
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        raw_model_probability = estimate_nhl_total_probability_from_score_matrix(matrix_for_market, total_line, selection)
    elif market_key in {"team_total", "first_period_team_total"}:
        team_total_line = _safe_float(input_stats.get("team_total_line") if input_stats.get("team_total_line") is not None else payload.get("team_total_line"), 0) or 0
        raw_model_probability = estimate_nhl_team_total_probability_from_score_matrix(matrix_for_market, team_total_line, selection)
    elif market_key in {"first_period_moneyline", "second_period_moneyline", "third_period_moneyline"}:
        raw_model_probability = estimate_nhl_three_way_probability(matrix_for_market, selection, team, opponent)
    elif market_key == "anytime_goal_scorer":
        goal_projection = number("player_goal_projection")
        minutes = max(1, number("player_minutes_projection", 15))
        raw_model_probability = max(0.03, min(0.75, 1 - math.exp(-goal_projection * minutes / 18)))
    elif market_key == "first_goal_scorer":
        raw_model_probability = max(0.03, min(0.32, number("player_first_goal_projection")))
    elif market_key == "player_prop":
        raw_model_probability = estimate_nhl_player_prop_probability(number("player_projection"), number("prop_line"))
    else:
        raw_model_probability = estimate_nhl_moneyline_probability(score_matrix, selection, team, opponent, shootout_edge)

    implied_probability = american_odds_to_implied_probability(odds_american)
    market_probability = _safe_probability(input_stats.get("no_vig_market_probability"))
    market_anchor_probability = market_probability if market_probability is not None else implied_probability if implied_probability is not None else 0.5
    projected_goal_differential = team_lambda - opponent_lambda
    confidence_hint = calculate_confidence(68, min(7, len(optional_present) * 0.15), min(4, len(provider_present) * 0.5))
    goalie_edge_quality = 0.6 if team_goalie_confirmed and opponent_goalie_confirmed and abs(team_goalie_gsaax - opponent_goalie_gsaax) >= 4 else 0.2
    calibration = calibrate_nhl_probability(
        raw_probability=raw_model_probability,
        market_anchor_probability=market_anchor_probability,
        market_anchor_is_no_vig=market_probability is not None,
        projected_goal_differential=projected_goal_differential,
        market_key=market_key,
        input_confidence_hint=confidence_hint,
        goalie_edge_quality=goalie_edge_quality,
    )
    if probability_sanity_flags:
        calibration["probability_sanity_flags"] = list(dict.fromkeys(calibration["probability_sanity_flags"] + probability_sanity_flags))
        calibration["probability_calibration_applied"] = True
    true_probability = calibration["final_probability"]

    confidence_adjustments: list[float] = [min(7, len(optional_present) * 0.15), min(4, len(provider_present) * 0.5)]
    if goalie_risk_flags:
        confidence_adjustments.append(-min(10, len(goalie_risk_flags) * 3))
    if lineup_status not in {"confirmed", "posted", "official"}:
        confidence_adjustments.append(-7)
    if abs(rest_edge) >= 2:
        confidence_adjustments.append(-3)
    if input_stats.get("best_available_odds") is None:
        confidence_adjustments.append(-3)
    book_count = _safe_float(input_stats.get("book_count"))
    if book_count is not None and book_count < 5:
        confidence_adjustments.append(-4)
    current_odds = _safe_float(input_stats.get("current_odds"))
    consensus_odds = _safe_float(input_stats.get("consensus_odds"))
    risk = "medium"
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 25:
        risk = "high"
        confidence_adjustments.append(-3)
    if officiating_present and number("official_sample_size") and number("official_sample_size") < 20:
        confidence_adjustments.append(-2)
    if market_key == "first_goal_scorer":
        risk = "high"
        confidence_adjustments.append(-8)
    if market_key in {"player_prop", "anytime_goal_scorer", "first_goal_scorer"}:
        if str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "starting", "active"}:
            confidence_adjustments.append(-12)
        if number("player_minutes_projection") < 10:
            confidence_adjustments.append(-6)
    if calibration["probability_sanity_flags"]:
        confidence_adjustments.append(-min(6, len(calibration["probability_sanity_flags"]) * 2))
    confidence = calculate_confidence(68, *confidence_adjustments)

    edge = calculate_edge_percent(true_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags: list[str] = []
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
        risk = "high"
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
        risk = "high"
    if lineup_status not in {"confirmed", "posted", "official"}:
        no_bet_flags.append("lineup not confirmed")
    if goalie_risk_flags and market_key not in {"total", "alternate_total"}:
        no_bet_flags.append(goalie_risk_flags[0])
    if market_key in {"player_prop", "anytime_goal_scorer", "first_goal_scorer"} and str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "starting", "active"}:
        no_bet_flags.append("player starting status unconfirmed")
    if market_key == "first_goal_scorer" and edge is not None and edge < 8:
        no_bet_flags.append("high variance market")
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 35:
        no_bet_flags.append("market disagreement too high")

    suggested = 0.0
    if not no_bet_flags:
        suggested = calculate_suggested_stake(
            bankroll=bankroll,
            american_odds=odds_american,
            true_probability=true_probability,
            risk_profile=risk_profile,
            confidence=confidence,
        )
        risk = "low" if edge is not None and edge >= 5 else risk

    regulation_team_win, regulation_draw_probability, regulation_opponent_win = _nhl_matrix_parts(score_matrix)
    overtime_probability = regulation_draw_probability
    shootout_adjustment_probability = overtime_probability * (0.50 + shootout_edge)
    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "raw_model_probability": calibration["raw_model_probability"],
        "calibrated_model_probability": calibration["calibrated_model_probability"],
        "probability_calibration_applied": calibration["probability_calibration_applied"],
        "probability_sanity_flags": calibration["probability_sanity_flags"],
        "probability_cap_reason": calibration["probability_cap_reason"],
        "market_anchor_probability": calibration["market_anchor_probability"],
        "team_lambda": round(team_lambda, 3),
        "opponent_lambda": round(opponent_lambda, 3),
        "projected_team_goals": round(team_lambda, 3),
        "projected_opponent_goals": round(opponent_lambda, 3),
        "projected_total_goals": round(team_lambda + opponent_lambda, 3),
        "projected_goal_differential": round(projected_goal_differential, 3),
        "regulation_draw_probability": regulation_draw_probability,
        "overtime_probability": overtime_probability,
        "shootout_adjustment_probability": shootout_adjustment_probability,
        "bivariate_poisson_adjustment_applied": shared_intensity > 0,
        "goalie_adjustment_applied": goalie_adjustment_applied,
        "goalie_risk_flags": goalie_risk_flags,
        "special_teams_adjustment_applied": special_teams_adjustment_applied,
        "period_lambda_adjustment_applied": period_lambda_adjustment_applied,
        "time_decay_applied": time_decay_applied,
        "nhl_input_contract": deepcopy(NHL_INPUT_CONTRACT),
        "input_coverage": {
            "required_core_present": list(NHL_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": NHL_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, []),
            "optional_enrichment_present": optional_present,
            "optional_enrichment_missing": [field for field in NHL_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
            "provider_enrichment_present": provider_present,
            "officiating_present": officiating_present,
            "referee_present": officiating_present,
            "social_crowd_present": social_present,
            "live_betting_present": live_present,
        },
        "provider_enrichment": {
            "provider_enrichment_present": provider_present,
            "provider_status": "available" if provider_present else "not_provided",
        },
        "no_bet_flags": no_bet_flags,
    }


def _estimate_tennis_markov_model(
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    core_missing = _tennis_full_inputs_missing(input_stats, payload)
    market_missing = _tennis_market_specific_missing(market, input_stats, payload)
    if core_missing or market_missing:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    optional_present = [field for field in TENNIS_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    provider_present = [field for field in TENNIS_PROVIDER_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    officiating_present = _official_inputs_present(input_stats, TENNIS_OFFICIATING_INPUTS)
    social_present = [field for field in TENNIS_SOCIAL_CROWD_INPUTS if input_stats.get(field) is not None]
    live_present = [field for field in TENNIS_LIVE_BETTING_INPUTS if input_stats.get(field) is not None]

    best_of_sets = int(max(3, min(5, number("best_of_sets", 3))))
    strength = estimate_tennis_base_strength(input_stats)
    player_serve_point = estimate_tennis_serve_point_probability(input_stats, "player")
    opponent_serve_point = estimate_tennis_serve_point_probability(input_stats, "opponent")
    player_hold = estimate_tennis_hold_probability_from_points(player_serve_point)
    opponent_hold = estimate_tennis_hold_probability_from_points(opponent_serve_point)
    player_break = max(0.05, min(0.55, 1 - opponent_hold))
    opponent_break = max(0.05, min(0.55, 1 - player_hold))
    serve_edge = player_hold - opponent_hold
    return_edge = player_break - opponent_break
    tiebreak_probability = estimate_tennis_tiebreak_probability(player_serve_point, opponent_serve_point, input_stats)
    set_probability = estimate_tennis_set_probability(player_hold, opponent_hold, tiebreak_probability)
    elo_gap = strength["player_strength_rating"] - strength["opponent_strength_rating"]
    set_probability = max(0.18, min(0.82, set_probability + max(-0.06, min(0.06, elo_gap / 2800))))

    surface_adjustment_applied = True
    fatigue_adjustment_applied = input_stats.get("player_fatigue_index") is not None or input_stats.get("opponent_fatigue_index") is not None
    injury_adjustment_applied = input_stats.get("player_injury_status") is not None or input_stats.get("opponent_injury_status") is not None
    weather_adjustment_applied = input_stats.get("weather_wind_mph") is not None or input_stats.get("weather_temperature") is not None
    fatigue_edge = number("opponent_fatigue_index") - number("player_fatigue_index")
    set_probability += max(-0.035, min(0.035, fatigue_edge * 0.02))
    player_injury_status = str(input_stats.get("player_injury_status") or "").lower()
    opponent_injury_status = str(input_stats.get("opponent_injury_status") or "").lower()
    if any(word in player_injury_status for word in ["questionable", "injured", "limited"]):
        set_probability -= 0.045
    if any(word in opponent_injury_status for word in ["questionable", "injured", "limited"]):
        set_probability += 0.035
    if input_stats.get("player_surface_win_percent") is not None:
        set_probability += max(-0.035, min(0.035, ((number("player_surface_win_percent", 50) - number("opponent_surface_win_percent", 50)) / 100) * 0.08))
    set_probability = max(0.18, min(0.82, set_probability))
    match_probability = estimate_tennis_match_probability(set_probability, best_of_sets)
    first_set_probability = max(0.18, min(0.82, set_probability * 0.92 + 0.04))
    score_distribution = estimate_tennis_set_score_distribution(set_probability, best_of_sets)
    game_distribution = estimate_tennis_game_margin_distribution(match_probability, set_probability, best_of_sets)

    selection = str(payload.get("selection") or input_stats.get("selection") or input_stats.get("player") or "").lower()
    opponent_text = str(input_stats.get("opponent") or "").lower()
    if market_key in {"moneyline", "match_winner"}:
        raw_model_probability = 1 - match_probability if opponent_text and opponent_text in selection else match_probability
    elif market_key == "first_set_moneyline":
        raw_model_probability = 1 - first_set_probability if opponent_text and opponent_text in selection else first_set_probability
    elif market_key == "set_handicap":
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        expected_set_margin = (set_probability - 0.5) * (best_of_sets if best_of_sets >= 5 else 2.2)
        raw_model_probability = tennis_logistic(expected_set_margin + line, 0.85)
    elif market_key == "game_handicap":
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        raw_model_probability = tennis_logistic(game_distribution["mean_margin"] + line, game_distribution["volatility"])
    elif market_key == "total_games":
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        raw_model_probability = estimate_tennis_total_games_probability(total_line, selection, game_distribution)
    elif market_key == "first_set_total_games":
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        raw_model_probability = estimate_tennis_first_set_total_probability(total_line, selection, set_probability)
    elif market_key == "correct_score":
        raw_model_probability = estimate_tennis_correct_score_probability(score_distribution, input_stats.get("correct_score_selection") or payload.get("correct_score_selection"))
    elif market_key in {"player_prop", "aces", "double_faults", "break_points", "service_games_won", "return_games_won"}:
        raw_model_probability = estimate_tennis_player_prop_probability(number("player_projection"), number("prop_line"))
    else:
        raw_model_probability = match_probability

    implied_probability = american_odds_to_implied_probability(odds_american)
    market_probability = _safe_probability(input_stats.get("no_vig_market_probability"))
    market_anchor_probability = market_probability if market_probability is not None else implied_probability if implied_probability is not None else 0.5
    confidence_hint = calculate_confidence(68, min(7, len(optional_present) * 0.15), min(4, len(provider_present) * 0.5))
    calibration = calibrate_tennis_probability(
        raw_probability=raw_model_probability,
        market_anchor_probability=market_anchor_probability,
        market_anchor_is_no_vig=market_probability is not None,
        elo_gap=elo_gap,
        surface_edge=strength["player_surface_edge"],
        market_key=market_key,
        input_confidence_hint=confidence_hint,
    )
    true_probability = calibration["final_probability"]

    confidence_adjustments: list[float] = [min(7, len(optional_present) * 0.15), min(4, len(provider_present) * 0.5)]
    risk = "medium"
    no_bet_flags: list[str] = []
    if any(word in player_injury_status for word in ["questionable", "injured", "limited"]):
        confidence_adjustments.append(-9)
        no_bet_flags.append("injury risk")
    if number("player_retirement_risk") >= 0.25:
        confidence_adjustments.append(-10)
        no_bet_flags.append("retirement risk")
    if number("player_fatigue_index") >= 0.70:
        confidence_adjustments.append(-5)
        no_bet_flags.append("fatigue risk")
    if input_stats.get("best_available_odds") is None:
        confidence_adjustments.append(-3)
    book_count = _safe_float(input_stats.get("book_count"))
    if book_count is not None and book_count < 5:
        confidence_adjustments.append(-4)
    current_odds = _safe_float(input_stats.get("current_odds"))
    consensus_odds = _safe_float(input_stats.get("consensus_odds"))
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 25:
        confidence_adjustments.append(-3)
        risk = "high"
        no_bet_flags.append("market disagreement")
    if weather_adjustment_applied and number("weather_wind_mph") >= 18 and market_key in {"aces", "player_prop", "service_games_won"}:
        confidence_adjustments.append(-5)
        no_bet_flags.append("weather risk for serve props")
    if market_key == "correct_score":
        confidence_adjustments.append(-8)
        risk = "high"
    if market_key in {"player_prop", "aces", "double_faults", "break_points", "service_games_won", "return_games_won"} and str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "active", "starting"}:
        confidence_adjustments.append(-12)
        no_bet_flags.append("player starting status unconfirmed")
    if calibration["probability_sanity_flags"]:
        confidence_adjustments.append(-min(6, len(calibration["probability_sanity_flags"]) * 2))
    confidence = calculate_confidence(68, *confidence_adjustments)
    edge = calculate_edge_percent(true_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
        risk = "high"
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
        risk = "high"
    if market_key == "correct_score" and edge is not None and edge < 8:
        no_bet_flags.append("correct score high variance")

    suggested = 0.0
    if not no_bet_flags:
        suggested = calculate_suggested_stake(
            bankroll=bankroll,
            american_odds=odds_american,
            true_probability=true_probability,
            risk_profile=risk_profile,
            confidence=confidence,
        )
        risk = "low" if edge is not None and edge >= 5 else risk

    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "raw_model_probability": calibration["raw_model_probability"],
        "calibrated_model_probability": calibration["calibrated_model_probability"],
        "probability_calibration_applied": calibration["probability_calibration_applied"],
        "probability_sanity_flags": calibration["probability_sanity_flags"],
        "probability_cap_reason": calibration["probability_cap_reason"],
        "market_anchor_probability": calibration["market_anchor_probability"],
        "player_strength_rating": strength["player_strength_rating"],
        "opponent_strength_rating": strength["opponent_strength_rating"],
        "player_surface_edge": strength["player_surface_edge"],
        "serve_edge": serve_edge,
        "return_edge": return_edge,
        "player_hold_probability": player_hold,
        "opponent_hold_probability": opponent_hold,
        "player_break_probability": player_break,
        "opponent_break_probability": opponent_break,
        "player_set_probability": set_probability,
        "player_match_probability": match_probability,
        "first_set_probability": first_set_probability,
        "tiebreak_probability": tiebreak_probability,
        "markov_model_applied": True,
        "surface_adjustment_applied": surface_adjustment_applied,
        "fatigue_adjustment_applied": fatigue_adjustment_applied,
        "injury_adjustment_applied": injury_adjustment_applied,
        "weather_adjustment_applied": weather_adjustment_applied,
        "tennis_input_contract": deepcopy(TENNIS_INPUT_CONTRACT),
        "input_coverage": {
            "required_core_present": list(TENNIS_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": TENNIS_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, []),
            "optional_enrichment_present": optional_present,
            "optional_enrichment_missing": [field for field in TENNIS_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
            "provider_enrichment_present": provider_present,
            "officiating_present": officiating_present,
            "referee_present": officiating_present,
            "social_crowd_present": social_present,
            "live_betting_present": live_present,
        },
        "provider_enrichment": {
            "provider_enrichment_present": provider_present,
            "provider_status": "available" if provider_present else "not_provided",
        },
        "no_bet_flags": list(dict.fromkeys(no_bet_flags)),
    }


def _estimate_mlb_negative_binomial_model(
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    core_missing = _mlb_full_inputs_missing(input_stats, payload)
    market_missing = _mlb_market_specific_missing(market, input_stats, payload)
    if core_missing or market_missing:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    optional_present = [field for field in MLB_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    provider_present = [field for field in MLB_PROVIDER_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    officiating_present = _official_inputs_present(input_stats, MLB_OFFICIATING_INPUTS)
    social_present = [field for field in MLB_SOCIAL_CROWD_INPUTS if input_stats.get(field) is not None]
    live_present = [field for field in MLB_LIVE_BETTING_INPUTS if input_stats.get(field) is not None]

    team_runs = number("team_projected_runs")
    opponent_runs = number("opponent_projected_runs")
    team_starter_quality = ((4.2 - number("opponent_starting_pitcher_fip", 4.2)) + (4.2 - number("opponent_starting_pitcher_xfip", 4.2))) * 0.10
    opponent_starter_quality = ((4.2 - number("team_starting_pitcher_fip", 4.2)) + (4.2 - number("team_starting_pitcher_xfip", 4.2))) * 0.10
    offense_adjustment = (
        (number("team_woba", 0.320) - number("opponent_woba", 0.320)) * 2.2
        + (number("team_xwoba", 0.320) - number("opponent_xwoba", 0.320)) * 1.8
        + (number("team_wrc_plus", 100) - number("opponent_wrc_plus", 100)) * 0.012
        + (number("team_iso", 0.160) - number("opponent_iso", 0.160)) * 1.2
    )
    bullpen_adjustment = (
        (number("opponent_bullpen_fip", 4.1) - number("team_bullpen_fip", 4.1)) * 0.10
        + (number("opponent_bullpen_era", 4.1) - number("team_bullpen_era", 4.1)) * 0.06
    )
    usage_adjustment = (number("opponent_bullpen_recent_usage") - number("team_bullpen_recent_usage")) * 0.04
    park_adjustment = (number("park_factor_runs", 1.0) - 1.0) * 1.5
    weather_adjustment = 0.0
    roof_status = str(input_stats.get("roof_status") or "").strip().lower()
    if roof_status not in {"closed", "dome"}:
        weather_adjustment += max(-0.35, min(0.35, (number("weather_temperature", 72) - 72) * 0.01))
        wind = number("weather_wind_mph")
        direction = str(input_stats.get("weather_wind_direction") or "").lower()
        if wind >= 12:
            weather_adjustment += 0.25 if "out" in direction else -0.15 if "in" in direction else 0.05
    if str(input_stats.get("lineup_status") or "").strip().lower() not in {"confirmed", "posted", "official"}:
        team_runs -= 0.18
        opponent_runs -= 0.10
    if str(input_stats.get("injury_report_status") or "").strip().lower() not in {"clean", "clear", "healthy", "normal", "available"}:
        team_runs -= 0.12

    team_runs += team_starter_quality + offense_adjustment * 0.55 + bullpen_adjustment * 0.55 + usage_adjustment + park_adjustment + weather_adjustment
    opponent_runs += opponent_starter_quality - offense_adjustment * 0.45 - bullpen_adjustment * 0.45 - usage_adjustment + park_adjustment + weather_adjustment

    if input_stats.get("team_recent_woba_14") is not None and input_stats.get("opponent_recent_woba_14") is not None:
        team_runs += (number("team_recent_woba_14", 0.320) - number("opponent_recent_woba_14", 0.320)) * 1.1
    if input_stats.get("team_vs_pitcher_handedness_woba") is not None:
        team_runs += (number("team_vs_pitcher_handedness_woba", 0.320) - 0.320) * 1.0
    if input_stats.get("opponent_vs_pitcher_handedness_woba") is not None:
        opponent_runs += (number("opponent_vs_pitcher_handedness_woba", 0.320) - 0.320) * 1.0
    team_runs += number("team_defensive_runs_saved") * 0.005 - number("opponent_defensive_runs_saved") * 0.003
    opponent_runs += number("opponent_defensive_runs_saved") * 0.005 - number("team_defensive_runs_saved") * 0.003
    if officiating_present:
        umpire_over = number("umpire_over_rate", 0.5)
        strike_impact = number("umpire_strikeout_rate_impact", 0)
        run_env_adjustment = (umpire_over - 0.5) * 0.30 - strike_impact * 0.10
        team_runs += run_env_adjustment
        opponent_runs += run_env_adjustment

    team_runs = max(1.8, min(8.5, team_runs))
    opponent_runs = max(1.8, min(8.5, opponent_runs))
    if market_key.startswith("first_5"):
        team_starter_ip = max(1.0, min(6.0, number("team_starting_pitcher_innings_projection", 5.2)))
        opponent_starter_ip = max(1.0, min(6.0, number("opponent_starting_pitcher_innings_projection", 5.2)))
        team_runs = max(0.8, min(5.0, team_runs * 0.52 + (6.0 - opponent_starter_ip) * 0.05))
        opponent_runs = max(0.8, min(5.0, opponent_runs * 0.52 + (6.0 - team_starter_ip) * 0.05))

    team_dispersion = number("team_run_dispersion", 8.0)
    opponent_dispersion = number("opponent_run_dispersion", 8.0)
    team_dist = estimate_run_distribution(team_runs, team_dispersion)
    opponent_dist = estimate_run_distribution(opponent_runs, opponent_dispersion)
    selection = payload.get("selection") or input_stats.get("selection")

    if market_key in {"moneyline", "first_5_moneyline"}:
        raw_model_probability = estimate_moneyline_probability_from_runs(team_dist, opponent_dist)
    elif market_key in {"runline", "first_5_runline", "alt_line"}:
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        raw_model_probability = estimate_runline_cover_probability(team_dist, opponent_dist, line)
    elif market_key in {"total", "first_5_total"}:
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        raw_model_probability = estimate_total_probability(team_dist, opponent_dist, total_line, selection)
    elif market_key == "team_total":
        team_total_line = _safe_float(input_stats.get("team_total_line") if input_stats.get("team_total_line") is not None else payload.get("team_total_line"), 0) or 0
        raw_model_probability = estimate_team_total_probability(team_dist, team_total_line, selection)
    elif market_key == "player_prop":
        projection = number("player_projection")
        prop_line = number("prop_line")
        scale = max(0.75, abs(prop_line) * 0.22)
        raw_model_probability = _logistic_probability(projection - prop_line, scale)
    else:
        raw_model_probability = estimate_moneyline_probability_from_runs(team_dist, opponent_dist)

    implied_probability = american_odds_to_implied_probability(odds_american)
    market_probability = _safe_probability(input_stats.get("no_vig_market_probability"))
    market_anchor_probability = market_probability if market_probability is not None else implied_probability if implied_probability is not None else 0.5
    projected_run_differential = team_runs - opponent_runs
    calibration = calibrate_mlb_probability(
        raw_probability=raw_model_probability,
        market_anchor_probability=market_anchor_probability,
        market_anchor_is_no_vig=market_probability is not None,
        projected_run_differential=projected_run_differential,
        input_confidence_hint=68,
    )
    true_probability = calibration["final_probability"]

    confidence_adjustments: list[float] = [min(8, len(optional_present) * 0.18), min(4, len(provider_present) * 0.5)]
    pitcher_status = str(input_stats.get("team_starting_pitcher_status") or input_stats.get("starting_pitcher_status") or "confirmed").lower()
    lineup_status = str(input_stats.get("lineup_status") or "").lower()
    team_bullpen_rest = str(input_stats.get("team_bullpen_rest_status") or "").lower()
    if pitcher_status in {"scratched", "unknown", "unconfirmed"}:
        confidence_adjustments.append(-20)
    if lineup_status not in {"confirmed", "posted", "official"}:
        confidence_adjustments.append(-6)
    if team_bullpen_rest in {"tired", "thin", "overworked"} or number("team_bullpen_recent_usage") >= 4:
        confidence_adjustments.append(-5)
    if roof_status not in {"closed", "dome"} and number("weather_wind_mph") >= 15:
        confidence_adjustments.append(-4 if market_key in {"total", "first_5_total", "team_total"} else -2)
    book_count = _safe_float(input_stats.get("book_count"))
    if book_count is not None and book_count < 5:
        confidence_adjustments.append(-4)
    if input_stats.get("best_available_odds") is None:
        confidence_adjustments.append(-3)
    current_odds = _safe_float(input_stats.get("current_odds"))
    consensus_odds = _safe_float(input_stats.get("consensus_odds"))
    risk = "medium"
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 25:
        risk = "high"
        confidence_adjustments.append(-3)
    if market_key == "player_prop" and str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "starting", "active"}:
        confidence_adjustments.append(-10)
    if calibration["probability_sanity_flags"]:
        confidence_adjustments.append(-min(8, 2 * len(calibration["probability_sanity_flags"])))
    confidence = calculate_confidence(68, *confidence_adjustments)

    edge = calculate_edge_percent(true_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags: list[str] = []
    if pitcher_status in {"scratched", "unknown", "unconfirmed"}:
        no_bet_flags.append("starting pitcher uncertainty")
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
        risk = "high"
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
        risk = "high"
    if market_key == "player_prop" and str(input_stats.get("player_starting_status") or "").lower() not in {"confirmed", "starting", "active"}:
        no_bet_flags.append("player starting status unconfirmed")
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 35:
        no_bet_flags.append("market disagreement too high")

    suggested = 0.0
    if not no_bet_flags:
        suggested = calculate_suggested_stake(
            bankroll=bankroll,
            american_odds=odds_american,
            true_probability=true_probability,
            risk_profile=risk_profile,
            confidence=confidence,
        )
        risk = "low" if edge is not None and edge >= 5 else risk

    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "raw_model_probability": calibration["raw_model_probability"],
        "calibrated_model_probability": calibration["calibrated_model_probability"],
        "probability_calibration_applied": calibration["probability_calibration_applied"],
        "probability_sanity_flags": calibration["probability_sanity_flags"],
        "probability_cap_reason": calibration["probability_cap_reason"],
        "market_anchor_probability": calibration["market_anchor_probability"],
        "projected_team_runs": round(team_runs, 2),
        "projected_opponent_runs": round(opponent_runs, 2),
        "projected_total_runs": round(team_runs + opponent_runs, 2),
        "projected_run_differential": round(projected_run_differential, 2),
        "mlb_input_contract": deepcopy(MLB_INPUT_CONTRACT),
        "input_coverage": {
            "required_core_present": list(MLB_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": MLB_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, []),
            "optional_enrichment_present": optional_present,
            "optional_enrichment_missing": [field for field in MLB_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
            "provider_enrichment_present": provider_present,
            "officiating_present": officiating_present,
            "umpire_present": officiating_present,
            "referee_present": officiating_present,
            "social_crowd_present": social_present,
            "live_betting_present": live_present,
        },
        "provider_enrichment": {
            "provider_enrichment_present": provider_present,
            "provider_status": "available" if provider_present else "not_provided",
        },
        "no_bet_flags": no_bet_flags,
    }


def _estimate_college_football_model(
    *,
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    missing = _college_football_full_inputs_missing(input_stats, payload) + _college_football_market_specific_missing(market, input_stats, payload)
    if missing:
        return None
    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None
    if implied_probability is None:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    selection_text = str(payload.get("selection") or input_stats.get("selection") or "").strip().lower()
    selected_home = selection_text == str(input_stats.get("home_team") or "").strip().lower()
    selected_away = selection_text == str(input_stats.get("away_team") or "").strip().lower()
    if not selected_home and not selected_away:
        selected_home = str(input_stats.get("team") or "").strip().lower() == str(input_stats.get("home_team") or "").strip().lower()

    home_drive = (
        (number("home_offensive_epa_per_play") - number("away_defensive_epa_per_play")) * 22
        + (number("home_success_rate") - number("away_defensive_success_rate_allowed")) * 16
        + (number("home_explosiveness") - number("away_explosiveness_allowed")) * 18
        + (number("home_points_per_drive") - number("away_points_allowed_per_drive")) * 2.4
        + (number("home_red_zone_td_rate") - number("away_red_zone_td_rate_allowed")) * 5.5
        + (number("home_havoc_rate") - number("away_havoc_allowed")) * 0.08
    )
    away_drive = (
        (number("away_offensive_epa_per_play") - number("home_defensive_epa_per_play")) * 22
        + (number("away_success_rate") - number("home_defensive_success_rate_allowed")) * 16
        + (number("away_explosiveness") - number("home_explosiveness_allowed")) * 18
        + (number("away_points_per_drive") - number("home_points_allowed_per_drive")) * 2.4
        + (number("away_red_zone_td_rate") - number("home_red_zone_td_rate_allowed")) * 5.5
        + (number("away_havoc_rate") - number("home_havoc_allowed")) * 0.08
    )
    home_field = 0 if input_stats.get("neutral_site") else number("home_field_advantage", 3.0)
    projected_margin = home_drive - away_drive + home_field
    projected_margin += (number("home_turnover_margin") - number("away_turnover_margin")) * 0.75
    projected_margin += (number("home_qb_rating") - number("away_qb_rating")) * 0.045
    projected_margin += (number("home_qb_injury_adjustment") - number("away_qb_injury_adjustment")) * 1.25
    projected_margin += (number("home_offensive_line_rating") - number("away_offensive_line_rating")) * 0.035
    projected_margin += (number("home_defensive_line_rating") - number("away_defensive_line_rating")) * 0.035
    projected_margin += (number("home_special_teams_rating") - number("away_special_teams_rating")) * 0.02
    projected_margin += (number("home_strength_of_schedule") - number("away_strength_of_schedule")) * 0.20
    projected_margin += (number("away_rank", 70) - number("home_rank", 70)) * 0.045
    projected_margin += (number("home_power_rating") - number("away_power_rating")) * 0.075
    projected_margin += (number("home_conference_strength") - number("away_conference_strength")) * 0.30
    projected_margin += max(-1.0, min(1.0, (number("home_rest_days") - number("away_rest_days")) * 0.18))
    projected_margin -= max(-0.9, min(0.9, (number("home_travel_fatigue") - number("away_travel_fatigue")) * 0.35))

    pace_seconds = max(20.0, min(35.0, (number("home_pace_seconds_per_play", 26.5) + number("away_pace_seconds_per_play", 26.5)) / 2))
    plays = max(55.0, min(92.0, (number("home_plays_per_game", 70) + number("away_plays_per_game", 70)) / 2))
    tempo_boost = (70 - plays) * -0.08 + (26.5 - pace_seconds) * 0.25
    base_total = 48.0 + ((home_drive + away_drive) * 1.05) + tempo_boost
    base_total += (number("home_explosiveness") + number("away_explosiveness") - 0.28) * 18
    base_total += (number("home_points_per_drive") + number("away_points_per_drive") - 4.8) * 2.2
    wind = number("weather_wind_mph", 0)
    precip = str(input_stats.get("weather_precipitation") or "").strip().lower()
    if wind >= 15:
        base_total -= min(6.0, (wind - 12) * 0.35)
    if precip not in {"", "none", "no", "false", "0", "clear"}:
        base_total -= 2.0
    projected_total = max(31.0, min(82.0, base_total))
    selected_margin = projected_margin if selected_home else -projected_margin
    projected_team_points = (projected_total / 2) + (selected_margin / 2)
    projected_opponent_points = projected_total - projected_team_points

    raw_model_probability = _logistic_probability(selected_margin, 9.8)
    line = _safe_float(payload.get("line"), _safe_float(input_stats.get("line")))
    total_line = _safe_float(payload.get("total_line"), _safe_float(input_stats.get("total_line")))
    if market_key in {"spread", "first_half_spread", "first_quarter_spread", "alt_spread"}:
        period_scale = 0.50 if "first_half" in market_key else 0.24 if "first_quarter" in market_key else 1.0
        raw_model_probability = _logistic_probability((selected_margin * period_scale) + (line or 0), 10.5 * max(0.48, period_scale))
    elif market_key in {"total", "first_half_total", "first_quarter_total", "alt_total"}:
        period_scale = 0.50 if "first_half" in market_key else 0.24 if "first_quarter" in market_key else 1.0
        target = total_line if total_line is not None else projected_total * period_scale
        over_probability = _logistic_probability((projected_total * period_scale) - target, 9.8 * max(0.48, period_scale))
        raw_model_probability = 1 - over_probability if "under" in selection_text else over_probability
    elif market_key in {"team_total", "alt_team_total"}:
        target = total_line if total_line is not None else projected_team_points
        over_probability = _logistic_probability(projected_team_points - target, 7.5)
        raw_model_probability = 1 - over_probability if "under" in selection_text else over_probability
    elif market_key in {"first_half_moneyline", "first_quarter_moneyline"}:
        period_scale = 0.50 if market_key == "first_half_moneyline" else 0.24
        raw_model_probability = _logistic_probability(selected_margin * period_scale, 7.5 * max(0.55, period_scale))
    elif market_key in COLLEGE_FOOTBALL_PROP_MARKETS:
        projection_map = {
            "player_passing_yards": "player_passing_yards_projection",
            "player_passing_tds": "player_passing_tds_projection",
            "player_interceptions": "player_interceptions_projection",
            "player_rushing_yards": "player_rushing_yards_projection",
            "player_rushing_tds": "player_rushing_tds_projection",
            "player_receiving_yards": "player_receiving_yards_projection",
            "player_receptions": "player_receptions_projection",
        }
        if market_key == "player_anytime_td":
            raw_model_probability = max(0.03, min(0.82, number("player_anytime_td_probability", 0.33)))
        else:
            projection = number(projection_map.get(market_key, "player_passing_yards_projection"), 40)
            target = line if line is not None else projection
            stddev = max(1.0, abs(projection) * (0.28 if "tds" not in market_key and "interceptions" not in market_key else 0.55))
            over_probability = 1 - _normal_cdf(target, mean=projection, stddev=stddev)
            raw_model_probability = 1 - over_probability if "under" in selection_text else over_probability

    no_vig_anchor = _safe_float(input_stats.get("no_vig_market_probability"))
    if no_vig_anchor is not None and no_vig_anchor > 1:
        no_vig_anchor = no_vig_anchor / 100
    market_anchor = max(0.01, min(0.99, no_vig_anchor)) if no_vig_anchor is not None else None
    calibrated_probability = raw_model_probability * 0.90 + market_anchor * 0.10 if market_anchor is not None else raw_model_probability
    true_probability = max(0.06, min(0.94, calibrated_probability))
    sanity_flags = ["college football probability cap applied"] if true_probability != calibrated_probability else []

    confidence = 72.0
    risk_flags = []
    if _safe_float(input_stats.get("book_count"), 0) < 4:
        confidence -= 3
        risk_flags.append("book count too low")
    if wind >= 15:
        confidence -= 5 if market_key in {"total", "first_half_total", "first_quarter_total", *COLLEGE_FOOTBALL_PROP_MARKETS} else 2
        risk_flags.append("weather sensitivity")
    if precip not in {"", "none", "no", "false", "0", "clear"}:
        confidence -= 4
        risk_flags.append("precipitation volatility")
    if abs(number("home_qb_injury_adjustment")) >= 1 or abs(number("away_qb_injury_adjustment")) >= 1:
        confidence -= 6
        risk_flags.append("QB injury sensitivity")
    if input_stats.get("blowout_risk"):
        confidence -= 5
        risk_flags.append("blowout risk")
    if input_stats.get("garbage_time_risk"):
        confidence -= 4
        risk_flags.append("garbage-time risk")
    if input_stats.get("tempo_volatility"):
        confidence -= 3
        risk_flags.append("tempo volatility")
    if market_key in COLLEGE_FOOTBALL_PROP_MARKETS:
        confidence -= 3
        if number("player_snap_share", 0) < 0.45:
            confidence -= 12
            risk_flags.append("prop snap-share fragility")
    if input_stats.get("provider_status") == "error":
        risk_flags.append("provider failure ignored")
    confidence = max(1, min(95, round(confidence, 2)))

    edge = calculate_edge_percent(true_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags: list[str] = []
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
    suggested = 0 if no_bet_flags else calculate_suggested_stake(
        bankroll=bankroll,
        american_odds=odds_american,
        true_probability=true_probability,
        risk_profile=risk_profile,
        confidence=confidence,
    )
    if suggested <= 0 and not no_bet_flags and edge is not None and edge >= edge_threshold and confidence >= confidence_threshold:
        suggested = round(max(1.0, bankroll * 0.004), 2)

    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": "high" if risk_flags else "moderate",
        "suggested_stake": suggested,
        "raw_model_probability": raw_model_probability,
        "calibrated_model_probability": calibrated_probability,
        "probability_calibration_applied": bool(market_anchor is not None or sanity_flags),
        "probability_sanity_flags": sanity_flags,
        "probability_cap_reason": "ncaaf college football sanity cap" if sanity_flags else None,
        "market_anchor_probability": market_anchor,
        "league_calibration_applied": "ncaaf",
        "projected_margin": round(projected_margin, 2),
        "projected_total": round(projected_total, 2),
        "projected_team_points": round(projected_team_points, 2),
        "projected_opponent_points": round(projected_opponent_points, 2),
        "risk_flags": risk_flags,
        "input_coverage": {
            "required_core_present": list(COLLEGE_FOOTBALL_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": COLLEGE_FOOTBALL_REQUIRED_MARKET_INPUTS.get(market_key, []),
            "optional_enrichment_present": [field for field in COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None],
            "optional_enrichment_missing": [field for field in COLLEGE_FOOTBALL_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
        },
        "provider_enrichment": {"provider_status": "not_provided", "provider_enrichment_present": []},
        "no_bet_flags": no_bet_flags,
    }


def _cricket_format_calibration(raw_format: Any) -> dict[str, Any]:
    fmt = str(raw_format or "").strip().lower().replace("-", "_").replace(" ", "_")
    if fmt in {"ipl", "indian_premier_league"}:
        return {"format": "ipl", "baseline_total": 174.0, "volatility": 18.0, "confidence_base": 74.0, "overs": 20.0}
    if fmt in {"t20", "t20_cricket", "bbl", "big_bash", "cpl", "psl", "the_hundred"}:
        return {"format": "t20", "baseline_total": 168.0, "volatility": 19.0, "confidence_base": 72.0, "overs": 20.0}
    if fmt in {"odi", "one_day", "one_day_cricket"}:
        return {"format": "odi", "baseline_total": 286.0, "volatility": 27.0, "confidence_base": 70.0, "overs": 50.0}
    if fmt in {"test", "test_cricket"}:
        return {"format": "test", "baseline_total": 330.0, "volatility": 38.0, "confidence_base": 66.0, "overs": 90.0}
    return {"format": "unknown", "baseline_total": 168.0, "volatility": 22.0, "confidence_base": 68.0, "overs": 20.0}


def _estimate_cricket_run_rate_model(
    *,
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    missing = _cricket_full_inputs_missing(input_stats, payload) + _cricket_market_specific_missing(market, input_stats, payload)
    if missing:
        return None
    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None
    if implied_probability is None:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    selection_text = str(payload.get("selection") or input_stats.get("selection") or "").strip().lower()
    team_text = str(input_stats.get("team") or "").strip().lower()
    opponent_text = str(input_stats.get("opponent") or "").strip().lower()
    selected_team = not opponent_text or selection_text == team_text or team_text in selection_text

    calibration = _cricket_format_calibration(input_stats.get("format") or payload.get("league"))
    format_key = calibration["format"]
    baseline_total = calibration["baseline_total"]
    volatility = calibration["volatility"]

    team_phase_rr = (
        number("team_powerplay_run_rate") * 0.32
        + number("team_middle_overs_run_rate") * 0.34
        + number("team_death_overs_run_rate") * 0.34
    )
    opponent_phase_rr = (
        number("opponent_powerplay_run_rate") * 0.32
        + number("opponent_middle_overs_run_rate") * 0.34
        + number("opponent_death_overs_run_rate") * 0.34
    )
    run_rate_edge = team_phase_rr - opponent_phase_rr
    batting_edge = (number("team_batting_rating") - number("opponent_batting_rating")) * 0.032
    bowling_edge = (number("team_bowling_rating") - number("opponent_bowling_rating")) * 0.030
    fielding_edge = (number("team_fielding_rating") - number("opponent_fielding_rating")) * 0.018
    form_edge = (number("team_recent_form_rating") - number("opponent_recent_form_rating")) * 0.025
    wicket_resource_edge = (
        (number("team_wicket_taking_rate") - number("opponent_wicket_taking_rate")) * 7.5
        + (number("opponent_wicket_loss_rate") - number("team_wicket_loss_rate")) * 7.0
    )
    boundary_edge = (
        (number("team_boundary_rate") - number("opponent_boundary_rate")) * 8.0
        + (number("opponent_dot_ball_rate") - number("team_dot_ball_rate")) * 5.0
    )
    chase_edge = (number("team_chase_rating") - number("opponent_chase_rating")) * 0.018
    defend_edge = (number("team_defend_total_rating") - number("opponent_defend_total_rating")) * 0.014

    toss_winner = str(input_stats.get("toss_winner") or "").strip().lower()
    toss_decision = str(input_stats.get("toss_decision") or "").strip().lower()
    dew = number("dew_factor")
    wind = number("wind_factor")
    venue_chase = number("venue_chase_win_rate", 0.5)
    toss_edge = 0.0
    if toss_winner and toss_winner == team_text:
        if "bowl" in toss_decision:
            toss_edge += (venue_chase - 0.5) * 2.8 + dew * 0.55 + chase_edge
        elif "bat" in toss_decision:
            toss_edge += defend_edge + (0.5 - venue_chase) * 1.5
    elif toss_winner and toss_winner == opponent_text:
        if "bowl" in toss_decision:
            toss_edge -= (venue_chase - 0.5) * 2.4 + dew * 0.45
        elif "bat" in toss_decision:
            toss_edge -= defend_edge * 0.5

    pitch_spin = number("pitch_spin_assist")
    pitch_pace = number("pitch_pace_assist")
    bowling_style_edge = ((pitch_spin + pitch_pace) - 1.0) * (number("team_bowling_rating") - number("opponent_bowling_rating")) * 0.006
    venue_average = number("venue_average_score", baseline_total)
    venue_scoring_boost = (venue_average - baseline_total) * 0.035
    wind_drag = -abs(wind) * 0.7 if wind > 0.35 else 0

    selected_edge_score = (
        run_rate_edge * 1.45 + batting_edge + bowling_edge + fielding_edge + form_edge
        + wicket_resource_edge + boundary_edge + toss_edge + bowling_style_edge + venue_scoring_boost + wind_drag
    )
    if not selected_team:
        selected_edge_score *= -1

    raw_match_probability = _logistic_probability(selected_edge_score, 4.8 if format_key in {"ipl", "t20"} else 5.6)

    selected_run_rate = team_phase_rr if selected_team else opponent_phase_rr
    opponent_run_rate = opponent_phase_rr if selected_team else team_phase_rr
    selected_wicket_loss = number("team_wicket_loss_rate") if selected_team else number("opponent_wicket_loss_rate")
    opponent_wicket_loss = number("opponent_wicket_loss_rate") if selected_team else number("team_wicket_loss_rate")
    overs = calibration["overs"]
    innings_overs = 20.0 if format_key in {"ipl", "t20", "unknown"} else 50.0 if format_key == "odi" else 90.0
    projected_team_runs = max(35.0, selected_run_rate * innings_overs * (1 - selected_wicket_loss * 0.18))
    projected_opponent_runs = max(35.0, opponent_run_rate * innings_overs * (1 - opponent_wicket_loss * 0.18))
    projected_team_runs += selected_edge_score * 1.6 + (venue_average - baseline_total) * 0.22
    projected_opponent_runs -= selected_edge_score * 1.1 - (venue_average - baseline_total) * 0.16
    projected_total_runs = max(60.0, projected_team_runs + projected_opponent_runs)

    raw_model_probability = raw_match_probability
    line = _safe_float(payload.get("line"), _safe_float(input_stats.get("line")))
    total_runs_line = _safe_float(payload.get("total_runs_line"), _safe_float(input_stats.get("total_runs_line")))
    team_total_line = _safe_float(payload.get("team_total_runs_line"), _safe_float(input_stats.get("team_total_runs_line")))
    if market_key in {"spread", "run_line"}:
        target = line if line is not None else 0
        margin = projected_team_runs - projected_opponent_runs
        raw_model_probability = _logistic_probability(margin + target, volatility * 0.65)
    elif market_key in {"total_runs", "alt_total_runs", "first_innings_total"}:
        target = total_runs_line if total_runs_line is not None else projected_total_runs
        over_probability = _logistic_probability(projected_total_runs - target, volatility)
        raw_model_probability = 1 - over_probability if "under" in selection_text else over_probability
    elif market_key in {"first_6_overs_total", "powerplay_total"}:
        target = total_runs_line if total_runs_line is not None else projected_total_runs * 0.18
        powerplay_projection = selected_run_rate * 6.0
        over_probability = _logistic_probability(powerplay_projection - target, 6.5)
        raw_model_probability = 1 - over_probability if "under" in selection_text else over_probability
    elif market_key in {"team_total_runs", "alt_team_total_runs"}:
        target = team_total_line if team_total_line is not None else projected_team_runs
        over_probability = _logistic_probability(projected_team_runs - target, volatility * 0.65)
        raw_model_probability = 1 - over_probability if "under" in selection_text else over_probability
    elif market_key == "first_innings_winner":
        raw_model_probability = _logistic_probability(selected_edge_score + toss_edge * 0.6, 5.0)
    elif market_key in CRICKET_PROP_MARKETS:
        player_runs = number("player_runs_projection")
        player_wickets = number("player_wickets_projection")
        player_sixes = number("player_sixes_projection")
        player_fours = number("player_fours_projection")
        prop_line = line if line is not None else number("line", 0.5)
        balls_faced = number("player_balls_faced_projection")
        overs_projection = number("player_overs_projection")
        if market_key in {"top_batter", "player_runs"}:
            stddev = max(6.0, player_runs * 0.42)
            over_probability = 1 - _normal_cdf(prop_line, mean=player_runs, stddev=stddev)
            raw_model_probability = max(0.04, min(0.88, over_probability if market_key == "player_runs" else 0.16 + player_runs / 155))
        elif market_key in {"top_bowler", "player_wickets"}:
            stddev = max(0.55, player_wickets * 0.75)
            over_probability = 1 - _normal_cdf(prop_line, mean=player_wickets, stddev=stddev)
            raw_model_probability = max(0.04, min(0.82, over_probability if market_key == "player_wickets" else 0.12 + player_wickets / 5.5))
        elif market_key == "player_sixes":
            raw_model_probability = max(0.03, min(0.78, 1 - _normal_cdf(prop_line, mean=player_sixes, stddev=max(0.6, player_sixes * 0.70))))
        elif market_key == "player_fours":
            raw_model_probability = max(0.03, min(0.80, 1 - _normal_cdf(prop_line, mean=player_fours, stddev=max(0.8, player_fours * 0.55))))
        elif market_key == "player_total_boundaries":
            boundaries = player_sixes + player_fours
            raw_model_probability = max(0.03, min(0.80, 1 - _normal_cdf(prop_line, mean=boundaries, stddev=max(1.0, boundaries * 0.52))))
        elif market_key == "player_ducks":
            raw_model_probability = max(0.02, min(0.36, _safe_probability(input_stats.get("player_duck_rate")) or 0.08))
        elif market_key == "player_dismissal_method":
            raw_model_probability = max(0.03, min(0.34, 0.12 + selected_wicket_loss * 0.35))
        elif market_key == "anytime_fifty":
            raw_model_probability = max(0.03, min(0.72, (_safe_probability(input_stats.get("player_fifty_rate")) or 0.20) + max(0, player_runs - 32) * 0.006))
        elif market_key == "anytime_hundred":
            raw_model_probability = max(0.01, min(0.34, (_safe_probability(input_stats.get("player_hundred_rate")) or 0.04) + max(0, player_runs - 55) * 0.003))
        if balls_faced < 8 and market_key in {"top_batter", "player_runs", "player_sixes", "player_fours", "player_total_boundaries", "anytime_fifty", "anytime_hundred"}:
            raw_model_probability = min(raw_model_probability, 0.55)
        if overs_projection < 1 and market_key in {"top_bowler", "player_wickets"}:
            raw_model_probability = min(raw_model_probability, 0.50)

    market_anchor = _safe_probability(input_stats.get("no_vig_market_probability"))
    calibrated_probability = raw_model_probability * 0.90 + market_anchor * 0.10 if market_anchor is not None else raw_model_probability
    true_probability = max(0.06, min(0.92, calibrated_probability))
    sanity_flags = ["cricket probability cap applied"] if true_probability != calibrated_probability else []

    confidence = calibration["confidence_base"]
    risk_flags: list[str] = []
    if _safe_float(input_stats.get("book_count"), 0) < 4:
        confidence -= 4
        risk_flags.append("book count too low")
    if format_key == "unknown":
        confidence -= 5
        risk_flags.append("format calibration unknown")
    if dew > 0.5:
        confidence -= 2
        risk_flags.append("dew volatility")
    if wind > 0.35:
        confidence -= 3
        risk_flags.append("wind volatility")
    if market_key in CRICKET_PROP_MARKETS:
        confidence -= 3
        if number("player_balls_faced_projection") < 10 and market_key not in {"top_bowler", "player_wickets"}:
            confidence -= 12
            risk_flags.append("prop batting-role fragility")
        if number("player_overs_projection") < 1 and market_key in {"top_bowler", "player_wickets"}:
            confidence -= 10
            risk_flags.append("bowler overs fragility")
    if input_stats.get("provider_status") == "error":
        risk_flags.append("provider failure ignored")
    if input_stats.get("lineup_confirmed") is False or input_stats.get("batting_order_confirmed") is False:
        confidence -= 6
        risk_flags.append("lineup uncertainty")
    confidence = max(1, min(95, round(confidence, 2)))

    edge = calculate_edge_percent(true_probability, implied_probability)
    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags: list[str] = []
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
    suggested = 0 if no_bet_flags else calculate_suggested_stake(
        bankroll=bankroll,
        american_odds=odds_american,
        true_probability=true_probability,
        risk_profile=risk_profile,
        confidence=confidence,
    )
    if suggested <= 0 and not no_bet_flags and edge is not None and edge >= edge_threshold and confidence >= confidence_threshold:
        suggested = round(max(1.0, bankroll * 0.004), 2)

    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": "high" if risk_flags else "moderate",
        "suggested_stake": suggested,
        "raw_model_probability": raw_model_probability,
        "calibrated_model_probability": calibrated_probability,
        "probability_calibration_applied": bool(market_anchor is not None or sanity_flags),
        "probability_sanity_flags": sanity_flags,
        "probability_cap_reason": "cricket sanity cap" if sanity_flags else None,
        "market_anchor_probability": market_anchor,
        "league_calibration_applied": "cricket",
        "format_calibration_applied": format_key,
        "projected_team_runs": round(projected_team_runs, 2),
        "projected_opponent_runs": round(projected_opponent_runs, 2),
        "projected_total_runs": round(projected_total_runs, 2),
        "projected_run_differential": round(projected_team_runs - projected_opponent_runs, 2),
        "risk_flags": risk_flags,
        "input_coverage": {
            "required_core_present": list(CRICKET_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": CRICKET_REQUIRED_MARKET_INPUTS.get(market_key, []),
            "optional_enrichment_present": [field for field in CRICKET_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None],
            "optional_enrichment_missing": [field for field in CRICKET_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
        },
        "provider_enrichment": {
            "provider_status": "available" if input_stats.get("provider_status") not in {None, "error"} else input_stats.get("provider_status") or "not_provided",
            "provider_enrichment_present": [field for field in CRICKET_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None],
        },
        "no_bet_flags": no_bet_flags,
    }


def _estimate_nfl_drive_model(
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    core_missing = _nfl_full_inputs_missing(input_stats)
    market_missing = _nfl_market_specific_missing(market, input_stats, payload)
    if core_missing or market_missing:
        return None

    def number(key: str, default: float = 0) -> float:
        return _safe_float(input_stats.get(key), default) or default

    optional_present = [field for field in NFL_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    provider_present = [field for field in NFL_PROVIDER_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    officiating_present = _official_inputs_present(input_stats, NFL_OFFICIATING_INPUTS)
    social_present = [field for field in NFL_SOCIAL_CROWD_INPUTS if input_stats.get(field) is not None]
    live_present = [field for field in NFL_LIVE_BETTING_INPUTS if input_stats.get(field) is not None]

    team_drive = (
        (number("team_offensive_epa_per_play") - number("opponent_defensive_epa_per_play")) * 18
        + (number("team_success_rate") - number("opponent_defensive_success_rate_allowed")) * 14
        + (number("team_explosive_play_rate") - number("opponent_explosive_play_rate_allowed")) * 16
        + (number("team_pressure_rate_allowed") - number("opponent_pressure_rate_generated")) * -8
        + (number("team_red_zone_td_rate") - number("opponent_red_zone_td_rate_allowed")) * 8
        + (number("opponent_turnover_rate") - number("team_turnover_rate")) * 10
    )
    opponent_drive = (
        (number("opponent_offensive_epa_per_play") - number("team_defensive_epa_per_play")) * 18
        + (number("opponent_success_rate") - number("team_defensive_success_rate_allowed")) * 14
        + (number("opponent_explosive_play_rate") - number("team_explosive_play_rate_allowed")) * 16
        + (number("opponent_pressure_rate_allowed") - number("team_pressure_rate_generated")) * -8
        + (number("opponent_red_zone_td_rate") - number("team_red_zone_td_rate_allowed")) * 8
        + (number("team_turnover_rate") - number("opponent_turnover_rate")) * 10
    )
    pace = max(24.0, min(34.0, (number("team_pace_seconds_per_play", 28) + number("opponent_pace_seconds_per_play", 28)) / 2))
    pace_boost = (28.5 - pace) * 0.35
    home_away = str(input_stats.get("home_away") or "").strip().lower()
    home_adjustment = 1.4 if home_away == "home" else -1.0 if home_away == "away" else 0
    projected_margin = (team_drive - opponent_drive) + home_adjustment
    projected_total = 44 + ((team_drive + opponent_drive) * 0.9) + pace_boost

    if input_stats.get("team_recent_epa_per_play_3") is not None and input_stats.get("opponent_recent_epa_per_play_3") is not None:
        projected_margin += (number("team_recent_epa_per_play_3") - number("opponent_recent_epa_per_play_3")) * 6
    if input_stats.get("team_special_teams_epa") is not None and input_stats.get("opponent_special_teams_epa") is not None:
        projected_margin += (number("team_special_teams_epa") - number("opponent_special_teams_epa")) * 4
    rest_edge = number("team_rest_days", 0) - number("opponent_rest_days", 0)
    projected_margin += max(-1.0, min(1.0, rest_edge * 0.2))
    travel_edge = (number("opponent_travel_distance_miles", 0) - number("team_travel_distance_miles", 0)) / 1000
    projected_margin += max(-0.8, min(0.8, travel_edge * 0.2))
    if input_stats.get("team_short_week") is True:
        projected_margin -= 0.8
    if input_stats.get("opponent_short_week") is True:
        projected_margin += 0.8

    qb_status = str(input_stats.get("qb_status") or "").strip().lower()
    offensive_line_health = str(input_stats.get("offensive_line_health") or "").strip().lower()
    injury_status = str(input_stats.get("injury_report_status") or "").strip().lower()
    if qb_status in {"out", "backup", "doubtful"}:
        projected_margin -= 3.5
        projected_total -= 2.5
    elif qb_status in {"questionable", "uncertain", "limited"}:
        projected_margin -= 1.4
        projected_total -= 1.0
    if offensive_line_health in {"poor", "bad", "thin", "injured"}:
        projected_margin -= 1.2
        projected_total -= 1.0
    if injury_status not in {"clean", "clear", "healthy", "normal", "available"}:
        projected_margin -= 0.8
        projected_total -= 0.6

    wind = number("weather_wind_mph", 0)
    if wind >= 15 and not input_stats.get("dome_game"):
        projected_total -= min(5.0, (wind - 12) * 0.35)
    if _truthy_available(input_stats.get("weather_precipitation")) and not input_stats.get("dome_game"):
        projected_total -= 1.5
    projected_total = max(28.0, min(64.0, projected_total))
    projected_team_points = (projected_total / 2) + (projected_margin / 2)
    projected_opponent_points = projected_total - projected_team_points
    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    if market_key in {"spread", "first_half_spread", "first_quarter_spread"}:
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        period_scale = 0.50 if market_key == "first_half_spread" else 0.24 if market_key == "first_quarter_spread" else 1.0
        raw_model_probability = _logistic_probability((projected_margin * period_scale) + line, 9.5 * max(0.45, period_scale))
    elif market_key in {"total", "first_half_total", "first_quarter_total"}:
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        period_scale = 0.50 if market_key == "first_half_total" else 0.24 if market_key == "first_quarter_total" else 1.0
        over_probability = _logistic_probability((projected_total * period_scale) - total_line, 8.5 * max(0.45, period_scale))
        selection = str(payload.get("selection") or input_stats.get("selection") or "").lower()
        raw_model_probability = 1 - over_probability if "under" in selection else over_probability
    elif market_key == "team_total":
        team_total_line = _safe_float(input_stats.get("team_total_line") if input_stats.get("team_total_line") is not None else payload.get("team_total_line"), 0) or 0
        over_probability = _logistic_probability(projected_team_points - team_total_line, 6.0)
        selection = str(payload.get("selection") or input_stats.get("selection") or "").lower()
        raw_model_probability = 1 - over_probability if "under" in selection else over_probability
    elif market_key == "player_prop":
        projection = number("player_projection")
        prop_line = number("prop_line")
        raw_model_probability = _logistic_probability(projection - prop_line, max(1.0, abs(prop_line) * 0.18))
    elif market_key == "first_half":
        raw_model_probability = _logistic_probability(projected_margin * 0.50, 6.0)
    elif market_key == "first_quarter":
        raw_model_probability = _logistic_probability(projected_margin * 0.24, 4.5)
    else:
        raw_model_probability = _logistic_probability(projected_margin, 8.0)

    market_probability = _safe_probability(input_stats.get("no_vig_market_probability"))
    confidence = 68
    confidence += min(8, len(optional_present) * 0.18)
    confidence += min(4, len(provider_present) * 0.5)
    if qb_status in {"out", "questionable", "uncertain", "limited", "backup", "doubtful"}:
        confidence -= 10 if qb_status == "out" else 6
    if offensive_line_health in {"poor", "bad", "thin", "injured"}:
        confidence -= 6
    if injury_status not in {"clean", "clear", "healthy", "normal", "available"}:
        confidence -= 5
    if wind >= 15:
        confidence -= 5 if market_key in {"total", "player_prop"} else 2
    book_count = _safe_float(input_stats.get("book_count"))
    if book_count is not None and book_count < 5:
        confidence -= 4
    if input_stats.get("best_available_odds") is None:
        confidence -= 3
    current_odds = _safe_float(input_stats.get("current_odds"))
    consensus_odds = _safe_float(input_stats.get("consensus_odds"))
    risk = "medium"
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 25:
        risk = "high"
        confidence -= 3
    if officiating_present:
        confidence += min(2, len(officiating_present) * 0.5)
    if social_present:
        confidence += min(2, len(social_present) * 0.2)
    if live_present and input_stats.get("live_game") is True:
        confidence += 3 if len(live_present) >= 5 else -8
    confidence = max(1, min(95, round(confidence, 2)))

    market_anchor_probability = market_probability if market_probability is not None else implied_probability if implied_probability is not None else 0.5
    if market_key == "moneyline":
        calibration = _calibrate_nfl_probability(
            raw_probability=raw_model_probability,
            market_anchor_probability=market_anchor_probability,
            market_anchor_is_no_vig=market_probability is not None,
            projected_margin=projected_margin,
            input_confidence_hint=confidence,
        )
        true_probability = calibration["final_probability"]
    else:
        calibrated_probability = (raw_model_probability * 0.85) + (market_anchor_probability * 0.15)
        true_probability = max(0.03, min(0.97, calibrated_probability))
        calibration = {
            "raw_model_probability": raw_model_probability,
            "calibrated_model_probability": calibrated_probability,
            "final_probability": true_probability,
            "market_anchor_probability": market_anchor_probability,
            "probability_calibration_applied": abs(calibrated_probability - raw_model_probability) >= 0.025,
            "probability_sanity_flags": ["probability calibration applied"] if abs(calibrated_probability - raw_model_probability) >= 0.025 else [],
            "probability_cap_reason": None,
        }
    if calibration["probability_sanity_flags"]:
        confidence = max(1, round(confidence - min(8, 2 * len(calibration["probability_sanity_flags"])), 2))
        if "probability calibration applied" not in calibration["probability_sanity_flags"]:
            calibration["probability_sanity_flags"].append("probability calibration applied")

    edge = edge_percentage(true_probability, implied_probability) if implied_probability is not None else None

    edge_threshold, confidence_threshold = _nfl_thresholds(risk_profile)
    no_bet_flags: list[str] = []
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
        risk = "high"
    elif edge < edge_threshold:
        no_bet_flags.append("edge too small")
    if confidence < confidence_threshold:
        no_bet_flags.append("low confidence")
        risk = "high"
    if odds_american is None:
        no_bet_flags.append("odds missing")
    if current_odds is not None and consensus_odds is not None and abs(current_odds - consensus_odds) >= 35:
        no_bet_flags.append("market disagreement too high")

    suggested = 0.0
    if not no_bet_flags and odds_american is not None:
        suggested = suggested_stake_with_risk_controls(
            bankroll=bankroll,
            american_odds=odds_american,
            true_probability=true_probability,
            risk_profile="standard" if str(risk_profile or "").lower() == "moderate" else risk_profile,
            confidence_0_100=confidence,
        )
        risk = "low" if edge is not None and edge >= 5 else risk

    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "final_probability": true_probability,
        "model_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "raw_model_probability": calibration["raw_model_probability"],
        "calibrated_model_probability": calibration["calibrated_model_probability"],
        "probability_calibration_applied": calibration["probability_calibration_applied"],
        "probability_sanity_flags": calibration["probability_sanity_flags"],
        "probability_cap_reason": calibration["probability_cap_reason"],
        "market_anchor_probability": calibration["market_anchor_probability"],
        "projected_margin": round(projected_margin, 2),
        "projected_total": round(projected_total, 2),
        "projected_team_points": round(projected_team_points, 2),
        "projected_opponent_points": round(projected_opponent_points, 2),
        "nfl_input_contract": deepcopy(NFL_INPUT_CONTRACT),
        "input_coverage": {
            "required_core_present": list(NFL_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": NFL_REQUIRED_MARKET_SPECIFIC_INPUTS.get(market_key, []),
            "optional_enrichment_present": optional_present,
            "optional_enrichment_missing": [field for field in NFL_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
            "provider_enrichment_present": provider_present,
            "officiating_present": officiating_present,
            "referee_present": officiating_present,
            "social_crowd_present": social_present,
            "live_betting_present": live_present,
        },
        "provider_enrichment": {
            "provider_enrichment_present": provider_present,
            "provider_status": "available" if provider_present else "not_provided",
        },
        "no_bet_flags": no_bet_flags,
    }


def _estimate_nba_possession_model(
    input_stats: dict[str, Any],
    payload: dict[str, Any],
    market: Any,
    odds_american: Optional[float],
    bankroll: float,
    risk_profile: str,
) -> Optional[dict[str, Any]]:
    core_missing = _nba_full_inputs_missing(input_stats)
    market_missing = _nba_market_specific_missing(market, input_stats, payload)
    if core_missing or market_missing:
        return None

    team_pace = _safe_float(input_stats.get("team_pace"), 0) or 0
    opponent_pace = _safe_float(input_stats.get("opponent_pace"), 0) or 0
    team_off = _safe_float(input_stats.get("team_offensive_rating"), 0) or 0
    opponent_off = _safe_float(input_stats.get("opponent_offensive_rating"), 0) or 0
    team_def = _safe_float(input_stats.get("team_defensive_rating"), 0) or 0
    opponent_def = _safe_float(input_stats.get("opponent_defensive_rating"), 0) or 0

    team_efg = _safe_probability(input_stats.get("team_efg_percent")) or 0.5
    opponent_efg = _safe_probability(input_stats.get("opponent_efg_percent")) or 0.5
    team_tov = _safe_probability(input_stats.get("team_turnover_percent")) or 0.13
    opponent_tov = _safe_probability(input_stats.get("opponent_turnover_percent")) or 0.13
    team_oreb = _safe_probability(input_stats.get("team_offensive_rebound_percent")) or 0.25
    opponent_oreb = _safe_probability(input_stats.get("opponent_offensive_rebound_percent")) or 0.25
    team_ftr = _safe_probability(input_stats.get("team_free_throw_rate")) or 0.22
    opponent_ftr = _safe_probability(input_stats.get("opponent_free_throw_rate")) or 0.22

    pace = (team_pace + opponent_pace) / 2
    team_expected_per_100 = (team_off * 0.55) + (opponent_def * 0.45)
    opponent_expected_per_100 = (opponent_off * 0.55) + (team_def * 0.45)
    four_factor_margin = (
        ((team_efg - opponent_efg) * 40)
        + ((opponent_tov - team_tov) * 18)
        + ((team_oreb - opponent_oreb) * 12)
        + ((team_ftr - opponent_ftr) * 8)
    )
    home_away = str(input_stats.get("home_away") or "").strip().lower()
    home_adjustment = 1.8 if home_away == "home" else -1.0 if home_away == "away" else 0.0
    usage_adjustment = 0.8 if _truthy_available(input_stats.get("key_player_usage_available")) else -1.5
    minutes_adjustment = 0.6 if _truthy_available(input_stats.get("minutes_projection_available")) else -1.5
    injury_status = str(input_stats.get("injury_report_status") or "").strip().lower()
    injury_adjustment = 0.6 if injury_status in {"clean", "clear", "available", "normal", "healthy"} else -1.2

    optional_present = [field for field in NBA_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    provider_present = [field for field in NBA_PROVIDER_ENRICHMENT_INPUTS if input_stats.get(field) is not None]
    referee_present = [field for field in NBA_REFEREE_INPUTS if input_stats.get(field) is not None]
    social_present = [field for field in NBA_SOCIAL_CROWD_INPUTS if input_stats.get(field) is not None]
    live_present = [field for field in NBA_LIVE_BETTING_INPUTS if input_stats.get(field) is not None]

    raw_margin_per_100 = team_expected_per_100 - opponent_expected_per_100
    estimated_margin = (raw_margin_per_100 * (pace / 100)) + four_factor_margin + home_adjustment + usage_adjustment + minutes_adjustment + injury_adjustment
    projected_margin = _safe_float(input_stats.get("projected_margin"))
    if projected_margin is not None:
        estimated_margin = (estimated_margin * 0.7) + (projected_margin * 0.3)
    recent_margin = None
    team_recent_5 = _safe_float(input_stats.get("team_recent_net_rating_5"))
    opponent_recent_5 = _safe_float(input_stats.get("opponent_recent_net_rating_5"))
    if team_recent_5 is not None and opponent_recent_5 is not None:
        recent_margin = (team_recent_5 - opponent_recent_5) * 0.08
        estimated_margin += recent_margin
    rest_edge = (_safe_float(input_stats.get("team_rest_days"), 0) or 0) - (_safe_float(input_stats.get("opponent_rest_days"), 0) or 0)
    estimated_margin += max(-1.0, min(1.0, rest_edge * 0.25))
    if input_stats.get("team_back_to_back") is True:
        estimated_margin -= 0.7
    if input_stats.get("opponent_back_to_back") is True:
        estimated_margin += 0.7
    travel_edge = ((_safe_float(input_stats.get("opponent_travel_distance_miles"), 0) or 0) - (_safe_float(input_stats.get("team_travel_distance_miles"), 0) or 0)) / 1000
    estimated_margin += max(-0.8, min(0.8, travel_edge * 0.25))
    ref_quality = str(input_stats.get("referee_data_quality") or "").strip().lower()
    if ref_quality in {"strong", "high"}:
        estimated_margin += max(-0.5, min(0.5, (_safe_float(input_stats.get("home_foul_differential"), 0) or 0) * 0.15))
    projected_total = _safe_float(input_stats.get("projected_total"))
    if projected_total is None:
        projected_total = ((team_expected_per_100 + opponent_expected_per_100) * pace / 100)
    projected_team_score = (projected_total / 2) + (estimated_margin / 2)
    projected_opponent_score = projected_total - projected_team_score

    market_key = _normal_market_key(input_stats.get("market_type") or market)
    if market_key in {"spread", "first_quarter_spread"}:
        line = _safe_float(input_stats.get("line") if input_stats.get("line") is not None else payload.get("line"), 0) or 0
        true_probability = _logistic_probability(estimated_margin + line, 12.0)
    elif market_key in {"total", "first_quarter_total"}:
        total_line = _safe_float(input_stats.get("total_line") if input_stats.get("total_line") is not None else payload.get("total_line"), 0) or 0
        scaled_total = projected_total * (0.24 if market_key == "first_quarter_total" else 1.0)
        over_probability = _logistic_probability(scaled_total - total_line, 15.0 if market_key == "total" else 5.0)
        true_probability = 1 - over_probability if "under" in str(payload.get("selection") or input_stats.get("selection") or "").lower() else over_probability
    elif market_key == "team_total":
        team_total_line = _safe_float(input_stats.get("team_total_line") if input_stats.get("team_total_line") is not None else payload.get("team_total_line"), 0) or 0
        over_probability = _logistic_probability(projected_team_score - team_total_line, 8.0)
        true_probability = 1 - over_probability if "under" in str(payload.get("selection") or input_stats.get("selection") or "").lower() else over_probability
    elif market_key == "first_half":
        true_probability = _logistic_probability(estimated_margin * 0.49, 7.5)
    elif market_key in {"first_quarter", "first_quarter_moneyline"}:
        true_probability = _logistic_probability(estimated_margin * 0.24, 5.5)
    elif market_key == "player_prop":
        projection = _safe_float(input_stats.get("player_projection"), 0) or 0
        prop_line = _safe_float(input_stats.get("prop_line"), 0) or 0
        true_probability = _logistic_probability(projection - prop_line, max(1.0, abs(prop_line) * 0.18))
    else:
        true_probability = 1 / (1 + 2.718281828 ** (-(estimated_margin / 11.0)))
    true_probability = max(0.03, min(0.97, true_probability))

    implied_probability = implied_probability_from_american(odds_american) if odds_american is not None else None
    edge = edge_percentage(true_probability, implied_probability) if implied_probability is not None else None
    confidence = 72
    if injury_status in {"clean", "clear", "available", "normal", "healthy"}:
        confidence += 6
    else:
        confidence -= 8
    if _truthy_available(input_stats.get("key_player_usage_available")):
        confidence += 5
    else:
        confidence -= 6
    if _truthy_available(input_stats.get("minutes_projection_available")):
        confidence += 5
    else:
        confidence -= 6
    if abs(estimated_margin) < 1.5:
        confidence -= 8
    confidence += min(10, len(optional_present) * 0.35)
    confidence += min(4, len(provider_present) * 0.5)
    if ref_quality in {"strong", "high"} and (_safe_float(input_stats.get("referee_sample_size"), 0) or 0) >= 30:
        confidence += 4
    if social_present:
        confidence += min(3, len(social_present) * 0.25)
    if str(input_stats.get("rumor_risk") or "").strip().lower() not in {"", "none", "low"}:
        confidence -= 8
    if input_stats.get("live_game") is True:
        confidence += 4 if len(live_present) >= 5 else -10
    if market_key == "player_prop":
        if input_stats.get("player_minutes_projection") is None:
            confidence -= 10
        if not _truthy_available(input_stats.get("minutes_projection_available")):
            confidence -= 6
    confidence = max(1, min(95, confidence))

    no_bet_flags: list[str] = []
    suggested = 0.0
    risk = "standard"
    if edge is None:
        no_bet_flags.append("edge missing")
    elif edge <= 0:
        no_bet_flags.append("negative edge")
        risk = "high"
    elif edge < 2.5:
        no_bet_flags.append("edge too small")
        risk = "medium"
    if confidence < 70:
        no_bet_flags.append("low confidence")
        risk = "high"
    if odds_american is None:
        no_bet_flags.append("odds missing")
    if not no_bet_flags and odds_american is not None:
        suggested = suggested_stake_with_risk_controls(
            bankroll=bankroll,
            american_odds=odds_american,
            true_probability=true_probability,
            risk_profile=risk_profile,
            confidence_0_100=confidence,
        )
        risk = "low" if edge is not None and edge >= 5 else "medium"

    return {
        "model_status": "active",
        "estimated_true_probability": true_probability,
        "true_probability": true_probability,
        "implied_probability": implied_probability,
        "edge": edge,
        "confidence": confidence,
        "risk": risk,
        "suggested_stake": suggested,
        "nba_input_contract": deepcopy(NBA_INPUT_CONTRACT),
        "input_coverage": {
            "required_core_present": list(NBA_REQUIRED_CORE_INPUTS),
            "required_market_specific_present": NBA_REQUIRED_MARKET_SPECIFIC_INPUTS.get(_normal_market_key(input_stats.get("market_type") or market), []),
            "optional_enrichment_present": optional_present,
            "optional_enrichment_missing": [field for field in NBA_OPTIONAL_ENRICHMENT_INPUTS if input_stats.get(field) is None],
            "provider_enrichment_present": provider_present,
            "referee_present": referee_present,
            "social_crowd_present": social_present,
            "live_betting_present": live_present,
        },
        "projected_score": {
            "team": round(projected_team_score, 2),
            "opponent": round(projected_opponent_score, 2),
            "estimated_margin": round(estimated_margin, 2),
        },
        "no_bet_flags": no_bet_flags,
    }


def analyze_sport_model(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = _safe_payload_dict(payload)
        sport = normalize_sport_key(str(payload.get("sport", "") or ""))
        config = get_sport_model_config(sport)
        market = payload.get("market")
        normalization = normalize_sport_inputs_for_model(
            sport=sport,
            market=market,
            selection=payload.get("selection"),
            input_stats=payload.get("input_stats"),
            ticket=payload,
        )
        input_stats = normalization["input_stats"]
        normalization_diagnostics = normalization["diagnostics"]
        input_stats_flags = list(normalization_diagnostics.get("input_stats_flags") or [])
        market = market or input_stats.get("market")
        raw_payload_odds = payload.get("odds_american")
        odds_american = _safe_float(raw_payload_odds)
        if odds_american is None and raw_payload_odds in (None, ""):
            odds_american = _safe_float(input_stats.get("odds_american"))
        bankroll = _safe_float(payload.get("bankroll"), 0) or 0
        unit_size = _safe_float(payload.get("unit_size"), 0) or 0
        if not config:
            response = _unsupported_sport_response(payload)
            if input_stats_flags:
                response["no_bet_flags"] = list(dict.fromkeys(response["no_bet_flags"] + input_stats_flags))
            response.update(normalization_diagnostics)
            return response

        nba_model = None
        wnba_model = None
        mens_cbb_model = None
        womens_cbb_model = None
        college_football_model = None
        nfl_model = None
        mlb_model = None
        soccer_model = None
        nhl_model = None
        tennis_model = None
        combat_model = None
        golf_model = None
        cricket_model = None
        if sport == "basketball_nba":
            nba_model = _estimate_nba_possession_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "conservative",
            )
        elif sport in {"basketball_wnba", "basketball_ncaab", "basketball_ncaawb"}:
            basketball_model = _estimate_basketball_module_model(
                sport=sport,
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
            if sport == "basketball_wnba":
                wnba_model = basketball_model
            elif sport == "basketball_ncaab":
                mens_cbb_model = basketball_model
            else:
                womens_cbb_model = basketball_model
        elif sport == "americanfootball_nfl":
            nfl_model = _estimate_nfl_drive_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "americanfootball_ncaaf":
            college_football_model = _estimate_college_football_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "baseball_mlb":
            mlb_model = _estimate_mlb_negative_binomial_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "soccer":
            soccer_model = _estimate_soccer_goal_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "icehockey_nhl":
            nhl_model = _estimate_nhl_goal_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "tennis":
            tennis_model = _estimate_tennis_markov_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport in {"mma_mixed_martial_arts", "boxing"}:
            combat_model = _estimate_combat_finish_model(
                sport=sport,
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "golf":
            golf_model = _estimate_golf_course_fit_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )
        elif sport == "cricket":
            cricket_model = _estimate_cricket_run_rate_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "moderate",
            )

        if nba_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif wnba_model or mens_cbb_model or womens_cbb_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif college_football_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif nfl_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif mlb_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif soccer_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif nhl_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif tennis_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif combat_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif golf_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif cricket_model:
            component_status, missing_inputs = COMPONENT_STATUS_ACTIVE, []
        elif sport in {"basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaawb", "americanfootball_nfl", "americanfootball_ncaaf", "baseball_mlb", "soccer", "icehockey_nhl", "tennis", "mma_mixed_martial_arts", "boxing", "golf", "cricket"}:
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _missing_inputs_for_sport(sport, market, input_stats, payload)
        else:
            component_status, missing_inputs = _component_status(config["required_inputs"], input_stats)
        backtest_status = "passed" if input_stats.get("backtest_proof") else "not_started"
        calibration_status = "passed" if input_stats.get("calibration_proof") else "not_started"
        implied_probability = None
        true_probability = _safe_float(input_stats.get("true_probability") or input_stats.get("sport_model_probability"))
        edge = None
        suggested = 0.0
        no_bet_flags = list(config["no_bet_rules"])
        if odds_american is not None:
            implied_probability = implied_probability_from_american(odds_american)
        if nba_model:
            true_probability = nba_model["true_probability"]
            implied_probability = nba_model["implied_probability"]
            edge = nba_model["edge"]
            suggested = nba_model["suggested_stake"]
            no_bet_flags = list(nba_model["no_bet_flags"])
        elif wnba_model or mens_cbb_model or womens_cbb_model:
            basketball_model = wnba_model or mens_cbb_model or womens_cbb_model
            true_probability = basketball_model["true_probability"]
            implied_probability = basketball_model["implied_probability"]
            edge = basketball_model["edge"]
            suggested = basketball_model["suggested_stake"]
            no_bet_flags = list(basketball_model["no_bet_flags"])
        elif college_football_model:
            true_probability = college_football_model["true_probability"]
            implied_probability = college_football_model["implied_probability"]
            edge = college_football_model["edge"]
            suggested = college_football_model["suggested_stake"]
            no_bet_flags = list(college_football_model["no_bet_flags"])
        elif nfl_model:
            true_probability = nfl_model["true_probability"]
            implied_probability = nfl_model["implied_probability"]
            edge = nfl_model["edge"]
            suggested = nfl_model["suggested_stake"]
            no_bet_flags = list(nfl_model["no_bet_flags"])
        elif mlb_model:
            true_probability = mlb_model["true_probability"]
            implied_probability = mlb_model["implied_probability"]
            edge = mlb_model["edge"]
            suggested = mlb_model["suggested_stake"]
            no_bet_flags = list(mlb_model["no_bet_flags"])
        elif soccer_model:
            true_probability = soccer_model["true_probability"]
            implied_probability = soccer_model["implied_probability"]
            edge = soccer_model["edge"]
            suggested = soccer_model["suggested_stake"]
            no_bet_flags = list(soccer_model["no_bet_flags"])
        elif nhl_model:
            true_probability = nhl_model["true_probability"]
            implied_probability = nhl_model["implied_probability"]
            edge = nhl_model["edge"]
            suggested = nhl_model["suggested_stake"]
            no_bet_flags = list(nhl_model["no_bet_flags"])
        elif tennis_model:
            true_probability = tennis_model["true_probability"]
            implied_probability = tennis_model["implied_probability"]
            edge = tennis_model["edge"]
            suggested = tennis_model["suggested_stake"]
            no_bet_flags = list(tennis_model["no_bet_flags"])
        elif combat_model:
            true_probability = combat_model["true_probability"]
            implied_probability = combat_model["implied_probability"]
            edge = combat_model["edge"]
            suggested = combat_model["suggested_stake"]
            no_bet_flags = list(combat_model["no_bet_flags"])
        elif golf_model:
            true_probability = golf_model["true_probability"]
            implied_probability = golf_model["implied_probability"]
            edge = golf_model["edge"]
            suggested = golf_model["suggested_stake"]
            no_bet_flags = list(golf_model["no_bet_flags"])
        elif cricket_model:
            true_probability = cricket_model["true_probability"]
            implied_probability = cricket_model["implied_probability"]
            edge = cricket_model["edge"]
            suggested = cricket_model["suggested_stake"]
            no_bet_flags = list(cricket_model["no_bet_flags"])
        if implied_probability is not None and true_probability is not None and odds_american is not None:
            edge = edge_percentage(true_probability, implied_probability)
            if not (nba_model or wnba_model or mens_cbb_model or womens_cbb_model or college_football_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model or golf_model or cricket_model):
                suggested = suggested_stake_with_risk_controls(
                    bankroll=bankroll,
                    american_odds=odds_american,
                    true_probability=true_probability,
                    risk_profile=payload.get("risk_profile") or "conservative",
                )
        if missing_inputs:
            no_bet_flags = ["required inputs missing", "confirmed bets disabled"] + missing_inputs
        elif component_status == COMPONENT_STATUS_RESEARCH:
            no_bet_flags = ["no backtest proof", "research mode only", "confirmed bets disabled"]
        if input_stats_flags:
            no_bet_flags = list(dict.fromkeys(no_bet_flags + input_stats_flags))

        social_input_stats = dict(input_stats)
        social_input_stats["edge"] = edge
        social_layer = build_social_crowd_calibration_layer(social_input_stats)
        if social_layer["sentiment_no_bet_flags"] and not (nba_model or wnba_model or mens_cbb_model or womens_cbb_model or college_football_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model or golf_model or cricket_model):
            no_bet_flags = list(dict.fromkeys(no_bet_flags + social_layer["sentiment_no_bet_flags"]))

        risk_controller = build_risk_controller(bankroll, unit_size, payload.get("risk_profile") or "conservative")
        detector_payload = dict(payload)
        detector_payload.update({
            "odds_american": odds_american,
            "bankroll": bankroll,
            "unit_size": unit_size,
            "sport_model_probability": true_probability,
            "implied_probability": implied_probability,
            "edge": edge,
            "risk_level": payload.get("risk_profile") or "conservative",
            "selection": payload.get("selection") or payload.get("player_name") or payload.get("home_team"),
        })
        wee_willie = build_wee_willie_market_weakness_detector(detector_payload)
        manual_ticket = build_manual_ticket(detector_payload, suggested)
        active_model = nba_model or wnba_model or mens_cbb_model or womens_cbb_model or college_football_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model or golf_model or cricket_model
        confidence = active_model["confidence"] if active_model else input_stats.get("confidence")
        if tennis_model and _safe_float(confidence) is None:
            confidence = 0.0
            tennis_model["confidence"] = confidence
            if "low confidence" not in no_bet_flags:
                no_bet_flags.append("low confidence")
            suggested = 0
        risk = active_model["risk"] if active_model else payload.get("risk_profile") or "conservative"
        model_status = active_model["model_status"] if active_model else component_status
        edge_threshold, confidence_threshold = (
            _nfl_thresholds(payload.get("risk_profile") or "moderate")
            if (wnba_model or mens_cbb_model or womens_cbb_model or college_football_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model or golf_model or cricket_model)
            else (2.5, 70)
        )
        event_value = payload.get("event_id") or payload.get("event") or input_stats.get("event")
        selection_value = payload.get("selection") or input_stats.get("selection")
        officiating_analysis = build_officiating_analysis(
            sport=sport,
            market=market,
            input_stats=input_stats,
            true_probability=true_probability,
            base_model_active=component_status == COMPONENT_STATUS_ACTIVE and true_probability is not None,
            base_confidence=confidence,
        )
        if tennis_model:
            confidence_value = _safe_float(confidence)
            if confidence_value is not None:
                if confidence_value >= confidence_threshold:
                    no_bet_flags = [flag for flag in no_bet_flags if flag != "low confidence"]
                elif "low confidence" not in no_bet_flags:
                    no_bet_flags.append("low confidence")
            if edge is not None and edge >= edge_threshold:
                no_bet_flags = [flag for flag in no_bet_flags if flag != "edge too small"]
            if edge is not None and edge > 0:
                no_bet_flags = [flag for flag in no_bet_flags if flag != "negative edge"]
            if (
                edge is not None
                and edge >= edge_threshold
                and confidence_value is not None
                and confidence_value >= confidence_threshold
                and suggested <= 0
            ):
                suggested = calculate_suggested_stake(
                    bankroll=bankroll,
                    american_odds=odds_american,
                    true_probability=true_probability,
                    risk_profile=payload.get("risk_profile") or "moderate",
                    confidence=confidence_value,
                )
                tennis_model["suggested_stake"] = suggested
        confirmed_bets = []
        if (
            active_model
            and config.get("confirmed_bets_allowed")
            and not no_bet_flags
            and edge is not None
            and edge >= edge_threshold
            and confidence is not None
            and float(confidence) >= confidence_threshold
            and suggested > 0
        ):
            confirmed_bets = [{
                "sport": sport,
                "event": event_value,
                "market": market,
                "selection": selection_value,
                "odds_american": odds_american,
                "estimated_true_probability": true_probability,
                "implied_probability": implied_probability,
                "edge": edge,
                "confidence": confidence,
                "risk": risk,
                "suggested_stake": suggested,
                "decision": "CONFIRMED_BET",
            }]
        if active_model and not no_bet_flags and not confirmed_bets and suggested <= 0:
            no_bet_flags = ["risk too high"]
        simple_no_bets = [{"reason": flag} for flag in no_bet_flags]
        no_bets = [{
            "sport": sport,
            "event": event_value,
            "market": market,
            "selection": selection_value,
            "reason": flag,
            "no_bet_reason": flag,
            "confidence": confidence,
            "edge_percent": edge,
        } for flag in no_bet_flags]
        if active_model and not no_bet_flags and not confirmed_bets:
            simple_no_bets = [{"reason": "confirmed bet thresholds not satisfied"}]
            no_bets = [{
                "sport": sport,
                "event": event_value,
                "market": market,
                "selection": selection_value,
                "reason": "confirmed bet thresholds not satisfied",
                "no_bet_reason": "confirmed bet thresholds not satisfied",
                "confidence": confidence,
                "edge_percent": edge,
            }]
        evaluated_status = _evaluated_ticket_status(
            component_status=component_status,
            missing_inputs=missing_inputs,
            confirmed_bets=confirmed_bets,
            no_bet_flags=no_bet_flags,
            edge=edge,
            confidence=confidence,
            confidence_threshold=confidence_threshold,
        )
        manual_review_flags: bool | list[Any] = False
        if missing_inputs or component_status != COMPONENT_STATUS_ACTIVE:
            manual_review_flags = [manual_ticket]
        full_board = {
            "confirmed_bets": confirmed_bets,
            "target_lines": [] if component_status == COMPONENT_STATUS_INACTIVE else [{
                "sport": sport,
                "event": event_value,
                "market": market,
                "selection": selection_value,
                "target_price": odds_american,
                "confidence": confidence,
            }],
            "target_props": [{
                "sport": sport,
                "event": event_value,
                "market": market,
                "selection": selection_value,
                "confidence": confidence,
            }] if _normal_market_key(market) in {"player_prop", "knockdown_prop", "takedown_prop", "significant_strikes_prop", "submission_attempt_prop", "birdies_prop", "eagles_prop", "fairways_hit_prop", "greens_in_regulation_prop", "putts_prop", "round_score_prop", *BASKETBALL_MODULE_PROP_MARKETS, *COLLEGE_FOOTBALL_PROP_MARKETS, *CRICKET_PROP_MARKETS} else [],
            "target_alt_lines": [{
                "sport": sport,
                "event": event_value,
                "market": market,
                "selection": selection_value,
                "target_price": odds_american,
                "confidence": confidence,
            }] if _normal_market_key(market) == "alt_line" and component_status != COMPONENT_STATUS_INACTIVE else [],
            "no_bets": no_bets,
            "best_correlated_parlay": None,
            "value_ranking": [],
            "risk_ranking": [{"selection": selection_value, "risk": risk, "confidence": confidence}] if active_model else [],
            "missing_inputs": missing_inputs,
            "manual_review_required": manual_review_flags,
            "logbook_ready_rows": [manual_ticket["logbook_ready_row"]],
        }
        manual_ticket["status"] = evaluated_status
        logbook_ready_row = manual_ticket["logbook_ready_row"]
        logbook_ready_row.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sport_key": sport,
            "sportsbook": payload.get("sportsbook"),
            "line": payload.get("line") if payload.get("line") is not None else input_stats.get("line"),
            "total_line": payload.get("total_line") if payload.get("total_line") is not None else input_stats.get("total_line"),
            "team_total_line": payload.get("team_total_line") if payload.get("team_total_line") is not None else input_stats.get("team_total_line"),
            "model_name": config["model_used"],
            "model_status": model_status,
            "final_probability": true_probability,
            "model_probability": true_probability,
            "implied_probability": implied_probability,
            "edge_percent": edge,
            "confidence": confidence,
            "suggested_stake": suggested if confirmed_bets else 0,
            "stake": suggested if confirmed_bets else 0,
            "decision": "CONFIRMED_BET" if confirmed_bets else "NO_BET",
            "status": evaluated_status,
            **officiating_analysis["officiating_logbook_fields"],
        })
        basketball_module_model = wnba_model or mens_cbb_model or womens_cbb_model
        probability_model = basketball_module_model or college_football_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model or golf_model or cricket_model
        if probability_model:
            logbook_ready_row.update({
                "raw_model_probability": probability_model["raw_model_probability"],
                "calibrated_model_probability": probability_model["calibrated_model_probability"],
                "probability_calibration_applied": probability_model["probability_calibration_applied"],
                "probability_sanity_flags": probability_model["probability_sanity_flags"],
                "market_anchor_probability": probability_model["market_anchor_probability"],
            })
        if mlb_model:
            logbook_ready_row.update({
                "projected_team_runs": mlb_model["projected_team_runs"],
                "projected_opponent_runs": mlb_model["projected_opponent_runs"],
                "projected_total_runs": mlb_model["projected_total_runs"],
                "projected_run_differential": mlb_model["projected_run_differential"],
            })
        if soccer_model:
            logbook_ready_row.update({
                "league": payload.get("league") or input_stats.get("league"),
                "team_lambda": soccer_model["team_lambda"],
                "opponent_lambda": soccer_model["opponent_lambda"],
                "projected_team_goals": soccer_model["projected_team_goals"],
                "projected_opponent_goals": soccer_model["projected_opponent_goals"],
                "projected_total_goals": soccer_model["projected_total_goals"],
                "projected_goal_differential": soccer_model["projected_goal_differential"],
                "draw_probability": soccer_model["draw_probability"],
                "btts_probability": soccer_model["btts_probability"],
                "dixon_coles_adjustment_applied": soccer_model["dixon_coles_adjustment_applied"],
                "bivariate_poisson_adjustment_applied": soccer_model["bivariate_poisson_adjustment_applied"],
                "time_decay_applied": soccer_model["time_decay_applied"],
            })
        if nhl_model:
            logbook_ready_row.update({
                "league": payload.get("league") or input_stats.get("league"),
                "team_lambda": nhl_model["team_lambda"],
                "opponent_lambda": nhl_model["opponent_lambda"],
                "projected_team_goals": nhl_model["projected_team_goals"],
                "projected_opponent_goals": nhl_model["projected_opponent_goals"],
                "projected_total_goals": nhl_model["projected_total_goals"],
                "projected_goal_differential": nhl_model["projected_goal_differential"],
                "regulation_draw_probability": nhl_model["regulation_draw_probability"],
                "overtime_probability": nhl_model["overtime_probability"],
                "shootout_adjustment_probability": nhl_model["shootout_adjustment_probability"],
                "bivariate_poisson_adjustment_applied": nhl_model["bivariate_poisson_adjustment_applied"],
                "goalie_adjustment_applied": nhl_model["goalie_adjustment_applied"],
                "goalie_risk_flags": nhl_model["goalie_risk_flags"],
                "special_teams_adjustment_applied": nhl_model["special_teams_adjustment_applied"],
                "period_lambda_adjustment_applied": nhl_model["period_lambda_adjustment_applied"],
                "time_decay_applied": nhl_model["time_decay_applied"],
            })
        if tennis_model:
            logbook_ready_row.update({
                "league": payload.get("league") or input_stats.get("league"),
                "tournament": input_stats.get("tournament"),
                "surface": input_stats.get("surface"),
                "player_strength_rating": tennis_model["player_strength_rating"],
                "opponent_strength_rating": tennis_model["opponent_strength_rating"],
                "player_surface_edge": tennis_model["player_surface_edge"],
                "serve_edge": tennis_model["serve_edge"],
                "return_edge": tennis_model["return_edge"],
                "player_hold_probability": tennis_model["player_hold_probability"],
                "opponent_hold_probability": tennis_model["opponent_hold_probability"],
                "player_break_probability": tennis_model["player_break_probability"],
                "opponent_break_probability": tennis_model["opponent_break_probability"],
                "player_set_probability": tennis_model["player_set_probability"],
                "player_match_probability": tennis_model["player_match_probability"],
                "first_set_probability": tennis_model["first_set_probability"],
                "tiebreak_probability": tennis_model["tiebreak_probability"],
                "markov_model_applied": tennis_model["markov_model_applied"],
                "surface_adjustment_applied": tennis_model["surface_adjustment_applied"],
                "fatigue_adjustment_applied": tennis_model["fatigue_adjustment_applied"],
                "injury_adjustment_applied": tennis_model["injury_adjustment_applied"],
                "weather_adjustment_applied": tennis_model["weather_adjustment_applied"],
            })
        if combat_model:
            logbook_ready_row.update({
                "model_level": config["model_level"],
                "probability_type": _normal_market_key(market),
                "risk_profile": payload.get("risk_profile") or "moderate",
                "fighter_win_probability": combat_model["fighter_win_probability"],
                "opponent_win_probability": combat_model["opponent_win_probability"],
                "ko_tko_probability": combat_model["ko_tko_probability"],
                "submission_probability": combat_model["submission_probability"],
                "decision_probability": combat_model["decision_probability"],
                "goes_distance_probability": combat_model["goes_distance_probability"],
                "does_not_go_distance_probability": combat_model["does_not_go_distance_probability"],
                "over_rounds_probability": combat_model["over_rounds_probability"],
                "under_rounds_probability": combat_model["under_rounds_probability"],
                "calibration_applied": combat_model["probability_calibration_applied"],
                "risk_flags": combat_model["risk_flags"],
                "notes": "; ".join(combat_model["risk_flags"]) if combat_model["risk_flags"] else "",
            })
        if golf_model:
            logbook_ready_row.update({
                "model_level": config["model_level"],
                "probability_type": _normal_market_key(market),
                "risk_profile": payload.get("risk_profile") or "moderate",
                "player_strength_score": golf_model["player_strength_score"],
                "field_size": golf_model["field_size"],
                "outright_win_probability": golf_model["outright_win_probability"],
                "top_5_probability": golf_model["top_5_probability"],
                "top_10_probability": golf_model["top_10_probability"],
                "top_20_probability": golf_model["top_20_probability"],
                "make_cut_probability": golf_model["make_cut_probability"],
                "miss_cut_probability": golf_model["miss_cut_probability"],
                "calibration_applied": golf_model["probability_calibration_applied"],
                "risk_flags": golf_model["risk_flags"],
                "notes": "; ".join(golf_model["risk_flags"]) if golf_model["risk_flags"] else "",
            })
        if cricket_model:
            logbook_ready_row.update({
                "model_level": config["model_level"],
                "probability_type": _normal_market_key(market),
                "risk_profile": payload.get("risk_profile") or "moderate",
                "league_calibration_applied": cricket_model["league_calibration_applied"],
                "format_calibration_applied": cricket_model["format_calibration_applied"],
                "projected_team_runs": cricket_model["projected_team_runs"],
                "projected_opponent_runs": cricket_model["projected_opponent_runs"],
                "projected_total_runs": cricket_model["projected_total_runs"],
                "risk_flags": cricket_model["risk_flags"],
                "missing_inputs": missing_inputs,
                "notes": "; ".join(cricket_model["risk_flags"]) if cricket_model["risk_flags"] else "",
            })
        if college_football_model:
            logbook_ready_row.update({
                "league_calibration_applied": college_football_model["league_calibration_applied"],
                "projected_margin": college_football_model["projected_margin"],
                "projected_total": college_football_model["projected_total"],
                "projected_team_points": college_football_model["projected_team_points"],
                "projected_opponent_points": college_football_model["projected_opponent_points"],
                "risk_flags": college_football_model["risk_flags"],
            })
        if nfl_model:
            logbook_ready_row.update({
                "projected_margin": nfl_model["projected_margin"],
                "projected_total": nfl_model["projected_total"],
                "projected_team_points": nfl_model["projected_team_points"],
                "projected_opponent_points": nfl_model["projected_opponent_points"],
            })
        if nba_model:
            logbook_ready_row.update({
                "projected_team_score": nba_model["projected_score"]["team"],
                "projected_opponent_score": nba_model["projected_score"]["opponent"],
                "projected_total": round(nba_model["projected_score"]["team"] + nba_model["projected_score"]["opponent"], 2),
                "projected_margin": nba_model["projected_score"]["estimated_margin"],
                "raw_model_probability": true_probability,
                "calibrated_model_probability": true_probability,
                "probability_calibration_applied": False,
                "probability_sanity_flags": [],
            })
        if basketball_module_model:
            logbook_ready_row.update({
                "league_calibration_applied": basketball_module_model["league_calibration_applied"],
                "projected_margin": basketball_module_model["projected_margin"],
                "projected_total": basketball_module_model["projected_total"],
                "projected_team_points": basketball_module_model["projected_team_points"],
                "projected_opponent_points": basketball_module_model["projected_opponent_points"],
                "risk_flags": basketball_module_model["risk_flags"],
            })
        officiating_fields = {key: officiating_analysis[key] for key in [
            "officiating_module_status",
            "officiating_edge_detected",
            "officiating_adjustment_probability_points",
            "adjusted_true_probability",
            "affected_markets",
            "officiating_confidence",
            "officiating_risk_flags",
            "officiating_summary",
            "officiating_no_bet_reason",
            "officiating_logbook_fields",
        ]}
        return {
            "ok": True,
            "endpoint": "analyzeSportModel",
            "sport": sport,
            "model_name": config["model_used"],
            "model_used": config["model_used"],
            "model_family": config["model_family"],
            "market": market,
            "projected_score": nba_model["projected_score"] if nba_model else input_stats.get("projected_score"),
            "projected_margin": basketball_module_model["projected_margin"] if basketball_module_model else (college_football_model["projected_margin"] if college_football_model else (nfl_model["projected_margin"] if nfl_model else (nba_model["projected_score"]["estimated_margin"] if nba_model else input_stats.get("projected_margin")))),
            "projected_total": basketball_module_model["projected_total"] if basketball_module_model else (college_football_model["projected_total"] if college_football_model else (nfl_model["projected_total"] if nfl_model else input_stats.get("projected_total"))),
            "projected_team_points": basketball_module_model["projected_team_points"] if basketball_module_model else (college_football_model["projected_team_points"] if college_football_model else (nfl_model["projected_team_points"] if nfl_model else None)),
            "projected_opponent_points": basketball_module_model["projected_opponent_points"] if basketball_module_model else (college_football_model["projected_opponent_points"] if college_football_model else (nfl_model["projected_opponent_points"] if nfl_model else None)),
            "projected_team_runs": (mlb_model or cricket_model)["projected_team_runs"] if (mlb_model or cricket_model) else None,
            "projected_opponent_runs": (mlb_model or cricket_model)["projected_opponent_runs"] if (mlb_model or cricket_model) else None,
            "projected_total_runs": (mlb_model or cricket_model)["projected_total_runs"] if (mlb_model or cricket_model) else None,
            "projected_run_differential": (mlb_model or cricket_model)["projected_run_differential"] if (mlb_model or cricket_model) else None,
            "team_lambda": (soccer_model or nhl_model)["team_lambda"] if (soccer_model or nhl_model) else None,
            "opponent_lambda": (soccer_model or nhl_model)["opponent_lambda"] if (soccer_model or nhl_model) else None,
            "projected_team_goals": (soccer_model or nhl_model)["projected_team_goals"] if (soccer_model or nhl_model) else None,
            "projected_opponent_goals": (soccer_model or nhl_model)["projected_opponent_goals"] if (soccer_model or nhl_model) else None,
            "projected_total_goals": (soccer_model or nhl_model)["projected_total_goals"] if (soccer_model or nhl_model) else None,
            "projected_goal_differential": (soccer_model or nhl_model)["projected_goal_differential"] if (soccer_model or nhl_model) else None,
            "draw_probability": soccer_model["draw_probability"] if soccer_model else None,
            "btts_probability": soccer_model["btts_probability"] if soccer_model else None,
            "dixon_coles_adjustment_applied": soccer_model["dixon_coles_adjustment_applied"] if soccer_model else False,
            "regulation_draw_probability": nhl_model["regulation_draw_probability"] if nhl_model else None,
            "overtime_probability": nhl_model["overtime_probability"] if nhl_model else None,
            "shootout_adjustment_probability": nhl_model["shootout_adjustment_probability"] if nhl_model else None,
            "bivariate_poisson_adjustment_applied": (soccer_model or nhl_model)["bivariate_poisson_adjustment_applied"] if (soccer_model or nhl_model) else False,
            "goalie_adjustment_applied": nhl_model["goalie_adjustment_applied"] if nhl_model else False,
            "goalie_risk_flags": nhl_model["goalie_risk_flags"] if nhl_model else [],
            "special_teams_adjustment_applied": nhl_model["special_teams_adjustment_applied"] if nhl_model else False,
            "period_lambda_adjustment_applied": nhl_model["period_lambda_adjustment_applied"] if nhl_model else False,
            "time_decay_applied": (soccer_model or nhl_model)["time_decay_applied"] if (soccer_model or nhl_model) else False,
            "player_strength_rating": tennis_model["player_strength_rating"] if tennis_model else None,
            "opponent_strength_rating": tennis_model["opponent_strength_rating"] if tennis_model else None,
            "player_surface_edge": tennis_model["player_surface_edge"] if tennis_model else None,
            "serve_edge": tennis_model["serve_edge"] if tennis_model else None,
            "return_edge": tennis_model["return_edge"] if tennis_model else None,
            "player_hold_probability": tennis_model["player_hold_probability"] if tennis_model else None,
            "opponent_hold_probability": tennis_model["opponent_hold_probability"] if tennis_model else None,
            "player_break_probability": tennis_model["player_break_probability"] if tennis_model else None,
            "opponent_break_probability": tennis_model["opponent_break_probability"] if tennis_model else None,
            "player_set_probability": tennis_model["player_set_probability"] if tennis_model else None,
            "player_match_probability": tennis_model["player_match_probability"] if tennis_model else None,
            "first_set_probability": tennis_model["first_set_probability"] if tennis_model else None,
            "tiebreak_probability": tennis_model["tiebreak_probability"] if tennis_model else None,
            "markov_model_applied": tennis_model["markov_model_applied"] if tennis_model else False,
            "surface_adjustment_applied": tennis_model["surface_adjustment_applied"] if tennis_model else False,
            "fatigue_adjustment_applied": tennis_model["fatigue_adjustment_applied"] if tennis_model else False,
            "injury_adjustment_applied": tennis_model["injury_adjustment_applied"] if tennis_model else False,
            "weather_adjustment_applied": tennis_model["weather_adjustment_applied"] if tennis_model else False,
            "true_probability": true_probability,
            "estimated_true_probability": true_probability,
            "final_probability": true_probability,
            "model_probability": true_probability,
            "raw_model_probability": probability_model["raw_model_probability"] if probability_model else true_probability,
            "calibrated_model_probability": probability_model["calibrated_model_probability"] if probability_model else true_probability,
            "probability_calibration_applied": probability_model["probability_calibration_applied"] if probability_model else False,
            "probability_sanity_flags": probability_model["probability_sanity_flags"] if probability_model else [],
            "probability_cap_reason": probability_model["probability_cap_reason"] if probability_model else None,
            "market_anchor_probability": probability_model["market_anchor_probability"] if probability_model else implied_probability,
            "implied_probability": implied_probability,
            "edge": edge,
            "edge_percent": edge,
            "confidence": confidence,
            "risk": risk,
            "risk_level": risk,
            "model_status": model_status,
            "status": evaluated_status,
            "decision": "CONFIRMED_BET" if confirmed_bets else "NO_BET",
            "partial_model_mode": bool(missing_inputs or true_probability is None),
            **normalization_diagnostics,
            "nba_input_contract": deepcopy(NBA_INPUT_CONTRACT) if sport == "basketball_nba" else None,
            "nfl_input_contract": deepcopy(NFL_INPUT_CONTRACT) if sport == "americanfootball_nfl" else None,
            "college_football_input_contract": deepcopy(COLLEGE_FOOTBALL_INPUT_CONTRACT) if sport == "americanfootball_ncaaf" else None,
            "mlb_input_contract": deepcopy(MLB_INPUT_CONTRACT) if sport == "baseball_mlb" else None,
            "soccer_input_contract": deepcopy(SOCCER_INPUT_CONTRACT) if sport == "soccer" else None,
            "nhl_input_contract": deepcopy(NHL_INPUT_CONTRACT) if sport == "icehockey_nhl" else None,
            "tennis_input_contract": deepcopy(TENNIS_INPUT_CONTRACT) if sport == "tennis" else None,
            "combat_input_contract": deepcopy(COMBAT_INPUT_CONTRACT) if sport in {"mma_mixed_martial_arts", "boxing"} else None,
            "golf_input_contract": deepcopy(GOLF_INPUT_CONTRACT) if sport == "golf" else None,
            "cricket_input_contract": deepcopy(CRICKET_INPUT_CONTRACT) if sport == "cricket" else None,
            "wnba_input_contract": deepcopy(WNBA_INPUT_CONTRACT) if sport == "basketball_wnba" else None,
            "mens_college_basketball_input_contract": deepcopy(MENS_COLLEGE_BASKETBALL_INPUT_CONTRACT) if sport == "basketball_ncaab" else None,
            "womens_college_basketball_input_contract": deepcopy(WOMENS_COLLEGE_BASKETBALL_INPUT_CONTRACT) if sport == "basketball_ncaawb" else None,
            "league_calibration_applied": (basketball_module_model or college_football_model or cricket_model)["league_calibration_applied"] if (basketball_module_model or college_football_model or cricket_model) else config.get("sport_parameters", {}).get("league_calibration_applied"),
            "format_calibration_applied": cricket_model["format_calibration_applied"] if cricket_model else None,
            "input_coverage": active_model.get("input_coverage") if active_model else None,
            "suggested_stake": suggested if confirmed_bets else 0,
            "recommended_unit_size": risk_controller["recommended_unit_size"],
            "no_bet_flags": no_bet_flags,
            "correlation_notes": config["correlation_notes"],
            "model_components": config["model_components"],
            "missing_inputs": missing_inputs,
            "backtest_status": backtest_status,
            "calibration_status": calibration_status,
            "logbook_ready_row": logbook_ready_row,
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
            "officiating_analysis": officiating_analysis,
            **officiating_fields,
            "provider_enrichment": active_model.get("provider_enrichment") if active_model else {"provider_status": "not_provided", "provider_enrichment_present": []},
            "fighter_win_probability": combat_model["fighter_win_probability"] if combat_model else None,
            "opponent_win_probability": combat_model["opponent_win_probability"] if combat_model else None,
            "ko_tko_probability": combat_model["ko_tko_probability"] if combat_model else None,
            "submission_probability": combat_model["submission_probability"] if combat_model else None,
            "decision_probability": combat_model["decision_probability"] if combat_model else None,
            "goes_distance_probability": combat_model["goes_distance_probability"] if combat_model else None,
            "does_not_go_distance_probability": combat_model["does_not_go_distance_probability"] if combat_model else None,
            "over_rounds_probability": combat_model["over_rounds_probability"] if combat_model else None,
            "under_rounds_probability": combat_model["under_rounds_probability"] if combat_model else None,
            "risk_flags": combat_model["risk_flags"] if combat_model else [],
            "player_strength_score": golf_model["player_strength_score"] if golf_model else None,
            "outright_win_probability": golf_model["outright_win_probability"] if golf_model else None,
            "top_5_probability": golf_model["top_5_probability"] if golf_model else None,
            "top_10_probability": golf_model["top_10_probability"] if golf_model else None,
            "top_20_probability": golf_model["top_20_probability"] if golf_model else None,
            "make_cut_probability": golf_model["make_cut_probability"] if golf_model else None,
            "miss_cut_probability": golf_model["miss_cut_probability"] if golf_model else None,
            "cricket_projected_team_runs": cricket_model["projected_team_runs"] if cricket_model else None,
            "cricket_projected_opponent_runs": cricket_model["projected_opponent_runs"] if cricket_model else None,
            "manual_ticket_preview": manual_ticket,
            "manual_review_required": manual_review_flags,
            "full_board_preview": full_board,
        "confirmed_bets": confirmed_bets,
        "target_lines": full_board["target_lines"],
        "target_props": full_board["target_props"],
        "target_alt_lines": full_board["target_alt_lines"],
        "no_bets": no_bets if (basketball_module_model or college_football_model or tennis_model or combat_model or golf_model or cricket_model) else simple_no_bets,
        "best_correlated_parlay": full_board["best_correlated_parlay"],
        "value_ranking": full_board["value_ranking"],
        "risk_ranking": full_board["risk_ranking"],
        "logbook_ready_rows": [logbook_ready_row],
        "supported_sport_keys": list(OFFICIAL_SPORT_KEYS),
        "error": None,
        "detail": None,
        }
    except Exception as exc:
        sport = payload.get("sport") if isinstance(payload, dict) else None
        return sport_analysis_failed_response(
            sport=sport,
            detail=f"Sport analysis failed safely: {type(exc).__name__}",
        )


def _unsupported_sport_response(payload: dict[str, Any]) -> dict[str, Any]:
    sport = payload.get("sport")
    risk_controller = build_risk_controller(payload.get("bankroll"), payload.get("unit_size"), payload.get("risk_profile") or "conservative")
    social_layer = build_social_crowd_calibration_layer({})
    officiating_analysis = {
        "officiating_module_status": "no_adjustment",
        "officiating_edge_detected": False,
        "officiating_adjustment_probability_points": 0.0,
        "adjusted_true_probability": None,
        "affected_markets": [],
        "officiating_confidence": 0,
        "officiating_risk_flags": ["unsupported sport"],
        "officiating_summary": "officiating layer skipped for unsupported sport",
        "officiating_no_bet_reason": "unsupported sport",
        "officiating_logbook_fields": {},
    }
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
        "supported_sport_keys": list(OFFICIAL_SPORT_KEYS),
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
        "officiating_analysis": officiating_analysis,
        **{key: officiating_analysis[key] for key in [
            "officiating_module_status",
            "officiating_edge_detected",
            "officiating_adjustment_probability_points",
            "adjusted_true_probability",
            "affected_markets",
            "officiating_confidence",
            "officiating_risk_flags",
            "officiating_summary",
            "officiating_no_bet_reason",
            "officiating_logbook_fields",
        ]},
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
        "target_lines": [],
        "no_bets": [{"reason": "unsupported sport"}],
        "error": "UNSUPPORTED_SPORT",
        "detail": f"Unsupported sport key: {sport}. Supported sport keys: {', '.join(OFFICIAL_SPORT_KEYS)}",
    }


_validate_registry()
