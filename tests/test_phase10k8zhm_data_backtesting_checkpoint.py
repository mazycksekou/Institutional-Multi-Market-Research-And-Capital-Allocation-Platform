from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_checkpoint_docs_capture_status_and_next_plan() -> None:
    combined = "\n".join(
        _read(path)
        for path in [
            ROOT / "PHASE10K8ZHM_DATA_BACKTESTING_CHECKPOINT.md",
            ROOT / "POST_DATA_BACKTESTING_ARCHITECTURE_MAP_AFTER_10K8ZHM.md",
            ROOT / "REMAINING_ANALYTICS_RESEARCH_QUEUE_AFTER_10K8ZHM.md",
            ROOT / "NEXT_ANALYTICS_RESEARCH_PLAN_AFTER_10K8ZHM.md",
        ]
    )
    for fragment in [
        "data foundation status",
        "backtesting foundation status",
        "legacy mapping status",
        "no live data activation",
        "no broker execution",
        "AI/LLM deferred",
        "analytics next",
        "research next",
        "next recommended path",
    ]:
        assert fragment.lower() in combined.lower()


def test_checkpoint_imports_remain_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    data = importlib.reload(importlib.import_module("src.data"))
    backtesting = importlib.reload(importlib.import_module("src.backtesting"))
    core = importlib.reload(importlib.import_module("src.core.backtester"))
    service = importlib.reload(importlib.import_module("src.services.model_backtest_service"))
    routes = importlib.reload(importlib.import_module("src.api.model_backtest_routes"))

    assert hasattr(data, "load_local_dataset")
    assert hasattr(backtesting, "build_simulation_plan")
    assert hasattr(core, "run_walk_forward_backtest")
    assert hasattr(service, "run_model_backtest")
    assert hasattr(routes, "register_model_backtest_routes")

    monkeypatch.undo()
    perf_routes = importlib.reload(importlib.import_module("src.api.performance_routes"))
    assert hasattr(perf_routes, "register_performance_routes")
