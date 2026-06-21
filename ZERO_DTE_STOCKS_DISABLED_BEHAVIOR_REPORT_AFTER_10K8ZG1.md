# ZERO_DTE_STOCKS_DISABLED_BEHAVIOR_REPORT_AFTER_10K8ZG1

## Disabled Behavior
- `ZeroDteStockProvider.fetch_snapshot()` raises `ProviderUnavailableError`.
- `ZeroDteStockProvider.fetch_quotes()` raises `ProviderUnavailableError`.
- `ZeroDteStockProvider.fetch_market_data()` raises `ProviderUnavailableError`.
- `ZeroDteStockProviderAdapter.fetch_snapshot()` raises `ProviderUnavailableError`.
- `ZeroDteStockProviderAdapter.fetch_quotes()` raises `ProviderUnavailableError`.
- `ZeroDteStockProviderAdapter.fetch_market_data()` raises `ProviderUnavailableError`.

## Why This Matters
The provider wrapper is proven read-only and cannot be used to fetch live data.
