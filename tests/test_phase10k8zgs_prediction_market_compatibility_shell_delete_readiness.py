from __future__ import annotations

import asyncio
import importlib
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]

DOCS = {
    "PHASE10K8ZGS_PREDICTION_MARKET_COMPATIBILITY_SHELL_DELETE_READINESS.md": [
        "Big-Picture Architecture",
        "Runtime Dependency Scan",
        "Delete-Readiness Classification",
        "Canonical Ownership Verification",
        "Compatibility Verification",
        "delete-ready",
        "test-blocked",
        "runtime-blocked",
        "compatibility-blocked",
        "src.services.prediction_market_runtime_bridge",
        "src.providers.prediction_markets",
        "src.connectors.prediction_market_data",
    ],
    "PREDICTION_MARKET_COMPATIBILITY_IMPORT_SCAN_AFTER_10K8ZGS.md": [
        "automation_scheduler/__init__.py",
        "scheduler_runner.py",
        "settlement_discovery.py",
        "calibration_collector.py",
        "prediction_market_outcome_candidates.py",
        "kalshi_client.py",
    ],
    "PREDICTION_MARKET_COMPATIBILITY_TEST_REDIRECTION_AFTER_10K8ZGS.md": [
        "tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py",
        "tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py",
        "tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py",
        "tests/test_screenshot_analysis.py",
    ],
    "PREDICTION_MARKET_COMPATIBILITY_DELETE_READINESS_AFTER_10K8ZGS.md": [
        "kalshi_client.py",
        "providers/kalshi_provider.py",
        "betting_providers/kalshi_api.py",
        "automation_scheduler/kalshi_readonly_adapter.py",
        "automation_scheduler/kalshi_market_provider.py",
        "runtime-blocked",
        "test-blocked",
        "compatibility-blocked",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_docs_exist_and_include_blocker_classifications() -> None:
    for relative, fragments in DOCS.items():
        text = _read(ROOT / relative)
        for fragment in fragments:
            assert fragment in text, f"missing {fragment!r} in {relative}"


def test_canonical_prediction_market_surfaces_import_and_legacy_shells_stay_disabled() -> None:
    bridge = importlib.import_module("src.services.prediction_market_runtime_bridge")
    providers_pkg = importlib.import_module("src.providers.prediction_markets")
    connectors_pkg = importlib.import_module("src.connectors.prediction_market_data")

    assert bridge is not None
    assert providers_pkg is not None
    assert connectors_pkg is not None

    client = importlib.import_module("kalshi_client")
    provider = importlib.import_module("providers.kalshi_provider")
    betting_api = importlib.import_module("betting_providers.kalshi_api")

    assert hasattr(client, "describe_kalshi_client")
    assert hasattr(provider, "describe_kalshi_provider")
    assert hasattr(betting_api, "KalshiApiAdapter")
    assert hasattr(bridge, "KalshiReadonlyAdapter")
    assert hasattr(bridge, "get_kalshi_snapshot")

    client_description = client.describe_kalshi_client()
    provider_description = provider.describe_kalshi_provider()
    assert client_description["live_access_enabled"] is False
    assert client_description["canonical_provider"] == "prediction_market"
    assert provider_description["canonical_provider"] == "prediction_market"
    assert provider_description["disabled_client"]["live_access_enabled"] is False

    adapter = betting_api.KalshiApiAdapter()
    assert adapter.enabled is False
    assert adapter.configured is True
    assert adapter.private_configured is False

    with pytest.raises(ConnectorDisabledError):
        asyncio.run(adapter.get_supported_sports())

    with pytest.raises(ConnectorDisabledError):
        asyncio.run(adapter.get_market_events())

    readonly_adapter = bridge.KalshiReadonlyAdapter()
    config = readonly_adapter.validate_config()
    health = readonly_adapter.health_check()
    assert config["ok"] is False
    assert config["status"] == "provider_disabled"
    assert health["ok"] is True
    assert health["live_calls_enabled"] is False

    with pytest.raises(ConnectorDisabledError):
        readonly_adapter.fetch_markets()

    with pytest.raises(ConnectorDisabledError):
        readonly_adapter.fetch_events()

    with pytest.raises(ConnectorDisabledError):
        readonly_adapter.fetch_snapshot()

    snapshot = bridge.get_kalshi_snapshot(readonly_adapter)
    assert snapshot["ok"] is True
    assert snapshot["dry_run"] is True
    assert snapshot["provider_id"] == "kalshi_prediction_market"

    assert "ConnectorDisabledError" in _read(ROOT / "kalshi_client.py")
    assert "requests = SimpleNamespace(get=None)" in _read(ROOT / "providers" / "kalshi_provider.py")
    assert "ConnectorDisabledError" in _read(ROOT / "betting_providers" / "kalshi_api.py")
    assert "ConnectorDisabledError" in _read(ROOT / "automation_scheduler" / "kalshi_readonly_adapter.py")
    assert "KalshiReadonlyAdapter" in _read(ROOT / "automation_scheduler" / "kalshi_market_provider.py")
