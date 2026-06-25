from __future__ import annotations

"""Import-safe compatibility facade for legacy automation scheduler symbols.

The module no longer imports the legacy scheduler package at import time.  It
first tries to resolve requested symbols from canonical ``src.*`` modules and
falls back to the legacy scheduler namespace only when an attribute is actually
requested.  That keeps the application import-safe while preserving behavior for
older call sites during the migration window.
"""

from importlib import import_module
from typing import Any

from src.services.runtime_shared import get_automation_data_dir, get_runtime_data_path


_CANONICAL_MODULES: tuple[str, ...] = (
    "src.analytics",
    "src.backtesting.dataset_builder",
    "src.backtesting.engine",
    "src.backtesting.historical_bridge",
    "src.backtesting.strategy_profiles",
    "src.brokerage.readiness_support",
    "src.data.historical_odds",
    "src.data.historical_sources",
    "src.data.line_movement",
    "src.data.source_event_links",
    "src.market_intelligence.feature_packs",
    "src.market_intelligence.impact",
    "src.market_intelligence.manifold",
    "src.market_intelligence.options",
    "src.market_intelligence.sports",
    "src.providers",
    "src.providers.health",
    "src.providers.policy",
    "src.research.feature_control",
    "src.research.history",
    "src.services.runtime_shared",
)

_LEGACY_MODULES: tuple[str, ...] = (
    "automation_scheduler",
    "automation_scheduler.data_paths",
    "automation_scheduler.response_compactor",
)


def _resolve_symbol(name: str) -> Any:
    for module_name in _CANONICAL_MODULES:
        module = import_module(module_name)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    for module_name in _LEGACY_MODULES:
        module = import_module(module_name)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str) -> Any:
    return _resolve_symbol(name)


def __dir__() -> list[str]:
    names = set(globals())
    for module_name in _CANONICAL_MODULES + _LEGACY_MODULES:
        try:
            module = import_module(module_name)
        except Exception:
            continue
        names.update(attr for attr in dir(module) if not attr.startswith("_"))
    return sorted(names)


__all__ = ["get_automation_data_dir", "get_runtime_data_path"]
