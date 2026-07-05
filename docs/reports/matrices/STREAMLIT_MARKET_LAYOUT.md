# Streamlit Market Layout

| Tab | Purpose | Next step |
|---|---|---|
| Instructions | Explains how to use the dashboard | Review the workflow and field groups |
| Operator Summary | Quick health snapshot of the latest model run | Explore Data Explorer if data seems sparse |
| Data Source Library | View all registered historical data sources | Pick one and import a local file |
| Import Historical Data | Upload a CSV or JSON file for a selected source | Visit Data Quality Check after import |
| Data Quality Check | File inventory, schema, and SQLite snapshot | Open Data Explorer to inspect field coverage |
| Data Explorer | Field coverage and missing-field analysis | Use feature control to shape the test |
| Model Projection | Projection / preview workflow | Compare against backtest and paper results |
| Paper Bets | Paper-trade preview | Review the paper ledger before considering any higher-risk work |
| Backtest Dashboard | Backtest outputs and summaries | Drill into bankroll and ROI sections |
| Test One Sport | Single-sport validation | Switch to Test All Sports once the lane is stable |
| Test All Sports | Multi-sport validation | Compare maturity across sport families |
| Bankroll Settings | Operator bankroll controls | Confirm risk posture before any scenario review |
| Regression Tactics | Strategy regression controls | Use for safe, local-only experimentation |
| System Health | Platform health snapshot | Inspect storage, readiness, and snapshots |

## Page-level notes

- The dashboard starts with instructions and operator summary.
- Historical data import and quality checks are first-class workflows.
- Model projection, paper bets, backtest dashboard, and test views are separately surfaced.
- Bankroll settings and regression tactics are treated as operator controls.
- System health is a dedicated page rather than an inline footer.
