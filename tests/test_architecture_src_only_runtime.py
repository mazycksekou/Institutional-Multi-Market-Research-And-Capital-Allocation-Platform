from __future__ import annotations

from scripts.check_architecture import ALLOWED_ROOT_PYTHON, collect_architecture_report


def test_root_runtime_python_files_are_only_approved_entrypoints() -> None:
    report = collect_architecture_report()
    assert report["root_python_files"] == sorted(ALLOWED_ROOT_PYTHON)
    assert report["non_src_runtime_python_files"] == sorted(ALLOWED_ROOT_PYTHON)
