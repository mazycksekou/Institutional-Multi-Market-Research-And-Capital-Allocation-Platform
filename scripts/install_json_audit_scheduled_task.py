from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the optional Windows Task Scheduler entry for the JSON audit pipeline.")
    parser.add_argument("--project-path", default=str(ROOT), help="Repository root used by the scheduled task.")
    parser.add_argument("--frequency", choices=["Daily", "Hourly"], default="Daily")
    parser.add_argument("--time", default="21:00")
    parser.add_argument("--task-name", default="BettingStockApiJsonAudit")
    parser.add_argument("--no-deepseek", action="store_true")
    args = parser.parse_args(argv)

    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Project path not found: {project_path}")
        return 1

    pipeline_script = project_path / "scripts" / "run_json_audit_pipeline.py"
    if not pipeline_script.exists():
        print(f"Pipeline script not found: {pipeline_script}")
        print("Copy this pack's scripts folder into the project root first.")
        return 1

    command = [sys.executable, str(pipeline_script), "--project-path", str(project_path)]
    if args.no_deepseek:
        command.append("--no-deepseek")
    task_command = subprocess.list2cmdline(command)

    if platform.system().lower() != "windows":
        print("Windows Task Scheduler is only available on Windows.")
        print(f"Canonical Python command: {task_command}")
        return 2

    if args.frequency == "Hourly":
        schtasks = ["schtasks", "/Create", "/TN", args.task_name, "/SC", "HOURLY", "/MO", "1", "/TR", task_command, "/F"]
    else:
        schtasks = ["schtasks", "/Create", "/TN", args.task_name, "/SC", "DAILY", "/ST", args.time, "/TR", task_command, "/F"]

    completed = subprocess.run(schtasks, check=False)
    if completed.returncode != 0:
        return completed.returncode

    print(f"Scheduled task installed: {args.task_name}")
    print(f"Frequency: {args.frequency}")
    if args.frequency == "Daily":
        print(f"Time: {args.time}")
    print(f"Project: {project_path}")
    print(f"Run now with: schtasks /Run /TN \"{args.task_name}\"")
    print(f"Check task with: schtasks /Query /TN \"{args.task_name}\"")
    print("Remove task with: python scripts/uninstall_json_audit_scheduled_task.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
