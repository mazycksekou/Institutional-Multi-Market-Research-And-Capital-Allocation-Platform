# Phase 10H16 – Calibration‑Ready Strategy Filter

## Overview

Phase 10H16 creates one calibration‑ready strategy filter that uses **Sport
Feature Packs**, **Market Feature Packs**, and the **Feature Ablation Lab**’s
active fields to decide which rows are allowed into calibration / testing.

It does **not** create preset experiment profiles (Phase 10H15 already
introduced the Feature Ablation Lab).  The new filter is an extra gate that
operators can enable *after* selecting a Feature Ablation profile.

## What it does

1.  Determines all safe pre‑decision fields (the same set as the Feature
    Ablation Lab).
2.  For **single‑sport** mode, the operator selects one sport, and only rows
    of that sport are examined.
3.  For **all‑sports** mode, sport readiness is evaluated for every
    normalised sport.  Sports that do not meet a configurable readiness
    threshold (≥80 % required coverage, ≥25 rows, usable/strong readiness
    level) are **excluded** from both performance calculations and ROI.
4.  Market families are evaluated similarly; only those that are ready are
    included.
5.  Every remaining row is diagnosed against the set of active fields and
    must meet a configurable field‑coverage percentage (default 60 %).
6.  Only rows that pass all gates contribute to the final performance
    summary.  **Excluded rows never count as losses.**

## Key design decisions

- **Leakage / result / settlement fields** are included in the never‑feature
  list and are never selectable as pre‑decision model inputs.  They are used
  only for post‑decision grading.
- The filter operates **entirely in the backend**.  The Streamlit dashboard
  only calls the public API and displays the returned data.
- No SQLite schema changes, no bankroll‑math rewrites, no new dependencies,
  no scraping, no network calls.
- The user‑facing wording is **“2‑Way / 3‑Way Moneyline”**; the legacy alias
  ``moneyline_or_1x2`` is not exposed preferentially.

## Files changed

| File | Change |
|------|--------|
| ``automation_scheduler/calibration_strategy_filter.py`` | **New** – main module |
| ``automation_scheduler/streamlit_dashboard_data.py`` | Added import and dashboard helper |
| ``streamlit_app.py`` | Added menu entry and UI section |
| ``tests/test_calibration_strategy_filter.py`` | **New** – backend tests |
| ``tests/test_streamlit_dashboard_data.py`` | Added 4 new tests |
| ``PHASE10H16_CALIBRATION_READY_STRATEGY_FILTER.md`` | This file |

## Next phase

Phase 10H17 – **Ablation Result Persistence / Experiment History** – will
add the ability to save and compare different filter configurations and their
results over time.
