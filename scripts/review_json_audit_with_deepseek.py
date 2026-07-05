from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "json_data_audit" / "latest_summary.md"
OUTPUT_PATH = ROOT / "reports" / "json_data_audit" / "latest_deepseek_review.md"
DEBUG_PATH = ROOT / "reports" / "json_data_audit" / "latest_deepseek_error_debug.txt"


def _sanitize_text(text: str) -> str:
    cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)
    cleaned = re.sub(r"(?i)(api[_-]?key|authorization|bearer|token|secret|signature|password)[^\r\n]{0,100}", r"\1=[REDACTED]", cleaned)
    return cleaned


def _post_deepseek(api_key: str, prompt: str) -> dict[str, object]:
    body = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "max_tokens": 350,
    }
    data = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    req = request.Request(
        "https://api.deepseek.com/chat/completions",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=60) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send the latest JSON audit summary to DeepSeek for a compact review.")
    parser.add_argument("--report-path", default=str(REPORT_PATH), help="Path to the JSON audit summary markdown file.")
    parser.add_argument("--output-path", default=str(OUTPUT_PATH), help="Where to write the DeepSeek review markdown.")
    parser.add_argument("--debug-path", default=str(DEBUG_PATH), help="Where to write debug details on failure.")
    parser.add_argument("--api-key", default=None, help="Override DEEPSEEK_API_KEY.")
    args = parser.parse_args(argv)

    report_path = Path(args.report_path)
    output_path = Path(args.output_path)
    debug_path = Path(args.debug_path)
    if not report_path.exists():
        raise SystemExit(f"Report not found: {report_path}")

    api_key = (args.api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
    if not api_key:
        raise SystemExit("Missing DEEPSEEK_API_KEY.")

    report = _sanitize_text(report_path.read_text(encoding="utf-8"))
    compact_report = report[:1200]
    prompt = _sanitize_text(
        f"""Review this JSON audit excerpt for my betting-stock-api project.

Return:
1. strongest data available now
2. messiest data
3. files to clean first
4. schemas to standardize
5. missing fields for calibration
6. safest next task for Codex
7. what DeepSeek can keep reviewing safely

Rules:
- no provider writes
- no live execution
- no bets/trades/orders
- no secrets handling
- no production data migration
- recommend read-only or test-only tasks first

Audit excerpt:
{compact_report}
"""
    )
    try:
        response = _post_deepseek(api_key, prompt)
        content = response["choices"][0]["message"]["content"]  # type: ignore[index]
        if not content:
            content = "DeepSeek returned an empty response."
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"# DeepSeek JSON Audit Review\n\n{content}", encoding="utf-8")
        print(f"DeepSeek review created:\n{output_path}")
        return 0
    except (OSError, error.URLError, error.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        debug = "\n".join(
            [
                "DeepSeek request failed.",
                "",
                f"Message:\n{exc}",
                "",
                f"Report chars:\n{len(report)}",
                f"Prompt chars:\n{len(prompt)}",
            ]
        )
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(debug, encoding="utf-8")
        output_path.write_text(f"# DeepSeek Review Failed\n\n{debug}", encoding="utf-8")
        print(f"DeepSeek request failed:\n{exc}")
        print(f"Debug written:\n{debug_path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
