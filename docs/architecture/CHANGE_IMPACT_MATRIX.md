# Change Impact Matrix

This matrix is a quick routing aid for future edits.
It maps the changed subsystem to the validation and downstream review it should trigger.

| Changed subsystem | Downstream impact | Required validation | Optional validation | Full-gate requirement |
| --- | --- | --- | --- | --- |
| Repository OS and execution policy | Changes how future tasks are discovered, scoped, and validated | Focused docs tests, document lifecycle check, repo preflight | Root markdown check if root docs are touched | Full gate only if the policy changes validation thresholds or shared contracts |
| Project status and next action | Changes live status, sequencing, and the handoff surface for the next task | Docs tests for status files, document lifecycle check, repo preflight | Roadmap check if sequencing text changes | Full gate only if sequencing or phase ownership changes materially |
| Master roadmap and document indexes | Changes long-range sequencing, current-truth discoverability, or retention registration | Docs tests, document lifecycle check | No additional validation if only links move | Full gate only if current-truth ownership or retention rules change |
| Historical runtime or storage | Can affect dataset creation, lineage, certification, and persisted evidence | Targeted runtime tests, compileall, adjacent regressions | Smoke tests if the change is narrow and isolated | Full gate when storage schema, lineage, certification, or lifecycle behavior changes |
| Feature, math, signal, decision, or backtest layers | Can affect downstream evidence and readiness across the chain | Targeted layer tests plus adjacent shared-runtime regressions | Docs tests if only commentary changes | Full gate when a shared evidence contract or persisted shape changes |
| Dashboard and readiness surfaces | Can affect reconstruction from persisted state and human review | Focused dashboard/readiness tests | Docs tests if only labels changed | Full gate when joins, readiness derivation, or persisted-state reconstruction changes |

If a change crosses two rows in this matrix, validate the shared boundary first and then widen only as needed.
