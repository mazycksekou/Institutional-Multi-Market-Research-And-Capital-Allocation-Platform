from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_docs_and_maps_record_that_the_legacy_prediction_market_proof_tests_were_retired() -> None:
    combined = "\n".join(
        _read(relative)
        for relative in [
            "PHASE10K8ZGX_PREDICTION_MARKET_PROOF_TEST_RETIREMENT.md",
            "PREDICTION_MARKET_PROOF_TEST_RETIREMENT_MAP_AFTER_10K8ZGX.md",
            "PREDICTION_MARKET_FINAL_REFERENCE_SCAN_AFTER_10K8ZGX.md",
            "FINAL_PREDICTION_MARKET_DELETE_READINESS_AFTER_10K8ZGX.md",
        ]
    )
    for required in [
        "10K8ZGX",
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "historical evidence only",
        "reclassified as historical evidence only",
        "No deletion occurs in this phase",
        "final delete readiness",
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
    adapter = bridge.PredictionMarketReadonlyAdapter({})
    assert adapter.validate_config()["status"] == "provider_disabled"
    with pytest.raises(ConnectorDisabledError):
        adapter.fetch_snapshot()

    client = connector.build_prediction_market_read_only_client()
    assert client.describe()["provider"] == "prediction_market_data"
    assert connector.describe_prediction_market_connector_readiness()["status"] == "disabled"
    with pytest.raises(ConnectorDisabledError):
        client.fetch_events()

    provider_adapter = provider.PredictionMarketProviderAdapter()
    assert provider_adapter.health_check()["status"] == "scaffold_only"
    assert provider_adapter.validate_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert provider_adapter.normalize_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "prediction_market"
