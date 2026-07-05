from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_MARKDOWN = {"README.md"}


def find_root_markdown(root: Path = ROOT) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".md"
        and path.name not in ALLOWED_ROOT_MARKDOWN
    )


def recommended_destination(path: Path) -> str:
    name = path.name.upper()
    if "DISCOVERY" in name or name.startswith("PHASE2_"):
        return "docs/discovery/"
    if "CONTRACT" in name:
        return "docs/contracts/"
    if "CATALOG" in name:
        return "docs/catalogs/"
    if "MATRIX" in name:
        return "docs/reports/matrices/"
    if "GAP" in name:
        return "docs/reports/gap_analysis/"
    if "SUMMARY" in name:
        return "docs/summaries/"
    if "ARCHITECTURE" in name or "OWNERSHIP" in name:
        return "docs/architecture/"
    if "CHECKPOINT" in name:
        return "docs/reports/checkpoints/"
    if "PROOF" in name:
        return "docs/reports/proofs/"
    if "AUDIT" in name:
        return "docs/reports/audits/"
    if "MIGRATION" in name:
        return "docs/reports/migrations/"
    if "INVENTORY" in name:
        return "docs/reports/inventories/"
    if "REPORT" in name or "SCAN" in name or "MAP" in name or "REDIRECTION" in name or "DELETE" in name or "READINESS" in name or "DECISION" in name or "PLAN" in name or "STATUS" in name or "QUEUE" in name or "BATCH" in name:
        return "docs/archive/historical_reports/"
    return "docs/archive/historical_reports/"


def main(argv: list[str] | None = None) -> int:
    offenders = find_root_markdown(ROOT)
    if not offenders:
        print("root_markdown: ok")
        print("allowed: README.md")
        return 0

    print("root_markdown: fail")
    print("allowed: README.md")
    for path in offenders:
        print(f"- {path.name} -> {recommended_destination(path)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
