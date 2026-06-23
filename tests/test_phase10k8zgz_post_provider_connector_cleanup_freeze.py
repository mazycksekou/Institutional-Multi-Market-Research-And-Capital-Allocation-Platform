from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

FREEZE_DOCS = [
    ROOT / "PHASE10K8ZGZ_POST_PROVIDER_CONNECTOR_CLEANUP_FREEZE.md",
    ROOT / "POST_PROVIDER_CONNECTOR_ARCHITECTURE_MAP_AFTER_10K8ZGZ.md",
    ROOT / "POST_DELETION_IMPORT_HEALTH_AFTER_10K8ZGZ.md",
    ROOT / "REMAINING_LEGACY_RUNTIME_OWNER_QUEUE_AFTER_10K8ZGZ.md",
    ROOT / "NEXT_CORE_ENGINE_EXTRACTION_PLAN_AFTER_10K8ZGZ.md",
]

DELETED_ODDS_MODULES = [
    "sharp_client",
    "providers.sharp_provider",
    "betting_providers.sharp_api",
    "betting_providers.the_odds_api",
    "betting_providers.sportsgameodds",
    "automation_scheduler.sharp_sportsbook_adapter",
    "automation_scheduler.sportsbook_odds_provider",
]

DELETED_PM_MODULES = [
    "kalshi_client",
    "providers.kalshi_provider",
    "betting_providers.kalshi_api",
    "automation_scheduler.kalshi_readonly_adapter",
    "automation_scheduler.kalshi_market_provider",
]

CANONICAL_ODDS_MODULES = [
    "src.services.odds_runtime_bridge",
    "src.connectors.odds_data",
    "src.providers.sportsbooks",
]

CANONICAL_PM_MODULES = [
    "src.services.prediction_market_runtime_bridge",
    "src.connectors.prediction_market_data",
    "src.providers.prediction_markets",
]

CANONICAL_MD_MODULES = [
    "src.connectors.market_data",
    "src.providers.zero_dte_stocks",
]

SAFE_FILES = [
    "main.py",
    "streamlit_app.py",
    "quant_engine.py",
    "risk_engine.py",
    "market_pricing.py",
    "model_probability.py",
    "bet_decision_engine.py",
    "screenshot_intake.py",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_freeze_docs_exist() -> None:
    for path in FREEZE_DOCS:
        assert path.exists(), path


def test_freeze_docs_contain_required_sections() -> None:
    combined = "\n".join(_read(path) for path in FREEZE_DOCS)
    required = [
        "10K8ZGZ",
        "deleted odds shell",
        "deleted prediction-market shell",
        "canonical odds",
        "canonical prediction",
        "main.py is not automatic deletion",
        "streamlit_app.py is not automatic deletion",
        "quant_engine.py is not automatic deletion",
        "risk_engine.py is not automatic deletion",
        "automation_scheduler remains a decommission target",
    ]
    for text in required:
        assert text.lower() in combined.lower(), text


def test_odds_flow_imports_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("import-time credential access is forbidden")
        ),
    )
    for mod in CANONICAL_ODDS_MODULES:
        importlib.import_module(mod)


def test_prediction_market_flow_imports_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("import-time credential access is forbidden")
        ),
    )
    for mod in CANONICAL_PM_MODULES:
        importlib.import_module(mod)


def test_market_data_flow_imports_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("import-time credential access is forbidden")
        ),
    )
    for mod in CANONICAL_MD_MODULES:
        importlib.import_module(mod)


def test_deleted_odds_modules_no_longer_import() -> None:
    for mod in DELETED_ODDS_MODULES:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)


def test_deleted_prediction_market_modules_no_longer_import() -> None:
    for mod in DELETED_PM_MODULES:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)


def test_no_runtime_file_imports_deleted_modules() -> None:
    needles = [
        "importlib.import_module(\"sharp_client\")",
        "importlib.import_module('sharp_client')",
        "importlib.import_module(\"providers.sharp_provider\")",
        "importlib.import_module('providers.sharp_provider')",
        "importlib.import_module(\"betting_providers.sharp_api\")",
        "importlib.import_module('betting_providers.sharp_api')",
        "importlib.import_module(\"betting_providers.the_odds_api\")",
        "importlib.import_module('betting_providers.the_odds_api')",
        "importlib.import_module(\"betting_providers.sportsgameodds\")",
        "importlib.import_module('betting_providers.sportsgameodds')",
        "importlib.import_module(\"automation_scheduler.sharp_sportsbook_adapter\")",
        "importlib.import_module('automation_scheduler.sharp_sportsbook_adapter')",
        "importlib.import_module(\"automation_scheduler.sportsbook_odds_provider\")",
        "importlib.import_module('automation_scheduler.sportsbook_odds_provider')",
        "import kalshi_client",
        "from kalshi_client import",
        "import providers.kalshi_provider",
        "from providers.kalshi_provider import",
        "import betting_providers.kalshi_api",
        "from betting_providers.kalshi_api import",
        "import automation_scheduler.kalshi_readonly_adapter",
        "from automation_scheduler.kalshi_readonly_adapter import",
        "import automation_scheduler.kalshi_market_provider",
        "from automation_scheduler.kalshi_market_provider import",
    ]
    for path in ROOT.rglob("*.py"):
        if path == Path(__file__).resolve() or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle in text:
                pytest.fail(f"Deleted module import found in {path}: {needle}")


def test_safe_files_not_automatic_deletion() -> None:
    combined = "\n".join(_read(path) for path in FREEZE_DOCS)
    for filename in SAFE_FILES:
        assert filename in combined, f"{filename} not mentioned in freeze docs"


def test_automation_scheduler_not_retained() -> None:
    combined = "\n".join(_read(path) for path in FREEZE_DOCS)
    assert "decommission" in combined.lower()
    assert "automation_scheduler" in combined.lower()
