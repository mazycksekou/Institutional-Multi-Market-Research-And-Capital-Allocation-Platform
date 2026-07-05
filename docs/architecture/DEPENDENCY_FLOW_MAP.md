# Dependency Flow Map

The repository is organized to keep high-level runtime surfaces thin and low-level primitives reusable.

## Intended Flow

```mermaid
flowchart LR
  Entry[API / CLI / Streamlit entrypoints] --> Services[src.services]
  Services --> Providers[src.providers]
  Services --> Connectors[src.connectors]
  Services --> Data[src.data]
  Services --> Analytics[src.analytics]
  Services --> Backtesting[src.backtesting]
  Services --> Research[src.research]
  Connectors --> Data
  Providers --> Connectors
  Data --> Storage[src.storage]
  Data --> Core[src.core]
  MarketIntelligence[src.market_intelligence] --> Data
  MarketIntelligence --> Core
  Backtesting --> Data
  Backtesting --> Core
  Backtesting --> Analytics
  Research --> Data
  Analytics --> Data
  Brokerage[src.brokerage] --> Core
  Brokerage --> Data
  Security[src.security] --> Core
  Security --> Data
```

## Dependency Rules

- `src.core` is the lowest reusable layer and should not import high-level packages.
- `src.data` should not import `src.api` or `src.services`.
- `src.providers` should not import `src.api`.
- `src.services` may orchestrate higher-level workflows but should avoid owning duplicate business logic.
- `src.api`, `main.py`, and `streamlit_app.py` should stay thin and delegate to canonical modules.

## Violation Handling

- If a dependency direction is unclear, classify the responsibility first and move the code to the lowest correct owner.
- If a module is only a compatibility surface, keep it thin and document the forwarding behavior.
- If a dependency is historical only, document it in `docs/archive/` rather than keeping it in runtime code.
