from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _write_log_line(log_path: Path, message: str) -> None:
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the JSON audit pipeline and optional DeepSeek review.")
    parser.add_argument("--project-path", default=str(ROOT), help="Repository root that contains the data and scripts folders.")
    parser.add_argument("--no-deepseek", action="store_true", help="Skip the optional DeepSeek review step.")
    parser.add_argument("--open-report", action="store_true", help="Open the generated summary report after the audit completes.")
    args = parser.parse_args(argv)

    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Project path not found: {project_path}")
        return 1

    report_dir = project_path / "reports" / "json_data_audit"
    log_path = report_dir / "automation_log.txt"
    audit_script = project_path / "scripts" / "analyze_json_data.py"
    review_script = project_path / "scripts" / "review_json_audit_with_deepseek.py"
    if not audit_script.exists():
        _write_log_line(log_path, f"Missing audit script: {audit_script}")
        return 1

    _write_log_line(log_path, "Starting JSON audit pipeline.")
    _write_log_line(log_path, f"ProjectPath={project_path}")
    _write_log_line(log_path, "Running audit script.")

    completed = subprocess.run([sys.executable, str(audit_script)], cwd=project_path, check=False)
    if completed.returncode != 0:
        _write_log_line(log_path, f"Audit script failed with exit code {completed.returncode}.")
        return completed.returncode

    summary_path = report_dir / "latest_summary.md"
    if not summary_path.exists():
        _write_log_line(log_path, f"Expected report not found: {summary_path}")
        return 1
    _write_log_line(log_path, f"Audit report created: {summary_path}")

    if not args.no_deepseek:
        if not review_script.exists():
            _write_log_line(log_path, "DeepSeek review script not found; audit completed and review skipped.")
        elif not os.environ.get("DEEPSEEK_API_KEY", "").strip():
            _write_log_line(log_path, "DEEPSEEK_API_KEY is not set; audit completed and review skipped.")
        else:
            _write_log_line(log_path, "Sending compact report to DeepSeek for review.")
            review_completed = subprocess.run(
                [sys.executable, str(review_script), "--report-path", str(summary_path)],
                cwd=project_path,
                check=False,
            )
            if review_completed.returncode != 0:
                _write_log_line(log_path, f"DeepSeek review failed with exit code {review_completed.returncode}.")
                return review_completed.returncode
            _write_log_line(log_path, f"DeepSeek review created: {report_dir / 'latest_deepseek_review.md'}")
    else:
        _write_log_line(log_path, "DeepSeek review skipped because --no-deepseek was used.")

    if args.open_report:
        try:
            webbrowser.open(summary_path.resolve().as_uri())
        except Exception:
            _write_log_line(log_path, "Unable to open summary report automatically.")

    _write_log_line(log_path, "JSON audit pipeline finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
