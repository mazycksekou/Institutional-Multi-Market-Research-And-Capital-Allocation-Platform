from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class PromptPolicy:
    policy_name: str = "deferred_ai_boundary"
    allow_external_execution: bool = False
    allow_prompt_secrets: bool = False
    allow_live_network: bool = False
    allow_training: bool = False
    local_only: bool = True
    require_explicit_review: bool = True


def default_prompt_policy() -> PromptPolicy:
    return PromptPolicy()


def validate_prompt_metadata(
    metadata: Mapping[str, Any],
    *,
    policy: PromptPolicy | None = None,
) -> dict[str, Any]:
    active_policy = policy or default_prompt_policy()
    issues: list[str] = []

    prompt_name = str(metadata.get("prompt_name") or metadata.get("name") or "").strip()
    purpose = str(metadata.get("purpose") or "").strip()
    if not prompt_name:
        issues.append("missing_prompt_name")
    if not purpose:
        issues.append("missing_purpose")
    if bool(metadata.get("allow_external_execution")) or bool(metadata.get("allow_live_network")):
        issues.append("external_execution_disabled")
    if bool(metadata.get("allow_prompt_secrets")):
        issues.append("prompt_secrets_disabled")
    if bool(metadata.get("allow_training")):
        issues.append("training_disabled")

    return {
        "ok": not issues,
        "status": "approved" if not issues else "rejected",
        "policy_name": active_policy.policy_name,
        "prompt_name": prompt_name,
        "purpose": purpose,
        "local_only": True,
        "can_execute": False,
        "can_call_network": False,
        "can_train": False,
        "issues": issues,
    }
