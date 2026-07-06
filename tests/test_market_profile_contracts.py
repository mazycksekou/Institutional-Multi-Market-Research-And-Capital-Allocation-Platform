from __future__ import annotations

import builtins
import importlib
from pathlib import Path

import pytest

from src.data.market_profile_contracts import MarketProfileContract, validate_market_profile_contract
from src.data.market_profile_registry import MarketProfileRegistry
from src.market_intelligence import market_profiles


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"


def test_market_profile_catalog_exposes_required_families() -> None:
    catalog = market_profiles.build_market_profile_catalog()
    profile_ids = {profile.profile_id for profile in catalog}

    assert {"sports", "prediction_markets", "options_0dte", "sports:nfl"}.issubset(profile_ids)
    assert market_profiles.SPORTS_PROFILE.profile_family == "sports"
    assert market_profiles.PREDICTION_MARKET_PROFILE.profile_family == "prediction_markets"
    assert market_profiles.OPTIONS_0DTE_PROFILE.profile_family == "options_0dte"
    assert market_profiles.NFL_AS_SPORTS_PROFILE_INSTANCE.profile_family == "sports"


def test_market_profile_contracts_validate_required_dimensions() -> None:
    for profile in market_profiles.build_market_profile_catalog():
        validation = validate_market_profile_contract(profile)
        assert validation["ok"], validation["errors"]
        assert isinstance(validation["profile"], MarketProfileContract)
        assert profile.canonical_identifiers
        assert profile.required_timestamps
        assert profile.canonical_fields
        assert profile.storage_requirements
        assert profile.backtest_requirements
        assert profile.worldview_permissions


def test_nfl_instance_is_the_sports_profile_instance() -> None:
    nfl_profile = market_profiles.NFL_AS_SPORTS_PROFILE_INSTANCE

    assert nfl_profile.profile_family == "sports"
    assert nfl_profile.profile_id == "sports:nfl"
    assert nfl_profile.market_scope == "americanfootball_nfl"
    assert "league" in nfl_profile.canonical_fields
    assert "game_id" in nfl_profile.canonical_identifiers
    assert "QB fields" in nfl_profile.atomic_feature_groups


def test_duplicate_profile_ids_are_rejected() -> None:
    registry = MarketProfileRegistry()
    registry.register(market_profiles.SPORTS_PROFILE)

    duplicate = market_profiles.SPORTS_PROFILE.with_metadata(label="duplicate")
    with pytest.raises(ValueError, match="duplicate market profile id"):
        registry.register(duplicate)


def test_framework_imports_do_not_pull_provider_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def guarded_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):  # type: ignore[no-untyped-def]
        if name.startswith("src.providers"):
            raise AssertionError(f"unexpected provider import: {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    reloaded = importlib.reload(market_profiles)

    assert reloaded.SPORTS_PROFILE.profile_id == "sports"
    assert reloaded.NFL_AS_SPORTS_PROFILE_INSTANCE.market_scope == "americanfootball_nfl"


def test_framework_modules_live_under_src() -> None:
    import src.data.market_profile_contracts as contracts_module
    import src.data.market_profile_registry as registry_module

    module_paths = {
        contracts_module.__file__,
        registry_module.__file__,
        market_profiles.__file__,
    }

    for module_path in module_paths:
        resolved = Path(module_path).resolve()
        assert resolved.is_relative_to(SRC_ROOT), resolved

