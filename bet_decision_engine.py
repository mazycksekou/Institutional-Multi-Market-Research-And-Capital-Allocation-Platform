"""Bet decision rules and line evaluation orchestration for Action endpoints."""
from __future__ import annotations

from typing import Any, Optional

import market_pricing
import model_blender
from quant_engine import (
    american_to_decimal,
    confidence_adjusted_stake,
    edge_percentage,
    expected_value_per_100,
    implied_probability_from_american,
    kelly_fraction,
    no_vig_probabilities_two_way,
    probability_to_fair_american,
    suggested_stake,
)

EDGE_STRONG_BET = 2.5
EDGE_BET = 1.0
EDGE_LEAN = 0.35


def _normalize_selection(sel: str) -> str:
    return (sel or "").strip().lower()


def _normalize_market(m: str) -> str:
    return (m or "").strip().lower()


def find_two_way_counterpart(lines: list[dict[str, Any]], idx: int) -> Optional[int]:
    base = lines[idx]
    mk = _normalize_market(str(base.get("market", "")))
    sel = _normalize_selection(str(base.get("selection", "")))
    ln = base.get("line")
    for j, other in enumerate(lines):
        if j == idx:
            continue
        if _normalize_market(str(other.get("market", ""))) != mk:
            continue
        if other.get("line") != ln:
            continue
        osel = _normalize_selection(str(other.get("selection", "")))
        if mk in ("totals", "total", "game_total", "team_total"):
            if ("over" in sel and "under" in osel) or ("under" in sel and "over" in osel):
                return j
        if mk in ("h2h", "moneyline", "ml", "money_line"):
            if sel and osel and sel != osel:
                return j
    return None


def no_vig_probability_for_line(lines: list[dict[str, Any]], idx: int) -> Optional[float]:
    j = find_two_way_counterpart(lines, idx)
    if j is None:
        return None
    a = lines[idx]
    b = lines[j]
    try:
        ia = implied_probability_from_american(int(a["odds_american"]))
        ib = implied_probability_from_american(int(b["odds_american"]))
        nv_a, _nv_b = no_vig_probabilities_two_way(ia, ib)
        return float(nv_a)
    except Exception:
        return None


def risk_grade_from_kelly(full_kelly_pct: float) -> str:
    if full_kelly_pct >= 8:
        return "high"
    if full_kelly_pct >= 3:
        return "medium"
    return "low"


def kelly_fraction_multiplier(risk_profile: str) -> float:
    rp = (risk_profile or "standard").strip().lower()
    if rp == "conservative":
        return 0.25
    if rp == "aggressive":
        return 1.0
    return 0.5


def decision_label(
    model_missing: bool,
    edge_pct: float,
    ev_per_100: float,
    full_kelly_pct: float,
) -> str:
    if model_missing:
        return "no_bet_model_missing"
    if edge_pct < EDGE_LEAN or ev_per_100 <= 0:
        return "no_bet"
    if edge_pct >= EDGE_STRONG_BET and full_kelly_pct >= 3:
        return "strong_bet"
    if edge_pct >= EDGE_BET and ev_per_100 > 0:
        return "bet"
    if edge_pct >= EDGE_LEAN:
        return "lean"
    return "no_bet"


def reason_text(decision: str, model_missing: bool) -> str:
    if model_missing:
        return "Model probability missing; no-vig used only as baseline — no recommendation."
    if decision == "no_bet":
        return "Edge or EV below betting threshold."
    if decision == "lean":
        return "Small positive EV; reduced sizing."
    if decision == "strong_bet":
        return "Strong positive EV versus implied after sizing discipline."
    if decision == "bet":
        return "Positive EV after implied probability and model probability comparison."
    return "Evaluated."


def evaluate_lines_payload(body: dict[str, Any]) -> dict[str, Any]:
    """Evaluate all lines. Returns dict suitable for HTTP 200 JSON."""
    sport = str(body.get("sport") or "")
    event = str(body.get("event") or "")
    bankroll = float(body.get("bankroll") or 0)
    unit_size = float(body.get("unit_size") or 0)
    risk_profile = str(body.get("risk_profile") or "standard")
    max_stake_pct = float(body.get("max_stake_pct") or 0.02)
    lines_in = body.get("lines") or []

    if not isinstance(lines_in, list) or not lines_in:
        return {"ok": False, "error": "INVALID_INPUT", "detail": "lines must be a non-empty list.", "results": []}

    if bankroll <= 0:
        return {"ok": False, "error": "INVALID_BANKROLL", "detail": "bankroll must be positive.", "results": []}

    if unit_size <= 0:
        return {"ok": False, "error": "INVALID_UNIT", "detail": "unit_size must be positive.", "results": []}

    normalized_lines: list[dict[str, Any]] = []
    for row in lines_in:
        if not isinstance(row, dict):
            continue
        normalized_lines.append(
            {
                "sportsbook": str(row.get("sportsbook", "")),
                "market": str(row.get("market", "")),
                "selection": str(row.get("selection", "")),
                "line": row.get("line"),
                "odds_american": row.get("odds_american"),
                "model_probability": row.get("model_probability"),
                "correlation_group": row.get("correlation_group"),
                "opening_odds_american": row.get("opening_odds_american"),
            }
        )

    if not normalized_lines:
        return {"ok": False, "error": "INVALID_LINES", "detail": "No valid line objects.", "results": []}

    group_odds: dict[tuple[Any, Any, Any], list[int]] = {}
    for row in normalized_lines:
        key = (_normalize_market(row["market"]), _normalize_selection(row["selection"]), row.get("line"))
        try:
            o = int(row["odds_american"])
        except Exception:
            continue
        group_odds.setdefault(key, []).append(o)

    results: list[dict[str, Any]] = []
    kmult = kelly_fraction_multiplier(risk_profile)

    for i, row in enumerate(normalized_lines):
        flags: list[str] = []
        try:
            odds_am = int(row["odds_american"])
        except Exception:
            results.append(
                {
                    "sportsbook": row.get("sportsbook"),
                    "market": row.get("market"),
                    "selection": row.get("selection"),
                    "line": row.get("line"),
                    "odds_american": row.get("odds_american"),
                    "error": "INVALID_ODDS",
                    "detail": "odds_american must be an integer.",
                }
            )
            continue

        try:
            dec = round(american_to_decimal(odds_am), 4)
            implied = implied_probability_from_american(odds_am)
            nv = no_vig_probability_for_line(normalized_lines, i)

            model_p: Optional[float]
            try:
                model_p = float(row["model_probability"]) if row.get("model_probability") is not None else None
            except Exception:
                model_p = None

            if model_p is not None and (model_p <= 0 or model_p >= 1):
                results.append(
                    {
                        "sportsbook": row["sportsbook"],
                        "market": row["market"],
                        "selection": row["selection"],
                        "line": row.get("line"),
                        "odds_american": odds_am,
                        "error": "INVALID_MODEL_PROBABILITY",
                        "detail": "model_probability must be in (0,1).",
                    }
                )
                continue

            model_missing = model_p is None
            market_baseline = nv if nv is not None else implied

            if model_missing:
                blended_true = float(market_baseline)
                true_p = blended_true
                flags.append("model_missing")
            else:
                blended_true, _ = model_blender.blend_probabilities(
                    model_p,
                    nv if nv is not None else implied,
                    model_weight=0.65,
                )
                true_p = float(blended_true)

            fair_am = int(probability_to_fair_american(true_p))
            edge_pct = edge_percentage(true_p, implied)
            ev100 = round(expected_value_per_100(odds_am, true_p), 4)
            fk = kelly_fraction(odds_am, true_p)
            full_kelly_pct = round(fk * 100, 2)
            fractional_kelly_pct = round(fk * kmult * 100, 2)

            key = (_normalize_market(row["market"]), _normalize_selection(row["selection"]), row.get("line"))
            nbooks = len(group_odds.get(key, [odds_am]))
            conf = model_blender.confidence_score(edge_pct, nbooks)

            base_stake = suggested_stake(
                bankroll,
                odds_am,
                true_p,
                fractional_kelly=kmult,
                max_bankroll_pct=max_stake_pct,
            )
            stake_adj = confidence_adjusted_stake(base_stake, float(conf))
            stake_final = min(max(0.0, stake_adj), bankroll * max_stake_pct)
            suggested_units = round(stake_final / unit_size, 2) if unit_size > 0 else 0.0

            same_key_odds = group_odds.get(key, [odds_am])
            mkt_spread = market_pricing.market_spread_implied(same_key_odds)
            if mkt_spread > 0.02:
                flags.append("wide_book_spread")

            decision = decision_label(model_missing, edge_pct, ev100, full_kelly_pct)
            if model_missing:
                decision = "no_bet_model_missing"
                suggested_units = 0.0
                stake_final = 0.0
            elif decision == "no_bet":
                suggested_units = 0.0
                stake_final = 0.0

            rg = risk_grade_from_kelly(full_kelly_pct)

            results.append(
                {
                    "sportsbook": row["sportsbook"],
                    "market": row["market"],
                    "selection": row["selection"],
                    "line": row.get("line"),
                    "odds_american": odds_am,
                    "odds_decimal": dec,
                    "implied_probability": round(implied, 6),
                    "no_vig_probability": round(nv, 6) if nv is not None else None,
                    "model_probability": round(model_p, 6) if model_p is not None else None,
                    "blended_true_probability": round(blended_true, 6),
                    "fair_odds_american": fair_am,
                    "edge_percent": round(edge_pct, 2),
                    "ev_per_100": ev100,
                    "full_kelly_percent": full_kelly_pct,
                    "fractional_kelly_percent": fractional_kelly_pct,
                    "suggested_units": suggested_units,
                    "suggested_stake": round(stake_final, 2),
                    "confidence": conf,
                    "risk_grade": rg,
                    "decision": decision,
                    "reason": reason_text(decision, model_missing),
                    "no_bet_flags": flags,
                    "correlation_group": row.get("correlation_group"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "sportsbook": row.get("sportsbook"),
                    "market": row.get("market"),
                    "selection": row.get("selection"),
                    "line": row.get("line"),
                    "odds_american": odds_am,
                    "error": "LINE_EVAL_ERROR",
                    "detail": str(exc),
                }
            )

    return {
        "ok": True,
        "sport": sport,
        "event": event,
        "risk_profile": risk_profile,
        "results": results,
    }
