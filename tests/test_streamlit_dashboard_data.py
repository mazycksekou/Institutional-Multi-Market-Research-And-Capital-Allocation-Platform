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
    make_arrow_safe_table_rows,
    make_arrow_safe_value,
    make_historical_projection_metric_rows,
    parse_feature_weights,
    row_matches_profile,
    run_sqlite_projection_for_dashboard,
    save_historical_upload_for_import,
    summarize_backtest_result,
    build_bankroll_curve_rows,
    classify_market_family,
    calculate_field_coverage,
    build_market_readiness_report,
    get_sqlite_data_explorer_snapshot_for_dashboard,
    get_required_field_groups_for_market,
)


def test_easy_labels_include_bankroll_language():
    assert EASY_LABELS["bankroll"] == "Portfolio Value"
    assert EASY_LABELS["bankroll_curve"] == "Line that shows portfolio value going up or down"


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


def test_make_arrow_safe_value_handles_list():
    import json

    val = make_arrow_safe_value([1, 2, 3])
    assert isinstance(val, str)
    assert json.loads(val) == [1, 2, 3]


def test_make_arrow_safe_value_handles_dict():
    import json

    d = {"b": 2, "a": 1}
    val = make_arrow_safe_value(d)
    parsed = json.loads(val)
    assert parsed == {"a": 1, "b": 2}  # sorted keys


def test_make_arrow_safe_value_handles_int():
    val = make_arrow_safe_value(5)
    assert isinstance(val, str)
    assert val == "5"


def test_make_arrow_safe_value_handles_bool():
    val = make_arrow_safe_value(True)
    assert isinstance(val, str)
    assert val == "True"


def test_make_arrow_safe_value_handles_none():
    val = make_arrow_safe_value(None)
    assert isinstance(val, str)
    assert val == "None"


def test_make_arrow_safe_table_rows_converts_nested():
    rows = [
        {"sports": ["soccer"], "value": 5, "nested": {"a": 1}},
    ]
    safe = make_arrow_safe_table_rows(rows)
    assert isinstance(safe[0]["sports"], str)
    assert isinstance(safe[0]["value"], str)   # int now becomes string
    assert isinstance(safe[0]["nested"], str)


def test_make_arrow_safe_table_rows_does_not_mutate():
    original = [{"value": [1, 2]}]
    safe = make_arrow_safe_table_rows(original)
    assert isinstance(original[0]["value"], list)
    assert isinstance(safe[0]["value"], str)


# ── Phase 10H10 – Data Explorer helpers ──────────────────────────────────


def test_classify_market_family_identifies_1x2():
    assert classify_market_family("1x2") == "moneyline_or_1x2"


def test_classify_market_family_identifies_moneyline():
    assert classify_market_family("moneyline") == "moneyline_or_1x2"


def test_classify_market_family_identifies_runline():
    assert classify_market_family("runline") == "spread_or_runline"


def test_classify_market_family_identifies_spread():
    assert classify_market_family("spread") == "spread_or_runline"


def test_classify_market_family_identifies_total():
    assert classify_market_family("total") == "total"
    assert classify_market_family("over/under") == "total"


def test_classify_market_family_identifies_player_prop():
    assert (
        classify_market_family("player points prop")
        == "player_prop"
    )
    assert (
        classify_market_family("player points", selection="LeBron James")
        == "player_prop"
    )
    assert classify_market_family("unknown") == "unknown"


def test_calculate_field_coverage_counts():
    rows = [
        {"sport": "soccer", "league": "EPL", "event_date": "2023-01-01",
         "home_team": "A", "away_team": "B"},
        {"sport": "soccer", "league": "EPL", "event_date": None,
         "home_team": None, "away_team": None},
    ]
    groups = {"core_event": ["sport", "league", "event_date", "home_team",
                             "away_team"]}
    cov = calculate_field_coverage(rows, groups)
    assert cov["sport"]["present_count"] == 2
    assert cov["sport"]["coverage_percent"] == 100.0
    assert cov["event_date"]["present_count"] == 1
    assert cov["event_date"]["status"] == "partial"


def test_build_market_readiness_report_football_data_rows():
    rows = [
        {
            "sport": "soccer",
            "league": "EPL",
            "event_date": "2023-08-12",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "market": "1X2",
            "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "final_result": "H",
            "winner": "Home",
            "home_score": 3,
            "away_score": 1,
        }
    ]
    report = build_market_readiness_report(rows)
    assert report["settlement_ready"] is True
    assert report["line_movement_ready"] is False
    assert report["player_prop_ready"] is False
    assert report["team_stats_ready"] is False
    assert report["projection_ready"] is True


def test_get_sqlite_data_explorer_snapshot_for_dashboard_works(tmp_path):
    from automation_scheduler.historical_odds_sqlite import (
        connect_historical_odds_db, initialize_historical_odds_db,
        import_historical_odds_file_to_sqlite,
    )
    # Create a tiny Football‑Data CSV
    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n"
    )
    file_path = tmp_path / "mini.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    db_path = tmp_path / "test_explorer.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    import_historical_odds_file_to_sqlite(
        conn, "football_data_uk", file_path
    )
    conn.close()

    snapshot = get_sqlite_data_explorer_snapshot_for_dashboard(db_path)
    assert snapshot["ok"] is True
    assert snapshot["total_rows"] >= 3
    assert "soccer" in snapshot["sports"]
    assert snapshot["readiness"]["settlement_ready"] is True
    assert snapshot["readiness"]["line_movement_ready"] is False
    assert snapshot["readiness"]["player_prop_ready"] is False
    # Check sample rows are Arrow‑safe (all values are strings)
    for sample in snapshot.get("sample_rows", []):
        for val in sample.values():
            assert isinstance(val, str)


def test_data_explorer_header_no_bad_title():
    # Verify that the title line in streamlit_app does not contain "??"
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'title("?? Betting Model Operator Dashboard")' not in content
    assert 'title("Betting Model Operator Dashboard")' in content


def test_line_movement_readiness_header_in_streamlit_app():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("Line Movement Readiness")' in content


def test_line_movement_baseline_testing_note_in_streamlit_app():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert (
        "Baseline testing can run with decision odds only."
        in content
    )


def test_get_line_volatility_snapshot_for_dashboard(tmp_path):
    from automation_scheduler.streamlit_dashboard_data import (
        get_line_volatility_snapshot_for_dashboard,
        import_historical_file_to_sqlite_for_dashboard,
    )

    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n"
    )
    file_path = tmp_path / "vol_dash.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    db_path = tmp_path / "vol_dash.db"
    import_historical_file_to_sqlite_for_dashboard(
        db_path, "football_data_uk", file_path
    )
    snap = get_line_volatility_snapshot_for_dashboard(db_path)
    assert snap.get("ok") is True
    assert snap["groups_seen"] >= 1
    assert "high_volatility_count" in snap
    assert "medium_volatility_count" in snap
    assert "low_volatility_count" in snap
    assert "unknown_volatility_count" in snap


def test_streamlit_app_contains_line_volatility():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("Line Volatility")' in content


def test_streamlit_app_contains_volatility_explanation():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert (
        "Line volatility shows how far the line moved up"
        in content
    )


def test_get_line_movement_snapshot_for_dashboard(tmp_path):
    from automation_scheduler.streamlit_dashboard_data import (
        get_line_movement_snapshot_for_dashboard,
        import_historical_file_to_sqlite_for_dashboard,
    )

    # Create minimal data
    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n"
    )
    file_path = tmp_path / "lm_test.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    db_path = tmp_path / "lm_test.db"
    import_historical_file_to_sqlite_for_dashboard(
        db_path, "football_data_uk", file_path
    )

    snap = get_line_movement_snapshot_for_dashboard(db_path)
    assert snap.get("ok") is True
    assert snap["total_snapshots"] >= 3
    assert snap["decision_snapshots"] >= 3
    # Football‑Data has no opening/closing, so these should be 0
    assert snap["opening_snapshots"] == 0
    assert snap["closing_snapshots"] == 0
    assert snap["line_movement_ready"] is False
    assert snap["clv_ready"] is False


def test_get_required_field_groups_for_market_returns_dict():
    groups = get_required_field_groups_for_market("moneyline_or_1x2")
    assert "core_event" in groups
    assert "line_core" in groups
    assert "settlement" in groups
    assert "projection_control" in groups

    groups2 = get_required_field_groups_for_market("player_prop")
    assert "player_stats" in groups2


def test_calculate_field_coverage_serializable():
    rows = [{"field1": 1, "field2": None}]
    groups = {"g": ["field1", "field2"]}
    cov = calculate_field_coverage(rows, groups)
    import json
    json.dumps(cov)  # must not raise


# ── Phase 10H10 – Dashboard wording / layout cleanup ─────────────────────


def test_portfolio_performance_curve_text_exists():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("Portfolio Performance Curve")' in content


def test_performance_data_table_text_exists():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'expander("Performance Data Table"' in content


def test_money_up_down_graph_no_longer_present():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("Money Up/Down Graph")' not in content


def test_graph_table_no_longer_present():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'expander("Graph table"' not in content


def test_operator_summary_has_system_status():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("System Status")' in content


def test_operator_summary_has_portfolio_snapshot():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("Portfolio Snapshot")' in content


def test_operator_summary_has_what_this_means():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("What This Means")' in content


def test_easy_labels_bankroll_label_updated():
    from automation_scheduler.streamlit_dashboard_data import EASY_LABELS
    assert EASY_LABELS["bankroll"] == "Portfolio Value"


def test_easy_labels_profit_loss_label_updated():
    from automation_scheduler.streamlit_dashboard_data import EASY_LABELS
    assert EASY_LABELS["profit_loss"] == "Net Result"


def test_easy_labels_bets_label_updated():
    from automation_scheduler.streamlit_dashboard_data import EASY_LABELS
    assert EASY_LABELS["bets"] == "Decisions"


def test_easy_labels_no_bets_label_updated():
    from automation_scheduler.streamlit_dashboard_data import EASY_LABELS
    assert EASY_LABELS["no_bets"] == "Skipped Decisions"


# ── Phase 10H11 – Feature Control Lab ──────────────────────────────────


def test_get_feature_control_profiles_includes_baseline_odds_custom():
    from automation_scheduler.streamlit_dashboard_data import (
        get_feature_control_profiles,
    )
    profiles = get_feature_control_profiles()
    values = [p["value"] for p in profiles]
    assert "available_baseline" in values
    assert "odds_only" in values
    assert "custom" in values


def test_get_never_feature_fields_includes_leakage():
    from automation_scheduler.streamlit_dashboard_data import (
        get_never_feature_fields,
    )
    fields = get_never_feature_fields()
    assert "final_result" in fields
    assert "winner" in fields
    assert "closing_odds" in fields
    assert "clv" in fields
    assert "profit_loss" in fields


def test_apply_feature_control_to_row_removes_leakage():
    from automation_scheduler.streamlit_dashboard_data import (
        build_feature_control_config,
        apply_feature_control_to_row,
        get_never_feature_fields,
    )
    config = build_feature_control_config()
    row = {
        "sport": "nba",
        "final_result": "H",
        "winner": "Home",
        "profit_loss": 10,
        "features_known_at_decision_time": {"model_probability": 0.6},
    }
    out = apply_feature_control_to_row(row, config)
    # Ensure leakage fields are not inside the snapshot
    snap = out.get("features_known_at_decision_time", {})
    for leak in get_never_feature_fields():
        assert leak not in snap
    # But they remain at top level for grading
    assert out["final_result"] == "H"
    assert out["winner"] == "Home"


def test_apply_feature_control_to_row_does_not_mutate_input():
    from automation_scheduler.streamlit_dashboard_data import (
        build_feature_control_config,
        apply_feature_control_to_row,
    )
    config = build_feature_control_config()
    row = {
        "sport": "nba",
        "final_result": "H",
        "features_known_at_decision_time": {"model_probability": 0.6},
    }
    orig_id = id(row["features_known_at_decision_time"])
    apply_feature_control_to_row(row, config)
    assert id(row["features_known_at_decision_time"]) == orig_id
    assert row["final_result"] == "H"


def test_summarize_feature_control_impact_returns_stable_keys():
    from automation_scheduler.streamlit_dashboard_data import (
        build_feature_control_config,
        summarize_feature_control_impact,
    )
    config = build_feature_control_config()
    rows = [
        {"sport": "nba", "features_known_at_decision_time": {"model_probability": 0.6}},
        {"sport": "mlb", "features_known_at_decision_time": {"model_probability": 0.4}},
    ]
    impact = summarize_feature_control_impact(rows, config)
    assert "profile" in impact
    assert "rows_seen" in impact
    assert "available_feature_count" in impact
    assert "missing_feature_count" in impact
    assert "removed_feature_count" in impact
    assert "operator_interpretation" in impact
    assert isinstance(impact["operator_interpretation"], str)


def test_summarize_feature_control_impact_operator_interpretation():
    from automation_scheduler.streamlit_dashboard_data import (
        build_feature_control_config,
        summarize_feature_control_impact,
    )
    config = build_feature_control_config()
    rows = []
    impact = summarize_feature_control_impact(rows, config)
    assert "This profile can test a basic available-data baseline" in impact["operator_interpretation"]


def test_get_dashboard_tab_instructions_contains_all_tabs():
    from automation_scheduler.streamlit_dashboard_data import (
        get_dashboard_tab_instructions,
    )
    instructions = get_dashboard_tab_instructions()
    tabs = [i["tab"] for i in instructions]
    assert "Instructions" in tabs
    assert "Data Explorer" in tabs
    assert "Model Projection" in tabs
    assert "Data Quality Check" in tabs


def test_get_overall_operator_workflow_steps_returns_ordered():
    from automation_scheduler.streamlit_dashboard_data import (
        get_overall_operator_workflow_steps,
    )
    steps = get_overall_operator_workflow_steps()
    assert len(steps) >= 8
    assert steps[0]["step"] == 1
    assert steps[-1]["step"] == len(steps)


# ── Phase 10H12B – Dashboard helper tests ──────────────────────


def test_get_volatility_result_breakdown_for_dashboard_without_projection_rows_returns_warning(tmp_path):
    from automation_scheduler.streamlit_dashboard_data import (
        get_volatility_result_breakdown_for_dashboard,
    )
    from automation_scheduler.historical_odds_sqlite import (
        connect_historical_odds_db,
        initialize_historical_odds_db,
    )
    from automation_scheduler.historical_line_movement import (
        initialize_line_movement_schema,
    )

    db_path = tmp_path / "empty_vol.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)
    conn.close()

    result = get_volatility_result_breakdown_for_dashboard(db_path)
    assert result["ok"] is True
    assert len(result["warnings"]) > 0
    assert "Row‑level projection results are not available" in result.get("operator_interpretation", "")


def test_volatility_result_breakdown_text_in_streamlit_app():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert 'subheader("Volatility Result Breakdown")' in content


def test_volatility_result_breakdown_explanation_in_streamlit_app():
    with open("streamlit_app.py", encoding="utf-8") as f:
        content = f.read()
    assert (
        "This shows whether low, medium, high, or unknown volatility "
        "produced better results."
    ) in content
    from automation_scheduler.streamlit_dashboard_data import (
        get_overall_operator_workflow_steps,
    )
    steps = get_overall_operator_workflow_steps()
    assert len(steps) >= 8
    assert steps[0]["step"] == 1
    assert steps[-1]["step"] == len(steps)
