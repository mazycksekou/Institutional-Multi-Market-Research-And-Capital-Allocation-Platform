from __future__ import annotations

"""Import-safe dashboard compatibility facade.

This module preserves the dashboard-facing symbol surface while avoiding any
top-level import of ``automation_scheduler``.  It prefers canonical ``src.*``
modules and only falls back to the legacy scheduler namespace when a symbol is
actually requested.
"""

from importlib import import_module
from typing import Any


_CANONICAL_MODULES: tuple[str, ...] = (
    "src.analytics",
    "src.backtesting.dataset_builder",
    "src.backtesting.engine",
    "src.backtesting.historical_bridge",
    "src.backtesting.strategy_profiles",
    "src.data.field_catalog",
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
    "src.research.feature_control",
    "src.research.history",
    "src.services.ops_workflow",
    "src.services.runtime_shared",
)

_LEGACY_MODULES: tuple[str, ...] = (
    "automation_scheduler.feature_ablation_lab",
    "automation_scheduler.historical_data_sources",
    "automation_scheduler.line_movement_data_quality_dashboard",
    "automation_scheduler.model_data_field_catalog",
    "automation_scheduler.source_event_link_resolver",
    "automation_scheduler.streamlit_dashboard_data",
    "automation_scheduler.zero_dte_fixture_template",
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
