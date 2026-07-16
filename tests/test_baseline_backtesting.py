from __future__ import annotations

import importlib
from pathlib import Path

from src.backtesting import (
    build_baseline_backtest_dashboard_snapshot,
    run_baseline_backtest,
)
from src.backtesting.decision_row_population import build_decision_row_population
from src.data.historical_research_database import build_historical_dataset_population
from src.data.nfl_injuries_research_asset_population import build_nfl_injuries_research_asset_population
from src.data.nfl_odds_research_asset_population import build_nfl_odds_research_asset_population
from src.data.nfl_p0_foundation import build_nfl_p0_dashboard_snapshot
from src.data.nfl_results_research_asset_population import build_nfl_results_research_asset_population
from src.data.nfl_schedule_research_asset_population import build_nfl_schedule_research_asset_population
from src.data.nfl_team_statistics_research_asset_population import build_nfl_team_statistics_research_asset_population
from src.data.nfl_weather_research_asset_population import build_nfl_weather_research_asset_population
from src.data.feature_registry import build_feature_snapshot_population
from src.data.math_engine_population import build_math_engine_population
from src.market_intelligence.signal_population import build_signal_population
from src.services.streamlit_dashboard_data import (
    get_baseline_backtest_snapshot_for_dashboard as get_baseline_backtest_snapshot_for_dashboard_service,
)


def _build_phase54_sources(storage_path: Path) -> None:
    for builder in (
        build_nfl_schedule_research_asset_population,
        build_nfl_results_research_asset_population,
        build_nfl_odds_research_asset_population,
        build_nfl_weather_research_asset_population,
        build_nfl_injuries_research_asset_population,
        build_nfl_team_statistics_research_asset_population,
    ):
        assert builder(storage_path=storage_path, game_count=1)["ok"] is True

    assert build_historical_dataset_population(storage_path=storage_path)["ok"] is True
    assert build_feature_snapshot_population(storage_path=storage_path)["ok"] is True
    assert build_math_engine_population(storage_path=storage_path)["ok"] is True
    assert build_signal_population(storage_path=storage_path)["ok"] is True
    assert build_decision_row_population(storage_path=storage_path)["ok"] is True


def test_baseline_backtest_materializes_deterministic_historical_replay_and_reuses_state(
    tmp_path: Path,
) -> None:
    storage_path = tmp_path / "baseline_backtest.sqlite"
    _build_phase54_sources(storage_path)

    first = run_baseline_backtest(storage_path=storage_path)
    second = run_baseline_backtest(storage_path=storage_path)
    dashboard = build_baseline_backtest_dashboard_snapshot(
        storage_path=storage_path,
        decision_batch_id=first["decision_batch_id"],
    )
    service_dashboard = get_baseline_backtest_snapshot_for_dashboard_service(
        storage_path,
        decision_batch_id=first["decision_batch_id"],
    )
    p0_dashboard = build_nfl_p0_dashboard_snapshot(storage_path=storage_path)

    assert first["ok"] is True
    assert first["status"] == "completed"
    assert first["readiness"] == "backtest_ready"
    assert first["sample_size"] == 3
    assert first["wins"] == 2
    assert first["losses"] == 1
    assert first["pushes"] == 0
    assert first["roi_percent"] == 20.0
    assert first["point_in_time_ok"] is True
    assert len(first["backtest_rows"]) == 3
    assert first["validation"]["ok"] is True
    assert "low_sample_size" in first["validation"]["warnings"]
    assert first["backtest_report"]["sample_size"] == 3
    assert first["backtest_report"]["eligible_decisions"] == 3
    assert first["backtest_report"]["rejected_decisions"] == 0
    assert set(first["backtest_report"]["performance_by_market"]) == {
        "moneyline",
        "spread",
        "total",
    }
    assert first["benchmark_comparison"]["no_trade"]["roi_percent"] == 0.0
    assert first["benchmark_comparison"]["market_implied"]["sample_size"] == 3

    artifact_refs = first["artifact_references"]
    assert Path(artifact_refs["report_json_path"]).exists()
    assert Path(artifact_refs["report_markdown_path"]).exists()
    assert Path(artifact_refs["dashboard_json_path"]).exists()

    assert second["ok"] is True
    assert second["backtest_run_id"] == first["backtest_run_id"]
    assert second["idempotent_reuse"] is True
    assert [row["backtest_row_id"] for row in second["backtest_rows"]] == [
        row["backtest_row_id"] for row in first["backtest_rows"]
    ]

    assert dashboard["ok"] is True
    assert dashboard["backtest_run_id"] == first["backtest_run_id"]
    assert dashboard["sample_size"] == 3
    assert service_dashboard["ok"] is True
    assert service_dashboard["backtest_run_id"] == first["backtest_run_id"]

    assert p0_dashboard["baseline_backtest_layer_readiness"]["status"] == "completed"
    assert p0_dashboard["baseline_backtest_layer_readiness"]["readiness"] == "backtest_ready"
    assert p0_dashboard["baseline_backtest_layer_readiness"]["sample_size"] == 3
    assert p0_dashboard["readiness_summary"]["baseline_backtest_status"] == "completed"


def test_baseline_backtest_requires_certified_decision_rows(tmp_path: Path) -> None:
    result = run_baseline_backtest(storage_path=tmp_path / "baseline_backtest_missing.sqlite")

    assert result["ok"] is False
    assert result["status"] == "missing_certified_decision_rows"
    assert result["readiness"] == "blocked"
    assert result["unresolved_blockers"]


def test_baseline_backtest_package_exports_are_available() -> None:
    module = importlib.import_module("src.backtesting")
    assert callable(module.run_baseline_backtest)
    assert callable(module.build_baseline_backtest_dashboard_snapshot)
    assert callable(module.get_baseline_backtest_snapshot_for_dashboard)
