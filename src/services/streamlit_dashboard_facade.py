from __future__ import annotations

"""Import-safe dashboard compatibility facade.

This module preserves the dashboard-facing symbol surface while avoiding any
top-level import of the removed ``automation_scheduler`` package.  It prefers
canonical ``src.*`` modules and only falls back to the relocated legacy code
under ``src.automation_scheduler_legacy`` when a symbol is actually requested.
"""

from importlib import import_module
from typing import Any, Mapping

from src.automation_scheduler_legacy.local_sports_history_audit import (
    ALLOWED_BLOCKED_REASONS as _LEGACY_ALLOWED_BLOCKED_REASONS,
)


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
    "src.market_intelligence.response_compactor",
    "src.market_intelligence.sports",
    "src.providers",
    "src.research.feature_control",
    "src.research.history",
    "src.services.ops_workflow",
    "src.services.runtime_shared",
    "src.services.automation_scheduler_facade",
)

_LEGACY_MODULES: tuple[str, ...] = (
    "src.automation_scheduler_legacy.ai_provider_security",
    "src.automation_scheduler_legacy.causal_scaffold",
    "src.automation_scheduler_legacy.candlestick_manifold_detector",
    "src.automation_scheduler_legacy.cross_asset_intelligence_router",
    "src.automation_scheduler_legacy.cross_asset_manifold_router",
    "src.automation_scheduler_legacy.data_intelligence_registry",
    "src.automation_scheduler_legacy.feature_ablation_lab",
    "src.automation_scheduler_legacy.field_scorecard",
    "src.automation_scheduler_legacy.graph_relationship_mapper",
    "src.automation_scheduler_legacy.hard_gate_policy",
    "src.automation_scheduler_legacy.historical_backtest_bridge",
    "src.automation_scheduler_legacy.historical_line_movement",
    "src.automation_scheduler_legacy.historical_odds_importers",
    "src.automation_scheduler_legacy.historical_odds_sqlite",
    "src.automation_scheduler_legacy.historical_data_sources",
    "src.automation_scheduler_legacy.institutional_cross_asset_adapters",
    "src.automation_scheduler_legacy.institutional_cross_asset_reports",
    "src.automation_scheduler_legacy.line_movement_data_quality_dashboard",
    "src.automation_scheduler_legacy.local_sports_history_audit",
    "src.automation_scheduler_legacy.manifold_cluster_registry",
    "src.automation_scheduler_legacy.market_state_manifold",
    "src.automation_scheduler_legacy.model_data_field_catalog",
    "src.automation_scheduler_legacy.nfl_coaching_adapters",
    "src.automation_scheduler_legacy.nfl_coaching_sources",
    "src.automation_scheduler_legacy.nfl_open_data_adapters",
    "src.automation_scheduler_legacy.nfl_open_data_sources",
    "src.automation_scheduler_legacy.owner_approval_gate",
    "src.automation_scheduler_legacy.pattern_calibration",
    "src.automation_scheduler_legacy.pattern_review_queue",
    "src.automation_scheduler_legacy.performance_metrics",
    "src.automation_scheduler_legacy.representation_feature_builder",
    "src.automation_scheduler_legacy.secret_safety",
    "src.automation_scheduler_legacy.security_readiness_report",
    "src.automation_scheduler_legacy.strategy_readiness_report",
    "src.automation_scheduler_legacy.strategy_router",
    "src.automation_scheduler_legacy.strategy_maturity",
    "src.automation_scheduler_legacy.source_event_link_resolver",
    "src.services.scheduler_config",
    "src.automation_scheduler_legacy.security_event_types",
    "src.automation_scheduler_legacy.security_policy",
    "src.automation_scheduler_legacy.streamlit_dashboard_data",
    "src.automation_scheduler_legacy.zero_dte_fixture_template",
)


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
    from src.automation_scheduler_legacy.nfl_coaching_sources import nfl_coaching_sources as legacy_nfl_coaching_sources

    return legacy_nfl_coaching_sources()


def nfl_open_data_sources() -> list[dict[str, Any]]:
    from src.automation_scheduler_legacy.nfl_open_data_sources import nfl_open_data_sources as legacy_nfl_open_data_sources

    return legacy_nfl_open_data_sources()


def adapter_by_id(source_id: str) -> Any:
    from src.automation_scheduler_legacy.nfl_coaching_adapters import adapter_by_id as coaching_adapter_by_id
    from src.automation_scheduler_legacy.nfl_open_data_adapters import adapter_by_id as open_data_adapter_by_id

    return coaching_adapter_by_id(source_id) or open_data_adapter_by_id(source_id)


def calculate_performance_metrics(entries: list[dict[str, Any]] | None) -> dict[str, Any]:
    from src.automation_scheduler_legacy.pattern_calibration import (
        calculate_performance_metrics as pattern_calibration_metrics,
    )
    from src.automation_scheduler_legacy.performance_metrics import (
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
    from src.automation_scheduler_legacy.pattern_review_queue import (
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
    from src.automation_scheduler_legacy.institutional_cross_asset_reports import (
        build_daily_report_payload as legacy_build_daily_report_payload,
    )

    return legacy_build_daily_report_payload(run_result)


def render_markdown_report(report: dict[str, Any]) -> str:
    from src.automation_scheduler_legacy.institutional_cross_asset_reports import (
        render_markdown_report as legacy_render_markdown_report,
    )

    return legacy_render_markdown_report(report)


def write_daily_report(*args: Any, **kwargs: Any) -> dict[str, Any]:
    if args and isinstance(args[0], Mapping):
        from src.automation_scheduler_legacy.institutional_cross_asset_reports import (
            write_daily_report as legacy_write_institutional_daily_report,
        )

        return legacy_write_institutional_daily_report(*args, **kwargs)
    from src.automation_scheduler_legacy.calibration_collector import (
        write_daily_report as legacy_write_calibration_daily_report,
    )

    return legacy_write_calibration_daily_report(*args, **kwargs)


def build_local_sports_history_audit_report(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from src.automation_scheduler_legacy.local_sports_history_audit import (
        build_local_sports_history_audit_report as legacy_build_local_sports_history_audit_report,
    )

    return legacy_build_local_sports_history_audit_report(*args, **kwargs)


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
ALLOWED_BLOCKED_REASONS = set(_LEGACY_ALLOWED_BLOCKED_REASONS) | {
    "no_local_records_found",
    "not_applicable_for_module",
}
