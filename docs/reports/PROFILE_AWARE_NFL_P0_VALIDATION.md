# Profile-Aware NFL P0 Validation

## Architecture Before

The NFL P0 foundation already reused the shared storage engine, shared validation helpers, and shared dashboard readiness path. It was structurally compatible with the Sports Market Profile framework, but it did not explicitly resolve or validate itself through the profile registry at runtime.

That meant the NFL P0 foundation could produce canonical fixtures and readiness snapshots, but the profile relationship existed mostly by documentation and convention.

## Architecture After

The NFL P0 foundation now resolves the canonical `sports:nfl` profile through the shared market-profile registry and validates that profile before accepting NFL P0 datasets.

The NFL P0 readiness path now includes explicit profile validation so the foundation can report whether the dataset layer is aligned with the Sports Market Profile before any storage/bootstrap work is accepted.

## Integration Points

The following shared modules are now part of the runtime path:

- `src/data/market_profile_contracts.py`
- `src/data/market_profile_registry.py`
- `src/market_intelligence/market_profiles.py`
- `src/storage/local_store.py`
- `src/data/validation.py`
- `src/services/streamlit_dashboard_data.py`

The NFL-specific orchestration remains in:

- `src/data/nfl_p0_foundation.py`

## Shared Modules Reused

- **Market profile contracts** for canonical profile validation.
- **Market profile registry** for registry-backed profile resolution.
- **Shared validation helpers** for row validation.
- **Shared storage engine** for NFL P0 table bootstrap and persistence.
- **Shared dashboard readiness path** for reporting.

## Duplicate Logic Avoided

No duplicate profile framework, registry, storage engine, or readiness layer was created.

The NFL P0 module now uses the existing Sports Market Profile instance instead of introducing a new NFL-only profile subsystem.

The only NFL-specific code remains orchestration, fixture generation, and NFL table assembly.

## Profile Validation Flow

1. Resolve `sports:nfl` from the shared market-profile registry.
2. Register the canonical Sports Profile instance if the registry is empty.
3. Validate the resolved profile with shared contract validation.
4. Confirm the NFL instance matches the canonical Sports Profile shape.
5. Block bootstrap if the profile is invalid.
6. Include profile validation status in readiness and dashboard snapshots.

## Future Compatibility

### MLB

MLB can reuse the same pattern by defining a Sports Profile instance for `sports:mlb` and letting its P0 foundation resolve and validate that profile through the same registry and validation helper path.

### Prediction Markets

Prediction markets can use the same contract and registry path by resolving a `prediction_markets` profile and validating canonical identifiers, timestamps, storage, leakage, and backtest rules through the shared framework.

### Options / 0DTE

Options / 0DTE can reuse the same pattern through the existing `options_0dte` profile family without copying NFL-specific orchestration or storage logic.

## Remaining Gaps

- The profile-aware NFL P0 path currently validates the canonical profile, but it still relies on the existing NFL P0 orchestration module for actual fixture/bootstrap behavior.
- A future MLB, NBA, or prediction-market P0 implementation should follow the same profile-aware pattern to keep the architecture uniform.
- Additional profile-specific readiness dashboards may be added later, but they should continue to consume the shared readiness snapshot pattern.

