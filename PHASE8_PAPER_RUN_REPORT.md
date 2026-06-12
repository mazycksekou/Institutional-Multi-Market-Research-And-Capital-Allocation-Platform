# Phase 8 Paper Run Baseline Report

Generated: 2026-06-12T15:14:09

- HEAD: `19dc577`
- Git clean at start: `True`

## Safety Environment
- PAPER_TRADING: `1`
- DRY_RUN: `1`
- DISABLE_LIVE_BETS: `1`
- ACTION_API_KEY: `SET`
- ODDS_API_KEY: `MISSING`
- THE_ODDS_API_KEY: `MISSING`
- DEEPSEEK_API_KEY: `MISSING`

## Compile / Import Checks
- main import: `PASS`
- main compile: `PASS`
- run once route compile: `PASS`
- scheduler tests compile: `PASS`

## Targeted Existing Test Checks
- targeted paper/scheduler pytest: `PASS`
```text
........................................................................ [ 84%]
.............                                                            [100%]
============================== warnings summary ===============================
..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\formparsers.py:12
  C:\Users\user\AppData\Local\Programs\Python\Python312\Lib\site-packages\starlette\formparsers.py:12: PendingDeprecationWarning: Please use `import python_multipart` instead.
    import multipart

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
```

## App Route Discovery
- Discovered candidate routes: `13`

| Methods | Path | Endpoint |
|---|---|---|
| `GET` | `/api/governance/report` | `get_governance_report_endpoint` |
| `GET` | `/api/performance/report` | `get_performance_report_endpoint` |
| `POST` | `/api/performance/paper-summary` | `run_performance_paper_summary_endpoint` |
| `GET` | `/api/actions/betting/clv-report` | `action_get_clv_report` |
| `GET` | `/api/automation/health` | `get_automation_scheduler_health` |
| `GET` | `/api/automation/advanced-red-team-report` | `get_automation_advanced_red_team_report_endpoint` |
| `GET` | `/api/automation/extreme-randomness-report` | `get_automation_extreme_randomness_report_endpoint` |
| `GET` | `/api/automation/review-queue` | `get_automation_scheduler_review_queue` |
| `GET` | `/api/automation/deepseek-daily-report` | `automation_deepseek_daily_report_endpoint` |
| `GET` | `/api/automation/data-sources/public-apis-expansion-report` | `get_public_apis_expansion_report_endpoint` |
| `GET` | `/api/automation/institutional-lab/report` | `get_institutional_lab_report_endpoint` |
| `GET` | `/api/automation/institutional-lab/daily-report` | `get_institutional_lab_daily_report_endpoint` |
| `POST` | `/api/automation/run-once` | `run_automation_scheduler_once` |

## Safe TestClient Route Smoke

| Status | Path | ok | error | detail |
|---:|---|---|---|---|
| 200 | `/api/governance/report` | `True` | `None` | `None` |
| 200 | `/api/performance/report` | `True` | `None` | `None` |
| 200 | `/api/performance/paper-summary` | `True` | `None` | `None` |
| 200 | `/api/actions/betting/clv-report` | `True` | `None` | `None` |
| 200 | `/api/automation/health` | `True` | `None` | `None` |
| 200 | `/api/automation/advanced-red-team-report` | `True` | `None` | `None` |
| 200 | `/api/automation/extreme-randomness-report` | `True` | `None` | `None` |
| 200 | `/api/automation/review-queue` | `True` | `None` | `None` |
| 200 | `/api/automation/deepseek-daily-report` | `True` | `None` | `None` |
| 200 | `/api/automation/data-sources/public-apis-expansion-report` | `True` | `None` | `None` |
| 200 | `/api/automation/institutional-lab/report` | `True` | `None` | `None` |
| 200 | `/api/automation/institutional-lab/daily-report` | `True` | `None` | `None` |
| 422 | `/api/automation/run-once` | `None` | `None` | `[{'type': 'extra_forbidden', 'loc': ['body', 'paper'], 'msg': 'Extra inputs are not permitted', 'input': True}, {'type': 'extra_forbidden', ` |

## Phase 8 Initial Result
OVERALL_OK: `True`
Safe paper-run baseline completed without hard failures.
