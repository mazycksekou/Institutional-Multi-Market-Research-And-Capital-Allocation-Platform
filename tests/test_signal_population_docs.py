from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_signal_population_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "SIGNAL_POPULATION_LAYER.md"
    report = DOCS / "reports" / "PHASE5_3_REUSABLE_SIGNALS.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    roadmap = DOCS / "MASTER_ROADMAP.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in (architecture_doc, report, project_status, next_action, roadmap, master_index, retention_index):
        assert path.exists(), f"missing document: {path}"

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    roadmap_text = _read(roadmap)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "Signal Population Layer" in architecture_text
    assert "observation-only" in architecture_text.lower()
    assert "decision_cutoff_time = scheduled_kickoff_time - 5 minutes" in architecture_text
    assert "Reusable Signals" in report_text
    assert "Canonical Owners Reused" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview / Research Query Engine Review" in report_text
    assert "signal_ready" in report_text
    assert "Phase 5.3 - Reusable Signals" in project_status_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "Research Intelligence" in next_action_text
    assert "certified and hardened nfl research pipeline" in next_action_text.lower()
    assert "Phase 5.3 completed reusable signals." in roadmap_text
    assert "Phase 5.4 completed the decision-row generation layer from the certified signal layer." in roadmap_text
    assert "docs/architecture/SIGNAL_POPULATION_LAYER.md" in master_index_text
    assert "docs/architecture/SIGNAL_POPULATION_LAYER.md" in retention_index_text
    assert "docs/reports/PHASE5_3_REUSABLE_SIGNALS.md" in retention_index_text


def test_signal_population_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "SIGNAL_POPULATION_LAYER.md"
    report = DOCS / "reports" / "PHASE5_3_REUSABLE_SIGNALS.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "signal" in text.lower()
