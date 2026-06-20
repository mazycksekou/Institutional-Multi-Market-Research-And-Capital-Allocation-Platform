from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from .contracts import ProviderContract, build_scaffold_provider_contract
from .errors import ProviderConfigurationError
from .health import ProviderHealthStatus, build_scaffold_health_status
from .normalization import normalize_provider_payload


@runtime_checkable
class ProviderAdapterProtocol(Protocol):
    contract: ProviderContract

    def get_capabilities(self) -> dict[str, Any]: ...

    def validate_config(self) -> dict[str, Any]: ...

    def health_check(self) -> dict[str, Any]: ...

    def fetch_snapshot(self) -> dict[str, Any]: ...

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]: ...

    def validate_payload(self, payload: Mapping[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]: ...


class ProviderAdapterBase:
    """Import-safe scaffold base for future provider adapters."""

    def __init__(self, contract: ProviderContract | Mapping[str, Any] | None = None) -> None:
        if contract is None:
            self.contract = build_scaffold_provider_contract("scaffold_provider")
        elif isinstance(contract, ProviderContract):
            self.contract = contract
        elif isinstance(contract, Mapping):
            self.contract = ProviderContract.from_mapping(contract)
        else:
            raise ProviderConfigurationError("provider_contract_invalid")

    def get_capabilities(self) -> dict[str, Any]:
        return self.contract.as_dict()

    def validate_config(self) -> dict[str, Any]:
        return {
            "ok": False,
            "status": "scaffold_only",
            "blockers": ["scaffold_only"],
        }

    def health_check(self) -> dict[str, Any]:
        return build_scaffold_health_status(
            self.contract.provider_id,
            provider_name=self.contract.provider_name,
            provider_type=self.contract.provider_type,
            blockers=("scaffold_only",),
        ).as_dict()

    def fetch_snapshot(self) -> dict[str, Any]:
        return {
            "provider_id": self.contract.provider_id,
            "provider_type": self.contract.provider_type,
            "status": "scaffold_only",
            "dry_run": True,
            "records": [],
            "blockers": ["scaffold_only"],
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_provider_payload(self.contract.provider_type, payload)

    def validate_payload(self, payload: Mapping[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        _ = (payload, max_staleness_seconds)
        return {
            "ok": False,
            "status": "scaffold_only",
            "errors": ["not_implemented"],
        }
