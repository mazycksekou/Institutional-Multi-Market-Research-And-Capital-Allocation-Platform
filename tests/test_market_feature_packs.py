"""Tests for market feature packs (Phase 10H14)."""

from automation_scheduler.market_feature_packs import (
    MARKET_FEATURE_PACKS_VERSION,
    MARKET_FEATURE_NEVER_FEATURE_FIELDS,
    normalize_market_family,
    get_market_feature_pack,
    get_supported_market_feature_packs,
    calculate_market_field_presence,
    evaluate_market_feature_readiness,
    summarize_market_feature_readiness,
)


def test_normalize_market_family_two_way_moneyline_aliases():
    assert normalize_market_family("moneyline") == "two_way_moneyline"
    assert normalize_market_family("ml") == "two_way_moneyline"
    assert normalize_market_family("winner") == "two_way_moneyline"
    assert normalize_market_family("game_winner") == "two_way_moneyline"
    assert normalize_market_family("home_away") == "two_way_moneyline"


def test_normalize_market_family_three_way_moneyline_aliases():
    assert normalize_market_family("1x2") == "three_way_moneyline"
    assert normalize_market_family("three_way") == "three_way_moneyline"
    assert normalize_market_family("three_way_moneyline") == "three_way_moneyline"
    assert normalize_market_family("full_time_result") == "three_way_moneyline"
    assert normalize_market_family("draw_market") == "three_way_moneyline"


def test_moneyline_or_1x2_legacy_alias_still_supported():
    # Direct pass of legacy key should map to two_way unless draw context
    assert normalize_market_family("moneyline_or_1x2") == "two_way_moneyline"
    # With draw context it returns three_way
    assert normalize_market_family("moneyline_or_1x2", selection="draw") == "three_way_moneyline"
    assert normalize_market_family("moneyline_or_1x2", market="moneyline_or_1x2", selection="draw") == "three_way_moneyline"


def test_three_way_moneyline_detects_draw_selection():
    assert normalize_market_family("moneyline", selection="draw") == "three_way_moneyline"
    assert normalize_market_family("ml", selection="x") == "three_way_moneyline"
    assert normalize_market_family("match_winner", selection="draw") == "three_way_moneyline"


def test_supported_market_feature_packs_include_two_way_and_three_way_moneyline():
    packs = get_supported_market_feature_packs()
    assert "two_way_moneyline" in packs
    assert "three_way_moneyline" in packs
    assert "moneyline_or_1x2" in packs  # legacy still present


def test_normalize_market_family_spread_runline_puckline_aliases():
    assert normalize_market_family("spread") == "spread_or_handicap"
    assert normalize_market_family("point_spread") == "spread_or_handicap"
    assert normalize_market_family("runline") == "runline"
    assert normalize_market_family("puckline") == "puckline"


def test_normalize_market_family_totals_and_team_totals():
    assert normalize_market_family("total") == "game_total"
    assert normalize_market_family("over/under") == "game_total"
    assert normalize_market_family("team_total") == "team_total"
    assert normalize_market_family("team_points") == "team_total"


def test_normalize_market_family_player_props():
    assert normalize_market_family("player_points") == "player_points_prop"
    assert normalize_market_family("player_rebounds") == "player_rebounds_prop"
    assert normalize_market_family("player_assists") == "player_assists_prop"
    assert normalize_market_family("player_shots") == "player_shots_prop"
    assert normalize_market_family("player_saves") == "player_saves_prop"
    assert normalize_market_family("player_strikeouts") == "player_strikeouts_prop"
    assert normalize_market_family("player_bases") == "player_bases_prop"
    assert normalize_market_family("player_touchdowns") == "player_touchdowns_prop"
    assert normalize_market_family("prop", selection="player") == "player_points_prop"
    assert normalize_market_family("player_prop") == "player_points_prop"


def test_normalize_market_family_combat_markets():
    assert normalize_market_family("fight_moneyline") == "fight_moneyline"
    assert normalize_market_family("method") == "fight_method"
    assert normalize_market_family("round") == "fight_round"
    assert normalize_market_family("total_rounds") == "fight_total_rounds"
    assert normalize_market_family("fighter_prop") == "fighter_prop"


def test_normalize_market_family_outrights_and_futures():
    assert normalize_market_family("outright") == "outright"
    assert normalize_market_family("futures") == "futures"
    assert normalize_market_family("tournament_winner") == "tournament_winner"
    assert normalize_market_family("championship_winner") == "championship_winner"
    assert normalize_market_family("award_winner") == "award_winner"


def test_normalize_market_family_motorsports_and_golf():
    assert normalize_market_family("race_winner") == "race_winner"
    assert normalize_market_family("top_finish") == "top_finish"
    assert normalize_market_family("head_to_head") == "head_to_head_matchup"
    assert normalize_market_family("finishing_position") == "finishing_position"
    assert normalize_market_family("cut_made") == "cut_made"
    assert normalize_market_family("placement") == "placement_market"


def test_normalize_market_family_esports_markets():
    assert normalize_market_family("esports_match_winner") == "esports_match_winner"
    assert normalize_market_family("map_winner") == "esports_map_winner"
    assert normalize_market_family("map_handicap") == "esports_map_handicap"
    assert normalize_market_family("map_total") == "esports_map_total"
    assert normalize_market_family("correct_score") == "esports_series_correct_score"


def test_normalize_market_family_soccer_specialty():
    assert normalize_market_family("both_teams_to_score") == "both_teams_to_score"
    assert normalize_market_family("btts") == "both_teams_to_score"
    assert normalize_market_family("double_chance") == "double_chance"
    assert normalize_market_family("draw_no_bet") == "draw_no_bet"
    assert normalize_market_family("corners") == "corners"
    assert normalize_market_family("cards") == "cards"


def test_get_market_feature_pack_unknown_returns_general():
    pack = get_market_feature_pack("unknown_market_xyz")
    assert pack["market_family"] == "general_market"
    assert pack["depth_level"] == "fallback"


def test_supported_market_feature_packs_include_core_repo_markets():
    packs = get_supported_market_feature_packs()
    assert "moneyline_or_1x2" in packs
    assert "spread_or_handicap" in packs
    assert "game_total" in packs
    assert "player_prop" in packs
    assert "fight_moneyline" in packs
    assert "outright" in packs
    assert "race_winner" in packs
    assert "esports_match_winner" in packs
    assert "general_market" in packs


def test_calculate_market_field_presence_counts_missing_values():
    rows = [
        {"sport": "nba", "pace": 101.0, "injuries": None},
        {"sport": "nba", "pace": None, "injuries": "yes"},
        {"sport": "nba", "injuries": ""},
    ]
    flds = ["sport", "pace", "injuries"]
    result = calculate_market_field_presence(rows, flds)
    assert result["sport"]["present_count"] == 3
    assert result["sport"]["coverage_percent"] == 100.0
    assert result["pace"]["present_count"] == 1
    assert result["injuries"]["present_count"] == 1


def test_evaluate_market_feature_readiness_strong_for_complete_rows():
    rows = [
        {
            "sport": "nba",
            "event_date": "2023-01-01",
            "market": "moneyline",
            "selection": "A",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
        },
    ]
    result = evaluate_market_feature_readiness(rows, market="moneyline")
    assert result["market_family"] == "moneyline_or_1x2"
    assert result["readiness_level"] in ("usable", "strong")
    assert result["total_rows"] == 1


def test_evaluate_market_feature_readiness_no_data():
    result = evaluate_market_feature_readiness([], market="moneyline")
    assert result["readiness_level"] == "no_data"
    assert result["total_rows"] == 0
    assert result["ok"] is True


def test_evaluate_market_feature_readiness_flags_missing_required_fields():
    rows = [
        {
            "sport": "nba",
            "event_date": "2023-01-01",
            # missing market, selection, odds, implied_prob
        },
    ]
    result = evaluate_market_feature_readiness(rows, market="moneyline")
    assert result["missing_required_fields"]  # at least one
    assert result["readiness_level"] in ("not_ready", "thin")


def test_summarize_market_feature_readiness_groups_by_normalized_market():
    rows = [
        {"sport": "nba", "market": "moneyline", "selection": "A",
         "event_date": "x", "odds_at_decision_time": 1.5,
         "market_implied_probability": 0.5},
        {"sport": "nba", "market": "spread", "selection": "A",
         "event_date": "y", "odds_at_decision_time": 2.0,
         "market_implied_probability": 0.5, "line_value": 1.5},
    ]
    summary = summarize_market_feature_readiness(rows)
    assert summary["ok"] is True
    assert "moneyline_or_1x2" in summary["markets"]
    assert "spread_or_handicap" in summary["markets"]
    assert summary["total_rows"] == 2


def test_never_feature_fields_include_leakage_fields():
    assert "final_result" in MARKET_FEATURE_NEVER_FEATURE_FIELDS
    assert "closing_odds" in MARKET_FEATURE_NEVER_FEATURE_FIELDS
    assert "clv" in MARKET_FEATURE_NEVER_FEATURE_FIELDS
