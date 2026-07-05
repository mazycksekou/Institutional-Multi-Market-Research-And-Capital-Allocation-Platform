# Streamlit Field Matrix

## Top-level dashboard layout

| Header | Purpose |
|---|---|
| `Instructions` | Dashboard usage overview |
| `Operator Summary` | Quick health snapshot |
| `Data Source Library` | Registered historical sources |
| `Import Historical Data` | Local file import workflow |
| `Data Quality Check` | Schema / snapshot review |
| `Data Explorer` | Field coverage exploration |
| `Model Projection` | Projection and projection preview |
| `Paper Bets` | Paper-trade preview |
| `Backtest Dashboard` | Backtest outputs and summaries |
| `Test One Sport` | Single-sport validation |
| `Test All Sports` | Multi-sport validation |
| `Bankroll Settings` | Operator bankroll controls |
| `Regression Tactics` | Strategy regression controls |
| `System Health` | Platform health snapshot |

## Metric surface

- Current AST scan found 79 unique `st.metric` labels in the dashboard file.
- The metric labels cluster around rows tested, readiness, profit, ROI, drawdown, duplicates, missing fields, linked snapshots, and system status.
- The dashboard also uses 9 top-level headers and a large set of subheaders to organize workflows.

## Feature-control profiles

| Profile | Meaning |
|---|---|
| Available Baseline | Use the fields we currently have without pretending missing fields exist |
| Odds Only | Test market/odds fields only |
| Remove Line Movement | Ignore line movement fields when not available |
| Settlement Check | Focus on whether outcomes/results exist |
| Custom Add/Remove | Operator chooses included/excluded fields |
