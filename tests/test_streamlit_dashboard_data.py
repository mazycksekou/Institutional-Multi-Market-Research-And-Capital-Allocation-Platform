from automation_scheduler.streamlit_dashboard_data import (
    EASY_LABELS,
    REGRESSION_TACTICS,
    RISK_PRESETS,
    SAFE_DEFAULTS,
    build_strategy_config,
    compact_counts,
    flatten_preview_rows,
    get_available_profile_options,
    parse_feature_weights,
    row_matches_profile,
    summarize_backtest_result,
    build_bankroll_curve_rows,
)


def test_easy_labels_include_bankroll_language():
    assert EASY_LABELS["bankroll"] == "Money in the account"
    assert EASY_LABELS["bankroll_curve"] == "Line that shows money going up or down"


def test_risk_presets_include_kid_safe_and_conservative():
    assert "Kid-safe demo / Tiny risk" in RISK_PRESETS
    assert "Conservative" in RISK_PRESETS


def test_regression_tactics_include_required_modes():
    assert "Use existing model probability" in REGRESSION_TACTICS
    assert "All-sports regression" in REGRESSION_TACTICS
    assert "Sport-specific regression" in REGRESSION_TACTICS
    assert "Custom feature weights" in REGRESSION_TACTICS


def test_parse_feature_weights_accepts_json_and_pairs():
    assert parse_feature_weights('{"pace_edge": 0.05}') == {"pace_edge": 0.05}
    assert parse_feature_weights("pace_edge=0.05, injury_edge:-0.02") == {
        "pace_edge": 0.05,
        "injury_edge": -0.02,
    }


def test_build_strategy_config_existing_probability_returns_none():
    assert build_strategy_config(tactic="Use existing model probability") is None


def test_build_strategy_config_all_sports():
    config = build_strategy_config(
        tactic="All-sports regression",
        intercept=0.55,
        feature_weights={"edge": 0.1},
    )

    assert config["mode"] == "sport_profiles"
    assert config["profile_scope"] == "all_sports"
    assert config["all_sports_profile"]["intercept"] == 0.55
    assert config["all_sports_profile"]["feature_weights"]["edge"] == 0.1


def test_build_strategy_config_sport_specific_alias():
    config = build_strategy_config(
        tactic="Sport-specific regression",
        profile_key="nba",
    )

    assert config["mode"] == "sport_profiles"
    assert "basketball_nba" in config["sport_profiles"]


def test_row_matches_profile_aliases():
    assert row_matches_profile({"sport": "nba"}, "basketball_nba") is True
    assert row_matches_profile({"sport": "mlb"}, "basketball_nba") is False
    assert row_matches_profile({"sport": "mlb"}, "all_sports") is True


def test_flatten_preview_rows_handles_items_wrapper():
    rows = flatten_preview_rows({"items": [{"a": 1}, {"a": 2}]})

    assert rows == [{"_index": 0, "a": 1}, {"_index": 1, "a": 2}]


def test_compact_counts_counts_unknown():
    rows = [{"sport": "nba"}, {"sport": "nba"}, {"sport": None}]

    assert compact_counts(rows, "sport") == [
        {"value": "nba", "count": 2},
        {"value": "UNKNOWN", "count": 1},
    ]


def test_summarize_backtest_result_and_curve():
    result = {
        "strategy_bankroll_summary": {
            "bets": 2,
            "no_bets": 0,
            "profit_loss": 5,
            "roi_percent": 0.5,
            "max_drawdown_percent": 1.0,
            "starting_bankroll": 1000,
            "ending_bankroll": 1005,
        },
        "strategy_bankroll_report": {
            "decisions": [
                {
                    "event_id": "e1",
                    "sport": "nba",
                    "market": "moneyline",
                    "ending_bankroll": 1010,
                    "profit_loss": 10,
                    "regression_strategy": {"profile": {"selected_profile_key": "basketball_nba"}},
                },
                {
                    "event_id": "e2",
                    "sport": "mlb",
                    "market": "moneyline",
                    "ending_bankroll": 1005,
                    "profit_loss": -5,
                    "regression_strategy": {"profile": {"selected_profile_key": "baseball_mlb"}},
                },
            ]
        },
    }

    summary = summarize_backtest_result(result)
    curve = build_bankroll_curve_rows(result)

    assert summary["bets"] == 2
    assert summary["sport_counts"]["nba"] == 1
    assert summary["profile_counts"]["basketball_nba"] == 1
    assert curve[0]["bankroll"] == 1010
    assert curve[1]["bankroll"] == 1005


def test_get_available_profile_options_has_all_sports():
    values = [item["value"] for item in get_available_profile_options()]

    assert "all_sports" in values
    assert len(values) >= 2
