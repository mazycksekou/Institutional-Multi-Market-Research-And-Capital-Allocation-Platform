from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_required_docs_and_runtime_redirection_text() -> None:
    docs = {
        "PHASE10K8ZGT_PREDICTION_MARKET_RUNTIME_SCHEDULER_REDIRECTION.md": [
            "src.services.prediction_market_runtime_bridge",
            "src.connectors.prediction_market_data",
            "src.providers.prediction_markets",
            "automation_scheduler/__init__.py",
            "automation_scheduler/scheduler_runner.py",
            "kalshi_client.py",
        ],
        "PREDICTION_MARKET_RUNTIME_SCHEDULER_REDIRECTION_MAP_AFTER_10K8ZGT.md": [
            "automation_scheduler/__init__.py",
            "automation_scheduler/scheduler_runner.py",
            "automation_scheduler/kalshi_readonly_readiness.py",
            "src.services.prediction_market_runtime_bridge",
        ],
        "PREDICTION_MARKET_RUNTIME_IMPORT_SCAN_AFTER_10K8ZGT.md": [
            "automation_scheduler/__init__.py",
            "automation_scheduler/scheduler_runner.py",
            "canonical bridge",
        ],
        "PREDICTION_MARKET_RUNTIME_DELETE_READINESS_AFTER_10K8ZGT.md": [
            "kalshi_client.py",
            "providers/kalshi_provider.py",
            "betting_providers/kalshi_api.py",
            "automation_scheduler/kalshi_readonly_adapter.py",
            "automation_scheduler/kalshi_market_provider.py",
            "compatibility-blocked",
            "test-blocked",
        ],
    }

    for relative, fragments in docs.items():
        text = _read(relative)
        for fragment in fragments:
            assert fragment in text, f"missing {fragment!r} in {relative}"


def test_runtime_scheduler_files_import_the_canonical_bridge_and_not_legacy_shells() -> None:
    runtime_files = [
        "automation_scheduler/__init__.py",
        "automation_scheduler/scheduler_runner.py",
        "src/services/settlement_service.py",
        "automation_scheduler/calibration_collector.py",
        "automation_scheduler/prediction_market_outcome_candidates.py",
        "automation_scheduler/kalshi_readonly_readiness.py",
    ]
    for relative in runtime_files:
        text = _read(relative)
        assert "src.services.prediction_market_runtime_bridge" in text or "src.services.settlement_service" in text
        assert "from .kalshi_readonly_adapter import" not in text
        assert "from .kalshi_market_provider import" not in text


def test_canonical_prediction_market_bridge_connectors_and_legacy_shells_remain_importable() -> None:
    bridge = importlib.import_module("src.services.prediction_market_runtime_bridge")
    connector = importlib.import_module("src.connectors.prediction_market_data")
    provider = importlib.import_module("src.providers.prediction_markets")
    odds_bridge = importlib.import_module("src.services.odds_runtime_bridge")
    odds_connector = importlib.import_module("src.connectors.odds_data")
    odds_provider = importlib.import_module("src.providers.sportsbooks")
    automation_scheduler_pkg = importlib.import_module("automation_scheduler")
    scheduler_runner = importlib.import_module("automation_scheduler.scheduler_runner")
    settlement_service = importlib.import_module("src.services.settlement_service")
    calibration_collector = importlib.import_module("automation_scheduler.calibration_collector")
    outcome_candidates = importlib.import_module("automation_scheduler.prediction_market_outcome_candidates")
    readiness = importlib.import_module("automation_scheduler.kalshi_readonly_readiness")

    assert bridge is not None
    assert connector is not None
    assert provider is not None
    assert odds_bridge is not None
    assert odds_connector is not None
    assert odds_provider is not None
    assert automation_scheduler_pkg is not None
    assert scheduler_runner.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert settlement_service.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert calibration_collector.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert outcome_candidates.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert readiness.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"

    adapter = bridge.KalshiReadonlyAdapter()
    assert adapter.validate_config()["ok"] is False
    assert adapter.health_check()["live_calls_enabled"] is False

    with pytest.raises(RuntimeError) as exc_info:
        adapter.fetch_snapshot()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"

    snapshot = bridge.get_kalshi_snapshot(adapter)
    assert snapshot["ok"] is True
    assert snapshot["dry_run"] is True
    assert snapshot["provider_id"] == "kalshi_prediction_market"

    for relative in [
        "PHASE10K8ZGT_PREDICTION_MARKET_RUNTIME_SCHEDULER_REDIRECTION.md",
        "PREDICTION_MARKET_RUNTIME_SCHEDULER_REDIRECTION_MAP_AFTER_10K8ZGT.md",
        "PREDICTION_MARKET_RUNTIME_IMPORT_SCAN_AFTER_10K8ZGT.md",
        "PREDICTION_MARKET_RUNTIME_DELETE_READINESS_AFTER_10K8ZGT.md",
    ]:
        text = _read(relative)
        assert (
            "src.services.prediction_market_runtime_bridge" in text
            or "historical evidence only" in text
            or "compatibility evidence" in text
            or "compatibility-blocked" in text
            or "delete-readiness" in text.lower()
        )
