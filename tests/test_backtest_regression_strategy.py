from automation_scheduler.backtest_strategy_bankroll import (
    apply_regression_strategy_to_rows,
    calculate_regression_probability,
    simulate_backtest_bankroll,
)
from automation_scheduler.backtesting_engine import run_backtest


def test_calculate_regression_probability_from_feature_weights():
    result = calculate_regression_probability(
        {
            "features": {
                "pace_edge": 2.0,
                "injury_edge": -1.0,
            }
        },
        intercept=0.5,
        feature_weights={
            "pace_edge": 0.02,
            "injury_edge": 0.03,
        },
    )

    assert result["probability"] == 0.51
    assert result["contributions"]["pace_edge"] == 0.04
    assert result["contributions"]["injury_edge"] == -0.03


def test_regression_probability_clamps_to_reasonable_probability_bounds():
    result = calculate_regression_probability(
        {"features": {"steam": 100}},
        intercept=0.5,
        feature_weights={"steam": 1.0},
        probability_floor=0.05,
        probability_ceiling=0.95,
    )

    assert result["probability"] == 0.95


def test_apply_regression_strategy_to_rows_sets_model_probability():
    rows = apply_regression_strategy_to_rows(
        [
            {
                "event_id": "e1",
                "features": {"pace_edge": 2.0},
                "model_probability": 0.4,
            }
        ],
        intercept=0.5,
        feature_weights={"pace_edge": 0.02},
    )

    assert rows[0]["model_probability"] == 0.54
    assert rows[0]["regression_probability"] == 0.54
    assert rows[0]["regression_strategy"]["strategy"] == "transparent_weighted_regression_probability"


def test_apply_regression_strategy_can_preserve_existing_probability():
    rows = apply_regression_strategy_to_rows(
        [
            {
                "event_id": "e1",
                "features": {"pace_edge": 2.0},
                "model_probability": 0.6,
            }
        ],
        intercept=0.5,
        feature_weights={"pace_edge": 0.02},
        override_existing_probability=False,
    )

    assert rows[0]["model_probability"] == 0.6
    assert rows[0]["regression_probability"] == 0.54


def test_bankroll_simulation_uses_regression_probability_after_apply():
    rows = apply_regression_strategy_to_rows(
        [
            {
                "event_id": "e1",
                "odds": 100,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "win",
                "features": {"pace_edge": 2.0},
            }
        ],
        intercept=0.5,
        feature_weights={"pace_edge": 0.02},
    )

    report = simulate_backtest_bankroll(
        rows,
        starting_bankroll=100,
        unit_size=10,
        min_model_probability=0.53,
    )

    assert report["bets"] == 1
    assert report["ending_bankroll"] == 110


def test_run_backtest_accepts_strategy_config_and_reports_it(tmp_path):
    result = run_backtest(
        model_id="regression-hook",
        rows=[
            {
                "event_id": "e1",
                "market_type": "moneyline",
                "odds": 100,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "win",
                "features": {"pace_edge": 2.0},
            }
        ],
        base_data_dir=str(tmp_path),
        strategy_config={
            "intercept": 0.5,
            "feature_weights": {"pace_edge": 0.02},
        },
    )

    assert result["strategy_config"]["intercept"] == 0.5
    assert result["strategy_bankroll_summary"]["bets"] == 1
    assert result["strategy_bankroll_report"]["decisions"][0]["model_probability"] == 0.54
