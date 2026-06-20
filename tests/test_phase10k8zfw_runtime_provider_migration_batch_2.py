from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZFW_RUNTIME_PROVIDER_MIGRATION_BATCH_2.md"
ROUTER_PLAN_PATH = ROOT / "PROVIDER_ROUTER_SPLIT_PLAN_AFTER_10K8ZFW.md"
HELPER_MAP_PATH = ROOT / "PROVIDER_HELPER_MIGRATION_MAP_AFTER_10K8ZFW.md"
COMPAT_STATUS_PATH = ROOT / "PROVIDER_COMPATIBILITY_STATUS_AFTER_10K8ZFW.md"

CANONICAL_MODULES = [
    "src.providers",
    "src.providers.categories",
    "src.providers.compat",
    "src.providers.routing",
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

LEGACY_MODULES = [
    "betting_providers.base",
    "betting_providers.provider_router",
    "providers.base_provider",
    "providers.odds_provider_router",
]

FORBIDDEN_IMPORT_PREFIXES = ("automation_scheduler",)
FORBIDDEN_DIRECT_IMPORTS = {"requests", "httpx", "yfinance", "openai", "anthropic", "playwright", "selenium", "alpaca", "robinhood", "ib_insync", "ccxt"}


def _module_path(module_name: str) -> Path:
    if module_name == "src.providers":
        return ROOT / "src" / "providers" / "__init__.py"
    if module_name == "src.providers.policy":
        return ROOT / "src" / "providers" / "policy" / "__init__.py"
    if module_name.startswith("src.providers.policy."):
        return ROOT / "src" / "providers" / "policy" / f"{module_name.split('.')[-1]}.py"
    if module_name.startswith("src.providers."):
        return ROOT / "src" / "providers" / f"{module_name.split('.')[-1]}.py"
    if module_name.startswith("betting_providers."):
        return ROOT / "betting_providers" / f"{module_name.split('.')[-1]}.py"
    if module_name.startswith("providers."):
        return ROOT / "providers" / f"{module_name.split('.')[-1]}.py"
    raise ValueError(module_name)


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


def test_runtime_helper_and_router_modules_import_safely(monkeypatch):
    def fail_getenv(*_args, **_kwargs):
        raise AssertionError("import-time credential access is forbidden")

    monkeypatch.setattr(os, "getenv", fail_getenv)

    imported = {module_name: importlib.import_module(module_name) for module_name in CANONICAL_MODULES + LEGACY_MODULES}

    categories = imported["src.providers.categories"]
    routing = imported["src.providers.routing"]
    compat = imported["src.providers.compat"]

    assert categories.PROVIDER_CATEGORIES == ("prediction_markets", "sportsbooks", "zero_dte_stocks")
    assert categories.category_package_name("prediction_markets") == "src.providers.prediction_markets"
    assert categories.category_package_name("sportsbooks") == "src.providers.sportsbooks"
    assert categories.category_package_name("zero_dte_stocks") == "src.providers.zero_dte_stocks"
    assert categories.provider_category_from_provider_type("prediction_market") == "prediction_markets"
    assert categories.provider_category_from_provider_type("sportsbook_odds") == "sportsbooks"
    assert categories.provider_category_from_provider_type("stock_price") == "zero_dte_stocks"
    assert routing.resolve_provider_category(provider_type="prediction_market") == "prediction_markets"
    assert routing.resolve_provider_category(provider_type="sportsbook_odds") == "sportsbooks"
    assert routing.resolve_provider_category(provider_type="stock_price") == "zero_dte_stocks"
    assert routing.provider_route_package(provider_type="prediction_market") == "src.providers.prediction_markets"
    assert routing.provider_route_package(provider_type="sportsbook_odds") == "src.providers.sportsbooks"
    assert routing.provider_route_package(provider_type="stock_price") == "src.providers.zero_dte_stocks"
    assert routing.default_provider_id_for_category("prediction_markets") == "prediction_market_placeholder"
    assert routing.default_provider_id_for_category("sportsbooks") == "sportsbook_placeholder"
    assert routing.default_provider_id_for_category("zero_dte_stocks") == "zero_dte_stock_placeholder"
    assert routing.category_route_summary(provider_type="prediction_market")["provider_category"] == "prediction_markets"

    assert callable(compat.env_bool)
    assert callable(compat.provider_disabled)
    assert callable(compat.unavailable)
    assert callable(compat.available)

    legacy_base = imported["betting_providers.base"]
    canonical_compat = imported["src.providers.compat"]
    assert legacy_base.ProviderAdapter.__name__ == canonical_compat.ProviderAdapter.__name__ == "ProviderAdapter"
    assert legacy_base.provider_disabled("demo") == canonical_compat.provider_disabled("demo")
    assert legacy_base.provider_not_configured("demo") == canonical_compat.provider_not_configured("demo")
    assert legacy_base.method_not_implemented("demo", "boom") == canonical_compat.method_not_implemented("demo", "boom")
    assert legacy_base.unknown_provider(["a", "b"]) == canonical_compat.unknown_provider(["a", "b"])
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: None)
    assert legacy_base.env_bool("MISSING_FLAG", default=True) is True

    legacy_provider_router = imported["betting_providers.provider_router"]
    assert hasattr(legacy_provider_router, "ProviderRouter")
    assert hasattr(legacy_provider_router, "provider_category")
    assert legacy_provider_router.provider_category("kalshi") == "prediction_markets"
    assert legacy_provider_router.provider_category("sharp_api") == "sportsbooks"

    legacy_base_provider = imported["providers.base_provider"]
    assert legacy_base_provider.available("demo", []) == canonical_compat.available("demo", [])
    assert legacy_base_provider.unavailable("demo") == canonical_compat.unavailable("demo")
    assert legacy_base_provider.provider_error("demo", "boom") == canonical_compat.provider_error("demo", "boom")

    assert hasattr(imported["providers.odds_provider_router"], "enrich_ticket")


def test_canonical_router_modules_do_not_import_legacy_packages_or_network_clients():
    for module_name in [
        "src.providers",
        "src.providers.categories",
        "src.providers.compat",
        "src.providers.routing",
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
    ]:
        path = _module_path(module_name)
        names = _import_names(path)
        for name in names:
            assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES), f"{path} imports legacy package {name}"
            assert name not in FORBIDDEN_DIRECT_IMPORTS, f"{path} imports network package {name}"


def test_phase_docs_exist_and_cover_required_strings():
    for path in (REPORT_PATH, ROUTER_PLAN_PATH, HELPER_MAP_PATH, COMPAT_STATUS_PATH):
        assert path.is_file()

    report = REPORT_PATH.read_text(encoding="utf-8")
    router_plan = ROUTER_PLAN_PATH.read_text(encoding="utf-8")
    helper_map = HELPER_MAP_PATH.read_text(encoding="utf-8")
    compat_status = COMPAT_STATUS_PATH.read_text(encoding="utf-8")

    for text in (report, router_plan, helper_map, compat_status):
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    for required in [
        "PHASE10K8ZFW",
        "Runtime Provider Migration Batch 2",
        "read-only helper and adapter layers",
        "Router Split Plan",
        "Compatibility Status",
        "Next Recommended Migration Batch",
        "main.py",
        "streamlit_app.py",
        "API routes",
        "Deletion Readiness Status",
        "Runtime provider migration is still limited to read-only helper and adapter layers.",
    ]:
        assert required in report or required in router_plan or required in helper_map or required in compat_status

    assert "prediction_markets" in router_plan
    assert "sportsbooks" in router_plan
    assert "zero_dte_stocks" in router_plan
    assert "Compatibility wrappers preserved" in compat_status
    assert "Legacy routers remain" in compat_status
    assert "No broad route rewrites" in compat_status

    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
