# NFL Vertical Slice Recommendation

This document answers the question: what should the next NFL implementation slice be?

It includes a senior systems engineer review and a worldview compatibility review.

## Executive Summary

The repository is ready for a first reusable NFL vertical slice, but the slice should be small, canonical, and point-in-time safe.

The best next move is not to start with a broad model program.
It is to build a narrow data foundation that can support reproducible NFL diagnostics, then expand from there.

## Three Forward Paths

### Path 1: Open-data team/game foundation first

**Benefits**

- fastest path to a canonical NFL slice
- uses the strongest existing open-data lanes
- improves data lineage, feature reproducibility, and future backtesting
- fits the current architecture cleanly

**Drawbacks**

- does not immediately solve player-level depth for every position
- coaching and injury detail remain incomplete at first

**Long-term maintenance cost**

- low to moderate

**Scalability**

- high; team/game foundations are reusable across NFL, NCAAF, and future markets

**Technical debt introduced**

- minimal if the slice stays point-in-time and versioned

**Technical debt removed**

- removes the need for ad hoc, report-only NFL references later

**Alignment with canonical architecture**

- excellent

**Industry-standard comparison**

- matches common platform-first build order: canonical data first, model later

**Recommendation**

- **Preferred**

### Path 2: Coaching / availability / weather context first

**Benefits**

- improves player-level diagnostics quickly
- useful for props and matchup analysis
- strengthens the impact and relevance layers

**Drawbacks**

- blocked source families make this slower than it looks
- could overfit to incomplete availability data

**Long-term maintenance cost**

- moderate

**Scalability**

- good, but depends on source approvals and provenance quality

**Technical debt introduced**

- medium if pursued before a stable point-in-time data foundation

**Technical debt removed**

- helps close the biggest prop-model blind spots

**Alignment with canonical architecture**

- acceptable if layered on top of Path 1

**Industry-standard comparison**

- common for advanced sports-model work, but usually after the base data layer exists

**Recommendation**

- **Acceptable**

### Path 3: Paid / live / advanced charting first

**Benefits**

- can unlock richer player-level modeling
- may produce the most sophisticated future models

**Drawbacks**

- highest dependency risk
- greatest provenance / licensing burden
- least aligned with the repository's current free/open discovery posture
- easiest way to introduce duplicate or brittle branches of logic

**Long-term maintenance cost**

- high

**Scalability**

- potentially high, but only after a mature governance layer exists

**Technical debt introduced**

- high

**Technical debt removed**

- none at this stage

**Alignment with canonical architecture**

- weak for Phase 4.1

**Industry-standard comparison**

- common in mature commercial stacks, but not the right first step for this repo

**Recommendation**

- **Not Recommended**

## Senior Systems Engineer Recommendation

Choose **Path 1**.

Why:

- it is the safest canonical step
- it reuses the strongest existing code
- it makes the future data/model/backtest layers cheaper to maintain
- it preserves the repository's platform-first architecture

Then layer **Path 2** on top once the base slice is real and reproducible.

Avoid Path 3 until the repository has a stable data foundation and stronger governance around source licensing, provenance, and duplicate ownership.

## Smallest Reusable NFL Vertical Slice

The smallest reusable implementation slice should be:

1. point-in-time NFL schedule / results / play-by-play foundation
2. canonical coaching and availability context where validated
3. weather and market snapshot context
4. reproducible feature snapshot generation
5. one football impact diagnostics path
6. one Streamlit dashboard view that renders the canonical reports

That slice is small enough to be maintainable and large enough to prove the architecture.

## Worldview Intelligence Review

This phase already improves the future Worldview Intelligence Layer in several ways:

- better experiment generation via clear feature families
- better hypothesis testing via explicit diagnostics
- better feature discovery via source / field catalogs
- better reproducibility via point-in-time contracts
- better data lineage and feature lineage via canonical contracts
- better explainability via risk and calibration surfaces

### What would help even more later

The next phase should consider explicit contracts for:

- experiment registry
- hypothesis registry
- evidence pack / citation pack
- feature lineage metadata
- model lineage metadata

These should be added only when they belong to the implementation phase, not retrofitted prematurely.

## Recommendation for Phase 4.2

Build the canonical NFL data foundation slice first, then expand to coaching/availability and position-specific player modeling.

That is the most maintainable path and the best match for the existing architecture.

