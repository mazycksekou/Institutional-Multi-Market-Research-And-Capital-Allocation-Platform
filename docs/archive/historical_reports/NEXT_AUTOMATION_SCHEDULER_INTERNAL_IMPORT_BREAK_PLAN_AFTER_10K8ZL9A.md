# Next Automation Scheduler Internal Import Break Plan After 10K8ZL9A

Remaining scheduler blockers after this batch:

- 13 internal scheduler self-importing files
- 299 test imports

Next practical step:

1. Break internal scheduler self-import chains by moving reusable logic into `src.market_intelligence`, `src.core`, `src.services`, `src.data`, `src.backtesting`, `src.analytics`, `src.research`, `src.ai`, or `src.brokerage` as appropriate.
2. Redirect test imports away from `automation_scheduler` where behavior is already covered canonically.
3. Re-run import scans before any deletion attempt.
