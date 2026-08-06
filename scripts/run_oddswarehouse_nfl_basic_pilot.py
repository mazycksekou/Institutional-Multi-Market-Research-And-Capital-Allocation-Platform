from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.oddswarehouse_nfl_basic_ingest import run_oddswarehouse_nfl_basic_pilot


def _default_desktop_file(filename: str) -> Path:
    return Path.home() / "Desktop" / filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the controlled OddsWarehouse NFL Basic bounded ingest.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=_default_desktop_file("NFL_Basic sample provider oddwarehouse 1.xlsx"),
        help="Path to the approved OddsWarehouse XLSX source or canonical 26-column CSV source.",
    )
    parser.add_argument(
        "--companion-evidence",
        type=Path,
        default=None,
        help="Optional path to the malformed companion CSV evidence file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Deterministically ingest only the first N source rows.",
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=None,
        help="Legacy alias for --source.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Legacy alias for --companion-evidence.",
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Optional SQLite storage path override.",
    )
    parser.add_argument(
        "--lakehouse-root",
        type=Path,
        default=None,
        help="Optional lakehouse root override.",
    )
    parser.add_argument(
        "--bronze-raw-root",
        type=Path,
        default=None,
        help="Optional Bronze/raw root override.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = args.workbook or args.source
    companion_evidence = args.companion_evidence or args.csv
    report = run_oddswarehouse_nfl_basic_pilot(
        source,
        companion_evidence,
        storage_path=args.storage_path,
        lakehouse_root=args.lakehouse_root,
        bronze_raw_root=args.bronze_raw_root,
        limit=args.limit,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
