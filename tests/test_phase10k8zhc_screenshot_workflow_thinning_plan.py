from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHC_SCREENSHOT_WORKFLOW_THINNING_PLAN.md",
    ROOT / "SCREENSHOT_WORKFLOW_OWNERSHIP_MAP_AFTER_10K8ZHC.md",
    ROOT / "SCREENSHOT_WORKFLOW_MIGRATION_SEQUENCE_AFTER_10K8ZHC.md",
]


def test_screenshot_docs_state_service_ownership() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "screenshot_intake.py",
        "compatibility_shim_candidate",
        "migrate_to_src_services",
        "src/services/screenshot_workflow.py",
        "ocr/image parsing is not core math",
        "provider and connector data must continue to arrive through canonical services",
        "no live connector calls",
    ]:
        assert phrase in text


def test_screenshot_intake_imports_and_behaves_safely() -> None:
    screenshot_intake = importlib.import_module("src.services.screenshot_intake")
    payload = {"sport": "basketball_nba", "market": "h2h", "selection": "home", "odds_american": -110}
    parsed = screenshot_intake.parse_ticket(payload)
    assert parsed["sport"] == "basketball_nba"
    analyzed = screenshot_intake.analyze_screenshot_ticket(payload)
    assert analyzed["ok"] is False or "provider_enrichment" in analyzed


def test_screenshot_intake_source_is_local_only() -> None:
    text = (ROOT / "src" / "services" / "screenshot_intake.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests", "httpx", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]:
        assert forbidden not in text
