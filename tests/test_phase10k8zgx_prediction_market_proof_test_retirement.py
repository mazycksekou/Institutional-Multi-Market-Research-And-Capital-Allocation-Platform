from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
FINAL_PROOF_TEST = "tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py"
RETIRED_OR_RECLASSIFIED_TESTS = [
    "tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py",
    "tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py",
    "tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py",
    "tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py",
    "tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py",
    "tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py",
    "tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py",
    "tests/test_phase10k8zfy_prediction_market_connector_batch_1.py",
    "tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py",
    "tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py",
]
LEGACY_SHELL_NEEDLES = [
    'importlib.import_module("kalshi_client")',
    'importlib.import_module("providers.kalshi_provider")',
    'importlib.import_module("betting_providers.kalshi_api")',
    'importlib.import_module("automation_scheduler.kalshi_readonly_adapter")',
    'importlib.import_module("automation_scheduler.kalshi_market_provider")',
    "importlib.import_module('kalshi_client')",
    "importlib.import_module('providers.kalshi_provider')",
    "importlib.import_module('betting_providers.kalshi_api')",
    "importlib.import_module('automation_scheduler.kalshi_readonly_adapter')",
    "importlib.import_module('automation_scheduler.kalshi_market_provider')",
    'patch("providers.kalshi_provider',
    "patch('providers.kalshi_provider",
    'patch("automation_scheduler.kalshi_readonly_adapter',
    "patch('automation_scheduler.kalshi_readonly_adapter",
    'patch("automation_scheduler.kalshi_market_provider',
    "patch('automation_scheduler.kalshi_market_provider",
]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _scan_tests_for_active_legacy_shell_references() -> set[str]:
    hits: set[str] = set()
    for path in (ROOT / "tests").glob("test_*.py"):
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(needle in text for needle in LEGACY_SHELL_NEEDLES):
            hits.add(path.relative_to(ROOT).as_posix())
    return hits


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


def test_only_the_final_delete_readiness_proof_file_still_touches_legacy_shell_names() -> None:
    active_hits = _scan_tests_for_active_legacy_shell_references()
    assert active_hits == {FINAL_PROOF_TEST}, active_hits


def test_legacy_prediction_market_shell_names_are_historical_evidence_only() -> None:
    for relative in RETIRED_OR_RECLASSIFIED_TESTS:
        text = _read(relative)
        assert (
            "src.services.prediction_market_runtime_bridge" in text
            or "src.connectors.prediction_market_data" in text
            or "src.providers.prediction_markets" in text
        )
