from __future__ import annotations

import argparse
import json
from pathlib import Path

from .nfl_mlb_active_discovery import build_active_source_discovery_log, write_active_source_discovery_log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--allow-oxylabs", action="store_true")
    parser.add_argument("--allow-paid-retrieval", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_active_source_discovery_log(sport="nfl", base_data_dir=args.base_data_dir, allow_oxylabs=args.allow_oxylabs, allow_paid_retrieval=args.allow_paid_retrieval)
    paths = write_active_source_discovery_log(report, sport="nfl") if args.persist else {}
    print(json.dumps({**{k: report.get(k) for k in ("ok", "status", "run_mode", "sources_discovered_count", "sources_accepted_count", "sources_rejected_count", "paid_source_enabled_count")}, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

