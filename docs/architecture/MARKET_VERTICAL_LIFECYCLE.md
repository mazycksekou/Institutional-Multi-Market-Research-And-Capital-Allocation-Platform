# Market Vertical Lifecycle

This document is the canonical lifecycle contract for every market vertical in the repository.
It complements `docs/MASTER_ROADMAP.md` and makes the lifecycle easier to apply consistently in implementation planning.

## Canonical Sequence

1. Discovery
2. Research Blueprint
3. Data Sources
4. Canonical Storage
5. Feature Engineering
6. Historical Dataset
7. Backtesting
8. Walk-Forward Validation
9. Paper Trading
10. Controlled Live Deployment

## Lifecycle Principles

- The same lifecycle applies to NFL, NBA, MLB, NHL, soccer, tennis, MMA, prediction markets, stocks, ETFs, options, crypto, futures, macro, and future markets.
- Discovery comes before implementation.
- Blueprinting comes before ingestion.
- Data validation comes before feature engineering.
- Historical datasets come before backtests.
- Historical datasets are permanent repository assets once certified.
- Providers are acquisition mechanisms only.
- Backtests never read directly from providers.
- The first production backtests use only the certified minimum schema.
- Advanced assets remain inactive until their data, math, and validation maturity are proven.
- Events own shared context.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are derived later and are not the storage primitive.
- Walk-forward validation comes before paper trading promotion.
- Paper trading comes before live deployment.
- No market is allowed to jump ahead because the source is familiar or the path feels obvious.

## Required Artifacts by Stage

| Stage | Required output |
| --- | --- |
| Discovery | Capability inventories, source inventories, contract inventories, connector mapping, gap analysis |
| Research Blueprint | Baseline market scope, feature priority matrix, leakage review, source mapping |
| Data Sources | Source approvals, timing rules, provenance categories |
| Canonical Storage | Table families, join keys, snapshot rules, lineage rules |
| Feature Engineering | Feature definitions, point-in-time guards, reuse plan |
| Historical Dataset | Versioned rows, frozen inputs, settled outcomes |
| Backtesting | Replayable rows, test harness, result metrics |
| Walk-Forward Validation | Chronological folds, out-of-sample evaluation |
| Paper Trading | Simulation controls, no-live-money safeguards |
| Controlled Live Deployment | Approval gate, observability, rollback plan |

## Historical Research Shape

The repository now treats the historical research path as event-centric and phase-aware:

Provider -> Acquisition -> Archive -> Normalization -> Certification -> Master Research Engine Specification -> Universal Feature Registry -> Universal Math Engine Contracts -> Research Asset Runtime Framework -> Historical Dataset Acquisition Framework -> Research Asset Source Discovery And Connector Mapping -> Historical Dataset Acquisition -> Historical Dataset Acquisition and Certification -> Feature Population -> Mathematical Engine Implementation -> Decision Rows -> Backtesting

Decision rows are generated research primitives.
Events are the shared historical ownership unit.
Markets and selections inherit the event context.

The phase-aware planning path is:

Phase 4.5A -> Master Research Engine Specification
Phase 4.5B -> Universal Feature Registry
Phase 4.5C -> Universal Math Engine Contracts
Phase 4.5D -> Research Asset Runtime Framework
Phase 4.6 -> Minimum Certified Historical Dataset Acquisition Framework
Phase 4.7A -> Research Asset Source Discovery & Connector Mapping
Phase 4.7B -> Historical Dataset Acquisition
Phase 4.7 -> Historical Dataset Acquisition and Certification
Phase 4.8 -> Historical Feature Population
Phase 4.9 -> Mathematical Engine Implementation
Phase 5.0 -> Decision Row Generation
Phase 5.1 -> Baseline Backtesting
Phase 5.2 -> Walk-Forward Validation

## Worldview Integration Rule

The Worldview Intelligence Layer may only request experiments against a market once the repository can prove:

- the market has a clear data contract,
- the data is point-in-time safe,
- the feature lineage is explicit,
- the backtest evidence is reproducible,
- and the requested experiment can be evaluated objectively.

## Practical Use

When a new market starts, the first question is not "what model do we train?"
The first question is "what is the smallest reproducible data slice that supports trustworthy research?"
