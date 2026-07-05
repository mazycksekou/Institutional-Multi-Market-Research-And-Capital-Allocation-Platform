# AI/LLM Credential Risk Map After 10K8ZI6

| File | Import-time credential read | Runtime credential read | Notes |
| --- | --- | --- | --- |
| `config.py` | Yes | Yes | Reads `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, and other env settings during bootstrap. |
| `main.py` | Yes | Yes | Reads API/bootstrap env values during import. |
| `automation_scheduler/ai_provider_security.py` | No | Yes | Env reads are inside helper functions, not import time. |
| `automation_scheduler/advanced_red_team_provider_policy.py` | No | Yes | Env reads are inside helper functions, not import time. |
| `automation_scheduler/deepseek_reviewer.py` | No | Yes | Runtime DeepSeek config is assembled locally from env. |
| `automation_scheduler/deepseek_profit_lab.py` | No | Yes | Runtime API-key and endpoint checks are performed locally. |
| `automation_scheduler/institutional_deepseek_review.py` | No | Yes | DeepSeek URL/model are resolved only at call time. |
| `src/providers/policy/secret_policy.py` | No | Yes | Secret names are static; env presence is checked only in helper calls. |
| `src/api/automation_deepseek_routes.py` | No | No | Route exposure only; no credential access. |
| `src/ai/*` | No | No | New scaffold is credential-free. |

