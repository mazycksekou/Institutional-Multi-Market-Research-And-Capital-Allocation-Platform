from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_universal_math_engine_contract_docs_exist_and_cover_required_topics() -> None:
    architecture_doc = DOCS / "architecture" / "UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md"
    report = DOCS / "reports" / "PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md"
    project_status = DOCS / "PROJECT_STATUS.md"
    next_action = DOCS / "NEXT_ACTION.md"
    contract_index = DOCS / "contracts" / "CONTRACT_INDEX.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [
        architecture_doc,
        report,
        project_status,
        next_action,
        contract_index,
        master_index,
        retention_index,
    ]:
        assert path.exists(), f"missing document: {path}"

    architecture_matches = sorted(path.resolve() for path in DOCS.rglob("UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md"))
    report_matches = sorted(path.resolve() for path in DOCS.rglob("PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md"))
    assert architecture_matches == [architecture_doc.resolve()]
    assert report_matches == [report.resolve()]

    architecture_text = _read(architecture_doc)
    report_text = _read(report)
    project_status_text = _read(project_status)
    next_action_text = _read(next_action)
    contract_index_text = _read(contract_index)
    master_index_text = _read(master_index)
    retention_index_text = _read(retention_index)

    assert "Universal Mathematical Engine Contracts" in architecture_text
    assert "Engine ID" in architecture_text
    assert "Engine Name" in architecture_text
    assert "Purpose" in architecture_text
    assert "Description" in architecture_text
    assert "Supported Markets" in architecture_text
    assert "Required Input Feature IDs" in architecture_text
    assert "Produced Output Feature IDs" in architecture_text
    assert "Input Data Types" in architecture_text
    assert "Output Data Types" in architecture_text
    assert "Units" in architecture_text
    assert "Dependencies" in architecture_text
    assert "Numerical Stability Requirements" in architecture_text
    assert "Point-in-Time Requirements" in architecture_text
    assert "Validation Rules" in architecture_text
    assert "Error Conditions" in architecture_text
    assert "Versioning Rules" in architecture_text
    assert "Lineage Requirements" in architecture_text
    assert "Owning Runtime Module" in architecture_text
    assert "Owning Validation Module" in architecture_text
    assert "Priority" in architecture_text
    assert "Lifecycle Status" in architecture_text
    assert "Defined -> Contract Ready -> Schema Ready" in architecture_text
    assert "Historical Dataset Ready" in architecture_text
    assert "Math Implemented" in architecture_text
    assert "Backtested" in architecture_text
    assert "Production Ready" in architecture_text
    assert "Probability" in architecture_text
    assert "Expected Value" in architecture_text
    assert "Reverse Line Movement" in architecture_text
    assert "Greeks" in architecture_text
    assert "Probability Walls" in architecture_text
    assert "No engine may reference a feature that is not represented in the Universal Feature Registry." in architecture_text
    assert "Research Asset Registry" in architecture_text
    assert "does not implement formulas" in architecture_text.lower()

    assert "Phase 4.5C - Universal Mathematical Engine Contracts" in report_text
    assert "Existing Mathematical Abstractions Discovered" in report_text
    assert "Existing Abstractions Reused" in report_text
    assert "Universal Mathematical Engine Contracts Created or Extended" in report_text
    assert "Dependency Framework Implemented" in report_text
    assert "Lifecycle Framework Implemented" in report_text
    assert "Duplicate Systems Avoided" in report_text
    assert "Future Research Asset Registry Recommendation" in report_text
    assert "Senior Systems Engineer Review" in report_text
    assert "Worldview Intelligence Review" in report_text
    assert "Readiness for Phase 4.5D" in report_text

    assert "Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework" in project_status_text
    assert "Phase 4.7 - Historical Dataset Acquisition and Certification (minimum certified schema first)" in next_action_text
    assert "docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in project_status_text
    assert "docs/reports/PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in project_status_text
    assert "Canonical math-engine inputs, outputs, lifecycle, and validation rules" in contract_index_text
    assert "docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in master_index_text
    assert "docs/reports/PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md" in retention_index_text


def test_universal_math_engine_contract_docs_do_not_depend_on_runtime_code() -> None:
    architecture_doc = DOCS / "architecture" / "UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md"
    report = DOCS / "reports" / "PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md"

    for text in (_read(architecture_doc), _read(report)):
        assert "import " not in text.lower()
        assert "subprocess" not in text.lower()
        assert "math" in text.lower()
