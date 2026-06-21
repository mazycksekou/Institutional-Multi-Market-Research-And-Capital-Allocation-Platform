from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .provider import (
    ZERO_DTE_STOCK_PROVIDER_TYPE,
    ZeroDteStockProvider,
    ZeroDteStockQuote,
    build_zero_dte_stock_quote,
    normalize_zero_dte_stock_quote,
    validate_zero_dte_stock_payload,
)

class ZeroDteStockProviderAdapter(ZeroDteStockProvider):
    pass


__all__ = [
    "ZERO_DTE_STOCK_PROVIDER_TYPE",
    "ZeroDteStockProviderAdapter",
    "ZeroDteStockQuote",
    "build_zero_dte_stock_quote",
    "normalize_zero_dte_stock_quote",
]
