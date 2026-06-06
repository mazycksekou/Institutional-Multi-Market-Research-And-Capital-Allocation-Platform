from __future__ import annotations

from typing import Any

from live_market_intelligence.core import build_oxylabs_audit, save_json, save_md


def build_audit() -> dict[str, Any]:
    return build_oxylabs_audit()


def main() -> int:
    report = build_audit()
    save_json("reports/LIVE_MARKET_OXYLABS_SOURCE_POLICY_AUDIT.json", report)
    lines = ["# LIVE MARKET OXYLABS SOURCE POLICY AUDIT", ""]
    for key in ("oxylabs_residential_proxy_used", "oxylabs_web_scraper_api_used", "oxylabs_calls_attempted", "oxylabs_calls_successful", "oxylabs_calls_failed"):
        lines.append(f"- `{key}`: `{report[key]}`")
    save_md("reports/LIVE_MARKET_OXYLABS_SOURCE_POLICY_AUDIT.md", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
