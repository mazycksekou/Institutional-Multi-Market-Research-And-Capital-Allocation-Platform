from live_market_intelligence.gates.bad_line_gate import bad_line_gate


def test_bad_line_gate_blocks_large_consensus_deviation():
    rows = [{"decimal_odds": 10.0}, {"decimal_odds": 1.1}]
    result = bad_line_gate(rows)
    assert result["ok"] is False
    assert result["alert_type"] == "NO_BET_BAD_LINE_RISK"
