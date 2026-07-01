from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.services.repo_inventory import tracked_python_files


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "inventories" / "orphan_dead_code_inventory.json"
EXPECTED_ZERO_IMPORT_SRC = [
    "src/connectors/feeds/__init__.py",
    "src/connectors/web_scraping/__init__.py",
]


def _load_inventory() -> dict[str, object]:
    assert INVENTORY_PATH.is_file(), "expected repository inventory artifact to exist"
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def test_inventory_matches_tracked_python_files() -> None:
    inventory = _load_inventory()
    tracked = tracked_python_files()
    tracked_paths = sorted(path.relative_to(ROOT).as_posix() for path in tracked)
    inventory_paths = sorted(row["path"] for row in inventory["files"])

    assert inventory["root"] == str(ROOT)
    assert inventory["total_files"] == len(tracked_paths)
    assert len(inventory_paths) == len(tracked_paths)
    assert inventory_paths == tracked_paths


def test_no_unknown_or_truly_dead_candidates_remain() -> None:
    inventory = _load_inventory()
    counts = Counter()
    zero_import_src = []

    for row in inventory["files"]:
        for classification in row["classification"]:
            counts[classification] += 1

        if row["path"].startswith("src/") and all(
            row[key] == 0
            for key in (
                "runtime_importer_count",
                "test_importer_count",
                "script_importer_count",
                "internal_importer_count",
            )
        ):
            zero_import_src.append(row["path"])

    assert counts["UNKNOWN"] == 0
    assert counts["TRULY_DEAD"] == 0
    assert sorted(zero_import_src) == EXPECTED_ZERO_IMPORT_SRC


def test_retired_scheduler_packages_are_absent() -> None:
    assert not (ROOT / "automation_scheduler").exists()
    assert not (ROOT / "src" / "automation_scheduler_legacy").exists()
