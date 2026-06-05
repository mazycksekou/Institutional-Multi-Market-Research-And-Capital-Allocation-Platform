from __future__ import annotations

import argparse
import json

from .nfl_mlb_active_discovery import build_schema_expansion_report, write_schema_expansion_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_schema_expansion_report(sport="mlb", base_data_dir=args.base_data_dir)
    paths = write_schema_expansion_report(report, sport="mlb") if args.persist else {}
    print(json.dumps({**{k: report.get(k) for k in ("ok", "status", "sport", "existing_fields_total", "existing_fields_populated_before", "existing_fields_populated_after", "new_fields_created_count", "new_tables_created_count")}, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

