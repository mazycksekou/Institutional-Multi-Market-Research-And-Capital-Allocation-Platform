# Validation Ownership Map

This map assigns validation ownership to the canonical subsystem that produces the evidence.
Targeted validation is sufficient when the change is local to one subsystem and does not alter shared contracts.
The full repository gate is required when shared runtime, storage, certification, lifecycle, governance, or contract behavior changes.

| Subsystem | Canonical owner | Required validation | Targeted validation is sufficient when | Full repository gate is required when |
| --- | --- | --- | --- | --- |
| Governance docs and indexes | `docs/PROJECT_STATUS.md`, `docs/NEXT_ACTION.md`, `docs/STATUS_UPDATE_POLICY.md`, `docs/MASTER_ROADMAP.md`, `docs/MASTER_DOCUMENT_INDEX.md`, `docs/DOCUMENT_RETENTION_INDEX.md` | Doc tests, `python scripts/check_document_lifecycle.py`, repo preflight | Only wording, links, or index entries change | Sequencing, retention policy, or live-truth ownership changes |
| Repository OS | `docs/architecture/REPOSITORY_OS.md` | Focused docs tests, document lifecycle check, repo preflight | The policy text changes without changing validation thresholds | Execution rules, validation routing, or ownership boundaries change |
| Architecture contracts | `docs/architecture/*`, `docs/contracts/*` | Focused docs tests plus direct contract checks | One contract changes without altering shared ownership | A shared contract or canonical index changes |
| Historical runtime and storage | `src/data/*`, `src/storage/*` | Targeted runtime tests, `python -m compileall src tests scripts`, adjacent regressions | A single runtime owner changes and downstream APIs stay stable | Storage schema, lineage, certification, or lifecycle behavior changes |
| Feature, math, signal, decision, and backtest layers | `src/data/feature_registry.py`, `src/data/math_engine_population.py`, `src/market_intelligence/signal_population.py`, `src/backtesting/decision_row_population.py`, `src/backtesting/*` | Targeted layer tests, adjacent shared-runtime tests, `compileall` | Only one layer changes and the upstream evidence contract is unchanged | Shared upstream contracts, lineage, or persisted shapes change |
| Dashboard and readiness surfaces | `src/data/nfl_p0_foundation.py`, `src/services/streamlit_dashboard_data.py` | Focused dashboard/readiness tests, adjacent runtime tests | Only display or summary projection changes | Reconstruction logic, readiness derivation, or persisted-state joins change |
| Validation scripts | `scripts/check_*.py`, `scripts/ops_check.py`, `scripts/run_tests.ps1` | Direct script execution, repo preflight, `git diff --check` | Script text or local guidance changes only | Script behavior, gate routing, or policy enforcement changes |

When in doubt, validate the changed subsystem first, then widen only if the change crosses a shared boundary.
