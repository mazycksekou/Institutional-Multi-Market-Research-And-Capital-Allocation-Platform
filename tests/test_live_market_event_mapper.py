from live_market_intelligence.normalization.event_mapper import map_event


def test_event_mapper_builds_stable_canonical_event_id():
    first = map_event({"sport": "NBA", "home": "LAL", "away": "BOS", "start_time": "2026-01-01T00:00:00Z"})
    second = map_event({"sport": "nba", "team_a": "BOS", "team_b": "LAL", "event_time": "2026-01-01T00:00:00Z"})
    assert first["ok"] is True
    assert first["canonical_event_id"] == second["canonical_event_id"]
