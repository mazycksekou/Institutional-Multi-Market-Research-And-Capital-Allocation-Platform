from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from src.connectors.market_data.models import MarketDataQuote, MarketDataSnapshot

from ..base import ProviderAdapterBase
from ..contracts import ProviderContract
from ..errors import ProviderUnavailableError
from ..health import build_scaffold_health_status
from .contracts import build_zero_dte_stock_provider_contract
from .models import ZeroDteStockProviderStatus, ZeroDteStockQuote, ZeroDteStockSnapshot
from .normalization import (
    build_zero_dte_stock_quote,
    build_zero_dte_stock_snapshot,
    normalize_zero_dte_stock_payload,
    normalize_zero_dte_stock_quote,
    normalize_zero_dte_stock_snapshot,
    validate_zero_dte_stock_payload,
)

ZERO_DTE_STOCK_PROVIDER_TYPE = "stock_price"


class ZeroDteStockProvider(ProviderAdapterBase):
    def __init__(self, contract: ProviderContract | Mapping[str, Any] | None = None) -> None:
        super().__init__(contract or build_zero_dte_stock_provider_contract())
        self.provider_status = ZeroDteStockProviderStatus(
            provider=self.contract.provider_id,
            provider_type=self.contract.provider_type,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "provider_id": self.contract.provider_id,
            "provider_name": self.contract.provider_name,
            "provider_type": self.contract.provider_type,
            "read_only": True,
            "live_access_enabled": False,
            "status": self.provider_status.status,
        }

    def normalize_payload(self, payload: Any) -> dict[str, Any]:
        return normalize_zero_dte_stock_payload(payload, provider=self.contract.provider_id)

    def normalize_market_data_quote(self, payload: MarketDataQuote | Mapping[str, Any] | ZeroDteStockQuote) -> ZeroDteStockQuote:
        return build_zero_dte_stock_quote(payload, provider=self.contract.provider_id)

    def normalize_market_data_snapshot(
        self,
        payload: MarketDataSnapshot | Iterable[MarketDataQuote | Mapping[str, Any] | ZeroDteStockQuote] | ZeroDteStockSnapshot,
    ) -> ZeroDteStockSnapshot:
        if isinstance(payload, ZeroDteStockSnapshot):
            return payload
        if isinstance(payload, MarketDataSnapshot):
            return build_zero_dte_stock_snapshot(payload.records, provider=self.contract.provider_id)
        return build_zero_dte_stock_snapshot(payload, provider=self.contract.provider_id)

    def build_quote(self, payload: Any, *, provider: str | None = None) -> ZeroDteStockQuote:
        return build_zero_dte_stock_quote(payload, provider=provider or self.contract.provider_id)

    def build_snapshot(self, payloads: Iterable[Any]) -> ZeroDteStockSnapshot:
        return build_zero_dte_stock_snapshot(payloads, provider=self.contract.provider_id)

    def validate_payload(self, payload: Any, max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        return validate_zero_dte_stock_payload(payload, max_staleness_seconds=max_staleness_seconds)

    def health_check(self) -> dict[str, Any]:
        return build_scaffold_health_status(
            self.contract.provider_id,
            provider_name=self.contract.provider_name,
            provider_type=self.contract.provider_type,
            blockers=("read_only_provider_wrapper",),
        ).as_dict()

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ProviderUnavailableError("zero_dte_stocks provider is read-only and does not fetch live data")

    def fetch_quotes(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ProviderUnavailableError("zero_dte_stocks provider is read-only and does not fetch live data")

    def fetch_market_data(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ProviderUnavailableError("zero_dte_stocks provider is read-only and does not fetch live data")


__all__ = [
    "ZERO_DTE_STOCK_PROVIDER_TYPE",
    "ZeroDteStockProvider",
    "ZeroDteStockProviderStatus",
    "ZeroDteStockQuote",
    "ZeroDteStockSnapshot",
    "build_zero_dte_stock_quote",
    "build_zero_dte_stock_snapshot",
    "normalize_zero_dte_stock_payload",
    "normalize_zero_dte_stock_quote",
    "normalize_zero_dte_stock_snapshot",
    "validate_zero_dte_stock_payload",
]
