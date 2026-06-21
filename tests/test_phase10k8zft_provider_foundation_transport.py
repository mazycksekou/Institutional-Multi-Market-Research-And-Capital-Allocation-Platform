from __future__ import annotations

import ast
import importlib
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZFT_PROVIDER_FOUNDATION_TRANSPORT.md"
OWNERSHIP_PATH = ROOT / "PROVIDER_FOUNDATION_OWNERSHIP_MAP_AFTER_10K8ZFT.md"
WRAPPER_REPORT_PATH = ROOT / "PROVIDER_COMPATIBILITY_WRAPPER_REPORT_AFTER_10K8ZFT.md"

CANONICAL_MODULES = [
    "src.providers",
    "src.providers.base",
    "src.providers.contracts",
    "src.providers.errors",
    "src.providers.health",
    "src.providers.normalization",
    "src.providers.policy",
    "src.providers.policy.allowlist",
    "src.providers.policy.secret_policy",
    "src.providers.policy.write_firewall",
    "src.providers.registry",
    "src.providers.validation",
]

DELETED_WRAPPERS = [
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_secret_policy",
    "providers.base_provider",
    "betting_providers.base",
    "betting_providers.normalization",
]

LEGACY_WRAPPERS = [
    "automation_scheduler.provider_allowlist",
    "automation_scheduler.kalshi_adapter_contract",
    "automation_scheduler.sportsbook_adapter_contract",
]

DELETED_COMPAT_WRAPPER_PATHS = [
    ROOT / "automation_scheduler" / "provider_registry.py",
    ROOT / "automation_scheduler" / "provider_write_firewall.py",
]

FORBIDDEN_IMPORT_PREFIXES = (
    "automation_scheduler",
    "betting_providers",
    "providers",
)

FORBIDDEN_DIRECT_IMPORTS = {
    "requests",
    "httpx",
    "yfinance",
    "openai",
    "anthropic",
    "playwright",
    "selenium",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}


def _module_path(module_name: str) -> Path:
    parts = module_name.split(".")
    if module_name == "src.providers":
        return ROOT / "src" / "providers" / "__init__.py"
    if module_name == "src.providers.policy":
        return ROOT / "src" / "providers" / "policy" / "__init__.py"
    if module_name.startswith("src.providers.policy."):
        return ROOT / "src" / "providers" / "policy" / f"{parts[-1]}.py"
    return ROOT / "src" / "providers" / f"{parts[-1]}.py"


def _import_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _normalize_health_summary(summary: dict[str, object]) -> dict[str, object]:
    normalized = dict(summary)
    normalized["timestamp"] = "normalized"
    top_provider_statuses = []
    for status in summary["top_provider_statuses"]:  # type: ignore[index]
        entry = dict(status)
        entry["last_checked_at"] = "normalized"
        top_provider_statuses.append(entry)
    normalized["top_provider_statuses"] = top_provider_statuses
    return normalized


def test_provider_foundation_modules_import_without_env_access(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {module_name: importlib.import_module(module_name) for module_name in CANONICAL_MODULES + LEGACY_WRAPPERS}

    assert imported["src.providers"].ProviderContract.__name__ == imported["src.providers.contracts"].ProviderContract.__name__ == "ProviderContract"
    assert imported["src.providers"].ProviderRegistry.__name__ == imported["src.providers.registry"].ProviderRegistry.__name__ == "ProviderRegistry"
    assert imported["src.providers"].ProviderHealthStatus.__name__ == imported["src.providers.health"].ProviderHealthStatus.__name__ == "ProviderHealthStatus"
    assert imported["src.providers"].ProviderAdapterBase.__name__ == imported["src.providers.base"].ProviderAdapterBase.__name__ == "ProviderAdapterBase"
    assert imported["src.providers"].normalize_provider_payload("sportsbook_odds", {"event_id": "e1"})["provider_type"] == "sportsbook_odds"
    assert callable(imported["automation_scheduler.provider_allowlist"].classify_provider)
    assert callable(imported["src.providers.policy.allowlist"].classify_provider)

    assert imported["automation_scheduler.kalshi_adapter_contract"].validate_payload(
        imported["automation_scheduler.kalshi_adapter_contract"].SAMPLE_DRY_RUN_PAYLOAD
    )["ok"] is True
    assert imported["automation_scheduler.kalshi_adapter_contract"].normalize_payload(
        imported["automation_scheduler.kalshi_adapter_contract"].SAMPLE_DRY_RUN_PAYLOAD
    )["provider_type"] == "prediction_market"
    assert imported["automation_scheduler.sportsbook_adapter_contract"].validate_payload(
        imported["automation_scheduler.sportsbook_adapter_contract"].SAMPLE_DRY_RUN_PAYLOAD
    )["ok"] is True
    assert imported["automation_scheduler.sportsbook_adapter_contract"].normalize_payload(
        imported["automation_scheduler.sportsbook_adapter_contract"].SAMPLE_DRY_RUN_PAYLOAD
    )["provider_type"] == "sportsbook_odds"

    for module_name in DELETED_WRAPPERS:
        assert not (ROOT / f"{module_name.replace('.', '/')}.py").exists(), module_name

    for path in DELETED_COMPAT_WRAPPER_PATHS:
        assert not path.exists(), path

    policy = imported["src.providers.policy.write_firewall"]
    assert policy.build_scaffold_write_firewall_policy().policy_status == "scaffold_only"


def test_legacy_wrappers_preserve_foundation_behavior(monkeypatch):
    for name in ("SHARP_PROVIDER_ENABLED", "SHARP_LIVE_READS_ENABLED", "KALSHI_PROVIDER_ENABLED", "KALSHI_LIVE_READS_ENABLED", "SHARP_API_KEY", "KALSHI_API_KEY", "KALSHI_API_SECRET"):
        monkeypatch.delenv(name, raising=False)

    canonical_contracts = importlib.import_module("src.providers.contracts")
    canonical_registry = importlib.import_module("src.providers.registry")
    canonical_base = importlib.import_module("src.providers.base")
    canonical_normalization = importlib.import_module("src.providers.normalization")
    canonical_validation = importlib.import_module("src.providers.validation")
    canonical_allowlist = importlib.import_module("src.providers.policy.allowlist")
    legacy_allowlist = importlib.import_module("automation_scheduler.provider_allowlist")
    legacy_kalshi = importlib.import_module("automation_scheduler.kalshi_adapter_contract")
    legacy_sportsbook = importlib.import_module("automation_scheduler.sportsbook_adapter_contract")

    canonical_defaults = canonical_contracts.get_default_provider_contracts()
    assert "prediction_market_placeholder" in canonical_defaults

    canonical_registry_snapshot = canonical_registry.get_provider_registry()
    legacy_registry_snapshot = canonical_registry.get_provider_registry(include_legacy_aliases=True)
    assert "prediction_market_placeholder" in canonical_registry_snapshot
    assert "sharp_sportsbook" not in canonical_registry_snapshot
    assert "kalshi_prediction_market" not in canonical_registry_snapshot
    assert "sharp_sportsbook" in legacy_registry_snapshot
    assert "kalshi_prediction_market" in legacy_registry_snapshot
    assert canonical_registry_snapshot["sportsbook_placeholder"]["provider_type"] == legacy_registry_snapshot["sportsbooks"]["provider_type"]
    assert legacy_allowlist.classify_provider("draftkings_sportsbook") == canonical_allowlist.classify_provider("draftkings_sportsbook")
    assert legacy_allowlist.provider_allowlist_response("internal_math") == canonical_allowlist.provider_allowlist_response("internal_math")
    assert legacy_kalshi.validate_payload(legacy_kalshi.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert legacy_sportsbook.validate_payload(legacy_sportsbook.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True

    contract = canonical_defaults["sportsbook_placeholder"]
    adapter = canonical_base.ProviderAdapterBase(contract)
    payload = {"event_id": "evt1", "sport": "basketball", "league": "NBA", "event_name": "A vs B", "book": "demo", "market": "h2h", "selection": "A", "line": None, "odds": -110, "timestamp": datetime.now(timezone.utc).isoformat()}
    assert adapter.normalize_payload(payload)["provider_type"] == "sportsbook_odds"
    assert adapter.validate_payload(payload)["ok"] is True

    normalized = canonical_normalization.normalize_provider_payload("sportsbook_odds", payload)
    assert normalized["provider_type"] == "sportsbook_odds"

    for path in DELETED_COMPAT_WRAPPER_PATHS:
        assert not path.exists(), path


def test_canonical_foundation_files_do_not_import_legacy_or_network_modules():
    all_paths = [_module_path(name) for name in CANONICAL_MODULES]
    all_paths.extend(ROOT / "automation_scheduler" / f"{name.split('.')[-1]}.py" for name in LEGACY_WRAPPERS)

    for path in all_paths:
        names = _import_names(path)
        for name in names:
            assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES), f"{path} imports legacy package {name}"
            assert name not in FORBIDDEN_DIRECT_IMPORTS, f"{path} imports network package {name}"


def test_phase_report_and_ownership_docs_exist_and_cover_required_strings():
    for path in (REPORT_PATH, OWNERSHIP_PATH, WRAPPER_REPORT_PATH):
        assert path.is_file()

    report = REPORT_PATH.read_text(encoding="utf-8")
    ownership = OWNERSHIP_PATH.read_text(encoding="utf-8")
    wrappers = WRAPPER_REPORT_PATH.read_text(encoding="utf-8")

    for text in (report, ownership, wrappers):
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    assert "Provider Foundation Transport" in report
    assert "Compatibility Strategy" in report
    assert "Rollback Strategy" in report
    assert "Files Intentionally Deferred" in report
    assert "src.providers" in report
    assert "legacy modules remain operational through compatibility wrappers" in report.lower()

    assert "Old Owner" in ownership
    assert "New Owner" in ownership
    assert "Compatibility Wrapper Location" in ownership
    assert "Migration Status" in ownership
    assert "Deletion Eligibility" in ownership
    assert "automation_scheduler/provider_contracts.py" in ownership
    assert "src/providers/contracts.py" in ownership
    assert "deferred runtime policy gate" in ownership

    assert "Wrapper Path" in wrappers
    assert "Redirect Target" in wrappers
    assert "Importer Count / Reference Count" in wrappers
    assert "Safe Deletion Phase" in wrappers
    assert "src/providers/registry.py" in wrappers
    assert "src/providers/policy/allowlist.py" in wrappers
    assert "provider_write_firewall.py" in wrappers
