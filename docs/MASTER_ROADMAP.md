# Master Roadmap

This roadmap is the permanent market lifecycle rule for the repository.
Every market uses the same progression, regardless of domain, provider mix, or future AI usage.

The repository does **not** skip discovery, blueprinting, validation, or reproducibility steps for any market.

## Universal Market Lifecycle

| Step | Name | Purpose | Exit criterion |
| --- | --- | --- | --- |
| 1 | Discovery | Identify current capabilities, sources, contracts, and blockers. | The repository has an evidence-backed inventory of what exists. |
| 2 | Research Blueprint | Define the smallest practical first slice and the contract for the initial model/backtest path. | The blueprint names the baseline dataset, features, joins, and gate criteria. |
| 3 | Data Sources | Decide which sources are usable, point-in-time safe, and governance-approved. | Every required field has a source category or a documented deferral. |
| 4 | Canonical Storage | Define the permanent storage model for raw, normalized, feature, and backtest artifacts. | Storage ownership and join keys are explicit. |
| 5 | Feature Engineering | Build reproducible feature pipelines only after storage and timing are settled. | Feature lineage and leakage controls are in place. |
| 6 | Historical Dataset | Materialize a versioned historical dataset from validated sources. | Dataset snapshots are reproducible and time aware. |
| 7 | Backtesting | Evaluate baseline models against settled outcomes with frozen inputs. | Backtests are reproducible and auditable. |
| 8 | Walk-Forward Validation | Test across forward time blocks to limit look-ahead bias. | Out-of-sample performance is measured chronologically. |
| 9 | Paper Trading | Simulate live decisions without capital risk. | The system can run in a controlled, non-live environment. |
| 10 | Controlled Live Deployment | Move only after governance, validation, and evidence are strong enough. | Live deployment is explicitly approved and monitored. |

## Permanent Rules

- Every market follows the same lifecycle.
- No market skips discovery.
- No market skips a research blueprint.
- No market skips data validation.
- No market skips historical backtesting.
- No market skips walk-forward validation.
- No market skips paper trading before live deployment.
- Market work must remain reproducible and point-in-time safe.
- Historical datasets are permanent repository assets.
- Providers are acquisition mechanisms only.
- The repository owns the certified dataset after acquisition and certification.
- Multiple providers may contribute to one dataset.
- The first production backtests use only the certified minimum schema.
- Advanced metrics remain inactive until their data, math, and validation maturity are proven.
- Events own shared information such as weather, officials, injuries, coaching, kickoff, stadium, rest, and travel.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are generated later from event + market + selection + feature snapshot; they are not the storage primitive.
- The master research engine specification governs the lifecycle of market inputs, signals, targets, confidence metrics, validation metrics, connectors, engines, and research assets.
- The Worldview Intelligence Layer may request experiments only after the market has enough lifecycle maturity to support objective testing.

## Historical Research Sequence

The historical research database now follows a shared chain that future markets can reuse:

Provider -> Acquisition -> Archive -> Normalization -> Certification -> Master Research Engine Specification -> Universal Feature Registry -> Universal Math Engine Contracts -> Research Asset Runtime Framework -> Historical Dataset Acquisition -> Historical Dataset Certification -> Feature Population -> Mathematical Engine Implementation -> Decision Rows -> Backtesting

Phase 4.4 established the event-centric historical acquisition foundation.
Phase 4.5A defined the master research engine specification.
Phase 4.5B built the universal feature registry.
Phase 4.5C defines the universal math engine contracts.
Phase 4.5D established the research asset runtime framework.
Phase 4.5E renames the master research engine specification and the research asset runtime framework to reflect the broader runtime ownership model.
Phase 4.6 acquires the minimum certified historical dataset.
Phase 4.7 certifies historical datasets against the governed inputs.
Phase 4.8 populates reusable historical features on top of certified events.
Phase 4.9 implements reusable mathematical engines.
Phase 5.0 generates decision rows from events, markets, selections, and feature snapshots.
Phase 5.1 begins baseline backtesting from frozen, certified inputs.
Phase 5.2 performs walk-forward validation on the baseline schema.
Later phases continue with paper trading, incremental live updates, Worldview Intelligence, and controlled production deployment.

## Current Phase Focus

Current NFL work is in Phase 4:

- Phase 4.1 established the NFL discovery and capability audit.
- Phase 4.2 defines the NFL research blueprint and the permanent roadmap rule.
- Phase 4.3 implemented the smallest reusable NFL slice after the blueprint was fixed.
- Phase 4.3.6 completed the profile-aware NFL P0 validation.
- Phase 4.3.7 defined the minimum backtest row contract.
- Phase 4.4 established the event-centric historical acquisition foundation.
- Phase 4.5A defined the master research engine specification.
- Phase 4.5B built the universal feature registry.
- Phase 4.5C completed the universal math engine contracts.
- Phase 4.5D established the research asset runtime framework.
- Phase 4.5E is the current phase and renames the canonical engineering specification and the research asset runtime framework so their names reflect the broader runtime ownership model.
- Phase 4.6 will acquire the minimum certified historical dataset.
- Phase 4.7 will certify historical datasets against the governed inputs.
- Phase 4.8 will populate generated historical features from events.
- Phase 4.9 will implement reusable mathematical engines.
- Phase 5.0 will generate decision rows from events, markets, selections, and feature snapshots.
- Phase 5.1 will begin baseline backtesting against the minimum certified schema.
- Phase 5.2 will perform walk-forward validation on the baseline schema.

The master research engine specification is already the canonical name for the broader research-engine scope. If the repository later needs an even broader top-level research asset registry, that should be treated as a separate future phase rather than another rename of this specification.

## Current Project Status

- Active branch: `feature/nfl-backtesting`
- Active market profile: `sports:nfl`
- Canonical project status: `docs/PROJECT_STATUS.md`
- Canonical next action: `docs/NEXT_ACTION.md`
- Canonical status policy: `docs/STATUS_UPDATE_POLICY.md`
- Canonical research engine specification: `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md`
- Canonical research asset runtime framework: `docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md`
- Canonical research asset contract: `docs/contracts/RESEARCH_ASSET_CONTRACT.md`
- Canonical minimum backtest row contract: `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- Canonical NFL minimum backtest row contract: `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- Canonical mathematical engine contracts: `docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md`
- Canonical historical research database: `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`

## Worldview Constraint

The Worldview Intelligence Layer is a research scientist, not a trader.
It can propose hypotheses and experiments.
It cannot bypass this lifecycle or request live experimentation before the evidence chain is mature enough.
