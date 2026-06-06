from live_market_intelligence.reports import (
    build_live_arbitrage_report,
    build_live_edge_report,
    build_provider_latency_report,
    build_source_policy_matrix,
)


def test_live_market_reports_include_safety_floor():
    reports = [
        build_live_arbitrage_report(),
        build_live_edge_report(),
        build_provider_latency_report(),
        build_source_policy_matrix(),
    ]
    for report in reports:
        assert report["provider_write"] is False
        assert report["execution_allowed"] is False
        assert report["raw_payload_included"] is False
