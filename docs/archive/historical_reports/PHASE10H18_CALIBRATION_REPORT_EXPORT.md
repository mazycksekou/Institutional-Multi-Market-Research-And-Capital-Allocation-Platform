# Phase 10H18 – Calibration Report Export / Operator Review Pack

## Purpose
Phase 10H18 exports saved experiment history runs (ablation or calibration) as a clean, human‑readable Markdown review pack. Operators can review the results offline or share them internally without re‑running any model tests.

## What it does
- Fetch a saved run using the existing `get_experiment_history_run` helper.
- Build stable sections: summary, configuration, field selection, inclusion/exclusion, performance, ROI breakdown, warnings.
- Render the sections as deterministic Markdown.
- Provide the Markdown content to the Streamlit dashboard (no files written to disk by the backend).

## What it does **not** do
- Does **not** re‑run model tests.
- Does **not** create new model logic or presets.
- Does **not** alter any existing schemas (historical odds, line movement, experiment history).
- Does **not** introduce scraping or network calls.

## Technical notes
- `build_experiment_report_export()` calls `get_experiment_history_run` (unchanged).  
- `render_experiment_report_markdown()` uses `build_experiment_report_sections()` to produce a stable dict, then formats it into Markdown.  
- Leakage fields remain blocked as active pre‑decision fields; the report notes this safety rule.  
- Only Markdown export is supported in this phase.  
- The Streamlit dashboard calls the dashboard bridge `get_experiment_report_export_for_dashboard()`.

## Roadmap checkpoint
After Phase 10H22, stop before moving to Phase 10H24.  
**Phase 10H23 is a required checkpoint**: Line Movement Data Quality Dashboard.  
That phase will show coverage, missing links, duplicate games, sports, markets, books, and readiness.  
No real vendor connector, paid data connector, scraper, or API connector should be implemented before Phase 10H23 is reviewed.

## Files changed
1. `automation_scheduler/experiment_report_exporter.py` – new module.  
2. `automation_scheduler/streamlit_dashboard_data.py` – added import and `get_experiment_report_export_for_dashboard()`.  
3. `streamlit_app.py` – added Calibration Report Export subsection in Experiment History.  
4. `PHASE10H18_CALIBRATION_REPORT_EXPORT.md` – this file.  
5. `tests/test_experiment_report_exporter.py` – new test file.  
6. `tests/test_streamlit_dashboard_data.py` – added tests for the new dashboard bridge and source text checks.
# Phase 10H18 – Calibration Report Export / Operator Review Pack

## Purpose
Phase 10H18 exports saved experiment history runs (ablation or calibration) as a clean, human‑readable Markdown review pack. Operators can review the results offline or share them internally without re‑running any model tests.

## What it does
- Fetch a saved run using the existing `get_experiment_history_run` helper.
- Build stable sections: summary, configuration, field selection, inclusion/exclusion, performance, ROI breakdown, warnings.
- Render the sections as deterministic Markdown.
- Provide the Markdown content to the Streamlit dashboard (no files written to disk by the backend).

## What it does **not** do
- Does **not** re‑run model tests.
- Does **not** create new model logic or presets.
- Does **not** alter any existing schemas (historical odds, line movement, experiment history).
- Does **not** introduce scraping or network calls.

## Technical notes
- `build_experiment_report_export()` calls `get_experiment_history_run` (unchanged).  
- `render_experiment_report_markdown()` uses `build_experiment_report_sections()` to produce a stable dict, then formats it into Markdown.  
- Leakage fields remain blocked as active pre‑decision fields; the report notes this safety rule.  
- Only Markdown export is supported in this phase.  
- The Streamlit dashboard calls the dashboard bridge `get_experiment_report_export_for_dashboard()`.

## Roadmap checkpoint
After Phase 10H22, stop before moving to Phase 10H24.  
**Phase 10H23 is a required checkpoint**: Line Movement Data Quality Dashboard.  
That phase will show coverage, missing links, duplicate games, sports, markets, books, and readiness.  
No real vendor connector, paid data connector, scraper, or API connector should be implemented before Phase 10H23 is reviewed.

## Files changed
1. `automation_scheduler/experiment_report_exporter.py` – new module.  
2. `automation_scheduler/streamlit_dashboard_data.py` – added import and `get_experiment_report_export_for_dashboard()`.  
3. `streamlit_app.py` – added Calibration Report Export subsection in Experiment History.  
4. `PHASE10H18_CALIBRATION_REPORT_EXPORT.md` – this file.  
5. `tests/test_experiment_report_exporter.py` – new test file.  
6. `tests/test_streamlit_dashboard_data.py` – added tests for the new dashboard bridge and source text checks.
