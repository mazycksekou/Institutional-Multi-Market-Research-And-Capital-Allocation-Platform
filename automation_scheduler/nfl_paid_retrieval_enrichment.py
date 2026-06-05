from __future__ import annotations

import argparse
import json

from .nfl_mlb_active_discovery import build_paid_retrieval_enrichment_report, write_paid_retrieval_enrichment_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--allow-oxylabs", action="store_true")
    parser.add_argument("--allow-paid-retrieval", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_paid_retrieval_enrichment_report(sport="nfl", base_data_dir=args.base_data_dir, allow_oxylabs=args.allow_oxylabs, allow_paid_retrieval=args.allow_paid_retrieval)
    paths = write_paid_retrieval_enrichment_report(report, sport="nfl") if args.persist else {}
    print(json.dumps({**{k: report.get(k) for k in ("ok", "status", "run_mode", "existing_fields_total", "existing_fields_populated_before", "existing_fields_populated_after", "fields_completed", "new_fields_created_count", "source_lanes_attempted", "source_lanes_populated", "source_lanes_still_blocked", "source_lanes_research", "paid_source_enabled_count")}, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

