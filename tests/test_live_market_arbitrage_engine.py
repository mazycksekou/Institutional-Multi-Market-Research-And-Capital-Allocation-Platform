from live_market_intelligence.engines.arbitrage_engine import detect_arbitrage_alert
from live_market_intelligence.fixtures.synthetic import synthetic_odds_rows


def test_arbitrage_engine_emits_confirmed_alert_without_execution():
    alert = detect_arbitrage_alert(synthetic_odds_rows())
    assert alert["ok"] is True
    assert alert["alert_type"] == "CONFIRMED_ARBITRAGE_ALERT"
    assert alert["execution_allowed"] is False
