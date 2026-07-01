"""Sport feature packs – repo‑wide sport readiness layer.

SPORT_FEATURE_PACKS_VERSION = "10H13"

This module defines canonical sport keys, their feature packs,
normalisation helpers, and readiness evaluation functions.
No SQLite changes, no bankroll maths, no network calls, no scraping.
Data leakage fields are explicitly blocked from pre‑decision features.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Version & never‑leak fields
# ---------------------------------------------------------------------------

SPORT_FEATURE_PACKS_VERSION: str = "10H13"

SPORT_FEATURE_NEVER_FEATURE_FIELDS: list[str] = [
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

_TEAM_REQUIRED: list[str] = [
    "sport",
    "event_date",
    "home_team",
    "away_team",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
]

_INDIVIDUAL_REQUIRED: list[str] = [
    "sport",
    "event_date",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
]

_THIN_REQUIRED = _INDIVIDUAL_REQUIRED.copy()

_THIN_RECOMMENDED: list[str] = [
    "participant_context",
    "team_or_player_recent_form",
    "matchup_context",
    "event_format",
    "venue_context",
    "injury_status",
]

# Shared general recommended for fallback
_GENERAL_RECOMMENDED: list[str] = [
    "source_key",
    "bookmaker",
    "opening_odds",
    "closing_odds",
]

# ---------------------------------------------------------------------------
# Master sport pack registry
# ---------------------------------------------------------------------------

SPORT_FEATURE_PACKS: dict[str, dict[str, Any]] = {
    # ── Basketball ──────────────────────────────────────────────────────
    "basketball_nba": {
        "sport_key": "basketball_nba",
        "sport_family": "basketball",
        "display_name": "NBA Basketball",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "home_or_away",
            "rest_days",
            "team_recent_form",
            "pace",
            "offensive_rating",
            "defensive_rating",
            "injury_status",
            "projected_lineup",
            "player_usage",
            "minutes_projection",
        ],
        "optional_fields": [
            "home_court",
            "back_to_back",
            "coach_rotation",
            "referee",
            "travel_distance",
            "altitude",
            "arena_attendance",
        ],
        "missing_data_warning": "Lineup and rotation data may be limited.",
        "operator_interpretation": (
            "Full depth – NBA basketball has rich team and player data. "
            "Projections can be built with pace and rating stats."
        ),
    },
    "basketball_wnba": {
        "sport_key": "basketball_wnba",
        "sport_family": "basketball",
        "display_name": "WNBA Basketball",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "home_or_away",
            "rest_days",
            "team_recent_form",
            "pace",
            "offensive_rating",
            "defensive_rating",
            "injury_status",
            "projected_lineup",
            "player_usage",
            "minutes_projection",
        ],
        "optional_fields": [
            "home_court",
            "back_to_back",
            "coach_rotation",
            "referee",
            "travel_distance",
            "arena_attendance",
        ],
        "missing_data_warning": "WNBA depth is similar to NBA, but fewer historical stats may be available.",
        "operator_interpretation": (
            "Full depth – WNBA is covered by the same basketball framework. "
            "Player usage and pace data are available."
        ),
    },
    "basketball_ncaab": {
        "sport_key": "basketball_ncaab",
        "sport_family": "basketball",
        "display_name": "NCAA Men's Basketball",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "home_or_away",
            "rest_days",
            "team_recent_form",
            "pace",
            "offensive_rating",
            "defensive_rating",
            "injury_status",
            "projected_lineup",
            "player_usage",
            "minutes_projection",
        ],
        "optional_fields": [
            "home_court",
            "back_to_back",
            "team_tempo",
            "referee",
            "conference_strength",
        ],
        "missing_data_warning": "College player data may be less granular than NBA.",
        "operator_interpretation": (
            "Full depth – NCAA men's basketball has strong team and pace stats."
        ),
    },
    "basketball_ncaaw": {
        "sport_key": "basketball_ncaaw",
        "sport_family": "basketball",
        "display_name": "NCAA Women's Basketball",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "home_or_away",
            "rest_days",
            "team_recent_form",
            "pace",
            "offensive_rating",
            "defensive_rating",
            "injury_status",
            "projected_lineup",
            "player_usage",
            "minutes_projection",
        ],
        "optional_fields": [
            "home_court",
            "back_to_back",
            "team_tempo",
            "referee",
            "conference_strength",
        ],
        "missing_data_warning": "Women's college basketball has similar depth to men's.",
        "operator_interpretation": (
            "Full depth – NCAA women's basketball is covered by the same basketball pack."
        ),
    },
    # ── Baseball ────────────────────────────────────────────────────────
    "baseball_mlb": {
        "sport_key": "baseball_mlb",
        "sport_family": "baseball",
        "display_name": "Major League Baseball",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "starting_pitcher",
            "bullpen_strength",
            "lineup_strength",
            "park_factor",
            "handedness_split",
            "weather",
            "umpire",
            "pitcher_recent_form",
        ],
        "optional_fields": [
            "home_court",
            "rest_days",
            "team_recent_form",
            "batting_stats",
            "pitching_stats",
        ],
        "missing_data_warning": "Pitcher and lineup data may be missing for some games.",
        "operator_interpretation": (
            "Full depth – MLB has rich pitcher, park, and lineup data."
        ),
    },
    # ── American football ───────────────────────────────────────────────
    "americanfootball_nfl": {
        "sport_key": "americanfootball_nfl",
        "sport_family": "american_football",
        "display_name": "NFL Football",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "qb_status",
            "injury_status",
            "offensive_line_rating",
            "defensive_rating",
            "rest_days",
            "weather",
            "travel",
            "coaching_context",
            "pace",
            "explosive_play_rate",
        ],
        "optional_fields": [
            "home_court",
            "venue",
            "referee",
            "surface_type",
            "team_temperature_movement",
        ],
        "missing_data_warning": "Injury status and line ratings may be incomplete.",
        "operator_interpretation": (
            "Full depth – NFL football has deep team and coaching data."
        ),
    },
    "americanfootball_ncaaf": {
        "sport_key": "americanfootball_ncaaf",
        "sport_family": "american_football",
        "display_name": "NCAA Football",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "qb_status",
            "injury_status",
            "offensive_line_rating",
            "defensive_rating",
            "rest_days",
            "weather",
            "travel",
            "coaching_context",
            "pace",
            "explosive_play_rate",
        ],
        "optional_fields": [
            "home_court",
            "venue",
            "referee",
            "surface_type",
            "conference_strength",
        ],
        "missing_data_warning": "College football data may be less granular.",
        "operator_interpretation": (
            "Full depth – NCAA football is covered by the same football pack."
        ),
    },
    # ── Soccer ──────────────────────────────────────────────────────────
    "soccer": {
        "sport_key": "soccer",
        "sport_family": "soccer",
        "display_name": "Soccer (Global)",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "home_form",
            "away_form",
            "xg_for",
            "xg_against",
            "lineup_status",
            "rest_days",
            "goalkeeper_status",
            "referee_context",
            "set_piece_strength",
        ],
        "optional_fields": [
            "possession",
            "shots_on_target",
            "corners",
            "cards",
            "substitution_depth",
        ],
        "missing_data_warning": "xG data may be unavailable for some leagues.",
        "operator_interpretation": (
            "Full depth – Soccer has strong team and expected goals data."
        ),
    },
    # ── Hockey ──────────────────────────────────────────────────────────
    "icehockey_nhl": {
        "sport_key": "icehockey_nhl",
        "sport_family": "hockey",
        "display_name": "NHL Hockey",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "starting_goalie",
            "rest_days",
            "team_recent_form",
            "power_play_rating",
            "penalty_kill_rating",
            "line_pair_context",
            "shot_quality",
            "possession_metrics",
        ],
        "optional_fields": [
            "home_court",
            "last_10_games",
            "faceoff_rating",
            "hits",
            "blocked_shots",
        ],
        "missing_data_warning": "Goalie and line data may be missing for early games.",
        "operator_interpretation": (
            "Full depth – NHL hockey has strong possession and special teams data."
        ),
    },
    # ── Tennis ──────────────────────────────────────────────────────────
    "tennis": {
        "sport_key": "tennis",
        "sport_family": "tennis",
        "display_name": "Tennis",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "player_rank",
            "surface",
            "recent_form",
            "head_to_head",
            "injury_status",
            "serve_rating",
            "return_rating",
            "fatigue",
            "tournament_round",
        ],
        "optional_fields": [
            "weather",
            "indoor_outdoor",
            "previous_performance_tournament",
            "coach_presence",
            "rest_days",
        ],
        "missing_data_warning": "Player rank and surface data are usually available.",
        "operator_interpretation": (
            "Full depth – Tennis has strong player form and surface data."
        ),
    },
    # ── Table tennis ────────────────────────────────────────────────────
    "table_tennis": {
        "sport_key": "table_tennis",
        "sport_family": "table_tennis",
        "display_name": "Table Tennis",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "player_rank",
            "recent_form",
            "head_to_head",
            "format",
            "serve_hold_rate",
            "pressure_context",
        ],
        "optional_fields": [],
        "missing_data_warning": "Limited historical data; player rank may be unavailable.",
        "operator_interpretation": (
            "Thin – Table tennis has less depth. Use basic odds and recent form."
        ),
    },
    # ── Golf / PGA / LPGA ───────────────────────────────────────────────
    "golf": {
        "sport_key": "golf",
        "sport_family": "golf",
        "display_name": "Golf",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "course_fit",
            "strokes_gained_off_tee",
            "strokes_gained_approach",
            "short_game_rating",
            "putting_rating",
            "weather_wave",
            "field_strength",
            "recent_form",
        ],
        "optional_fields": [
            "tournament_history",
            "course_par",
            "elevation",
            "wind_speed",
            "greens_in_regulation_percentage",
        ],
        "missing_data_warning": "Strokes gained data may be limited for smaller tours.",
        "operator_interpretation": (
            "Full depth – Golf has rich strokes-gained and course data."
        ),
    },
    "pga": {
        "sport_key": "pga",
        "sport_family": "golf",
        "display_name": "PGA Tour Golf",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "course_fit",
            "strokes_gained_off_tee",
            "strokes_gained_approach",
            "short_game_rating",
            "putting_rating",
            "weather_wave",
            "field_strength",
            "recent_form",
        ],
        "optional_fields": [
            "tournament_history",
            "course_par",
            "elevation",
            "wind_speed",
            "greens_in_regulation_percentage",
        ],
        "missing_data_warning": "PGA tour has the deepest strokes‑gained data.",
        "operator_interpretation": (
            "Full depth – PGA Tour has best strokes‑gained and field data."
        ),
    },
    "lpga": {
        "sport_key": "lpga",
        "sport_family": "golf",
        "display_name": "LPGA Tour Golf",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "course_fit",
            "strokes_gained_off_tee",
            "strokes_gained_approach",
            "short_game_rating",
            "putting_rating",
            "weather_wave",
            "field_strength",
            "recent_form",
        ],
        "optional_fields": [],
        "missing_data_warning": "LPGA strokes‑gained data may be less available than PGA.",
        "operator_interpretation": (
            "Full depth – LPGA is covered by the same golf pack, but data availability may vary."
        ),
    },
    # ── Motorsports ─────────────────────────────────────────────────────
    "nascar": {
        "sport_key": "nascar",
        "sport_family": "motorsport",
        "display_name": "NASCAR",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "track_type",
            "qualifying_position",
            "practice_speed",
            "driver_form",
            "team_strength",
            "pit_crew_rating",
            "manufacturer",
            "weather",
        ],
        "optional_fields": [
            "restart_position",
            "caution_count",
            "fuel_strategy",
            "tire_wear",
            "pit_stop_avg",
        ],
        "missing_data_warning": "Practice and qualifying data may be limited for smaller events.",
        "operator_interpretation": (
            "Full depth – NASCAR has strong team, track, and driver data."
        ),
    },
    "formula_1": {
        "sport_key": "formula_1",
        "sport_family": "motorsport",
        "display_name": "Formula 1",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "qualifying_position",
            "constructor_strength",
            "driver_form",
            "track_type",
            "tire_strategy",
            "weather",
            "practice_pace",
            "reliability_rating",
        ],
        "optional_fields": [
            "pit_stop_avg",
            "penalty_points",
            "championship_standings",
            "data_availability",
        ],
        "missing_data_warning": "Practice and tire data may be limited.",
        "operator_interpretation": (
            "Full depth – Formula 1 has strong constructor and driver data."
        ),
    },
    "formula_e": {
        "sport_key": "formula_e",
        "sport_family": "motorsport",
        "display_name": "Formula E",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "qualifying_position",
            "constructor_strength",
            "driver_form",
            "track_type",
            "energy_management",
            "weather",
            "practice_pace",
            "reliability_rating",
        ],
        "optional_fields": [
            "pit_stop_avg",
            "penalty_points",
            "championship_standings",
        ],
        "missing_data_warning": "Formula E data may be less detailed than F1.",
        "operator_interpretation": (
            "Full depth – Formula E is covered by motorsport framework."
        ),
    },
    "indycar": {
        "sport_key": "indycar",
        "sport_family": "motorsport",
        "display_name": "IndyCar",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "qualifying_position",
            "constructor_strength",
            "driver_form",
            "track_type",
            "weather",
            "practice_pace",
            "reliability_rating",
        ],
        "optional_fields": [],
        "missing_data_warning": "IndyCar data depth is moderate; use basic driver and team stats.",
        "operator_interpretation": (
            "Thin – IndyCar has less granular data than Formula 1."
        ),
    },
    "motogp": {
        "sport_key": "motogp",
        "sport_family": "motorsport",
        "display_name": "MotoGP",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "qualifying_position",
            "constructor_strength",
            "rider_form",
            "track_type",
            "weather",
            "practice_pace",
            "reliability_rating",
        ],
        "optional_fields": [],
        "missing_data_warning": "MotoGP data depth is moderate.",
        "operator_interpretation": (
            "Thin – MotoGP has fewer statistics than Formula 1."
        ),
    },
    # ── Cricket ─────────────────────────────────────────────────────────
    "cricket": {
        "sport_key": "cricket",
        "sport_family": "cricket",
        "display_name": "Cricket",
        "depth_level": "full",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": [
            "format",
            "pitch_condition",
            "toss_result",
            "batting_order_strength",
            "bowling_attack_strength",
            "recent_form",
            "venue_factor",
            "weather",
        ],
        "optional_fields": [
            "head_to_head",
            "over_rate",
            "player_of_the_match",
            "stadium_capacity",
        ],
        "missing_data_warning": "Pitch and toss data may be missing for older matches.",
        "operator_interpretation": (
            "Full depth – Cricket has format, pitch, and team data."
        ),
    },
    # ── Combat sports ───────────────────────────────────────────────────
    "combat_sports": {
        "sport_key": "combat_sports",
        "sport_family": "combat_sports",
        "display_name": "Combat Sports (General)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "fighter_recent_form",
            "reach",
            "stance",
            "age",
            "camp_change",
            "injury_status",
            "striking_rating",
            "grappling_rating",
            "takedown_defense",
            "weight_cut_context",
        ],
        "optional_fields": [],
        "missing_data_warning": "Combat sports have variable data quality.",
        "operator_interpretation": (
            "Full depth – General combat sports pack covers striking and grappling."
        ),
    },
    "ufc_mma": {
        "sport_key": "ufc_mma",
        "sport_family": "combat_sports",
        "display_name": "UFC / MMA",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "fighter_recent_form",
            "reach",
            "stance",
            "age",
            "camp_change",
            "injury_status",
            "striking_rating",
            "grappling_rating",
            "takedown_defense",
            "weight_cut_context",
        ],
        "optional_fields": [],
        "missing_data_warning": "UFC data is usually rich.",
        "operator_interpretation": (
            "Full depth – UFC has detailed fighter metrics."
        ),
    },
    "mma": {
        "sport_key": "mma",
        "sport_family": "combat_sports",
        "display_name": "MMA (General)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "fighter_recent_form",
            "reach",
            "stance",
            "age",
            "camp_change",
            "injury_status",
            "striking_rating",
            "grappling_rating",
            "takedown_defense",
            "weight_cut_context",
        ],
        "optional_fields": [],
        "missing_data_warning": "General MMA data may be uneven.",
        "operator_interpretation": (
            "Full depth – General MMA pack works for any MMA promotion."
        ),
    },
    "ufc": {
        "sport_key": "ufc",
        "sport_family": "combat_sports",
        "display_name": "UFC",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "fighter_recent_form",
            "reach",
            "stance",
            "age",
            "camp_change",
            "injury_status",
            "striking_rating",
            "grappling_rating",
            "takedown_defense",
            "weight_cut_context",
        ],
        "optional_fields": [],
        "missing_data_warning": "UFC data is usually rich.",
        "operator_interpretation": (
            "Full depth – UFC has detailed fighter metrics."
        ),
    },
    "boxing": {
        "sport_key": "boxing",
        "sport_family": "combat_sports",
        "display_name": "Boxing",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "fighter_recent_form",
            "reach",
            "stance",
            "age",
            "camp_change",
            "injury_status",
            "punch_volume",
            "knockout_rate",
            "defensive_rating",
            "weight_class_context",
        ],
        "optional_fields": [],
        "missing_data_warning": "Boxing punch stats may be unavailable for smaller events.",
        "operator_interpretation": (
            "Full depth – Boxing has strong fighter and punch stats."
        ),
    },
    # ── Esports ─────────────────────────────────────────────────────────
    "esports": {
        "sport_key": "esports",
        "sport_family": "esports",
        "display_name": "Esports (General)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "game_title",
            "team_recent_form",
            "roster_status",
            "patch_version",
            "tournament_stage",
            "head_to_head",
        ],
        "optional_fields": [
            "map_information",
            "side_information",
            "coach_presence",
        ],
        "missing_data_warning": "Game‑specific data varies; use general form and roster.",
        "operator_interpretation": (
            "Full depth – General esports pack covers basic team and roster info."
        ),
    },
    "call_of_duty": {
        "sport_key": "call_of_duty",
        "sport_family": "esports",
        "display_name": "Call of Duty (Esports)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "team_recent_form",
            "roster_status",
            "map_pool",
            "mode_strength",
            "patch_version",
            "tournament_stage",
            "head_to_head",
        ],
        "optional_fields": [],
        "missing_data_warning": "CoD map pool and mode data may be limited.",
        "operator_interpretation": (
            "Full depth – Call of Duty esports has team and map data."
        ),
    },
    "cs2": {
        "sport_key": "cs2",
        "sport_family": "esports",
        "display_name": "CS2 (Counter‑Strike 2)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "team_recent_form",
            "roster_status",
            "map_pool",
            "pistol_round_rate",
            "economy_rating",
            "patch_version",
            "tournament_stage",
            "head_to_head",
        ],
        "optional_fields": [],
        "missing_data_warning": "CS2 pistol round and economy stats may be missing.",
        "operator_interpretation": (
            "Full depth – CS2 has strong team and map data."
        ),
    },
    "dota2": {
        "sport_key": "dota2",
        "sport_family": "esports",
        "display_name": "Dota 2",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "team_recent_form",
            "roster_status",
            "hero_pool",
            "draft_strength",
            "patch_version",
            "tournament_stage",
            "side_preference",
            "head_to_head",
        ],
        "optional_fields": [],
        "missing_data_warning": "Dota 2 draft and hero data may be limited.",
        "operator_interpretation": (
            "Full depth – Dota 2 has hero and draft data."
        ),
    },
    "league_of_legends": {
        "sport_key": "league_of_legends",
        "sport_family": "esports",
        "display_name": "League of Legends",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "team_recent_form",
            "roster_status",
            "champion_pool",
            "lane_matchup_rating",
            "patch_version",
            "objective_control",
            "tournament_stage",
            "head_to_head",
        ],
        "optional_fields": [],
        "missing_data_warning": "LCS/LEC champion and objective data may be limited.",
        "operator_interpretation": (
            "Full depth – LoL has champion and objective data."
        ),
    },
    "overwatch": {
        "sport_key": "overwatch",
        "sport_family": "esports",
        "display_name": "Overwatch (Esports)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "team_recent_form",
            "roster_status",
            "hero_pool",
            "map_pool",
            "patch_version",
            "role_matchup",
            "tournament_stage",
            "head_to_head",
        ],
        "optional_fields": [],
        "missing_data_warning": "Overwatch hero and map data may be limited.",
        "operator_interpretation": (
            "Full depth – Overwatch has hero and map data."
        ),
    },
    "valorant": {
        "sport_key": "valorant",
        "sport_family": "esports",
        "display_name": "Valorant (Esports)",
        "depth_level": "full",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": [
            "team_recent_form",
            "roster_status",
            "agent_pool",
            "map_pool",
            "pistol_round_rate",
            "economy_rating",
            "patch_version",
            "tournament_stage",
            "head_to_head",
        ],
        "optional_fields": [],
        "missing_data_warning": "Valorant agent and economy data may be limited.",
        "operator_interpretation": (
            "Full depth – Valorant has agent and map data."
        ),
    },
    # ── Thin repo‑thin sports ───────────────────────────────────────────
    "afl": {
        "sport_key": "afl",
        "sport_family": "australian_football",
        "display_name": "AFL (Australian Football)",
        "depth_level": "thin",
        "required_fields": _THIN_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "AFL may have limited historical data.",
        "operator_interpretation": (
            "Thin – AFL has basic odds and seasonal context."
        ),
    },
    "badminton": {
        "sport_key": "badminton",
        "sport_family": "raquet_sport",
        "display_name": "Badminton",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Badminton data coverage may be sparse.",
        "operator_interpretation": (
            "Thin – Badminton pack provides basic odds and player context."
        ),
    },
    "darts": {
        "sport_key": "darts",
        "sport_family": "darts",
        "display_name": "Darts",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Darts data depth is limited.",
        "operator_interpretation": (
            "Thin – Darts pack has basic odds and player form."
        ),
    },
    "handball": {
        "sport_key": "handball",
        "sport_family": "handball",
        "display_name": "Handball",
        "depth_level": "thin",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Handball data may be less comprehensive.",
        "operator_interpretation": (
            "Thin – Handball pack provides team and basic stats."
        ),
    },
    "lacrosse": {
        "sport_key": "lacrosse",
        "sport_family": "lacrosse",
        "display_name": "Lacrosse",
        "depth_level": "thin",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Lacrosse data may be scarce.",
        "operator_interpretation": (
            "Thin – Lacrosse has basic team context."
        ),
    },
    "pickleball": {
        "sport_key": "pickleball",
        "sport_family": "raquet_sport",
        "display_name": "Pickleball",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Pickleball data is emergent.",
        "operator_interpretation": (
            "Thin – Pickleball has minimal historical data."
        ),
    },
    "rugby": {
        "sport_key": "rugby",
        "sport_family": "rugby",
        "display_name": "Rugby",
        "depth_level": "thin",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Rugby data coverage varies.",
        "operator_interpretation": (
            "Thin – Rugby pack has team and basic form."
        ),
    },
    "snooker": {
        "sport_key": "snooker",
        "sport_family": "cue_sport",
        "display_name": "Snooker",
        "depth_level": "thin",
        "required_fields": _INDIVIDUAL_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Snooker data depth is limited.",
        "operator_interpretation": (
            "Thin – Snooker pack has basic player and tournament data."
        ),
    },
    "volleyball": {
        "sport_key": "volleyball",
        "sport_family": "volleyball",
        "display_name": "Volleyball",
        "depth_level": "thin",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Volleyball data may be limited.",
        "operator_interpretation": (
            "Thin – Volleyball has team context."
        ),
    },
    "water_polo": {
        "sport_key": "water_polo",
        "sport_family": "water_polo",
        "display_name": "Water Polo",
        "depth_level": "thin",
        "required_fields": _TEAM_REQUIRED,
        "recommended_fields": _THIN_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Water polo data is scarce.",
        "operator_interpretation": (
            "Thin – Water polo has minimal depth."
        ),
    },
    # ── Fallback ────────────────────────────────────────────────────────
    "general": {
        "sport_key": "general",
        "sport_family": "general",
        "display_name": "General Fallback",
        "depth_level": "fallback",
        "required_fields": _THIN_REQUIRED,
        "recommended_fields": _GENERAL_RECOMMENDED,
        "optional_fields": [],
        "missing_data_warning": "Unknown sport – using fallback pack.",
        "operator_interpretation": (
            "Fallback – No sport pack available. "
            "Use odds and basic context only."
        ),
    },
}


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def normalize_sport_key(value: str | None) -> str:
    """Return a canonical sport key for any alias, or 'general' for unknowns."""
    if not value:
        return "general"
    s = value.strip().lower().replace("-", "_").replace(" ", "_")

    # Basketball
    if s in ("basketball_nba", "nba", "basketball"):
        return "basketball_nba"
    if s in ("basketball_wnba", "wnba"):
        return "basketball_wnba"
    if s in (
        "basketball_ncaab", "ncaab", "ncaamb",
        "college_basketball", "mens_college_basketball",
    ):
        return "basketball_ncaab"
    if s in (
        "basketball_ncaaw", "ncaaw", "ncaawb", "ncaawbasketball",
        "womens_college_basketball", "college_womens_basketball",
        "basketball_ncaawb",
    ):
        return "basketball_ncaaw"

    # Baseball
    if s in ("baseball_mlb", "mlb", "baseball", "major_league_baseball"):
        return "baseball_mlb"

    # American football
    if s in ("americanfootball_nfl", "nfl", "football", "american_football", "cfl"):
        return "americanfootball_nfl"
    if s in (
        "americanfootball_ncaaf", "ncaaf", "ncaafb",
        "college_football",
    ):
        return "americanfootball_ncaaf"

    # Soccer
    if s in (
        "soccer", "football_global", "epl", "mls", "premier_league",
    ):
        return "soccer"

    # Hockey
    if s in ("icehockey_nhl", "nhl", "hockey"):
        return "icehockey_nhl"

    # Tennis / racket
    if s in ("tennis",):
        return "tennis"
    if s in ("table_tennis", "ping_pong"):
        return "table_tennis"

    # Golf
    if s in ("golf",):
        return "golf"
    if s in ("pga",):
        return "pga"
    if s in ("lpga",):
        return "lpga"

    # Motorsports
    if s in ("nascar",):
        return "nascar"
    if s in ("formula_1", "f1", "formula1"):
        return "formula_1"
    if s in ("formula_e", "formulae"):
        return "formula_e"
    if s in ("indycar",):
        return "indycar"
    if s in ("motogp", "moto_gp"):
        return "motogp"

    # Cricket
    if s in ("cricket", "ipl"):
        return "cricket"

    # Combat
    if s in ("combat_sports", "combat_sport", "combat"):
        return "combat_sports"
    if s in ("ufc_mma", "ufcmma"):
        return "ufc_mma"
    if s in ("mma",):
        return "mma"
    if s in ("ufc",):
        return "ufc"
    if s in ("boxing",):
        return "boxing"

    # Esports
    if s in ("esports", "esport", "egaming"):
        return "esports"
    if s in ("call_of_duty", "cod"):
        return "call_of_duty"
    if s in ("cs2", "csgo", "counter_strike", "counter_strike_2"):
        return "cs2"
    if s in ("dota2", "dota_2", "dota"):
        return "dota2"
    if s in ("league_of_legends", "lol"):
        return "league_of_legends"
    if s in ("overwatch",):
        return "overwatch"
    if s in ("valorant",):
        return "valorant"

    # Thin sports
    if s in ("afl",):
        return "afl"
    if s in ("badminton",):
        return "badminton"
    if s in ("darts",):
        return "darts"
    if s in ("handball",):
        return "handball"
    if s in ("lacrosse",):
        return "lacrosse"
    if s in ("pickleball",):
        return "pickleball"
    if s in ("rugby",):
        return "rugby"
    if s in ("snooker",):
        return "snooker"
    if s in ("volleyball",):
        return "volleyball"
    if s in ("water_polo", "waterpolo"):
        return "water_polo"

    return "general"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_supported_sport_feature_packs() -> dict[str, dict[str, Any]]:
    """Return copy of all registered sport packs."""
    return dict(SPORT_FEATURE_PACKS)


def get_sport_feature_pack(sport: str | None) -> dict[str, Any]:
    """Return the pack for *sport* (after normalisation), or the general fallback."""
    key = normalize_sport_key(sport)
    pk = SPORT_FEATURE_PACKS.get(key)
    if pk is not None:
        return dict(pk)  # return copy
    return dict(SPORT_FEATURE_PACKS["general"])


def calculate_field_presence(
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


def evaluate_sport_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
    sport: str | None = None,
) -> dict[str, Any]:
    """Evaluate how ready *rows* are for a given *sport*, returning a report dict."""
    pack = get_sport_feature_pack(sport)
    req = pack["required_fields"]
    rec = pack["recommended_fields"]

    total_rows = len(rows)
    if total_rows == 0:
        return {
            "ok": True,
            "version": SPORT_FEATURE_PACKS_VERSION,
            "sport_key": pack["sport_key"],
            "sport_family": pack["sport_family"],
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
            "never_feature_fields": list(SPORT_FEATURE_NEVER_FEATURE_FIELDS),
            "warnings": [pack["missing_data_warning"]],
            "operator_interpretation": pack["operator_interpretation"],
        }

    presence = calculate_field_presence(rows, req + rec)
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
        "version": SPORT_FEATURE_PACKS_VERSION,
        "sport_key": pack["sport_key"],
        "sport_family": pack["sport_family"],
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
        "never_feature_fields": list(SPORT_FEATURE_NEVER_FEATURE_FIELDS),
        "warnings": warnings,
        "operator_interpretation": pack["operator_interpretation"],
    }


def summarize_sport_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Group rows by normalised sport key and evaluate each group.

    Returns overall summary including strongest and weakest sports.
    """
    groups: dict[str, list[dict]] = {}
    for r in rows:
        sk = normalize_sport_key(r.get("sport"))
        groups.setdefault(sk, []).append(r)

    sports_eval: dict[str, Any] = {}
    for sk, grp in groups.items():
        sports_eval[sk] = evaluate_sport_feature_readiness(grp, sk)

    total_rows = sum(e["total_rows"] for e in sports_eval.values())

    # Determine strongest / weakest based on avg_req coverage
    strongest: list[str] = []
    weakest: list[str] = []
    if sports_eval:
        sorted_keys = sorted(
            sports_eval,
            key=lambda k: (sports_eval[k]["required_coverage_percent"], -sports_eval[k]["total_rows"]),
            reverse=True,
        )
        strongest = sorted_keys[:3]
        weakest = sorted_keys[-3:]

    warnings: list[str] = []
    for k, e in sports_eval.items():
        for w in e.get("warnings", []):
            warnings.append(f"[{k}] {w}")

    interp = (
        f"Found {len(sports_eval)} sport(s) with {total_rows} total rows. "
        f"Strongest: {','.join(strongest)}. Weakest: {','.join(weakest)}."
    )

    return {
        "ok": True,
        "version": SPORT_FEATURE_PACKS_VERSION,
        "total_rows": total_rows,
        "sports": {k: {
            "sport_key": v["sport_key"],
            "sport_family": v["sport_family"],
            "display_name": v["display_name"],
            "depth_level": v["depth_level"],
            "total_rows": v["total_rows"],
            "readiness_level": v["readiness_level"],
            "required_coverage_percent": v["required_coverage_percent"],
            "recommended_coverage_percent": v["recommended_coverage_percent"],
            "missing_required_fields": v["missing_required_fields"],
            "missing_recommended_fields": v["missing_recommended_fields"],
            "operator_interpretation": v["operator_interpretation"],
        } for k, v in sports_eval.items()},
        "strongest_sports": [
            {"sport_key": k, "readiness_level": sports_eval[k]["readiness_level"]}
            for k in strongest
        ],
        "weakest_sports": [
            {"sport_key": k, "readiness_level": sports_eval[k]["readiness_level"]}
            for k in weakest
        ],
        "warnings": warnings,
        "operator_interpretation": interp,
    }
