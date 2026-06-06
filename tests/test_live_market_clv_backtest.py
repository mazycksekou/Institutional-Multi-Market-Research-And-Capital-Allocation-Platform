from live_market_intelligence.replay.clv_backtest import calculate_clv_metrics


def test_clv_backtest_reports_positive_closing_line_value():
    result = calculate_clv_metrics(2.0, 2.1)
    assert result["ok"] is True
    assert result["positive_clv"] is True
    assert result["provider_write"] is False
