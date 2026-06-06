from live_market_intelligence.normalization.market_mapper import map_market_type


def test_market_mapper_supports_requested_market_families():
    assert map_market_type("Asian Handicap")["canonical_market_type"] == "asian_handicap"
    assert map_market_type("make/miss cut")["canonical_market_type"] == "make_miss_cut"
    assert map_market_type("unsupported market")["ok"] is False
