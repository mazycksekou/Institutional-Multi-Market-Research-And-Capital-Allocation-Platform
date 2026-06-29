import json

from src.services.streamlit_dashboard_facade import build_canonical_backtest_dataset, summarize_canonical_dataset_report
from src.services.streamlit_dashboard_facade import build_strategy_config_for_row, describe_regression_profiles, get_regression_profile, normalize_strategy_profile_key
from src.services.streamlit_dashboard_facade import run_backtest


def test_normalize_strategy_profile_key_uses_existing_readiness_aliases():
    assert normalize_strategy_profile_key("nba") == "basketball_nba"
    assert normalize_strategy_profile_key("nfl") == "americanfootball_nfl"
    assert normalize_strategy_profile_key("mlb") == "baseball_mlb"
    assert normalize_strategy_profile_key("kalshi") == "prediction_market"


def test_get_regression_profile_can_force_all_sports():
    profile = get_regression_profile(
        sport="nba",
        profile_scope="all_sports",
        all_sports_profile={"intercept": 0.52, "feature_weights": {"generic_edge": 0.01}},
    )

    assert profile["profile_scope"] == "all_sports"
    assert profile["selection_reason"] == "forced_all_sports"
    assert profile["intercept"] == 0.52


def test_get_regression_profile_selects_sport_specific_profile():
    profile = get_regression_profile(
        sport="nba",
        sport_profiles={
            "nba": {
                "intercept": 0.55,
                "feature_weights": {"pace_edge": 0.02},
            }
        },
    )

    assert profile["profile_name"] == "basketball_nba"
    assert profile["profile_scope"] == "sport_specific"
    assert profile["selection_reason"] == "sport_specific_match"
    assert profile["feature_weights"]["pace_edge"] == 0.02


def test_build_strategy_config_for_row_returns_executable_config():
    config = build_strategy_config_for_row(
        {"sport": "nba"},
        sport_profiles={"nba": {"intercept": 0.55, "feature_weights": {"pace_edge": 0.02}}},
    )

    assert config["intercept"] == 0.55
    assert config["profile_name"] == "basketball_nba"
    assert config["profile_scope"] == "sport_specific"


def test_run_backtest_sport_profiles_routes_each_row_to_correct_profile(tmp_path):
    result = run_backtest(
        model_id="sport-profile-proof",
        rows=[
            {
                "event_id": "nba-1",
                "sport": "nba",
                "market_type": "moneyline",
                "odds": 100,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "win",
                "features": {"pace_edge": 2.0},
            },
            {
                "event_id": "mlb-1",
                "sport": "mlb",
                "market_type": "moneyline",
                "odds": 100,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "loss",
                "features": {"starter_edge": 3.0},
            },
        ],
        base_data_dir=str(tmp_path),
        strategy_config={
            "mode": "sport_profiles",
            "profile_scope": "auto",
            "all_sports_profile": {"intercept": 0.5, "feature_weights": {"generic_edge": 0.01}},
            "sport_profiles": {
                "nba": {"intercept": 0.5, "feature_weights": {"pace_edge": 0.02}},
                "mlb": {"intercept": 0.5, "feature_weights": {"starter_edge": 0.03}},
            },
        },
    )

    decisions = result["strategy_bankroll_report"]["decisions"]
    assert decisions[0]["model_probability"] == 0.54
    assert decisions[1]["model_probability"] == 0.59


def test_dataset_builder_reports_sport_coverage(tmp_path):
    artifact = tmp_path / "paper.json"
    output = tmp_path / "latest.jsonl"
    schema = tmp_path / "schema_report.json"

    artifact.write_text(
        json.dumps(
            [
                {"event": "e1", "sport": "nba", "market_type": "moneyline", "odds": 100, "predicted_probability": 0.57},
                {"event": "e2", "market_type": "spread", "odds": -110, "predicted_probability": 0.54},
            ]
        ),
        encoding="utf-8",
    )

    report = build_canonical_backtest_dataset(
        artifact_paths=[artifact],
        output_jsonl_path=output,
        schema_report_path=schema,
    )
    summary = summarize_canonical_dataset_report(report)

    assert summary["field_coverage"]["coverage"]["sport"]["present"] == 1
    assert summary["field_coverage"]["coverage"]["sport"]["missing"] == 1
    assert summary["field_coverage"]["sport_counts"]["UNKNOWN"] == 1


def test_describe_regression_profiles_documents_owners():
    description = describe_regression_profiles()

    assert description["data_readiness_owner"] == "automation_scheduler.data_availability_tiers"
    assert description["strategy_profile_owner"] == "automation_scheduler.backtest_strategy_profiles"
    assert description["public_runner"] == "automation_scheduler.backtesting_engine.run_backtest"
