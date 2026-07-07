# Architecture Enforcement Current State

Branch: `phase-6-api-slimming`

Current state snapshot:

- Root runtime Python files: `api_server.py`, `main.py`, `orb_backtest.py`, `streamlit_app.py`, `zero_dte_orb.py`
- Approved entrypoints: `api_server.py`, `main.py`, `orb_backtest.py`, `streamlit_app.py`, `zero_dte_orb.py`
- Root Markdown offenders: none
- Ignored `src/**/*.py` files: none
- Direct legacy executable import targets: none
- Archived migration-proof tests: 266

Observed repository shape:

- Runtime/application code is under `src/`
- Tests are under `tests/`
- Scripts are under `scripts/`
- Documentation is under `docs/`
- Legacy scheduler compatibility import surfaces have been retired from active Python imports

Notes:

- Historical migration-proof tests are archived by `tests/conftest.py` and do not block the active product gate.
- Legacy identifier strings still exist in some metadata and endpoint names, but they are not active import surfaces and are not counted by the architecture gate.
