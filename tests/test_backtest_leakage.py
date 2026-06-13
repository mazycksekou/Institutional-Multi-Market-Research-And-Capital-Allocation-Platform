import pytest

from automation_scheduler.backtest_leakage import (
    assert_backtest_rows_no_hard_leakage,
    evaluate_backtest_row_leakage,
    evaluate_backtest_rows_leakage,
    summarize_backtest_leakage_report,
)
from automation_scheduler.backtesting_engine import run_backtest


def test_sharp_style_allows_top_level_results_and_clv_for_grading():
    result = evaluate_backtest_row_leakage(
        {
            "event_id": "e1",
            "decision_time": "2026-01-01T00:00:00Z",
            "odds": -110,
            "model_probability": 0.55,
            "result_status": "win",
            "closing_odds": -125,
            "clv_percent": 2.1,
            "features": {"pace": 99.1},
        }
    )

    assert result["ok"] is True
    assert "top_level_evaluation_fields_present_allowed_for_grading" in result["warnings"]
    assert "result_status" in result["top_level_evaluation_fields"]
    assert "closing_odds" in result["top_level_evaluation_fields"]


def test_sharp_style_blocks_result_inside_pre_decision_features():
    result = evaluate_backtest_row_leakage(
        {
            "event_id": "e1",
            "decision_time": "2026-01-01T00:00:00Z",
            "odds": -110,
            "model_probability": 0.55,
            "features": {
                "pace": 99.1,
                "final_result": "win",
            },
        }
    )

    assert result["ok"] is False
    assert result["hard_fail_reasons"] == [
        "future_or_settlement_fields_inside_pre_decision_features"
    ]
    assert result["leakage_fields"] == ["final_result"]


def test_sharp_style_warns_not_fails_when_clv_exists_without_decision_time():
    result = evaluate_backtest_row_leakage(
        {
            "event_id": "e1",
            "odds": -110,
            "model_probability": 0.55,
            "closing_odds": -125,
            "features": {"pace": 99.1},
        }
    )

    assert result["ok"] is True
    assert "closing_or_clv_fields_present_without_decision_time_timing_should_be_verified" in result["warnings"]


def test_sharp_style_batch_report_and_summary():
    report = evaluate_backtest_rows_leakage(
        [
            {
                "event_id": "e1",
                "decision_time": "2026-01-01T00:00:00Z",
                "odds": -110,
                "model_probability": 0.55,
                "features": {"pace": 99.1},
            },
            {
                "event_id": "e2",
                "decision_time": "2026-01-01T00:00:00Z",
                "odds": -110,
                "model_probability": 0.55,
                "features": {"result_status": "loss"},
            },
        ]
    )

    summary = summarize_backtest_leakage_report(report)

    assert report["ok"] is False
    assert report["hard_failed_rows"] == [1]
    assert summary["hard_failed_count"] == 1


def test_sharp_style_assert_raises_only_on_hard_leakage():
    assert_backtest_rows_no_hard_leakage(
        [
            {
                "event_id": "e1",
                "odds": -110,
                "model_probability": 0.55,
                "result_status": "win",
                "closing_odds": -125,
                "features": {"pace": 99.1},
            }
        ]
    )

    with pytest.raises(ValueError):
        assert_backtest_rows_no_hard_leakage(
            [
                {
                    "event_id": "e1",
                    "odds": -110,
                    "model_probability": 0.55,
                    "features": {"clv": 3.2},
                }
            ]
        )


def test_backtesting_engine_includes_leakage_report_without_overblocking(tmp_path):
    result = run_backtest(
        model_id="leakage-policy",
        rows=[
            {
                "event_id": "e1",
                "market_type": "moneyline",
                "odds": 120,
                "closing_odds": 100,
                "model_probability": 0.57,
                "result_status": "win",
                "features": {"pace": 99.1},
            }
        ],
        base_data_dir=str(tmp_path),
    )

    assert result["leakage_report"]["ok"] is True
    assert result["leakage_report"]["warning_count"] >= 1
