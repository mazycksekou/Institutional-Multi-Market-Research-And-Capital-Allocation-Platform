from live_market_intelligence.alerts.alert_deduplicator import AlertDeduplicator


def test_alert_deduplicator_suppresses_duplicate_market_alerts():
    deduper = AlertDeduplicator()
    alert = {"event_id": "evt_1", "market_id": "mkt_1", "selection_ids": ["sel_1"], "book": "A"}
    assert deduper.should_emit(alert) is True
    assert deduper.should_emit(dict(alert)) is False
