from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_master_research_engine_specification_docs_exist_and_cover_required_topics() -> None:
    spec = DOCS / "architecture" / "MASTER_RESEARCH_ENGINE_SPECIFICATION.md"
    report = DOCS / "reports" / "PHASE4_5A_MASTER_RESEARCH_ENGINE_SPECIFICATION.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"

    assert spec.exists()
    assert report.exists()

    spec_text = _read(spec)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)

    assert "Master Research Engine Specification" in spec_text
    assert "Universal Market Input Domains" in spec_text
    assert "Metric Lifecycle Tracking" in spec_text
    assert "Defined -> Schema Ready" in spec_text
    assert "Source Identified" in spec_text
    assert "Connector Ready" in spec_text
    assert "Historical Data Ready" in spec_text
    assert "Math Implemented" in spec_text
    assert "Signal Ready" in spec_text
    assert "Backtested" in spec_text
    assert "Production Ready" in spec_text
    assert "Sports" in spec_text
    assert "Prediction Markets" in spec_text
    assert "Options / 0DTE" in spec_text
    assert "Futures" in spec_text
    assert "Crypto" in spec_text
    assert "Macro" in spec_text
    assert "Exists partially" in spec_text
    assert "Production ready" in spec_text
    assert "Documentation only" in spec_text
    assert "Scaffold only" in spec_text
    assert "Audit Summary" in spec_text
    assert "Reuse Rule" in spec_text
    assert "Out Of Scope" in spec_text

    assert "Phase 4.5A Master Research Engine Specification" in report_text
    assert "Audit Matrix" in report_text
    assert "Metric Lifecycle Summary" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text
    assert "universal feature registry" in report_text.lower()
    assert "MASTER_RESEARCH_ENGINE_SPECIFICATION" in report_text or "rename" in report_text.lower()

    assert "Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework" in project_status_text
    assert "docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md" in project_status_text
    assert "docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in project_status_text
    assert "Phase 4.9G - NFL Injuries Research Asset Population" in next_action_text


def test_master_research_engine_specification_docs_do_not_depend_on_runtime_code() -> None:
    spec = DOCS / "architecture" / "MASTER_RESEARCH_ENGINE_SPECIFICATION.md"
    report = DOCS / "reports" / "PHASE4_5A_MASTER_RESEARCH_ENGINE_SPECIFICATION.md"

    for text in (_read(spec), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "market input" in text.lower()
