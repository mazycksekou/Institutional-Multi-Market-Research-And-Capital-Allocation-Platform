# ORPHAN_CODE_REPORT_AFTER_10K8ZFM

## Executive Summary
Static import analysis found several files with no obvious inbound imports, but not all of them are dead. Some are intentional entrypoints or compatibility shells. Others are genuine manual-review candidates. No deletion is allowed in this phase.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## Method
I treated a file as orphan-like when:
- it had no obvious static importers in the repo scan
- it was not clearly a test fixture or package `__init__` that exists only for packaging
- it was not a known runtime entrypoint

I treated the following as not-orphaned even if static import counts were low:
- `main.py`
- `streamlit_app.py`
- `api_server.py`
- `scripts/*.py` entrypoints
- compatibility shells such as `automation_scheduler/__init__.py`

## Not Orphaned Despite Weak Static Inbound Counts
These files are executable entrypoints or compatibility shells and should not be treated as dead code:
- `main.py` - FastAPI app assembly entrypoint
- `api_server.py` - dynamic proxy to `main.py`
- `streamlit_app.py` - Streamlit dashboard shell
- `scripts/daily_data_hygiene.py` - daily hygiene wrapper
- `scripts/r2_archive_pipeline.py` - archive pipeline CLI
- `scripts/ops_check.py` - ops wrapper
- `automation_scheduler/__init__.py` - broad compatibility facade
- `providers/__init__.py` - compatibility provider layer
- `betting_providers/__init__.py` - adapter export surface

## Orphan-Like / Manual Review Candidates

| File | Why it appears orphaned | Evidence we have | Missing evidence | Deletion forbidden in this phase | Next verification step |
| --- | --- | --- | --- | --- | --- |
| `authentication_scheduler/line_movement_import_contract.py` | No obvious inbound imports in the static scan | File exists; zero inbound edges in the import graph | Runtime caller, CLI hook, or test coverage | yes | Search for dynamic imports and manual execution references |
| `research_engine/decision_committee.py` | No obvious inbound imports | Package exists; static scan did not show a consumer | Whether it is launched manually or indirectly from a missing script | yes | Search `rg -n "decision_committee"` across repo and scripts |
| `research_engine/evidence_scorecard.py` | No obvious inbound imports | Package exists; static scan did not show a consumer | Whether it is used by a hidden workflow or not | yes | Search `rg -n "evidence_scorecard"` and check test coverage |
| `config.py` | Zero static inbound edges from the import graph | Top-level config module exists | Dynamic loads, manual imports, or environment usage | yes | Search for `import config` and inspect runtime startup paths |
| `logger_setup.py` | Zero static inbound edges | Top-level utility exists | Logging bootstrap via dynamic import or shell wrapper | yes | Search for `logger_setup` and startup hooks |
| `kalshi_client.py` | Zero static inbound edges in the graph | Top-level client module exists | If manually imported by scripts or notebooks | yes | Search for `kalshi_client` references before any cleanup decision |
| `sharp_client.py` | Zero static inbound edges in the graph | Top-level client module exists | If manually imported by scripts or notebooks | yes | Search for `sharp_client` references before any cleanup decision |
| `parlay_engine.py` | Very low/zero static inbound edges | Top-level engine module exists | If hidden by dynamic imports or legacy scripts | yes | Search for `parlay_engine` references and test coverage |
| `asian_markets.py` | Very low/zero static inbound edges | Top-level module exists | Whether it is an old research utility or live workflow dependency | yes | Search for `asian_markets` references and runtime hooks |
| `live_market_intelligence/` | Scaffold tree only | Directory exists with zero files | Whether future files will populate it | yes | Keep as scaffold until a real owner and contract exist |
| `models/` | Empty directory | Directory exists with zero files | Whether it is intended as a future model store | yes | Verify future artifact conventions before any removal |
| `unused/` | Empty directory | Directory exists with zero files | Whether it is intentionally reserved | yes | Confirm whether the folder is a placeholder or accidental |

## Compatibility-Only Modules
These are not orphaned, but they are compatibility-heavy and should be treated as retirement targets only after wrappers stabilize:
- `automation_scheduler/__init__.py`
- `providers/__init__.py`
- `betting_providers/__init__.py`
- `api_server.py`
- `tests/support/action_imports.py`

## Legacy / Deprecated-Looking Code
The following modules look legacy because they sit outside the canonical owner map or because they keep old naming conventions alive:
- `market_pricing.py`
- `quant_engine.py`
- `risk_engine.py`
- `bet_log.py`
- `bet_decision_engine.py`
- `model_probability.py`
- `multi_sport_model_registry.py`
- `screenshot_intake.py`
- `full_board_engine.py`
- `logbook_engine.py`

These are not deletion candidates in this phase. They are manual-review candidates only.

## Test-Only / Support Code
- `tests/support/action_imports.py` is a test helper, not production code.
- The phase-report tests intentionally hard-code documentation strings and should be preserved as guardrails.

## Evidence Missing
For many of the manual-review candidates, we still lack:
- runtime entrypoint confirmation
- direct call graph evidence
- coverage evidence
- operational docs that state the file is intentionally reserved

## Conclusion
There are likely some genuine orphan candidates, but the safe answer is manual review, not deletion. Entry points and compatibility shells are especially easy to mislabel if we only look at static import counts.
