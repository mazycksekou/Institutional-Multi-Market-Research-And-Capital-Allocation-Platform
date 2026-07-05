# Automation Scheduler Decommission Sequence After 10K8ZHG

1. Keep the canonical bridge paths in `src.services` as the runtime ownership boundary.
2. Move safe, local-only scheduler orchestration into `src.services` where dependency proof exists.
3. Leave dashboard helpers in `automation_scheduler/streamlit_dashboard_data.py` only until a service-side replacement exists.
4. Keep provider classification and registry compatibility shells until import-proof and test redirection are complete.
5. Decommission `automation_scheduler` only after runtime, test, and compatibility proof clears the remaining shells.
