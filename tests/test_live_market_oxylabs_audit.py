from live_market_intelligence.core import build_oxylabs_audit


def test_oxylabs_audit_is_policy_review_only():
    report = build_oxylabs_audit()
    assert report["oxylabs_residential_proxy_used"] is True
    assert report["oxylabs_web_scraper_api_used"] is True
    assert report["oxylabs_calls_attempted"] >= 25
    assert report["oxylabs_calls_successful"] + report["oxylabs_calls_failed"] == report["oxylabs_calls_attempted"]
    assert report["provider_write"] is False
    assert report["raw_html_persisted"] is False
