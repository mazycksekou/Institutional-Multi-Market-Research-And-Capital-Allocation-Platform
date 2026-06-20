from __future__ import annotations

from typing import Any, Mapping

PROVIDER_CATEGORIES = (
    "prediction_markets",
    "sportsbooks",
    "zero_dte_stocks",
)

PROVIDER_CATEGORY_TO_PROVIDER_TYPES: dict[str, tuple[str, ...]] = {
    "prediction_markets": ("prediction_market",),
    "sportsbooks": ("sportsbook_odds", "player_props"),
    "zero_dte_stocks": ("stock_price", "stock_fundamentals"),
}

PROVIDER_CATEGORY_TO_PACKAGE: dict[str, str] = {
    "prediction_markets": "src.providers.prediction_markets",
    "sportsbooks": "src.providers.sportsbooks",
    "zero_dte_stocks": "src.providers.zero_dte_stocks",
}


def normalize_provider_category(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower().replace("-", "_")
    return normalized if normalized in PROVIDER_CATEGORIES else None


def provider_category_from_provider_type(provider_type: str | None) -> str | None:
    if provider_type is None:
        return None
    normalized = str(provider_type).strip().lower().replace("-", "_")
    normalized_category = normalize_provider_category(normalized)
    if normalized_category is not None:
        return normalized_category
    for category, provider_types in PROVIDER_CATEGORY_TO_PROVIDER_TYPES.items():
        if normalized in provider_types:
            return category
    return None


def provider_category_from_mapping(mapping: Mapping[str, Any] | None) -> str | None:
    if mapping is None:
        return None
    category = provider_category_from_provider_type(mapping.get("provider_type"))
    if category is not None:
        return category
    return normalize_provider_category(mapping.get("provider_category"))


def category_provider_types(category: str | None) -> tuple[str, ...]:
    normalized = normalize_provider_category(category)
    if normalized is None:
        raise ValueError(f"unknown provider_category: {category}")
    return PROVIDER_CATEGORY_TO_PROVIDER_TYPES[normalized]


def category_package_name(category: str | None) -> str:
    normalized = normalize_provider_category(category)
    if normalized is None:
        raise ValueError(f"unknown provider_category: {category}")
    return PROVIDER_CATEGORY_TO_PACKAGE[normalized]


def is_supported_provider_category(category: str | None) -> bool:
    return normalize_provider_category(category) is not None


__all__ = [
    "PROVIDER_CATEGORIES",
    "PROVIDER_CATEGORY_TO_PACKAGE",
    "PROVIDER_CATEGORY_TO_PROVIDER_TYPES",
    "category_package_name",
    "category_provider_types",
    "is_supported_provider_category",
    "normalize_provider_category",
    "provider_category_from_mapping",
    "provider_category_from_provider_type",
]
