# Canonical Ownership Map

This map describes the current canonical ownership boundaries used throughout the repository.

| Responsibility | Canonical owner | Notes |
| --- | --- | --- |
| Public API routes and entrypoint wiring | `src.api` | Thin route layer only |
| Runtime orchestration and facades | `src.services` | Coordinates application workflows and dashboard adapters |
| External provider contracts and policy | `src.providers` | Provider-facing behavior and registry boundaries |
| External-source connectors | `src.connectors` | Normalizes external sources into canonical internal contracts |
| Core math, pricing, portfolio, execution primitives | `src.core` | Lowest-level reusable primitives |
| Canonical data contracts, lineage, storage, local helpers | `src.data` | Owns data contracts and local persistence boundaries |
| Historical replay, simulation, strategy profiles | `src.backtesting` | Backtest and replay orchestration |
| Sports and market intelligence | `src.market_intelligence` | Sports, prediction markets, options, manifold, and signal intelligence |
| Reporting, readiness, governance, summaries | `src.analytics` | Readable outputs and governance summaries |
| Experiments, calibration, feature control | `src.research` | Research metadata and studies |
| Policy, gates, secret-safety, approval | `src.security` | Security boundaries and local-only enforcement |
| Disabled AI metadata and prompt artifacts | `src.ai` | No live model activation |
| Brokerage and execution boundaries | `src.brokerage` | Production-shaped execution without live order submission |
| Persistence primitives | `src.storage` | Backend storage abstractions used by canonical data ownership |
| Sport-domain helpers and models | `src.sports` | Sport-specific helpers that do not belong in market intelligence |

## Ownership Rules

- Every runtime responsibility should have exactly one canonical owner.
- Compatibility shims are allowed only when they forward to canonical owners and do not duplicate business logic.
- Shared code should move toward the lowest stable owner that can preserve behavior.
- Documentation, reports, and historical evidence do not own runtime behavior.

## Ownership Notes

- No standalone public `src.models` package is currently required by the repository structure.
- Model-like concerns are distributed across `src.ai`, `src.market_intelligence`, and `src.research` according to purpose.
- Configuration ownership is kept close to the runtime module that consumes it unless a dedicated shared layer is justified.
