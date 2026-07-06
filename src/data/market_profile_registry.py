from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .market_profile_contracts import MarketProfileContract, build_market_profile_contract, validate_market_profile_contract


@dataclass(slots=True)
class MarketProfileRegistry:
    _profiles: dict[str, MarketProfileContract] = field(default_factory=dict)

    def register(self, profile: MarketProfileContract | Mapping[str, object]) -> MarketProfileContract:
        contract = profile if isinstance(profile, MarketProfileContract) else build_market_profile_contract(profile)
        validation = validate_market_profile_contract(contract)
        if not validation["ok"]:
            raise ValueError("; ".join(validation["errors"]) or "market profile validation failed")
        profile_id = contract.profile_id
        if profile_id in self._profiles:
            raise ValueError(f"duplicate market profile id: {profile_id}")
        self._profiles[profile_id] = contract
        return contract

    def get(self, profile_id: str) -> MarketProfileContract | None:
        return self._profiles.get(str(profile_id).strip())

    def list(self) -> tuple[MarketProfileContract, ...]:
        return tuple(self._profiles[profile_id] for profile_id in sorted(self._profiles))

    def clear(self) -> None:
        self._profiles.clear()

    def extend(self, profiles: Iterable[MarketProfileContract | Mapping[str, object]]) -> None:
        for profile in profiles:
            self.register(profile)


DEFAULT_MARKET_PROFILE_REGISTRY = MarketProfileRegistry()


def register_market_profile(profile: MarketProfileContract | Mapping[str, object]) -> MarketProfileContract:
    return DEFAULT_MARKET_PROFILE_REGISTRY.register(profile)


def get_market_profile(profile_id: str) -> MarketProfileContract | None:
    return DEFAULT_MARKET_PROFILE_REGISTRY.get(profile_id)


def list_market_profiles() -> tuple[MarketProfileContract, ...]:
    return DEFAULT_MARKET_PROFILE_REGISTRY.list()


def reset_market_profile_registry() -> None:
    DEFAULT_MARKET_PROFILE_REGISTRY.clear()
