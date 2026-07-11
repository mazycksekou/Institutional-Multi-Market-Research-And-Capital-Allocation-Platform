# Phase 5.0 - Historical Dataset Population Layer

## Summary

Phase 5.0 materializes the first deterministic NFL historical dataset batch from the certified minimum-schema research assets.
The layer reuses the shared historical acquisition, research-asset certification, lifecycle, storage, coverage-planner, dashboard, and NFL P0 owners.
It does not introduce a parallel NFL dataset framework.

## What Changed

- populated `dataset.sports.nfl.historical_dataset` from certified schedule, results, odds, weather, injuries, and team-statistics evidence
- extended the canonical dataset-batch and dataset-row persistence contract with scheduled kickoff, decision cutoff, selected per-asset timestamps, freshness, source record identities, certification references, lineage ids, and decision-readiness fields
- enforced the canonical game-scoped cutoff policy of scheduled kickoff minus five minutes
- selected each predictor asset independently at its latest eligible certified availability time at or before the shared cutoff
- kept results label-only so realized outcomes do not influence predictor selection, batch identity, or readiness
- added join diagnostics, cardinality validation, rejected-evidence reporting, and evidence-package persistence
- integrated dataset readiness into the coverage planner, NFL P0 foundation, and shared Streamlit dashboard adapter
- preserved deterministic rerun behavior, stable row identities, stable batch identities, stable lineage-edge identities, and local schema reconciliation for existing databases
- added focused runtime and documentation regression coverage for cutoff independence, multi-row control, dashboard reconstruction, import safety, and rerun determinism

## Dataset Grain And Decision Cutoff

The populated layer keeps one canonical row per NFL event plus market decision context.
For the current minimum slice that yields one deterministic row for each supported market context while still preserving controlled child evidence from multi-row sources.

The critical policy is:

`decision_cutoff = scheduled_kickoff_time - 5 minutes`

That cutoff is game-scoped, deterministic, and independent of whichever asset happened to update last.
Odds, weather, injuries, and team-statistics can therefore contribute different timestamps to the same row as long as every selected predictor record was available by the shared cutoff.

## Snapshot Selection And Cardinality Controls

Phase 5.0 makes the selection rules explicit:

- odds: latest eligible market snapshot at or before the cutoff
- weather: latest eligible predecision weather evidence at or before the cutoff, without promoting realized weather into predictors
- injuries: latest eligible report state at or before the cutoff, without using later revisions
- team statistics: latest eligible predecision statistics that exclude the target event
- results: labels only

The dataset layer rejects:

- after-cutoff predictor evidence
- at-kickoff or post-kickoff predictor evidence
- same-event team statistics
- rolling windows that include the target event
- uncontrolled many-to-many expansion

Join diagnostics persist source counts, eligible counts, rejected counts, unmatched counts, and final dataset row counts so apparently valid output sizes cannot hide duplicate evidence or row multiplication.

## Persistence, Lineage, And Evidence Package

The canonical storage path persists dataset batches and dataset rows through the shared local storage owner.
Every row now retains:

- scheduled kickoff
- decision cutoff
- cutoff policy version
- selected asset timestamps
- per-asset freshness at cutoff
- selected source record ids
- source certification ids
- lineage ids
- missing required assets
- decision-readiness status

The evidence package records the batch identity, source asset batches, certification references, alignment evidence, join diagnostics, rejected evidence summary, cutoff policy, selection policy, and readiness result.
Lineage remains queryable and stable across idempotent reruns.

## Coverage Planner, Dashboard, And NFL P0 Integration

The minimum-schema required asset gap remains closed.
Phase 5.0 adds the dataset-layer readiness rollup without reopening deferred enrichment assets as blockers.

The coverage planner now distinguishes between:

- a deliberately omitted embedded snapshot with `not_embedded`
- a requested snapshot that failed to build with `coverage_planner_snapshot_failed`

The shared dashboard path reconstructs dataset readiness from persisted state and reports the dataset batch, row counts, rejected evidence, unmatched evidence, validation status, certification state, lineage completeness, and readiness state.
The NFL P0 foundation now rolls up dataset-layer readiness alongside the six certified source assets.

## Query And Worldview Readiness

The populated dataset layer is ready for deterministic query of:

- dataset and batch discovery
- event and team lookup
- season and week filtering
- selected snapshot inspection
- realized label inspection
- cutoff eligibility
- rejected evidence
- source lineage
- source certification
- dataset certification
- readiness status
- evidence-package retrieval

That gives the future Research Query Engine and Worldview layer a reproducible evidence substrate without letting either layer invent or bypass certified history.

## Senior Systems Engineer Review

### Strengths

- The phase reuses the canonical shared owners instead of introducing an NFL-only dataset runtime.
- The decision cutoff contract is fixed to scheduled kickoff minus five minutes and no longer drifts with asset update timing.
- Cardinality diagnostics are first-class persisted evidence rather than best-effort logging.
- The persisted row contract is explicit and queryable, not an opaque JSON dump.

### Weaknesses

- The current minimum slice still depends on a narrow set of fixture-backed evidence paths, so the next phase should avoid assuming broader market coverage than the repository actually certifies today.
- The shared alignment model still mixes asset-scoped lifecycle state with row-level evidence, which is manageable now but could need a richer aggregate contract later.

### Implemented Improvements

- fixed game-scoped cutoff handling
- fixed coverage-planner embedding-state reporting
- preserved results as label-only evidence
- preserved deterministic reruns and schema reconciliation
- added import-safety coverage to guard against circular exports

### Deferred Improvements

- richer aggregate alignment summaries for multi-row assets
- broader multi-event fixture coverage once the feature layer is stable
- additional optional enrichment assets after the minimum feature path is established

### Recommendation

Advance directly to reusable feature population from the certified historical dataset layer.
Do not reopen optional enrichment assets, connector work, or downstream modeling as blockers for that next phase.

## Worldview / Research Query Engine Review

### Query Readiness

The dataset layer is queryable by dataset, batch, event, team, week, market context, selected evidence, rejected evidence, certification state, and readiness state.

### Evidence-Package Readiness

The persisted evidence package captures cutoff policy, selection policy, source certifications, diagnostics, and lineage in a reproducible form suitable for later evidence export.

### Experiment Readiness

The layer is ready for feature population and later hypothesis design, but not yet for mathematical engines, signals, decision rows, or backtesting.

### Lineage Quality

Lineage is explicit from dataset rows back to the contributing certified source rows and their certifications, with stable ids across idempotent reruns.

### Unresolved Blockers

No minimum-schema asset blockers remain.
Optional enrichment assets, paid data acquisition, and live connector work stay deferred and non-blocking for the next governed phase.

### Recommendation

Use the certified dataset layer as the sole evidence substrate for Phase 5.1 reusable feature population.

## Validation

- focused historical dataset population runtime tests: passed
- focused historical dataset population documentation tests: passed
- adjacent shared-runtime regression tests: passed
- compileall: passed
- import/circular-export checks: passed
- smoke: passed with 19 executed selections and 18 skips
- root markdown: passed
- OpenAPI contract: passed
- architecture: passed
- audit lifecycle: passed
- document lifecycle: advisory with one warning and no clear violations
- ops workflow check: passed with `verification_ok`
- repository preflight checks: before-commit, before-push, and end-task passed in the final staged and committed states
- full repository test gate: passed with 3823 tests passed, 670 skipped, and 519 subtests passed

## Readiness For Phase 5.1

Phase 5.1 may begin from the certified historical dataset layer without reopening optional enrichment assets as blockers.
The next governed phase should populate reusable features from certified dataset rows and certified event context while preserving lineage, deterministic identities, and point-in-time safety.
