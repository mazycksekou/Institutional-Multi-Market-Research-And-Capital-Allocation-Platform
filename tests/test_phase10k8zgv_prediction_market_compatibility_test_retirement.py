from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]

DOC_FRAGMENTS = {
    "PHASE10K8ZGV_PREDICTION_MARKET_COMPATIBILITY_TEST_RETIREMENT.md": [
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "tests/test_kalshi_readonly_adapter.py",
        "tests/test_scheduler_runner.py",
        "legacy shell modules remain on disk",
        "compatibility-oriented tests",
    ],
    "PREDICTION_MARKET_COMPATIBILITY_TEST_RETIREMENT_MAP_AFTER_10K8ZGV.md": [
        "tests/test_kalshi_readonly_adapter.py",
        "tests/test_kalshi_readonly_readiness_contract.py",
        "tests/test_calibration_collector.py",
        "tests/test_scheduler_runner.py",
        "tests/test_kalshi_market_provider.py",
        "tests/test_screenshot_analysis.py",
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
    ],
    "PREDICTION_MARKET_COMPATIBILITY_REFERENCE_SCAN_AFTER_10K8ZGV.md": [
        "Historical Evidence Still Present",
        "kalshi_client.py",
        "providers/kalshi_provider.py",
        "automation_scheduler/kalshi_readonly_adapter.py",
        "automation_scheduler/kalshi_market_provider.py",
    ],
    "PREDICTION_MARKET_DELETE_READINESS_STATUS_AFTER_10K8ZGV.md": [
        "kalshi_client.py",
        "providers/kalshi_provider.py",
        "betting_providers/kalshi_api.py",
        "automation_scheduler/kalshi_readonly_adapter.py",
        "automation_scheduler/kalshi_market_provider.py",
        "compatibility-blocked",
    ],
}

TARGET_SCAN = {
    "tests/test_kalshi_readonly_adapter.py": [
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "PredictionMarketReadonlyAdapter",
        "PredictionMarketProviderAdapter",
    ],
    "tests/test_kalshi_readonly_readiness_contract.py": [
        "src.services.prediction_market_runtime_bridge",
        "KalshiReadonlyAdapter",
    ],
    "tests/test_calibration_collector.py": [
        "src.services.prediction_market_runtime_bridge",
        "KalshiReadonlyAdapter",
    ],
    "tests/test_scheduler_runner.py": [
        "src.services.prediction_market_runtime_bridge.KalshiReadonlyAdapter.fetch_snapshot",
        "src.services.odds_runtime_bridge.SharpSportsbookAdapter.fetch_snapshot",
    ],
    "tests/test_kalshi_market_provider.py": [
        "src.services.prediction_market_runtime_bridge",
        "src.providers.prediction_markets",
    ],
    "tests/test_screenshot_analysis.py": [
        "src.providers.prediction_markets",
        "screenshot_intake.enrich_ticket",
    ],
}

def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_docs_capture_the_test_retirement_and_remaining_delete_readiness() -> None:
    for relative, fragments in DOC_FRAGMENTS.items():
        text = _read(relative)
        for fragment in fragments:
            assert fragment in text, f"missing {fragment!r} in {relative}"


def test_target_tests_now_use_canonical_prediction_market_surfaces() -> None:
    for relative, fragments in TARGET_SCAN.items():
        text = _read(relative)
        for fragment in fragments:
            assert fragment in text, f"missing canonical fragment {fragment!r} in {relative}"

    assert "providers.kalshi_provider" not in _read("tests/test_kalshi_readonly_adapter.py")
    assert "automation_scheduler.kalshi_readonly_adapter" not in _read("tests/test_kalshi_readonly_readiness_contract.py")
    assert "automation_scheduler.kalshi_readonly_adapter" not in _read("tests/test_calibration_collector.py")
    assert "automation_scheduler.scheduler_runner.KalshiReadonlyAdapter.fetch_snapshot" not in _read("tests/test_scheduler_runner.py")
    assert "automation_scheduler.kalshi_market_provider" not in _read("tests/test_kalshi_market_provider.py")
    assert "providers.kalshi_provider.requests.get" not in _read("tests/test_screenshot_analysis.py")


def test_canonical_prediction_market_modules_import_and_remain_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbid_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", _forbid_getenv)

    bridge = importlib.reload(importlib.import_module("src.services.prediction_market_runtime_bridge"))
    connector = importlib.reload(importlib.import_module("src.connectors.prediction_market_data"))
    provider = importlib.reload(importlib.import_module("src.providers.prediction_markets"))

    assert bridge.KalshiReadonlyAdapter is bridge.PredictionMarketReadonlyAdapter
    bridge_adapter = bridge.KalshiReadonlyAdapter({})
    assert bridge_adapter.validate_config()["status"] == "provider_disabled"
    assert bridge_adapter.health_check()["status"] == "provider_disabled"
    with pytest.raises(ConnectorDisabledError):
        bridge_adapter.fetch_snapshot()

    connector_client = connector.build_prediction_market_read_only_client()
    assert connector_client.describe()["provider"] == "prediction_market_data"
    with pytest.raises(ConnectorDisabledError):
        connector_client.fetch_events()

    provider_adapter = provider.PredictionMarketProviderAdapter()
    assert provider_adapter.health_check()["status"] == "scaffold_only"
    assert provider_adapter.validate_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert provider_adapter.normalize_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "prediction_market"


def test_legacy_prediction_market_shell_names_are_historical_evidence_only() -> None:
    evidence_files = [
        "PHASE10K8ZGV_PREDICTION_MARKET_COMPATIBILITY_TEST_RETIREMENT.md",
        "PREDICTION_MARKET_COMPATIBILITY_TEST_RETIREMENT_MAP_AFTER_10K8ZGV.md",
        "PREDICTION_MARKET_COMPATIBILITY_REFERENCE_SCAN_AFTER_10K8ZGV.md",
        "PREDICTION_MARKET_DELETE_READINESS_STATUS_AFTER_10K8ZGV.md",
        "tests/test_kalshi_readonly_adapter.py",
        "tests/test_kalshi_readonly_readiness_contract.py",
        "tests/test_calibration_collector.py",
        "tests/test_scheduler_runner.py",
        "tests/test_kalshi_market_provider.py",
        "tests/test_screenshot_analysis.py",
    ]
    for relative in evidence_files:
        text = _read(relative)
        lowered = text.lower()
        assert (
            "historical" in lowered
            or "compatibility" in lowered
            or "evidence" in lowered
            or "delete-readiness" in lowered
            or "src.services.prediction_market_runtime_bridge" in text
            or "src.connectors.prediction_market_data" in text
            or "src.providers.prediction_markets" in text
        )
