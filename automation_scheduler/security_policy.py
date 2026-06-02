from __future__ import annotations

import os
from typing import Any


ALLOWED_AI_PROVIDERS = ["deepseek", "openai"]
DEFAULT_AI_PROVIDER = "deepseek"

AI_ALLOWED_CAPABILITIES = [
    "analyze_compact_redacted_data",
    "summarize_review_queues",
    "flag_fake_edge",
    "flag_stale_markets",
    "flag_trap_zones",
    "flag_out_of_distribution_setups",
    "flag_missing_data",
    "flag_security_warnings",
    "disagree_with_core_model",
    "downgrade_review_priority",
    "request_more_data",
    "create_compact_disagreement_records",
    "produce_no_bet_no_trade_warnings",
    "produce_daily_research_reports",
]

AI_FORBIDDEN_CAPABILITIES = [
    "place_trades",
    "place_bets",
    "submit_orders",
    "submit_wagers",
    "submit_kalshi_orders",
    "submit_sportsbook_bets",
    "submit_broker_orders",
    "submit_crypto_exchange_orders",
    "approve_live_execution",
    "bypass_dry_run",
    "write_to_providers",
    "alter_execution_flags",
    "alter_risk_limits",
    "alter_secrets",
    "access_raw_api_keys",
    "return_secrets",
    "generate_executable_order_payloads",
    "generate_bet_slips",
    "promote_to_executable_status",
    "set_owner_approval",
    "disable_kill_switches",
]

EXECUTION_TRUE_FIELDS = {
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "auto_execution",
    "auto_execution_enabled",
    "auto_bet_enabled",
    "auto_trade_enabled",
    "submit_live_order",
    "submit_order",
    "place_order",
    "place_bet",
    "submit_bet",
    "submit_trade",
    "broker_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "kalshi_order_execution_enabled",
    "crypto_trade_execution_enabled",
    "stock_trade_execution_enabled",
    "owner_approval_present",
    "owner_approval_signature_valid",
}

EXECUTABLE_PAYLOAD_KEYS = {
    "order_payload",
    "broker_order_payload",
    "sportsbook_bet_payload",
    "kalshi_order_payload",
    "crypto_trade_payload",
    "stock_trade_payload",
    "trade_payload",
    "execution_payload",
    "executable_order_payload",
    "bet_slip",
    "wager_payload",
    "order_request",
    "provider_write_payload",
}

FORBIDDEN_ACTION_VALUES = {
    "buy",
    "sell",
    "order",
    "trade",
    "execute",
    "place_bet",
    "submit_bet",
    "submit_order",
    "submit_trade",
    "kalshi_order",
    "sportsbook_bet",
    "crypto_swap",
    "enable_execution",
    "disable_kill_switch",
}


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def locked_safety_flags() -> dict[str, Any]:
    return {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "dry_run": True,
        "simulation_only": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "secrets_detected": False,
    }


def kill_switch_state() -> dict[str, Any]:
    switches = {
        "GLOBAL_EXECUTION_KILL_SWITCH": env_bool("GLOBAL_EXECUTION_KILL_SWITCH", True),
        "BROKER_EXECUTION_KILL_SWITCH": env_bool("BROKER_EXECUTION_KILL_SWITCH", True),
        "SPORTSBOOK_EXECUTION_KILL_SWITCH": env_bool("SPORTSBOOK_EXECUTION_KILL_SWITCH", True),
        "KALSHI_EXECUTION_KILL_SWITCH": env_bool("KALSHI_EXECUTION_KILL_SWITCH", True),
        "CRYPTO_EXECUTION_KILL_SWITCH": env_bool("CRYPTO_EXECUTION_KILL_SWITCH", True),
        "STOCK_EXECUTION_KILL_SWITCH": env_bool("STOCK_EXECUTION_KILL_SWITCH", True),
        "AI_EXECUTION_AUTHORITY_KILL_SWITCH": True,
    }
    return {
        "status": "active" if any(switches.values()) else "inactive",
        "kill_switches_active": any(switches.values()),
        "switches": switches,
        **locked_safety_flags(),
    }


def _walk_payload(payload: Any, path: str = "") -> list[str]:
    violations: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            lower_key = str(key).strip().lower()
            current = f"{path}.{lower_key}" if path else lower_key
            if lower_key in EXECUTION_TRUE_FIELDS and value is True:
                violations.append(f"execution_flag_true:{current}")
            if lower_key in EXECUTABLE_PAYLOAD_KEYS and value not in (None, {}, [], ""):
                violations.append(f"executable_payload:{current}")
            if lower_key in {"recommended_action", "action", "order_action", "side", "intent"}:
                if str(value or "").strip().lower() in FORBIDDEN_ACTION_VALUES:
                    violations.append(f"forbidden_action:{current}")
            violations.extend(_walk_payload(value, current))
    elif isinstance(payload, list):
        for index, item in enumerate(payload[:100]):
            violations.extend(_walk_payload(item, f"{path}[{index}]"))
    elif isinstance(payload, str):
        value = payload.strip().lower()
        if value in FORBIDDEN_ACTION_VALUES:
            violations.append(f"forbidden_action_value:{path}")
    return violations


def detect_execution_authority_violations(payload: Any) -> list[str]:
    return sorted(set(_walk_payload(payload)))


def enforce_ai_capability_boundary(payload: Any, *, actor_provider: str | None = None) -> dict[str, Any]:
    violations = detect_execution_authority_violations(payload)
    status = "ai_execution_authority_blocked" if violations else "ai_capability_limited"
    return {
        "ok": not bool(violations),
        "status": status,
        "actor_type": "ai_provider",
        "actor_provider": actor_provider,
        "allowed_capabilities": AI_ALLOWED_CAPABILITIES,
        "forbidden_capabilities": AI_FORBIDDEN_CAPABILITIES,
        "violations": violations,
        "ai_can_only_flag_downgrade_disagree_or_request_more_data": True,
        **locked_safety_flags(),
    }
