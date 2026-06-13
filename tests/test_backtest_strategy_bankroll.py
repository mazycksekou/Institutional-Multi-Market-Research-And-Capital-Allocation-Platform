from automation_scheduler.backtest_strategy_bankroll import (
    decide_backtest_bet,
    simulate_backtest_bankroll,
    summarize_strategy_bankroll_report,
)
from automation_scheduler.backtesting_engine import run_backtest


def test_decide_backtest_bet_uses_edge_and_probability_thresholds():
    bet = decide_backtest_bet(
        {"edge": 3.0, "model_probability": 0.56},
        min_edge_percent=1.0,
        min_model_probability=0.52,
    )
    no_bet = decide_backtest_bet(
        {"edge": 0.5, "model_probability": 0.56},
        min_edge_percent=1.0,
        min_model_probability=0.52,
    )

    assert bet["decision"] == "bet"
    assert no_bet["decision"] == "no_bet"
    assert "edge_below_threshold" in no_bet["reasons"]


def test_simulate_backtest_bankroll_tracks_roi_drawdown_and_buckets():
    report = simulate_backtest_bankroll(
        [
            {
                "event_id": "e1",
                "odds": 100,
                "model_probability": 0.57,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "win",
                "clv_percent": 2.0,
            },
            {
                "event_id": "e2",
                "odds": -110,
                "model_probability": 0.54,
                "ev_percent": 2.0,
                "paper_stake": 10,
                "result_status": "loss",
                "clv_percent": -1.0,
            },
        ],
        starting_bankroll=100,
        unit_size=10,
    )

    assert report["bets"] == 2
    assert report["rows_seen"] == 2
    assert report["total_staked"] == 20
    assert report["profit_loss"] < 1
    assert "bankroll_curve" in report
    assert report["edge_buckets"]
    assert report["clv_buckets"]


def test_strategy_bankroll_summary_is_compact():
    report = simulate_backtest_bankroll(
        [
            {
                "event_id": "e1",
                "odds": 100,
                "model_probability": 0.57,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "win",
            }
        ],
        starting_bankroll=100,
        unit_size=10,
    )
    summary = summarize_strategy_bankroll_report(report)

    assert summary["bets"] == 1
    assert summary["ending_bankroll"] == 110
    assert "bankroll_curve" not in summary


def test_run_backtest_includes_strategy_bankroll_report(tmp_path):
    result = run_backtest(
        model_id="strategy-bankroll",
        rows=[
            {
                "event_id": "e1",
                "market_type": "moneyline",
                "odds": 100,
                "closing_odds": -110,
                "model_probability": 0.57,
                "ev_percent": 3.0,
                "paper_stake": 10,
                "result_status": "win",
                "features": {"pace": 99.1},
            }
        ],
        base_data_dir=str(tmp_path),
    )

    assert result["strategy_bankroll_summary"]["bets"] == 1
    assert result["strategy_bankroll_summary"]["ending_bankroll"] == 1010
    assert result["strategy_bankroll_report"]["decisions"][0]["event_id"] == "e1"
