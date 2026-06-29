# Roadmap to Data Migration and Backtesting After 10K8ZMP

1. Stabilize and commit current scheduler removal checkpoint
   - Objective: lock the current migration state into a clean commit.
   - Blocker: dirty worktree and uncommitted compatibility bridge.
   - Success: clean git status and checkpoint commit.
   - Estimated phases: 1

2. Decommission `src.automation_scheduler_legacy`
   - Objective: retire the compatibility bridge.
   - Blocker: remaining active callers and historical proof references.
   - Success: zero active imports and delete-ready proof.
   - Estimated phases: 1-2

3. Final zero-dependency scan
   - Objective: confirm no runtime/test/internal dependencies remain.
   - Blocker: any lingering bridge usage.
   - Success: zero dependency proof docs.
   - Estimated phases: 1

4. Final scheduler-decommission proof
   - Objective: prove the bridge is safe to remove.
   - Blocker: any active runtime or test dependency.
   - Success: delete-ready classification for the bridge.
   - Estimated phases: 1

5. Market intelligence data adapter inventory
   - Objective: identify remaining market data ingestion surfaces.
   - Blocker: incomplete canonical data-owner mapping.
   - Success: complete adapter inventory and target map.
   - Estimated phases: 1

6. Market intelligence data adapter implementation
   - Objective: absorb remaining data adapters into `src.market_intelligence`/`src.data`.
   - Blocker: any live API or credential coupling.
   - Success: canonical local-only adapters.
   - Estimated phases: 1-2

7. Data migration layer expansion
   - Objective: broaden canonical data contracts.
   - Blocker: unresolved legacy payload parity.
   - Success: stable `src.data` migration layer.
   - Estimated phases: 1-2

8. Backtesting dataset integration
   - Objective: connect canonical data into replayable datasets.
   - Blocker: dataset schema drift.
   - Success: backtesting datasets use canonical data contracts.
   - Estimated phases: 1-2

9. Backtesting replay/simulation integration
   - Objective: wire replay and simulation to canonical datasets.
   - Blocker: leakage or replay contract gaps.
   - Success: deterministic local-only replay/simulation.
   - Estimated phases: 1-2

10. Intelligence report backtesting
    - Objective: evaluate market-intelligence outputs in replay.
    - Blocker: missing standard report contracts.
    - Success: backtestable intelligence reports.
    - Estimated phases: 1

11. Read-only dashboard/API reporting
    - Objective: publish read-only views over canonical data and backtests.
    - Blocker: dashboard parity gaps.
    - Success: no-write reporting surfaces.
    - Estimated phases: 1

12. Final pre-live validation harness
    - Objective: prepare the final no-live-activation validation suite.
    - Blocker: any remaining live-activation boundary gap.
    - Success: end-to-end readiness proof with live behavior still disabled.
    - Estimated phases: 1
