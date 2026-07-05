# Post Data / Backtesting Architecture Map After 10K8ZHM

## Canonical Layers

- `src.data`: local dataset contracts, metadata, registry, validation
- `src.backtesting`: backtest dataset contracts, leakage checks, replay and simulation plans
- `src.core`: math, risk, and the existing walk-forward backtester kernel
- `src.services`: orchestration wrappers
- `src.api`: route exposure only

## Future Layers

- `src.analytics`: attribution, reporting, governance, and performance analysis
- `src.research`: experiments, research lanes, and exploratory analysis

## Deferred Domains

- AI/LLM
- brokerage/live execution
- live data activation

