# Engineering Standards

These standards keep the repository predictable for engineers, reviewers, and automation.

## Folder Rules

- Runtime/application code belongs under `src/`
- Tests belong under `tests/`
- Scripts and local tools belong under `scripts/`
- Documentation belongs under `docs/`
- Root Markdown should stay at `README.md` only

## Naming Rules

- Use names that describe the actual responsibility
- Do not rename functional code only for style
- Keep provider, connector, model, runtime, and adapter terms distinct when they refer to different responsibilities

## Import Rules

- Prefer canonical `src.*` imports
- Keep root entrypoints thin
- Do not create duplicate ownership in a second package
- Compatibility shims must be minimal and temporary

## Documentation Rules

- Create new Markdown directly in the correct `docs/` subfolder
- Archive historical evidence rather than deleting it when it still has audit value
- Keep public architecture docs vendor-neutral and implementation-light

## Testing Rules

- Run local validation before committing
- Keep smoke tests fast and representative
- Update tests only when the expected contract or path has legitimately changed

## Commit Guidance

- Make small, reviewable commits
- Use commit messages that describe the user-visible or structural change
- Commit after each clean logical migration or documentation package

## Versioning Guidance

- Increment versions only when a contract or behavior boundary changes
- Treat non-breaking documentation and governance updates as patch-level work
- Keep runtime version pins, CI version pins, and deployment descriptors synchronized whenever possible

## Reproducibility Guidance

- Document required tooling in `docs/operations/DEPENDENCY_REPRODUCIBILITY.md`
- Prefer pinned runtime dependencies and explicit environment descriptors
- Treat optional developer tools as optional unless a script or workflow genuinely requires them
- Use repo-local validation as the source of truth rather than ad hoc machine state

## Archive vs Delete

- Archive historical reports, proofs, and migration evidence when they remain useful
- Delete only files that are obsolete, duplicated, unreferenced, and not useful as audit evidence

## Adding a Provider

1. Define the provider responsibility in `src.providers`
2. Add connector or adapter code only where needed
3. Describe field coverage in the provider matrix
4. Validate the public contract and local architecture rules

## Release And Handoff

- Use repository pre-flight checks before commit and push
- Record modernization milestones and major governance changes in architecture or operations docs
- Prefer draft PRs or explicit review-ready PRs depending on the task scope

## Adding a Connector

1. Place the implementation in `src.connectors`
2. Keep the connector read-only unless a canonical owner explicitly requires otherwise
3. Reuse canonical data contracts
4. Add tests that prove the connector does not own duplicate business logic

## Adding a Model or Analysis Runtime

1. Keep the public interface vendor-neutral
2. Store private logic behind canonical `src.*` ownership
3. Do not expose feature engineering, calibration, or weights in public docs
4. Add backtest and governance coverage for the new runtime path

## Adding a New Market or Sport Lane

1. Add the domain to the canonical market intelligence layer
2. Define the required fields and storage expectations
3. Document backtest and Streamlit compatibility
4. Keep field ownership unique and traceable
