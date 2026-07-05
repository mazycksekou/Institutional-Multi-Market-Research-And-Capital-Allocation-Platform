from __future__ import annotations

import scripts.check_architecture as check_architecture
from scripts.check_architecture import collect_architecture_report


def test_no_src_python_files_are_ignored_by_git() -> None:
    report = collect_architecture_report()
    assert report["ignored_source_files"] == []


def test_missing_git_for_ignored_source_scan_reports_cleanly(monkeypatch) -> None:
    def _raise_file_not_found(*_args, **_kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(check_architecture.subprocess, "run", _raise_file_not_found)
    offenders = check_architecture._ignored_source_files()
    assert offenders == [{"path": "<git>", "rule": "git is required for ignored source file validation"}]
