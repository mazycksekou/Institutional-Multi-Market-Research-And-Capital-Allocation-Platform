from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_universal_feature_registry_docs_exist_and_cover_required_topics() -> None:
    registry = DOCS / "architecture" / "UNIVERSAL_FEATURE_REGISTRY.md"
    report = DOCS / "reports" / "PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    master_spec = DOCS / "architecture" / "MASTER_RESEARCH_ENGINE_SPECIFICATION.md"

    assert registry.exists()
    assert report.exists()
    assert master_spec.exists()

    registry_matches = sorted(path.resolve() for path in DOCS.rglob("UNIVERSAL_FEATURE_REGISTRY.md"))
    report_matches = sorted(path.resolve() for path in DOCS.rglob("PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md"))
    assert registry_matches == [registry.resolve()]
    assert report_matches == [report.resolve()]

    registry_text = _read(registry)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    master_spec_text = _read(master_spec)

    assert "Universal Feature Registry" in registry_text
    assert "Canonical Owners Reused" in registry_text
    assert "Feature Registry Contract" in registry_text
    assert "Feature Lifecycle" in registry_text
    assert "Defined -> Schema Ready" in registry_text
    assert "Source Identified" in registry_text
    assert "Connector Ready" in registry_text
    assert "Historical Dataset Ready" in registry_text
    assert "Math Ready" in registry_text
    assert "Signal Ready" in registry_text
    assert "Validated" in registry_text
    assert "Production Ready" in registry_text
    assert "Universal" in registry_text
    assert "Sports" in registry_text
    assert "Prediction Markets" in registry_text
    assert "Options / 0DTE" in registry_text
    assert "Futures" in registry_text
    assert "Crypto" in registry_text
    assert "Macro" in registry_text
    assert "Feature ID" in registry_text
    assert "Feature Name" in registry_text
    assert "Feature Family" in registry_text
    assert "Market Family" in registry_text
    assert "Feature Version" in registry_text
    assert "Entity / Side Scope" in registry_text
    assert "Dataset Grain Compatibility" in registry_text
    assert "Source Dataset Field References" in registry_text
    assert "Transformation Version" in registry_text
    assert "Cutoff Semantics" in registry_text
    assert "Lifecycle Status" in registry_text
    assert "Portability Classification" in registry_text
    assert "Priority" in registry_text
    assert "src.data.feature_registry" in registry_text
    assert "dataset.sports.nfl.historical_dataset" in registry_text
    assert "dataset_row_id" in registry_text
    assert "decision_context_id" in registry_text
    assert "scheduled_kickoff_time - 5 minutes" in registry_text
    assert "deterministic derived" in registry_text.lower()
    assert "deferred mathematical-engine output" in registry_text.lower()
    assert "Out Of Scope" in registry_text
    assert "do not implement providers" in registry_text.lower()

    assert "Phase 4.5B Universal Feature Registry" in report_text or "Phase 4.5B - Universal Feature Registry" in report_text
    assert "Existing registries discovered" in report_text
    assert "Existing abstractions reused" in report_text
    assert "Feature families documented" in report_text
    assert "Lifecycle framework implemented" in report_text
    assert "Duplicate systems avoided" in report_text
    assert "Naming review" in report_text
    assert "MASTER_RESEARCH_ENGINE_SPECIFICATION" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text
    assert "Phase 4.5C - Universal Math Engine Contracts" in report_text

    assert "Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework" in project_status_text
    assert "Universal Market Framework" in next_action_text
    assert "Phase 5.7 - Research Intelligence" in next_action_text
    assert "docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md" in project_status_text
    assert "docs/reports/PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md" in project_status_text
    assert "certified and hardened nfl research pipeline" in next_action_text.lower()
    assert "MASTER_RESEARCH_ENGINE_SPECIFICATION" in master_spec_text


def test_universal_feature_registry_docs_do_not_depend_on_runtime_code() -> None:
    registry = DOCS / "architecture" / "UNIVERSAL_FEATURE_REGISTRY.md"
    report = DOCS / "reports" / "PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md"

    for text in (_read(registry), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "registry" in text.lower()
