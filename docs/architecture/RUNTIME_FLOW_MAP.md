# Runtime Flow Map

## Typical Runtime Path

```mermaid
flowchart LR
  Root[Thin root entrypoints] --> Services[src.services]
  Services --> API[src.api]
  Services --> Data[src.data]
  Services --> Providers[src.providers]
  Services --> Connectors[src.connectors]
  Services --> MarketIntelligence[src.market_intelligence]
  Services --> Backtesting[src.backtesting]
  Services --> Analytics[src.analytics]
  Services --> Research[src.research]
  Data --> Storage[src.storage]
  Providers --> Connectors
```

## Notes

- Root entrypoints are intentionally thin.
- Runtime behavior should flow through canonical service layers, not through duplicated top-level packages.
- Reporting and dashboard surfaces should consume canonical data rather than constructing their own independent storage paths.
