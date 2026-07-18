from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.oddswarehouse_nfl_basic_ingest import run_oddswarehouse_nfl_basic_pilot


def _default_desktop_file(filename: str) -> Path:
    return Path.home() / "Desktop" / filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the controlled OddsWarehouse NFL Basic 2009 pilot ingest.",
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=_default_desktop_file("NFL_Basic sample provider oddwarehouse 1.xlsx"),
        help="Path to the authoritative OddsWarehouse workbook.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=_default_desktop_file("NFL_Basic sample provider oddwarehouse.csv"),
        help="Path to the accompanying malformed CSV evidence file.",
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
    report = run_oddswarehouse_nfl_basic_pilot(
        args.workbook,
        args.csv,
        storage_path=args.storage_path,
        lakehouse_root=args.lakehouse_root,
        bronze_raw_root=args.bronze_raw_root,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
