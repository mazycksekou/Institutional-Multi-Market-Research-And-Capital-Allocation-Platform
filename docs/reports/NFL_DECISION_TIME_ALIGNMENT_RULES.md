# NFL Decision-Time Alignment Rules

## Purpose

These rules define how NFL decision rows stay point-in-time safe.

## Core rule

Every field used in the row must be known at or before the same `decision_time`.

## Alignment rules

| Rule | Requirement |
| --- | --- |
| Single event | One row maps to one game only. |
| Single decision time | Every pregame field freezes at the same cutoff. |
| Odds snapshot timing | The odds snapshot time must be at or before decision time. |
| Feature snapshot timing | The feature snapshot time must be at or before decision time. |
| Weather timing | Use forecast timing, not actual game weather. |
| Injury timing | Use report timing as-of decision time, not later updates. |
| Depth chart timing | Use the latest snapshot available before decision time. |
| Closing line timing | Closing line can support CLV, but not pregame features. |
| Outcome timing | Outcome fields attach only after the game is complete. |
| Lineage timing | The lineage chain must point to frozen upstream datasets. |

## Disallowed patterns

- postgame results inside pregame features
- future odds inside a decision snapshot
- actual weather used as if it were forecast weather
- injury updates after the cutoff
- market close used as if it were known before kickoff
- mixed timestamps that do not resolve to one row-level decision time

## Practical rule

If a reviewer cannot explain when a field became known, the field is not aligned.

## Exclusion consequence

Misaligned rows are either:

- `NO_TRADE` if the row is complete but should be skipped
- `EXCLUDED` if the row is unsafe or incomplete
- `NEEDS_REVIEW` if the row is ambiguous
