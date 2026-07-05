# Configuration Governance

## Purpose

This repository treats configuration as explicit, documented input rather than hidden machine state.

The `.env.example` file is the starting point for local configuration, and the runtime code reads configuration from environment variables only when it needs them.

## Governance Rules

- Every non-secret config must have a documented purpose.
- Every secret-bearing config must be treated as sensitive even when the repository only checks for presence.
- Defaults must be explicit.
- Configuration should be grouped by owner so a new contributor can see which subsystem uses it.
- New configuration should be added to `.env.example` and documented here before it is relied upon in runtime code.

## Configuration Surface

The table below is derived from `.env.example` and current `os.getenv(...)` usage in runtime code.

| Variable | Owner | Purpose | Default / fallback | Secret? |
| --- | --- | --- | --- | --- |
| `ODDS_API_KEY` | Providers / betting data | Odds provider auth | empty / disabled | Yes |
| `ODDS_API_ENABLED` | Providers / betting data | Enables odds provider path | `true` | No |
| `ACTION_API_KEY` | API / auth | API key check for protected routes | empty / disabled | Yes |
| `SHARP_API_KEY` | Providers | Sharp provider auth | empty / disabled | Yes |
| `SHARP_API_BASE_URL` | Providers | Sharp provider endpoint | empty | No |
| `SHARP_API_ENABLED` | Providers | Enables sharp provider path | `false` | No |
| `OPENAI_API_KEY` | AI boundary | Credential presence for disabled AI-related surfaces | empty / disabled | Yes |
| `DEEPSEEK_ENABLED` | AI / research | Enables DeepSeek-boundary helpers | `false` | No |
| `DEEPSEEK_API_KEY` | AI / research | DeepSeek auth | empty / disabled | Yes |
| `DEEPSEEK_BASE_URL` | AI / research | DeepSeek endpoint | `https://api.deepseek.com` or local helper fallback | No |
| `DEEPSEEK_MODEL` | AI / research | Model selector | `deepseek-chat` | No |
| `DEEPSEEK_TIMEOUT_SECONDS` | AI / research | Request timeout | `20` | No |
| `DEEPSEEK_MAX_ITEMS_PER_REVIEW` | AI / research | Review batch size | `5` | No |
| `DEEPSEEK_DAILY_REPORT_ENABLED` | AI / reporting | Controls report generation | `true` | No |
| `DEEPSEEK_DISAGREEMENT_QUEUE_ENABLED` | AI / reporting | Controls disagreement queue | `true` | No |
| `KALSHI_ENABLED` | Providers | Prediction-market provider switch | `false` | No |
| `KALSHI_ENV` | Providers | Provider environment selector | `demo` | No |
| `KALSHI_BASE_URL` | Providers | Provider endpoint | empty | No |
| `KALSHI_API_KEY_ID` | Providers | Credential identifier | empty / disabled | Yes |
| `KALSHI_PRIVATE_KEY` | Providers | Private key material | empty / disabled | Yes |
| `DEFAULT_BETTING_PROVIDER` | Providers | Default sportsbook provider | `the_odds_api` | No |
| `DEFAULT_MARKET_PROVIDER` | Providers | Default prediction-market provider | `kalshi` | No |
| `DEFAULT_BOOKMAKERS` | Services / API | Default bookmaker list | `draftkings,fanduel,betmgm,caesars,espnbet,bet365` | No |
| `DEFAULT_REGIONS` | Services / API | Default region selector | `us` | No |
| `THE_ODDS_API_KEY` | Providers | Alternate odds provider key | `ODDS_API_KEY` fallback | Yes |
| `ALERT_WEBHOOK_URL` | Operations | Optional alert target | empty | Sensitive |
| `USE_MOCK_PROVIDERS` | Runtime / tests | Enables mock provider behavior | `true` | No |
| `DRY_RUN` | Runtime / tests | Prevents live side effects | `true` | No |
| `BACKGROUND_AGENT_ENABLED` | Operations | Enables background agent behavior | `false` | No |
| `LIVE_AGENT_INTERVAL_SECONDS` | Operations | Polling interval | `60` | No |
| `ODDS_STALE_SECONDS` | Data freshness | Odds freshness threshold | `90` | No |
| `LIVE_FEATURE_STALE_SECONDS` | Data freshness | Feature freshness threshold | `300` | No |
| `PROVIDER_CACHE_TTL_SECONDS` | Providers | Cache lifetime | `15` | No |
| `ALERT_DEDUPE_COOLDOWN_SECONDS` | Operations | Alert throttling | `1800` | No |
| `MIN_PROVIDER_REQUESTS_REMAINING` | Providers | Provider safety guard | `25` | No |
| `BANKROLL_UNITS` | Strategy / risk | Default bankroll size | `100` | No |
| `KELLY_FRACTION` | Strategy / risk | Kelly sizing multiplier | `0.25` | No |
| `MAX_STAKE_UNITS` | Strategy / risk | Max stake cap | `1.0` | No |
| `MAX_DAILY_RISK_UNITS` | Strategy / risk | Daily risk cap | `5.0` | No |
| `MAX_EVENT_RISK_UNITS` | Strategy / risk | Event risk cap | `2.0` | No |
| `MAX_CORRELATED_RISK_UNITS` | Strategy / risk | Correlated risk cap | `2.0` | No |
| `AUTOMATION_DATA_DIR` | Storage / ops | Local persistent storage root | repo-local `data/` fallback when unset | No |
| `APP_BASE_URL` | Ops / deployment | Public app base URL | unset unless deployed | No |
| `RENDER_API_KEY` | Deployment | Render API access | empty / optional | Yes |
| `COLLECTOR_CRON_TOKEN` | Operations | Scheduled task guard | empty / disabled | Yes |
| `SPORTS_MASTER_DB_PATH` | Storage | Backtest / historical DB path | `data/sports_master.db` | No |
| `CFBD_API_KEY` | Providers | College football data auth | empty / disabled | Yes |
| `INSTITUTIONAL_DEEPSEEK_REVIEW_ENABLED` | AI / research | Institutional review switch | `false` | No |
| `INSTITUTIONAL_DEEPSEEK_LOCAL_URL` | AI / research | Local LLM endpoint | `http://127.0.0.1:11434/api/generate` | No |
| `INSTITUTIONAL_DEEPSEEK_MODEL` | AI / research | Local review model | `deepseek-r1` | No |
| `AI_ANALYST_PROVIDER` | AI boundary | Analyst provider selector | canonical default | No |
| `OPENAI_ANALYST_MODEL` | AI boundary | Optional analyst model name | empty | Yes |
| `ADVANCED_RED_TEAM_PROVIDER` | Security / AI boundary | Red-team provider selector | canonical default | No |
| `OPENAI_RED_TEAM_MODEL` | Security / AI boundary | Optional red-team model name | empty | Yes |

## Secret Classification

- **Secret** means the variable should be treated as sensitive because it can authenticate to an external service or reveal operational capability.
- **Sensitive** means the value is not always a credential, but it may expose infrastructure behavior or deployment endpoints.
- Non-secret values may still affect behavior and should remain documented.

## Ownership Notes

- Provider variables belong to provider-facing boundaries.
- AI variables belong to the disabled AI boundary unless the runtime explicitly moves them elsewhere.
- Storage and ops variables belong to the local persistence and workflow layers.
- Strategy/risk variables belong to the sizing and safety boundary.

## Gaps

- `docs/.env.example` is authoritative, but configuration ownership should still be reviewed whenever a new variable is added.
- A future pass could group these variables into machine-readable sections if the repository needs automated config validation.
