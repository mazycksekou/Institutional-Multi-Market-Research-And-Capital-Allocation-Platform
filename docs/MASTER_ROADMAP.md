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
- Events own shared information such as weather, officials, injuries, coaching, kickoff, stadium, rest, and travel.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are generated later from event + market + selection + feature snapshot; they are not the storage primitive.
- The Worldview Intelligence Layer may request experiments only after the market has enough lifecycle maturity to support objective testing.

## Historical Research Sequence

The historical research database now follows a shared chain that future markets can reuse:

Provider -> Acquisition -> Archive -> Normalization -> Certification -> Event -> Feature Snapshot -> Markets -> Selections -> Decision Rows -> Backtesting

Phase 4.4 establishes the event-centric historical acquisition foundation.
Phase 4.5 populates reusable historical features on top of certified events.
Phase 4.6 constructs decision rows from events, markets, selections, and feature snapshots.
Later phases continue with backtesting, walk-forward validation, paper trading, and controlled live deployment.

## Current Phase Focus

Current NFL work is in Phase 4:

- Phase 4.1 established the NFL discovery and capability audit.
- Phase 4.2 defines the NFL research blueprint and the permanent roadmap rule.
- Phase 4.3 implemented the smallest reusable NFL slice after the blueprint was fixed.
- Phase 4.3.6 completed the profile-aware NFL P0 validation.
- Phase 4.3.7 defined the minimum backtest row contract.
- Phase 4.4 is the current phase and builds the event-centric historical acquisition foundation.
- Phase 4.5 is the next recommended phase and should populate historical features from certified events.
- Phase 4.6 will construct generated decision rows from events, markets, selections, and feature snapshots.

## Current Project Status

- Active branch: `feature/nfl-backtesting`
- Active market profile: `sports:nfl`
- Canonical project status: `docs/PROJECT_STATUS.md`
- Canonical next action: `docs/NEXT_ACTION.md`
- Canonical status policy: `docs/STATUS_UPDATE_POLICY.md`
- Canonical minimum backtest row contract: `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- Canonical NFL minimum backtest row contract: `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- Canonical historical research database: `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`

## Worldview Constraint

The Worldview Intelligence Layer is a research scientist, not a trader.
It can propose hypotheses and experiments.
It cannot bypass this lifecycle or request live experimentation before the evidence chain is mature enough.
