# PHASE10K8ZFR_PRODUCTION_MODULE_BOUNDARY_SCAFFOLD

## Executive Summary
This phase creates scaffold-only production module boundaries for future AI, brokerage, and connector systems. The repository now has explicit package landing zones under `src/ai`, `src/brokerage`, and `src/connectors` while `src/providers` remains the canonical product-category provider boundary.

The new packages are inert. They do not call external services, do not execute trades, do not scrape, do not infer, and do not change existing runtime behavior.

## Current HEAD
`a3bbc95`

## Purpose
Clarify the long-term architecture so future AI/LLM, brokerage/live-trading, and connector work can land in isolated production domains without being mixed into provider ownership or legacy vendor modules.

## Scope
- Create scaffold-only `src/ai/`, `src/brokerage/`, and `src/connectors/` packages.
- Update prior strategy documentation so AI, brokerage, and connector boundaries are treated as future production domains.
- Preserve all existing runtime behavior and legacy modules.

## Non-Goals
- No AI implementation.
- No commercial LLM calls.
- No model training.
- No broker execution.
- No real trade execution.
- No paper trading implementation yet.
- No scraper implementation.
- No live connector implementation.
- No external API calls.
- No runtime provider migration.
- No deletion of legacy runtime modules.
- No behavior changes.

## Relationship to 10K8ZFQ
10K8ZFQ classified many AI/vendor/broker/scraper references as delete candidates because they were legacy ownership signals, not because the future production domains should disappear. This phase corrects that interpretation: delete only vendor-specific or duplicate legacy ownership, but preserve the production domains as scaffolds under `src/`.

## Boundary Model
| Boundary | Responsibility | Must Not Do |
| --- | --- | --- |
| `src/providers` | product-category provider normalization and contracts | own AI decisions, brokerage execution, or raw connector mechanics |
| `src/ai` | AI/LLM/model reasoning boundary | call commercial LLMs, train models, infer at import time, or read secrets |
| `src/brokerage` | execution boundary for paper/live trading | submit orders, cancel orders, trade live, or read broker credentials |
| `src/connectors` | raw external data access boundary | scrape, open live connections, or call external APIs |

## What Belongs in `src/providers`
- Product-category provider contracts.
- Provider registry and health scaffolding.
- Normalization and category semantics.
- Prediction-market, 0DTE/stocks, and sportsbook ownership.

## What Belongs in `src/ai`
- Future AI/LLM interfaces.
- Model, prompt, evaluation, and policy scaffolds.
- Controlled reasoning boundaries only.

## What Belongs in `src/brokerage`
- Future execution interfaces.
- Risk control and order gateway scaffolds.
- Paper/live trading boundaries only.

## What Belongs in `src/connectors`
- Raw market-data connector scaffolds.
- Odds, prediction-market, and feed connector boundaries.
- Web-scraping boundary scaffolds, with no live access yet.

## What Must Not Cross Boundaries
- `src/providers` must not own AI reasoning, broker execution, or raw scraping.
- `src/ai` must not reach into provider transport or broker execution.
- `src/brokerage` must not fetch raw external data.
- `src/connectors` must not normalize product-category meaning or execute trades.

## Safety Guarantees
- Import-safe scaffold packages only.
- No network activity at import time.
- No credentials required at import time.
- No runtime behavior changes.
- No live API, trade, or scrape behavior.

## No-Network Guarantee
The new packages contain only inert package markers. They do not import live networking libraries, do not open sockets, and do not call external APIs.

## No-Execution Guarantee
The new packages do not submit orders, place trades, cancel orders, scrape pages, or run inference. Any future function in these boundaries must be introduced explicitly and safely.

## No-AI-Call Guarantee
The new `src/ai` scaffold does not call OpenAI, Anthropic, Gemini, Perplexity, Together, or any other model API. It is only a landing zone for future controlled AI work.

## Future Migration Strategy
1. Keep `src/providers` as the canonical category-owned provider boundary.
2. Land AI reasoning and evaluation under `src/ai` when explicitly approved.
3. Land execution logic under `src/brokerage` only after safety and risk controls exist.
4. Land raw data access and feed logic under `src/connectors` before anything else consumes it.
5. Keep vendor-specific and duplicate legacy ownership separate from these production domains.

## Required Statement
AI/LLM, brokerage/live-trading, and scraper/live-connector functionality are future production domains, not automatic deletion categories. They must be isolated under src/ai, src/brokerage, and src/connectors respectively before any implementation is authorized.

## Files Created
- `src/ai/__init__.py`
- `src/ai/llm/__init__.py`
- `src/ai/models/__init__.py`
- `src/ai/prompts/__init__.py`
- `src/ai/evaluation/__init__.py`
- `src/ai/policy/__init__.py`
- `src/brokerage/__init__.py`
- `src/brokerage/paper_trading/__init__.py`
- `src/brokerage/live_trading/__init__.py`
- `src/brokerage/execution/__init__.py`
- `src/brokerage/risk_controls/__init__.py`
- `src/brokerage/order_gateway/__init__.py`
- `src/connectors/__init__.py`
- `src/connectors/market_data/__init__.py`
- `src/connectors/odds_data/__init__.py`
- `src/connectors/prediction_market_data/__init__.py`
- `src/connectors/web_scraping/__init__.py`
- `src/connectors/feeds/__init__.py`
- `tests/test_phase10k8zfr_production_module_boundaries.py`

## Files Updated
- `FULL_VENDOR_REFERENCE_INVENTORY_AFTER_10K8ZFQ.md`
- `PROVIDER_PRODUCT_GOAL_ALIGNMENT_REPORT_AFTER_10K8ZFQ.md`
- `VENDOR_MODULE_DELETION_CANDIDATES_AFTER_10K8ZFQ.md`
- `PHASE10K8ZFQ_VENDOR_MODULE_AUDIT.md`

## Tests Run
`pytest tests/test_phase10k8zfr_production_module_boundaries.py tests/test_phase10k8zfo_src_providers_skeleton.py tests/test_phase10k8zfp_provider_taxonomy_correction.py -q`

Result: `10 passed`

## Smoke Checks Run
`rg -n "automation_scheduler|betting_providers|providers|requests|httpx|yfinance|selenium|playwright|openai|anthropic|alpaca|robinhood|ib_insync|ccxt" src/ai src/brokerage src/connectors`

`rg -n "AKIA|ASIA|your_real_secret|SECRET_ACCESS_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY" PHASE10K8ZFR_PRODUCTION_MODULE_BOUNDARY_SCAFFOLD.md FULL_VENDOR_REFERENCE_INVENTORY_AFTER_10K8ZFQ.md PROVIDER_PRODUCT_GOAL_ALIGNMENT_REPORT_AFTER_10K8ZFQ.md VENDOR_MODULE_DELETION_CANDIDATES_AFTER_10K8ZFQ.md PHASE10K8ZFQ_VENDOR_MODULE_AUDIT.md tests/test_phase10k8zfr_production_module_boundaries.py`

Result: no forbidden matches in the scaffold packages and no secret-like patterns in the report/doc set.

## Acceptance Results
Scaffold-only production boundaries created successfully. The new packages import safely, the provider taxonomy tests still pass, and the updated strategy documentation clarifies that AI, brokerage, and connector domains are future production boundaries rather than deletion categories.

## Next Recommended Phase
Proceed with the first controlled transport batch for the newly established production domains only after the boundary tests and provider taxonomy tests pass locally.
