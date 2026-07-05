from __future__ import annotations

from pathlib import Path

from scripts.check_architecture import collect_architecture_report


def test_no_legacy_executable_import_refs_remain() -> None:
    report = collect_architecture_report()
    assert report["legacy_import_issues"] == []
    assert report["archived_tests"], "Historical migration-proof tests should be archived, not active."
    assert not Path("src/services/automation_scheduler_facade.py").exists()
    assert Path("src/services/runtime_facade.py").is_file()
