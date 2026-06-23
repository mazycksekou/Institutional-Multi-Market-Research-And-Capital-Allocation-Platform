# Remaining Legacy Runtime Owner Queue (After 10K8ZGZ)

These files still contain logic that will eventually be migrated to `src/core/` or `src/services/` or removed completely.  
They are **not** deletion candidates in this phase.

| File | Type |
|------|------|
| `automation_scheduler/` | Legacy workflow – decommission target |
| `quant_engine.py` | Top‑level quant wrappers |
| `risk_engine.py` | Risk helpers |
| `market_pricing.py` | Cross‑book aggregation |
| `model_probability.py` | Probability blending |
| `bet_decision_engine.py` | Line evaluation |
| `bet_log.py` | Bet logging |
| `screenshot_intake.py` | Screenshot analysis workflow |
| `main.py` | App bootstrap shell |
| `streamlit_app.py` | Dashboard UI shell |
| `src/api/*` | Route registrations |
| `src/services/*` | Orchestration bridges |

Ownership rules from the master phase apply:  
- `src/core/` owns reusable intelligence.  
- `src/services/` owns orchestration.  
- `main.py` and `streamlit_app.py` remain entrypoints.  
- `automation_scheduler/` is not to receive new ownership.
