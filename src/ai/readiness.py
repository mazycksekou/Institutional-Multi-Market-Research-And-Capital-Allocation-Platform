from __future__ import annotations

from typing import Any

from .contracts import AIReadinessSnapshot


def build_ai_readiness(
    *,
    enabled: bool = False,
    reason: str = "ai_llm_deferred",
    provider: str = "disabled",
    model: str = "disabled",
) -> dict[str, Any]:
    snapshot = AIReadinessSnapshot(
        enabled=bool(enabled),
        status="active" if enabled else "deferred",
        reason=str(reason or "ai_llm_deferred"),
        provider=str(provider or "disabled").strip() or "disabled",
        model=str(model or "disabled").strip() or "disabled",
        local_only=True,
    )
    return {
        "ok": True,
        "status": snapshot.status,
        "enabled": snapshot.enabled,
        "reason": snapshot.reason,
        "provider": snapshot.provider,
        "model": snapshot.model,
        "local_only": snapshot.local_only,
        "external_calls_enabled": False,
        "prompt_execution_enabled": False,
        "training_enabled": False,
        "network_enabled": False,
    }


def get_ai_readiness() -> dict[str, Any]:
    return build_ai_readiness()

