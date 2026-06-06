from live_market_intelligence.contracts.live_state_snapshot import synthetic_live_state_rows


def test_live_state_snapshot_contract_has_state_hash_and_no_raw_payload():
    row = synthetic_live_state_rows()[0]
    assert row["state_snapshot_id"]
    assert row["event_state_hash"]
    assert row["game_status"] == "live"
    assert row["live_state_age_ms"] >= 0
    assert "raw_payload" not in row
