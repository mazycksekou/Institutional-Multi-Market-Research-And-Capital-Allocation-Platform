# Dashboard Thinning Sequence After 10K8ZHF

1. Keep `main.py` as the bootstrap shell.
2. Keep `streamlit_app.py` as the display/UI shell.
3. Move any reusable orchestration logic into services when it can be done without a dashboard rewrite.
4. Leave connector/provider ownership out of dashboard code.
5. Do not delete either entrypoint in this phase.
