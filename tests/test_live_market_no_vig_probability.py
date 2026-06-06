from live_market_intelligence.metrics.no_vig_probability import no_vig_probability


def test_no_vig_probability_normalizes_market_probabilities():
    result = no_vig_probability({"home": 0.55, "away": 0.55})
    assert result["ok"] is True
    assert round(sum(result["no_vig_probabilities"].values()), 6) == 1.0
    assert result["market_hold"] > 0
