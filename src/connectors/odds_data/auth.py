from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OddsDataAuthRequirement:
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    )
    live_access_enabled: bool = False
    description: str = "credential names are declared only; secrets are never read at import time"

    def describe(self) -> dict[str, object]:
        return {
            "credential_names": list(self.credential_names),
            "live_access_enabled": self.live_access_enabled,
            "description": self.description,
        }


def build_odds_data_auth_requirement(
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    ),
    *,
    live_access_enabled: bool = False,
) -> OddsDataAuthRequirement:
    return OddsDataAuthRequirement(
        credential_names=credential_names,
        live_access_enabled=live_access_enabled,
    )
