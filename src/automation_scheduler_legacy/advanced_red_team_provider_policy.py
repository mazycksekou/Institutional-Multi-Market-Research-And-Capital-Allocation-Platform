from __future__ import annotations

import os
from typing import Any

from .provider_allowlist import normalize_provider_name
from src.security.policy import locked_safety_flags


ALLOWED_ADVANCED_RED_TEAM_AI_PROVIDERS = ["deepseek", "openai"]
DEFAULT_ADVANCED_RED_TEAM_PROVIDER = "deepseek"
INTERNAL_DETERMINISTIC_PROVIDERS = {"internal", "internal_deterministic", "local_math", "offline_diagnostics", "python_diagnostics"}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _timeout_seconds() -> float:
    try:
        return max(1.0, min(120.0, float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "20") or 20)))
    except (TypeError, ValueError):
        return 20.0


def get_advanced_red_team_config() -> dict[str, Any]:
    provider = normalize_provider_name(os.getenv("ADVANCED_RED_TEAM_PROVIDER", DEFAULT_ADVANCED_RED_TEAM_PROVIDER))
    return {
        "advanced_red_team_enabled": _env_bool("ADVANCED_RED_TEAM_ENABLED", True),
        "advanced_red_team_provider": provider or DEFAULT_ADVANCED_RED_TEAM_PROVIDER,
        "advanced_red_team_allow_openai": _env_bool("ADVANCED_RED_TEAM_ALLOW_OPENAI", False),
        "deepseek_enabled": _env_bool("DEEPSEEK_ENABLED", False),
        "deepseek_base_url_configured": bool(os.getenv("DEEPSEEK_BASE_URL", "").strip()),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip() or "deepseek-chat",
        "deepseek_timeout_seconds": _timeout_seconds(),
        "openai_red_team_enabled": _env_bool("OPENAI_RED_TEAM_ENABLED", False),
        "openai_red_team_model_configured": bool(os.getenv("OPENAI_RED_TEAM_MODEL", "").strip()),
        "allowed_ai_providers": ALLOWED_ADVANCED_RED_TEAM_AI_PROVIDERS,
        "default_provider": DEFAULT_ADVANCED_RED_TEAM_PROVIDER,
        **locked_safety_flags(),
    }


def provider_not_allowed_response(provider: str | None) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "provider_not_allowed_for_red_team",
        "provider": provider,
        "allowed_ai_providers": ALLOWED_ADVANCED_RED_TEAM_AI_PROVIDERS,
        "default_provider": DEFAULT_ADVANCED_RED_TEAM_PROVIDER,
        "deepseek_used": False,
        "openai_used": False,
        "external_ai_call_performed": False,
        "red_team_only": True,
        **locked_safety_flags(),
    }


def evaluate_advanced_red_team_provider(provider: str | None = None) -> dict[str, Any]:
    config = get_advanced_red_team_config()
    selected = normalize_provider_name(provider or config["advanced_red_team_provider"] or DEFAULT_ADVANCED_RED_TEAM_PROVIDER)

    if selected in INTERNAL_DETERMINISTIC_PROVIDERS:
        return {
            "ok": True,
            "status": "internal_deterministic_diagnostics_allowed",
            "provider": selected,
            "external_ai_provider": False,
            "read_only_internal_computation": True,
            "allowed_ai_providers": ALLOWED_ADVANCED_RED_TEAM_AI_PROVIDERS,
            "default_provider": DEFAULT_ADVANCED_RED_TEAM_PROVIDER,
            "deepseek_used": False,
            "openai_used": False,
            "external_ai_call_performed": False,
            "red_team_only": True,
            **locked_safety_flags(),
        }

    if selected == "deepseek":
        deepseek_selected_and_enabled = bool(config["advanced_red_team_enabled"] and config["deepseek_enabled"])
        return {
            "ok": True,
            "status": "red_team_provider_allowed" if deepseek_selected_and_enabled else "deepseek_disabled_deterministic_only",
            "provider": "deepseek",
            "external_ai_provider": True,
            "deepseek_enabled": bool(config["deepseek_enabled"]),
            "deepseek_model": config["deepseek_model"],
            "deepseek_timeout_seconds": config["deepseek_timeout_seconds"],
            "allowed_ai_providers": ALLOWED_ADVANCED_RED_TEAM_AI_PROVIDERS,
            "default_provider": DEFAULT_ADVANCED_RED_TEAM_PROVIDER,
            "deepseek_used": False,
            "deepseek_selected": True,
            "openai_used": False,
            "external_ai_call_performed": False,
            "red_team_only": True,
            **locked_safety_flags(),
        }

    if selected == "openai":
        allowed = bool(
            config["advanced_red_team_enabled"]
            and config["openai_red_team_enabled"]
            and config["advanced_red_team_allow_openai"]
        )
        if not allowed:
            out = provider_not_allowed_response("openai")
            out["denial_reason"] = "openai_red_team_not_explicitly_enabled"
            return out
        return {
            "ok": True,
            "status": "red_team_provider_allowed",
            "provider": "openai",
            "external_ai_provider": True,
            "openai_red_team_enabled": True,
            "openai_red_team_model_configured": bool(config["openai_red_team_model_configured"]),
            "allowed_ai_providers": ALLOWED_ADVANCED_RED_TEAM_AI_PROVIDERS,
            "default_provider": DEFAULT_ADVANCED_RED_TEAM_PROVIDER,
            "deepseek_used": False,
            "openai_used": False,
            "openai_selected": True,
            "external_ai_call_performed": False,
            "red_team_only": True,
            **locked_safety_flags(),
        }

    out = provider_not_allowed_response(selected)
    out["denial_reason"] = "forbidden_external_ai_provider"
    return out
