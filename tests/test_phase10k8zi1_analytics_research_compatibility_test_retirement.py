from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI1_ANALYTICS_RESEARCH_COMPATIBILITY_TEST_RETIREMENT.md",
    ROOT / "ANALYTICS_RESEARCH_COMPATIBILITY_TEST_RETIREMENT_MAP_AFTER_10K8ZI1.md",
    ROOT / "ANALYTICS_RESEARCH_ACTIVE_TEST_REFERENCE_SCAN_AFTER_10K8ZI1.md",
    ROOT / "ANALYTICS_RESEARCH_TEST_BLOCKER_STATUS_AFTER_10K8ZI1.md",
]

ACTIVE_TESTS = [
    ROOT / "tests/test_governance_health.py",
    ROOT / "tests/test_governance_report.py",
    ROOT / "tests/test_model_validation_report.py",
    ROOT / "tests/test_market_research_store.py",
    ROOT / "tests/test_data_intelligence_stack.py",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_docs_record_compatibility_retirement_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "compatibility-oriented tests",
        "canonical runtime checks",
        "src.analytics.governance",
        "src.analytics.reports",
        "src.research.storage",
        "src.research.maturity",
        "historical evidence only",
    ]:
        assert fragment.lower() in text.lower()


def test_active_tests_now_use_canonical_owners() -> None:
    for path in ACTIVE_TESTS:
        content = _read(path)
        assert "from src.analytics" in content or "from src.research" in content
        assert "from model_governance.governance_health" not in content
        assert "from model_governance.governance_report" not in content
        assert "from model_governance.model_validation_report" not in content
        assert "from research.market_research_schema" not in content
        assert "from research.market_research_store" not in content
        assert "import research.market_research_schema" not in content
        assert "import research.market_research_store" not in content
        assert "automation_scheduler.deep_learning_research_lanes" not in content
        assert "automation_scheduler.tabular_ml_research" not in content
        assert "automation_scheduler.model_maturity_registry" not in content


def test_canonical_analytics_and_research_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    analytics = importlib.reload(importlib.import_module("src.analytics"))
    research = importlib.reload(importlib.import_module("src.research"))

    performance = analytics.build_performance_summary([0.1, -0.05, 0.2])
    governance = analytics.summarize_governance(blockers=("x",))
    storage = research.describe_research_store(path="local-only")
    maturity = research.build_model_maturity_registry(total_labeled_outcomes=25)

    assert performance.sample_count == 3
    assert governance.status == "review_required"
    assert storage.local_only is True
    assert maturity["status"] == "model_maturity_registry"
    assert maturity["total_models"] > 0
