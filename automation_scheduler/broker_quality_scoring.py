from __future__ import annotations

from typing import Any


BROKER_STATUSES = {"RESEARCH_ONLY", "PAPER_SUPPORTED", "SANDBOX_READY", "NOT_APPROVED"}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def score_broker_provider(row: dict[str, Any]) -> dict[str, Any]:
    reliability = _clamp(_num(row.get("api_reliability_score"), 50.0))
    uptime = _clamp(_num(row.get("uptime_score"), 50.0))
    latency = _clamp(_num(row.get("latency_score"), 50.0))
    order_types = _clamp(_num(row.get("order_type_support_score"), 50.0))
    fees = _clamp(_num(row.get("fee_score"), 50.0))
    spread_quality = _clamp(_num(row.get("spread_quality_score"), 50.0))
    slippage_risk = _clamp(_num(row.get("slippage_risk_score"), 50.0))
    execution_restriction_risk = _clamp(_num(row.get("execution_restriction_risk"), 50.0))
    compliance_risk = _clamp(_num(row.get("compliance_risk_score"), 50.0))
    paper_or_sandbox_support = bool(row.get("paper_or_sandbox_support", False))
    asset_types = list(row.get("asset_types_supported") or [])
    broker_quality_score = (
        reliability * 0.18
        + uptime * 0.16
        + latency * 0.12
        + order_types * 0.12
        + fees * 0.10
        + spread_quality * 0.14
        + (100.0 - slippage_risk) * 0.08
        + (100.0 - execution_restriction_risk) * 0.05
        + (100.0 - compliance_risk) * 0.05
    )
    broker_quality_score = round(_clamp(broker_quality_score), 2)
    if compliance_risk >= 80 or execution_restriction_risk >= 85:
        broker_status = "NOT_APPROVED"
    elif paper_or_sandbox_support and broker_quality_score >= 80 and reliability >= 75:
        broker_status = "SANDBOX_READY"
    elif paper_or_sandbox_support:
        broker_status = "PAPER_SUPPORTED"
    else:
        broker_status = "RESEARCH_ONLY"
    return {
        "broker_name": str(row.get("broker_name") or row.get("provider_name") or "unknown"),
        "provider_type": str(row.get("provider_type") or "broker_research"),
        "asset_types_supported": asset_types,
        "api_reliability_score": reliability,
        "uptime_score": uptime,
        "latency_score": latency,
        "order_type_support_score": order_types,
        "fee_score": fees,
        "spread_quality_score": spread_quality,
        "slippage_risk_score": slippage_risk,
        "paper_or_sandbox_support": paper_or_sandbox_support,
        "execution_restriction_risk": execution_restriction_risk,
        "compliance_risk_score": compliance_risk,
        "broker_quality_score": broker_quality_score,
        "broker_status": broker_status,
        "source_access_type": row.get("source_access_type", "research_metadata"),
        "current_phase_allowed": bool(row.get("current_phase_allowed", True)),
        "future_paid_candidate": bool(row.get("future_paid_candidate", False)),
        "requires_budget_approval": bool(row.get("requires_budget_approval", False)),
        "approval_status": row.get("approval_status", "needs_review"),
        "enabled": False,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
    }


def default_broker_quality_rows() -> list[dict[str, Any]]:
    return [
        score_broker_provider(
            {
                "broker_name": "research_only_equity_broker_template",
                "provider_type": "broker_research",
                "asset_types_supported": ["stock", "etf"],
                "api_reliability_score": 70,
                "uptime_score": 70,
                "latency_score": 60,
                "order_type_support_score": 65,
                "fee_score": 70,
                "spread_quality_score": 60,
                "slippage_risk_score": 45,
                "paper_or_sandbox_support": True,
                "execution_restriction_risk": 45,
                "compliance_risk_score": 35,
                "approval_status": "needs_review",
            }
        ),
        score_broker_provider(
            {
                "broker_name": "research_only_crypto_exchange_template",
                "provider_type": "exchange_research",
                "asset_types_supported": ["crypto"],
                "api_reliability_score": 65,
                "uptime_score": 68,
                "latency_score": 62,
                "order_type_support_score": 58,
                "fee_score": 55,
                "spread_quality_score": 55,
                "slippage_risk_score": 55,
                "paper_or_sandbox_support": False,
                "execution_restriction_risk": 60,
                "compliance_risk_score": 60,
                "approval_status": "not_approved",
            }
        ),
    ]


def build_broker_quality_report(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    brokers = [score_broker_provider(row) for row in rows] if rows is not None else default_broker_quality_rows()
    status_counts: dict[str, int] = {}
    for broker in brokers:
        status = str(broker.get("broker_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "ok": True,
        "status": "ok",
        "broker_count": len(brokers),
        "status_counts": status_counts,
        "brokers": brokers,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
    }
