from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_ROOT = ROOT / "src" / "providers"
REPORT_PATH = ROOT / "PHASE10K8ZFU_PROVIDER_FOUNDATION_COMPLETION.md"
GEN_MAP_PATH = ROOT / "PROVIDER_CONTRACT_GENERALIZATION_MAP_AFTER_10K8ZFU.md"
WRAPPER_STATUS_PATH = ROOT / "PROVIDER_LEGACY_WRAPPER_STATUS_AFTER_10K8ZFU.md"
RUNTIME_READINESS_PATH = ROOT / "PROVIDER_RUNTIME_MIGRATION_READINESS_AFTER_10K8ZFU.md"

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
    "src.providers.prediction_markets",
    "src.providers.prediction_markets.contracts",
    "src.providers.sportsbooks",
    "src.providers.sportsbooks.contracts",
    "src.providers.zero_dte_stocks",
    "src.providers.zero_dte_stocks.contracts",
    "src.providers.registry",
    "src.providers.validation",
]

LEGACY_MODULES = [
    "automation_scheduler.provider_allowlist",
    "automation_scheduler.provider_secret_policy",
    "automation_scheduler.kalshi_adapter_contract",
    "automation_scheduler.sportsbook_adapter_contract",
    "automation_scheduler.provider_contracts",
    "automation_scheduler.provider_registry",
    "automation_scheduler.provider_health",
    "automation_scheduler.provider_adapter_base",
    "automation_scheduler.provider_normalization_contract",
    "automation_scheduler.provider_payload_validator",
    "automation_scheduler.provider_write_firewall",
    "betting_providers.base",
    "betting_providers.normalization",
    "providers.base_provider",
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


def _module_file(module_name: str) -> Path:
    parts = module_name.split(".")
    if module_name == "src.providers":
        return PROVIDER_ROOT / "__init__.py"
    if module_name == "src.providers.policy":
        return PROVIDER_ROOT / "policy" / "__init__.py"
    if module_name.startswith("src.providers.policy."):
        return PROVIDER_ROOT / "policy" / f"{parts[-1]}.py"
    if module_name == "src.providers.prediction_markets":
        return PROVIDER_ROOT / "prediction_markets" / "__init__.py"
    if module_name == "src.providers.prediction_markets.contracts":
        return PROVIDER_ROOT / "prediction_markets" / "contracts.py"
    if module_name == "src.providers.sportsbooks":
        return PROVIDER_ROOT / "sportsbooks" / "__init__.py"
    if module_name == "src.providers.sportsbooks.contracts":
        return PROVIDER_ROOT / "sportsbooks" / "contracts.py"
    if module_name == "src.providers.zero_dte_stocks":
        return PROVIDER_ROOT / "zero_dte_stocks" / "__init__.py"
    if module_name == "src.providers.zero_dte_stocks.contracts":
        return PROVIDER_ROOT / "zero_dte_stocks" / "contracts.py"
    return PROVIDER_ROOT / f"{parts[-1]}.py"


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


def _canonical_provider_text() -> str:
    texts: list[str] = []
    for path in PROVIDER_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        texts.append(path.read_text(encoding="utf-8"))
    return "\n".join(texts)


def test_provider_foundation_completion_imports_and_contract_generalization(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {module_name: importlib.import_module(module_name) for module_name in CANONICAL_MODULES + LEGACY_MODULES}

    assert imported["src.providers"].ProviderAdapterContract is imported["src.providers.contracts"].ProviderAdapterContract
    assert imported["src.providers"].ReadOnlyProviderContract is imported["src.providers.contracts"].ReadOnlyProviderContract
    assert imported["src.providers"].ProviderPayloadValidator is imported["src.providers.validation"].ProviderPayloadValidator
    assert imported["src.providers"].ProviderWritePolicy is imported["src.providers.policy.write_firewall"].ProviderWritePolicy
    assert imported["src.providers"].PredictionMarketProviderContract is imported["src.providers.contracts"].ProviderContract
    assert imported["src.providers"].SportsbookProviderContract is imported["src.providers.contracts"].ProviderContract
    assert imported["src.providers"].ZeroDteStockProviderContract is imported["src.providers.contracts"].ProviderContract

    prediction = imported["src.providers.prediction_markets.contracts"]
    sportsbook = imported["src.providers.sportsbooks.contracts"]
    stocks = imported["src.providers.zero_dte_stocks.contracts"]
    assert prediction.PredictionMarketProviderContract is imported["src.providers.contracts"].ProviderContract
    assert sportsbook.SportsbookProviderContract is imported["src.providers.contracts"].ProviderContract
    assert stocks.ZeroDteStockProviderContract is imported["src.providers.contracts"].ProviderContract

    legacy_kalshi = imported["automation_scheduler.kalshi_adapter_contract"]
    legacy_sportsbook = imported["automation_scheduler.sportsbook_adapter_contract"]
    legacy_allowlist = imported["automation_scheduler.provider_allowlist"]
    legacy_secret = imported["automation_scheduler.provider_secret_policy"]
    legacy_write_firewall = imported["automation_scheduler.provider_write_firewall"]
    legacy_base = imported["betting_providers.base"]
    legacy_normalization = imported["betting_providers.normalization"]
    legacy_base_provider = imported["providers.base_provider"]

    assert legacy_kalshi.validate_payload(legacy_kalshi.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert legacy_kalshi.normalize_payload(legacy_kalshi.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "prediction_market"
    assert legacy_sportsbook.validate_payload(legacy_sportsbook.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert legacy_sportsbook.normalize_payload(legacy_sportsbook.SAMPLE_DRY_RUN_PAYLOAD)["provider_type"] == "sportsbook_odds"
    assert legacy_allowlist.classify_provider("kalshi_prediction_market") == "kalshi_order"
    assert legacy_allowlist.classify_provider("sharp_sportsbook") == "sportsbook"
    assert legacy_secret.list_required_secret_names("sharp_sportsbook") == ["SHARP_API_KEY"]
    assert legacy_secret.list_required_secret_names("kalshi_prediction_market") == ["KALSHI_API_KEY", "KALSHI_API_SECRET"]
    assert hasattr(legacy_write_firewall, "check_provider_write_attempt")
    assert legacy_base.PREDICTION_MARKET == "prediction_market"
    assert hasattr(legacy_normalization, "normalize_kalshi_event")
    assert hasattr(legacy_normalization, "normalize_sportsbook_odds")
    assert hasattr(legacy_base_provider, "available")

    scaffold_policy = imported["src.providers.policy.write_firewall"].build_scaffold_provider_write_policy()
    assert scaffold_policy.policy_status == "scaffold_only"

    validator = imported["src.providers.validation"].ProviderPayloadValidator
    assert validator.validate("sportsbook_odds", legacy_sportsbook.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True
    assert validator.validate("prediction_market", legacy_kalshi.SAMPLE_DRY_RUN_PAYLOAD)["ok"] is True


def test_canonical_provider_root_has_no_vendor_strings():
    assert PROVIDER_ROOT.is_dir()
    assert not (PROVIDER_ROOT / "kalshi").exists()
    assert not (PROVIDER_ROOT / "sharp").exists()

    for path in PROVIDER_ROOT.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        lowered_parts = {part.lower() for part in path.parts}
        assert "kalshi" not in lowered_parts
        assert "sharp" not in lowered_parts
        if path.is_file() and path.suffix == ".py":
            text = path.read_text(encoding="utf-8")
            assert "kalshi" not in text.lower()
            assert "sharp" not in text.lower()


def test_canonical_modules_are_import_safe_and_do_not_pull_legacy_or_network_dependencies():
    for module_name in CANONICAL_MODULES:
        path = _module_file(module_name)
        names = _import_names(path)
        for name in names:
            assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES), f"{path} imports legacy package {name}"
            assert name not in FORBIDDEN_DIRECT_IMPORTS, f"{path} imports network package {name}"


def test_phase_documents_exist_and_cover_required_strings():
    for path in (REPORT_PATH, GEN_MAP_PATH, WRAPPER_STATUS_PATH, RUNTIME_READINESS_PATH):
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "Provider Foundation Completion" in report
    assert "Files Transported" in report
    assert "Files Generalized" in report
    assert "Files Deferred" in report
    assert "Compatibility Strategy" in report
    assert "Rollback Strategy" in report
    assert "Risks" in report
    assert "Test Results" in report
    assert "Next Recommended Phase" in report
    assert "src/providers now owns provider foundations." in report
    assert "vendor-neutral" in report
    assert "prediction_markets" in report
    assert "zero_dte_stocks" in report
    assert "sportsbooks" in report

    gen_map = GEN_MAP_PATH.read_text(encoding="utf-8")
    assert "Provider Contract Generalization" in gen_map or "Generalization Map" in gen_map
    assert "automation_scheduler/kalshi_adapter_contract.py" in gen_map
    assert "src/providers/prediction_markets/contracts.py" in gen_map
    assert "automation_scheduler/sportsbook_adapter_contract.py" in gen_map
    assert "src/providers/sportsbooks/contracts.py" in gen_map
    assert "ProviderWritePolicy" in gen_map
    assert "vendor names remain only in compatibility wrappers" in gen_map.lower()

    wrapper_status = WRAPPER_STATUS_PATH.read_text(encoding="utf-8")
    assert "Wrapper Status" in wrapper_status
    assert "Importer / Reference Count" in wrapper_status or "Importer" in wrapper_status
    assert "automation_scheduler/provider_contracts.py" in wrapper_status
    assert "automation_scheduler/provider_registry.py" in wrapper_status
    assert "automation_scheduler/provider_secret_policy.py" in wrapper_status
    assert "automation_scheduler/kalshi_adapter_contract.py" in wrapper_status
    assert "automation_scheduler/sportsbook_adapter_contract.py" in wrapper_status
    assert "Safe Deletion Phase" in wrapper_status

    readiness = RUNTIME_READINESS_PATH.read_text(encoding="utf-8")
    assert "Runtime Migration Readiness" in readiness
    assert "Provider foundation migration is complete" in readiness
    assert "runtime provider migration is still not started" in readiness.lower()
    assert "betting_providers/base.py" in readiness
    assert "betting_providers/normalization.py" in readiness
    assert "providers/base_provider.py" in readiness
    assert "first runtime batch" in readiness.lower()
