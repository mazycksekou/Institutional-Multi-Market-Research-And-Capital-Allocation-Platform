from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "PHASE10K8ZFR_PRODUCTION_MODULE_BOUNDARY_SCAFFOLD.md"

EXPECTED_MODULES = [
    "src.ai",
    "src.ai.llm",
    "src.ai.models",
    "src.ai.prompts",
    "src.ai.evaluation",
    "src.ai.policy",
    "src.brokerage",
    "src.brokerage.paper_trading",
    "src.brokerage.live_trading",
    "src.brokerage.execution",
    "src.brokerage.risk_controls",
    "src.brokerage.order_gateway",
    "src.connectors",
    "src.connectors.market_data",
    "src.connectors.odds_data",
    "src.connectors.prediction_market_data",
    "src.connectors.web_scraping",
    "src.connectors.feeds",
]

FORBIDDEN_IMPORT_PREFIXES = (
    'src.automation_scheduler_legacy',
    "betting_providers",
    "providers",
)

FORBIDDEN_DIRECT_IMPORTS = {
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
}

EXECUTION_WORDS = ("execute", "execution", "order", "trade", "scrape", "scraping", "inference")
CLARIFICATION_TEXT = (
    "AI/LLM, brokerage/live-trading, and scraper/live-connector functionality are future production domains, "
    "not automatic deletion categories."
)


def _module_path(module_name: str) -> Path:
    return ROOT.joinpath(*module_name.split("."), "__init__.py")


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


def _module_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_production_scaffolds_import_safely_and_stay_inert():
    for module_name in EXPECTED_MODULES:
        path = _module_path(module_name)
        assert path.is_file()

        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

        text = _module_text(path)
        lowered = text.lower()
        assert "automation_scheduler" not in text
        assert "betting_providers" not in text
        assert "providers" not in text
        assert "requests" not in lowered
        assert "httpx" not in lowered
        assert "yfinance" not in lowered
        assert "selenium" not in lowered
        assert "playwright" not in lowered
        assert "openai" not in lowered
        assert "anthropic" not in lowered
        assert "alpaca" not in lowered
        assert "robinhood" not in lowered
        assert "ib_insync" not in lowered
        assert "ccxt" not in lowered
        assert "getenv" not in lowered
        assert "load_dotenv" not in lowered

        for name in _import_names(path):
            assert not any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_IMPORT_PREFIXES)
            assert name not in FORBIDDEN_DIRECT_IMPORTS


def test_scaffold_packages_do_not_define_live_execution_entrypoints():
    for module_name in EXPECTED_MODULES:
        path = _module_path(module_name)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lowered = node.name.lower()
                if any(word in lowered for word in EXECUTION_WORDS):
                    raises_not_implemented = any(
                        isinstance(child, ast.Raise)
                        and isinstance(child.exc, ast.Call)
                        and isinstance(child.exc.func, ast.Name)
                        and child.exc.func.id == "NotImplementedError"
                        for child in ast.walk(node)
                    )
                    assert raises_not_implemented


def test_report_and_strategy_docs_include_production_boundary_clarification():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "Executive Summary" in text
    assert "Current HEAD" in text
    assert "Purpose" in text
    assert "Scope" in text
    assert "Non-Goals" in text
    assert "Boundary Model" in text
    assert "What Belongs in `src/providers`" in text
    assert "What Belongs in `src/ai`" in text
    assert "What Belongs in `src/brokerage`" in text
    assert "What Belongs in `src/connectors`" in text
    assert "No-Network Guarantee" in text
    assert "No-Execution Guarantee" in text
    assert "No-AI-Call Guarantee" in text
    assert "Future Migration Strategy" in text
    assert CLARIFICATION_TEXT in text
    assert "src/providers" in text
    assert "src/ai" in text
    assert "src/brokerage" in text
    assert "src/connectors" in text

    docs = [
        ROOT / "FULL_VENDOR_REFERENCE_INVENTORY_AFTER_10K8ZFQ.md",
        ROOT / "PROVIDER_PRODUCT_GOAL_ALIGNMENT_REPORT_AFTER_10K8ZFQ.md",
        ROOT / "VENDOR_MODULE_DELETION_CANDIDATES_AFTER_10K8ZFQ.md",
        ROOT / "PHASE10K8ZFQ_VENDOR_MODULE_AUDIT.md",
    ]
    for doc in docs:
        doc_text = doc.read_text(encoding="utf-8")
        assert CLARIFICATION_TEXT in doc_text
        assert "src/ai" in doc_text
        assert "src/brokerage" in doc_text
        assert "src/connectors" in doc_text
