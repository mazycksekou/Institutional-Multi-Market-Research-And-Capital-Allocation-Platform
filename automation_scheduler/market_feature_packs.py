"""Market feature packs – repo‑wide market‑type readiness layer.

MARKET_FEATURE_PACKS_VERSION = "10H14"

This module defines canonical market‑family keys, their feature packs,
normalisation helpers, and readiness evaluation functions.
No SQLite changes, no bankroll maths, no network calls, no scraping.
Data leakage fields are explicitly blocked from pre‑decision features.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Version & never‑leak fields
# ---------------------------------------------------------------------------

MARKET_FEATURE_PACKS_VERSION: str = "10H14"

MARKET_FEATURE_NEVER_FEATURE_FIELDS: list[str] = [
    "final_result",
    "winner",
    "home_score",
    "away_score",
    "profit_loss",
    "closing_odds",
    "closing_line",
    "clv",
    "result",
    "settled_result",
    "bet_result",
    "outcome",
]

# ---------------------------------------------------------------------------
# Helper internal – required / recommended / optional sets builders
# ---------------------------------------------------------------------------

_BASE_REQUIRED: list[str] = [
    "sport",
    "event_date",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
]

_BASE_RECOMMENDED: list[str] = [
    "home_team",
    "away_team",
    "bookmaker",
    "opening_odds",
    "closing_odds",
    "implied_probability",
    "line_movement_signal",
    "volatility_level",
]

# ---------------------------------------------------------------------------
# Master market pack registry
# ---------------------------------------------------------------------------

MARKET_FEATURE_PACKS: dict[str, dict[str, Any]] = {
    # ── Winner markets ──────────────────────────────────────────────────
    "moneyline_or_1x2": {
        "market_family": "moneyline_or_1x2",
        "display_name": "Moneyline / 1X2",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": _BASE_RECOMMENDED,
        "optional_fields": ["home_or_away", "three_way"],
        "missing_data_warning": "Moneyline markets need at least odds and implied probability.",
        "operator_interpretation": (
            "Full depth – standard winner markets have robust odds availability."
        ),
    },
    # ── Spread / handicap ────────────────────────────────────────────────
    "spread_or_handicap": {
        "market_family": "spread_or_handicap",
        "display_name": "Spread / Handicap",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": _BASE_RECOMMENDED + [
            "opening_line", "closing_line", "spread_line", "handicap",
            "line_movement_signal", "volatility_level",
        ],
        "optional_fields": ["home_or_away", "three_way"],
        "missing_data_warning": "Line value is critical for spread analysis.",
        "operator_interpretation": (
            "Full depth – spread markets have line and odds data."
        ),
    },
    "runline": {
        "market_family": "runline",
        "display_name": "Runline (Baseball)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": _BASE_RECOMMENDED + [
            "opening_line", "closing_line", "run_line",
            "line_movement_signal", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Runline is baseball‐specific; line value required.",
        "operator_interpretation": (
            "Full depth – runline markets are covered by spread pack."
        ),
    },
    "puckline": {
        "market_family": "puckline",
        "display_name": "Puckline (Hockey)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": _BASE_RECOMMENDED + [
            "opening_line", "closing_line", "puck_line",
            "line_movement_signal", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Puckline is hockey‐specific; line value required.",
        "operator_interpretation": (
            "Full depth – puckline markets are covered by spread pack."
        ),
    },
    "asian_handicap": {
        "market_family": "asian_handicap",
        "display_name": "Asian Handicap",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": _BASE_RECOMMENDED + [
            "opening_line", "closing_line", "asian_line",
            "line_movement_signal", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Asian handicap may require understanding of quarter‐goal lines.",
        "operator_interpretation": (
            "Standard depth – Asian handicap markets require line value."
        ),
    },
    # ── Totals ────────────────────────────────────────────────────────────
    "game_total": {
        "market_family": "game_total",
        "display_name": "Game Total (Over/Under)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": _BASE_RECOMMENDED + [
            "opening_total", "closing_total", "total_line",
            "pace_context", "weather",
            "line_movement_signal", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Line value is crucial for totals analysis.",
        "operator_interpretation": (
            "Full depth – game totals have pace and weather context."
        ),
    },
    "team_total": {
        "market_family": "team_total",
        "display_name": "Team Total",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["team_name", "line_value"],
        "recommended_fields": [
            "opponent_team", "bookmaker", "opening_total", "closing_total",
            "pace_context", "matchup_context",
            "line_movement_signal", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Team total needs team_name and line value.",
        "operator_interpretation": (
            "Full depth – team totals have pace and matchup data."
        ),
    },
    "period_total": {
        "market_family": "period_total",
        "display_name": "Period Total (Quarter/Half/Inning)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "period_context",
            "opening_total", "closing_total", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Period totals need period context.",
        "operator_interpretation": (
            "Standard depth – period totals require period and line value."
        ),
    },
    # ── Player props ───────────────────────────────────────────────────
    "player_prop": {
        "market_family": "player_prop",
        "display_name": "Player Prop (Generic)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "minutes_projection", "usage_rate", "matchup_context",
            "injury_status", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player name and line value are required.",
        "operator_interpretation": (
            "Full depth – player props have usage and matchup data."
        ),
    },
    "player_points_prop": {
        "market_family": "player_points_prop",
        "display_name": "Player Points Prop",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "minutes_projection", "usage_rate", "matchup_context",
            "injury_status", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player points prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – points props have usage and matchup data."
        ),
    },
    "player_rebounds_prop": {
        "market_family": "player_rebounds_prop",
        "display_name": "Player Rebounds Prop",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "minutes_projection", "usage_rate", "matchup_context",
            "injury_status", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player rebounds prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – rebounds props have usage and matchup data."
        ),
    },
    "player_assists_prop": {
        "market_family": "player_assists_prop",
        "display_name": "Player Assists Prop",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "minutes_projection", "usage_rate", "matchup_context",
            "injury_status", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player assists prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – assists props have usage and matchup data."
        ),
    },
    "player_shots_prop": {
        "market_family": "player_shots_prop",
        "display_name": "Player Shots Prop",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "minutes_projection", "usage_rate", "matchup_context",
            "injury_status", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player shots prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – shots props have usage and matchup data."
        ),
    },
    "player_saves_prop": {
        "market_family": "player_saves_prop",
        "display_name": "Player Saves Prop (Hockey/Goalie)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "minutes_projection", "usage_rate", "matchup_context",
            "injury_status", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player saves prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – saves props have usage and matchup data."
        ),
    },
    "player_strikeouts_prop": {
        "market_family": "player_strikeouts_prop",
        "display_name": "Player Strikeouts Prop (Pitcher)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "pitcher_recent_form", "opponent_strikeout_rate",
            "matchup_context", "injury_status",
            "opening_line", "closing_line", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player strikeouts prop needs pitcher name and line.",
        "operator_interpretation": (
            "Full depth – strikeouts props have pitcher and matchup data."
        ),
    },
    "player_bases_prop": {
        "market_family": "player_bases_prop",
        "display_name": "Player Total Bases Prop (Baseball)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "batter_recent_form", "pitcher_matchup",
            "opening_line", "closing_line", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player total bases prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – total bases props have batter and pitcher data."
        ),
    },
    "player_touchdowns_prop": {
        "market_family": "player_touchdowns_prop",
        "display_name": "Player Touchdowns Prop (Football)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["player_name", "line_value"],
        "recommended_fields": [
            "team_name", "opponent_team", "prop_type",
            "touchdown_rate", "red_zone_usage", "injury_status",
            "opening_line", "closing_line", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Player touchdowns prop needs player name and line.",
        "operator_interpretation": (
            "Full depth – touchdown props have red zone and usage data."
        ),
    },
    # ── Combat markets ─────────────────────────────────────────────────
    "fight_moneyline": {
        "market_family": "fight_moneyline",
        "display_name": "Fight Moneyline",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "fighter_name", "opponent_name", "weight_class",
            "method", "round_number", "fight_format",
            "reach", "stance", "recent_form", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Fighter moneyline needs at least odds.",
        "operator_interpretation": (
            "Full depth – fight moneyline has fighter form and physical data."
        ),
    },
    "fight_method": {
        "market_family": "fight_method",
        "display_name": "Fight Method of Victory",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "fighter_name", "opponent_name", "weight_class",
            "method", "round_number", "fight_format",
            "reach", "stance", "recent_form", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Fight method markets need odds and fighter context.",
        "operator_interpretation": (
            "Full depth – fight method has fighter and format data."
        ),
    },
    "fight_round": {
        "market_family": "fight_round",
        "display_name": "Fight Round Betting",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "fighter_name", "opponent_name", "weight_class",
            "method", "round_number", "fight_format",
            "reach", "stance", "recent_form", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Fight round markets need odds and fighter context.",
        "operator_interpretation": (
            "Full depth – fight round markets have fighter and round data."
        ),
    },
    "fight_total_rounds": {
        "market_family": "fight_total_rounds",
        "display_name": "Fight Total Rounds (Over/Under)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "fighter_name", "opponent_name", "weight_class",
            "method", "round_number", "fight_format",
            "reach", "stance", "recent_form", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Fight total rounds needs line value.",
        "operator_interpretation": (
            "Full depth – fight total rounds has line value and fighter data."
        ),
    },
    "fighter_prop": {
        "market_family": "fighter_prop",
        "display_name": "Fighter Prop (Generic)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "fighter_name", "opponent_name", "weight_class",
            "method", "round_number", "fight_format",
            "reach", "stance", "recent_form", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Fighter prop needs odds and fighter context.",
        "operator_interpretation": (
            "Full depth – fighter props have fighter and format data."
        ),
    },
    # ── Outrights / futures ─────────────────────────────────────────────
    "outright": {
        "market_family": "outright",
        "display_name": "Outright Winner",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "season", "tournament", "field_size",
            "participant_context", "opening_odds", "closing_odds",
            "implied_probability", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Outright markets need participant context.",
        "operator_interpretation": (
            "Full depth – outright markets have tournament and field data."
        ),
    },
    "futures": {
        "market_family": "futures",
        "display_name": "Futures / Season Market",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "season", "tournament", "field_size",
            "participant_context", "opening_odds", "closing_odds",
            "implied_probability", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Futures markets need season and field size.",
        "operator_interpretation": (
            "Full depth – futures markets have season and field data."
        ),
    },
    "tournament_winner": {
        "market_family": "tournament_winner",
        "display_name": "Tournament Winner",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "tournament", "field_size",
            "participant_context", "opening_odds", "closing_odds",
            "implied_probability", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Tournament winner markets need tournament context.",
        "operator_interpretation": (
            "Standard depth – tournament winner markets have tournament and field data."
        ),
    },
    "championship_winner": {
        "market_family": "championship_winner",
        "display_name": "Championship / Title Winner",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "tournament", "field_size",
            "participant_context", "opening_odds", "closing_odds",
            "implied_probability", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Championship winner markets need championship context.",
        "operator_interpretation": (
            "Standard depth – championship winner markets have tournament and field data."
        ),
    },
    "award_winner": {
        "market_family": "award_winner",
        "display_name": "Award Winner (MVP, Cy Young, etc.)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "award_name", "season",
            "participant_context", "opening_odds", "closing_odds",
            "implied_probability", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Award winner markets need award and participant context.",
        "operator_interpretation": (
            "Standard depth – award winner markets have award and season data."
        ),
    },
    # ── Motorsports / golf ─────────────────────────────────────────────
    "race_winner": {
        "market_family": "race_winner",
        "display_name": "Race Winner (Motorsports)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "event_name", "qualifying_position", "recent_form",
            "weather", "manufacturer", "team_strength",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Race winner markets need event and driver context.",
        "operator_interpretation": (
            "Full depth – race winner markets have driver and team data."
        ),
    },
    "top_finish": {
        "market_family": "top_finish",
        "display_name": "Top Finish (Top 5/10/20)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "event_name", "qualifying_position", "recent_form",
            "weather", "manufacturer", "team_strength",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Top finish markets need event and driver context.",
        "operator_interpretation": (
            "Full depth – top finish markets have driver and team data."
        ),
    },
    "head_to_head_matchup": {
        "market_family": "head_to_head_matchup",
        "display_name": "Head‑to‑Head Matchup",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "participant_a", "participant_b",
            "season", "tournament", "recent_form",
            "head_to_head_record", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Head‑to‑head markets need both participants.",
        "operator_interpretation": (
            "Full depth – head‑to‑head markets have recent form and H2H record."
        ),
    },
    "finishing_position": {
        "market_family": "finishing_position",
        "display_name": "Finishing Position (Exact)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "event_name", "qualifying_position", "recent_form",
            "weather", "manufacturer", "team_strength",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Exact finishing position markets need driver and event context.",
        "operator_interpretation": (
            "Thin – exact finishing positions have limited depth."
        ),
    },
    "cut_made": {
        "market_family": "cut_made",
        "display_name": "Make/Miss Cut (Golf)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "event_name", "course_fit", "recent_form",
            "weather", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Cut lines may be unavailable.",
        "operator_interpretation": (
            "Thin – cut markets have limited data availability."
        ),
    },
    "placement_market": {
        "market_family": "placement_market",
        "display_name": "Placement Market (Golf/Motorsports)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "event_name", "qualifying_position", "recent_form",
            "weather", "manufacturer", "team_strength",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Placement markets may have limited data.",
        "operator_interpretation": (
            "Thin – placement markets have lower data depth."
        ),
    },
    # ── Esports ─────────────────────────────────────────────────────────
    "esports_match_winner": {
        "market_family": "esports_match_winner",
        "display_name": "Esports Match Winner",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "game_title", "team_name", "opponent_team",
            "roster_status", "patch_version", "tournament_stage",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Esports match winner needs game title and teams.",
        "operator_interpretation": (
            "Full depth – esports match winner has team and roster data."
        ),
    },
    "esports_map_winner": {
        "market_family": "esports_map_winner",
        "display_name": "Esports Map Winner",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "game_title", "team_name", "opponent_team",
            "map_number", "map_pool", "roster_status",
            "patch_version", "tournament_stage", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Esports map winner needs map number and map pool.",
        "operator_interpretation": (
            "Full depth – esports map winner has map and team data."
        ),
    },
    "esports_map_handicap": {
        "market_family": "esports_map_handicap",
        "display_name": "Esports Map Handicap",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "game_title", "team_name", "opponent_team",
            "map_number", "map_pool", "roster_status",
            "patch_version", "tournament_stage", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Esports map handicap requires line value.",
        "operator_interpretation": (
            "Standard depth – esports map handicap has map and team data."
        ),
    },
    "esports_map_total": {
        "market_family": "esports_map_total",
        "display_name": "Esports Map Total",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "game_title", "team_name", "opponent_team",
            "map_number", "map_pool", "roster_status",
            "patch_version", "tournament_stage", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Esports map total may have limited historical data.",
        "operator_interpretation": (
            "Thin – esports map total has basic totals context."
        ),
    },
    "esports_series_correct_score": {
        "market_family": "esports_series_correct_score",
        "display_name": "Esports Series Correct Score",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "game_title", "team_name", "opponent_team",
            "roster_status", "patch_version", "tournament_stage",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Correct score markets need deep series knowledge.",
        "operator_interpretation": (
            "Thin – correct score markets have limited historical data."
        ),
    },
    # ── Soccer specialty ────────────────────────────────────────────────
    "both_teams_to_score": {
        "market_family": "both_teams_to_score",
        "display_name": "Both Teams to Score (BTTS)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "home_team", "away_team", "home_form", "away_form",
            "weather", "referee_context",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "BTTS needs team form and weather.",
        "operator_interpretation": (
            "Standard depth – BTTS markets have team form and weather context."
        ),
    },
    "double_chance": {
        "market_family": "double_chance",
        "display_name": "Double Chance",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "home_team", "away_team", "home_form", "away_form",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Double chance needs team form.",
        "operator_interpretation": (
            "Standard depth – double chance markets have team form context."
        ),
    },
    "draw_no_bet": {
        "market_family": "draw_no_bet",
        "display_name": "Draw No Bet (DNB)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "home_team", "away_team", "home_form", "away_form",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Draw no bet needs team form.",
        "operator_interpretation": (
            "Standard depth – DNB markets have team form context."
        ),
    },
    "corners": {
        "market_family": "corners",
        "display_name": "Corner Total (Soccer)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "home_team", "away_team", "home_form", "away_form",
            "weather", "referee_context",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Corner data may be sparse.",
        "operator_interpretation": (
            "Thin – corner markets have limited historical data."
        ),
    },
    "cards": {
        "market_family": "cards",
        "display_name": "Card Total / Bookings (Soccer)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "home_team", "away_team", "home_form", "away_form",
            "referee_context", "weather",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Card data may be sparse.",
        "operator_interpretation": (
            "Thin – card markets have limited historical data."
        ),
    },
    # ── Cricket specialty ─────────────────────────────────────────────
    "innings_total": {
        "market_family": "innings_total",
        "display_name": "Innings Total (Cricket)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "home_team", "away_team", "innings",
            "pitch_condition", "toss_result",
            "batting_order_strength", "bowling_attack_strength",
            "weather",
        ],
        "optional_fields": [],
        "missing_data_warning": "Innings total data may be limited.",
        "operator_interpretation": (
            "Thin – innings totals have basic cricket context."
        ),
    },
    "wicket_prop": {
        "market_family": "wicket_prop",
        "display_name": "Wicket Prop (Cricket)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "home_team", "away_team",
            "pitch_condition", "toss_result",
            "bowling_attack_strength",
        ],
        "optional_fields": [],
        "missing_data_warning": "Wicket prop data may be limited.",
        "operator_interpretation": (
            "Thin – wicket props have basic cricket context."
        ),
    },
    "top_batter": {
        "market_family": "top_batter",
        "display_name": "Top Batter (Cricket)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "player_name", "team_name", "opponent_team",
            "pitch_condition", "recent_form",
        ],
        "optional_fields": [],
        "missing_data_warning": "Top batter data may be limited.",
        "operator_interpretation": (
            "Thin – top batter markets have basic batting context."
        ),
    },
    "top_bowler": {
        "market_family": "top_bowler",
        "display_name": "Top Bowler (Cricket)",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "player_name", "team_name", "opponent_team",
            "pitch_condition", "recent_form",
        ],
        "optional_fields": [],
        "missing_data_warning": "Top bowler data may be limited.",
        "operator_interpretation": (
            "Thin – top bowler markets have basic bowling context."
        ),
    },
    # ── Tennis / set markets ─────────────────────────────────────────
    "match_winner": {
        "market_family": "match_winner",
        "display_name": "Match Winner (Tennis)",
        "depth_level": "full",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "player_name", "opponent_name", "surface",
            "tournament_round", "recent_form", "head_to_head",
            "fatigue", "line_value", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Tennis match winner needs player names and surface.",
        "operator_interpretation": (
            "Full depth – tennis match winner has surface and form data."
        ),
    },
    "set_winner": {
        "market_family": "set_winner",
        "display_name": "Set Winner (Tennis)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "player_name", "opponent_name", "surface",
            "tournament_round", "recent_form", "head_to_head",
            "set_number", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Set winner markets need set number.",
        "operator_interpretation": (
            "Standard depth – set winner markets have set context."
        ),
    },
    "game_spread": {
        "market_family": "game_spread",
        "display_name": "Game Spread (Tennis)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "player_name", "opponent_name", "surface",
            "tournament_round", "recent_form", "head_to_head",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Game spread markets need line value.",
        "operator_interpretation": (
            "Standard depth – game spread markets have line and player data."
        ),
    },
    "set_spread": {
        "market_family": "set_spread",
        "display_name": "Set Spread (Tennis)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "player_name", "opponent_name", "surface",
            "tournament_round", "recent_form", "head_to_head",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Set spread markets need line value.",
        "operator_interpretation": (
            "Standard depth – set spread markets have line and player data."
        ),
    },
    "match_total_games": {
        "market_family": "match_total_games",
        "display_name": "Match Total Games (Tennis)",
        "depth_level": "standard",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "player_name", "opponent_name", "surface",
            "tournament_round", "recent_form", "head_to_head",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Match total games markets need line value.",
        "operator_interpretation": (
            "Standard depth – match total games markets have line and player data."
        ),
    },
    # ── Live / alternate ─────────────────────────────────────────────
    "live_market": {
        "market_family": "live_market",
        "display_name": "Live / In‑Play Market",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "bookmaker", "opening_odds", "closing_odds",
            "in_play_signal", "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Live markets may have limited historical data.",
        "operator_interpretation": (
            "Thin – live markets have limited historical depth."
        ),
    },
    "alternate_line": {
        "market_family": "alternate_line",
        "display_name": "Alternate Line / Alt Spread",
        "depth_level": "thin",
        "required_fields": _BASE_REQUIRED + ["line_value"],
        "recommended_fields": [
            "bookmaker", "opening_line", "closing_line",
            "volatility_level",
        ],
        "optional_fields": [],
        "missing_data_warning": "Alternate line markets may have limited historical data.",
        "operator_interpretation": (
            "Thin – alternate line markets have limited historical depth."
        ),
    },
    # ── Fallback ──────────────────────────────────────────────────────
    "general_market": {
        "market_family": "general_market",
        "display_name": "General Market (Fallback)",
        "depth_level": "fallback",
        "required_fields": _BASE_REQUIRED,
        "recommended_fields": [
            "source_key", "bookmaker", "opening_odds",
            "closing_odds", "line_value",
        ],
        "optional_fields": [],
        "missing_data_warning": "Unknown market type – using fallback pack.",
        "operator_interpretation": (
            "Fallback – No market pack available. Use odds and basic context only."
        ),
    },
}


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def normalize_market_family(
    market: object = None,
    selection: object = None,
    sport: object = None,
) -> str:
    """Return a canonical market family for any alias, or 'general_market' for unknowns."""
    if not market:
        return "general_market"
    m = str(market).strip().lower().replace("-", "_").replace(" ", "_")
    sel = (str(selection or "")).strip().lower()
    sp = (str(sport or "")).strip().lower()

    # Winner markets
    if m in ("moneyline", "ml", "winner", "match_winner", "game_winner",
             "home_away", "1x2", "three_way", "full_time_result"):
        return "moneyline_or_1x2"

    # Spread / handicap
    if m in ("spread", "point_spread", "handicap", "line", "asian_handicap"):
        return "spread_or_handicap"
    if m in ("runline", "run_line"):
        return "runline"
    if m in ("puckline", "puck_line"):
        return "puckline"

    # Totals
    if m in ("total", "totals", "over_under", "over/under", "o/u", "ou",
             "game_total", "total_points", "total_goals", "total_runs"):
        # further distinguish based on selection and player/team context
        if selection and ("over" in sel or "under" in sel):
            if sp or (selection and ("team" in sel or "player" not in sel)):
                pass
        return "game_total"
    if m in ("team_total", "team_totals", "team_points", "team_runs",
             "team_goals"):
        return "team_total"
    if m in ("period_total", "quarter_total", "half_total", "inning_total",
             "set_total"):
        return "period_total"

    # Player props
    if m in ("player_prop", "prop", "player_points", "points_prop"):
        return "player_points_prop"
    if m in ("player_rebounds", "rebounds_prop"):
        return "player_rebounds_prop"
    if m in ("player_assists", "assists_prop"):
        return "player_assists_prop"
    if m in ("player_shots", "shots_prop"):
        return "player_shots_prop"
    if m in ("player_saves", "saves_prop"):
        return "player_saves_prop"
    if m in ("player_strikeouts", "strikeouts_prop", "pitcher_strikeouts"):
        return "player_strikeouts_prop"
    if m in ("player_bases", "total_bases"):
        return "player_bases_prop"
    if m in ("player_touchdowns", "touchdown_prop", "anytime_touchdown"):
        return "player_touchdowns_prop"
    # generic prop with player name
    if "prop" in m or "prop" in sel:
        if selection and ("player" in sel or "team" not in sel):
            return "player_prop"

    # Combat
    if m in ("fight_moneyline", "fighter_moneyline"):
        return "fight_moneyline"
    if m in ("method", "fight_method", "method_of_victory"):
        return "fight_method"
    if m in ("round", "fight_round", "round_betting"):
        return "fight_round"
    if m in ("total_rounds", "fight_total_rounds", "over_under_rounds"):
        return "fight_total_rounds"
    if m in ("fighter_prop",):
        return "fighter_prop"

    # Outrights / futures
    if m in ("outright", "outright_winner"):
        return "outright"
    if m in ("future", "futures"):
        return "futures"
    if m in ("tournament_winner",):
        return "tournament_winner"
    if m in ("championship_winner", "title_winner"):
        return "championship_winner"
    if m in ("award_winner", "awards"):
        return "award_winner"

    # Motorsports / golf
    if m in ("race_winner",):
        return "race_winner"
    if m in ("top_finish", "top_5", "top_10", "top_20"):
        return "top_finish"
    if m in ("head_to_head", "h2h", "matchup"):
        return "head_to_head_matchup"
    if m in ("finishing_position", "finishing_pos"):
        return "finishing_position"
    if m in ("make_cut", "cut_made", "missed_cut"):
        return "cut_made"
    if m in ("placement", "placement_market"):
        return "placement_market"

    # Esports
    if m in ("esports_match_winner",):
        return "esports_match_winner"
    if m in ("map_winner", "esports_map_winner"):
        return "esports_map_winner"
    if m in ("map_handicap", "esports_map_handicap"):
        return "esports_map_handicap"
    if m in ("map_total", "esports_map_total"):
        return "esports_map_total"
    if m in ("correct_score", "series_correct_score",
             "esports_series_correct_score"):
        return "esports_series_correct_score"

    # Soccer specialty
    if m in ("both_teams_to_score", "btts"):
        return "both_teams_to_score"
    if m in ("double_chance",):
        return "double_chance"
    if m in ("draw_no_bet", "dnb"):
        return "draw_no_bet"
    if m in ("corners", "corner_total"):
        return "corners"
    if m in ("cards", "card_total", "bookings"):
        return "cards"

    # Cricket
    if m in ("innings_total",):
        return "innings_total"
    if m in ("wickets", "wicket_prop"):
        return "wicket_prop"
    if m in ("top_batter", "top_batsman"):
        return "top_batter"
    if m in ("top_bowler",):
        return "top_bowler"

    # Tennis
    if m in ("match_winner",):
        # We already mapped match_winner to moneyline_or_1x2 earlier.
        # This handles sport==tennis case.
        if sp == "tennis":
            return "match_winner"
        return "moneyline_or_1x2"
    if m in ("set_winner",):
        return "set_winner"
    if m in ("game_spread",):
        return "game_spread"
    if m in ("set_spread",):
        return "set_spread"
    if m in ("match_total_games", "total_games"):
        return "match_total_games"

    # Live / alternate
    if m in ("live", "in_play", "in_game"):
        return "live_market"
    if m in ("alternate", "alt_line", "alternate_line"):
        return "alternate_line"

    return "general_market"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_supported_market_feature_packs() -> dict[str, dict[str, Any]]:
    """Return copy of all registered market packs."""
    return dict(MARKET_FEATURE_PACKS)


def get_market_feature_pack(
    market: object = None,
    selection: object = None,
    sport: object = None,
) -> dict[str, Any]:
    """Return the pack for a market family (after normalisation), or the general fallback."""
    key = normalize_market_family(market, selection, sport)
    pk = MARKET_FEATURE_PACKS.get(key)
    if pk is not None:
        return dict(pk)
    return dict(MARKET_FEATURE_PACKS["general_market"])


def calculate_market_field_presence(
    rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """For each field compute present_count, missing_count, coverage_percent.

    None, '', [], {} count as missing.
    """
    result: dict[str, dict[str, Any]] = {}
    total = len(rows) or 1
    for fld in fields:
        present = sum(
            1 for r in rows
            if (
                fld in r
                and r[fld] is not None
                and r[fld] != ""
                and (not isinstance(r[fld], (list, dict)) or len(r[fld]) > 0)
            )
        )
        missing = len(rows) - present
        pct = round(present / total * 100, 1)
        result[fld] = {
            "present_count": present,
            "missing_count": missing,
            "coverage_percent": pct,
        }
    return result


def evaluate_market_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
    market: object = None,
    selection: object = None,
    sport: object = None,
) -> dict[str, Any]:
    """Evaluate how ready *rows* are for a given market family, returning a report dict."""
    pack = get_market_feature_pack(market, selection, sport)
    req = pack["required_fields"]
    rec = pack["recommended_fields"]

    total_rows = len(rows)
    if total_rows == 0:
        return {
            "ok": True,
            "version": MARKET_FEATURE_PACKS_VERSION,
            "market_family": pack["market_family"],
            "display_name": pack["display_name"],
            "depth_level": pack["depth_level"],
            "total_rows": 0,
            "required_coverage_percent": 0.0,
            "recommended_coverage_percent": 0.0,
            "readiness_level": "no_data",
            "required_fields": req,
            "recommended_fields": rec,
            "missing_required_fields": [],
            "missing_recommended_fields": [],
            "field_presence": {},
            "never_feature_fields": list(MARKET_FEATURE_NEVER_FEATURE_FIELDS),
            "warnings": [pack["missing_data_warning"]],
            "operator_interpretation": pack["operator_interpretation"],
        }

    presence = calculate_market_field_presence(rows, req + rec)
    req_pcts = [presence[f]["coverage_percent"] for f in req if f in presence]
    rec_pcts = [presence[f]["coverage_percent"] for f in rec if f in presence]

    avg_req = round(sum(req_pcts) / max(len(req_pcts), 1), 1) if req_pcts else 0.0
    avg_rec = round(sum(rec_pcts) / max(len(rec_pcts), 1), 1) if rec_pcts else 0.0

    missing_req = [f for f in req if f in presence and presence[f]["coverage_percent"] == 0.0]
    missing_rec = [f for f in rec if f in presence and presence[f]["coverage_percent"] == 0.0]

    if avg_req >= 95 and avg_rec >= 60:
        rlevel = "strong"
    elif avg_req >= 80:
        rlevel = "usable"
    elif avg_req >= 50:
        rlevel = "thin"
    else:
        rlevel = "not_ready"

    warnings: list[str] = []
    if missing_req:
        warnings.append(
            f"Missing required fields: {', '.join(missing_req[:5])}"
            + (f" (+{len(missing_req)-5} more)" if len(missing_req) > 5 else "")
        )
    if missing_rec:
        warnings.append(
            f"Missing recommended fields: {', '.join(missing_rec[:5])}"
            + (f" (+{len(missing_rec)-5} more)" if len(missing_rec) > 5 else "")
        )
    if pack["missing_data_warning"]:
        warnings.append(pack["missing_data_warning"])

    return {
        "ok": True,
        "version": MARKET_FEATURE_PACKS_VERSION,
        "market_family": pack["market_family"],
        "display_name": pack["display_name"],
        "depth_level": pack["depth_level"],
        "total_rows": total_rows,
        "required_coverage_percent": avg_req,
        "recommended_coverage_percent": avg_rec,
        "readiness_level": rlevel,
        "required_fields": req,
        "recommended_fields": rec,
        "missing_required_fields": missing_req,
        "missing_recommended_fields": missing_rec,
        "field_presence": presence,
        "never_feature_fields": list(MARKET_FEATURE_NEVER_FEATURE_FIELDS),
        "warnings": warnings,
        "operator_interpretation": pack["operator_interpretation"],
    }


def summarize_market_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Group rows by normalised market family and evaluate each group.

    Returns overall summary including strongest and weakest markets.
    """
    groups: dict[str, list[dict]] = {}
    for r in rows:
        mkt = normalize_market_family(r.get("market"), r.get("selection"), r.get("sport"))
        groups.setdefault(mkt, []).append(r)

    markets_eval: dict[str, Any] = {}
    for mkt_key, grp in groups.items():
        markets_eval[mkt_key] = evaluate_market_feature_readiness(
            grp, market=mkt_key, selection=None, sport=None
        )

    total_rows = sum(e["total_rows"] for e in markets_eval.values())

    strongest: list[str] = []
    weakest: list[str] = []
    if markets_eval:
        sorted_keys = sorted(
            markets_eval,
            key=lambda k: (
                markets_eval[k]["required_coverage_percent"],
                -markets_eval[k]["total_rows"],
            ),
            reverse=True,
        )
        strongest = sorted_keys[:3]
        weakest = sorted_keys[-3:]

    warnings: list[str] = []
    for k, e in markets_eval.items():
        for w in e.get("warnings", []):
            warnings.append(f"[{k}] {w}")

    interp = (
        f"Found {len(markets_eval)} market(s) with {total_rows} total rows. "
        f"Strongest: {','.join(strongest)}. Weakest: {','.join(weakest)}."
    )

    return {
        "ok": True,
        "version": MARKET_FEATURE_PACKS_VERSION,
        "total_rows": total_rows,
        "markets": {
            k: {
                "market_family": v["market_family"],
                "display_name": v["display_name"],
                "depth_level": v["depth_level"],
                "total_rows": v["total_rows"],
                "readiness_level": v["readiness_level"],
                "required_coverage_percent": v["required_coverage_percent"],
                "recommended_coverage_percent": v["recommended_coverage_percent"],
                "missing_required_fields": v["missing_required_fields"],
                "missing_recommended_fields": v["missing_recommended_fields"],
                "operator_interpretation": v["operator_interpretation"],
            }
            for k, v in markets_eval.items()
        },
        "strongest_markets": [
            {"market_family": k, "readiness_level": markets_eval[k]["readiness_level"]}
            for k in strongest
        ],
        "weakest_markets": [
            {"market_family": k, "readiness_level": markets_eval[k]["readiness_level"]}
            for k in weakest
        ],
        "warnings": warnings,
        "operator_interpretation": interp,
    }
