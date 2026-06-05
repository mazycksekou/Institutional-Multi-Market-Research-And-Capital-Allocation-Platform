from __future__ import annotations

import argparse
import json

from .nfl_mlb_free_vs_paid_calibration import load_structured_wiki_seed_sample


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-records", type=int, default=3)
    args = parser.parse_args(argv)
    report = load_structured_wiki_seed_sample(max_records=args.max_records)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
