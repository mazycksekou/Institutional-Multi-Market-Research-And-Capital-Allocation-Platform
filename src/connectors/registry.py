from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .contracts import ConnectorContract


@dataclass
class ConnectorRegistry:
    _contracts: dict[str, ConnectorContract] = field(default_factory=dict)

    def register(self, contract: ConnectorContract) -> ConnectorContract:
        self._contracts[contract.name] = contract
        return contract

    def get(self, name: str) -> ConnectorContract | None:
        return self._contracts.get(name)

    def list(self) -> tuple[ConnectorContract, ...]:
        return tuple(self._contracts.values())

    def clear(self) -> None:
        self._contracts.clear()


_DEFAULT_REGISTRY = ConnectorRegistry()


def create_connector_registry(contracts: Iterable[ConnectorContract] = ()) -> ConnectorRegistry:
    registry = ConnectorRegistry()
    for contract in contracts:
        registry.register(contract)
    return registry


def get_connector_registry() -> ConnectorRegistry:
    return _DEFAULT_REGISTRY
