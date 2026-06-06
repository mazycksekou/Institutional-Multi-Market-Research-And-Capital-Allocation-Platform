from live_market_intelligence.engines.exposure_engine import simulate_exposure


def test_exposure_engine_simulates_without_provider_execution():
    exposure = simulate_exposure([{"sport": "basketball_nba", "event_id": "evt_1", "market_id": "mkt_1", "suggested_stake": 0.0}])
    assert exposure.bankroll_at_risk_simulated == 0.0
    assert exposure.max_alerted_stake == 0.0
