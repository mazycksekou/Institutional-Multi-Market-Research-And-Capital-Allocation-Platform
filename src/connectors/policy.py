from __future__ import annotations

from dataclasses import dataclass

from .contracts import CONNECTOR_CATEGORIES


@dataclass(frozen=True)
class ConnectorPolicy:
    allow_live_access: bool = False
    allow_credentials: bool = False
    allow_scraping: bool = False
    allow_websocket: bool = False
    allowed_categories: tuple[str, ...] = CONNECTOR_CATEGORIES
    notes: tuple[str, ...] = ()


def build_scaffold_connector_policy() -> ConnectorPolicy:
    return ConnectorPolicy()


def assert_connector_boundary(policy: ConnectorPolicy) -> None:
    if policy.allow_live_access or policy.allow_credentials or policy.allow_scraping or policy.allow_websocket:
        raise ValueError("connector boundary is scaffold-only")
