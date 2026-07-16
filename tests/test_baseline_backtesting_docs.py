from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_baseline_backtesting_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "BASELINE_BACKTESTING_LAYER.md"
    report = DOCS / "reports" / "PHASE5_5_BASELINE_BACKTESTING.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"
    p0_architecture = DOCS / "architecture" / "NFL_P0_DATA_FOUNDATION.md"

    for path in (
        architecture_doc,
        report,
        project_status,
        next_action,
        roadmap,
        master_index,
        retention_index,
        p0_architecture,
    ):
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)
    p0_text = _read(p0_architecture)

    assert "Baseline Backtesting Layer" in architecture_text
    assert "certified decision rows" in architecture_text.lower()
    assert "deterministic replay" in architecture_text.lower()
    assert "point-in-time validation" in architecture_text.lower()
    assert "benchmark comparison" in architecture_text.lower()
    assert "dashboard-ready outputs" in architecture_text.lower()
    assert "decision_cutoff_time = scheduled_kickoff_time - 5 minutes" in architecture_text
    assert "backtest_runs" in architecture_text
    assert "backtest_rows" in architecture_text
    assert "report.json" in architecture_text
    assert "summary.md" in architecture_text
    assert "dashboard.json" in architecture_text
    assert "backtest_completed" in architecture_text

    assert "Phase 5.5 - Baseline Backtesting" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "Implementation Summary" in report_text
    assert "Validation" in report_text
    assert "2 wins, 1 loss, 0 pushes" in report_text
    assert "20.0%" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text

    assert "Phase 5.5 - Baseline Backtesting" in project_status_text
    assert "Phase 5.6 - Validation And Hardening" in project_status_text
    assert "Phase 5.7 - Research Intelligence" in project_status_text
    assert "docs/architecture/BASELINE_BACKTESTING_LAYER.md" in project_status_text
    assert "docs/reports/PHASE5_5_BASELINE_BACKTESTING.md" in project_status_text

    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "Research Intelligence" in next_action_text
    assert "certified and hardened NFL research pipeline" in next_action_text

    assert "Phase 5.5 completed baseline backtesting from frozen, certified inputs." in roadmap_text
    assert "Phase 5.6 completed pipeline validation and hardening on the production research engine path." in roadmap_text
    assert "Phase 5.7 completed deterministic Research Intelligence on top of the certified NFL pipeline." in roadmap_text

    assert "docs/architecture/BASELINE_BACKTESTING_LAYER.md" in master_index_text
    assert "docs/architecture/BASELINE_BACKTESTING_LAYER.md" in retention_index_text
    assert "docs/reports/PHASE5_5_BASELINE_BACKTESTING.md" in retention_index_text

    assert "baseline-backtest-layer rollup" in p0_text.lower()
    assert "baseline backtesting is complete in Phase 5.5" in p0_text


def test_baseline_backtesting_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "BASELINE_BACKTESTING_LAYER.md"
    report = DOCS / "reports" / "PHASE5_5_BASELINE_BACKTESTING.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "backtest" in text.lower()
