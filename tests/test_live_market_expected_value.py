from live_market_intelligence.metrics.expected_value import edge, expected_value


def test_expected_value_and_edge_are_positive_for_model_overlay():
    result = expected_value(0.55, 2.1)
    assert result["ok"] is True
    assert result["expected_value"] > 0
    assert edge(0.55, 2.1)["edge"] > 0
