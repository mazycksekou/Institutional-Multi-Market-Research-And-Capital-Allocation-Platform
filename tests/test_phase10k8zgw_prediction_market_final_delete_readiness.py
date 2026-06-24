from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_docs_capture_the_final_delete_readiness_and_remaining_blockers() -> None:
    combined = "\n".join(
        _read(relative)
        for relative in [
            "PHASE10K8ZGY_PREDICTION_MARKET_SHELL_DELETION.md",
            "PREDICTION_MARKET_SHELL_DELETION_PROOF_AFTER_10K8ZGY.md",
            "POST_PREDICTION_MARKET_SHELL_DELETION_IMPORT_SCAN_AFTER_10K8ZGY.md",
            "PREDICTION_MARKET_DELETION_COMPLETION_STATUS_AFTER_10K8ZGY.md",
        ]
    )
    for required in [
        "10K8ZGY",
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "Only the five proof-backed prediction-market legacy shells are deleted in this phase.",
        "canonical prediction-market flow",
    ]:
        assert required in combined


def test_canonical_prediction_market_stack_imports_and_stays_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("import-time credential access is forbidden")
        ),
    )

    bridge = importlib.reload(importlib.import_module("src.services.prediction_market_runtime_bridge"))
    connector = importlib.reload(importlib.import_module("src.connectors.prediction_market_data"))
    provider = importlib.reload(importlib.import_module("src.providers.prediction_markets"))

    assert bridge.KalshiReadonlyAdapter is bridge.PredictionMarketReadonlyAdapter

    bridge_adapter = bridge.PredictionMarketReadonlyAdapter({})
    assert bridge_adapter.validate_config()["status"] == "provider_disabled"
    assert bridge_adapter.health_check()["status"] == "provider_disabled"
    with pytest.raises(RuntimeError) as exc_info:
        bridge_adapter.fetch_snapshot()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"

    connector_client = connector.build_prediction_market_read_only_client()
    assert connector_client.describe()["provider"] == "prediction_market_data"
    assert connector.describe_prediction_market_connector_readiness()["status"] == "disabled"
    with pytest.raises(RuntimeError) as exc_info:
        connector_client.fetch_events()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"

    provider_adapter = provider.PredictionMarketProviderAdapter()
    assert provider_adapter.health_check()["status"] == "scaffold_only"
    assert provider_adapter.validate_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert provider_adapter.normalize_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "prediction_market"


def test_canonical_odds_flow_remains_intact() -> None:
    odds_bridge = importlib.import_module("src.services.odds_runtime_bridge")
    odds_connector = importlib.import_module("src.connectors.odds_data")
    odds_provider = importlib.import_module("src.providers.sportsbooks")

    assert hasattr(odds_bridge, "SharpSportsbookAdapter")
    assert hasattr(odds_connector, "build_odds_data_read_only_client")
    assert hasattr(odds_provider, "SportsbookProviderAdapter")


def test_deleted_prediction_market_shells_no_longer_import() -> None:
    for module_name in [
        "kalshi_client",
        "providers.kalshi_provider",
        "betting_providers.kalshi_api",
        "automation_scheduler.kalshi_readonly_adapter",
        "automation_scheduler.kalshi_market_provider",
    ]:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module_name)


def test_no_active_runtime_imports_target_deleted_prediction_market_shells() -> None:
    deleted_modules = {
        "kalshi_client",
        "providers.kalshi_provider",
        "betting_providers.kalshi_api",
        "automation_scheduler.kalshi_readonly_adapter",
        "automation_scheduler.kalshi_market_provider",
    }
    runtime_hits = []
    for path in ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(
            f"import {module_name}" in text or f"from {module_name}" in text
            for module_name in deleted_modules
        ):
            runtime_hits.append(path.relative_to(ROOT).as_posix())
    assert runtime_hits == [], runtime_hits
