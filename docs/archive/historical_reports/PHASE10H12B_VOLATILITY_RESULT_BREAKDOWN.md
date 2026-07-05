# Phase 10H12B — Volatility Result Breakdown

## Summary

- **10H12A** provided the ability to measure line volatility (the raw availability signal).
- **10H12B** adds a result breakdown layer that answers the question:  
  *“Did low/medium/high/unknown volatility improve or hurt consistency?”*

## What changed

1. **`attach_volatility_to_backtest_rows`** (in `historical_line_movement.py`)  
   Matches backtest/projection decision rows to volatility groups using stable keys  
   (`event_id`, `market`, `selection`, `player_name`, `team_name`, `bookmaker`).  
   Attaches `volatility_level`, `line_move_up`, `line_move_down`, `line_total_range`,  
   `odds_move_up`, `odds_move_down`, `odds_total_range` to each row.  
   Input rows are never mutated.

2. **`summarize_results_by_volatility`** (in `historical_line_movement.py`)  
   Groups rows by `volatility_level` and computes:  
   - decisions, skipped decisions, settled count  
   - wins, losses, pushes  
   - `net_result`, `roi_percent`, `win_rate_percent`  
   - average line/odds move metrics  
   Returns operator‑friendly interpretation and any warnings.

3. **`get_volatility_result_breakdown_for_dashboard`** (in `streamlit_dashboard_data.py`)  
   Opens the SQLite store, retrieves volatility snapshots, and (if row‑level projection  
   results are provided) attaches volatility and summarizes.  
   If row‑level decisions are missing, returns an availability‑only view with a clear  
   warning instead of faking results.

4. **Streamlit UI** (in `streamlit_app.py`)  
   - The **Model Projection** tab now shows a “Volatility Result Breakdown” section  
     after a projection run.  
   - The **Backtest Dashboard** tab shows the same section when an existing dashboard  
     result is loaded.  
   - Both sections include explanatory text:  
     *“This shows whether low, medium, high, or unknown volatility produced better results.”*

5. **Tests**  
   Added six new tests for the volatility attachment and summary functions, and three  
   tests for the dashboard helper and the new Streamlit UI text.

## Next phase

**Phase 10H13 – Sport Feature Packs**  
Build predefined field groups per sport (NBA, MLB, NHL, EPL, etc.) to simplify data exploration and projection setup.
