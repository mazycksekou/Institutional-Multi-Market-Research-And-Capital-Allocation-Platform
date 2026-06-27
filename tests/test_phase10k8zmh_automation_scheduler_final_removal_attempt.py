from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_FILES = [
    ROOT / "PHASE10K8ZMH_AUTOMATION_SCHEDULER_FINAL_REMOVAL_ATTEMPT.md",
    ROOT / "AUTOMATION_SCHEDULER_ACTIVE_IMPORT_SCAN_AFTER_10K8ZMH.md",
    ROOT / "AUTOMATION_SCHEDULER_ACTIVE_TEST_SCAN_AFTER_10K8ZMH.md",
    ROOT / "AUTOMATION_SCHEDULER_INTERNAL_IMPORT_SCAN_AFTER_10K8ZMH.md",
    ROOT / "AUTOMATION_SCHEDULER_FINAL_REDIRECTION_MAP_AFTER_10K8ZMH.md",
    ROOT / "AUTOMATION_SCHEDULER_FINAL_DELETE_DECISION_AFTER_10K8ZMH.md",
    ROOT / "AUTOMATION_SCHEDULER_EXACT_BLOCKER_LEDGER_AFTER_10K8ZMH.md",
    ROOT / "NEXT_AUTOMATION_SCHEDULER_BLOCKER_BATCH_AFTER_10K8ZMH.md",
]

RUNTIME_PROOF_FILES = [
    ROOT / "main.py",
    ROOT / "streamlit_app.py",
    ROOT / "src" / "api" / "automation_review_outcomes_routes.py",
    ROOT / "src" / "api" / "provider_status_routes.py",
    ROOT / "src" / "brokerage" / "readiness.py",
    ROOT / "src" / "services" / "execution_service.py",
    ROOT / "src" / "services" / "ledger_service.py",
    ROOT / "src" / "services" / "settlement_service.py",
]

HISTORICAL_PROOF_REFERENCE_FILES = {
    ROOT / "tests" / "test_phase10k8zgz_post_provider_connector_cleanup_freeze.py": [
        "automation_scheduler.sharp_sportsbook_adapter",
        "automation_scheduler.sportsbook_odds_provider",
    ],
}

CANONICAL_IMPORTS = [
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
        lines = source.splitlines()
        in_scheduler = "automation_scheduler" in path.parts
        if "tests" in path.parts:
            scope = "test"
        elif "scripts" in path.parts:
            scope = "scripts"
        elif in_scheduler:
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
                elif in_scheduler and node.level and node.level > 0:
                    summary["internal"]["count"] = int(summary["internal"]["count"]) + 1
                    summary["internal"]["files"].add(path)

    return summary


def _assert_no_direct_scheduler_imports(path: Path) -> None:
    source = path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                not (alias.name == "automation_scheduler" or alias.name.startswith("automation_scheduler."))
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not (module == "automation_scheduler" or module.startswith("automation_scheduler."))


def test_phase10k8zmh_automation_scheduler_final_removal_attempt() -> None:
    for doc in DOC_FILES:
        assert doc.exists(), doc

    summary = _scan_imports()
    assert summary["runtime"]["count"] == 0
    assert len(summary["runtime"]["files"]) == 0
    assert summary["test"]["count"] == 387
    assert len(summary["test"]["files"]) == 191
    assert summary["scripts"]["count"] == 0
    assert summary["internal"]["count"] == 745
    assert len(summary["internal"]["files"]) == 262

    blocker_ledger = (ROOT / "AUTOMATION_SCHEDULER_EXACT_BLOCKER_LEDGER_AFTER_10K8ZMH.md").read_text(encoding="utf-8")
    assert "ACTIVE_RUNTIME_IMPORT`: `0`" in blocker_ledger
    assert "ACTIVE_TEST_IMPORT`: `387`" in blocker_ledger
    assert "INTERNAL_SCHEDULER_IMPORT`: `745`" in blocker_ledger

    delete_decision = (ROOT / "AUTOMATION_SCHEDULER_FINAL_DELETE_DECISION_AFTER_10K8ZMH.md").read_text(encoding="utf-8")
    assert "was **not** deleted" in delete_decision
    assert "387" in delete_decision
    assert "745" in delete_decision

    for path in RUNTIME_PROOF_FILES:
        _assert_no_direct_scheduler_imports(path)

    for path, needles in HISTORICAL_PROOF_REFERENCE_FILES.items():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            assert needle in text, (path, needle)

    kalshi_proof_file = ROOT / "tests" / "test_phase10k8zgy_prediction_market_shell_deletion.py"
    kalshi_text = kalshi_proof_file.read_text(encoding="utf-8", errors="ignore")
    legacy_prefix = "automation_scheduler."
    for module_name in ("kalshi_readonly_adapter", "kalshi_market_provider"):
        importlib_needle = "importlib.import_module('" + legacy_prefix + module_name + "')"
        patch_needle = "patch('" + legacy_prefix + module_name
        assert legacy_prefix + module_name in kalshi_text, (kalshi_proof_file, module_name)
        assert "importlib.import_module" in kalshi_text, kalshi_proof_file
        assert "patch(" in kalshi_text, kalshi_proof_file
        assert "automation_scheduler" in kalshi_text, kalshi_proof_file
        assert importlib_needle in kalshi_text or importlib_needle.replace("'", '"') in kalshi_text
        assert patch_needle in kalshi_text or patch_needle.replace("'", '"') in kalshi_text

    for module_name in CANONICAL_IMPORTS:
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name

    assert (ROOT / "automation_scheduler").is_dir()
