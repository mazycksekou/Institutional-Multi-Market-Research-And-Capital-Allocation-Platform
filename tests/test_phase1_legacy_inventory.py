from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT / "src" / "automation_scheduler_legacy"
DOCS = [
    ROOT / "PHASE1_LEGACY_INVENTORY.md",
    ROOT / "PHASE1_CLASSIFICATION.md",
    ROOT / "PHASE1_DELETE_LIST.md",
    ROOT / "PHASE1_IMPORT_GRAPH.md",
]


def _read_json(path: Path) -> dict:
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def _legacy_python_files() -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in LEGACY_ROOT.rglob("*.py"))


def _run_ops_check(mode: str, input_path: Path, output_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/ops_check.py",
            "--mode",
            mode,
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
    )


def test_phase1_legacy_inventory_covers_every_legacy_python_file(tmp_path: Path) -> None:
    for doc in DOCS:
        assert doc.is_file(), doc

    assert LEGACY_ROOT.is_dir()
    assert not (ROOT / "automation_scheduler").exists()
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == "phase-6-api-slimming"

    legacy_files = _legacy_python_files()
    paths_file = tmp_path / "legacy_paths.txt"
    paths_file.write_text("\n".join(legacy_files) + "\n", encoding="utf-8")
    inventory_json = tmp_path / "legacy_inventory.json"
    import_scan_json = tmp_path / "legacy_import_scan.json"

    _run_ops_check("inventory", paths_file, inventory_json)
    _run_ops_check("import-scan", paths_file, import_scan_json)

    inventory = _read_json(inventory_json)
    import_scan = _read_json(import_scan_json)

    assert sorted(row["path"] for row in inventory["files"]) == legacy_files
    assert sorted(row["path"] for row in import_scan["files"]) == legacy_files

    for row in inventory["files"]:
        assert row["path"].startswith("src/automation_scheduler_legacy/")
        assert row["classification"]
        assert row["canonical_target"].startswith("src.")
        assert row["deletion_risk"] in {"low", "medium", "high"}
        assert row["migration_decision"]
        assert row["public_symbols"] is not None
        assert row["imports"] is not None
        assert row["runtime_callers"] is not None
        assert row["test_callers"] is not None
        assert row["internal_legacy_callers"] is not None

    for row in import_scan["files"]:
        assert row["path"].startswith("src/automation_scheduler_legacy/")
        assert row["canonical_target"].startswith("src.")

    assert len(inventory["files"]) == len(legacy_files)
    assert len(import_scan["files"]) == len(legacy_files)
