# NFL Gap Analysis

This report identifies what is still missing before the repository can support a full reusable NFL vertical slice.

## Critical Gaps

| Gap | Why it matters | Current evidence |
|---|---|---|
| No fully validated NFL ingestion slice | Without validated inputs, feature snapshots and backtests remain theoretical | feature builders report `no_validated_records_for_source` and coaching builders report `no_coaching_records_available` |
| No point-in-time NFL feature store populated with real rows | The backtest and model layers need reproducible feature snapshots | cutoff-week helpers exist, but stored snapshots are not yet a real NFL dataset |
| No settled-outcome calibration bucket set | Calibration and CLV/ROI checks need real outcomes | football diagnostics mark calibration as `insufficient_data` |
| Coaching sources are blocked | Coaching continuity and staff-turnover work needs a source lane | coaching source report flags robots / terms / provenance blockers |
| No official injury/availability lane | Player-level diagnostics are constrained without stronger availability signals | availability context exists, but source-backed validation is missing |

## High Gaps

| Gap | Why it matters | Current evidence |
|---|---|---|
| No complete NFL backtest dataset | Backtesting needs decision-time snapshots plus settled outcomes | backtest contract exists, but the data slice is incomplete |
| No NFL-specific model pipeline | Model outputs depend on a reproducible feature slice | `test_nfl_model_activation.py` exists, but the repo is still diagnostics-first |
| No fully populated Streamlit NFL data pages | The dashboard can show readiness and reports, but not a production NFL data plane | `streamlit_dashboard_facade.py` provides report helpers rather than a full NFL store |
| No validated officials lane | Officials are catalogued, but not in an end-to-end usable feed | field catalog only |
| No validated medical lane | Injury and practice data are still partial/contract-only | availability context remains a modifier layer |

## Medium Gaps

| Gap | Why it matters | Current evidence |
|---|---|---|
| Better free/open coaching source coverage | Would improve continuity and role context | current source families are mostly blocked |
| Better player-tracking depth | Would improve role and matchup nuance | tracking is explicitly not required yet |
| More complete market history / open-close alignment | Needed for CLV and calibration | historical odds helpers exist, but NFL-specific settled slices are incomplete |
| Wider special-teams support | Useful for certain props and game-state models | contract exists; validated lane does not |

## Low / Future Gaps

| Gap | Why it matters | Current evidence |
|---|---|---|
| Advanced charting / tracking providers | would sharpen advanced player models | current discovery marks several lanes as research-only or blocked |
| Live execution / paper trading | useful later, but out of scope for Phase 4.1 | explicitly forbidden in this phase |
| Paid-provider integrations | may be useful later, but should not be the default path | paid lanes are blocked or budget gated |

## Missing Contracted Pieces

The following contract files exist or are being created to make the missing slices explicit:

- `docs/contracts/NFL_CANONICAL_DATA_CONTRACT.md`
- `docs/contracts/NFL_BACKTEST_CONTRACT.md`
- `docs/contracts/NFL_FEATURE_STORE_CONTRACT.md`
- `docs/contracts/NFL_STREAMLIT_CONTRACT.md`
- `docs/contracts/NFL_PROVIDER_CONTRACT.md`
- `docs/contracts/NFL_ATOMIC_FEATURE_CONTRACT.md`
- `docs/contracts/NFL_COMPOSITE_FEATURE_CONTRACT.md`
- `docs/contracts/NFL_POSITION_GROUP_FEATURE_CONTRACT.md`

## Priority Ranking

- **Critical**: validated NFL inputs, point-in-time feature snapshots, settled-outcome calibration bucket set, coaching source viability
- **High**: backtest dataset, model pipeline, officials lane, medical lane
- **Medium**: richer open coaching sources, market history alignment, special teams
- **Low**: deeper charting / tracking
- **Future**: live execution, paper trading, paid providers

## Practical Conclusion

The repo is not blocked architecturally.
It is blocked on the final reusable data slice needed to move from discovery into a real vertical-slice implementation.

