from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHF_DASHBOARD_ENTRYPOINT_OWNERSHIP_AUDIT.md",
    ROOT / "DASHBOARD_ENTRYPOINT_OWNERSHIP_MAP_AFTER_10K8ZHF.md",
    ROOT / "DASHBOARD_THINNING_SEQUENCE_AFTER_10K8ZHF.md",
]


def test_dashboard_docs_state_entrypoints_are_shells_only() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS).lower()
    for phrase in [
        "main.py is not a deletion candidate",
        "streamlit_app.py is not a deletion candidate",
        "keep_entrypoint_or_dashboard",
        "bootstrap shell",
        "display/ui shell",
        "no connector ownership belongs in the dashboard",
    ]:
        assert phrase in text


def test_dashboard_entrypoint_files_are_not_deletion_candidates() -> None:
    main_text = (ROOT / "main.py").read_text(encoding="utf-8")
    streamlit_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    for phrase in ["load_dotenv", "yfinance", "automation_scheduler"]:
        assert phrase in main_text or phrase in streamlit_text


def test_dashboard_source_scan_is_import_safe_by_design() -> None:
    for relpath in ["main.py", "streamlit_app.py"]:
        assert (ROOT / relpath).exists()
