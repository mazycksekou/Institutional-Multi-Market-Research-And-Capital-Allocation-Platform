from __future__ import annotations

import ast
import importlib
import os
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

LEGACY_WRAPPERS = [
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_registry",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_secret_policy",
    "automation_scheduler.provider_allowlist",
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


def test_provider_foundation_modules_import_without_env_access(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {module_name: importlib.import_module(module_name) for module_name in CANONICAL_MODULES + LEGACY_WRAPPERS}

    assert imported["src.providers"].ProviderContract is imported["src.providers.contracts"].ProviderContract
    assert imported["src.providers"].ProviderRegistry is imported["src.providers.registry"].ProviderRegistry
    assert imported["src.providers"].ProviderHealthStatus is imported["src.providers.health"].ProviderHealthStatus
    assert imported["src.providers"].ProviderAdapterBase is imported["src.providers.base"].ProviderAdapterBase
    assert imported["src.providers"].normalize_provider_payload is imported["src.providers.normalization"].normalize_provider_payload
    assert imported["automation_scheduler.provider_contracts"].build_provider_contract is imported["src.providers.contracts"].build_provider_contract
    assert callable(imported["automation_scheduler.provider_registry"].get_provider_registry)
    assert imported["automation_scheduler.provider_health"].summarize_provider_health is imported["src.providers.health"].summarize_provider_health
    assert imported["automation_scheduler.provider_adapter_base"].ProviderAdapterBase is imported["src.providers.base"].ProviderAdapterBase
    assert imported["automation_scheduler.provider_normalization_contract"].get_normalized_schema is imported["src.providers.normalization"].get_normalized_schema
    assert imported["automation_scheduler.provider_payload_validator"].validate_provider_payload is imported["src.providers.validation"].validate_provider_payload
    assert imported["automation_scheduler.provider_secret_policy"].redact_secret is imported["src.providers.policy.secret_policy"].redact_secret
    assert imported["automation_scheduler.provider_allowlist"].classify_provider is imported["src.providers.policy.allowlist"].classify_provider

    policy = imported["src.providers.policy.write_firewall"]
    assert policy.build_scaffold_write_firewall_policy().policy_status == "scaffold_only"


def test_legacy_wrappers_preserve_foundation_behavior(monkeypatch):
    for name in ("SHARP_PROVIDER_ENABLED", "SHARP_LIVE_READS_ENABLED", "KALSHI_PROVIDER_ENABLED", "KALSHI_LIVE_READS_ENABLED", "SHARP_API_KEY", "KALSHI_API_KEY", "KALSHI_API_SECRET"):
        monkeypatch.delenv(name, raising=False)

    canonical_contracts = importlib.import_module("src.providers.contracts")
    legacy_contracts = importlib.import_module("automation_scheduler.provider_contracts")
    canonical_registry = importlib.import_module("src.providers.registry")
    legacy_registry = importlib.import_module("automation_scheduler.provider_registry")
    canonical_health = importlib.import_module("src.providers.health")
    legacy_health = importlib.import_module("automation_scheduler.provider_health")
    canonical_base = importlib.import_module("src.providers.base")
    legacy_base = importlib.import_module("automation_scheduler.provider_adapter_base")
    canonical_normalization = importlib.import_module("src.providers.normalization")
    legacy_normalization = importlib.import_module("automation_scheduler.provider_normalization_contract")
    canonical_validation = importlib.import_module("src.providers.validation")
    legacy_validation = importlib.import_module("automation_scheduler.provider_payload_validator")
    canonical_secret = importlib.import_module("src.providers.policy.secret_policy")
    legacy_secret = importlib.import_module("automation_scheduler.provider_secret_policy")
    canonical_allowlist = importlib.import_module("src.providers.policy.allowlist")
    legacy_allowlist = importlib.import_module("automation_scheduler.provider_allowlist")

    canonical_defaults = canonical_contracts.get_default_provider_contracts()
    legacy_defaults = legacy_contracts.get_default_provider_contracts()
    assert "prediction_market_placeholder" in canonical_defaults
    assert "kalshi_placeholder" not in canonical_defaults
    assert "kalshi_placeholder" in legacy_defaults
    assert legacy_defaults["kalshi_placeholder"] == canonical_defaults["prediction_market_placeholder"]

    canonical_registry_snapshot = canonical_registry.get_provider_registry()
    legacy_registry_snapshot = legacy_registry.get_provider_registry()
    assert "prediction_market_placeholder" in canonical_registry_snapshot
    assert "sharp_sportsbook" not in canonical_registry_snapshot
    assert "kalshi_prediction_market" not in canonical_registry_snapshot
    assert "sharp_sportsbook" in legacy_registry_snapshot
    assert "kalshi_prediction_market" in legacy_registry_snapshot
    assert canonical_registry_snapshot["sportsbook_placeholder"]["provider_type"] == legacy_registry_snapshot["sportsbooks"]["provider_type"]
    assert legacy_health.summarize_provider_health(canonical_contracts.get_default_provider_contracts()) == canonical_health.summarize_provider_health(canonical_contracts.get_default_provider_contracts())
    assert legacy_base.ProviderAdapterBase is canonical_base.ProviderAdapterBase
    assert legacy_validation.validate_provider_payload("sportsbook_odds", {"event_id": "e1", "market": "h2h", "selection": "A", "odds": -110, "timestamp": "2026-06-20T00:00:00+00:00"}) == canonical_validation.validate_provider_payload("sportsbook_odds", {"event_id": "e1", "market": "h2h", "selection": "A", "odds": -110, "timestamp": "2026-06-20T00:00:00+00:00"})
    assert legacy_normalization.get_normalized_schema("sportsbook_odds") == canonical_normalization.get_normalized_schema("sportsbook_odds")
    assert legacy_allowlist.classify_provider("draftkings_sportsbook") == canonical_allowlist.classify_provider("draftkings_sportsbook")
    assert legacy_allowlist.provider_allowlist_response("internal_math") == canonical_allowlist.provider_allowlist_response("internal_math")
    assert legacy_secret.redact_secret("abc") == canonical_secret.redact_secret("abc")
    assert legacy_secret.list_required_secret_names("sharp_sportsbook") == canonical_secret.list_required_secret_names("sharp_sportsbook")

    contract = canonical_defaults["sportsbook_placeholder"]
    adapter = canonical_base.ProviderAdapterBase(contract)
    assert adapter.get_capabilities() == legacy_base.ProviderAdapterBase(contract).get_capabilities()
    assert adapter.validate_config() == legacy_base.ProviderAdapterBase(contract).validate_config()
    assert adapter.health_check() == legacy_base.ProviderAdapterBase(contract).health_check()
    assert adapter.fetch_snapshot() == legacy_base.ProviderAdapterBase(contract).fetch_snapshot()
    payload = {"event_id": "evt1", "sport": "basketball", "league": "NBA", "event_name": "A vs B", "book": "demo", "market": "h2h", "selection": "A", "line": None, "odds": -110, "timestamp": "2026-06-20T00:00:00+00:00"}
    assert adapter.normalize_payload(payload) == legacy_base.ProviderAdapterBase(contract).normalize_payload(payload)
    assert adapter.validate_payload(payload) == legacy_base.ProviderAdapterBase(contract).validate_payload(payload)

    normalized = canonical_normalization.normalize_provider_payload("sportsbook_odds", payload)
    assert normalized == legacy_normalization.normalize_provider_payload("sportsbook_odds", payload)
    assert normalized["provider_type"] == "sportsbook_odds"

    redacted = canonical_secret.redact_mapping({"api_key": "secret_value", "nested": {"token": "abc"}})
    assert redacted == legacy_secret.redact_mapping({"api_key": "secret_value", "nested": {"token": "abc"}})


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
