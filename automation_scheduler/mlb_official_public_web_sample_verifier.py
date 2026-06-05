from __future__ import annotations

import argparse
import json

from .nfl_mlb_free_vs_paid_calibration import build_mlb_official_public_web_sample_verification_report, write_mlb_official_public_web_sample_verification_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_mlb_official_public_web_sample_verification_report()
    paths = write_mlb_official_public_web_sample_verification_report(report) if args.persist else {}
    print(json.dumps({**report, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
