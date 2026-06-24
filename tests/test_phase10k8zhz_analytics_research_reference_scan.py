from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "ANALYTICS_RESEARCH_ACTIVE_REFERENCE_SCAN_AFTER_10K8ZHZ.md",
    ROOT / "ANALYTICS_RESEARCH_REFERENCE_REMEDIATION_PLAN_AFTER_10K8ZHZ.md",
]


def test_reference_scan_docs_exist_and_classify_references() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for fragment in [
        "runtime import",
        "test import",
        "monkeypatch or mock targets",
        "historical proof evidence",
        "compatibility export",
        "string-only metadata",
        "doc-only evidence",
    ]:
        assert fragment in text.lower()


def test_doc_only_evidence_is_not_treated_as_blocker() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    assert "doc-only evidence" in text.lower()
    assert "doc-only evidence is tracked separately and does not count as a runtime dependency" in text.lower()


def test_canonical_architecture_remains_intact_and_deleted_shells_not_reintroduced() -> None:
    for relpath in [
        "src/analytics/__init__.py",
        "src/research/__init__.py",
        "src/connectors",
        "src/providers",
    ]:
        assert (ROOT / relpath).exists()

    for relpath in [
        "kalshi_client.py",
        "providers/kalshi_provider.py",
        "betting_providers/kalshi_api.py",
        "automation_scheduler/kalshi_readonly_adapter.py",
        "automation_scheduler/kalshi_market_provider.py",
        "sharp_client.py",
        "providers/sharp_provider.py",
        "betting_providers/sharp_api.py",
        "betting_providers/the_odds_api.py",
        "betting_providers/sportsgameodds.py",
        "automation_scheduler/sharp_sportsbook_adapter.py",
        "automation_scheduler/sportsbook_odds_provider.py",
    ]:
        assert not (ROOT / relpath).exists()
