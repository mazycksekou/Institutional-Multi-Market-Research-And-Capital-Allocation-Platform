from __future__ import annotations

import ast
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "build",
    "dist",
}

ENTRYPOINT_TARGETS = {
    "api_server.py": "src.api.server",
    "main.py": "src.api.app",
    "streamlit_app.py": "src.services.streamlit_dashboard_facade",
}

PREFIX_TARGETS = (
    ("authentication_scheduler/", "src.data.line_movement"),
    ("betting_providers/", "src.providers"),
    ("providers/", "src.providers"),
    ("research_engine/", "src.research"),
    ("research/", "src.research"),
    ("math_models/institutional/", "src.analytics.institutional"),
    ("model_governance/", "src.analytics.model_governance"),
)

FILE_TARGETS = {
    "asian_markets.py": "src.market_intelligence.options",
    "bet_decision_engine.py": "src.services.bet_decision_engine",
    "bet_log.py": "src.services.bet_log",
    "config.py": "src.core.settings",
    "full_board_engine.py": "src.services.full_board_engine",
    "logger_setup.py": "src.core.settings",
    "logbook_engine.py": "src.services.logbook_engine",
    "market_pricing.py": "src.core.market_pricing",
    "model_blender.py": "src.services.model_blender",
    "model_probability.py": "src.core.model_probability",
    "multi_sport_model_registry.py": "src.market_intelligence.multi_sport_model_registry",
    "parlay_engine.py": "src.core.pricing",
    "quant_engine.py": "src.core.quant_engine",
    "risk_engine.py": "src.core.risk_engine",
    "screenshot_intake.py": "src.services.screenshot_intake",
}


def is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_DIRS)


def tracked_python_files(root: Path = ROOT) -> list[Path]:
    try:
        output = subprocess.run(
            ["git", "ls-files", "*.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except Exception:
        output = [str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*.py") if path.is_file() and not is_excluded(path)]
    return [path for path in (root / rel for rel in output) if path.is_file() and not is_excluded(path)]


def relpath(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def module_name_for_path(path: Path, root: Path = ROOT) -> str:
    rel = path.relative_to(root)
    if rel.name == "__init__.py":
        return ".".join(rel.parent.parts)
    return ".".join(rel.with_suffix("").parts)


def package_name_for_path(path: Path, root: Path = ROOT) -> str:
    rel = path.relative_to(root)
    if rel.name == "__init__.py":
        return ".".join(rel.parent.parts)
    return ".".join(rel.parent.parts)


def module_candidates_for_path(path: Path, root: Path = ROOT) -> list[str]:
    rel = path.relative_to(root)
    candidates: list[str] = []
    if rel.name == "__init__.py":
        candidates.append(".".join(rel.parent.parts))
    elif rel.suffix == ".py":
        candidates.append(".".join(rel.with_suffix("").parts))
        if rel.parent.parts:
            candidates.append(".".join(rel.parent.parts))
    return [candidate for idx, candidate in enumerate(candidates) if candidate and candidate not in candidates[:idx]]


def _relative_import(importer_rel: str, module: str | None, level: int) -> str | None:
    if level <= 0:
        return module
    importer_parent = Path(importer_rel).parent.parts
    if level > len(importer_parent) + 1:
        return module
    base = list(importer_parent[: len(importer_parent) - max(level - 1, 0)])
    if module:
        base.extend(module.split("."))
    return ".".join(base) if base else module


def _parse_python(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8-sig", errors="replace"))
    except SyntaxError:
        return None


def _literal_strings(node: ast.AST) -> list[str]:
    values: list[str] = []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        values.append(node.value)
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for item in node.elts:
            values.extend(_literal_strings(item))
    return values


def _top_level_docstring(tree: ast.AST | None) -> str:
    if tree is None:
        return ""
    docstring = ast.get_docstring(tree) or ""
    first_line = docstring.strip().splitlines()[0].strip() if docstring.strip() else ""
    return first_line


def _public_symbols(tree: ast.AST | None) -> list[str]:
    if tree is None:
        return []
    symbols: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    symbols.update(_literal_strings(node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
            symbols.update(_literal_strings(node.value) if node.value is not None else [])
    return sorted(symbols)


def _direct_imports(tree: ast.AST | None, importer_rel: str) -> list[str]:
    if tree is None:
        return []
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = _relative_import(importer_rel, node.module, node.level or 0)
            if mod:
                imports.add(mod)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "import_module":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imports.add(str(node.args[0].value))
            elif isinstance(func, ast.Name) and func.id == "import_module":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imports.add(str(node.args[0].value))
    return sorted(imports)


def build_import_index(root: Path = ROOT) -> dict[str, dict[str, list[str]]]:
    index: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for path in tracked_python_files(root):
        if not path.is_file():
            continue
        rel = relpath(path, root)
        category = "runtime"
        if rel.startswith("tests/"):
            category = "test"
        elif rel.startswith("scripts/"):
            category = "script"
        tree = _parse_python(path)
        if tree is None:
            continue
        for module in _direct_imports(tree, rel):
            index[module][category].add(rel)
    return {
        module: {category: sorted(paths) for category, paths in categories.items()}
        for module, categories in index.items()
    }


def _classify_path(rel: str, importers: dict[str, dict[str, list[str]]]) -> list[str]:
    canonical = canonical_target_for_path(rel)
    runtime_count, test_count, script_count, internal_count = importer_counts_for_path(rel, importers)
    categories: list[str] = []
    if rel in ENTRYPOINT_TARGETS:
        categories.append("UNSAFE_TO_TOUCH")
    elif runtime_count == test_count == script_count == internal_count == 0:
        categories.append("DELETE_READY_AFTER_PROOF")
    else:
        if canonical.startswith("src.providers"):
            categories.append("MIGRATE_TO_SRC_SERVICES")
        elif canonical.startswith("src.core"):
            categories.append("MIGRATE_TO_SRC_CORE")
        elif canonical.startswith("src.analytics"):
            categories.append("MIGRATE_TO_SRC_ANALYTICS")
        elif canonical.startswith("src.research"):
            categories.append("MIGRATE_TO_SRC_RESEARCH")
        elif canonical.startswith("src.data"):
            categories.append("MIGRATE_TO_SRC_DATA")
        elif canonical.startswith("src.market_intelligence"):
            categories.append("MIGRATE_TO_SRC_MARKET_INTELLIGENCE")
        elif canonical.startswith("src.services"):
            categories.append("MIGRATE_TO_SRC_SERVICES")
        elif canonical.startswith("src.ai"):
            categories.append("MIGRATE_TO_SRC_AI")
        elif canonical.startswith("src.brokerage"):
            categories.append("MIGRATE_TO_SRC_BROKERAGE")
        else:
            categories.append("COMPATIBILITY_WRAPPER_ONLY")
    if runtime_count:
        categories.append("ACTIVE_RUNTIME_DEPENDENCY")
    if test_count:
        categories.append("ACTIVE_TEST_DEPENDENCY")
    if internal_count:
        categories.append("INTERNAL_LEGACY_DEPENDENCY")
    if not categories:
        categories.append("DOC_OR_HISTORICAL_ONLY")
    return categories


def canonical_target_for_path(rel: str) -> str:
    if rel in ENTRYPOINT_TARGETS:
        return ENTRYPOINT_TARGETS[rel]
    if rel in FILE_TARGETS:
        return FILE_TARGETS[rel]
    for prefix, target in PREFIX_TARGETS:
        if rel.startswith(prefix):
            return target
    if rel.startswith("src/"):
        return ".".join(Path(rel).with_suffix("").parts)
    if "/" in rel:
        parent = rel.rsplit("/", 1)[0]
        return f"src.{parent.replace('/', '.')}"
    stem = Path(rel).stem
    if stem:
        return f"src.{stem}"
    return "src"


def importer_counts_for_path(rel: str, import_index: dict[str, dict[str, list[str]]]) -> tuple[int, int, int, int]:
    targets = module_candidates_for_path(ROOT / rel)
    matched: set[str] = set()
    runtime: set[str] = set()
    test: set[str] = set()
    script: set[str] = set()
    for target in targets:
        categories = import_index.get(target, {})
        for category, bucket in (("runtime", runtime), ("test", test), ("script", script)):
            for importer in categories.get(category, []):
                matched.add(importer)
                bucket.add(importer)
        # include imports against the package root as well
        if "/" in rel or rel.endswith("__init__.py"):
            package_target = target.rsplit(".", 1)[0] if "." in target else target
            categories = import_index.get(package_target, {})
            for category, bucket in (("runtime", runtime), ("test", test), ("script", script)):
                for importer in categories.get(category, []):
                    matched.add(importer)
                    bucket.add(importer)
    internal = {
        importer
        for importer in matched
        if rel.startswith("src/") and importer.startswith(rel.rsplit("/", 1)[0] + "/")
    }
    return len(runtime), len(test), len(script), len(internal)


def build_inventory_report(paths: Sequence[Path], root: Path = ROOT) -> dict[str, Any]:
    import_index = build_import_index(root)
    items: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = relpath(path, root)
        tree = _parse_python(path)
        docstring = _top_level_docstring(tree)
        direct_imports = _direct_imports(tree, rel)
        public_symbols = _public_symbols(tree)
        runtime_count, test_count, script_count, internal_count = importer_counts_for_path(rel, import_index)
        canonical = canonical_target_for_path(rel)
        classification = _classify_path(rel, import_index)
        items.append(
            {
                "path": rel,
                "module_candidates": module_candidates_for_path(path, root),
                "public_symbols": public_symbols,
                "responsibility": docstring or _fallback_responsibility(rel, canonical),
                "imports": direct_imports,
                "runtime_callers": import_index.get(module_candidates_for_path(path, root)[0], {}).get("runtime", []) if module_candidates_for_path(path, root) else [],
                "test_callers": import_index.get(module_candidates_for_path(path, root)[0], {}).get("test", []) if module_candidates_for_path(path, root) else [],
                "internal_legacy_callers": [],
                "canonical_target": canonical,
                "deletion_risk": _deletion_risk(runtime_count, test_count, script_count, internal_count, rel),
                "migration_decision": _migration_decision(classification),
                "classification": classification,
                "runtime_importer_count": runtime_count,
                "test_importer_count": test_count,
                "script_importer_count": script_count,
                "internal_importer_count": internal_count,
            }
        )
    return {
        "root": str(root),
        "input_count": len(paths),
        "files": items,
    }


def _fallback_responsibility(rel: str, canonical: str) -> str:
    if rel in ENTRYPOINT_TARGETS:
        return "Application entrypoint"
    if rel.startswith("tests/"):
        return "Test module"
    if rel.startswith("scripts/"):
        return "Maintenance script"
    if rel.endswith("__init__.py"):
        return "Package namespace"
    if "config" in rel:
        return "Environment/configuration helper"
    if "logger" in rel:
        return "Logging helper"
    if "alias" in rel or "provider" in rel:
        return f"Compatibility shim for {canonical}"
    return f"Legacy module targeting {canonical}"


def _deletion_risk(runtime_count: int, test_count: int, script_count: int, internal_count: int, rel: str) -> str:
    if rel in ENTRYPOINT_TARGETS:
        return "high"
    if runtime_count or test_count:
        return "high"
    if script_count or internal_count:
        return "medium"
    return "low"


def _migration_decision(classification: Sequence[str]) -> str:
    if "DELETE_READY_AFTER_PROOF" in classification:
        return "delete_after_proof"
    if "UNSAFE_TO_TOUCH" in classification:
        return "preserve"
    if any(item.startswith("MIGRATE_TO_SRC_") for item in classification):
        return "migrate"
    return "review"


def build_import_scan_report(paths: Sequence[Path], root: Path = ROOT) -> dict[str, Any]:
    import_index = build_import_index(root)
    rows = []
    for path in paths:
        if not path.is_file():
            continue
        rel = relpath(path, root)
        runtime_count, test_count, script_count, internal_count = importer_counts_for_path(rel, import_index)
        rows.append(
            {
                "path": rel,
                "module_candidates": module_candidates_for_path(path, root),
                "runtime_importer_count": runtime_count,
                "test_importer_count": test_count,
                "script_importer_count": script_count,
                "internal_importer_count": internal_count,
                "runtime_importers": sorted(set(import_index.get(module_candidates_for_path(path, root)[0], {}).get("runtime", []))) if module_candidates_for_path(path, root) else [],
                "test_importers": sorted(set(import_index.get(module_candidates_for_path(path, root)[0], {}).get("test", []))) if module_candidates_for_path(path, root) else [],
                "script_importers": sorted(set(import_index.get(module_candidates_for_path(path, root)[0], {}).get("script", []))) if module_candidates_for_path(path, root) else [],
                "canonical_target": canonical_target_for_path(rel),
            }
        )
    return {
        "root": str(root),
        "input_count": len(paths),
        "files": rows,
    }
