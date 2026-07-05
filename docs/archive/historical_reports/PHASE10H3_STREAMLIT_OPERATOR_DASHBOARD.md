# Phase 10H3 Streamlit Operator Dashboard

Generated: 2026-06-12T22:55:29

## Added

- `automation_scheduler/streamlit_dashboard_data.py`
- `streamlit_app.py`
- `tests/test_streamlit_dashboard_data.py`

## Purpose

Build a local operator dashboard that is easy to read and safe for paper testing.

## Professional Design

- Streamlit is visual layer only.
- Helper logic is pure Python and testable without Streamlit installed.
- Missing dashboard files are handled gracefully.
- Dashboard JSON and Markdown can be generated on demand.
- Bankroll inputs are simple and visible.
- Regression tactic selection is explicit.
- One-sport and all-sports tests are separated.
- Easy Mode labels explain technical fields in plain language.

## Menus

1. Home / Explain Like I'm 8
2. Data Library
3. Paper Bets
4. Backtest Dashboard
5. Test One Sport
6. Test All Sports
7. Bankroll Settings
8. Regression Tactics
9. System Health

## Result

`streamlit_operator_dashboard_added`
