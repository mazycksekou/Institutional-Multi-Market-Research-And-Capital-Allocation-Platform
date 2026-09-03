# Master Roadmap

This roadmap is the permanent market lifecycle rule for the repository.
Every market uses the same progression, regardless of domain, provider mix, or future AI usage.

The repository does **not** skip discovery, blueprinting, validation, or reproducibility steps for any market.

## Long-Term Platform Sequence

Universal Market Framework
-> NFL Production Completion
-> Data Identity, Reconciliation and Lakehouse Foundation
-> First Controlled NFL Vendor Ingest
-> Portable External Research-Data Storage
-> Covariance and Time-Dependent Risk Capability Audit
-> Implement only covariance and risk capabilities confirmed missing by that audit
-> additional sports
-> prediction markets
-> Zero-DTE options
-> Worldview Intelligence
-> cross-market intelligence
-> universal risk and capital allocation
-> paper trading
-> controlled live execution
-> production platform and IP custody
-> institutional readiness
-> autonomous development

These are roadmap lanes only. They are not implementation authorization beyond the active governed phase in `docs/NEXT_ACTION.md`.

## Post-NFL Production Data Platform And Risk Lane

Immediately after complete NFL production validation, the next governed lanes are:

- `Data Identity, Reconciliation and Lakehouse Foundation`
- `First Controlled NFL Vendor Ingest`
- `Portable External Research-Data Storage`
- `Covariance and Time-Dependent Risk Capability Audit`

The data identity foundation phase is complete and validated. It:

- audit existing ingestion, normalization, identity, matching, reconciliation, quality-control, and physical-storage capabilities before implementation
- reuse the acquisition, `LocalStorageEngine`, local-platform, historical-research-database, certification, lifecycle, lineage, and validation owners
- add only missing shared identity, reconciliation, quarantine, revision-aware, and lakehouse capabilities
- map Bronze, Silver, and Gold onto the existing lifecycle rather than replacing it
- implement Parquet-based analytical storage and Delta-compatible interfaces
- defer Spark until measured data scale proves distributed execution is required
- avoid ingesting the vendor dataset in that phase

The first controlled NFL vendor ingest phase must:

- reuse the completed shared identity, reconciliation, quarantine, revision-aware, and lakehouse capabilities
- reuse the canonical acquisition, certification, lifecycle, lineage, validation, and dashboard owners
- onboard only the first controlled NFL vendor slice needed to prove the shared contracts under governed ingest conditions
- preserve certified NFL reference behavior, parity evidence, lineage, provenance, determinism, and point-in-time safety
- avoid covariance implementation, additional markets, paper trading, and live execution in that phase

The portable external research-data storage phase must:

- reuse the completed shared identity, reconciliation, quarantine, revision-aware, lakehouse, and First Controlled NFL Vendor Ingest capabilities
- reuse the canonical acquisition, storage, certification, lifecycle, lineage, validation, and dashboard owners
- externalize only the storage roots, configuration, and portability seams required to make repository-owned historical, lakehouse, and research artifacts portable
- preserve certified NFL reference behavior, Bronze, Silver, and Gold mapping, lineage, provenance, determinism, and point-in-time safety
- avoid covariance implementation, additional markets, paper trading, and live execution in that phase

The covariance audit completed repository inspection before implementation and determined existing, partial, missing, duplicated, or deferred support for:

- covariance and correlation
- rolling and exponentially weighted covariance
- covariance stability and regime detection
- cross-market and strategy covariance
- holding-period and forecast-horizon risk
- confidence and freshness decay
- overnight, weekend, event, expiration, and liquidity risk
- time-to-event and time-to-expiration risk
- risk-horizon normalization and attribution

Do not implement these capabilities during the sequencing correction, during the data identity foundation phase, during the first controlled NFL vendor ingest, or during the portable external research-data storage phase unless a later governed phase explicitly activates them. Static covariance/matrix completion and Dynamic and Point-in-Time Covariance are now complete inside the governed covariance and risk implementation lane; Portfolio Exposure and Incremental Risk is the next active capability.

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
- `docs/architecture/REPOSITORY_OS.md` is the canonical execution policy for repository work, and `docs/NEXT_ACTION.md` remains the sole sequencing source.
- Events own shared information such as weather, officials, injuries, coaching, kickoff, stadium, rest, and travel.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are generated later from event + market + selection + feature snapshot; they are not the storage primitive.
- The master research engine specification governs the lifecycle of market inputs, signals, targets, confidence metrics, validation metrics, connectors, engines, and research assets.
- The Worldview Intelligence Layer may request experiments only after the market has enough lifecycle maturity to support objective testing.

## Historical Research Sequence

The historical research database now follows a shared chain that future markets can reuse:

Provider -> Raw Acquisition Cache -> Integrity Validation -> Normalization -> Research Asset Certification -> Dataset Certification -> Historical Research Database -> Master Research Engine Specification -> Universal Feature Registry -> Universal Math Engine Contracts -> Research Asset Runtime Framework -> Historical Dataset Acquisition Framework -> Historical Research Asset Certification Runtime -> Research Asset Lifecycle Runtime -> Research Asset Source Discovery And Connector Mapping -> Research Asset Population -> Historical Dataset Population -> Feature Population -> Mathematical Engine Population -> Signal Population -> Decision Rows -> Backtesting -> Pipeline Validation -> Research Intelligence

Phase 4.4 established the event-centric historical acquisition foundation.
Phase 4.5A defined the master research engine specification.
Phase 4.5B built the universal feature registry.
Phase 4.5C defines the universal math engine contracts.
Phase 4.5D established the research asset runtime framework.
Phase 4.5E renamed the master research engine specification and the research asset runtime framework to reflect the broader runtime ownership model.
Phase 4.6 defines the minimum certified historical dataset acquisition framework.
Phase 4.7A discovers and maps research asset sources and connector families for the minimum certified historical schema.
Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation.
Phase 4.7C certifies the individual research assets required by the minimum certified historical dataset and then certifies the dataset once every required asset passes.
Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification.
Phase 4.9A populates the NFL schedule research asset.
Phase 4.9B builds the research asset coverage planner and provider selection framework.
Phase 4.9C implements the first production connector for the NFL schedule research asset.
Phase 4.9D populates the NFL results research asset.
Phase 4.9E completes the NFL odds research asset population and certifies its decision-time-safe join to the schedule and results backbone.
Phase 4.9F completed the NFL weather research asset population and certified its forecast-time-safe join to the schedule, results, and odds backbone.
Phase 4.9G completed the NFL injuries research asset population and certified its report-time-safe join to the schedule, results, odds, and weather backbone.
Phase 4.9H completed the NFL team statistics research asset population and closed the known minimum-schema asset gap.
Phase 5.0 completed the historical dataset population layer and certified the first deterministic NFL minimum-schema dataset batch.
Phase 5.1B completed the reusable feature snapshot population layer from the certified historical dataset batch.
Phase 5.2 completed reusable mathematical engines.
Phase 5.3 completed reusable signals.
Phase 5.4 completed the decision-row generation layer from the certified signal layer.
Phase 5.5 completed baseline backtesting from frozen, certified inputs.
Phase 5.6 completed pipeline validation and hardening on the production research engine path.
Phase 5.7 completed deterministic Research Intelligence on top of the certified NFL pipeline.
The next governed step is the Universal Market Framework, preserved here as the Phase 5.7 historical handoff statement.
The Universal Market Framework completed the governed extraction of reusable market-agnostic contracts, registries, lifecycle interfaces, readiness surfaces, and dashboard/query interfaces without mutating the hardened NFL path.
The next governed step after Universal Market Framework completion is NFL Production Completion so the certified NFL reference implementation can be audited against production-complete requirements without duplicating reusable framework logic.
After complete NFL production validation, the next governed lanes are Data Identity, Reconciliation and Lakehouse Foundation, then First Controlled NFL Vendor Ingest, then Portable External Research-Data Storage, then the Covariance and Time-Dependent Risk Capability Audit.
Only after that audit completes should the repository implement the covariance and risk capabilities confirmed missing by the audit.
Later roadmap lanes continue with additional sports, prediction markets, Zero-DTE options, Worldview Intelligence, cross-market intelligence, universal risk and capital allocation, paper trading, controlled live execution, production platform and IP custody, institutional readiness, and autonomous development.

Deferred enrichment lanes after the first minimum-schema dataset path remains stable:

- Phase 4.9I - NFL Player Statistics Research Asset Population
- Phase 4.9J - NFL Betting Splits Research Asset Population
Phase 4.9I populates the NFL player statistics research asset.
Phase 4.9J populates the NFL betting splits research asset.

## Current Phase Focus

Current NFL work follows the certified Phase 5 chain and the completed Universal Market Framework:

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
- Phase 4.5E completed the rename of the canonical engineering specification and the research asset runtime framework so their names reflect the broader runtime ownership model.
- Phase 4.6 defines the minimum certified historical dataset acquisition framework.
- Phase 4.7A will discover and map research asset sources and connector families for the minimum certified historical schema.
- Phase 4.7B will build the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation.
- Phase 4.7C completed the historical research asset certification runtime and gated dataset certification on asset-level evidence.
- Phase 4.8 will implement the research asset lifecycle runtime and time/entity alignment certification.
- Phase 4.9A completed the NFL schedule research asset population.
- Phase 4.9B completed the research asset coverage planner and provider selection framework.
- Phase 4.9C completed the first production connector for the NFL schedule research asset.
- Phase 4.9D completed the NFL results research asset population and certified its join to the schedule backbone.
- Phase 4.9E completed the NFL odds research asset population and certified its decision-time-safe join to the schedule and results backbone.
- Phase 4.9F completed the NFL weather research asset population and certified its forecast-time-safe join to the schedule, results, and odds backbone.
- Phase 4.9G completed the NFL injuries research asset population and certified its report-time-safe join to the schedule, results, odds, and weather backbone.
- Phase 4.9H completed the NFL team statistics research asset population and closed the known minimum-schema asset gap.
- Phase 5.0 completed the historical dataset population layer and certified the first deterministic NFL minimum-schema dataset batch.
- Phase 5.1B completed the reusable feature snapshot population layer from certified historical dataset rows.
- Phase 5.2 completed the reusable mathematical engines.
- Phase 5.3 completed reusable signals.
- Phase 5.4 completed the decision-row generation layer from the certified signal layer.
- Phase 5.5 completed baseline backtesting against the minimum certified schema.
- Phase 5.6 completed pipeline validation and hardening on the production research engine path.
- Phase 5.7 completed Research Intelligence on the certified NFL pipeline.
- Universal Market Framework generalized the certified NFL research chain without changing certified NFL outputs.
- Data Identity, Reconciliation and Lakehouse Foundation is complete and validated above the certified NFL production chain.
- First Controlled NFL Vendor Ingest is complete and validated on top of the shared identity, reconciliation, quarantine, revision-aware, and lakehouse capabilities.
- Portable External Research-Data Storage is complete and validated on top of the controlled vendor ingest and the shared identity, reconciliation, quarantine, revision-aware, and lakehouse owners.
- Covariance and Time-Dependent Risk Capability Audit is complete and validated; it confirmed the implementation lane for only proven covariance and risk gaps.
- Static Covariance and Matrix Completion is complete and validated.
- Dynamic and Point-in-Time Covariance is complete and validated.
- Implement Confirmed Covariance And Time-Dependent Risk Gaps is the active governed phase.
- Portfolio Exposure and Incremental Risk is the active checkpoint inside that phase.
- Phase 4.9I and Phase 4.9J remain deferred enrichment asset lanes after the first baseline dataset path is established.

The master research engine specification is already the canonical name for the broader research-engine scope. If the repository later needs an even broader top-level research asset registry, that should be treated as a separate future phase rather than another rename of this specification.

## Current Project Status

- Active branch: `main`
- Active governed phase: `Implement Confirmed Covariance And Time-Dependent Risk Gaps`
- Active checkpoint: `Portfolio Exposure and Incremental Risk`
- Active market profile: `sports:nfl`
- Canonical project status: `docs/PROJECT_STATUS.md`
- Canonical next action: `docs/NEXT_ACTION.md`
- Canonical status policy: `docs/STATUS_UPDATE_POLICY.md`
- Canonical research engine specification: `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md`
- Canonical research asset runtime framework: `docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md`
- Canonical research asset source discovery and connector mapping framework: `docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md`
- Canonical historical dataset acquisition framework: `docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md`
- Canonical research asset contract: `docs/contracts/RESEARCH_ASSET_CONTRACT.md`
- Canonical minimum backtest row contract: `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- Canonical NFL minimum backtest row contract: `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- Canonical mathematical engine contracts: `docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md`
- Canonical historical research database: `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- Canonical NFL odds research asset: `docs/architecture/NFL_ODDS_RESEARCH_ASSET.md`
- Canonical NFL weather research asset: `docs/architecture/NFL_WEATHER_RESEARCH_ASSET.md`
- Canonical NFL injuries research asset: `docs/architecture/NFL_INJURIES_RESEARCH_ASSET.md`
- Canonical NFL team statistics research asset: `docs/architecture/NFL_TEAM_STATISTICS_RESEARCH_ASSET.md`

## Worldview Constraint

The Worldview Intelligence Layer is a research scientist, not a trader.
It can propose hypotheses and experiments.
It cannot bypass this lifecycle or request live experimentation before the evidence chain is mature enough.
