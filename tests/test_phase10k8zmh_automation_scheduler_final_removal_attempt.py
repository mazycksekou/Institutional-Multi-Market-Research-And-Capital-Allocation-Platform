from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

DOC_FILES = [
    ROOT / "PHASE10K8ZMN_COMPATIBILITY_SHELL_ELIMINATION.md",
    ROOT / "RUNTIME_ZERO_IMPORT_PROOF_AFTER_10K8ZMN.md",
    ROOT / "TEST_ZERO_IMPORT_PROOF_AFTER_10K8ZMN.md",
    ROOT / "INTERNAL_ZERO_IMPORT_PROOF_AFTER_10K8ZMN.md",
    ROOT / "FINAL_DELETE_PROOF_AFTER_10K8ZMN.md",
]

CANONICAL_IMPORTS = [
    "src.services.streamlit_dashboard_facade",
    "src.services.automation_scheduler_facade",
    "src.market_intelligence.manifold",
    "src.data.historical_odds",
    "src.backtesting.engine",
    "src.research.history",
    "src.services.runtime_shared",
    "src.analytics.performance",
    "src.brokerage.readiness",
    "src.ai.readiness",
]


def _scan_imports() -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {
        "runtime": {"count": 0, "files": set()},
        "test": {"count": 0, "files": set()},
        "scripts": {"count": 0, "files": set()},
        "internal": {"count": 0, "files": set()},
    }
    excluded = {".git", ".pytest_cache", ".venv", "venv", "__pycache__", ".aider.tags.cache.v4"}

    for path in ROOT.rglob("*.py"):
        if any(part in excluded for part in path.parts):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:  # pragma: no cover - repository should already parse cleanly
            raise AssertionError(f"Unexpected syntax error in {path}: {exc}") from exc
        if "tests" in path.parts:
            scope = "test"
        elif "scripts" in path.parts:
            scope = "scripts"
        elif "automation_scheduler" in path.parts:
            scope = "internal"
        else:
            scope = "runtime"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name == "automation_scheduler" or name.startswith("automation_scheduler."):
                        summary[scope]["count"] = int(summary[scope]["count"]) + 1
                        summary[scope]["files"].add(path)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "automation_scheduler" or module.startswith("automation_scheduler."):
                    summary[scope]["count"] = int(summary[scope]["count"]) + 1
                    summary[scope]["files"].add(path)
                elif scope == "internal" and node.level and node.level > 0:
                    summary["internal"]["count"] = int(summary["internal"]["count"]) + 1
                    summary["internal"]["files"].add(path)

    return summary


def test_phase10k8zmh_automation_scheduler_final_removal_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    for doc in DOC_FILES:
        assert doc.exists(), doc

    combined_docs = "\n".join(doc.read_text(encoding="utf-8", errors="ignore") for doc in DOC_FILES)
    for phrase in [
        "compatibility shell removed",
        "runtime imports: 0",
        "test imports: 0",
        "internal imports: 0",
        "canonical ownership remains under src/*",
        "automation_scheduler directory removed",
    ]:
        assert phrase in combined_docs.lower(), phrase

    summary = _scan_imports()
    assert summary["runtime"]["count"] == 0
    assert len(summary["runtime"]["files"]) == 0
    assert summary["test"]["count"] == 0
    assert len(summary["test"]["files"]) == 0
    assert summary["scripts"]["count"] == 0
    assert summary["internal"]["count"] == 0
    assert len(summary["internal"]["files"]) == 0

    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    for module_name in CANONICAL_IMPORTS:
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

    assert not (ROOT / "automation_scheduler").exists()
    assert (ROOT / "src" / "automation_scheduler_legacy").is_dir()
