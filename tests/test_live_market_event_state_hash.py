from live_market_intelligence.fixtures.synthetic import synthetic_live_state_rows, synthetic_odds_rows
from live_market_intelligence.normalization.event_state_hash import event_state_hash
from live_market_intelligence.normalization.market_state_hash import market_state_hash


def test_state_hashes_are_stable_for_same_normalized_facts():
    state = synthetic_live_state_rows()[0]
    market = synthetic_odds_rows()[0]
    assert event_state_hash(state) == event_state_hash(dict(state))
    assert market_state_hash(market) == market_state_hash(dict(market))
