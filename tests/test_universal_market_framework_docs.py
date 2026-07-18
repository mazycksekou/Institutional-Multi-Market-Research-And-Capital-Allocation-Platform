from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_universal_market_framework_governance_docs_are_indexed_and_placeholder_only() -> None:
    product_spec = DOCS / "PRODUCT_SPEC.md"
    business_strategy = DOCS / "BUSINESS_STRATEGY.md"
    ip_register = DOCS / "INTELLECTUAL_PROPERTY_REGISTER.md"
    master_index = DOCS / "MASTER_DOCUMENT_INDEX.md"
    retention_index = DOCS / "DOCUMENT_RETENTION_INDEX.md"

    for path in [product_spec, business_strategy, ip_register, master_index, retention_index]:
        assert path.exists()

    for path in [product_spec, business_strategy, ip_register]:
        text = _read(path)
        assert "Status: Draft — Not Yet Authoritative" in text
        assert "## Purpose" in text
        assert "## Planned Table Of Contents" in text
        assert "## Authoritative Document References" in text
        assert "## Activation / Completion Trigger" in text

    ip_text = _read(ip_register)
    for category in [
        "Software IP",
        "Data IP",
        "Research and methodology IP",
        "Feature, math, signal, and decision IP",
        "Research Intelligence and Worldview IP",
        "Capital-allocation and risk IP",
        "Process and governance IP",
        "Validated performance and track-record IP",
        "Ownership, confidentiality, and protection status",
    ]:
        assert category in ip_text

    retention_text = _read(retention_index)
    for doc in [
        "docs/PRODUCT_SPEC.md",
        "docs/BUSINESS_STRATEGY.md",
        "docs/INTELLECTUAL_PROPERTY_REGISTER.md",
    ]:
        assert doc in retention_text


def test_universal_market_framework_roadmap_sequence_and_mission_are_preserved() -> None:
    project_status = _read(DOCS / "PROJECT_STATUS.md")
    roadmap = _read(DOCS / "MASTER_ROADMAP.md")

    assert "## Mission" in project_status
    assert "NFL Production Completion" in project_status
    assert "Data Identity, Reconciliation and Lakehouse Foundation" in project_status
    assert "First Controlled NFL Vendor Ingest" in project_status
    assert "Covariance and Time-Dependent Risk Capability Audit" in project_status
    assert (
        "Build a deterministic, explainable, auditable, institutional-grade\n"
        "multi-market research and capital allocation platform"
    ) in project_status

    expected_sequence = (
        "Universal Market Framework\n"
        "-> NFL Production Completion\n"
        "-> Data Identity, Reconciliation and Lakehouse Foundation\n"
        "-> First Controlled NFL Vendor Ingest\n"
        "-> Portable External Research-Data Storage\n"
        "-> Covariance and Time-Dependent Risk Capability Audit\n"
        "-> Implement only covariance and risk capabilities confirmed missing by that audit\n"
        "-> additional sports\n"
        "-> prediction markets\n"
        "-> Zero-DTE options\n"
        "-> Worldview Intelligence\n"
        "-> cross-market intelligence\n"
        "-> universal risk and capital allocation\n"
        "-> paper trading\n"
        "-> controlled live execution\n"
        "-> production platform and IP custody\n"
        "-> institutional readiness\n"
        "-> autonomous development"
    )
    assert expected_sequence in roadmap
    assert "These are roadmap lanes only" in roadmap
    assert "Immediately after complete NFL production validation" in roadmap
