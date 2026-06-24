"""Disabled broker credential descriptors and policy helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .contracts import DisabledBrokerageError


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class BrokerCredentialDescriptor:
    """Local metadata descriptor describing future broker credentials."""

    broker_name: str
    credential_name: str
    environment_variable: str | None = None
    secret_source: str = "disabled"
    required: bool = True
    live_trading_allowed: bool = False
    import_time_reads_blocked: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerCredentialPolicy:
    """Disabled policy describing what broker credentials will be needed later."""

    broker_name: str
    required_credentials: tuple[str, ...] = ()
    credential_sources: tuple[str, ...] = ()
    rotation_required: bool = True
    import_time_reads_blocked: bool = True
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_credentials"] = list(self.required_credentials)
        payload["credential_sources"] = list(self.credential_sources)
        payload["metadata"] = dict(self.metadata)
        return payload


class DisabledBrokerCredentialError(DisabledBrokerageError):
    """Raised when broker credential validation is attempted against the disabled boundary."""


def _coerce_descriptor(
    credential: BrokerCredentialDescriptor | Mapping[str, Any] | None,
) -> BrokerCredentialDescriptor | None:
    if credential is None:
        return None
    if isinstance(credential, BrokerCredentialDescriptor):
        return credential
    if not isinstance(credential, Mapping):
        return None
    return BrokerCredentialDescriptor(
        broker_name=str(credential.get("broker_name") or credential.get("broker") or credential.get("provider") or "unknown"),
        credential_name=str(credential.get("credential_name") or credential.get("name") or "unknown"),
        environment_variable=credential.get("environment_variable") or credential.get("env_var"),
        secret_source=str(credential.get("secret_source") or "disabled"),
        required=bool(credential.get("required", True)),
        live_trading_allowed=bool(credential.get("live_trading_allowed", False)),
        import_time_reads_blocked=bool(credential.get("import_time_reads_blocked", True)),
        metadata=dict(credential.get("metadata") or {k: v for k, v in credential.items() if v is not None}),
    )


def _coerce_policy(policy: BrokerCredentialPolicy | Mapping[str, Any] | None) -> BrokerCredentialPolicy | None:
    if policy is None:
        return None
    if isinstance(policy, BrokerCredentialPolicy):
        return policy
    if not isinstance(policy, Mapping):
        return None
    required = policy.get("required_credentials") or policy.get("required_credential_names") or ()
    sources = policy.get("credential_sources") or policy.get("sources") or ()
    return BrokerCredentialPolicy(
        broker_name=str(policy.get("broker_name") or policy.get("broker") or policy.get("provider") or "unknown"),
        required_credentials=tuple(str(item) for item in required if item is not None),
        credential_sources=tuple(str(item) for item in sources if item is not None),
        rotation_required=bool(policy.get("rotation_required", True)),
        import_time_reads_blocked=bool(policy.get("import_time_reads_blocked", True)),
        live_trading_allowed=bool(policy.get("live_trading_allowed", False)),
        metadata=dict(policy.get("metadata") or {k: v for k, v in policy.items() if v is not None}),
    )


def validate_broker_credentials_disabled(
    credential: BrokerCredentialDescriptor | Mapping[str, Any] | None = None,
    *,
    policy: BrokerCredentialPolicy | Mapping[str, Any] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    descriptor = _coerce_descriptor(credential)
    policy_descriptor = _coerce_policy(policy)
    broker_name = descriptor.broker_name if descriptor is not None else (policy_descriptor.broker_name if policy_descriptor is not None else "unknown")
    credential_name = descriptor.credential_name if descriptor is not None else "unknown"
    message = reason or "broker credential validation is disabled until live trading approval is explicitly granted"
    raise DisabledBrokerCredentialError(
        f"{message}; broker={broker_name}; credential_name={credential_name}; credential_policy={bool(policy_descriptor is not None)}"
    )


__all__ = [
    "BrokerCredentialDescriptor",
    "BrokerCredentialPolicy",
    "DisabledBrokerCredentialError",
    "validate_broker_credentials_disabled",
]
