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
    "ncaab": "basketball_ncaab",
    "nfl": "americanfootball_nfl",
    "cfb": "americanfootball_ncaaf",
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
        input_stats, input_stats_flags = _normalize_input_stats(payload.get("input_stats"))
        if sport == "tennis":
            input_stats = _normalize_tennis_input_aliases(input_stats)
        elif sport in {"mma_mixed_martial_arts", "boxing"}:
            input_stats = _normalize_combat_input_aliases(input_stats, payload, sport)
        odds_american = _safe_float(payload.get("odds_american"))
        bankroll = _safe_float(payload.get("bankroll"), 0) or 0
        unit_size = _safe_float(payload.get("unit_size"), 0) or 0
        if not config:
            response = _unsupported_sport_response(payload)
            if input_stats_flags:
                response["no_bet_flags"] = list(dict.fromkeys(response["no_bet_flags"] + input_stats_flags))
            return response

        nba_model = None
        nfl_model = None
        mlb_model = None
        soccer_model = None
        nhl_model = None
        tennis_model = None
        combat_model = None
        if sport == "basketball_nba":
            nba_model = _estimate_nba_possession_model(
                input_stats=input_stats,
                payload=payload,
                market=market,
                odds_american=odds_american,
                bankroll=bankroll,
                risk_profile=payload.get("risk_profile") or "conservative",
            )
        elif sport == "americanfootball_nfl":
            nfl_model = _estimate_nfl_drive_model(
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

        if nba_model:
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
        elif sport == "basketball_nba":
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _nba_full_inputs_missing(input_stats) + _nba_market_specific_missing(market, input_stats, payload)
        elif sport == "americanfootball_nfl":
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _nfl_full_inputs_missing(input_stats) + _nfl_market_specific_missing(market, input_stats, payload)
        elif sport == "baseball_mlb":
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _mlb_full_inputs_missing(input_stats, payload) + _mlb_market_specific_missing(market, input_stats, payload)
        elif sport == "soccer":
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _soccer_full_inputs_missing(input_stats, payload) + _soccer_market_specific_missing(market, input_stats, payload)
        elif sport == "icehockey_nhl":
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _nhl_full_inputs_missing(input_stats, payload) + _nhl_market_specific_missing(market, input_stats, payload)
        elif sport == "tennis":
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _tennis_full_inputs_missing(input_stats, payload) + _tennis_market_specific_missing(market, input_stats, payload)
        elif sport in {"mma_mixed_martial_arts", "boxing"}:
            component_status = COMPONENT_STATUS_INACTIVE
            missing_inputs = _combat_full_inputs_missing(input_stats, payload) + _combat_market_specific_missing(market, input_stats, payload)
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
        if implied_probability is not None and true_probability is not None and odds_american is not None:
            edge = edge_percentage(true_probability, implied_probability)
            if not (nba_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model):
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
        if social_layer["sentiment_no_bet_flags"] and not (nba_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model):
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
        active_model = nba_model or nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model
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
            if (nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model)
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
            }] if _normal_market_key(market) in {"player_prop", "knockdown_prop", "takedown_prop", "significant_strikes_prop", "submission_attempt_prop"} else [],
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
        probability_model = nfl_model or mlb_model or soccer_model or nhl_model or tennis_model or combat_model
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
            "projected_margin": nfl_model["projected_margin"] if nfl_model else (nba_model["projected_score"]["estimated_margin"] if nba_model else input_stats.get("projected_margin")),
            "projected_total": nfl_model["projected_total"] if nfl_model else input_stats.get("projected_total"),
            "projected_team_points": nfl_model["projected_team_points"] if nfl_model else None,
            "projected_opponent_points": nfl_model["projected_opponent_points"] if nfl_model else None,
            "projected_team_runs": mlb_model["projected_team_runs"] if mlb_model else None,
            "projected_opponent_runs": mlb_model["projected_opponent_runs"] if mlb_model else None,
            "projected_total_runs": mlb_model["projected_total_runs"] if mlb_model else None,
            "projected_run_differential": mlb_model["projected_run_differential"] if mlb_model else None,
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
            "nba_input_contract": deepcopy(NBA_INPUT_CONTRACT) if sport == "basketball_nba" else None,
            "nfl_input_contract": deepcopy(NFL_INPUT_CONTRACT) if sport == "americanfootball_nfl" else None,
            "mlb_input_contract": deepcopy(MLB_INPUT_CONTRACT) if sport == "baseball_mlb" else None,
            "soccer_input_contract": deepcopy(SOCCER_INPUT_CONTRACT) if sport == "soccer" else None,
            "nhl_input_contract": deepcopy(NHL_INPUT_CONTRACT) if sport == "icehockey_nhl" else None,
            "tennis_input_contract": deepcopy(TENNIS_INPUT_CONTRACT) if sport == "tennis" else None,
            "combat_input_contract": deepcopy(COMBAT_INPUT_CONTRACT) if sport in {"mma_mixed_martial_arts", "boxing"} else None,
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
            "manual_ticket_preview": manual_ticket,
            "manual_review_required": manual_review_flags,
            "full_board_preview": full_board,
        "confirmed_bets": confirmed_bets,
        "target_lines": full_board["target_lines"],
        "target_props": full_board["target_props"],
        "target_alt_lines": full_board["target_alt_lines"],
        "no_bets": no_bets if (tennis_model or combat_model) else simple_no_bets,
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
