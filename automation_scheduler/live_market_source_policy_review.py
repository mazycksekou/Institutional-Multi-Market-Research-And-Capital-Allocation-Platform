from __future__ import annotations

from typing import Any

from live_market_intelligence.core import build_source_policy_matrix, save_json, save_md


def build_review() -> dict[str, Any]:
    return build_source_policy_matrix()


def main() -> int:
    report = build_review()
    save_json("reports/LIVE_MARKET_SOURCE_POLICY_MATRIX.json", report)
    lines = ["# LIVE MARKET SOURCE POLICY MATRIX", ""]
    for key in (
        "source_policy_sources_reviewed",
        "source_policy_sources_accepted_for_ingestion",
        "source_policy_sources_replay_only",
        "source_policy_sources_manual_only",
        "source_policy_sources_paid_license_required",
        "source_policy_sources_policy_blocked",
        "source_policy_sources_terms_blocked",
        "source_policy_sources_license_unclear",
    ):
        lines.append(f"- `{key}`: `{report[key]}`")
    save_md("reports/LIVE_MARKET_SOURCE_POLICY_MATRIX.md", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
