"""Tests for sport feature packs (Phase 10H13)."""

from automation_scheduler.sport_feature_packs import (
    SPORT_FEATURE_PACKS_VERSION,
    SPORT_FEATURE_NEVER_FEATURE_FIELDS,
    normalize_sport_key,
    get_sport_feature_pack,
    get_supported_sport_feature_packs,
    calculate_field_presence,
    evaluate_sport_feature_readiness,
    summarize_sport_feature_readiness,
)


def test_normalize_sport_key_aliases_for_core_repo_sports():
    assert normalize_sport_key("nba") == "basketball_nba"
    assert normalize_sport_key("basketball_wnba") == "basketball_wnba"
    assert normalize_sport_key("ncaab") == "basketball_ncaab"
    assert normalize_sport_key("ncaaw") == "basketball_ncaaw"
    assert normalize_sport_key("mlb") == "baseball_mlb"
    assert normalize_sport_key("nfl") == "americanfootball_nfl"
    assert normalize_sport_key("ncaaf") == "americanfootball_ncaaf"
    assert normalize_sport_key("soccer") == "soccer"
    assert normalize_sport_key("nhl") == "icehockey_nhl"
    assert normalize_sport_key("tennis") == "tennis"
    assert normalize_sport_key("golf") == "golf"


def test_normalize_sport_key_aliases_for_esports_and_combat():
    assert normalize_sport_key("csgo") == "cs2"
    assert normalize_sport_key("lol") == "league_of_legends"
    assert normalize_sport_key("ufc_mma") == "ufc_mma"
    assert normalize_sport_key("ufc") == "ufc"
    assert normalize_sport_key("boxing") == "boxing"


def test_normalize_sport_key_aliases_for_thin_sports():
    assert normalize_sport_key("afl") == "afl"
    assert normalize_sport_key("badminton") == "badminton"
    assert normalize_sport_key("darts") == "darts"
    assert normalize_sport_key("handball") == "handball"
    assert normalize_sport_key("lacrosse") == "lacrosse"
    assert normalize_sport_key("pickleball") == "pickleball"
    assert normalize_sport_key("rugby") == "rugby"
    assert normalize_sport_key("snooker") == "snooker"
    assert normalize_sport_key("volleyball") == "volleyball"
    assert normalize_sport_key("water_polo") == "water_polo"


def test_get_sport_feature_pack_unknown_returns_general():
    pack = get_sport_feature_pack("unknown_sport_xyz")
    assert pack["sport_key"] == "general"
    assert pack["depth_level"] == "fallback"


def test_supported_sport_feature_packs_include_repo_active_sports():
    packs = get_supported_sport_feature_packs()
    assert "basketball_nba" in packs
    assert "baseball_mlb" in packs
    assert "americanfootball_nfl" in packs
    assert "soccer" in packs
    assert "icehockey_nhl" in packs
    assert "tennis" in packs
    assert "golf" in packs
    assert "cricket" in packs
    assert "combat_sports" in packs
    assert "esports" in packs
    assert "general" in packs


def test_calculate_field_presence_counts_missing_values():
    rows = [
        {"sport": "nba", "pace": 101.0, "injuries": None},
        {"sport": "nba", "pace": None, "injuries": "yes"},
        {"sport": "nba", "injuries": ""},
    ]
    flds = ["sport", "pace", "injuries"]
    result = calculate_field_presence(rows, flds)
    assert result["sport"]["present_count"] == 3
    assert result["sport"]["coverage_percent"] == 100.0
    assert result["pace"]["present_count"] == 1
    assert result["pace"]["coverage_percent"] == 33.3
    assert result["injuries"]["present_count"] == 1  # "" is missing, None missing, "yes" present


def test_evaluate_sport_feature_readiness_strong_for_complete_rows():
    rows = [
        {
            "sport": "nba",
            "event_date": "2023-01-01",
            "home_team": "A",
            "away_team": "B",
            "market": "moneyline",
            "selection": "A",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "home_or_away": "home",
            "rest_days": 2,
        },
    ]
    # Almost all required fields present; recommended partially present
    result = evaluate_sport_feature_readiness(rows, sport="nba")
    assert result["sport_key"] == "basketball_nba"
    assert result["readiness_level"] in ("usable", "strong")
    assert result["total_rows"] == 1


def test_evaluate_sport_feature_readiness_no_data():
    result = evaluate_sport_feature_readiness([], sport="nba")
    assert result["readiness_level"] == "no_data"
    assert result["total_rows"] == 0
    assert result["ok"] is True


def test_evaluate_sport_feature_readiness_flags_missing_required_fields():
    rows = [
        {
            "sport": "nba",
            "event_date": "2023-01-01",
            "home_team": "A",
            # missing away_team, market, selection, odds, implied_prob
        },
    ]
    result = evaluate_sport_feature_readiness(rows, sport="nba")
    # Many required fields missing
    assert result["missing_required_fields"]  # at least one
    assert result["readiness_level"] in ("not_ready", "thin")


def test_summarize_sport_feature_readiness_groups_by_normalized_sport():
    rows = [
        {"sport": "nba", "event_date": "x", "market": "ml", "selection": "A",
         "odds_at_decision_time": 1.5, "market_implied_probability": 0.5},
        {"sport": "mlb", "event_date": "y", "market": "ml", "selection": "A",
         "odds_at_decision_time": 2.0, "market_implied_probability": 0.5},
    ]
    summary = summarize_sport_feature_readiness(rows)
    assert summary["ok"] is True
    assert "basketball_nba" in summary["sports"]
    assert "baseball_mlb" in summary["sports"]
    assert summary["total_rows"] == 2


def test_never_feature_fields_include_leakage_fields():
    assert "final_result" in SPORT_FEATURE_NEVER_FEATURE_FIELDS
    assert "closing_odds" in SPORT_FEATURE_NEVER_FEATURE_FIELDS
    assert "clv" in SPORT_FEATURE_NEVER_FEATURE_FIELDS


def test_esports_specific_packs_exist():
    packs = get_supported_sport_feature_packs()
    for key in ("call_of_duty", "cs2", "dota2", "league_of_legends", "overwatch", "valorant"):
        assert key in packs


def test_motorsports_specific_packs_exist():
    packs = get_supported_sport_feature_packs()
    for key in ("nascar", "formula_1", "formula_e", "indycar", "motogp"):
        assert key in packs


def test_combat_sports_specific_packs_exist():
    packs = get_supported_sport_feature_packs()
    for key in ("combat_sports", "ufc_mma", "mma", "ufc", "boxing"):
        assert key in packs


def test_thin_sport_packs_exist():
    packs = get_supported_sport_feature_packs()
    for key in ("afl", "badminton", "darts", "handball", "lacrosse", "pickleball",
                "rugby", "snooker", "volleyball", "water_polo"):
        assert key in packs
