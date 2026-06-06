from live_market_intelligence.core import build_final_report


def test_live_arbitrage_edge_final_report_captures_required_evidence():
    report = build_final_report(branch_name="live-arbitrage-edge-standard", commit_hash="test")
    assert report["final_verdict"] == "LIVE_ARBITRAGE_EDGE_STANDARD_COMPLETE"
    assert report["module_name"] == "live_market_intelligence"
    assert report["read_only_mode"] is True
    assert report["provider_write"] is False
    assert report["execution_allowed"] is False
    assert report["supported_sports_count"] >= 18
    assert report["replay_certification_status"] == "passed"
