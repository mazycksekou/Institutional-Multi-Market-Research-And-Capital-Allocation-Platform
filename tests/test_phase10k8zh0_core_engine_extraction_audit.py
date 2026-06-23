from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

AUDIT_DOCS = [
    ROOT / "PHASE10K8ZH0_CORE_ENGINE_EXTRACTION_AUDIT.md",
    ROOT / "CORE_ENGINE_FUNCTION_INVENTORY_AFTER_10K8ZH0.md",
    ROOT / "CORE_ENGINE_OWNERSHIP_MAP_AFTER_10K8ZH0.md",
    ROOT / "CORE_ENGINE_DUPLICATION_REPORT_AFTER_10K8ZH0.md",
    ROOT / "CORE_ENGINE_MIGRATION_SEQUENCE_AFTER_10K8ZH0.md",
]

CLASSIFICATION_TAGS = [
    "MIGRATE_TO_SRC_CORE_MATH",
    "MIGRATE_TO_SRC_CORE_PROBABILITY",
    "MIGRATE_TO_SRC_CORE_PRICING",
    "MIGRATE_TO_SRC_CORE_RISK",
    "MIGRATE_TO_SRC_CORE_PORTFOLIO",
    "MIGRATE_TO_SRC_CORE_EXECUTION",
    "MIGRATE_TO_SRC_CORE_GAME_THEORY",
    "MIGRATE_TO_SRC_SERVICES",
    "KEEP_ENTRYPOINT_OR_DASHBOARD",
    "COMPATIBILITY_SHIM_CANDIDATE",
    "DELETE_CANDIDATE_AFTER_PROOF",
    "UNSAFE_TO_TOUCH",
]

SAFE_FILES = [
    "quant_engine.py",
    "risk_engine.py",
    "market_pricing.py",
    "model_probability.py",
    "main.py",
    "streamlit_app.py",
]


def test_audit_docs_exist() -> None:
    for path in AUDIT_DOCS:
        assert path.exists(), path


def test_classification_tags_present() -> None:
    combined = "\n".join(
        p.read_text(encoding="utf-8") for p in AUDIT_DOCS if p.exists()
    )
    for tag in CLASSIFICATION_TAGS:
        assert tag in combined, f"{tag} not found in audit docs"


def test_safe_files_not_automatic_deletion() -> None:
    combined = "\n".join(
        p.read_text(encoding="utf-8") for p in AUDIT_DOCS if p.exists()
    )
    for filename in SAFE_FILES:
        assert filename in combined, f"{filename} not mentioned in audit docs"


def test_no_source_migration_or_deletion() -> None:
    # Ensure none of the audit targets have been moved or deleted
    for mod in ("quant_engine.py", "risk_engine.py", "market_pricing.py",
                "model_probability.py", "bet_decision_engine.py",
                "screenshot_intake.py", "main.py", "streamlit_app.py"):
        assert (ROOT / mod).exists(), f"{mod} was deleted unexpectedly"
