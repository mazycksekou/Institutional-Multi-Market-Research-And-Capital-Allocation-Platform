from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ACCEPTED_BRANCHES = {
    "phase-6-api-slimming",
    "feature/external-research-data-storage",
    "feature/nfl-backtesting",
    "main",
}
DEFAULT_BRANCH = "feature/external-research-data-storage"


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPYCACHEPREFIX", None)
    return env


def _current_branch() -> str | None:
    for env_var in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(env_var, "").strip()
        if value:
            return value

    completed = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    branch = (completed.stdout or completed.stderr or "").strip()
    return branch or None


def _pytest_env() -> dict[str, str]:
    env = _base_env()
    branch = _current_branch()
    if branch not in ACCEPTED_BRANCHES:
        env["GITHUB_HEAD_REF"] = DEFAULT_BRANCH
        env["GITHUB_REF_NAME"] = DEFAULT_BRANCH
    return env


def _render_command(command: Iterable[str]) -> str:
    return shlex.join([str(part) for part in command])


def _run_command(command: list[str], *, env: dict[str, str]) -> int:
    print(_render_command(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=env)
    return completed.returncode


def _validation_commands() -> list[tuple[list[str], bool]]:
    return [
        ([PYTHON, "-m", "pip", "check"], False),
        ([PYTHON, "-m", "compileall", "src", "tests", "scripts"], True),
        ([PYTHON, "scripts/check_root_markdown.py"], False),
        ([PYTHON, "scripts/check_openapi_contract.py", "--output", "text"], False),
        ([PYTHON, "scripts/check_architecture.py", "--output", "text"], False),
        ([PYTHON, "scripts/ops_check.py", "--mode", "local", "--output", "text", "--skip-network"], False),
        ([PYTHON, "-m", "pytest", "-ra"], False),
    ]


def _install_requirements() -> int:
    for requirement in ("requirements.txt", "requirements-dev.txt"):
        command = [PYTHON, "-m", "pip", "install", "-r", requirement]
        code = _run_command(command, env=_base_env())
        if code != 0:
            return code
    return 0


def _run_validation() -> int:
    with tempfile.TemporaryDirectory(prefix="codex_pyc_") as pycache_prefix:
        for command, needs_pycache_prefix in _validation_commands():
            env = _pytest_env() if command[:3] == [PYTHON, "-m", "pytest"] else _base_env()
            if needs_pycache_prefix:
                env["PYTHONPYCACHEPREFIX"] = pycache_prefix
            code = _run_command(command, env=env)
            if code != 0:
                return code
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the repository quality gates.")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install requirements.txt and requirements-dev.txt before running validation.",
    )
    args = parser.parse_args(argv)

    if args.install:
        code = _install_requirements()
        if code != 0:
            return code

    return _run_validation()


if __name__ == "__main__":
    raise SystemExit(main())
