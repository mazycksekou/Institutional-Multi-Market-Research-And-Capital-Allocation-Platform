from __future__ import annotations

from scripts.check_architecture import collect_architecture_report


def test_no_src_python_files_are_ignored_by_git() -> None:
    report = collect_architecture_report()
    assert report["ignored_source_files"] == []
