from __future__ import annotations

"""Import-safe dashboard compatibility facade.

This module preserves the dashboard-facing symbol surface while avoiding any
top-level import of the removed scheduler bridge.  It prefers canonical
``src.*`` modules and only falls back to relocated compatibility modules when a
symbol is actually requested.
"""

from importlib import import_module
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from src.market_intelligence.local_sports_history_audit import (
    ALLOWED_BLOCKED_REASONS as _LEGACY_ALLOWED_BLOCKED_REASONS,
)

if TYPE_CHECKING:
    from src.services.odds_runtime_bridge import SharpSportsbookAdapter
    from src.services.odds_runtime_bridge import get_sportsbook_snapshot
    from src.services.odds_runtime_bridge import summarize_sportsbook_snapshot
    from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter
    from src.services.prediction_market_runtime_bridge import get_kalshi_snapshot
    from src.services.prediction_market_runtime_bridge import summarize_kalshi_snapshot
    from src.services.settlement_service import build_outcome_completion_report, write_outcome_completion_candidates
    from src.services.ledger_service import load_security_audit_records
    from src.services.ledger_service import append_security_event
    from src.services.execution_service import build_broker_quality_report
    from src.services.execution_service import SAFETY_FLAGS
    from src.services.execution_service import run_small_account_review
    from src.services.execution_service import simulate_execution
    from src.services.execution_service import rejection_response


_CANONICAL_MODULES: tuple[str, ...] = (
    "src.analytics",
    "src.analytics.calibration",
    "src.analytics.calibration_collector",
    "src.analytics.intelligence_readiness_report",
    "src.analytics.institutional_cross_asset_calibration",
    "src.analytics.institutional_cross_asset_reports",
    "src.analytics.manifold_calibration",
    "src.analytics.manifold_review_queue",
    "src.analytics.micro_outcome_calibration",
    "src.analytics.pattern_review_queue",
    "src.analytics.performance_metrics",
    "src.analytics.report_writer",
    "src.analytics.strategy_readiness_report",
    "src.analytics.review_queue",
    "src.backtesting.dataset_builder",
    "src.backtesting.engine",
    "src.backtesting.historical_bridge",
    "src.backtesting.strategy_profiles",
    "src.brokerage.paper_decision_ledger",
    "src.data.field_catalog",
    "src.data.historical_odds",
    "src.data.historical_sources",
    "src.data.line_movement",
    "src.data.odds_math",
    "src.data.outcome_migration",
    "src.data.data_availability_tiers",
    "src.data.data_source_registry",
    "src.data.data_source_research_lanes",
    "src.data.source_event_links",
    "src.market_intelligence.data_intelligence_registry",
    "src.services.collector_scheduled_runner",
    "src.services.execution_service",
    "src.services.ledger_service",
    "src.services.outcome_store",
    "src.services.settlement_service",
    "src.market_intelligence.feature_packs",
    "src.market_intelligence.impact",
    "src.market_intelligence.manifold",
    "src.market_intelligence.options",
    "src.market_intelligence.response_compactor",
    "src.market_intelligence.sports",
    "src.market_intelligence.institutional_cross_asset_lab",
    "src.market_intelligence.model_input_coverage",
    "src.providers",
    "src.providers.health",
    "src.providers.registry",
    "src.providers.ncaaf_collegefootballdata_adapter",
    "src.security.ai_provider_security",
    "src.security.hard_gate_policy",
    "src.security.owner_approval_gate",
    "src.security.policy",
    "src.security.risk_limit_guard",
    "src.security.secret_safety",
    "src.research.feature_control",
    "src.research.history",
    "src.services.ops_workflow",
    "src.services.runtime_shared",
    "src.services.system_health",
    "src.services.automation_scheduler_facade",
    "src.ai.deepseek_daily_report",
    "src.ai.deepseek_disagreement_queue",
    "src.ai.deepseek_profit_lab",
    "src.ai.deepseek_reviewer",
    "src.ai.institutional_deepseek_review",
    "src.services.scheduler_runner",
    "src.services.security_readiness",
)

_MODULE_ALIASES: dict[str, str] = {
    "append_audit_record": "src.services.audit_log",
    "read_audit_records": "src.services.audit_log",
    "ops_workflow": "src.services.ops_workflow",
    "ncaaf_collegefootballdata_adapter": "src.providers.ncaaf_collegefootballdata_adapter",
    "odds_math": "src.data.odds_math",
    "outcome_migration": "src.data.outcome_migration",
    "quality_tier": "src.market_intelligence.institutional_cross_asset_scores",
}

_LEGACY_MODULES: tuple[str, ...] = (
    "src.security.ai_provider_security",
    "src.research.causal_scaffold",
    "src.market_intelligence.candlestick_manifold_detector",
    "src.market_intelligence.cross_asset_intelligence_router",
    "src.market_intelligence.cross_asset_manifold_router",
    "src.market_intelligence.data_intelligence_registry",
    "src.research.feature_ablation_lab",
    "src.analytics.field_scorecard",
    "src.market_intelligence.graph_relationship_mapper",
    "src.security.hard_gate_policy",
    "src.data.historical_backtest_bridge",
    "src.data.historical_line_movement",
    "src.data.historical_odds_importers",
    "src.data.historical_odds_sqlite",
    "src.data.historical_data_sources",
    "src.providers.institutional_cross_asset_adapters",
    "src.analytics.institutional_cross_asset_reports",
    "src.data.line_movement_data_quality_dashboard",
    "src.market_intelligence.local_sports_history_audit",
    "src.market_intelligence.manifold_cluster_registry",
    "src.market_intelligence.market_state_manifold",
    "src.data.model_data_field_catalog",
    "src.providers.nfl_coaching_adapters",
    "src.market_intelligence.nfl_coaching_sources",
    "src.providers.nfl_open_data_adapters",
    "src.data.nfl_open_data_sources",
    "src.research.pattern_calibration",
    "src.analytics.pattern_review_queue",
    "src.analytics.performance_metrics",
    "src.research.representation_feature_builder",
    "src.services.security_readiness",
    "src.analytics.strategy_readiness_report",
    "src.core.strategy_router",
    "src.core.strategy_maturity",
    "src.data.source_event_link_resolver",
    "src.services.scheduler_config",
    "src.services.streamlit_dashboard_data",
    "src.data.zero_dte_fixture_template",
)

_DISCOVERY_PACKAGES: tuple[str, ...] = (
    "src.analytics",
    "src.backtesting",
    "src.brokerage",
    "src.core",
    "src.data",
    "src.market_intelligence",
    "src.providers",
    "src.research",
    "src.security",
    "src.services",
    "src.ai",
)


@lru_cache(maxsize=1)
def _discovered_module_names() -> tuple[str, ...]:
    root = Path(__file__).resolve().parents[2]
    discovered: list[str] = []
    for package in _DISCOVERY_PACKAGES:
        package_path = root / Path(*package.split("."))
        if not package_path.exists():
            continue
        for path in sorted(package_path.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                module = path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
            except Exception:
                continue
            if module.startswith("src.api."):
                continue
            if module == __name__:
                continue
            discovered.append(module)
    return tuple(dict.fromkeys(discovered))


@lru_cache(maxsize=1)
def _discovered_symbol_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for module_name in _CANONICAL_MODULES + _discovered_module_names() + _LEGACY_MODULES:
        if module_name == __name__:
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue
        for attr in dir(module):
            if attr.startswith("_"):
                continue
            index.setdefault(attr, module_name)
    return index


SAMPLE_DRY_RUN_PAYLOAD: dict[str, Any] = {
    "event_id": "evt_generic_1",
    "market_id": "mkt_generic_1",
    "odds": 1.5,
    "implied_probability": 0.5,
    "symbol": "GENERIC",
    "price": 100.0,
    "market_cap": 1_000_000_000,
    "report_date": "2024-01-01",
    "player_name": "Player A",
    "line": 1.5,
    "severity_score": 0.5,
    "source": "unit_test",
    "published_at": "2024-01-01T00:00:00Z",
}


def normalize_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    data = dict(SAMPLE_DRY_RUN_PAYLOAD)
    data.update(dict(payload or {}))
    return data


def validate_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    data = dict(payload or {})
    return {
        "ok": bool(data),
        "status": "validated" if data else "missing_payload",
        "missing_required_fields": [],
        "warnings": [],
    }


def nfl_coaching_sources() -> list[dict[str, Any]]:
    from src.market_intelligence.nfl_coaching_sources import nfl_coaching_sources as legacy_nfl_coaching_sources

    return legacy_nfl_coaching_sources()


def nfl_open_data_sources() -> list[dict[str, Any]]:
    from src.data.nfl_open_data_sources import nfl_open_data_sources as legacy_nfl_open_data_sources

    return legacy_nfl_open_data_sources()


def adapter_by_id(source_id: str) -> Any:
    from src.providers.nfl_coaching_adapters import adapter_by_id as coaching_adapter_by_id
    from src.providers.nfl_open_data_adapters import adapter_by_id as open_data_adapter_by_id

    return coaching_adapter_by_id(source_id) or open_data_adapter_by_id(source_id)


def calculate_performance_metrics(entries: list[dict[str, Any]] | None) -> dict[str, Any]:
    from src.research.pattern_calibration import (
        calculate_performance_metrics as pattern_calibration_metrics,
    )
    from src.analytics.performance_metrics import (
        calculate_performance_metrics as paper_performance_metrics,
    )

    rows = [dict(row) for row in entries or [] if isinstance(row, Mapping)]

    pattern_rows: list[dict[str, Any]] = []
    perf_rows: list[dict[str, Any]] = []
    for row in rows:
        pattern_row = dict(row)
        if pattern_row.get("settlement_status") is None and pattern_row.get("outcome_status") is not None:
            pattern_row["settlement_status"] = pattern_row.get("outcome_status")
        if pattern_row.get("paper_profit_loss") is None and pattern_row.get("profit_loss") is not None:
            pattern_row["paper_profit_loss"] = pattern_row.get("profit_loss")
        if pattern_row.get("paper_stake") is None:
            pattern_row["paper_stake"] = pattern_row.get("stake") or pattern_row.get("recommended_stake_percent") or 1.0
        if pattern_row.get("result_status") is None:
            pnl = pattern_row.get("paper_profit_loss")
            try:
                pnl_value = float(pnl) if pnl is not None else 0.0
            except (TypeError, ValueError):
                pnl_value = 0.0
            pattern_row["result_status"] = "win" if pnl_value > 0 else "loss" if pnl_value < 0 else "push"
        pattern_rows.append(pattern_row)

        perf_row = dict(row)
        if perf_row.get("outcome_status") is None and perf_row.get("settlement_status") is not None:
            perf_row["outcome_status"] = perf_row.get("settlement_status")
        if perf_row.get("profit_loss") is None and perf_row.get("paper_profit_loss") is not None:
            perf_row["profit_loss"] = perf_row.get("paper_profit_loss")
        if perf_row.get("profit_loss") is None and perf_row.get("follow_through_percent") is not None:
            perf_row["profit_loss"] = perf_row.get("follow_through_percent")
        perf_rows.append(perf_row)

    metrics = dict(pattern_calibration_metrics(pattern_rows))
    metrics.update(paper_performance_metrics(perf_rows))
    return metrics


def load_pattern_review_queue(*, base_data_dir: str | None = None, limit: int | None = None) -> dict[str, Any]:
    from src.analytics.pattern_review_queue import (
        load_pattern_review_queue as legacy_load_pattern_review_queue,
    )

    def scrub(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): scrub(item)
                for key, item in value.items()
                if "secret" not in str(key).lower()
                and "raw_payload" not in str(key).lower()
            }
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    return scrub(legacy_load_pattern_review_queue(base_data_dir=base_data_dir, limit=limit))


def build_daily_report_payload(run_result: dict[str, Any]) -> dict[str, Any]:
    from src.analytics.institutional_cross_asset_reports import (
        build_daily_report_payload as legacy_build_daily_report_payload,
    )

    return legacy_build_daily_report_payload(run_result)


def render_markdown_report(report: dict[str, Any]) -> str:
    from src.analytics.institutional_cross_asset_reports import (
        render_markdown_report as legacy_render_markdown_report,
    )

    return legacy_render_markdown_report(report)


def write_daily_report(*args: Any, **kwargs: Any) -> dict[str, Any]:
    if args and isinstance(args[0], Mapping):
        from src.analytics.institutional_cross_asset_reports import (
            write_daily_report as legacy_write_institutional_daily_report,
        )

        return legacy_write_institutional_daily_report(*args, **kwargs)
    from src.analytics.calibration_collector import (
        write_daily_report as legacy_write_calibration_daily_report,
    )

    return legacy_write_calibration_daily_report(*args, **kwargs)


def build_local_sports_history_audit_report(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from src.market_intelligence.local_sports_history_audit import (
        build_local_sports_history_audit_report as legacy_build_local_sports_history_audit_report,
    )

    return legacy_build_local_sports_history_audit_report(*args, **kwargs)


def _resolve_symbol(name: str) -> Any:
    module_alias = _MODULE_ALIASES.get(name)
    if module_alias is not None:
        module = import_module(module_alias)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
        globals()[name] = module
        return module
    module_name = _discovered_symbol_index().get(name)
    if module_name is not None:
        try:
            module = import_module(module_name)
        except Exception:
            pass
        else:
            if hasattr(module, name):
                value = getattr(module, name)
                globals()[name] = value
                return value
    for module_name in _CANONICAL_MODULES:
        if module_name == __name__:
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    for module_name in _discovered_module_names():
        if module_name == __name__:
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    for module_name in _LEGACY_MODULES:
        if module_name == __name__:
            continue
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            continue
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
        if module_name == __name__:
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue
        names.update(attr for attr in dir(module) if not attr.startswith("_"))
    return sorted(names)
ALLOWED_BLOCKED_REASONS = set(_LEGACY_ALLOWED_BLOCKED_REASONS) | {
    "no_local_records_found",
    "not_applicable_for_module",
}
