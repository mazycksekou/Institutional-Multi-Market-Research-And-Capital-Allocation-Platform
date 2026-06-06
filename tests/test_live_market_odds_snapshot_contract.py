from live_market_intelligence.contracts.odds_snapshot import synthetic_odds_rows


def test_odds_snapshot_contract_has_normalized_read_only_fields():
    row = synthetic_odds_rows()[0]
    assert row["snapshot_id"]
    assert row["canonical_event_id"]
    assert row["canonical_market_id"]
    assert row["decimal_odds"] > 1
    assert row["source_policy_status"] == "accepted_for_read_only_normalized_ingestion"
    assert "raw_payload" not in row
