from automation_scheduler.streamlit_dashboard_data import (
    EASY_LABELS,
    REGRESSION_TACTICS,
    RISK_PRESETS,
    SAFE_DEFAULTS,
    build_strategy_config,
    compact_counts,
    flatten_preview_rows,
    get_available_profile_options,
    get_historical_import_source_options,
    get_historical_sqlite_snapshot_for_dashboard,
    import_historical_file_to_sqlite_for_dashboard,
    make_historical_projection_metric_rows,
    parse_feature_weights,
    row_matches_profile,
    run_sqlite_projection_for_dashboard,
    save_historical_upload_for_import,
    summarize_backtest_result,
    build_bankroll_curve_rows,
)


def test_easy_labels_include_bankroll_language():
    assert EASY_LABELS["bankroll"] == "Money in the account"
    assert EASY_LABELS["bankroll_curve"] == "Line that shows money going up or down"


def test_risk_presets_include_kid_safe_and_conservative():
    assert "Tiny Risk Demo" in RISK_PRESETS
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


# ── Historical SQLite / Projection helpers ──────────────────────────────

def test_get_historical_import_source_options_includes_football_and_mlb():
    opts = get_historical_import_source_options()
    keys = [opt["source_key"] for opt in opts]
    assert "football_data_uk" in keys
    assert "arnav_mlb_odds_scraper" in keys


def test_save_historical_upload_for_import(tmp_path):
    source_key = "football_data_uk"
    filename = "test_upload.csv"
    content = b"dummy,csv,content\n1,2,3"
    result = save_historical_upload_for_import(
        source_key, filename, content, upload_dir=tmp_path
    )
    assert result["ok"] is True
    assert result["source_key"] == source_key
    assert result["filename"] == filename
    assert result["size_bytes"] > 0
    saved_path = tmp_path / source_key / filename
    assert saved_path.exists()


def test_import_historical_file_to_sqlite_for_dashboard_inserts_rows(tmp_path):
    # Create a minimal Football-Data CSV that produces 3 canonical rows
    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n"
    )
    file_path = tmp_path / "test_data.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    db_path = tmp_path / "test_import.db"
    result = import_historical_file_to_sqlite_for_dashboard(
        db_path, "football_data_uk", file_path
    )
    assert result["ok"] is True
    assert result["rows_seen"] == 3
    assert result["rows_inserted"] == 3
    assert result["rows_rejected"] == 0


def test_get_historical_sqlite_snapshot_for_dashboard_after_import(tmp_path):
    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n"
    )
    file_path = tmp_path / "snap.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    db_path = tmp_path / "test_snap.db"
    import_historical_file_to_sqlite_for_dashboard(
        db_path, "football_data_uk", file_path
    )
    snap = get_historical_sqlite_snapshot_for_dashboard(db_path)
    assert snap["ok"] is True
    assert snap["table_counts"].get("historical_odds", 0) >= 1
    filters = snap.get("filter_options", {})
    assert "sports" in filters
    # The football_data_uk importer sets sport to "soccer"
    assert "soccer" in filters.get("sports", [])


def test_run_sqlite_projection_for_dashboard_ok(tmp_path):
    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n"
    )
    file_path = tmp_path / "proj.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    db_path = tmp_path / "test_proj.db"
    import_historical_file_to_sqlite_for_dashboard(
        db_path, "football_data_uk", file_path
    )
    proj = run_sqlite_projection_for_dashboard(db_path)
    assert proj["ok"] is True
    summary = proj["summary"]
    assert summary["rows_loaded"] >= 3
    assert summary["rows_converted"] >= 3


def test_make_historical_projection_metric_rows_returns_keys():
    dummy_summary = {
        "rows_loaded": 100,
        "rows_converted": 95,
        "bets": 10,
        "no_bets": 90,
        "profit_loss": 5.0,
        "roi_percent": 0.5,
        "max_drawdown_percent": 1.0,
        "projection_ready": True,
        "reason": "",
    }
    rows = make_historical_projection_metric_rows(dummy_summary)
    assert len(rows) == 1
    row = rows[0]
    assert row["rows_loaded"] == 100
    assert row["projection_ready"] is True
    assert row["reason"] == ""
