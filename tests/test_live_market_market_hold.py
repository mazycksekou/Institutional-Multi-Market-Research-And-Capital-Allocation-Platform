from live_market_intelligence.metrics.market_hold import market_hold


def test_market_hold_reports_vig_from_decimal_prices():
    result = market_hold([1.9, 1.9])
    assert result["ok"] is True
    assert result["market_hold"] > 0
