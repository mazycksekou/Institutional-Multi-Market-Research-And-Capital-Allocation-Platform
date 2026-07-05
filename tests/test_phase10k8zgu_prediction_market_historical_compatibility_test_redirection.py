from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "docs" / "archive" / "milestones" / "LEGACY_CLEANUP_SUMMARY.md"

DOCS = {
    "docs/archive/historical_reports/PHASE10K8ZGU_PREDICTION_MARKET_HISTORICAL_COMPATIBILITY_TEST_REDIRECTION.md": [
        "Historical compatibility tests must not preserve legacy prediction-market shells unnecessarily.",
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "historical evidence only",
        "reclassified as compatibility evidence",
    ],
    "docs/archive/historical_reports/PREDICTION_MARKET_HISTORICAL_TEST_REDIRECTION_MAP_AFTER_10K8ZGU.md": [
        "tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py",
        "tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py",
        "tests/test_kalshi_readonly_adapter.py",
        "historical evidence only",
        "compatibility evidence",
    ],
    "docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md": [
        "PREDICTION_MARKET_COMPATIBILITY_REFERENCE_SCAN_AFTER_10K8ZGU.md",
        "PREDICTION_MARKET_DELETE_READINESS_RECHECK_AFTER_10K8ZGU.md",
        "Deleted In This Pass",
    ],
}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_docs_exist_and_reclassify_historical_compatibility_tests() -> None:
    for relative, fragments in DOCS.items():
        text = _read(relative)
        for fragment in fragments:
            assert fragment in text, f"missing {fragment!r} in {relative}"


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

    for relative in [
        "docs/archive/historical_reports/PHASE10K8ZGU_PREDICTION_MARKET_HISTORICAL_COMPATIBILITY_TEST_REDIRECTION.md",
        "docs/archive/historical_reports/PREDICTION_MARKET_HISTORICAL_TEST_REDIRECTION_MAP_AFTER_10K8ZGU.md",
        "docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md",
    ]:
        text = _read(relative)
        lowered = text.lower()
        assert (
            "historical" in lowered
            or "compatibility" in lowered
            or "evidence" in lowered
            or "delete-readiness" in lowered
            or "src.services.prediction_market_runtime_bridge" in text
        )
