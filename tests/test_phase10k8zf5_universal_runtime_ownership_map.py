from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REPORT = ROOT / "PHASE10K8ZF5_UNIVERSAL_RUNTIME_OWNERSHIP_MAP.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zf5_universal_runtime_ownership_map() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZF5 report to exist."
    assert README.is_file(), "Expected README.md to exist."

    readme_text = read_text(README)
    report_text = read_text(REPORT)

    required_readme_strings = [
        "Universal Ownership Rule",
        "one canonical owner per concept",
        "Do not create parallel implementations of math, metrics, signals, providers, backtesting, storage, or dashboard-data logic.",
        "automation_scheduler/ and live_market_intelligence/ are migration sources",
        "Do not delete legacy code until duplicate status is proven",
    ]
    for needle in required_readme_strings:
        assert needle in readme_text, f"Missing README string: {needle}"

    required_report_strings = [
        "10K8ZF5",
        "Universal Runtime Entrypoint + Canonical Ownership Map",
        "senior-systems-engineer quality",
        "one universal system",
        "one canonical owner per concept",
        "no duplicate math",
        "no duplicate metrics",
        "no duplicate signals",
        "no duplicate risk logic",
        "no duplicate provider adapters",
        "no duplicate backtest engines",
        "no duplicate dashboard-data paths",
        "Do not delete any code until explicitly proven duplicate",
        "automation_scheduler/ is a migration source until mapped into canonical owners",
        "live_market_intelligence/ is a migration source until mapped into canonical owners",
        "src/core/",
        "src/risk/",
        "src/providers/",
        "src/markets/",
        "src/signals/",
        "src/backtester/",
        "src/metrics/",
        "src/storage/",
        "src/api/",
        "dashboard/",
        "src/signals/footprint.py detects large-flow anomaly",
        "src/signals/opening_range.py detects OR high/low/break/failure",
        "src/backtester/experiment_matrix.py tests with / without / fade / confirm / avoid",
        "src/metrics/ proves whether signal improved or degraded expectancy",
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
        "implementation reviewed in 10K8ZF5",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_sections = [
        "Runtime Entrypoints",
        "Dashboard/UI Ownership",
        "Backend/API Ownership",
        "Core Math Ownership",
        "Risk Ownership",
        "Provider Ownership",
        "Market Schema/Catalog Ownership",
        "Signal/Research Ownership",
        "Backtester/Data Ownership",
        "Metrics/Reporting Ownership",
        "Storage/History Ownership",
        "automation_scheduler Migration Source Map",
        "live_market_intelligence Migration Source Map",
        "research and research_engine Migration Source Map",
        "providers and betting_providers Migration Source Map",
        "Root File Ownership Map",
        "Duplicate Math Risk Map",
        "Duplicate Metrics Risk Map",
        "Duplicate Signals Risk Map",
        "Duplicate Risk Logic Map",
        "Duplicate Provider Risk Map",
        "Duplicate Backtest Risk Map",
        "Duplicate Storage Risk Map",
        "Duplicate Dashboard-Data Risk Map",
        "Duplicate API Route Risk Map",
        "Must-Not-Delete-Yet List",
        "Future Migration Actions",
        "Pre-Backtest Universal System Gates",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert section in report_text, f"Missing report section: {section}"

    for path in [
        "src/core/",
        "src/risk/",
        "src/providers/",
        "src/markets/",
        "src/signals/",
        "src/backtester/",
        "src/metrics/",
        "src/storage/",
        "src/api/",
        "dashboard/",
    ]:
        assert path in report_text, f"Missing final architecture path: {path}"

    for needle in [
        "Deletion is not allowed in this phase.",
        "do not delete any code until explicitly proven duplicate",
    ]:
        assert needle.lower() in report_text.lower()

    forbidden_claims = [
        "live-execution engine",
        "production live trading enabled",
        "broker orders enabled",
        "real trades enabled",
    ]
    for needle in forbidden_claims:
        assert needle not in readme_text
        assert needle not in report_text

    for pattern in [
        ROOT / "pages",
        ROOT / "app" / "pages",
        ROOT / "frontend",
        ROOT / "frontend" / "pages",
    ]:
        if pattern.exists():
            assert not any(pattern.rglob("*.py")), f"Unexpected frontend page files in {pattern}"
