"""Kill-switch governance policy scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


def _to_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        candidate = value.as_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    payload: dict[str, Any] = {}
    for name in ("name", "required", "satisfied", "description", "metadata", "rule_id", "override_id", "reason", "status", "clear"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class KillSwitchRule:
    """Metadata-only kill-switch rule."""

    name: str
    required: bool = True
    satisfied: bool = False
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class KillSwitchOverride:
    """Metadata-only kill-switch override record."""

    override_id: str
    reason: str = "override_metadata_only"
    requested_clear: bool = False
    approved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class KillSwitchPolicy:
    """Local kill-switch policy metadata."""

    policy_id: str
    rules: tuple[KillSwitchRule, ...] = ()
    overrides: tuple[KillSwitchOverride, ...] = ()
    status: str = "blocked"
    live_trading_allowed: bool = False
    blocked: bool = True
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rules"] = [item.as_dict() for item in self.rules]
        payload["overrides"] = [item.as_dict() for item in self.overrides]
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class KillSwitchDecision:
    """Evaluation result for the kill-switch policy."""

    decision_id: str
    policy: KillSwitchPolicy
    override: KillSwitchOverride | None = None
    approved: bool = False
    status: str = "blocked"
    blocked_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    live_trading_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["policy"] = self.policy.as_dict()
        payload["override"] = self.override.as_dict() if self.override is not None else None
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def _coerce_rule(item: KillSwitchRule | Mapping[str, Any] | str) -> KillSwitchRule:
    if isinstance(item, KillSwitchRule):
        return item
    payload = _to_payload(item)
    if isinstance(item, str):
        payload.setdefault("name", item)
    return KillSwitchRule(
        name=str(payload.get("name") or payload.get("rule_id") or "unknown"),
        required=bool(payload.get("required", True)),
        satisfied=bool(payload.get("satisfied", False)),
        description=str(payload.get("description") or ""),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_override(item: KillSwitchOverride | Mapping[str, Any] | None) -> KillSwitchOverride | None:
    if item is None:
        return None
    if isinstance(item, KillSwitchOverride):
        return item
    payload = _to_payload(item)
    return KillSwitchOverride(
        override_id=str(payload.get("override_id") or "kill_switch_override"),
        reason=str(payload.get("reason") or "override_metadata_only"),
        requested_clear=bool(payload.get("requested_clear", False)),
        approved=bool(payload.get("approved", False)),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def _coerce_policy(policy: KillSwitchPolicy | Mapping[str, Any] | None) -> KillSwitchPolicy:
    if isinstance(policy, KillSwitchPolicy):
        return policy
    payload = _to_payload(policy)
    rules = payload.get("rules")
    overrides = payload.get("overrides")
    rule_items = tuple(_coerce_rule(item) for item in rules) if isinstance(rules, Sequence) and not isinstance(rules, (str, bytes)) else ()
    override_items = tuple(_coerce_override(item) for item in overrides) if isinstance(overrides, Sequence) and not isinstance(overrides, (str, bytes)) else ()
    if not rule_items:
        rule_items = (
            KillSwitchRule(name="block_everything", description="The kill switch blocks all live execution by default."),
            KillSwitchRule(name="authoritative_block", description="The kill switch remains authoritative in this phase."),
        )
    return KillSwitchPolicy(
        policy_id=str(payload.get("policy_id") or "kill_switch_policy_default"),
        rules=rule_items,
        overrides=override_items,
        status=str(payload.get("status") or "blocked"),
        live_trading_allowed=bool(payload.get("live_trading_allowed", False)),
        blocked=bool(payload.get("blocked", True)),
        warnings=_coerce_text_tuple(payload.get("warnings")),
        metadata=dict(payload.get("metadata") or {k: v for k, v in payload.items() if v is not None}),
    )


def build_default_policy(*, metadata: Mapping[str, Any] | None = None) -> KillSwitchPolicy:
    """Return the default block-everything kill-switch policy."""

    return KillSwitchPolicy(
        policy_id="kill_switch_policy_default",
        rules=(
            KillSwitchRule(name="block_everything", description="The kill switch blocks all live execution by default."),
            KillSwitchRule(name="authoritative_block", description="The kill switch remains authoritative in this phase."),
        ),
        overrides=(),
        status="blocked",
        live_trading_allowed=False,
        blocked=True,
        warnings=("kill_switch_policy_remains_blocking_in_this_phase",),
        metadata=dict(metadata or {}),
    )


def evaluate_policy(
    kill_switch_policy: KillSwitchPolicy | Mapping[str, Any] | None = None,
    *,
    override: KillSwitchOverride | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> KillSwitchDecision:
    """Evaluate the kill-switch policy locally without enabling trading."""

    policy = _coerce_policy(kill_switch_policy)
    override_item = _coerce_override(override)
    rule_items = tuple(_coerce_rule(item) for item in policy.rules)
    blockers = ["kill_switch_authoritative", "live_trading_disabled"]
    if override_item is not None:
        blockers.append("override_cannot_enable_trading")
        if override_item.requested_clear:
            blockers.append("requested_clear_recorded_but_not_effective")
    if any(item.required and not item.satisfied for item in rule_items):
        blockers.append("unsatisfied_kill_switch_rules")
    status = "blocked" if override_item is None else "blocked_override_recorded"
    return KillSwitchDecision(
        decision_id=f"{policy.policy_id}:decision",
        policy=policy,
        override=override_item,
        approved=False,
        status=status,
        blocked_reasons=tuple(dict.fromkeys(blockers)),
        warnings=("kill_switch_override_remains_metadata_only",),
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "KillSwitchDecision",
    "KillSwitchOverride",
    "KillSwitchPolicy",
    "KillSwitchRule",
    "build_default_policy",
    "evaluate_policy",
]
