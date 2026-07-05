"""Scaffold-only AI boundary package."""

from .contracts import AIReadinessSnapshot, AIRequestDescriptor, AIPromptMetadata, build_ai_request_descriptor, build_prompt_metadata
from .disabled_client import AIExecutionDisabledError, DisabledAIClient
from .prompt_policy import PromptPolicy, default_prompt_policy, validate_prompt_metadata
from .readiness import build_ai_readiness, get_ai_readiness

__all__ = [
    "AIExecutionDisabledError",
    "AIReadinessSnapshot",
    "AIRequestDescriptor",
    "AIPromptMetadata",
    "DisabledAIClient",
    "PromptPolicy",
    "build_ai_readiness",
    "build_ai_request_descriptor",
    "build_prompt_metadata",
    "default_prompt_policy",
    "get_ai_readiness",
    "validate_prompt_metadata",
]
