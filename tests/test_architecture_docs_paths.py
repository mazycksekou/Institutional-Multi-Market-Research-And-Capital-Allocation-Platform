from __future__ import annotations

from pathlib import Path

from scripts.check_architecture import collect_architecture_report
from scripts.check_root_markdown import find_root_markdown


def test_root_markdown_policy_is_enforced() -> None:
    assert find_root_markdown() == []
    report = collect_architecture_report()
    assert report["root_markdown_offenders"] == []
    assert Path("README.md").is_file()
