from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.services.streamlit_dashboard_facade import odds_math as legacy_odds_math
from src.core import math_utils as core_math_utils


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFG_SAFE_MIGRATION_BATCH_1_REPORT.md"
README = ROOT / "README.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
DASHBOARD_DATA = ROOT / "src" / "services" / "streamlit_dashboard_data.py"
DAILY_HYGIENE_SCRIPT = ROOT / "scripts" / "daily_data_hygiene.py"
RUNNER = ROOT / "scripts" / "run_daily_data_hygiene.ps1"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str], label: str) -> None:
    for item in items:
        assert item in text, f"Missing {label} string: {item}"


def test_phase10k8zfg_safe_migration_batch_1() -> None:
    assert REPORT.exists()
    assert DAILY_HYGIENE_SCRIPT.exists()
    assert RUNNER.exists()

    report = read_text(REPORT)
    readme = read_text(README)
    streamlit_text = read_text(STREAMLIT_APP)
    dashboard_text = read_text(DASHBOARD_DATA)
    hygiene_text = read_text(DAILY_HYGIENE_SCRIPT)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZFE",
        "Relationship to 10K8ZFF",
        "Relationship to 10K8ZFE1",
        "Relationship to 10K8ZFE2",
        "Migration Strategy",
        "Canonical Owner Inputs",
        "Files Changed",
        "Functions Migrated Or Wrapped",
        "Functions Deferred",
        "Compatibility Guarantees",
        "Behavior Preservation Evidence",
        "Must-Not-Delete-Yet Compliance",
        "Daily Hygiene Scheduler Preservation",
        "Risk Preset / Scenario Language Preservation",
        "Safety Gate Results",
        "Tests Run",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    assert_contains_all(
        report,
        [
            "10K8ZFG",
            "Safe Migration Batch 1",
            "compatibility migration",
            "canonical owner",
            "canonical ownership map",
            "migration direction",
            "old import path preserved",
            "wrapper preserved",
            "behavior unchanged",
            "no files deleted",
            "no files moved",
            "no public functions removed",
            "no code migrated without tests",
            "no AI integration",
            "no ML training",
            "no backtest runner",
            "no controlled data loader",
            "no broker execution",
            "no real trade execution",
            "no scraper actions",
            "source code was preserved",
            "tests/fixtures were preserved",
            "manifests were preserved",
            "archives were preserved",
            "tracked files were preserved",
            "must_not_delete_yet complied",
            "daily data hygiene scheduler remains operational",
            "dry-run by default",
            "agent is advisory only",
            "risk preset controls sizing",
            "scenario mode controls missing-data handling",
            "Proceed to 10K8ZFH Safe Migration Batch 2",
        ],
        "report",
    )

    assert "This phase does not authorize deletion." in report

    for domain in [
        "canonical owner",
        "canonical ownership map",
        "migration direction",
        "old import path preserved",
        "wrapper preserved",
        "behavior unchanged",
    ]:
        assert domain in report

    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None
    assert "your_real_secret" not in report

    assert_contains_all(
        readme,
        [
            "10K8ZF7 R2 Archive Pipeline",
            "cleanup mode is explicit and gated",
        ],
        "README",
    )
    assert re.search(r"AKIA[0-9A-Z]{16}", readme) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", readme) is None
    assert "your_real_secret" not in readme

    assert "Aggressive paper only" not in streamlit_text
    assert "Aggressive" in dashboard_text
    assert "risk preset controls sizing" in dashboard_text.lower()
    assert "scenario mode controls missing-data handling" in dashboard_text.lower()
    assert "Baseline / Imputed" in dashboard_text
    assert "Strict / Complete Cases Only" in dashboard_text
    assert "Stress / Adverse Missing-Data Fill" in dashboard_text
    assert "dry-run by default" in hygiene_text
    assert "--execute" in hygiene_text
    assert "allow-delete-local-raw" in hygiene_text

    assert legacy_odds_math.american_to_decimal(150) == pytest.approx(
        core_math_utils.american_to_decimal(150), rel=0, abs=1e-6
    )
    assert legacy_odds_math.american_to_decimal(-200) == pytest.approx(
        core_math_utils.american_to_decimal(-200), rel=0, abs=1e-6
    )
    assert legacy_odds_math.american_to_implied_probability(150) == pytest.approx(
        round(core_math_utils.american_to_implied_probability(150), 6), rel=0, abs=1e-6
    )
    assert legacy_odds_math.decimal_to_implied_probability(2.5) == pytest.approx(
        round(core_math_utils.decimal_to_implied_probability(2.5), 6), rel=0, abs=1e-6
    )
    assert legacy_odds_math.decimal_to_american(2.5) == core_math_utils.decimal_to_american(2.5)

    legacy_vig = legacy_odds_math.remove_two_way_vig(0.55, 0.55)
    core_vig = core_math_utils.remove_two_way_vig(0.55, 0.55)
    assert legacy_vig["fair_probability_a"] == pytest.approx(round(core_vig["fair_probability_a"], 6), rel=0, abs=1e-6)
    assert legacy_vig["fair_probability_b"] == pytest.approx(round(core_vig["fair_probability_b"], 6), rel=0, abs=1e-6)
    assert legacy_vig["vig"] == pytest.approx(round(core_vig["vig"], 6), rel=0, abs=1e-6)

    legacy_ev = legacy_odds_math.calculate_ev(10, 0.55, -110)
    core_ev = core_math_utils.calculate_ev(10, 0.55, -110)
    assert legacy_ev == pytest.approx(round(core_ev, 6), rel=0, abs=1e-6)

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))

