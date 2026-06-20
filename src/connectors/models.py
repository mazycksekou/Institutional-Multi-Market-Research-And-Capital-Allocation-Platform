from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ConnectorRequest:
    category: str
    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    source: str = "local"


@dataclass(frozen=True)
class ConnectorResponse:
    category: str
    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    status: str = "scaffold"
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConnectorHealthStatus:
    category: str
    name: str
    healthy: bool = False
    status: str = "scaffold"
    details: Mapping[str, Any] = field(default_factory=dict)
