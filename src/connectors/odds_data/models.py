from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class OddsDataRecord:
    provider: str
    sport: str = ""
    league: str = ""
    event_id: str = ""
    market: str = ""
    selection: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OddsDataSnapshot:
    provider: str = "odds_data"
    records: tuple[OddsDataRecord, ...] = ()
    status: str = "inert"
    read_only: bool = True


@dataclass(frozen=True)
class OddsDataConnectorStatus:
    provider: str = "odds_data"
    status: str = "disabled"
    read_only: bool = True
    live_access_enabled: bool = False
    message: str = "connector wrapper is inert until live access is explicitly authorized"
