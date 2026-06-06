from live_market_intelligence.core import SAFETY_FLAGS, build_safety_report


def test_live_market_safety_scan_has_zero_execution_and_provider_write_surfaces():
    report = build_safety_report()
    assert report["safety_scan_passed"] is True
    assert report["execution_surface_count"] == 0
    assert report["provider_write_surface_count"] == 0
    for key, expected in SAFETY_FLAGS.items():
        assert report[key] == expected
