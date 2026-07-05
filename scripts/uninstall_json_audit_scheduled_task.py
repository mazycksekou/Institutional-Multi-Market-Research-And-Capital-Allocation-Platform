from __future__ import annotations

import argparse
import platform
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Uninstall the optional Windows Task Scheduler entry for the JSON audit pipeline.")
    parser.add_argument("--task-name", default="BettingStockApiJsonAudit")
    args = parser.parse_args(argv)

    if platform.system().lower() != "windows":
        print("Windows Task Scheduler is only available on Windows.")
        return 2

    completed = subprocess.run(["schtasks", "/Delete", "/TN", args.task_name, "/F"], check=False)
    if completed.returncode == 0:
        print(f"Scheduled task removed: {args.task_name}")
    else:
        print(f"Scheduled task not found or could not be removed: {args.task_name}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
