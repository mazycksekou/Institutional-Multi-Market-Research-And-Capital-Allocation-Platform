from live_market_intelligence.metrics.odds_converter import american_to_decimal, decimal_to_american


def test_odds_converter_round_trips_common_prices():
    assert american_to_decimal(110)["decimal_odds"] == 2.1
    assert american_to_decimal(-110)["decimal_odds"] > 1.9
    assert decimal_to_american(2.1)["american_odds"] == 110
