from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_TEST = ROOT / "tests" / "test_streamlit_dashboard_data.py"
LEGACY_PKG = "automation" + "_" + "scheduler"
LEGACY_ROOT = ROOT / LEGACY_PKG

DOC_FILES = [
    ROOT / "PHASE10K8ZMI_STREAMLIT_DASHBOARD_TEST_IMPORT_REDIRECTION.md",
    ROOT / "STREAMLIT_DASHBOARD_TEST_IMPORTS_BEFORE_10K8ZMI.md",
    ROOT / "STREAMLIT_DASHBOARD_TEST_REDIRECTION_MAP_AFTER_10K8ZMI.md",
    ROOT / "STREAMLIT_DASHBOARD_TEST_ZERO_IMPORT_PROOF_AFTER_10K8ZMI.md",
    ROOT / "NEXT_AUTOMATION_SCHEDULER_TEST_IMPORT_BATCH_AFTER_10K8ZMI.md",
]

CANONICAL_IMPORTS = [
    "src.services.streamlit_dashboard_facade",
    "src.backtesting.strategy_profiles",
    "src.data.field_catalog",
    "src.data.historical_odds",
    "src.data.line_movement",
    "src.data.source_event_links",
    "src.market_intelligence.feature_packs",
    "src.research.feature_control",
    "src.research.history",
    "src.backtesting.dataset_builder",
    "src.backtesting.engine",
    "src.backtesting.historical_bridge",
    "src.services.ops_workflow",
]

RISKY_MODULE_TOKENS = ("broker", "trade", "order", "live", "deployment", "connector")


def _collect_legacy_import_nodes(path: Path) -> list[ast.AST]:
    source = path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(source, filename=str(path))
    offenders: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == LEGACY_PKG or name.startswith(LEGACY_PKG + "."):
                    offenders.append(node)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == LEGACY_PKG or module.startswith(LEGACY_PKG + "."):
                offenders.append(node)
    return offenders


def _scan_repo_import_counts() -> dict[str, tuple[int, int]]:
    excluded = {".git", ".pytest_cache", ".venv", "venv", "__pycache__", ".aider.tags.cache.v4"}
    counts: dict[str, dict[str, object]] = {
        "runtime": {"count": 0, "files": set()},
        "test": {"count": 0, "files": set()},
        "scripts": {"count": 0, "files": set()},
        "internal": {"count": 0, "files": set()},
    }

    for path in ROOT.rglob("*.py"):
        if any(part in excluded for part in path.parts):
            continue

        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(path))
        in_scheduler = LEGACY_PKG in path.parts
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
                    if name == LEGACY_PKG or name.startswith(LEGACY_PKG + "."):
                        counts[scope]["count"] = int(counts[scope]["count"]) + 1
                        counts[scope]["files"].add(path)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == LEGACY_PKG or module.startswith(LEGACY_PKG + "."):
                    counts[scope]["count"] = int(counts[scope]["count"]) + 1
                    counts[scope]["files"].add(path)
                elif in_scheduler and node.level and node.level > 0:
                    counts["internal"]["count"] = int(counts["internal"]["count"]) + 1
                    counts["internal"]["files"].add(path)

    return {
        scope: (int(payload["count"]), len(payload["files"]))
        for scope, payload in counts.items()
    }


def test_phase10k8zmi_streamlit_dashboard_test_import_redirection() -> None:
    for doc in DOC_FILES:
        assert doc.exists(), doc

    source = TARGET_TEST.read_text(encoding="utf-8", errors="ignore")
    assert LEGACY_PKG not in source

    offenders = _collect_legacy_import_nodes(TARGET_TEST)
    assert offenders == []

    counts = _scan_repo_import_counts()
    assert counts["runtime"] == (0, 0)
    assert counts["test"] == (387, 191)
    assert counts["scripts"] == (0, 0)
    assert counts["internal"] == (745, 262)

    before_doc = (ROOT / "STREAMLIT_DASHBOARD_TEST_IMPORTS_BEFORE_10K8ZMI.md").read_text(encoding="utf-8")
    assert "42" in before_doc
    assert "524" in before_doc
    assert "198" in before_doc
    assert "745" in before_doc

    map_doc = (ROOT / "STREAMLIT_DASHBOARD_TEST_REDIRECTION_MAP_AFTER_10K8ZMI.md").read_text(encoding="utf-8")
    for needle in (
        "src.services.streamlit_dashboard_facade",
        "src.data.historical_odds",
        "src.data.line_movement",
        "src.research.history",
        "src.services.ops_workflow",
    ):
        assert needle in map_doc

    zero_doc = (ROOT / "STREAMLIT_DASHBOARD_TEST_ZERO_IMPORT_PROOF_AFTER_10K8ZMI.md").read_text(encoding="utf-8")
    assert "0" in zero_doc
    assert "482" in zero_doc
    assert "197" in zero_doc
    assert "745" in zero_doc
    assert "262" in zero_doc

    next_doc = (ROOT / "NEXT_AUTOMATION_SCHEDULER_TEST_IMPORT_BATCH_AFTER_10K8ZMI.md").read_text(encoding="utf-8")
    assert "tests/test_baseball_impact_intelligence.py" in next_doc
    assert "17" in next_doc

    for module_name in CANONICAL_IMPORTS:
        imported = importlib.import_module(module_name)
        assert imported.__name__ == module_name
        assert module_name.startswith("src.")
        assert not any(token in module_name for token in RISKY_MODULE_TOKENS)

    assert LEGACY_ROOT.is_dir()
    assert any(LEGACY_ROOT.rglob("*.py"))
