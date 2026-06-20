from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .categories import (
    category_package_name,
    normalize_provider_category,
    provider_category_from_mapping,
    provider_category_from_provider_type,
)

CATEGORY_DEFAULT_PROVIDER_IDS: dict[str, str] = {
    "prediction_markets": "prediction_market_placeholder",
    "sportsbooks": "sportsbook_placeholder",
    "zero_dte_stocks": "zero_dte_stock_placeholder",
}


def provider_category_from_provider_id(provider_id: str | None) -> str | None:
    if provider_id is None:
        return None
    normalized = str(provider_id).strip().lower()
    if not normalized:
        return None
    return normalize_provider_category(normalized)


def resolve_provider_category(
    provider_id: str | None = None,
    provider_type: str | None = None,
    *,
    provider: Mapping[str, Any] | None = None,
) -> str | None:
    if provider is not None:
        category = provider_category_from_mapping(provider)
        if category is not None:
            return category
    category = provider_category_from_provider_type(provider_type)
    if category is not None:
        return category
    return provider_category_from_provider_id(provider_id)


def provider_route_package(
    provider_id: str | None = None,
    provider_type: str | None = None,
    *,
    provider: Mapping[str, Any] | None = None,
) -> str | None:
    category = resolve_provider_category(provider_id, provider_type, provider=provider)
    if category is None:
        return None
    return category_package_name(category)


def build_category_route_map(provider_ids: Iterable[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORY_DEFAULT_PROVIDER_IDS}
    for provider_id in provider_ids:
        category = provider_category_from_provider_id(provider_id)
        if category is None:
            continue
        grouped.setdefault(category, []).append(provider_id)
    return grouped


def default_provider_id_for_category(category: str | None, *, default_provider_id: str | None = None) -> str:
    normalized = normalize_provider_category(category)
    if normalized is None:
        raise ValueError(f"unknown provider_category: {category}")
    if default_provider_id:
        return default_provider_id
    return CATEGORY_DEFAULT_PROVIDER_IDS[normalized]


def category_route_summary(
    provider_id: str | None = None,
    provider_type: str | None = None,
    *,
    provider: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    category = resolve_provider_category(provider_id, provider_type, provider=provider)
    return {
        "provider_id": provider_id,
        "provider_type": provider_type,
        "provider_category": category,
        "provider_package": category_package_name(category) if category else None,
    }


__all__ = [
    "CATEGORY_DEFAULT_PROVIDER_IDS",
    "build_category_route_map",
    "category_route_summary",
    "default_provider_id_for_category",
    "provider_category_from_provider_id",
    "provider_route_package",
    "resolve_provider_category",
]
