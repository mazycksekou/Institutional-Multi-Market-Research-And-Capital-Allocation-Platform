from live_market_intelligence.core import ACCEPTED_INGESTION_DECISION
from live_market_intelligence.gates.source_policy_gate import source_policy_gate


def test_source_policy_gate_allows_only_accepted_read_only_ingestion():
    assert source_policy_gate(ACCEPTED_INGESTION_DECISION)["ok"] is True
    blocked = source_policy_gate("policy_blocked")
    assert blocked["ok"] is False
    assert blocked["alert_type"] == "NO_BET_SOURCE_POLICY_BLOCKED"
    assert blocked["provider_write"] is False
