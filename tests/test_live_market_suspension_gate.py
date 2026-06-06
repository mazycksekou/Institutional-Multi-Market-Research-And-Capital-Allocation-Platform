from live_market_intelligence.gates.suspension_risk_gate import suspension_risk_gate


def test_suspension_gate_blocks_suspended_or_halted_markets():
    result = suspension_risk_gate([{"market_status": "suspended"}])
    assert result["ok"] is False
    assert result["alert_type"] == "NO_BET_MARKET_SUSPENDED"
