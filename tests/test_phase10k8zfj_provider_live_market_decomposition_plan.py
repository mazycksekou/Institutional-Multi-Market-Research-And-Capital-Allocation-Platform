from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFJ_PROVIDER_LIVE_MARKET_DECOMPOSITION_PLAN.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_contains_all(text: str, required: list[str]) -> None:
    missing = [item for item in required if item not in text]
    assert not missing, f"Missing required strings: {missing}"


def test_provider_live_market_decomposition_plan_report_is_complete() -> None:
    assert REPORT.exists(), "Expected provider decomposition plan report to exist"
    text = _read(REPORT)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZFF",
        "Relationship to 10K8ZFI",
        "Provider Decomposition Method",
        "Provider Inventory",
        "Provider Interface / Adapter Base Lane",
        "Provider Registry / Router Lane",
        "Provider Normalization / Contracts Lane",
        "Provider Health / Status Lane",
        "Sportsbook Adapters Lane",
        "Kalshi Adapters Lane",
        "Sharp / Market Intelligence Adapters Lane",
        "Enrichment / Services Lane",
        "live_market_intelligence Lane",
        "Deprecated / Manual Review Candidates",
        "Future Provider Owner Decision",
        "Provider Migration Waves",
        "Must-Not-Delete-Yet Compliance",
        "External Call Safety Policy",
        "Unsafe Actions",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    _assert_contains_all(text, required_sections)

    required_strings = [
        "10K8ZFJ",
        "Provider / live_market_intelligence Decomposition Plan",
        "decomposition plan only",
        "no files deleted",
        "no files moved",
        "no source-function migration",
        "no public functions removed",
        "behavior unchanged",
        "provider canonical owner",
        "provider migration direction",
        "canonical owner",
        "canonical ownership map",
        "migration direction",
        "must_not_delete_yet",
        "Provider Interface / Adapter Base",
        "Provider Registry / Router",
        "Provider Normalization / Contracts",
        "Provider Health / Status",
        "Sportsbook Adapters",
        "Kalshi Adapters",
        "Sharp / Market Intelligence Adapters",
        "Enrichment / Services",
        "live_market_intelligence",
        "Deprecated / Manual Review Candidates",
        "Provider Wave 0",
        "Provider Wave 1",
        "Provider Wave 2",
        "Provider Wave 3",
        "Provider Wave 4",
        "Provider Wave 5",
        "Provider Wave 6",
        "Provider Wave 7",
        "Provider Wave 8",
        "no external API calls",
        "no live connectors",
        "no credentials committed",
        "no secrets printed",
        "R2 credentials come from environment variables only",
        "daily data hygiene scheduler remains operational",
        "dry-run by default",
        "agent is advisory only",
        "agent does not directly delete files",
        "risk preset controls sizing",
        "scenario mode controls missing-data handling",
        "This phase does not authorize deletion.",
        "Proceed to 10K8ZFK Test Suite Cleanup Plan",
        "source code was preserved",
        "tests/fixtures were preserved",
        "manifests were preserved",
        "archives were preserved",
        "tracked files were preserved",
    ]
    _assert_contains_all(text, required_strings)

    for wave in range(9):
        assert f"Provider Wave {wave}" in text

    assert "scaffold-only" in text
    assert "empty scaffold tree" in text
    assert "no source-function migration" in text
    assert "no public functions removed" in text
    assert "behavior unchanged" in text
    assert "This phase does not authorize deletion." in text

    live_market_intelligence = ROOT / "live_market_intelligence"
    assert live_market_intelligence.exists()
    assert not any(path.is_file() for path in live_market_intelligence.rglob("*"))


def test_provider_live_market_decomposition_plan_has_no_obvious_secrets_or_frontend_pages() -> None:
    patterns = [
        "AKIA",
        "ASIA",
        "your_real_secret",
    ]

    candidate_paths = []
    candidate_paths.extend(path for path in ROOT.glob("README*") if path.is_file())
    candidate_paths.extend(path for path in ROOT.glob("PHASE*.md") if path.is_file())
    candidate_roots = [
        ROOT / "providers",
        ROOT / "betting_providers",
        ROOT / "src" / "automation_scheduler_legacy",
        ROOT / "src",
    ]
    for base in candidate_roots:
        if base.exists():
            candidate_paths.extend(
                path
                for path in base.rglob("*")
                if path.is_file() and path.suffix in {".py", ".md", ".txt", ".toml", ".yaml", ".yml"}
            )
    candidate_paths.extend(
        path
        for path in [ROOT / "main.py", ROOT / "api_server.py", ROOT / "streamlit_app.py", ROOT / "screenshot_intake.py"]
        if path.exists()
    )

    for path in candidate_paths:
        text = _read(path)
        for pattern in patterns:
            assert pattern not in text, f"Found {pattern} in {path}"

    frontend_patterns = [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]
    for pattern in frontend_patterns:
        assert not list(ROOT.glob(pattern)), f"Unexpected frontend page files matched {pattern}"

    streamlit_text = _read(ROOT / "streamlit_app.py")
    dashboard_text = _read(ROOT / "src" / "automation_scheduler_legacy" / "streamlit_dashboard_data.py")
    assert "Aggressive paper only" not in streamlit_text
    assert "None - no risk preset adjustment" in streamlit_text
    assert "Aggressive" in dashboard_text
    assert "Baseline / Imputed" in dashboard_text
    assert "Strict / Complete Cases Only" in dashboard_text
    assert "Stress / Adverse Missing-Data Fill" in dashboard_text
