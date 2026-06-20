from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..base import ProviderAdapterBase
from ..contracts import ProviderContract
from ..health import build_scaffold_health_status
from ..validation import validate_provider_payload
from .contracts import build_zero_dte_stock_provider_contract
from .models import ZeroDteStockQuote

ZERO_DTE_STOCK_PROVIDER_TYPE = "stock_price"


def normalize_zero_dte_stock_quote(payload: Mapping[str, Any], *, provider: str = "zero_dte_stocks") -> dict[str, Any]:
    return ZeroDteStockQuote.from_mapping(payload, provider=provider).as_dict()


def build_zero_dte_stock_quote(payload: Mapping[str, Any], *, provider: str = "zero_dte_stocks") -> ZeroDteStockQuote:
    return ZeroDteStockQuote.from_mapping(payload, provider=provider)


class ZeroDteStockProviderAdapter(ProviderAdapterBase):
    def __init__(self, contract: ProviderContract | Mapping[str, Any] | None = None) -> None:
        super().__init__(contract or build_zero_dte_stock_provider_contract())

    def build_quote(self, payload: Mapping[str, Any], *, provider: str | None = None) -> ZeroDteStockQuote:
        return build_zero_dte_stock_quote(payload, provider=provider or "zero_dte_stocks")

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_zero_dte_stock_quote(payload, provider="zero_dte_stocks")

    def validate_payload(self, payload: Mapping[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        return validate_provider_payload(
            ZERO_DTE_STOCK_PROVIDER_TYPE,
            dict(payload),
            max_staleness_seconds=max_staleness_seconds,
        )

    def health_check(self) -> dict[str, Any]:
        return build_scaffold_health_status(
            self.contract.provider_id,
            provider_name=self.contract.provider_name,
            provider_type=self.contract.provider_type,
            blockers=("read_only_category_adapter",),
        ).as_dict()


__all__ = [
    "ZERO_DTE_STOCK_PROVIDER_TYPE",
    "ZeroDteStockProviderAdapter",
    "ZeroDteStockQuote",
    "build_zero_dte_stock_quote",
    "normalize_zero_dte_stock_quote",
]
