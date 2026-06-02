from __future__ import annotations

import json
from typing import Any


DEEPSEEK_STANDING_INSTRUCTION = """You are DeepSeek acting only as a read-only Profit Lab red-team analyst.
Analyze compact redacted data only.
Never request secrets.
Never request raw payloads.
Never approve execution.
Never create orders or bet slips.
Never submit trades, bets, wagers, broker orders, Kalshi orders, sportsbook bets, or crypto orders.
Classify edge quality, liquidity risk, trap risk, calibration support, out-of-distribution risk, and missing data.
If evidence is weak, say so.
Do not fabricate outcomes, probabilities, settlement results, historical performance, or calibration support.
You may downgrade, disagree, request more data, or recommend review-only attention.
You may not output BUY, SELL, PLACE_BET, PLACE_ORDER, EXECUTE, or any executable payload.
Return strict compact JSON only."""


CANDIDATE_OUTPUT_CONTRACT = {
    "deepseek_status": "review_complete",
    "candidate_id": "string",
    "asset_type": "string",
    "market_type": "string",
    "recommended_action": "ACTIVE_REVIEW|WATCHLIST_REVIEW|LOW_PRIORITY_REVIEW|NO_BET|NO_TRADE|DATA_INSUFFICIENT|NO_REVIEW",
    "confidence_score": 0,
    "edge_quality_score": 0,
    "liquidity_risk_score": 0,
    "trap_risk_score": 0,
    "calibration_support_score": 0,
    "out_of_distribution_risk": 0,
    "agreement_with_core_model": False,
    "disagreement_reasons": [],
    "missing_inputs": [],
    "review_reasons": [],
    "no_bet_reasons": [],
    "no_trade_reasons": [],
    "next_data_to_collect": [],
    "red_team_only": True,
    "deepseek_used": True,
    "provider_write": False,
    "execution_allowed": False,
    "live_execution_enabled": False,
    "auto_execution": False,
    "human_approval_required": True,
    "owner_approval_required": True,
}


DAILY_REPORT_OUTPUT_CONTRACT = {
    "report_id": "string",
    "date": "YYYY-MM-DD",
    "strongest_review_candidates": [],
    "strongest_no_bet_no_trade_traps": [],
    "calibration_improvements": [],
    "failing_clusters": [],
    "missing_data": [],
    "provider_issues": [],
    "disagreement_count": 0,
    "repeated_model_mistakes": [],
    "recommended_next_data_to_collect": [],
    "recommended_next_codex_task": "string",
    "safety_status": {
        "red_team_only": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": True,
        "owner_approval_required": True,
    },
    "red_team_only": True,
    "deepseek_used": True,
    "provider_write": False,
    "execution_allowed": False,
    "live_execution_enabled": False,
    "auto_execution": False,
    "human_approval_required": True,
    "owner_approval_required": True,
}


def build_candidate_review_prompt(compact_input: dict[str, Any]) -> str:
    return "\n".join(
        [
            DEEPSEEK_STANDING_INSTRUCTION,
            "Task: attack the candidate's claimed edge. Identify fake edge, weak calibration, insufficient sample, liquidity traps, stale markets, wide-spread fake value, settlement uncertainty, provider/data quality failures, timestamp problems, low-confidence prop or pattern setups, sportsbook trap lines, and no-bet/no-trade conditions.",
            "Use only this output schema:",
            json.dumps(CANDIDATE_OUTPUT_CONTRACT, separators=(",", ":"), sort_keys=True),
            "Compact redacted input:",
            json.dumps(compact_input, separators=(",", ":"), sort_keys=True),
        ]
    )


def build_daily_report_prompt(compact_input: dict[str, Any]) -> str:
    return "\n".join(
        [
            DEEPSEEK_STANDING_INSTRUCTION,
            "Task: produce a compact daily Profit Lab red-team report from the supplied summaries. Focus on where edge is real, fake, unsupported, stale, trapped by liquidity/spread/settlement, or contradicted by outcomes/calibration.",
            "Use only this output schema:",
            json.dumps(DAILY_REPORT_OUTPUT_CONTRACT, separators=(",", ":"), sort_keys=True),
            "Compact redacted input:",
            json.dumps(compact_input, separators=(",", ":"), sort_keys=True),
        ]
    )
