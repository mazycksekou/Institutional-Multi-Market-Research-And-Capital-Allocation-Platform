"""Disabled live-trading kill-switch scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class KillSwitchState:
    """Metadata-only kill-switch state for live trading."""

    kill_switch_id: str
    clear: bool = False
    status: str = "blocked"
    reason: str = "live_trading_disabled"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


class KillSwitchTriggeredError(RuntimeError):
    """Raised when the kill switch blocks live activation."""


def build_default_kill_switch_state() -> KillSwitchState:
    """Return the default blocked kill-switch posture."""

    return KillSwitchState(
        kill_switch_id="default_live_trading_kill_switch",
        clear=False,
        status="blocked",
        reason="live_trading_disabled",
    )


def require_kill_switch_clear(kill_switch_state: KillSwitchState | dict[str, Any] | None = None) -> KillSwitchState:
    """Require a local kill-switch state to be clear before future activation."""

    state = kill_switch_state if isinstance(kill_switch_state, KillSwitchState) else build_default_kill_switch_state() if kill_switch_state is None else KillSwitchState(
        kill_switch_id=str(kill_switch_state.get("kill_switch_id") or "live_trading_kill_switch"),
        clear=bool(kill_switch_state.get("clear", False)),
        status=str(kill_switch_state.get("status") or ("clear" if bool(kill_switch_state.get("clear", False)) else "blocked")),
        reason=str(kill_switch_state.get("reason") or "live_trading_disabled"),
        metadata=dict(kill_switch_state.get("metadata") or {k: v for k, v in kill_switch_state.items() if v is not None}),
    )
    if not state.clear:
        raise KillSwitchTriggeredError(f"kill switch remains engaged; status={state.status}; reason={state.reason}")
    return state


__all__ = [
    "KillSwitchState",
    "KillSwitchTriggeredError",
    "build_default_kill_switch_state",
    "require_kill_switch_clear",
]
