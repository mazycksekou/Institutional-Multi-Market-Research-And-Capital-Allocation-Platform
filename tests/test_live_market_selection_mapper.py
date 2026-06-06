from live_market_intelligence.normalization.selection_mapper import map_selection


def test_selection_mapper_builds_canonical_selection_id():
    result = map_selection("Over 47.5", event_id="evt_1", market_type="total")
    assert result["ok"] is True
    assert result["canonical_selection_id"].startswith("sel_")
    assert result["selection_side"] == "over"
