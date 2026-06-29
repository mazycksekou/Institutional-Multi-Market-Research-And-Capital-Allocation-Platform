from __future__ import annotations

"""Import-safe compatibility facade for legacy automation scheduler symbols.

The module no longer imports the removed top-level scheduler package at import
time.  It first tries to resolve requested symbols from canonical ``src.*``
modules and falls back to the relocated legacy code under
``src.automation_scheduler_legacy`` only when an attribute is actually
requested. That keeps the application import-safe while preserving behavior for
older call sites during the migration window.
"""

from importlib import import_module
import pkgutil
from functools import lru_cache
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
    "src.market_intelligence.response_compactor",
    "src.market_intelligence.sports",
    "src.providers",
    "src.providers.health",
    "src.providers.policy",
    "src.research.feature_control",
    "src.research.history",
    "src.services.runtime_shared",
)

_LEGACY_MODULES: tuple[str, ...] = (
    "src.automation_scheduler_legacy.ai_provider_security",
    "src.automation_scheduler_legacy.causal_scaffold",
    "src.automation_scheduler_legacy.candlestick_manifold_detector",
    "src.automation_scheduler_legacy.cross_asset_intelligence_router",
    "src.automation_scheduler_legacy.cross_asset_manifold_router",
    "src.automation_scheduler_legacy.data_intelligence_registry",
    "src.automation_scheduler_legacy",
    "src.automation_scheduler_legacy.data_paths",
    "src.automation_scheduler_legacy.feature_ablation_lab",
    "src.automation_scheduler_legacy.field_scorecard",
    "src.automation_scheduler_legacy.graph_relationship_mapper",
    "src.automation_scheduler_legacy.hard_gate_policy",
    "src.automation_scheduler_legacy.historical_backtest_bridge",
    "src.automation_scheduler_legacy.historical_line_movement",
    "src.automation_scheduler_legacy.historical_odds_importers",
    "src.automation_scheduler_legacy.historical_odds_sqlite",
    "src.automation_scheduler_legacy.historical_data_sources",
    "src.automation_scheduler_legacy.line_movement_data_quality_dashboard",
    "src.automation_scheduler_legacy.manifold_cluster_registry",
    "src.automation_scheduler_legacy.market_state_manifold",
    "src.automation_scheduler_legacy.model_data_field_catalog",
    "src.automation_scheduler_legacy.owner_approval_gate",
    "src.automation_scheduler_legacy.representation_feature_builder",
    "src.automation_scheduler_legacy.response_compactor",
    "src.automation_scheduler_legacy.secret_safety",
    "src.automation_scheduler_legacy.security_readiness_report",
    "src.automation_scheduler_legacy.strategy_readiness_report",
    "src.automation_scheduler_legacy.strategy_router",
    "src.automation_scheduler_legacy.strategy_maturity",
    "src.automation_scheduler_legacy.source_event_link_resolver",
    "src.automation_scheduler_legacy.scheduler_config",
    "src.automation_scheduler_legacy.security_event_types",
    "src.automation_scheduler_legacy.security_policy",
    "src.automation_scheduler_legacy.streamlit_dashboard_data",
    "src.automation_scheduler_legacy.zero_dte_fixture_template",
)


@lru_cache(maxsize=1)
def _dynamic_legacy_module_names() -> tuple[str, ...]:
    module_names: list[str] = []
    seen: set[str] = set()
    try:
        legacy_root = import_module("src.automation_scheduler_legacy")
    except Exception:
        return tuple(module_names)

    package_path = getattr(legacy_root, "__path__", None)
    if package_path is None:
        return tuple(module_names)

    for module_info in pkgutil.walk_packages(package_path, legacy_root.__name__ + "."):
        if module_info.name not in seen:
            seen.add(module_info.name)
            module_names.append(module_info.name)
    return tuple(module_names)


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
    for module_name in _dynamic_legacy_module_names():
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
