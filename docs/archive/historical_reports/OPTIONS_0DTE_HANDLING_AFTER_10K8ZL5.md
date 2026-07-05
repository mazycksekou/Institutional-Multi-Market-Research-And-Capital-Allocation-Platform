# Options 0DTE Handling After 10K8ZL5

- If `T <= 0`, the option is ignored.
- Positive remaining time is floored at 1 minute by default.
- Extremely far-OTM strikes are filtered out locally.
- Intraday OI is treated as stale.

