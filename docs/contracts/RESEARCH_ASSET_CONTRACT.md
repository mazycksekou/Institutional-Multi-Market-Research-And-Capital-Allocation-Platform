# Research Asset Contract

This contract defines the canonical record shape for any governed research asset in the repository.
It is architecture and schema guidance only.
It does not implement runtime behavior.

## Purpose

The contract gives every research asset one stable identity, one owner, one lifecycle, and one lineage chain.
It is the shared contract for datasets, features, mathematical engines, signals, targets, confidence measures, decision rows, backtests, experiments, evidence packages, connectors, and validation results.

## Research Asset ID Standard

Every asset must use a permanent lowercase dotted identifier.

Format:

`category.family.scope.name`

Examples:

- `dataset.nfl.games`
- `dataset.nfl.odds`
- `feature.sports.ticket_percentage`
- `math.options.gex`
- `signal.sports.reverse_line_movement`
- `target.options.primary_target`
- `connector.theoddsapi`
- `experiment.nfl.spread_model`
- `validation.dataset.certification`

Rules:

- keep the ID stable
- do not embed version numbers in the ID
- do not reuse retired IDs
- do not encode machine-specific paths
- do not encode provider credentials or private names

## Required Contract Fields

Every research asset entry must expose the following fields:

| Field | Meaning |
| --- | --- |
| Research Asset ID | Permanent canonical identifier. |
| Asset Category | Dataset, feature, math engine, signal, target, confidence, decision row, backtest, experiment, evidence package, connector, or validation result. |
| Description | Short statement of what the asset is. |
| Purpose | Why the asset exists in the research workflow. |
| Owner | Canonical runtime owner or canonical document owner. |
| Dependencies | Other assets that must exist first. |
| Consumes | Inputs the asset reads. |
| Produces | Outputs the asset emits. |
| Lifecycle | Current lifecycle state. |
| Versioning | Dataset, schema, or contract version rules. |
| Validation Owner | Module or script responsible for validation. |
| Storage Owner | Module or storage layer responsible for persistence. |
| Profile Owner | Market-profile owner, if applicable. |
| Runtime Owner | Module that owns runtime behavior, if any. |
| Evidence Requirements | What evidence is needed before promotion. |
| Point-in-Time Rules | Timing and leakage rules. |
| Lineage Requirements | Source-to-consumer traceability requirements. |
| Supported Markets | Market families the asset can serve. |
| Priority | Relative implementation priority. |

## Asset Category Rules

### Dataset

Dataset assets represent certified historical data.
They must be point-in-time safe, versioned, lineage-aware, and owned by the repository.

### Feature

Feature assets represent reusable feature definitions that are compatible with the universal feature registry.

### Mathematical Engine

Mathematical engine assets represent reusable calculations that obey the universal mathematical engine contracts.

### Signal / Target / Confidence

These assets must trace back to registered features and governed validation rules.

### Decision Row

Decision rows are generated research artifacts, not the storage primitive.

### Backtest / Experiment / Evidence Package

These assets must be reproducible without depending on live providers.

### Connector

Connectors are acquisition and adaptation assets, not business logic owners.

### Validation Result

Validation assets report readiness, leakage, schema, and lineage state.

## Lifecycle Framework

Every research asset must support the same lifecycle progression:

Defined -> Contract Ready -> Schema Ready -> Source Identified -> Connector Ready -> Historical Dataset Ready -> Math Ready -> Signal Ready -> Validated -> Backtested -> Production Ready

The lifecycle gate meaning is:

- Defined: the asset exists conceptually
- Contract Ready: the record shape is documented
- Schema Ready: the fields and types are known
- Source Identified: at least one usable source family is known
- Connector Ready: a canonical adapter path exists
- Historical Dataset Ready: certified historical inputs can support the asset
- Math Ready: the derivation path is ready in the canonical runtime owner
- Signal Ready: the asset can be consumed by downstream layers
- Validated: the asset has evidence, lineage, and leakage checks
- Backtested: the asset has been evaluated where backtesting applies
- Production Ready: the asset can be consumed in the canonical workflow

## Certification States

Research asset certification reuses the canonical certification states that the runtime exposes:

- UNKNOWN
- DISCOVERED
- ACQUIRED
- VALIDATED
- PARTIALLY_CERTIFIED
- CERTIFIED
- REJECTED
- SUPERSEDED
- REVOKED

## Certification Failure Reasons

Certification failures must be explainable and machine-readable.

Accepted failure reasons:

- Missing Fields
- Coverage Failure
- Schema Failure
- Timestamp Failure
- Duplicate Records
- Corrupted Payload
- Failed Checksum
- Lineage Failure
- Provider Conflict
- Point-In-Time Violation

## Ownership Rules

Every asset must have exactly one canonical owner.
The owner may delegate work, but the owner cannot be ambiguous.

Preferred owners:

- `src.data` for dataset contracts and lineage metadata
- `src.storage` for persistence and table ownership
- `src.core` for mathematical primitives
- `src.market_intelligence` for market-facing signals and market-aware metadata
- `src.backtesting` for historical decision and replay contracts
- `src.research` for experiments and evidence bundles
- `src.analytics` for summaries and validation reporting
- `src.providers` and `src.connectors` for acquisition boundaries
- `src.data.validation` and `scripts` for validation gates

## Evidence Requirements

Before an asset can be considered mature, it must be able to point to:

- source metadata
- lineage metadata
- schema version
- point-in-time safety status
- validation result
- supported market family
- canonical owner

## Supported Markets

The contract applies to the same supported market families as the repository-wide framework:

- universal
- sports
- prediction markets
- options / 0DTE
- futures
- crypto
- macro

## Out Of Scope

This contract does not:

- implement formulas
- ingest data
- implement provider integrations
- build feature pipelines
- build backtests
- train models
- execute trades

It only defines the reusable record shape that future runtime owners must honor.
