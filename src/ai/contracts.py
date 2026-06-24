from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AIPromptMetadata:
    prompt_name: str
    purpose: str
    variables: tuple[str, ...] = ()
    model: str = "disabled"
    provider: str = "disabled"
    local_only: bool = True
    can_execute: bool = False


@dataclass(frozen=True, slots=True)
class AIRequestDescriptor:
    request_id: str
    prompt_name: str
    provider: str = "disabled"
    model: str = "disabled"
    local_only: bool = True
    can_execute: bool = False
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class AIReadinessSnapshot:
    enabled: bool
    status: str
    reason: str
    provider: str = "disabled"
    model: str = "disabled"
    local_only: bool = True


def build_prompt_metadata(
    prompt_name: str,
    purpose: str,
    *,
    variables: tuple[str, ...] = (),
    model: str = "disabled",
    provider: str = "disabled",
) -> AIPromptMetadata:
    return AIPromptMetadata(
        prompt_name=str(prompt_name or "").strip(),
        purpose=str(purpose or "").strip(),
        variables=tuple(str(item).strip() for item in variables if str(item).strip()),
        model=str(model or "disabled").strip() or "disabled",
        provider=str(provider or "disabled").strip() or "disabled",
    )


def build_ai_request_descriptor(
    request_id: str,
    prompt_name: str,
    *,
    provider: str = "disabled",
    model: str = "disabled",
    metadata: Mapping[str, Any] | None = None,
) -> AIRequestDescriptor:
    items = tuple(
        (str(key), str(value))
        for key, value in sorted(dict(metadata or {}).items(), key=lambda item: str(item[0]))
    )
    return AIRequestDescriptor(
        request_id=str(request_id or "").strip(),
        prompt_name=str(prompt_name or "").strip(),
        provider=str(provider or "disabled").strip() or "disabled",
        model=str(model or "disabled").strip() or "disabled",
        metadata=items,
    )
