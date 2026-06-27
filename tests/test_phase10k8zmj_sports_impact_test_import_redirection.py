from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PKG = "automation" + "_" + "scheduler"
LEGACY_ROOT = ROOT / LEGACY_PKG

DOC_FILES = [
    ROOT / "PHASE10K8ZMJ_SPORTS_IMPACT_TEST_IMPORT_REDIRECTION.md",
    ROOT / "SPORTS_IMPACT_TEST_IMPORTS_BEFORE_10K8ZMJ.md",
    ROOT / "SPORTS_IMPACT_TEST_REDIRECTION_MAP_AFTER_10K8ZMJ.md",
    ROOT / "SPORTS_IMPACT_TEST_ZERO_IMPORT_PROOF_AFTER_10K8ZMJ.md",
    ROOT / "NEXT_AUTOMATION_SCHEDULER_TEST_IMPORT_BATCH_AFTER_10K8ZMJ.md",
]

TARGET_TESTS = [
    ROOT / "tests" / "test_baseball_impact_intelligence.py",
    ROOT / "tests" / "test_golf_impact_intelligence.py",
    ROOT / "tests" / "test_hockey_impact_intelligence.py",
    ROOT / "tests" / "test_soccer_impact_intelligence.py",
    ROOT / "tests" / "test_combat_impact_intelligence.py",
    ROOT / "tests" / "test_tennis_impact_intelligence.py",
]

CANONICAL_MODULES = [
    "src.market_intelligence.sports",
    "src.market_intelligence.response_compactor",
]

CANONICAL_ATTRS = [
    ("src.market_intelligence.sports", "evaluate_baseball_data_availability"),
    ("src.market_intelligence.sports", "build_golf_impact_diagnostics"),
    ("src.market_intelligence.sports", "evaluate_hockey_goalie_impact"),
    ("src.market_intelligence.sports", "evaluate_soccer_tactical_context"),
    ("src.market_intelligence.sports", "evaluate_combat_striking_impact"),
    ("src.market_intelligence.sports", "evaluate_tennis_serve_impact"),
    ("src.market_intelligence.response_compactor", "compact_baseball_impact_diagnostics_response"),
    ("src.market_intelligence.response_compactor", "redact_and_limit_payload"),
]


def _scan_imports() -> dict[str, tuple[int, int]]:
    counts: dict[str, dict[str, object]] = {
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


def test_phase10k8zmj_sports_impact_test_import_redirection() -> None:
    for doc in DOC_FILES:
        assert doc.exists(), doc

    for path in TARGET_TESTS:
        source = path.read_text(encoding="utf-8", errors="ignore")
        assert LEGACY_PKG not in source, path
        assert _collect_legacy_import_nodes(path) == [], path

    counts = _scan_imports()
    assert counts["runtime"] == (0, 0)
    assert counts["test"] == (387, 191)
    assert counts["scripts"] == (0, 0)
    assert counts["internal"] == (745, 262)

    before_doc = (ROOT / "SPORTS_IMPACT_TEST_IMPORTS_BEFORE_10K8ZMJ.md").read_text(encoding="utf-8")
    assert "95" in before_doc
    assert "482" in before_doc
    assert "197" in before_doc
    assert "745" in before_doc

    map_doc = (ROOT / "SPORTS_IMPACT_TEST_REDIRECTION_MAP_AFTER_10K8ZMJ.md").read_text(encoding="utf-8")
    for needle in (
        "src.market_intelligence.sports",
        "src.market_intelligence.response_compactor",
        "compact_*_impact_diagnostics_response",
        "redact_and_limit_payload",
    ):
        assert needle in map_doc

    zero_doc = (ROOT / "SPORTS_IMPACT_TEST_ZERO_IMPORT_PROOF_AFTER_10K8ZMJ.md").read_text(encoding="utf-8")
    assert "387" in zero_doc
    assert "191" in zero_doc
    assert "745" in zero_doc
    assert "262" in zero_doc

    next_doc = (ROOT / "NEXT_AUTOMATION_SCHEDULER_TEST_IMPORT_BATCH_AFTER_10K8ZMJ.md").read_text(encoding="utf-8")
    assert "tests/test_football_impact_intelligence.py" in next_doc
    assert "11" in next_doc

    for module_name, attr_name in CANONICAL_ATTRS:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name
        attr = getattr(module, attr_name)
        assert callable(attr)
        assert module_name.startswith("src.market_intelligence")

    for module_name in CANONICAL_MODULES:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name

    assert LEGACY_ROOT.is_dir()
    assert any(LEGACY_ROOT.rglob("*.py"))
