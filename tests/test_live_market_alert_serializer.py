from live_market_intelligence.alerts.alert_serializer import serialize_alert


def test_alert_serializer_forces_read_only_safety_flags():
    alert = serialize_alert({"alert_type": "EDGE_ALERT", "provider_write": True, "execution_allowed": True})
    assert alert["provider_write"] is False
    assert alert["execution_allowed"] is False
    assert alert["alert_id"].startswith("alert_")
