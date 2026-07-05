from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "docs" / "archive" / "milestones" / "LEGACY_CLEANUP_SUMMARY.md"
RETENTION_INDEX = ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_docs_exist_and_reclassify_historical_compatibility_tests() -> None:
    summary = _read("docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md")
    retention = _read("docs/DOCUMENT_RETENTION_INDEX.md")

    for fragment in [
        "Prediction-market and odds compatibility snapshots",
        "PREDICTION_MARKET_COMPATIBILITY_REFERENCE_SCAN_AFTER_10K8ZGU.md",
        "PREDICTION_MARKET_DELETE_READINESS_RECHECK_AFTER_10K8ZGU.md",
        "Deleted In This Pass",
    ]:
        assert fragment in summary

    assert "docs/archive/milestones/legacy_cleanup_summary.md" in retention.lower()
    assert "consolidated" in retention.lower()


def test_historical_prediction_market_redirection_uses_canonical_bridge_and_keeps_legacy_shells_importable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    bridge = importlib.import_module("src.services.prediction_market_runtime_bridge")
    connector = importlib.import_module("src.connectors.prediction_market_data")
    provider = importlib.import_module("src.providers.prediction_markets")
    odds_bridge = importlib.import_module("src.services.odds_runtime_bridge")
    odds_connector = importlib.import_module("src.connectors.odds_data")
    odds_provider = importlib.import_module("src.providers.sportsbooks")

    assert bridge is not None
    assert connector is not None
    assert provider is not None
    assert odds_bridge is not None
    assert odds_connector is not None
    assert odds_provider is not None

    scheduler_runner = importlib.import_module('src.services.scheduler_runner')
    settlement_service = importlib.import_module("src.services.settlement_service")
    calibration_collector = importlib.import_module('src.analytics.calibration_collector')
    outcome_candidates = importlib.import_module('src.market_intelligence.prediction_market_outcome_candidates')
    readiness = importlib.import_module('src.providers.kalshi_readonly_readiness')

    assert scheduler_runner.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert settlement_service.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert calibration_collector.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert outcome_candidates.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"
    assert readiness.KalshiReadonlyAdapter.__module__ == "src.services.prediction_market_runtime_bridge"

    bridge_adapter = bridge.KalshiReadonlyAdapter()
    assert bridge_adapter.validate_config()["ok"] is False
    assert bridge_adapter.health_check()["live_calls_enabled"] is False
    with pytest.raises(RuntimeError) as exc_info:
        bridge_adapter.fetch_snapshot()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"
    snapshot = bridge.get_kalshi_snapshot(bridge_adapter)
    assert snapshot["ok"] is True
    assert snapshot["dry_run"] is True
    assert snapshot["provider_id"] == "kalshi_prediction_market"

    summary = _read("docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md")
    retention = _read("docs/DOCUMENT_RETENTION_INDEX.md")
    assert "PREDICTION_MARKET_COMPATIBILITY_REFERENCE_SCAN_AFTER_10K8ZGU.md" in summary
    assert "PREDICTION_MARKET_DELETE_READINESS_RECHECK_AFTER_10K8ZGU.md" in summary
    assert "docs/archive/milestones/legacy_cleanup_summary.md" in retention.lower()
