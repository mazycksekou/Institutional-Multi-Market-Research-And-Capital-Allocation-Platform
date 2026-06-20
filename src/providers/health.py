from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(slots=True)
class ProviderHealthStatus:
    provider_id: str
    provider_name: str = ""
    provider_type: str = ""
    status: str = "scaffold_only"
    enabled: bool = False
    live_calls_enabled: bool = False
    dry_run: bool = True
    checked_at: str = "scaffold_only"
    blockers: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "status": self.status,
            "enabled": self.enabled,
            "live_calls_enabled": self.live_calls_enabled,
            "dry_run": self.dry_run,
            "checked_at": self.checked_at,
            "blockers": list(self.blockers),
            "details": dict(self.details),
        }


def build_scaffold_health_status(
    provider_id: str,
    *,
    provider_name: str = "",
    provider_type: str = "",
    blockers: Iterable[str] | None = None,
) -> ProviderHealthStatus:
    return ProviderHealthStatus(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_type=provider_type,
        status="scaffold_only",
        blockers=tuple(str(blocker) for blocker in (blockers or ())),
    )
