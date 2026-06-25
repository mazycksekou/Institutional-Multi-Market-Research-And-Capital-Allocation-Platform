from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

SPORT_FEATURE_PACKS_VERSION = "src.market_intelligence.feature_packs.v1"
MARKET_FEATURE_PACKS_VERSION = "src.market_intelligence.feature_packs.v1"


def _legacy_sport_module():
    from automation_scheduler import sport_feature_packs as legacy_sport_feature_packs

    return legacy_sport_feature_packs


def _legacy_market_module():
    from automation_scheduler import market_feature_packs as legacy_market_feature_packs

    return legacy_market_feature_packs


def normalize_sport_key(value: Any) -> str:
    return _legacy_sport_module().normalize_sport_key(value)


def normalize_market_family(
    market: Any,
    selection: Any | None = None,
    sport: Any | None = None,
) -> str:
    return _legacy_market_module().normalize_market_family(market, selection, sport)


def _field_presence(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[str, dict[str, Any]]:
    total_rows = len(rows)
    presence: dict[str, dict[str, Any]] = {}
    for field in fields:
        present = sum(1 for row in rows if row.get(field) not in (None, ""))
        missing = max(0, total_rows - present)
        coverage = round((present / total_rows * 100.0) if total_rows else 0.0, 1)
        presence[field] = {
            "present_count": present,
            "missing_count": missing,
            "coverage_percent": coverage,
        }
    return presence


def _pack_summary(
    *,
    key_name: str,
    key_value: str,
    family: str,
    required_fields: Sequence[str],
    recommended_fields: Sequence[str],
) -> dict[str, Any]:
    return {
        "ok": True,
        "version": SPORT_FEATURE_PACKS_VERSION,
        key_name: key_value,
        "sport_family": family,
        "display_name": key_value.replace("_", " ").title(),
        "depth_level": 1 if key_value else 0,
        "required_fields": list(required_fields),
        "recommended_fields": list(recommended_fields),
        "missing_data_warning": "",
        "operator_interpretation": (
            f"Local feature pack for {key_value or family}. "
            "Readiness is evaluated using deterministic local coverage only."
        ),
    }


def get_sport_feature_pack(sport: Any | None) -> dict[str, Any]:
    return _legacy_sport_module().get_sport_feature_pack(sport)


def evaluate_sport_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
    sport: Any | None = None,
    *,
    min_required_coverage_percent: float = 80.0,
    min_recommended_coverage_percent: float = 60.0,
) -> dict[str, Any]:
    return _legacy_sport_module().evaluate_sport_feature_readiness(rows, sport)


def summarize_sport_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _legacy_sport_module().summarize_sport_feature_readiness(rows)


def get_market_feature_pack(
    market: Any | None,
    *,
    selection: Any | None = None,
    sport: Any | None = None,
) -> dict[str, Any]:
    return _legacy_market_module().get_market_feature_pack(
        market,
        selection=selection,
        sport=sport,
    )


def evaluate_market_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
    market: Any | None = None,
    *,
    selection: Any | None = None,
    sport: Any | None = None,
    min_required_coverage_percent: float = 80.0,
    min_recommended_coverage_percent: float = 60.0,
) -> dict[str, Any]:
    return _legacy_market_module().evaluate_market_feature_readiness(
        rows,
        market,
        selection=selection,
        sport=sport,
    )


def summarize_market_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _legacy_market_module().summarize_market_feature_readiness(rows)
