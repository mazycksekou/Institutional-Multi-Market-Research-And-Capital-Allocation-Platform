from __future__ import annotations

from typing import Any, Mapping


def normalize_provider_payload(provider_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a pure local copy of the payload for future provider normalization.

    The scaffold intentionally performs no network access, no credential lookups,
    and no legacy-provider delegation.
    """

    normalized = dict(payload)
    if provider_type and "provider_type" not in normalized:
        normalized["provider_type"] = provider_type
    return normalized
