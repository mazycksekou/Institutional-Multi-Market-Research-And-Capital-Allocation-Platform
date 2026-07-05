from __future__ import annotations

import importlib
import pkgutil
import sys
import types
from functools import lru_cache
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)


def _alias_module(old_name: str, new_name: str) -> None:
    sys.modules.setdefault(old_name, importlib.import_module(new_name))


def _alias_package(old_name: str, new_name: str) -> None:
    package = importlib.import_module(new_name)
    sys.modules.setdefault(old_name, package)

    if hasattr(package, "__path__"):
        for modinfo in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            module = importlib.import_module(modinfo.name)
            suffix = modinfo.name[len(package.__name__) + 1 :]
            sys.modules.setdefault(f"{old_name}.{suffix}", module)


_alias_module("asian_markets", "src.market_intelligence.options")
_alias_module("config", "src.core.settings")
_alias_module("logger_setup", "src.core.settings")
_alias_module("parlay_engine", "src.core.pricing")
_alias_module("bet_decision_engine", "src.services.bet_decision_engine")
_alias_module("bet_log", "src.services.bet_log")
_alias_module("market_pricing", "src.core.market_pricing")
_alias_module("model_probability", "src.core.model_probability")
_alias_module("multi_sport_model_registry", "src.market_intelligence.multi_sport_model_registry")
_alias_module("quant_engine", "src.core.quant_engine")
_alias_module("risk_engine", "src.core.risk_engine")
_alias_module("screenshot_intake", "src.services.screenshot_intake")
_alias_module("full_board_engine", "src.services.full_board_engine")
_alias_module("logbook_engine", "src.services.logbook_engine")
_alias_module("model_blender", "src.services.model_blender")
_alias_module("providers", "src.providers")
_alias_module("betting_providers", "src.providers")
_alias_module("research", "src.research")
_alias_module("research_engine", "src.research")
_alias_package("model_governance", "src.analytics.model_governance")

math_models = types.ModuleType("math_models")
math_models.__path__ = []  # type: ignore[attr-defined]
sys.modules.setdefault("math_models", math_models)
_alias_package("math_models.institutional", "src.analytics.institutional")
math_models.institutional = sys.modules["math_models.institutional"]


_ARCHIVE_HINTS = (
    'ROOT / "PHASE',
    'ROOT.glob("PHASE',
    'Path("PHASE',
    'LEGACY_ROOT = ROOT / "src" / "automation_scheduler_legacy"',
    "src/automation_scheduler_legacy",
    "automation_scheduler_legacy",
)
_ARCHIVE_ALLOWLIST = {
    "test_phase1_legacy_inventory.py",
    "test_phase3b_local_data_platform.py",
}


@lru_cache(maxsize=None)
def _read_test_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "architecture_archive: archived migration-proof tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    for item in items:
        path = Path(str(item.fspath))
        if path.name in _ARCHIVE_ALLOWLIST or not path.name.startswith("test_phase"):
            continue
        if path.name.startswith("test_phase10k"):
            item.add_marker(pytest.mark.architecture_archive)
            item.add_marker(pytest.mark.skip(reason="archived migration proof"))
            continue
        text = _read_test_source(path)
        if any(hint in text for hint in _ARCHIVE_HINTS):
            item.add_marker(pytest.mark.architecture_archive)
            item.add_marker(pytest.mark.skip(reason="archived migration proof"))
