from live_market_intelligence.metrics.freshness_latency_clock import evaluate_clock_sync, evaluate_freshness, evaluate_latency


def test_freshness_latency_and_clock_checks_block_unsafe_states():
    assert evaluate_freshness({"odds_age_ms": 100})["ok"] is True
    assert evaluate_freshness({"odds_age_ms": 2000})["alert_type"] == "NO_BET_STALE_ODDS"
    assert evaluate_latency(1500)["alert_type"] == "NO_BET_PROVIDER_LATENCY_TOO_HIGH"
    assert evaluate_clock_sync(800)["alert_type"] == "NO_BET_CLOCK_UNSAFE"
