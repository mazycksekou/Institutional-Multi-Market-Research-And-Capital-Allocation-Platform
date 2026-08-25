from __future__ import annotations

import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    ROOT / "PHASE10K8ZHI_LEGACY_FULL_GATE_REMEDIATION.md",
    ROOT / "FULL_GATE_FAILURE_INVENTORY_AFTER_10K8ZHI.md",
    ROOT / "FULL_GATE_REMEDIATION_DECISIONS_AFTER_10K8ZHI.md",
    ROOT / "DATA_BACKTESTING_FOUNDATION_AUDIT_AFTER_10K8ZHI.md",
    ROOT / "DATA_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md",
    ROOT / "BACKTESTING_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md",
    ROOT / "ANALYTICS_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md",
    ROOT / "RESEARCH_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md",
    ROOT / "DATA_BACKTESTING_MIGRATION_SEQUENCE_AFTER_10K8ZHI.md",
    ROOT / "REMAINING_LEGACY_TEST_BLOCKERS_AFTER_10K8ZHI.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_docs_capture_remediation_and_data_backtesting_foundations() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for required in [
        "PHASE 10K8ZHI",
        "Current HEAD",
        "Full Gate Failure Inventory",
        "Migration-regression failure",
        "Compatibility-wrapper and scheduler-coupling failures",
        "Compatibility-wrapper scan failures",
        "Stale test assumptions",
        "Data/Backtesting Foundation Audit",
        "src.data",
        "src.backtesting",
        "src.analytics",
        "src.research",
        "No remaining active blockers",
    ]:
        assert required in combined


def test_core_math_risk_and_backtest_layers_import_safely(monkeypatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    math_utils = importlib.import_module("src.core.math_utils")
    risk = importlib.import_module("src.core.risk")
    backtester = importlib.import_module("src.core.backtester")
    service = importlib.import_module("src.services.model_backtest_service")
    routes = importlib.import_module("src.api.model_backtest_routes")

    for name in [
        "mean",
        "median",
        "variance",
        "std_dev",
        "dot_product",
        "weighted_sum",
        "covariance",
        "correlation",
        "covariance_matrix",
        "correlation_matrix",
        "portfolio_return",
        "portfolio_variance",
    ]:
        assert hasattr(math_utils, name), name

    for name in [
        "sharpe_ratio",
        "max_drawdown",
        "portfolio_risk",
        "exposure_summary",
    ]:
        assert hasattr(risk, name), name

    assert hasattr(backtester, "run_walk_forward_backtest")
    assert hasattr(service, "run_model_backtest")
    assert hasattr(routes, "register_model_backtest_routes")


def test_data_backtesting_migration_docs_match_owning_layers() -> None:
    data_map = _read(ROOT / "DATA_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md")
    backtesting_map = _read(ROOT / "BACKTESTING_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md")
    analytics_map = _read(ROOT / "ANALYTICS_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md")
    research_map = _read(ROOT / "RESEARCH_LAYER_OWNERSHIP_MAP_AFTER_10K8ZHI.md")
    migration_sequence = _read(ROOT / "DATA_BACKTESTING_MIGRATION_SEQUENCE_AFTER_10K8ZHI.md")

    for text, required in [
        (data_map, "src.data"),
        (data_map, "automation_scheduler/historical_odds_sqlite.py"),
        (backtesting_map, "src.backtesting"),
        (backtesting_map, "automation_scheduler/backtesting_engine.py"),
        (analytics_map, "src.analytics"),
        (analytics_map, "model_governance/model_inventory.py"),
        (research_map, "src.research"),
        (research_map, "research/market_research_store.py"),
        (migration_sequence, "src.data"),
        (migration_sequence, "src.backtesting"),
        (migration_sequence, "src.analytics"),
        (migration_sequence, "src.research"),
    ]:
        assert required in text
