from __future__ import annotations

from typing import Any

from src.market_intelligence.basketball_player_impact_common import clamp, compact_list, finalize_safe_response, normalize_basketball_sport, safe_float, sport_contract


MARKET_REQUIRED_SAMPLES = {
    "prop": 120,
    "points_prop": 120,
    "assists_prop": 120,
    "rebounds_prop": 120,
    "threes_prop": 120,
    "blocks_steals_prop": 120,
    "pra_prop": 150,
    "spread": 100,
    "total": 100,
    "team_total": 100,
    "sgp_correlation": 180,
}


def _market_family(record: dict[str, Any]) -> str:
    market = str(record.get("market_type") or record.get("market") or "").strip().lower()
    prop_type = str(record.get("prop_type") or "").strip().lower()
    if prop_type:
        return f"{prop_type}_prop" if not prop_type.endswith("_prop") else prop_type
    if "assist" in market:
        return "assists_prop"
    if "rebound" in market:
        return "rebounds_prop"
    if "three" in market or "3" in market:
        return "threes_prop"
    if "block" in market or "steal" in market:
        return "blocks_steals_prop"
    if "pra" in market:
        return "pra_prop"
    if "point" in market and "spread" not in market:
        return "points_prop"
    if "team_total" in market:
        return "team_total"
    if "total" in market:
        return "total"
    if "spread" in market:
        return "spread"
    if "sgp" in market or "correlation" in market:
        return "sgp_correlation"
    return "prop" if "prop" in market else (market or "unknown")


def _record_matches(candidate: dict[str, Any], record: dict[str, Any], sport: str, target_market: str | None) -> bool:
    if normalize_basketball_sport(record.get("sport") or record.get("league")) != sport:
        return False
    for key in ("player_id", "team_id", "opponent_id"):
        if candidate.get(key) not in (None, "", []) and record.get(key) not in (None, "", []) and str(candidate.get(key)) != str(record.get(key)):
            return False
    if target_market and _market_family(record) != target_market:
        return False
    return True


def _summarize(records: list[dict[str, Any]], required_sample_size: int) -> dict[str, Any]:
    sample = len(records)
    hits = 0
    misses = 0
    edges: list[float] = []
    clv: list[float] = []
    errors: list[float] = []
    false_positive = 0
    false_negative = 0
    profits: list[float] = []
    for record in records:
        outcome = str(record.get("outcome") or record.get("result") or "").strip().lower()
        hit = record.get("hit")
        if hit is None:
            hit = outcome in {"hit", "win", "won", "success", "covered", "over_hit", "under_hit"}
        if bool(hit):
            hits += 1
        elif outcome or record.get("hit") is not None:
            misses += 1
        edge = safe_float(record.get("edge") or record.get("edge_estimate"))
        if edge is not None:
            edges.append(edge)
        value = safe_float(record.get("closing_line_value") or record.get("clv"))
        if value is not None:
            clv.append(value)
        error = safe_float(record.get("calibration_error"))
        if error is not None:
            errors.append(abs(error))
        if bool(record.get("false_positive")):
            false_positive += 1
        if bool(record.get("false_negative")):
            false_negative += 1
        profit = safe_float(record.get("profit") or record.get("return"))
        if profit is not None:
            profits.append(profit)
    decided = hits + misses
    hit_rate = hits / decided if decided else 0.0
    miss_rate = misses / decided if decided else 0.0
    avg_edge = sum(edges) / len(edges) if edges else 0.0
    avg_clv = sum(clv) / len(clv) if clv else 0.0
    avg_error = sum(errors) / len(errors) if errors else (abs(hit_rate - 0.5) if decided else 0.0)
    gross_wins = sum(value for value in profits if value > 0)
    gross_losses = abs(sum(value for value in profits if value < 0))
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else (None if not profits else gross_wins)
    insufficient = sample < required_sample_size or decided < max(30, int(required_sample_size * 0.5))
    return {
        "current_sample_size": sample,
        "required_sample_size": required_sample_size,
        "outcome_coverage": round(clamp(sample / max(required_sample_size, 1) * 100.0) / 100.0, 4),
        "hit_rate": round(hit_rate, 4),
        "miss_rate": round(miss_rate, 4),
        "average_edge": round(avg_edge, 4),
        "average_closing_line_value": round(avg_clv, 4),
        "calibration_error": round(avg_error, 4),
        "false_positive_rate": round(false_positive / sample, 4) if sample else 0.0,
        "false_negative_rate": round(false_negative / sample, 4) if sample else 0.0,
        "profit_factor_if_available": round(profit_factor, 4) if profit_factor is not None else None,
        "insufficient_sample": bool(insufficient),
        "calibration_status": "insufficient_sample" if insufficient else ("calibrated_watch" if avg_error <= 0.12 else "calibration_warning"),
    }


def evaluate_basketball_player_impact_calibration(
    candidate: dict[str, Any] | None = None,
    outcome_records: list[dict[str, Any]] | None = None,
    *,
    market_type: str | None = None,
) -> dict[str, Any]:
    source = candidate if isinstance(candidate, dict) else {}
    sport = normalize_basketball_sport(source.get("sport") or source.get("league"))
    target_market = _market_family({"market_type": market_type}) if market_type else None
    rows = [record for record in (outcome_records or []) if isinstance(record, dict)]
    matching = [record for record in rows if _record_matches(source, record, sport, target_market)]
    required = MARKET_REQUIRED_SAMPLES.get(target_market or "prop", 120)
    summary = _summarize(matching, required)

    by_market: dict[str, dict[str, Any]] = {}
    for market, required_size in MARKET_REQUIRED_SAMPLES.items():
        market_rows = [record for record in rows if _record_matches(source, record, sport, market)]
        if market_rows:
            by_market[market] = _summarize(market_rows, required_size)
    if not by_market:
        by_market = {
            "props": _summarize([], MARKET_REQUIRED_SAMPLES["prop"]),
            "spreads": _summarize([], MARKET_REQUIRED_SAMPLES["spread"]),
            "totals": _summarize([], MARKET_REQUIRED_SAMPLES["total"]),
            "team_totals": _summarize([], MARKET_REQUIRED_SAMPLES["team_total"]),
            "sgp_correlation": _summarize([], MARKET_REQUIRED_SAMPLES["sgp_correlation"]),
        }

    contract = sport_contract(sport)
    payload = {
        **summary,
        "sport": sport,
        "league": contract["league"],
        "calibration_bucket": f"{contract['calibration_bucket_prefix']}.{target_market or 'all_markets'}",
        "market_specific_calibration": by_market,
        "calibration_missing_inputs": [] if rows else ["settled_outcomes", "closing_line_value", "market_specific_results"],
        "next_required_data": compact_list(["settled_outcomes", "closing_line_value", "line_movement", "prop_type", "minutes_outcome"], limit=10),
    }
    return finalize_safe_response(payload, source_payload={"candidate": source, "outcome_records": rows[:5]})
