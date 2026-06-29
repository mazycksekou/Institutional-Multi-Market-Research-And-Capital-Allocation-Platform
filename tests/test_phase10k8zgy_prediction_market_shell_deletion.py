from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
DELETED_SHELLS = [
    "kalshi_client",
    "providers.kalshi_provider",
    "betting_providers.kalshi_api",
    "automation_scheduler.kalshi_readonly_adapter",
    "automation_scheduler.kalshi_market_provider",
]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _assert_deleted_shell_absent(module_name: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)


def test_phase10k8zgy_documents_capture_the_shell_deletion() -> None:
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
        "canonical prediction-market flow remains intact",
        "deleted files",
        "import scan after deletion",
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
    with pytest.raises(RuntimeError) as exc_info:
        adapter.fetch_snapshot()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"

    client = connector.build_prediction_market_read_only_client()
    assert client.describe()["provider"] == "prediction_market_data"
    assert connector.describe_prediction_market_connector_readiness()["status"] == "disabled"
    with pytest.raises(RuntimeError) as exc_info:
        client.fetch_events()
    assert exc_info.value.__class__.__name__ == "ConnectorDisabledError"

    provider_adapter = provider.PredictionMarketProviderAdapter()
    assert provider_adapter.health_check()["status"] == "scaffold_only"
    assert provider_adapter.validate_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert provider_adapter.normalize_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "prediction_market"


def test_deleted_prediction_market_shells_no_longer_import() -> None:
    for module_name in DELETED_SHELLS:
        _assert_deleted_shell_absent(module_name)


def test_runtime_and_test_import_scans_do_not_reintroduce_deleted_shells() -> None:
    runtime_files = [path for path in ROOT.rglob("*.py") if path.parts[-2] not in {"tests", "__pycache__"}]
    import_needles = [
        'importlib.import_module("kalshi_client")',
        'importlib.import_module("providers.kalshi_provider")',
        'importlib.import_module("betting_providers.kalshi_api")',
        'importlib.import_module("src.automation_scheduler_legacy.kalshi_readonly_adapter")',
        'importlib.import_module("src.automation_scheduler_legacy.kalshi_market_provider")',
        "importlib.import_module('kalshi_client')",
        "importlib.import_module('providers.kalshi_provider')",
        "importlib.import_module('betting_providers.kalshi_api')",
        "importlib.import_module('src.automation_scheduler_legacy.kalshi_readonly_adapter')",
        "importlib.import_module('src.automation_scheduler_legacy.kalshi_market_provider')",
        'patch("providers.kalshi_provider',
        "patch('providers.kalshi_provider",
        'patch("src.automation_scheduler_legacy.kalshi_readonly_adapter',
        "patch('src.automation_scheduler_legacy.kalshi_readonly_adapter",
        'patch("src.automation_scheduler_legacy.kalshi_market_provider',
        "patch('src.automation_scheduler_legacy.kalshi_market_provider",
    ]

    active_runtime_hits: list[str] = []
    for path in runtime_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(needle in text for needle in import_needles):
            active_runtime_hits.append(path.relative_to(ROOT).as_posix())

    assert active_runtime_hits == [], active_runtime_hits

    active_test_hits: list[str] = []
    for path in (ROOT / "tests").glob("test_*.py"):
        if path == Path(__file__).resolve():
            continue
        if path.name == "test_phase10k8zmh_automation_scheduler_final_removal_attempt.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(needle in text for needle in import_needles):
            active_test_hits.append(path.relative_to(ROOT).as_posix())

    assert active_test_hits == [], active_test_hits
