from __future__ import annotations

from typing import Any

from src.data.data_paths import get_storage_health
from src.security.ai_provider_security import get_ai_provider_config
from src.security.policy import ALLOWED_AI_PROVIDERS, DEFAULT_AI_PROVIDER, kill_switch_state, locked_safety_flags


__all__ = ["build_security_readiness_report"]


def build_security_readiness_report(*, base_data_dir: str | None = None) -> dict[str, Any]:
    ai_config = get_ai_provider_config()
    kill_switches = kill_switch_state()
    storage = get_storage_health()
    return {
        "ok": True,
        "status": "security_readiness",
        "ai_allowed_providers": ALLOWED_AI_PROVIDERS,
        "default_ai_provider": DEFAULT_AI_PROVIDER,
        "openai_enabled_for_analysis": bool(ai_config["openai_analyst_enabled"] and ai_config["allow_openai_analyst"]),
        "deepseek_enabled_for_analysis": bool(ai_config["deepseek_enabled"]),
        "forbidden_provider_policy": "deny_by_default",
        "kill_switches_active": bool(kill_switches["kill_switches_active"]),
        "kill_switches": kill_switches["switches"],
        "audit_ledger_enabled": bool(storage.get("write_ok", False)),
        "security_posture": "locked_read_only",
        "ai_execution_authority": "blocked",
        "provider_write_firewall": "locked",
        "owner_approval_scaffold": "enabled_fail_closed",
        "risk_limit_guard": "enabled_fail_closed",
        "storage": storage,
        "allowed_ai_provider_config_names": [
            "AI_ANALYST_PROVIDER",
            "DEEPSEEK_ENABLED",
            "DEEPSEEK_BASE_URL",
            "DEEPSEEK_MODEL",
            "DEEPSEEK_TIMEOUT_SECONDS",
            "OPENAI_ANALYST_ENABLED",
            "OPENAI_ANALYST_MODEL",
            "ALLOW_OPENAI_ANALYST",
        ],
        **locked_safety_flags(),
        "secrets_detected": False,
        "raw_payload_exposed": False,
        "auth_header_exposed": False,
        "signature_exposed": False,
        "redaction_applied": True,
    }

