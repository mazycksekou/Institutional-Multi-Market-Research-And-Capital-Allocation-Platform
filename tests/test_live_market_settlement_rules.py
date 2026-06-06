from live_market_intelligence.contracts.settlement_rules import default_settlement_rule


def test_settlement_rule_contract_is_canonical_and_replay_safe():
    rule = default_settlement_rule("nba", "moneyline")
    assert rule.sport == "basketball_nba"
    assert rule.market_type == "moneyline"
    assert rule.settlement_rule_id.startswith("sr_")
    assert rule.source_policy_status == "accepted_for_replay_only"
