# Phase 10H23B – Operator UI Simplification

- **Main menu simplified** – only `Feature Ablation Lab`, `Test One Sport`, `Test All Sports`, `Bankroll Settings`, `Instructions` are visible.
- **Feature Ablation Lab** is now the default landing page.
- **Calibration‑Ready Strategy Filter** folded into Feature Ablation Lab as a collapsed expander.
- **Synthetic Line Movement Sandbox** and **Line Movement Data Quality Check** kept as collapsed review tools, not separate main pages.
- **No vendor connector, API, scraper, or paid data control was added.**
- **Phase 10H24** remains blocked until review.

### Changed files
- `streamlit_app.py` – menu list reduced; Feature Ablation Lab updated with collapsed sub‑sections.
- `streamlit_app.py` – added explanatory notes for synthetic sandbox and test flows.
