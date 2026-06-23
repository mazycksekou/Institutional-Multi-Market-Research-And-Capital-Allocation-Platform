from __future__ import annotations

import importlib
import os
import re
import subprocess
from pathlib import Path

import pytest

from src.connectors.errors import ConnectorDisabledError


ROOT = Path(__file__).resolve().parents[1]
LEGACY_SHELLS = [
    "kalshi_client",
    "providers.kalshi_provider",
    "betting_providers.kalshi_api",
    "automation_scheduler.kalshi_readonly_adapter",
    "automation_scheduler.kalshi_market_provider",
]
ACTIVE_TEST_ALLOWLIST = {
    "tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py",
}


def _tracked_python_files() -> list[Path]:
    result = subprocess.check_output(["git", "ls-files", "*.py"], cwd=ROOT, text=True)
    files = [ROOT / line for line in result.splitlines() if line.strip()]
    current = Path(__file__).resolve()
    if current not in files:
        files.append(current)
    return files


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_docs_capture_the_final_delete_readiness_and_remaining_blockers() -> None:
    combined = "\n".join(
        _read(relative)
        for relative in [
            "PHASE10K8ZGW_PREDICTION_MARKET_FINAL_DELETE_READINESS.md",
            "PREDICTION_MARKET_FINAL_IMPORT_SCAN_AFTER_10K8ZGW.md",
            "PREDICTION_MARKET_FINAL_TEST_SCAN_AFTER_10K8ZGW.md",
            "PREDICTION_MARKET_FINAL_DELETE_DECISION_AFTER_10K8ZGW.md",
        ]
    )
    for required in [
        "10K8ZGW",
        "src.services.prediction_market_runtime_bridge",
        "src.connectors.prediction_market_data",
        "src.providers.prediction_markets",
        "No deletion occurs in this phase",
        "test-blocked",
        "historical proof tests",
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
    with pytest.raises(ConnectorDisabledError):
        bridge_adapter.fetch_snapshot()

    connector_client = connector.build_prediction_market_read_only_client()
    assert connector_client.describe()["provider"] == "prediction_market_data"
    assert connector.describe_prediction_market_connector_readiness()["status"] == "disabled"
    with pytest.raises(ConnectorDisabledError):
        connector_client.fetch_events()

    provider_adapter = provider.PredictionMarketProviderAdapter()
    assert provider_adapter.health_check()["status"] == "scaffold_only"
    assert provider_adapter.validate_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert provider_adapter.normalize_payload(provider.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "prediction_market"


def test_runtime_scan_finds_no_active_import_dependency_on_legacy_shells() -> None:
    runtime_files = [path for path in _tracked_python_files() if path.relative_to(ROOT).parts[0] != "tests"]
    active_import_pattern = re.compile(
        r"^\s*(?:from|import)\s+.*(?:"
        + "|".join(re.escape(shell) for shell in LEGACY_SHELLS)
        + r")\b",
        re.MULTILINE,
    )

    active_hits: dict[str, list[str]] = {}
    for path in runtime_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if active_import_pattern.search(text):
            active_hits[path.relative_to(ROOT).as_posix()] = [
                shell for shell in LEGACY_SHELLS if re.search(rf"\b{re.escape(shell)}\b", text)
            ]

    assert active_hits == {}, active_hits

    evidence_hits = {
        "src/api/market_utility_routes.py": ["kalshi_client.py"],
        "kalshi_client.py": ["legacy_module"],
        "automation_scheduler/kalshi_readonly_adapter.py": ["legacy_module"],
    }
    for relative, fragments in evidence_hits.items():
        text = _read(relative)
        for fragment in fragments:
            assert fragment in text, f"missing evidence fragment {fragment!r} in {relative}"


def test_test_scan_shows_only_historical_proof_files_touch_legacy_shells() -> None:
    test_files = [path for path in _tracked_python_files() if path.relative_to(ROOT).parts[0] == "tests"]
    active_needles = [
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
    active_hits: set[str] = set()
    for path in test_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(needle in text for needle in active_needles):
            active_hits.add(path.relative_to(ROOT).as_posix())

    assert active_hits == ACTIVE_TEST_ALLOWLIST, active_hits


def test_legacy_prediction_market_shells_remain_importable_but_disabled() -> None:
    legacy_client = importlib.import_module("kalshi_client")
    legacy_provider = importlib.import_module("providers.kalshi_provider")
    legacy_betting = importlib.import_module("betting_providers.kalshi_api")
    legacy_adapter = importlib.import_module("automation_scheduler.kalshi_readonly_adapter")
    legacy_market_provider = importlib.import_module("automation_scheduler.kalshi_market_provider")

    assert hasattr(legacy_client, "describe_kalshi_client")
    assert hasattr(legacy_provider, "describe_kalshi_provider")
    assert hasattr(legacy_betting, "KalshiApiAdapter")
    assert hasattr(legacy_adapter, "KalshiReadonlyAdapter")
    assert hasattr(legacy_market_provider, "get_kalshi_snapshot")

    assert legacy_client.describe_kalshi_client()["live_access_enabled"] is False
    assert legacy_provider.describe_kalshi_provider()["canonical_provider"] == "prediction_market"
    assert legacy_betting.KalshiApiAdapter().enabled is False
    assert legacy_adapter.KalshiReadonlyAdapter({}).validate_config()["status"] == "provider_disabled"
    assert legacy_market_provider.get_kalshi_snapshot()["status"] == "provider_disabled"


def test_canonical_odds_flow_remains_intact() -> None:
    odds_bridge = importlib.import_module("src.services.odds_runtime_bridge")
    odds_connector = importlib.import_module("src.connectors.odds_data")
    odds_provider = importlib.import_module("src.providers.sportsbooks")

    assert hasattr(odds_bridge, "SharpSportsbookAdapter")
    assert hasattr(odds_connector, "build_odds_data_read_only_client")
    assert hasattr(odds_provider, "SportsbookProviderAdapter")
