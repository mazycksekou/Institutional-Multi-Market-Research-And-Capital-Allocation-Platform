from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
REPORT = ROOT / "PHASE10K8ZF4_ASSET_GRADE_REPO_CLEAN_INVENTORY.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zf4_asset_grade_repo_clean_inventory() -> None:
    assert README.is_file(), "Expected README.md to exist."
    assert GITIGNORE.is_file(), "Expected .gitignore to exist."
    assert REPORT.is_file(), "Expected the 10K8ZF4 report to exist."

    readme_text = read_text(README)
    gitignore_text = read_text(GITIGNORE)
    report_text = read_text(REPORT)

    required_readme_strings = [
        "Unified Quantitative Market Research & Backtesting Engine",
        "research/backtest mode only",
        "Terminal 1",
        "Backend / FastAPI Engine",
        "Terminal 2",
        "Streamlit Operator Dashboard",
        "Do not merge FastAPI and Streamlit into one file.",
        "streamlit_app.py is the dashboard entrypoint.",
        "main.py is the backend/API entrypoint if present.",
        "Local /data is not product source code.",
        "Do not commit local data dumps.",
        "Only tiny deterministic fixtures belong in tests/fixtures/.",
        "pre-backtest cleanup must finish before controlled data loader or backtest runner",
    ]
    for needle in required_readme_strings:
        assert needle in readme_text, f"Missing README string: {needle}"

    required_gitignore_strings = [
        "data/",
        "reports/",
        ".env",
        "__pycache__/",
        ".pytest_cache/",
        ".venv/",
        "*.sqlite",
        "*.db",
    ]
    for needle in required_gitignore_strings:
        assert needle in gitignore_text, f"Missing .gitignore string: {needle}"

    required_report_strings = [
        "10K8ZF4",
        "Asset-Grade Repo Clean Inventory",
        "senior-systems-engineer quality",
        "README.md",
        ".gitignore",
        "Local /data is not product source code",
        "Do not commit local data dumps",
        "Only tiny deterministic fixtures belong in tests/fixtures/",
        "Terminal 1 is Backend / FastAPI Engine",
        "Terminal 2 is Streamlit Operator Dashboard",
        "Do not merge FastAPI and Streamlit into one file",
        "streamlit_app.py is the dashboard entrypoint",
        "main.py is the backend/API entrypoint if present",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Later: Live Model Testing",
        "pre-backtest cleanup must finish before controlled data loader or backtest runner",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls without explicit provider phase",
        "no database writes without explicit storage phase",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF4",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    forbidden_claims = [
        "live-execution engine",
        "production live trading enabled",
        "broker orders enabled",
        "real trades enabled",
    ]
    for needle in forbidden_claims:
        assert needle not in readme_text
        assert needle not in report_text

    frontend_globs = [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]
    for pattern in frontend_globs:
        assert not list(ROOT.glob(pattern)), f"Unexpected frontend page files matching {pattern}"
