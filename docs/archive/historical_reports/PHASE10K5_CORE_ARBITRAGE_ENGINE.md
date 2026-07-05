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
| `automation_scheduler/arbitrage/two_way_arbitrage.py` | Two‑way sports arbitrage detection | Source scan (`detect_two_way_arbitrage` function confirmed) | Positive (+120/+120) and negative (–110/–110) cases validated. | **Yes** | Use as‑is (`detect_prediction_arbitrage` added, no extra helper). | Low. |
| `automation_scheduler/arbitrage/three_way_arbitrage.py` | Three‑way / multi‑outcome arbitrage | Source scan (expected `detect_three_way_arbitrage`) | +250/250/250 → arbitrage proven. | **Yes** | Use as‑is (no extension needed). | Medium (same naming risk). |
| `automation_scheduler/prediction_market_outcome_candidates.py` | Prediction‑market yes/no outcome logic | Source scan (`evaluate_outcome_evidence`) | yes=0.47, no=0.47 → arbitrage; yes=0.53, no=0.51 → no arbitrage. | **Yes** | Use as‑is. | Low. |
| `research/market_research_schema.py` | SQL table definitions, including `arbitrage_opportunities` | `get_create_sql("arbitrage_opportunities")` | Table SQL returned successfully; name present. | **Yes** | Reference only. No schema changes needed. | None. |
| `quant_engine.py` | Kelly, EV, bankroll math (unused here) | Not inspected | Not required for 10K5 core math. | **No** | Document for next phase. | N/A. |
| `risk_engine.py` | Bankroll, stake sizing (unused here) | Not inspected | Same. | **No** | Document for next phase. | N/A. |
| `automation_scheduler/liquidity_risk.py` | Stale‑odds / execution risk (unused here) | Not inspected | Not in 10K5 scope. | **No** | Document for next phase. | N/A. |

### Summary of used / extended owners

- **Used without change:** `math_utils`, `odds_math`, `three_way_arbitrage`, `prediction_market_outcome_candidates`, `market_research_schema`.
- **Extended:** `two_way_arbitrage.py` – added `detect_prediction_arbitrage` (a pure‑math yes/no price arbitrage helper). The dutching/stake‑allocation helper is defined in the test file only.
- **Created (if needed):** **None.** A new package was not required because the combination of existing owners plus one tiny inline test helper covers all 10K5 math.

### No‑vig normalisation

Provided via a pure‑Python helper `no_vig(prob1, prob2)` defined in the test file itself.  
If an existing owner supplies the same normalisation later, the test can be updated to call it instead.

### Dutching / stake allocation

The tiny helper `equal_gross_payout_stake` is defined directly in the test file.  
It performs proportional allocation based on decimal odds (derived from implied probabilities).  
No production code is modified for dutching.

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


## Phase 10K5 Targeted Fix: Existing Owner Wiring

Actual owner behavior found during the targeted failure loop:

- `automation_scheduler.arbitrage.two_way_arbitrage.detect_two_way_arbitrage`
  takes one positional `offers` list plus keyword-only options. The 10K5
  tests were corrected to call the existing owner instead of assuming a
  two-positional-argument interface.
- `automation_scheduler.arbitrage.three_way_arbitrage.detect_three_way_arbitrage`
  takes one positional `offers` list plus keyword-only options. The 10K5
  tests were corrected to provide explicit three-outcome selections.
- `automation_scheduler.prediction_market_outcome_candidates.evaluate_outcome_evidence`
  is settlement/evidence logic, not a prediction-market yes/no arbitrage owner.
  It was rejected as an arbitrage owner.
- `automation_scheduler.arbitrage.two_way_arbitrage.detect_prediction_arbitrage`
  was added as a tiny pure helper inside an existing arbitrage owner, avoiding a
  duplicate arbitrage package.
- No live connectors, API calls, Streamlit imports, pandas requirement, database
  writes, prediction testing, frontend changes, runtime migration, or duplicate
  cleanup were added.

