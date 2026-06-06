from live_market_intelligence.core import SAFETY_FLAGS
from live_market_intelligence.contracts.provider_contracts import assert_read_only_surface, build_provider_registry


def test_read_only_provider_contract_allows_only_fetch_validate_normalize_methods():
    registry = build_provider_registry()
    assert registry
    for provider in registry.values():
        surface = assert_read_only_surface(provider)
        assert surface["ok"], surface
        assert provider.provider_write is False
        assert provider.execution_allowed is False
        payload = provider.fetch_snapshot()
        for key, expected in SAFETY_FLAGS.items():
            assert payload[key] == expected
