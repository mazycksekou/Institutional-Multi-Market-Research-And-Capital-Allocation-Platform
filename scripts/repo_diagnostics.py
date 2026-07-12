from __future__ import annotations

import argparse
import ast
import json
import platform
import shlex
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from scripts import run_quality_gates
from scripts.check_architecture import collect_architecture_report
from scripts.check_openapi_contract import collect_openapi_report
from scripts.check_root_markdown import find_root_markdown
from src.providers.registry import get_provider_registry
from src.services.repo_inventory import module_name_for_path


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
API_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace", "api_route"}


def _is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_DIRS)


def _git_value(args: list[str], *, timeout: int = 10) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except Exception:
        return None
    output = (completed.stdout or completed.stderr or "").strip()
    return output if completed.returncode == 0 and output else None


def _git_lines(args: list[str], *, timeout: int = 10) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]


def _git_state() -> dict[str, Any]:
    git_dir = _git_value(["rev-parse", "--git-dir"])
    branch = _git_value(["branch", "--show-current"]) or _git_value(["rev-parse", "--abbrev-ref", "HEAD"]) or "detached"
    head = _git_value(["rev-parse", "HEAD"])
    upstream = _git_value(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    counts = _git_value(["rev-list", "--left-right", "--count", "HEAD...@{u}"]) if upstream else None
    ahead = behind = None
    if counts:
        parts = counts.split()
        if len(parts) >= 2:
            try:
                ahead = int(parts[0])
                behind = int(parts[1])
            except ValueError:
                ahead = behind = None
    staged_files = _git_lines(["diff", "--cached", "--name-only", "--diff-filter=ACMRDTUXB"])
    modified_files = _git_lines(["diff", "--name-only", "--diff-filter=ACMRDTUXB"])
    untracked_files = _git_lines(["ls-files", "--others", "--exclude-standard"])
    status_summary = _git_value(["status", "--short", "--branch"]) or ""
    available = git_dir is not None
    return {
        "available": available,
        "status": "available" if available else "unavailable",
        "branch": branch if available else None,
        "head": head,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "staged_files": staged_files,
        "modified_files": modified_files,
        "untracked_files": untracked_files,
        "clean": None if not available else not modified_files and not untracked_files,
        "status_summary": status_summary,
    }


def _relative_files(base: Path, *, suffixes: set[str] | None = None) -> list[Path]:
    if not base.exists():
        return []
    files = [path for path in base.rglob("*") if path.is_file() and not _is_excluded(path)]
    if suffixes is not None:
        files = [path for path in files if path.suffix in suffixes]
    return sorted(files)


def _collect_workflow_inventory(root: Path = ROOT) -> dict[str, Any]:
    workflows_dir = root / ".github" / "workflows"
    files = []
    for path in sorted(list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))):
        if not path.is_file() or _is_excluded(path):
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "name": None,
                    "jobs": [],
                    "branches": [],
                    "events": [],
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        on_value = data.get("on")
        if on_value is None and True in data:
            on_value = data[True]
        events, branches = _workflow_events_and_branches(on_value)
        jobs = sorted(data.get("jobs", {}).keys()) if isinstance(data.get("jobs"), dict) else []
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "name": data.get("name"),
                "jobs": jobs,
                "branches": branches,
                "events": events,
            }
        )
    return {"root": str(root), "count": len(files), "files": files}


def _workflow_events_and_branches(on_value: Any) -> tuple[list[str], list[str]]:
    events: set[str] = set()
    branches: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, str):
            events.add(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                events.add(str(key))
                if key in {"push", "pull_request", "workflow_dispatch"}:
                    if isinstance(item, dict):
                        branch_list = item.get("branches") or []
                        if isinstance(branch_list, list):
                            for branch in branch_list:
                                branches.add(str(branch))
                        elif isinstance(branch_list, str):
                            branches.add(branch_list)

    walk(on_value)
    return sorted(events), sorted(branches)


def _collect_script_inventory(root: Path = ROOT) -> dict[str, Any]:
    scripts_dir = root / "scripts"
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "suffix": path.suffix or "",
        }
        for path in _relative_files(scripts_dir)
    ]
    return {"root": str(root), "count": len(files), "files": files}


def _route_from_decorator(decorator: ast.expr, *, file_path: Path, function_name: str, root: Path) -> dict[str, Any] | None:
    if not isinstance(decorator, ast.Call):
        return None
    func = decorator.func
    if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name) or func.value.id != "app":
        return None
    method = func.attr.lower()
    if method not in API_METHODS:
        return None
    path = None
    if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
        path = decorator.args[0].value
    operation_id = None
    include_in_schema = True
    for keyword in decorator.keywords:
        if keyword.arg == "operation_id" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            operation_id = keyword.value.value
        elif keyword.arg == "include_in_schema" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, bool):
            include_in_schema = keyword.value.value
    if path is None:
        return None
    return {
        "path": path,
        "method": method.upper(),
        "operation_id": operation_id,
        "function": function_name,
        "file": file_path.relative_to(root).as_posix(),
        "include_in_schema": include_in_schema,
    }


def _collect_api_route_inventory(root: Path = ROOT) -> dict[str, Any]:
    api_dir = root / "src" / "api"
    routes: list[dict[str, Any]] = []
    for path in _relative_files(api_dir, suffixes={".py"}):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                route = _route_from_decorator(decorator, file_path=path, function_name=node.name, root=root)
                if route is not None:
                    routes.append(route)
    routes.sort(key=lambda item: (item["path"], item["method"], item["file"], item["function"]))
    method_counts = Counter(route["method"] for route in routes)
    return {
        "root": str(root),
        "count": len(routes),
        "method_counts": dict(sorted(method_counts.items())),
        "routes": routes,
    }


def _layer_for_path(rel: str) -> str:
    if rel.startswith("src/api/"):
        return "src.api"
    if rel.startswith("src/services/"):
        return "src.services"
    if rel.startswith("src/providers/"):
        return "src.providers"
    if rel.startswith("src/core/"):
        return "src.core"
    if rel.startswith("src/analytics/"):
        return "src.analytics"
    if rel.startswith("src/research/"):
        return "src.research"
    if rel.startswith("src/data/"):
        return "src.data"
    if rel.startswith("src/backtesting/"):
        return "src.backtesting"
    if rel.startswith("tests/"):
        return "tests"
    if rel.startswith("scripts/"):
        return "scripts"
    if rel.startswith("src/"):
        return "src.other"
    return "root"


def _collect_module_inventory(root: Path = ROOT) -> dict[str, Any]:
    files = _relative_files(root, suffixes={".py"})
    layers: dict[str, list[str]] = defaultdict(list)
    for path in files:
        rel = path.relative_to(root).as_posix()
        layers[_layer_for_path(rel)].append(module_name_for_path(path, root))
    layer_items = [
        {
            "layer": layer,
            "count": len(modules),
            "modules": sorted(modules),
        }
        for layer, modules in sorted(layers.items())
    ]
    return {"root": str(root), "count": len(files), "layers": layer_items}


def _collect_test_inventory(root: Path = ROOT) -> dict[str, Any]:
    tests_dir = root / "tests"
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "family": path.stem.split("_", 2)[1] if path.stem.startswith("test_") and "_" in path.stem[5:] else path.stem,
        }
        for path in _relative_files(tests_dir, suffixes={".py"})
    ]
    family_counts = Counter(item["family"] for item in files)
    return {
        "root": str(root),
        "count": len(files),
        "family_counts": dict(sorted(family_counts.items())),
        "files": files,
    }


def _collect_provider_inventory() -> dict[str, Any]:
    registry = get_provider_registry()
    providers = [
        {
            "provider_id": provider_id,
            "provider_type": data.get("provider_type"),
            "provider_name": data.get("provider_name"),
            "enabled": bool(data.get("enabled")),
            "live_calls_enabled": bool(data.get("live_calls_enabled")),
            "credential_status": data.get("credential_status"),
        }
        for provider_id, data in sorted(registry.items())
    ]
    type_counts = Counter(provider["provider_type"] for provider in providers)
    return {
        "count": len(providers),
        "type_counts": dict(sorted(type_counts.items())),
        "providers": providers,
    }


def _display_value(value: Any, default: str = "n/a") -> str:
    return default if value in {None, ""} else str(value)


def _normalize_command(command: Iterable[str]) -> str:
    parts = [str(part) for part in command]
    if parts and parts[0] == sys.executable:
        parts[0] = "python"
    return shlex.join(parts)


def _collect_quality_gates() -> dict[str, Any]:
    validation_commands = [
        _normalize_command(command)
        for command, _needs_pycache_prefix in run_quality_gates._validation_commands()  # noqa: SLF001
    ]
    return {
        "canonical_local_command": "./.venv/bin/python scripts/run_quality_gates.py --install",
        "workflow_command": "python scripts/run_quality_gates.py --install",
        "validation_commands": validation_commands,
    }


def _repository_health(
    *,
    git: dict[str, Any],
    workflows: dict[str, Any],
    scripts: dict[str, Any],
    routes: dict[str, Any],
    tests: dict[str, Any],
    modules: dict[str, Any],
    providers: dict[str, Any],
) -> dict[str, Any]:
    root_markdown_offenders = [path.relative_to(ROOT).as_posix() for path in find_root_markdown(ROOT)]
    openapi = collect_openapi_report(ROOT)
    architecture = collect_architecture_report(ROOT)
    issues: list[str] = []
    if not git.get("available"):
        issues.append("git metadata unavailable")
    elif not git["clean"]:
        issues.append("git working tree is not clean")
    if root_markdown_offenders:
        issues.append("root markdown contains unmanaged files")
    if not bool(openapi.get("ok")):
        issues.append("openapi contract has errors")
    if architecture.get("root_markdown_offenders") or architecture.get("ignored_source_files") or architecture.get("legacy_import_issues"):
        issues.append("architecture check has violations")
    if not workflows["count"]:
        issues.append("no workflows discovered")
    if not scripts["count"]:
        issues.append("no scripts discovered")
    if not routes["count"]:
        issues.append("no API routes discovered")
    if not tests["count"]:
        issues.append("no tests discovered")
    if not modules["count"]:
        issues.append("no modules discovered")
    if not providers["count"]:
        issues.append("no providers discovered")
    status = "ok" if not issues else "warn"
    return {
        "status": status,
        "ok": not issues,
        "issues": issues,
        "git_available": bool(git.get("available")),
        "git_clean": git["clean"],
        "root_markdown": {
            "ok": not root_markdown_offenders,
            "offenders": root_markdown_offenders,
        },
        "openapi": {
            "ok": bool(openapi.get("ok")),
            "path_count": openapi.get("path_count"),
            "operation_count": openapi.get("operation_count"),
        },
        "architecture": {
            "ok": not (architecture.get("root_markdown_offenders") or architecture.get("ignored_source_files") or architecture.get("legacy_import_issues")),
            "root_markdown_offenders": len(architecture.get("root_markdown_offenders") or []),
            "ignored_source_files": len(architecture.get("ignored_source_files") or []),
            "legacy_import_issues": len(architecture.get("legacy_import_issues") or []),
        },
    }


def collect_repository_diagnostics(root: Path = ROOT) -> dict[str, Any]:
    git = _git_state()
    workflows = _collect_workflow_inventory(root)
    scripts = _collect_script_inventory(root)
    routes = _collect_api_route_inventory(root)
    tests = _collect_test_inventory(root)
    modules = _collect_module_inventory(root)
    providers = _collect_provider_inventory()
    quality_gates = _collect_quality_gates()
    health = _repository_health(
        git=git,
        workflows=workflows,
        scripts=scripts,
        routes=routes,
        tests=tests,
        modules=modules,
        providers=providers,
    )
    python_info = {
        "executable": sys.executable,
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "venv": {
            "active": sys.prefix != sys.base_prefix,
            "path": sys.prefix,
            "base_prefix": sys.base_prefix,
            "prefix": sys.prefix,
        },
    }
    return {
        "root": str(root),
        "git": git,
        "python": python_info,
        "repository_health": health,
        "workflow_inventory": workflows,
        "script_inventory": scripts,
        "api_route_inventory": routes,
        "test_inventory": tests,
        "module_inventory": modules,
        "provider_inventory": providers,
        "quality_gates": quality_gates,
    }


def _format_list(items: list[str], *, limit: int = 8) -> str:
    if not items:
        return "none"
    shown = items[:limit]
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(shown) + suffix


def render_repository_diagnostics_text(report: dict[str, Any]) -> str:
    git = report["git"]
    python_info = report["python"]
    health = report["repository_health"]
    workflows = report["workflow_inventory"]
    scripts = report["script_inventory"]
    routes = report["api_route_inventory"]
    tests = report["test_inventory"]
    modules = report["module_inventory"]
    providers = report["provider_inventory"]
    gates = report["quality_gates"]
    lines = [
        "repository diagnostics",
        f"git: available={git['available']} branch={_display_value(git['branch'])} head={_display_value(git['head'])} clean={_display_value(git['clean'])} upstream={_display_value(git.get('upstream'))}",
        f"python: executable={python_info['executable']} version={python_info['version']} venv_active={python_info['venv']['active']} venv_prefix={python_info['venv']['prefix']}",
        f"health: status={health['status']} ok={health['ok']} issues={len(health['issues'])}",
        f"workflow inventory: count={workflows['count']} files={_format_list([item['path'] for item in workflows['files']])}",
        f"script inventory: count={scripts['count']} files={_format_list([item['path'] for item in scripts['files']])}",
        f"api route inventory: count={routes['count']} methods={dict(routes['method_counts'])}",
        f"test inventory: count={tests['count']} families={_format_list([f'{family}={count}' for family, count in tests['family_counts'].items()])}",
        "module inventory by layer:",
    ]
    for layer in modules["layers"]:
        lines.append(f"  - {layer['layer']}: {layer['count']}")
    lines.extend(
        [
            f"provider inventory: count={providers['count']} types={dict(providers['type_counts'])}",
            "configured quality gates:",
            f"  canonical_local_command: {gates['canonical_local_command']}",
            f"  workflow_command: {gates['workflow_command']}",
        ]
    )
    for command in gates["validation_commands"]:
        lines.append(f"  - {command}")
    if health["issues"]:
        lines.append("repository health issues:")
        for issue in health["issues"]:
            lines.append(f"  - {issue}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report read-only repository diagnostics.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    report = collect_repository_diagnostics(ROOT)
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_repository_diagnostics_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
