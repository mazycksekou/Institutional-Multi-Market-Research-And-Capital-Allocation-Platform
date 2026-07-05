from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

REPORT_PATH = ROOT / "docs" / "reports" / "proofs" / "PHASE10K8ZGA_PROVIDER_REGISTRY_RUNTIME_BLOCKER_PROOF.md"
IMPORT_SCAN_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PROVIDER_REGISTRY_IMPORT_SCAN_AFTER_10K8ZGA.md"
MIGRATION_MAP_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PROVIDER_REGISTRY_MIGRATION_MAP_AFTER_10K8ZGA.md"
DELETE_READINESS_PATH = ROOT / "docs" / "archive" / "historical_reports" / "PROVIDER_REGISTRY_DELETE_READINESS_AFTER_10K8ZGA.md"

pytestmark = pytest.mark.smoke

RUNTIME_FILES = [
    ROOT / "src" / "providers" / "registry.py",
    ROOT / "src" / "services" / "scheduler_config.py",
    ROOT / "src" / "services" / "cadence_controller.py",
    ROOT / "src" / "providers" / "kalshi_readonly_readiness.py",
    ROOT / "src" / "services" / "streamlit_dashboard_facade.py",
]

FORBIDDEN_NETWORK_ROOTS = {
    "requests",
    "httpx",
    "yfinance",
    "openai",
    "anthropic",
    "playwright",
    "selenium",
    "websocket",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _runtime_uses_legacy_registry_import(text: str) -> bool:
    return "from .provider_registry import" in text or "import automation_scheduler.provider_registry" in text or "from automation_scheduler.provider_registry import" in text


def test_phase10k8zga_registry_docs_exist_and_cover_required_strings():
    for path in (REPORT_PATH, IMPORT_SCAN_PATH, MIGRATION_MAP_PATH, DELETE_READINESS_PATH):
        assert path.is_file(), path

    report = _read(REPORT_PATH)
    import_scan = _read(IMPORT_SCAN_PATH)
    migration_map = _read(MIGRATION_MAP_PATH)
    delete_readiness = _read(DELETE_READINESS_PATH)

    for text in (report, import_scan, migration_map, delete_readiness):
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    required_report_strings = [
        "PHASE10K8ZGA",
        "provider_registry",
        "src.providers.registry",
        "runtime blocker",
        "compatibility shim",
        "delete-ready",
        "automation_scheduler/provider_write_firewall.py",
        "No deletion occurs in this phase.",
    ]
    for required in required_report_strings:
        assert required in report

    assert "automation_scheduler/provider_registry.py" in import_scan
    assert "automation_scheduler/provider_write_firewall.py" in report
    assert "automation_scheduler/provider_write_firewall.py" in migration_map
    assert "automation_scheduler/provider_registry.py" in migration_map
    assert "delete-ready" in delete_readiness
    assert "compatibility shim" in delete_readiness


def test_phase10k8zga_runtime_dependency_redirect(monkeypatch, tmp_path):
    original_getenv = os.getenv

    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    canonical_registry = importlib.import_module("src.providers.registry")
    scheduler_config = importlib.import_module('src.services.scheduler_config')
    readiness = importlib.import_module('src.providers.kalshi_readonly_readiness')
    cadence_controller = importlib.import_module('src.services.cadence_controller')
    scheduler_pkg = importlib.import_module('src.services.streamlit_dashboard_facade')

    monkeypatch.setattr(os, "getenv", original_getenv)
    monkeypatch.setattr(canonical_registry.os, "getenv", lambda *_args, **_kwargs: None)
    for name in (
        "LEGACY_PROVIDER_REGISTRY_COMPAT",
        "SHARP_PROVIDER_ENABLED",
        "SHARP_LIVE_READS_ENABLED",
        "KALSHI_PROVIDER_ENABLED",
        "KALSHI_LIVE_READS_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)

    runtime_texts = {path.as_posix(): _read(path) for path in RUNTIME_FILES}
    for path_str, text in runtime_texts.items():
        assert not _runtime_uses_legacy_registry_import(text), path_str
        if path_str.endswith(("cadence_controller.py", "kalshi_readonly_readiness.py", "streamlit_dashboard_facade.py")):
            assert "src.providers.registry" in text, path_str

    for path in RUNTIME_FILES:
        roots = _import_roots(path)
        assert roots.isdisjoint(FORBIDDEN_NETWORK_ROOTS), (path, roots & FORBIDDEN_NETWORK_ROOTS)

    canonical_default = canonical_registry.get_provider_registry()
    canonical_legacy = canonical_registry.get_provider_registry(include_legacy_aliases=True)
    scheduler_snapshot = scheduler_pkg.get_provider_registry_snapshot(base_data_dir=str(tmp_path))
    assert not (ROOT / "automation_scheduler" / "provider_registry.py").exists()
    assert not (ROOT / "src" / "automation_scheduler_legacy").exists()

    assert "sharp_sportsbook" not in canonical_default
    assert "kalshi_prediction_market" not in canonical_default
    for key in ("sharp_sportsbook", "kalshi_prediction_market", "odds_api", "alpaca", "news_provider"):
        assert key in canonical_legacy, key

    assert scheduler_snapshot["provider_count"] == len(canonical_legacy)
    scheduler_provider_ids = {item["provider_id"] for item in scheduler_snapshot["providers"]}
    for key in ("sharp_sportsbook", "kalshi_prediction_market"):
        assert key in scheduler_provider_ids, key

    config = scheduler_config.get_default_scheduler_config(base_data_dir=str(tmp_path))
    assert config["providers"]["kalshi_prediction_market"]["provider_id"] == "kalshi_prediction_market"
    assert config["providers"]["sharp_sportsbook"]["provider_id"] == "sharp_sportsbook"

    readiness_contract = readiness.build_kalshi_readonly_contract()
    assert readiness_contract["provider_id"] == "kalshi_prediction_market"
    assert readiness_contract["provider_name"] == "Kalshi Prediction Market"

    assert callable(cadence_controller.choose_next_check_seconds)
    assert callable(scheduler_pkg.get_provider_registry_snapshot)

