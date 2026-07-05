"""Metadata-only rollback plan scaffold for future live activation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class RollbackPlan:
    """Local metadata describing a future rollback plan."""

    rollback_id: str
    reason: str = "live_trading_deferred"
    steps: tuple[str, ...] = ()
    status: str = "metadata_only"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = list(self.steps)
        payload["metadata"] = dict(self.metadata)
        return payload


def build_rollback_plan(
    *,
    rollback_id: str = "rollback_plan_default",
    reason: str = "live_trading_deferred",
    steps: tuple[str, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> RollbackPlan:
    """Build a metadata-only rollback plan."""

    return RollbackPlan(
        rollback_id=rollback_id,
        reason=reason,
        steps=tuple(str(step) for step in steps),
        metadata=dict(metadata or {}),
    )


__all__ = [
    "RollbackPlan",
    "build_rollback_plan",
]
