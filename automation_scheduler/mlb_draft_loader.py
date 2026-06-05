from __future__ import annotations

import argparse
import json

from .nfl_mlb_free_vs_paid_calibration import load_mlb_draft_sample


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", default=2025)
    args = parser.parse_args(argv)
    report = load_mlb_draft_sample(year=args.year)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
