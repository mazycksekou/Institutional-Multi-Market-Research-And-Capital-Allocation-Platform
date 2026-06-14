"""Calibration‑Ready Strategy Filter – Phase 10H16.

Uses Sport Feature Packs, Market Feature Packs, and Feature Ablation Lab
active fields to decide which rows are allowed into calibration/testing.

Architecture:
- Backend owns all filter/gating logic.
- Only eligible rows enter performance calculations.
- Never‑feature fields are excluded from pre‑decision features.
- Excluded sports/market families are reported with reasons, not counted as losses.

Dependencies:
- automation_scheduler.sport_feature_packs
- automation_scheduler.market_feature_packs
- automation_scheduler.feature_ablation_lab
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from automation_scheduler.sport_feature_packs import (
    normalize_sport_key,
    get_sport_feature_pack,
    evaluate_sport_feature_readiness,
)
from automation_scheduler.market_feature_packs import (
    normalize_market_family,
    get_market_feature_pack,
    evaluate_market_feature_readiness,
)
from automation_scheduler.feature_ablation_lab import (
    FEATURE_ABLATION_LAB_VERSION,
    ABLATION_NEVER_FEATURE_FIELDS,
    BASE_FIELD_GROUPS,
    _all_safe_fields_for_combination,
    _safe_float,
    _safe_int,
    _safe_str,
    apply_field_ablation,
)

# ---------------------------------------------------------------------------
# Version & never‑feature fields
# ---------------------------------------------------------------------------

CALIBRATION_STRATEGY_FILTER_VERSION: str = "10H16"

CALIBRATION_FILTER_NEVER_FEATURE_FIELDS: list[str] = [
    "final_result",
    "winner",
    "home_score",
    "away_score",
    "profit_loss",
    "closing_odds",
    "closing_line",
    "clv",
    "result",
    "settled_result",
    "bet_result",
    "outcome",
]

# ---------------------------------------------------------------------------
# Part 2 – Filter configuration
# ---------------------------------------------------------------------------


def build_default_calibration_filter_config(
    mode: str = "single_sport",
    sport: object = None,
    market: object = None,
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    min_required_coverage_percent: float = 80.0,
    min_active_field_coverage_percent: float = 60.0,
    min_rows_per_sport: int = 25,
    min_rows_per_market: int = 10,
) -> dict[str, Any]:
    """Return a default configuration dict for the calibration strategy filter.

    Parameters
    ----------
    mode : str
        ``"single_sport"`` or ``"all_sports"``.
    sport : str, optional
        Normalised sport key (ignored in all_sports mode).
    market : str, optional
        Normalised market family.
    selected_fields, removed_fields, selected_groups
        Arbitrary field controls, forwarded to the ablation layer.
    min_required_coverage_percent : float
        Minimum required field coverage to consider a sport/market ready
        (passed to sport‑ and market‑readiness evaluation).
    min_active_field_coverage_percent : float
        Minimum percentage of active pre‑decision fields a row must have to
        be eligible.
    min_rows_per_sport : int
        Minimum number of rows needed for a sport to be included in all_sports
        mode.
    min_rows_per_market : int
        Minimum number of rows needed for a market family to be included.
    """
    never = list(CALIBRATION_FILTER_NEVER_FEATURE_FIELDS)
    return {
        "ok": True,
        "version": CALIBRATION_STRATEGY_FILTER_VERSION,
        "mode": mode,
        "sport": sport,
        "market": market,
        "selected_fields": selected_fields or [],
        "removed_fields": removed_fields or [],
        "selected_groups": selected_groups or [],
        "min_required_coverage_percent": min_required_coverage_percent,
        "min_active_field_coverage_percent": min_active_field_coverage_percent,
        "min_rows_per_sport": min_rows_per_sport,
        "min_rows_per_market": min_rows_per_market,
        "never_feature_fields": never,
        "operator_interpretation": (
            "Calibration filter configured. "
            f"Mode: {mode}. "
            f"Min required coverage: {min_required_coverage_percent}%. "
            f"Min active field coverage: {min_active_field_coverage_percent}%. "
            f"Min rows per sport: {min_rows_per_sport}. "
            f"Min rows per market: {min_rows_per_market}."
        ),
    }


# ---------------------------------------------------------------------------
# Part 3 – Row diagnostics
# ---------------------------------------------------------------------------

_REQUIRED_BASE_FIELDS: list[str] = [
    "sport",
    "event_date",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
]


def _base_fields_present(row: Mapping[str, Any]) -> bool:
    for f in _REQUIRED_BASE_FIELDS:
        v = row.get(f)
        if v is None or v == "":
            return False
    return True


def diagnose_calibration_row(
    row: Mapping[str, Any],
    active_fields: list[str],
    sport_readiness: dict[str, Any] | None = None,
    market_readiness: dict[str, Any] | None = None,
    min_active_field_coverage_percent: float = 60.0,
) -> dict[str, Any]:
    """Return diagnostics for a single row.

    Eligibility rules:
    - Required base fields must be present.
    - Never‑feature fields are ignored as active fields.
    - Row must have at least *min_active_field_coverage_percent* of the
      active fields present (excluding never‑feature fields).
    - If *sport_readiness* is provided and the row's sport is not ready,
      the row is also excluded.
    - If *market_readiness* is provided and the row's market family is not
      ready, the row is also excluded.
    """
    exclusion_reasons: list[str] = []
    warnings: list[str] = []

    never_set = set(CALIBRATION_FILTER_NEVER_FEATURE_FIELDS)

    # 1. Required base fields
    if not _base_fields_present(row):
        exclusion_reasons.append("missing_base_fields")

    # 2. Active field coverage (excluding never fields)
    effective_active = [f for f in active_fields if f not in never_set]
    present = 0
    for f in effective_active:
        v = row.get(f)
        if v is not None and v != "":
            present += 1
    needed = max(1, round(len(effective_active) * min_active_field_coverage_percent / 100))
    coverage_pct = round(present / len(effective_active) * 100, 1) if effective_active else 100.0
    if present < needed:
        exclusion_reasons.append("insufficient_active_field_coverage")

    # 3. Sport readiness gate
    sport_key = normalize_sport_key(row.get("sport"))
    if sport_readiness is not None:
        info = sport_readiness.get(sport_key) or {}
        ready = info.get("ready", False)
        if not ready:
            exclusion_reasons.append("sport_not_ready")

    # 4. Market readiness gate
    mkt = normalize_market_family(row.get("market"), row.get("selection"), row.get("sport"))
    if market_readiness is not None:
        info = market_readiness.get(mkt) or {}
        ready = info.get("ready", False)
        if not ready:
            exclusion_reasons.append("market_not_ready")

    issues = []
    for r in exclusion_reasons:
        if r == "missing_base_fields":
            missing = [f for f in _REQUIRED_BASE_FIELDS if row.get(f) in (None, "")]
            issues.append(f"Missing required fields: {', '.join(missing)}")
        elif r == "insufficient_active_field_coverage":
            issues.append(
                f"Active field coverage {coverage_pct}% < "
                f"{min_active_field_coverage_percent}% "
                f"(present {present}/{len(effective_active)})"
            )
        elif r == "sport_not_ready":
            issues.append(f"Sport '{sport_key}' is not calibration ready")
        elif r == "market_not_ready":
            issues.append(f"Market family '{mkt}' is not calibration ready")

    eligible = len(exclusion_reasons) == 0

    return {
        "eligible": eligible,
        "sport_key": sport_key,
        "market_family": mkt,
        "active_field_count": len(effective_active),
        "present_active_field_count": present,
        "active_field_coverage_percent": coverage_pct,
        "missing_active_fields": [f for f in effective_active if row.get(f) in (None, "")],
        "exclusion_reasons": exclusion_reasons,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Part 4 – Sport and market readiness snapshot
# ---------------------------------------------------------------------------


def _sport_readiness_for_rows(
    rows: Sequence[Mapping[str, Any]],
    threshold: float = 80.0,
    min_rows: int = 25,
) -> dict[str, dict[str, Any]]:
    """Evaluate readiness per normalised sport and decide inclusion."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        sk = normalize_sport_key(r.get("sport"))
        groups[sk].append(r)

    result: dict[str, dict[str, Any]] = {}
    for sk, grp in groups.items():
        eval_result = evaluate_sport_feature_readiness(grp, sk)
        required_coverage = eval_result.get("required_coverage_percent", 0.0)
        readiness_level = eval_result.get("readiness_level", "not_ready")
        has_min_rows = len(grp) >= min_rows
        meets_coverage = required_coverage >= threshold

        ready = (
            readiness_level in ("usable", "strong")
            and has_min_rows
            and meets_coverage
        )

        # build stable exclusion reason
        if not ready:
            reasons = []
            if readiness_level not in ("usable", "strong"):
                reasons.append("sport_not_ready")
            if not has_min_rows:
                reasons.append("sport_min_rows_not_met")
            if not meets_coverage:
                reasons.append("insufficient_required_coverage")
            reason_str = "; ".join(reasons)
        else:
            reason_str = "Ready"

        result[sk] = {
            "sport_key": eval_result["sport_key"],
            "sport_family": eval_result["sport_family"],
            "display_name": eval_result["display_name"],
            "depth_level": eval_result["depth_level"],
            "total_rows": eval_result["total_rows"],
            "required_coverage_percent": eval_result["required_coverage_percent"],
            "recommended_coverage_percent": eval_result["recommended_coverage_percent"],
            "readiness_level": readiness_level,
            "missing_required_fields": eval_result["missing_required_fields"],
            "ready": ready,
            "reason": reason_str,
        }
    return result


def _market_readiness_for_rows(
    rows: Sequence[Mapping[str, Any]],
    threshold: float = 80.0,
    min_rows: int = 10,
) -> dict[str, dict[str, Any]]:
    """Evaluate readiness per normalised market family and decide inclusion."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        mkt = normalize_market_family(r.get("market"), r.get("selection"), r.get("sport"))
        groups[mkt].append(r)

    result: dict[str, dict[str, Any]] = {}
    for mkt_key, grp in groups.items():
        eval_result = evaluate_market_feature_readiness(grp, market=mkt_key, sport=None)
        required_coverage = eval_result.get("required_coverage_percent", 0.0)
        readiness_level = eval_result.get("readiness_level", "not_ready")
        has_min_rows = len(grp) >= min_rows
        meets_coverage = required_coverage >= threshold

        ready = (
            readiness_level in ("usable", "strong")
            and has_min_rows
            and meets_coverage
        )

        # build stable exclusion reason
        if not ready:
            reasons = []
            if readiness_level not in ("usable", "strong"):
                reasons.append("market_not_ready")
            if not has_min_rows:
                reasons.append("market_min_rows_not_met")
            if not meets_coverage:
                reasons.append("insufficient_required_coverage")
            reason_str = "; ".join(reasons)
        else:
            reason_str = "Ready"

        result[mkt_key] = {
            "market_family": eval_result["market_family"],
            "display_name": eval_result["display_name"],
            "depth_level": eval_result["depth_level"],
            "total_rows": eval_result["total_rows"],
            "required_coverage_percent": eval_result["required_coverage_percent"],
            "recommended_coverage_percent": eval_result["recommended_coverage_percent"],
            "readiness_level": readiness_level,
            "missing_required_fields": eval_result["missing_required_fields"],
            "ready": ready,
            "reason": reason_str,
        }
    return result


def build_calibration_readiness_snapshot(
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Return readiness snapshot for all sports and market families."""
    min_coverage = float(config.get("min_required_coverage_percent", 80.0))
    min_rows_sport = int(config.get("min_rows_per_sport", 25))
    min_rows_market = int(config.get("min_rows_per_market", 10))

    sport_rdy = _sport_readiness_for_rows(rows, threshold=min_coverage, min_rows=min_rows_sport)
    market_rdy = _market_readiness_for_rows(rows, threshold=min_coverage, min_rows=min_rows_market)

    included_sports = [k for k, v in sport_rdy.items() if v["ready"]]
    excluded_sports = [dict(v) for v in sport_rdy.values() if not v["ready"]]
    included_markets = [k for k, v in market_rdy.items() if v["ready"]]
    excluded_markets = [dict(v) for v in market_rdy.values() if not v["ready"]]

    row_counts_by_sport: dict[str, int] = {}
    for r in rows:
        sk = normalize_sport_key(r.get("sport"))
        row_counts_by_sport[sk] = row_counts_by_sport.get(sk, 0) + 1
    row_counts_by_market: dict[str, int] = {}
    for r in rows:
        mkt = normalize_market_family(r.get("market"), r.get("selection"), r.get("sport"))
        row_counts_by_market[mkt] = row_counts_by_market.get(mkt, 0) + 1

    warnings: list[str] = []
    if excluded_sports:
        warnings.append(
            f"Excluded {len(excluded_sports)} sport(s): "
            + "; ".join(f"{e['sport_key']} ({e['reason']})" for e in excluded_sports)
        )
    if excluded_markets:
        warnings.append(
            f"Excluded {len(excluded_markets)} market(s): "
            + "; ".join(f"{e['market_family']} ({e['reason']})" for e in excluded_markets)
        )

    interp = (
        f"Readiness snapshot: {len(included_sports)} included sport(s), "
        f"{len(included_markets)} included market family(s). "
        f"{len(warnings)} warning(s)."
    )

    return {
        "ok": True,
        "version": CALIBRATION_STRATEGY_FILTER_VERSION,
        "total_rows": len(rows),
        "included_sports": included_sports,
        "excluded_sports": excluded_sports,
        "included_market_families": included_markets,
        "excluded_market_families": excluded_markets,
        "sport_readiness": sport_rdy,
        "market_readiness": market_rdy,
        "row_counts_by_sport": row_counts_by_sport,
        "row_counts_by_market_family": row_counts_by_market,
        "warnings": warnings,
        "operator_interpretation": interp,
    }


# ---------------------------------------------------------------------------
# Part 5 – Apply strategy filter
# ---------------------------------------------------------------------------


def _rows_for_sport(
    rows: Sequence[Mapping[str, Any]],
    sport_key: str,
) -> list[dict[str, Any]]:
    norm = normalize_sport_key(sport_key)
    return [dict(r) for r in rows if normalize_sport_key(r.get("sport")) == norm]


def _rows_for_market(
    rows: Sequence[Mapping[str, Any]],
    market_family: str,
) -> list[dict[str, Any]]:
    norm = normalize_market_family(market_family)
    return [dict(r) for r in rows if normalize_market_family(r.get("market"), r.get("selection"), r.get("sport")) == norm]


def apply_calibration_strategy_filter(
    rows: Sequence[Mapping[str, Any]],
    mode: str = "single_sport",
    sport: object = None,
    market: object = None,
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    min_required_coverage_percent: float = 80.0,
    min_active_field_coverage_percent: float = 60.0,
    min_rows_per_sport: int = 25,
    min_rows_per_market: int = 10,
) -> dict[str, Any]:
    """Apply the calibration strategy filter to *rows*.

    Steps:
    1. Determine active pre‑decision fields (using Feature Ablation Lab's
       field‑selection logic).
    2. If *mode* is ``"single_sport"``, restrict to *sport* (if given).
    3. Build readiness snapshot for remaining rows.
    4. Diagnose every remaining row against readiness gates and active field
       coverage.
    5. Separate included / excluded rows.
    6. Return results.
    """
    # 1. Active fields
    sport_key = normalize_sport_key(sport) if sport else "general"
    market_family = normalize_market_family(market, sport=sport_key) if market else "general_market"

    # Use ablation lab to get all selectable fields.
    all_selectable = _all_safe_fields_for_combination(sport_key, market_family)

    never_set = set(CALIBRATION_FILTER_NEVER_FEATURE_FIELDS)
    # apply group / field selection
    group_fields: set[str] = set()
    if selected_groups:
        for grp in BASE_FIELD_GROUPS:
            if grp["group_key"] in selected_groups:
                group_fields.update(grp["fields"])
    all_valid = set(all_selectable) - never_set
    active_set = all_valid.copy()
    if selected_groups:
        active_set = all_valid & group_fields
    if selected_fields:
        allowed = set(selected_fields)
        active_set = allowed & all_valid
    rem = set(removed_fields or [])
    active_set -= rem
    active_fields = sorted(active_set)

    # 2. Row restriction for single_sport mode
    if mode == "single_sport" and sport_key != "general":
        working_rows = _rows_for_sport(rows, sport_key)
    else:
        working_rows = [dict(r) for r in rows]

    if market_family != "general_market":
        working_rows = _rows_for_market(working_rows, market_family)

    # 3. Readiness snapshot
    config = build_default_calibration_filter_config(
        mode=mode,
        sport=sport_key,
        market=market_family,
        selected_fields=selected_fields,
        removed_fields=removed_fields,
        selected_groups=selected_groups,
        min_required_coverage_percent=min_required_coverage_percent,
        min_active_field_coverage_percent=min_active_field_coverage_percent,
        min_rows_per_sport=min_rows_per_sport,
        min_rows_per_market=min_rows_per_market,
    )
    readiness = build_calibration_readiness_snapshot(working_rows, config)

    # 4. Diagnose each row
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    exclude_reason_counter: Counter[str] = Counter()

    for r in working_rows:
        diag = diagnose_calibration_row(
            r,
            active_fields,
            sport_readiness=readiness.get("sport_readiness"),
            market_readiness=readiness.get("market_readiness"),
            min_active_field_coverage_percent=min_active_field_coverage_percent,
        )
        if diag["eligible"]:
            included.append(r)
        else:
            excluded.append({"row": r, "diagnosis": diag})
            for reason in diag["exclusion_reasons"]:
                exclude_reason_counter[reason] += 1

    warnings: list[str] = list(readiness.get("warnings", []))
    # check if no included rows
    if not included:
        warnings.append("No rows passed the calibration filter.")

    return {
        "ok": True,
        "version": CALIBRATION_STRATEGY_FILTER_VERSION,
        "mode": mode,
        "sport_key": sport_key,
        "market_family": market_family,
        "config": config,
        "active_fields": active_fields,
        "removed_fields": list(rem),
        "readiness_snapshot": readiness,
        "included_rows": included,
        "excluded_rows": excluded,
        "included_row_count": len(included),
        "excluded_row_count": len(excluded),
        "exclusion_reason_counts": dict(exclude_reason_counter),
        "warnings": warnings,
        "operator_interpretation": (
            f"Calibration filter applied. "
            f"{len(included)} included rows, {len(excluded)} excluded rows."
        ),
    }


# ---------------------------------------------------------------------------
# Part 6 – Performance summary
# ---------------------------------------------------------------------------


def summarize_calibration_strategy_performance(
    filtered_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Summarise performance using **only** ``included_rows``.

    Leakage / result fields are used *only* for post‑decision grading.
    Excluded rows are never counted.
    """
    included = list(filtered_result.get("included_rows") or [])

    if not included:
        return {
            "ok": True,
            "version": CALIBRATION_STRATEGY_FILTER_VERSION,
            "total_rows": filtered_result.get("included_row_count", 0),
            "included_row_count": 0,
            "excluded_row_count": filtered_result.get("excluded_row_count", 0),
            "decisions": 0,
            "skipped_decisions": 0,
            "settled_count": 0,
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "net_result": 0.0,
            "roi_percent": 0.0,
            "win_rate_percent": 0.0,
            "roi_by_sport": {},
            "roi_by_market_family": {},
            "exclusion_reason_counts": filtered_result.get("exclusion_reason_counts", {}),
            "warnings": ["No rows passed the calibration filter."],
            "operator_interpretation": "No data available.",
        }

    decisions = 0
    skipped_decisions = 0
    settled = 0
    wins = 0
    losses = 0
    pushes = 0
    net = 0.0
    rois: list[float] = []

    sport_nets: dict[str, list[float]] = defaultdict(list)
    mkt_nets: dict[str, list[float]] = defaultdict(list)

    for r in included:
        # skip if the row was marked as no-bet
        if r.get("no_bet") or r.get("reason") is not None:
            skipped_decisions += 1
            continue
        decisions += 1

        net_val = _safe_float(r.get("profit_loss") or r.get("pnl"))
        net += net_val
        roi_val = _safe_float(r.get("roi_percent"))
        rois.append(roi_val)

        sk = normalize_sport_key(r.get("sport"))
        sport_nets[sk].append(net_val)

        mkt = normalize_market_family(r.get("market"), r.get("selection"), r.get("sport"))
        mkt_nets[mkt].append(net_val)

        final = _safe_str(r.get("final_result") or r.get("result") or r.get("outcome")).upper()
        if final in ("W", "WIN", "H", "HOME", "YES", "Y"):
            wins += 1
            settled += 1
        elif final in ("L", "LOSS", "A", "AWAY", "NO", "N"):
            losses += 1
            settled += 1
        elif final in ("P", "PUSH", "D", "DRAW", "T", "TIE"):
            pushes += 1
            settled += 1

    roi_avg = sum(rois) / len(rois) if rois else 0.0
    win_rate = (wins / settled * 100) if settled > 0 else 0.0

    roi_by_sport: dict[str, dict] = {}
    for sk, vals in sport_nets.items():
        total = sum(vals)
        cnt = len(vals)
        roi_by_sport[sk] = {
            "rows": cnt,
            "net_result": round(total, 2),
            "roi_percent": round(total / cnt * 100, 2) if cnt else 0.0,
        }
    roi_by_market: dict[str, dict] = {}
    for mkt, vals in mkt_nets.items():
        total = sum(vals)
        cnt = len(vals)
        roi_by_market[mkt] = {
            "rows": cnt,
            "net_result": round(total, 2),
            "roi_percent": round(total / cnt * 100, 2) if cnt else 0.0,
        }

    warnings: list[str] = []
    if settled == 0:
        warnings.append(
            "Calibration filter coverage is available, but settled performance "
            "is limited until row-level outcomes are available."
        )

    return {
        "ok": True,
        "version": CALIBRATION_STRATEGY_FILTER_VERSION,
        "total_rows": len(included),
        "included_row_count": len(included),
        "excluded_row_count": filtered_result.get("excluded_row_count", 0),
        "decisions": decisions,
        "skipped_decisions": skipped_decisions,
        "settled_count": settled,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "net_result": round(net, 2),
        "roi_percent": round(roi_avg, 2),
        "win_rate_percent": round(win_rate, 2),
        "roi_by_sport": roi_by_sport,
        "roi_by_market_family": roi_by_market,
        "exclusion_reason_counts": filtered_result.get("exclusion_reason_counts", {}),
        "warnings": warnings,
        "operator_interpretation": (
            f"{settled} settled outcomes of {decisions} decisions. "
            f"ROI: {roi_avg:.2f}%, win rate {win_rate:.2f}%."
        ),
    }


# ---------------------------------------------------------------------------
# Part 7 – Main runner
# ---------------------------------------------------------------------------


def run_calibration_strategy_filter(
    rows: Sequence[Mapping[str, Any]],
    mode: str = "single_sport",
    sport: object = None,
    market: object = None,
    selected_fields: list[str] | None = None,
    removed_fields: list[str] | None = None,
    selected_groups: list[str] | None = None,
    min_required_coverage_percent: float = 80.0,
    min_active_field_coverage_percent: float = 60.0,
    min_rows_per_sport: int = 25,
    min_rows_per_market: int = 10,
) -> dict[str, Any]:
    """Run the full calibration strategy filter and return combined result."""
    filtered = apply_calibration_strategy_filter(
        rows=rows,
        mode=mode,
        sport=sport,
        market=market,
        selected_fields=selected_fields,
        removed_fields=removed_fields,
        selected_groups=selected_groups,
        min_required_coverage_percent=min_required_coverage_percent,
        min_active_field_coverage_percent=min_active_field_coverage_percent,
        min_rows_per_sport=min_rows_per_sport,
        min_rows_per_market=min_rows_per_market,
    )
    performance = summarize_calibration_strategy_performance(filtered)

    readiness = filtered.get("readiness_snapshot", {})

    return {
        "ok": True,
        "version": CALIBRATION_STRATEGY_FILTER_VERSION,
        "mode": mode,
        "sport_key": filtered.get("sport_key", "general"),
        "market_family": filtered.get("market_family", "general_market"),
        "active_fields": filtered.get("active_fields", []),
        "removed_fields": filtered.get("removed_fields", []),
        "included_sports": readiness.get("included_sports", []),
        "excluded_sports": readiness.get("excluded_sports", []),
        "included_market_families": readiness.get("included_market_families", []),
        "excluded_market_families": readiness.get("excluded_market_families", []),
        "readiness_snapshot": readiness,
        "performance": performance,
        "exclusion_reason_counts": filtered.get("exclusion_reason_counts", {}),
        "warnings": filtered.get("warnings", []) + performance.get("warnings", []),
        "operator_interpretation": (
            "Calibration-ready strategy filter completed. "
            f"Included {filtered['included_row_count']} rows, "
            f"excluded {filtered['excluded_row_count']} rows."
        ),
    }
