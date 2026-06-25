from __future__ import annotations

from typing import Any, Mapping, Sequence

from ._shared import as_plain_dict, build_text_summary, clamp, compact_list, normalize_text
from .contracts import MarketIntelligenceContract, STANDARD_REPORT_FIELDS, build_market_intelligence_contract


def build_market_intelligence_report(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    contract = build_market_intelligence_contract(data)
    report = contract.as_dict()
    report["confidence"] = clamp(report.get("confidence", 0.0))
    report["liquidity_zones"] = [as_plain_dict(zone) for zone in report.get("liquidity_zones") or []]
    report["catalysts"] = compact_list(report.get("catalysts"), limit=10)
    report["reasoning"] = compact_list(report.get("reasoning"), limit=12)
    report["trade_plan"] = str(report.get("trade_plan") or "")
    report["risk"] = str(report.get("risk") or "")
    report["invalidation"] = str(report.get("invalidation") or "")
    report["no_trade_reason"] = str(report.get("no_trade_reason") or "")
    for key, value in data.items():
        if key not in report:
            report[key] = value
    for field in STANDARD_REPORT_FIELDS:
        report.setdefault(field, None)
    report["report_summary"] = build_text_summary(
        [
            normalize_text(report.get("market")),
            normalize_text(report.get("bias")),
            f"confidence={report['confidence']:.1f}",
            report.get("no_trade_reason") or report.get("risk") or "review_only",
        ]
    )
    return report


def build_standard_market_intelligence_report(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_market_intelligence_report(payload, **overrides)


def summarize_market_intelligence_report(report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = as_plain_dict(report or {})
    return {
        "market": data.get("market"),
        "symbol_or_event": data.get("symbol_or_event"),
        "bias": data.get("bias"),
        "confidence": clamp(data.get("confidence", 0.0)),
        "primary_target": data.get("primary_target"),
        "secondary_target": data.get("secondary_target"),
        "stretch_target": data.get("stretch_target"),
        "support": data.get("support"),
        "resistance": data.get("resistance"),
        "no_trade_reason": data.get("no_trade_reason"),
        "report_summary": data.get("report_summary"),
    }


def validate_market_intelligence_report(report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = as_plain_dict(report or {})
    missing = [field for field in STANDARD_REPORT_FIELDS if field not in data]
    return {
        "ok": not missing,
        "missing_fields": missing,
        "status": "valid" if not missing else "invalid",
    }
