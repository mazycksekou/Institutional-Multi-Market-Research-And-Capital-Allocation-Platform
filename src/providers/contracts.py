from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

PROVIDER_SCHEMA_VERSION = "src.providers.skeleton.v1"


def _as_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (list, tuple, set)):
        return tuple(str(value) for value in values)
    if isinstance(values, str):
        return (values,)
    return (str(values),)


@dataclass(slots=True)
class ProviderContract:
    provider_id: str
    provider_name: str = ""
    provider_type: str = "unknown"
    enabled: bool = False
    dry_run: bool = True
    supports_streaming: bool = False
    supports_polling: bool = True
    min_poll_seconds: int = 60
    required_credentials: tuple[str, ...] = ()
    supported_markets: tuple[str, ...] = ()
    live_calls_enabled: bool = False
    contract_status: str = "scaffold_only"
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = PROVIDER_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ProviderContract":
        return cls(
            provider_id=str(data.get("provider_id") or ""),
            provider_name=str(data.get("provider_name") or ""),
            provider_type=str(data.get("provider_type") or "unknown"),
            enabled=bool(data.get("enabled", False)),
            dry_run=bool(data.get("dry_run", True)),
            supports_streaming=bool(data.get("supports_streaming", False)),
            supports_polling=bool(data.get("supports_polling", True)),
            min_poll_seconds=max(1, int(data.get("min_poll_seconds", 60))),
            required_credentials=_as_tuple(data.get("required_credentials")),
            supported_markets=_as_tuple(data.get("supported_markets")),
            live_calls_enabled=bool(data.get("live_calls_enabled", False)),
            contract_status=str(data.get("contract_status") or "scaffold_only"),
            metadata=dict(data.get("metadata") or {}),
            schema_version=str(data.get("schema_version") or PROVIDER_SCHEMA_VERSION),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "supports_streaming": self.supports_streaming,
            "supports_polling": self.supports_polling,
            "min_poll_seconds": self.min_poll_seconds,
            "required_credentials": list(self.required_credentials),
            "supported_markets": list(self.supported_markets),
            "live_calls_enabled": self.live_calls_enabled,
            "contract_status": self.contract_status,
            "metadata": dict(self.metadata),
            "schema_version": self.schema_version,
        }


def build_scaffold_provider_contract(
    provider_id: str,
    provider_name: str = "",
    provider_type: str = "unknown",
) -> ProviderContract:
    return ProviderContract(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_type=provider_type,
        contract_status="scaffold_only",
    )
