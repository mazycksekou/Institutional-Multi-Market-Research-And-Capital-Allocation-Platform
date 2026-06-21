from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class OddsDataSourceProfile:
    provider: str = "odds_data"
    read_only: bool = True
    live_access_enabled: bool = False
    legacy_aliases: tuple[str, ...] = ("legacy_odds_vendor_a", "legacy_odds_vendor_b", "legacy_odds_vendor_c")
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "live_access_enabled": self.live_access_enabled,
            "legacy_aliases": list(self.legacy_aliases),
            "credential_names": list(self.credential_names),
            "metadata": dict(self.metadata),
        }


def build_odds_data_source_profile(
    *,
    provider: str = "odds_data",
    read_only: bool = True,
    live_access_enabled: bool = False,
    legacy_aliases: tuple[str, ...] = ("legacy_odds_vendor_a", "legacy_odds_vendor_b", "legacy_odds_vendor_c"),
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    ),
    metadata: Mapping[str, Any] | None = None,
) -> OddsDataSourceProfile:
    return OddsDataSourceProfile(
        provider=provider,
        read_only=read_only,
        live_access_enabled=live_access_enabled,
        legacy_aliases=legacy_aliases,
        credential_names=credential_names,
        metadata={} if metadata is None else dict(metadata),
    )
