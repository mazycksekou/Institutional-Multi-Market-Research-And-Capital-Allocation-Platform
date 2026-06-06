from live_market_intelligence.metrics.arbitrage_math import detect_three_way_arbitrage, detect_two_way_arbitrage
from live_market_intelligence.fixtures.synthetic import synthetic_odds_rows


def test_arbitrage_math_detects_two_way_synthetic_opportunity():
    result = detect_two_way_arbitrage(synthetic_odds_rows())
    assert result["ok"] is True
    assert result["arb_exists"] is True
    assert result["provider_write"] is False


def test_arbitrage_math_detects_three_way_when_three_outcomes_are_present():
    rows = [
        {"selection": "home", "book": "A", "decimal_odds": 3.4},
        {"selection": "draw", "book": "B", "decimal_odds": 3.4},
        {"selection": "away", "book": "C", "decimal_odds": 3.4},
    ]
    assert detect_three_way_arbitrage(rows)["arb_exists"] is True
