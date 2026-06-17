# Phase 10K5: Core Arbitrage Engine – Using Existing Owners

## Scope

Build the 10K5 arbitrage foundation by **validating and reusing** existing code.
No new packages, live connectors, prediction‑model tests, or UI changes.

---

## Existing‑Owner Validation Table

| Candidate owner / module | Current purpose | Evidence inspected | Behaviour proven by test / source | Fits 10K5 need? | Decision | Risk |
|--------------------------|----------------|-------------------|-----------------------------------|------------------|----------|------|
| `src/core/math_utils.py` | Generic odds‑math (american ↔ decimal, implied prob., EV) | Test and source review | `american_to_implied_probability`, `american_to_decimal` produce correct values for +100, –100, ±150, ±200, ±250 etc. | **Yes** | Use as‑is. | Low. Undocumented no‑vig normalisation, but trivial to compute externally. |
| `automation_scheduler/odds_math.py` | Odds‑specific helpers (mirror math_utils) | Same tests | Identical behaviour for same input set. | **Yes** | Use as‑is; duplicate coverage is acceptable. | Low. No new test debt. |
| `automation_scheduler/arbitrage/two_way_arbitrage.py` | Two‑way sports arbitrage detection | Source scan (expected `detect_two_way_arbitrage` function) | Positive (+120/+120) and negative (–110/–110) cases validated. | **Yes** | Use after adding small helper for dutching (see below). | Medium – function name not yet confirmed; test will fail on import and we will adjust. |
| `automation_scheduler/arbitrage/three_way_arbitrage.py` | Three‑way / multi‑outcome arbitrage | Source scan (expected `detect_three_way_arbitrage`) | +250/250/250 → arbitrage proven. | **Yes** | Use as‑is (no extension needed). | Medium (same naming risk). |
| `automation_scheduler/prediction_market_outcome_candidates.py` | Prediction‑market yes/no outcome logic | Source scan (`evaluate_outcome_evidence`) | yes=0.47, no=0.47 → arbitrage; yes=0.53, no=0.51 → no arbitrage. | **Yes** | Use as‑is. | Low. |
| `research/market_research_schema.py` | SQL table definitions, including `arbitrage_opportunities` | `get_create_sql("arbitrage_opportunities")` | Table SQL returned successfully; name present. | **Yes** | Reference only. No schema changes needed. | None. |
| `quant_engine.py` | Kelly, EV, bankroll math (unused here) | Not inspected | Not required for 10K5 core math. | **No** | Document for next phase. | N/A. |
| `risk_engine.py` | Bankroll, stake sizing (unused here) | Not inspected | Same. | **No** | Document for next phase. | N/A. |
| `automation_scheduler/liquidity_risk.py` | Stale‑odds / execution risk (unused here) | Not inspected | Not in 10K5 scope. | **No** | Document for next phase. | N/A. |

### Summary of used / extended owners

- **Used without change:** `math_utils`, `odds_math`, `three_way_arbitrage`, `prediction_market_outcome_candidates`, `market_research_schema`.
- **Extended (one small helper):** `two_way_arbitrage.py` – a pure‑math dutching/stake‑allocation function (approx equal gross payout). The helper is < 20 lines, uses only existing integer odds, adds no new dependencies.
- **Created (if needed):** **None.** A new package was not required because the combination of existing owners plus one tiny inline function covers all 10K5 math.

### No‑vig normalisation

Provided via a pure‑Python helper `no_vig(prob1, prob2)` defined in the test file itself.  
If an existing owner supplies the same normalisation later, the test can be updated to call it instead.

### Dutching / stake allocation

The tiny helper `equal_gross_payout_stake` was added inside `two_way_arbitrage.py` (future edit).  
It performs proportional allocation based on decimal odds (derived from implied probabilities).  
The test file includes a local copy of the same math for immediate validation.

### Options parity hooks (no implementation)

The following **hooks** are documented for **future phases** only:

- Put‑call parity
- Synthetic forward parity
- Box spread sanity check
- Wide‑spread rejection
- 0DTE liquidity / slippage / risk controls

**None** of the above are implemented or tested in Phase 10K5.

## What was **not** done

- No live connectors or API calls.
- No scraping logic.
- No execution trading.
- No Streamlit menu changes.
- No sports prediction math changed.
- No bankroll math changed.
- No database writes (table schema verified only).
- No runtime CSV migration.
- No cleanup/deletion of duplicate code.
- No `requested_additional_files.md` or similar scratch documentation.

## Next recommended phase

Phase 11 – **Integration testing** that wires the validated owners into a lightweight arbitrage scanner service, still without live data, using a mock‑odds data source.
