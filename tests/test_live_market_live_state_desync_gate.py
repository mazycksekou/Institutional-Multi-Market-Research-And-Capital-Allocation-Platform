from live_market_intelligence.fixtures.synthetic import synthetic_live_state_rows
from live_market_intelligence.gates.live_state_desync_gate import live_state_desync_gate
from live_market_intelligence.normalization.event_state_hash import event_state_hash


def test_live_state_desync_gate_blocks_conflicting_event_states():
    first = synthetic_live_state_rows()[0]
    second = dict(first, clock="07:01")
    second["event_state_hash"] = event_state_hash(second)
    result = live_state_desync_gate([first, second])
    assert result["ok"] is False
    assert result["alert_type"] == "NO_BET_LIVE_STATE_DESYNC"
