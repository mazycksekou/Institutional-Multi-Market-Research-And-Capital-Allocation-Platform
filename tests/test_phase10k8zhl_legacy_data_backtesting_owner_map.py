from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_legacy_owner_map_docs_exist_and_cover_migration_scope() -> None:
    owner_map = _read(ROOT / "LEGACY_DATA_BACKTESTING_OWNER_MAP_AFTER_10K8ZHL.md")
    migration_sequence = _read(ROOT / "DATA_BACKTESTING_MIGRATION_SEQUENCE_AFTER_10K8ZHL.md")
    delete_readiness = _read(ROOT / "DATA_BACKTESTING_DELETE_READINESS_AFTER_10K8ZHL.md")

    for fragment in [
        "automation_scheduler/backtesting_engine.py",
        "automation_scheduler/backtest_dataset_builder.py",
        "automation_scheduler/backtest_schema.py",
        "automation_scheduler/backtest_leakage.py",
        "automation_scheduler/backtest_strategy_bankroll.py",
        "automation_scheduler/backtest_strategy_profiles.py",
        "automation_scheduler/historical_data_sources.py",
        "automation_scheduler/historical_odds_importers.py",
        "automation_scheduler/historical_odds_sqlite.py",
        "automation_scheduler/historical_backtest_bridge.py",
        "src.core.backtester",
        "src.services.model_backtest_service",
        "src.api.model_backtest_routes",
        "src.api.performance_routes",
        "automation_scheduler remains a decommission target",
        "No deletions occurred",
    ]:
        assert fragment in owner_map or fragment in migration_sequence or fragment in delete_readiness

    for required in ["MIGRATE_TO_SRC_DATA", "MIGRATE_TO_SRC_BACKTESTING", "MIGRATE_TO_SRC_ANALYTICS", "MIGRATE_TO_SRC_RESEARCH"]:
        assert required in owner_map


def test_legacy_owner_map_keeps_canonical_core_owner() -> None:
    owner_map = _read(ROOT / "LEGACY_DATA_BACKTESTING_OWNER_MAP_AFTER_10K8ZHL.md")
    assert "src.core.backtester" in owner_map
    assert "src.backtesting" in owner_map
    assert "src.data" in owner_map


def test_no_legacy_data_backtesting_files_were_deleted() -> None:
    for relative in [
        "automation_scheduler/backtesting_engine.py",
        "automation_scheduler/backtest_dataset_builder.py",
        "automation_scheduler/backtest_schema.py",
        "automation_scheduler/backtest_leakage.py",
        "automation_scheduler/backtest_strategy_bankroll.py",
        "automation_scheduler/backtest_strategy_profiles.py",
        "automation_scheduler/historical_data_sources.py",
        "automation_scheduler/historical_odds_importers.py",
        "automation_scheduler/historical_odds_sqlite.py",
        "automation_scheduler/historical_backtest_bridge.py",
        "src/core/backtester.py",
        "src/services/model_backtest_service.py",
        "src/api/model_backtest_routes.py",
        "src/api/performance_routes.py",
    ]:
        assert (ROOT / relative).exists(), relative
