from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .contracts import ProviderContract
from .errors import ProviderConfigurationError


@dataclass(slots=True)
class ProviderRegistry:
    _contracts: dict[str, ProviderContract] = field(default_factory=dict)

    def register(self, contract: ProviderContract | Mapping[str, Any]) -> ProviderContract:
        normalized = contract if isinstance(contract, ProviderContract) else ProviderContract.from_mapping(contract)
        if not normalized.provider_id:
            raise ProviderConfigurationError("provider_id is required")
        self._contracts[normalized.provider_id] = normalized
        return normalized

    def get(self, provider_id: str) -> ProviderContract | None:
        return self._contracts.get(str(provider_id))

    def list(self) -> list[ProviderContract]:
        return list(self._contracts.values())

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {provider_id: contract.as_dict() for provider_id, contract in self._contracts.items()}

    def clear(self) -> None:
        self._contracts.clear()

    def is_empty(self) -> bool:
        return not self._contracts

    def __len__(self) -> int:
        return len(self._contracts)

    def __contains__(self, provider_id: object) -> bool:
        return str(provider_id) in self._contracts


def create_provider_registry() -> ProviderRegistry:
    return ProviderRegistry()
