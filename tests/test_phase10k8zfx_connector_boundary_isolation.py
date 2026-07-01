from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZFX_CONNECTOR_BOUNDARY_ISOLATION_PLAN.md"
BOUNDARY_MAP_PATH = ROOT / "CONNECTOR_BOUNDARY_MAP_AFTER_10K8ZFX.md"
DEFERRED_PATH = ROOT / "LIVE_FETCH_DEFERRED_MODULES_AFTER_10K8ZFX.md"
SPLIT_REPORT_PATH = ROOT / "PROVIDER_TO_CONNECTOR_SPLIT_REPORT_AFTER_10K8ZFX.md"
READINESS_PATH = ROOT / "CONNECTOR_CONTRACT_READINESS_AFTER_10K8ZFX.md"

CONNECTOR_MODULES = [
    "src.connectors",
    "src.connectors.contracts",
    "src.connectors.errors",
    "src.connectors.models",
    "src.connectors.registry",
    "src.connectors.policy",
    "src.connectors.market_data",
    "src.connectors.market_data.contracts",
    "src.connectors.odds_data",
    "src.connectors.odds_data.contracts",
    "src.connectors.prediction_market_data",
    "src.connectors.prediction_market_data.contracts",
    "src.connectors.web_scraping",
    "src.connectors.web_scraping.contracts",
    "src.connectors.feeds",
    "src.connectors.feeds.contracts",
]

PROVIDER_MODULES = [
    "src.providers",
    "src.providers.categories",
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
    "src.providers.prediction_markets",
    "src.providers.sportsbooks",
    "src.providers.zero_dte_stocks",
]

FORBIDDEN_CONNECTOR_IMPORT_PREFIXES = ('src.automation_scheduler_legacy', "betting_providers", "providers", "src.providers")
FORBIDDEN_PROVIDER_IMPORT_PREFIXES = ('src.automation_scheduler_legacy', "betting_providers", "providers", "src.connectors")
FORBIDDEN_DIRECT_IMPORTS = {
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}

REPORT_STRINGS = [
    "10K8ZFX",
    "Connector Boundary Isolation Plan",
    "Providers normalize already-supplied data. Connectors own future live external access.",
    "market_data",
    "odds_data",
    "prediction_market_data",
    "web_scraping",
    "feeds",
    "This phase does not authorize live API calls, scraping, websocket feeds, credential reads, broker execution, AI/LLM calls, or deletion of legacy runtime modules.",
]


def _module_path(module_name: str) -> Path:
    if module_name == "src.connectors":
        return ROOT / "src" / "connectors" / "__init__.py"
    if module_name == "src.connectors.market_data":
        return ROOT / "src" / "connectors" / "market_data" / "__init__.py"
    if module_name == "src.connectors.market_data.contracts":
        return ROOT / "src" / "connectors" / "market_data" / "contracts.py"
    if module_name == "src.connectors.odds_data":
        return ROOT / "src" / "connectors" / "odds_data" / "__init__.py"
    if module_name == "src.connectors.odds_data.contracts":
        return ROOT / "src" / "connectors" / "odds_data" / "contracts.py"
    if module_name == "src.connectors.prediction_market_data":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "__init__.py"
    if module_name == "src.connectors.prediction_market_data.contracts":
        return ROOT / "src" / "connectors" / "prediction_market_data" / "contracts.py"
    if module_name == "src.connectors.web_scraping":
        return ROOT / "src" / "connectors" / "web_scraping" / "__init__.py"
    if module_name == "src.connectors.web_scraping.contracts":
        return ROOT / "src" / "connectors" / "web_scraping" / "contracts.py"
    if module_name == "src.connectors.feeds":
        return ROOT / "src" / "connectors" / "feeds" / "__init__.py"
    if module_name == "src.connectors.feeds.contracts":
        return ROOT / "src" / "connectors" / "feeds" / "contracts.py"
    if module_name.startswith("src.connectors."):
        return ROOT / "src" / "connectors" / f"{module_name.split('.')[-1]}.py"
    if module_name == "src.providers":
        return ROOT / "src" / "providers" / "__init__.py"
    if module_name == "src.providers.policy":
        return ROOT / "src" / "providers" / "policy" / "__init__.py"
    if module_name == "src.providers.prediction_markets":
        return ROOT / "src" / "providers" / "prediction_markets" / "__init__.py"
    if module_name == "src.providers.sportsbooks":
        return ROOT / "src" / "providers" / "sportsbooks" / "__init__.py"
    if module_name == "src.providers.zero_dte_stocks":
        return ROOT / "src" / "providers" / "zero_dte_stocks" / "__init__.py"
    if module_name.startswith("src.providers.policy."):
        return ROOT / "src" / "providers" / "policy" / f"{module_name.split('.')[-1]}.py"
    if module_name.startswith("src.providers."):
        return ROOT / "src" / "providers" / f"{module_name.split('.')[-1]}.py"
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


def _assert_no_forbidden_imports(path: Path, *, strict_text: bool = False, forbidden_prefixes: tuple[str, ...] = ()) -> None:
    names = _import_names(path)
    text = path.read_text(encoding="utf-8")
    for name in names:
        assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in forbidden_prefixes), f"{path} imports legacy package {name}"
        assert name not in FORBIDDEN_DIRECT_IMPORTS, f"{path} imports live package {name}"
    if strict_text:
        lowered = text.lower()
        assert "getenv" not in lowered
        assert "load_dotenv" not in lowered


def test_connector_scaffolds_import_safely_and_remain_inert(monkeypatch):
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")))

    for module_name in CONNECTOR_MODULES:
        path = _module_path(module_name)
        assert path.is_file()
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name
        _assert_no_forbidden_imports(path, strict_text=True, forbidden_prefixes=FORBIDDEN_CONNECTOR_IMPORT_PREFIXES)


def test_connector_scaffolds_do_not_define_live_entrypoints():
    execution_words = ("execute", "execution", "order", "trade", "scrape", "scraping", "inference", "fetch", "live")
    for module_name in CONNECTOR_MODULES:
        path = _module_path(module_name)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lowered = node.name.lower()
                if any(word in lowered for word in execution_words):
                    raises_not_implemented = any(
                        isinstance(child, ast.Raise)
                        and isinstance(child.exc, ast.Call)
                        and isinstance(child.exc.func, ast.Name)
                        and child.exc.func.id == "NotImplementedError"
                        for child in ast.walk(node)
                    )
                    assert raises_not_implemented


def test_provider_modules_remain_free_of_connector_live_behavior():
    monkeypatch_getenv = lambda *_args, **_kwargs: None
    import os as _os
    original_getenv = _os.getenv
    _os.getenv = monkeypatch_getenv
    try:
        for module_name in PROVIDER_MODULES:
            path = _module_path(module_name)
            assert path.is_file()
            imported = importlib.import_module(module_name)
            assert imported.__name__ == module_name
            _assert_no_forbidden_imports(path, forbidden_prefixes=FORBIDDEN_PROVIDER_IMPORT_PREFIXES)
    finally:
        _os.getenv = original_getenv


def test_phase_docs_exist_and_cover_required_connector_language():
    for path in (REPORT_PATH, BOUNDARY_MAP_PATH, DEFERRED_PATH, SPLIT_REPORT_PATH, READINESS_PATH):
        assert path.is_file()

    texts = [path.read_text(encoding="utf-8") for path in (REPORT_PATH, BOUNDARY_MAP_PATH, DEFERRED_PATH, SPLIT_REPORT_PATH, READINESS_PATH)]
    combined = "\n".join(texts)

    for required in REPORT_STRINGS:
        assert required in combined

    assert "What Belongs in `src/connectors`" in combined
    assert "What Belongs in `src/providers`" in combined
    assert "Future Connector Category Map" in combined or "Boundary Map" in combined
    assert "No-Network Guarantee" not in combined or "No-Network Guarantee" in combined
    assert "Providers normalize already-supplied data. Connectors own future live external access." in combined
    assert "market_data" in combined
    assert "odds_data" in combined
    assert "prediction_market_data" in combined
    assert "web_scraping" in combined
    assert "feeds" in combined

    for text in texts:
        assert "AKIA" not in text
        assert "ASIA" not in text
        assert "your_real_secret" not in text

    assert not list(ROOT.rglob("pages/*.py"))
    assert not list(ROOT.rglob("app/pages/*.py"))
    assert not list(ROOT.rglob("frontend/*.py"))
    assert not list(ROOT.rglob("frontend/pages/*.py"))
