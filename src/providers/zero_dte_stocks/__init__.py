"""0DTE/stocks provider namespace for the future canonical provider package."""

from .contracts import (
    SAMPLE_DRY_RUN_PAYLOAD,
    ZERO_DTE_STOCK_PROVIDER_TYPE,
    ZeroDteStockProviderContract,
    build_zero_dte_stock_provider_contract,
    normalize_zero_dte_stock_payload,
    validate_zero_dte_stock_payload,
)
from .adapters import (
    ZERO_DTE_STOCK_PROVIDER_TYPE as ADAPTER_ZERO_DTE_STOCK_PROVIDER_TYPE,
    ZeroDteStockProviderAdapter,
    ZeroDteStockQuote,
    build_zero_dte_stock_quote,
    normalize_zero_dte_stock_quote,
)
from .models import ZeroDteStockProviderStatus, ZeroDteStockSnapshot
from .normalization import build_zero_dte_stock_snapshot, normalize_zero_dte_stock_snapshot
from .provider import ZeroDteStockProvider

__all__ = [
    "ADAPTER_ZERO_DTE_STOCK_PROVIDER_TYPE",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "ZERO_DTE_STOCK_PROVIDER_TYPE",
    "ZeroDteStockProviderAdapter",
    "ZeroDteStockProvider",
    "ZeroDteStockProviderContract",
    "ZeroDteStockProviderStatus",
    "ZeroDteStockQuote",
    "ZeroDteStockSnapshot",
    "build_zero_dte_stock_provider_contract",
    "build_zero_dte_stock_quote",
    "build_zero_dte_stock_snapshot",
    "normalize_zero_dte_stock_payload",
    "normalize_zero_dte_stock_quote",
    "normalize_zero_dte_stock_snapshot",
    "validate_zero_dte_stock_payload",
]
