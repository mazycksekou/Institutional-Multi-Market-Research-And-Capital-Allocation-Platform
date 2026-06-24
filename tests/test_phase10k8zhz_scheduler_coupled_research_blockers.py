from __future__ import annotations

import importlib
import inspect
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "SCHEDULER_COUPLED_RESEARCH_BLOCKERS_AFTER_10K8ZHZ.md",
    ROOT / "AI_ADJACENT_RESEARCH_DEFERRED_BLOCKERS_AFTER_10K8ZHZ.md",
    ROOT / "NEXT_SCHEDULER_RESEARCH_REMEDIATION_PLAN_AFTER_10K8ZHZ.md",
]


def test_scheduler_blocker_docs_exist() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "SCHEDULER_COUPLED_BLOCKED",
        "FILE_IO_OR_STORAGE_BLOCKED",
        "AI_ADJACENT_BLOCKED",
        "automation_scheduler/feature_ablation_lab.py",
        "automation_scheduler/calibration_strategy_filter.py",
        "automation_scheduler/experiment_history_store.py",
        "automation_scheduler/deepseek_*",
    ]:
        assert fragment.lower() in text.lower()


def test_scheduler_coupled_sources_are_local_and_deferred() -> None:
    for name in [
        "automation_scheduler.feature_ablation_lab",
        "automation_scheduler.calibration_strategy_filter",
        "automation_scheduler.experiment_history_store",
    ]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "openai" not in source
        assert "anthropic" not in source
        assert "requests" not in source
        assert "httpx" not in source
        assert "apscheduler" not in source
        assert "schedule(" not in source

    assert (ROOT / "automation_scheduler").exists()
    assert (ROOT / "automation_scheduler" / "feature_ablation_lab.py").exists()
