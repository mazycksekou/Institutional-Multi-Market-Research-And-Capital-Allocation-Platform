from live_market_intelligence.engines.edge_engine import detect_edge_alert
from live_market_intelligence.fixtures.synthetic import synthetic_odds_rows


def test_edge_engine_emits_edge_alert_without_stake_execution():
    alert = detect_edge_alert(synthetic_odds_rows()[0], {"model_probability": 0.55, "calibrated_model_probability": 0.55, "confidence": 0.8})
    assert alert["ok"] is True
    assert alert["alert_type"] == "EDGE_ALERT"
    assert alert["suggested_stake"] == 0.0
