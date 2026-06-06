from live_market_intelligence.metrics.implied_probability import break_even_probability, implied_probability_from_american


def test_implied_probability_from_decimal_and_american_prices():
    assert round(break_even_probability(2.0)["break_even_probability"], 4) == 0.5
    assert round(implied_probability_from_american(100)["implied_probability"], 4) == 0.5
