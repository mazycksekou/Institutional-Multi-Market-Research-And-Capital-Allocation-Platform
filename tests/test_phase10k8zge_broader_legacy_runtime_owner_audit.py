from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ROOT / "PHASE10K8ZGE_BROADER_LEGACY_RUNTIME_OWNER_AUDIT.md",
    ROOT / "LEGACY_RUNTIME_OWNER_INVENTORY_AFTER_10K8ZGE.md",
    ROOT / "LEGACY_APPLE_TRANSPORT_MAP_AFTER_10K8ZGE.md",
    ROOT / "AUTOMATION_SCHEDULER_REMAINING_OWNERSHIP_AFTER_10K8ZGE.md",
    ROOT / "ROOT_LEVEL_ENGINE_OWNERSHIP_MAP_AFTER_10K8ZGE.md",
    ROOT / "NEXT_MIGRATION_AND_DELETION_SEQUENCE_AFTER_10K8ZGE.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_broader_legacy_runtime_owner_audit_docs_and_tags() -> None:
    docs = {path.name: _read(path) for path in REPORTS}
    combined = "\n".join(docs.values())

    required_sections = [
        "Executive Summary",
        "Big-Picture Architecture",
        "What Has Already Been Migrated Or Deleted",
        "Remaining Legacy Owners",
        "What Should Not Be Deleted",
        "What Is Unsafe To Touch",
        "Recommended Next Actions",
        "Transport Table",
        "Ownership Families",
        "Ownership Map",
        "Recommended Next Phases",
        "Deletion Policy",
    ]
    for section in required_sections:
        assert section in combined, f"missing section: {section}"

    required_tags = [
        "MIGRATE_TO_SRC_PROVIDERS",
        "MIGRATE_TO_SRC_CONNECTORS",
        "MIGRATE_TO_SRC_SERVICES",
        "MIGRATE_TO_SRC_CORE",
        "MIGRATE_TO_SRC_AI_LATER",
        "MIGRATE_TO_SRC_BROKERAGE_LATER",
        "KEEP_ENTRYPOINT_OR_DASHBOARD",
        "COMPATIBILITY_SHIM_CANDIDATE",
        "DELETE_CANDIDATE_AFTER_PROOF",
        "UNSAFE_TO_TOUCH",
    ]
    for tag in required_tags:
        assert tag in combined, f"missing tag: {tag}"

    required_strings = [
        "Useful functionality should be transported into the correct src domain before legacy modules are deleted. Entrypoints, dashboards, quant logic, and risk logic are not automatic deletion candidates; they must be classified by ownership and dependency role.",
        "automation_scheduler remains a decommission target",
        "Math/risk foundation integration comes after migration/deletion cleanup.",
        "AI/LLM integration comes after canonical math/risk/data/evaluation foundations.",
        "No deletion occurred in this phase.",
        "No migration occurred in this phase.",
        "main.py",
        "streamlit_app.py",
        "quant_engine.py",
        "risk_engine.py",
    ]
    for needle in required_strings:
        assert needle in combined, f"missing text: {needle}"

    for forbidden in ["AKIA", "ASIA", "your_real_secret"]:
        assert forbidden not in combined

    # Explicitly verify that the four shell / utility files are not treated as automatic deletion candidates.
    assert "Not an automatic deletion candidate" in combined


def test_audit_documents_preserve_repository_safety_context() -> None:
    main_text = _read(ROOT / "main.py")
    streamlit_text = _read(ROOT / "streamlit_app.py")
    quant_text = _read(ROOT / "quant_engine.py")
    risk_text = _read(ROOT / "risk_engine.py")
    provider_router_text = _read(ROOT / "src" / "providers" / "provider_router.py")
    model_card_text = _read(ROOT / "src" / "api" / "model_card_service.py")
    provider_status_text = _read(ROOT / "src" / "api" / "provider_status_routes.py")

    assert "from src.providers.provider_router import ProviderRouter" in model_card_text
    assert "import automation_scheduler" in provider_status_text
    assert "ProviderRouter" in provider_router_text
    assert "def evaluate_lines_payload" in _read(ROOT / "bet_decision_engine.py")
    assert "def calculate_profit_loss" in _read(ROOT / "bet_log.py")

    # Runtime owners still exist and are not deleted by this audit phase.
    for path in [ROOT / "main.py", ROOT / "streamlit_app.py", ROOT / "quant_engine.py", ROOT / "risk_engine.py"]:
        assert path.exists()

    # The audit itself must not introduce live-network or credential material into the reports.
    report_blob = "\n".join(_read(path) for path in REPORTS)
    assert re.search(r"AKIA[0-9A-Z]{16}", report_blob) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report_blob) is None
    assert "your_real_secret" not in report_blob

    # The audit should mention the current state of the shells and utility layers.
    for token in ["KEEP_ENTRYPOINT_OR_DASHBOARD", "MIGRATE_TO_SRC_CORE", "MIGRATE_TO_SRC_SERVICES", "MIGRATE_TO_SRC_CONNECTORS"]:
        assert token in report_blob

    # The root-level utility text should still look like utility code, not deletion proof.
    assert "FastAPI" in main_text
    assert "streamlit" in streamlit_text.lower()
    assert "kelly" in quant_text.lower()
    assert "risk" in risk_text.lower()

