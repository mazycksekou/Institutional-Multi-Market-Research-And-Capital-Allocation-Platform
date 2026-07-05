# AI/LLM Runtime Risk Map After 10K8ZI6

| File | Live call risk | Scheduler coupling | Future canonical target |
| --- | --- | --- | --- |
| `automation_scheduler/deepseek_reviewer.py` | Yes | Yes | `src.ai.disabled_client` then `src.services` later |
| `automation_scheduler/deepseek_profit_lab.py` | Yes | Yes | `src.ai.disabled_client` then `src.services` later |
| `automation_scheduler/institutional_deepseek_review.py` | Yes | Yes | `src.ai.disabled_client` then `src.services` later |
| `automation_scheduler/deepseek_prompt_contracts.py` | No | Yes | `src.ai.prompt_policy` |
| `automation_scheduler/deepseek_response_validator.py` | No | Yes | `src.ai.contracts` |
| `automation_scheduler/deepseek_daily_report.py` | No | Yes | `src.research` / `src.analytics` later |
| `automation_scheduler/deepseek_disagreement_queue.py` | No | Yes | `src.research` later |
| `automation_scheduler/deepseek_data_pull_check.py` | No | Yes | `src.research` / `src.services` later |
| `automation_scheduler/advanced_red_team_report.py` | No | Yes | `src.analytics` / `src.research` later |
| `src/api/automation_deepseek_routes.py` | No | Yes | `src.services` later |
| `main.py` | No | Yes | keep as bootstrap shell |

