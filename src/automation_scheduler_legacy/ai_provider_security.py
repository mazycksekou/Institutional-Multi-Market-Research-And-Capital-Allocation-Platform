from __future__ import annotations

import os
from typing import Any

from src.services.ledger_service import append_security_event
from .provider_allowlist import classify_provider, is_internal_deterministic_provider
from .security_event_types import AI_PROVIDER_REJECTED, AI_PROVIDER_SELECTED, FORBIDDEN_PROVIDER_REJECTED
from .security_policy import ALLOWED_AI_PROVIDERS, DEFAULT_AI_PROVIDER, env_bool, locked_safety_flags


def _timeout_seconds() -> float:
    raw = os.getenv("DEEPSEEK_TIMEOUT_SECONDS", os.getenv("DEEPSEEK_TIMEOUT", "20"))
    try:
        return max(1.0, float(raw or 20))
    except (TypeError, ValueError):
        return 20.0


def get_ai_provider_config() -> dict[str, Any]:
    return {
        "ai_analyst_provider": os.getenv("AI_ANALYST_PROVIDER", DEFAULT_AI_PROVIDER).strip().lower() or DEFAULT_AI_PROVIDER,
        "deepseek_enabled": env_bool("DEEPSEEK_ENABLED", True),
        "deepseek_base_url_configured": bool(os.getenv("DEEPSEEK_BASE_URL", "http://127.0.0.1:11434").strip()),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-r1").strip() or "deepseek-r1",
        "deepseek_timeout_seconds": _timeout_seconds(),
        "openai_analyst_enabled": env_bool("OPENAI_ANALYST_ENABLED", False),
        "allow_openai_analyst": env_bool("ALLOW_OPENAI_ANALYST", False),
        "openai_analyst_model_configured": bool(os.getenv("OPENAI_ANALYST_MODEL", "").strip()),
        "allowed_ai_providers": ALLOWED_AI_PROVIDERS,
        "default_provider": DEFAULT_AI_PROVIDER,
        **locked_safety_flags(),
    }


def _rejected_response(
    *,
    provider: str,
    reason: str,
    provider_class: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "ai_provider_not_allowed",
        "provider": provider,
        "provider_class": provider_class,
        "denial_reason": reason,
        "allowed_ai_providers": ALLOWED_AI_PROVIDERS,
        "default_provider": DEFAULT_AI_PROVIDER,
        **locked_safety_flags(),
    }


def evaluate_ai_provider(
    provider: str | None = None,
    *,
    provider_type: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
) -> dict[str, Any]:
    config = get_ai_provider_config()
    selected = str(provider or config["ai_analyst_provider"] or DEFAULT_AI_PROVIDER).strip().lower()
    provider_class = classify_provider(selected, provider_type=provider_type)

    if is_internal_deterministic_provider(selected, provider_type=provider_type):
        response = {
            "ok": True,
            "status": "internal_deterministic_diagnostics_allowed",
            "provider": selected,
            "provider_class": provider_class,
            "external_ai_provider": False,
            "read_only_computation": True,
            "allowed_ai_providers": ALLOWED_AI_PROVIDERS,
            "default_provider": DEFAULT_AI_PROVIDER,
            **locked_safety_flags(),
        }
        return response

    if provider_class not in {"deepseek", "openai"}:
        response = _rejected_response(
            provider=selected,
            reason="forbidden_or_unknown_external_ai_provider",
            provider_class=provider_class,
        )
        if persist_audit:
            append_security_event(
                event_type=FORBIDDEN_PROVIDER_REJECTED,
                actor_type="system",
                actor_provider=selected,
                action_requested="select_ai_analyst_provider",
                denial_reason=response["denial_reason"],
                provider_name=selected,
                request_payload={"provider": selected, "provider_type": provider_type},
                response_payload=response,
                base_data_dir=base_data_dir,
            )
        return response

    if provider_class == "deepseek" and not config["deepseek_enabled"]:
        response = _rejected_response(provider=selected, reason="deepseek_disabled", provider_class=provider_class)
        if persist_audit:
            append_security_event(
                event_type=AI_PROVIDER_REJECTED,
                actor_type="system",
                actor_provider=selected,
                action_requested="select_ai_analyst_provider",
                denial_reason=response["denial_reason"],
                provider_name=selected,
                request_payload={"provider": selected},
                response_payload=response,
                base_data_dir=base_data_dir,
            )
        return response

    if provider_class == "openai" and not (config["openai_analyst_enabled"] and config["allow_openai_analyst"]):
        response = _rejected_response(provider=selected, reason="openai_analysis_not_explicitly_enabled", provider_class=provider_class)
        if persist_audit:
            append_security_event(
                event_type=AI_PROVIDER_REJECTED,
                actor_type="system",
                actor_provider=selected,
                action_requested="select_ai_analyst_provider",
                denial_reason=response["denial_reason"],
                provider_name=selected,
                request_payload={"provider": selected},
                response_payload=response,
                base_data_dir=base_data_dir,
            )
        return response

    response = {
        "ok": True,
        "status": "ai_provider_allowed",
        "provider": selected,
        "provider_class": provider_class,
        "external_ai_provider": True,
        "allowed_ai_providers": ALLOWED_AI_PROVIDERS,
        "default_provider": DEFAULT_AI_PROVIDER,
        "openai_requires_dual_enable": True,
        "analysis_only": True,
        "can_execute": False,
        "can_write_to_provider": False,
        "can_generate_executable_payloads": False,
        **locked_safety_flags(),
    }
    if persist_audit:
        append_security_event(
            event_type=AI_PROVIDER_SELECTED,
            actor_type="system",
            actor_provider=selected,
            action_requested="select_ai_analyst_provider",
            action_allowed=False,
            denial_reason="analysis_only_no_execution_authority",
            provider_name=selected,
            request_payload={"provider": selected},
            response_payload=response,
            base_data_dir=base_data_dir,
        )
    return response
