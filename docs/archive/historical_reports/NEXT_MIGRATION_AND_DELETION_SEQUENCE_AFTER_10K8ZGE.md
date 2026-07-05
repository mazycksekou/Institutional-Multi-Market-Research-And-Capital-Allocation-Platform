# Next Migration and Deletion Sequence After 10K8ZGE

## Recommended Next Phases
1. **Connector isolation proof and migration**: move or wrap live client behavior from `kalshi_client.py`, `sharp_client.py`, and the remaining `automation_scheduler` live adapters into `src/connectors`.
2. **Core math/risk extraction**: transport reusable quant, pricing, probability, and bankroll math from `quant_engine.py`, `risk_engine.py`, `market_pricing.py`, and `model_probability.py` into `src/core`.
3. **Service orchestration thinning**: move `bet_decision_engine.py`, `bet_log.py`, `screenshot_intake.py`, and bridge helpers into `src/services`.
4. **Entrypoint/dashboard thinning**: reduce `main.py` and `streamlit_app.py` to thin shells that only wire canonical services together.
5. **Deletion proof for compatibility shims**: after import redirection and test redirection are complete, prove remaining compatibility shims are delete-ready and remove only the proof-backed ones.

## Deletion Policy
- Delete only after import proof, compatibility proof, and full local test proof are clean.
- Do not delete any file that still owns live network, credential, execution, or dashboard behavior.

## Strategic Notes
- Math/risk foundation integration comes after migration/deletion cleanup.
- AI/LLM integration comes after canonical math/risk/data/evaluation foundations are stable.
- `automation_scheduler` remains a decommission target until runtime bridges are no longer needed.

