from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from model_governance.cross_book_gate import evaluate_cross_book_gate
from model_governance.data_lineage import create_lineage_record
from model_governance.data_quality_monitor import evaluate_data_quality
from model_governance.settlement_liquidity_gate import evaluate_settlement_liquidity_gate

from .arbitrage_detector import detect_arbitrage
from .cross_book_line_comparator import group_cross_book_markets
from .ev_line_shopper import shop_ev_lines
from .middle_opportunity_detector import detect_middle_opportunity
from .opportunity_scoring import calculate_opportunity_score, classify_opportunity
from .provider_adapter_base import ProviderAdapterBase
from .provider_health import summarize_provider_health, write_provider_health_snapshot
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .snapshot_store import save_snapshot
from .snapshot_store import SnapshotStore
from .report_writer import write_report
from .review_queue import build_review_item, list_active_review_items, upsert_review_item
from .system_health import write_system_health
from .run_context import create_run_context
from .kalshi_market_provider import get_kalshi_snapshot, summarize_kalshi_snapshot
from .kalshi_readonly_adapter import KalshiReadonlyAdapter
from .sharp_sportsbook_adapter import SharpSportsbookAdapter
from .sportsbook_odds_provider import get_valid_normalized_records, summarize_sportsbook_snapshot

KALSHI_STALE_MARKET_SECONDS = 60 * 15
KALSHI_LOW_LIQUIDITY_THRESHOLD = 0.35


def _parse_iso_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _is_kalshi_market_closed(record: dict[str, Any], now: datetime) -> bool:
    status = str(record.get("status") or "").strip().lower()
    if status in {"closed", "settled", "resolved", "final"}:
        return True
    close_time = _parse_iso_utc(record.get("close_time"))
    return bool(close_time and close_time <= now)


def _is_kalshi_market_stale(record: dict[str, Any], now: datetime) -> bool:
    timestamp = _parse_iso_utc(record.get("timestamp"))
    if timestamp is None:
        return True
    age_seconds = max(0, int((now - timestamp).total_seconds()))
    return age_seconds >= KALSHI_STALE_MARKET_SECONDS


def _kalshi_liquidity_metrics(record: dict[str, Any]) -> tuple[float, bool]:
    liquidity_score = record.get("liquidity_score")
    if isinstance(liquidity_score, (int, float)):
        score = float(liquidity_score)
    else:
        yes_bid = record.get("yes_bid")
        yes_ask = record.get("yes_ask")
        score = 0.0
        if isinstance(yes_bid, (int, float)) and isinstance(yes_ask, (int, float)):
            spread = max(0.0, float(yes_ask) - float(yes_bid))
            score = max(0.0, min(1.0, 1.0 - spread))
    volume = float(record.get("volume") or 0.0)
    open_interest = float(record.get("open_interest") or 0.0)
    low_liquidity = bool(score < KALSHI_LOW_LIQUIDITY_THRESHOLD or volume < 100.0 or open_interest < 100.0)
    return score, low_liquidity


def _collect_provider_placeholders(config: dict[str, Any]) -> dict[str, Any]:
    snapshots = []
    skipped: list[dict[str, str]] = []
    sharp_snapshot: dict[str, Any] | None = None
    kalshi_snapshot: dict[str, Any] | None = None
    for provider_id, contract in config.get("providers", {}).items():
        if provider_id == "sharp_sportsbook":
            sharp = SharpSportsbookAdapter(contract)
            config_check = sharp.validate_config()
            can_read_live = bool(
                contract.get("enabled", False)
                and contract.get("live_calls_enabled", False)
                and config_check.get("credential_status") == "ok"
                and config.get("auto_execution_enabled", False) is False
            )
            if can_read_live:
                sharp_snapshot = sharp.fetch_snapshot()
                snapshots.append(summarize_sportsbook_snapshot(sharp_snapshot))
            else:
                sharp_reason = "dry_run_placeholder"
                if "provider_disabled" in config_check["blockers"]:
                    sharp_reason = "provider_disabled"
                elif "live_reads_disabled" in config_check["blockers"]:
                    sharp_reason = "live_reads_disabled"
                elif "blocked_missing_credentials" in config_check["blockers"]:
                    sharp_reason = "missing_credentials"
                skipped.append({"provider_id": provider_id, "reason": sharp_reason})
                sharp_snapshot = sharp.fetch_snapshot()
                snapshots.append(summarize_sportsbook_snapshot(sharp_snapshot))
            continue

        if provider_id == "kalshi_prediction_market":
            kalshi = KalshiReadonlyAdapter(contract)
            config_check = kalshi.validate_config()
            can_read_live = bool(
                contract.get("enabled", False)
                and contract.get("live_calls_enabled", False)
                and config_check.get("credential_status") == "ok"
                and config.get("dry_run", True) is True
                and config.get("auto_execution_enabled", False) is False
                and contract.get("auto_execution_enabled", False) is False
                and contract.get("kalshi_order_execution_enabled", False) is False
            )
            if can_read_live:
                kalshi_snapshot = get_kalshi_snapshot(kalshi)
                snapshots.append(summarize_kalshi_snapshot(kalshi_snapshot))
            else:
                kalshi_reason = "dry_run_placeholder"
                if "provider_disabled" in config_check["blockers"]:
                    kalshi_reason = "provider_disabled"
                elif "live_reads_disabled" in config_check["blockers"]:
                    kalshi_reason = "live_reads_disabled"
                elif "blocked_missing_credentials" in config_check["blockers"]:
                    kalshi_reason = "missing_credentials"
                skipped.append({"provider_id": provider_id, "reason": kalshi_reason})
                kalshi_snapshot = get_kalshi_snapshot(kalshi)
                snapshots.append(summarize_kalshi_snapshot(kalshi_snapshot))
            continue

        adapter = ProviderAdapterBase(contract)
        config_check = adapter.validate_config()
        skipped_reason = "dry_run_placeholder"
        if "disabled_provider" in config_check["blockers"]:
            skipped_reason = "provider_disabled"
        elif "live_calls_disabled" in config_check["blockers"]:
            skipped_reason = "live_reads_disabled"
        elif "missing_credentials" in config_check["blockers"]:
            skipped_reason = "missing_credentials"
        skipped.append({"provider_id": provider_id, "reason": skipped_reason})
        snapshots.append(adapter.fetch_snapshot())
    write_provider_health_snapshot(config.get("providers", {}))
    return {
        "snapshots": snapshots,
        "skipped": skipped,
        "health": summarize_provider_health(config.get("providers", {})),
        "sharp_snapshot": sharp_snapshot,
        "kalshi_snapshot": kalshi_snapshot,
    }


def _as_score_0_to_10(value: float, scale: float = 10.0) -> float:
    return max(0.0, min(10.0, round(value / scale, 4)))


def _build_scored_candidate(base: dict[str, Any], *, opportunity_score: float | None = None) -> dict[str, Any]:
    provider_data_quality_score = float(base.get("provider_data_quality_score", 100.0))
    book_disagreement_score = float(base.get("book_disagreement_score", 0.0))
    market_identity_score = float(base.get("market_identity_score", 0.0))
    stale_data_risk_score = float(base.get("stale_data_risk_score", 0.0))
    liquidity_placeholder_score = float(base.get("liquidity_placeholder_score", 70.0))
    cross_book_score = float(base.get("cross_book_score", 0.0))
    field_scores = {
        "provider_data_quality_score": _as_score_0_to_10(provider_data_quality_score),
        "book_disagreement_score": _as_score_0_to_10(book_disagreement_score),
        "market_identity_score": _as_score_0_to_10(market_identity_score),
        "stale_data_risk_score": _as_score_0_to_10(stale_data_risk_score),
        "liquidity_placeholder_score": _as_score_0_to_10(liquidity_placeholder_score),
        "cross_book_score": _as_score_0_to_10(cross_book_score),
    }
    score = float(opportunity_score) if opportunity_score is not None else calculate_opportunity_score(field_scores)
    action = classify_opportunity(score, {"ignore_below": 55, "watch_threshold": 55, "review_threshold": 70, "urgent_threshold": 85})
    return {
        **base,
        "field_scores": field_scores,
        "opportunity_score": round(score, 2),
        "recommended_action": action,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
    }


def _evaluate_sharp_review_candidates(config: dict[str, Any], sharp_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    if not sharp_snapshot:
        return {"records_received": 0, "records_valid": 0, "records_rejected": 0, "candidates": [], "blockers": ["sharp_snapshot_missing"]}
    valid_records = get_valid_normalized_records(sharp_snapshot)
    records_received = int(sharp_snapshot.get("records_received", len(sharp_snapshot.get("records", []))))
    records_valid = int(sharp_snapshot.get("records_valid", len(valid_records)))
    records_rejected = int(sharp_snapshot.get("records_rejected", max(0, records_received - records_valid)))
    groups = group_cross_book_markets(valid_records)
    candidates: list[dict[str, Any]] = []
    for group in groups:
        offers = list(group.get("offers", []))
        if not offers:
            continue
        comparison = group.get("comparison", {})
        best = comparison.get("best_offer") or offers[0]
        books_compared = int(group.get("books_compared", comparison.get("books_compared", 0)))
        base = {
            "source": "sharp_scheduler_cross_book_v1",
            "provider_id": "sharp_sportsbook",
            "provider": "sharp_sportsbook",
            "event_id": group.get("event_id"),
            "event_name": best.get("event_name"),
            "sport": best.get("sport"),
            "league": best.get("league"),
            "market_type": "sports_pregame_main",
            "sport_or_symbol": best.get("league") or best.get("sport") or "sports",
            "market": group.get("market"),
            "selection": group.get("selection"),
            "book": best.get("bookmaker"),
            "best_book": comparison.get("best_book"),
            "best_odds": comparison.get("best_odds"),
            "best_line": comparison.get("best_line"),
            "implied_probability": best.get("implied_probability"),
            "books_compared": books_compared,
            "book_disagreement_score": float(comparison.get("book_disagreement_score", 0.0)),
            "market_identity_score": float(comparison.get("market_identity_confidence", 100.0)),
            "stale_data_risk": bool(comparison.get("stale_data_risk", False)),
            "stale_data_risk_score": 0.0 if comparison.get("stale_data_risk", False) else 100.0,
            "provider_data_quality_score": 100.0 if records_received and records_valid >= 1 else 0.0,
            "liquidity_placeholder_score": 70.0,
            "cross_book_score": min(100.0, float(books_compared) * 35.0),
            "blockers": [],
            "top_reasons": [],
        }

        quality = evaluate_data_quality(
            provider_id="sharp_sportsbook",
            provider_type="sportsbook_odds",
            payload_schema_version=sharp_snapshot.get("schema_version"),
            validation_status="accepted",
            stale_provider_payload=bool(comparison.get("stale_data_risk", False)),
        )
        gate = evaluate_cross_book_gate(
            market_identity_confidence=base["market_identity_score"],
            stale_data=base["stale_data_risk"],
            odds_timestamp_mismatch=bool(comparison.get("timestamp_mismatch_seconds", 0) > 120),
            false_arbitrage_risk=books_compared <= 1,
            liquidity_score=base["liquidity_placeholder_score"],
        )
        settlement = evaluate_settlement_liquidity_gate(liquidity_score=base["liquidity_placeholder_score"])
        lineage = create_lineage_record(
            provider_id="sharp_sportsbook",
            provider_type="sportsbook_odds",
            payload_schema_version=sharp_snapshot.get("schema_version", "unknown"),
            validation_status=quality.get("validation_status", "accepted"),
            snapshot_id=str(sharp_snapshot.get("timestamp", "")),
        )
        base["data_quality_result"] = quality.get("data_quality_result")
        base["cross_book_gate_result"] = gate.get("cross_book_gate_result")
        base["settlement_liquidity_gate_result"] = settlement.get("gate_result")
        base["lineage"] = lineage
        base["blocked_reasons"] = list(gate.get("blocked_reasons", []))

        if books_compared <= 1:
            watch = _build_scored_candidate(
                {
                    **base,
                    "candidate_type": "watch_recheck",
                    "reason": "single_book_only",
                    "blockers": ["single_book_only"],
                    "top_reasons": ["single_book_only"],
                },
                opportunity_score=58.0,
            )
            candidates.append(watch)
            continue

        best_line_candidate = _build_scored_candidate({**base, "candidate_type": "best_line_available"}, opportunity_score=72.0)
        candidates.append(best_line_candidate)

        model_probability = best.get("model_probability")
        no_vig_probability = best.get("no_vig_probability")
        probability_input = model_probability if model_probability is not None else no_vig_probability
        if probability_input is None:
            candidates.append(
                _build_scored_candidate(
                    {
                        **base,
                        "candidate_type": "watch_recheck",
                        "reason": "no_probability_context",
                        "blockers": ["no_probability_context"],
                        "top_reasons": ["no_probability_context"],
                    },
                    opportunity_score=59.0,
                )
            )
        else:
            ev_result = shop_ev_lines(offers, model_probability=float(probability_input))
            ev_best = ev_result.get("best_line_available") or {}
            if ev_result.get("candidate_found") and float(ev_best.get("ev_percent", 0)) > 0:
                candidates.append(
                    _build_scored_candidate(
                        {
                            **base,
                            "candidate_type": "positive_ev_candidate",
                            "model_probability": ev_best.get("model_probability"),
                            "no_vig_probability": ev_best.get("no_vig_probability"),
                            "implied_probability": ev_best.get("implied_probability"),
                            "ev_percent": ev_best.get("ev_percent"),
                            "best_odds": ev_best.get("best_odds", base.get("best_odds")),
                            "best_line": ev_best.get("best_line", base.get("best_line")),
                            "book": ev_best.get("bookmaker", base.get("book")),
                            "best_book": ev_best.get("best_book", base.get("best_book")),
                            "top_reasons": ["positive_ev_probability_backed"],
                        },
                        opportunity_score=78.0,
                    )
                )
            else:
                candidates.append(
                    _build_scored_candidate(
                        {
                            **base,
                            "candidate_type": "watch_recheck",
                            "reason": str(ev_result.get("reason", "no_positive_ev")),
                            "top_reasons": [str(ev_result.get("reason", "no_positive_ev"))],
                        },
                        opportunity_score=57.0,
                    )
                )

        if no_vig_probability is not None:
            candidates.append(
                _build_scored_candidate(
                    {
                        **base,
                        "candidate_type": "no_vig_market_context",
                        "no_vig_probability": no_vig_probability,
                        "top_reasons": ["no_vig_probability_available"],
                    },
                    opportunity_score=70.0,
                )
            )

        if float(base.get("book_disagreement_score", 0.0)) > 0:
            candidates.append(
                _build_scored_candidate(
                    {
                        **base,
                        "candidate_type": "book_disagreement_candidate",
                        "top_reasons": ["book_price_disagreement"],
                    },
                    opportunity_score=74.0,
                )
            )

        arb = detect_arbitrage(
            offers,
            market_identity_confidence=float(base.get("market_identity_score", 0.0)),
            stale_data_risk=bool(base.get("stale_data_risk", False)),
        )
        if arb.get("candidate_found"):
            candidates.append(
                _build_scored_candidate(
                    {
                        **base,
                        "candidate_type": "arbitrage_candidate",
                        "arbitrage_implied_sum": arb.get("arbitrage_implied_sum"),
                        "estimated_roi_percent": arb.get("estimated_roi_percent"),
                        "stake_plan": arb.get("stake_plan"),
                        "top_reasons": ["cross_book_arbitrage_structure_detected"],
                    },
                    opportunity_score=82.0,
                )
            )

        line_offers = [offer for offer in offers if offer.get("line") is not None]
        if len(line_offers) >= 2:
            sorted_line_offers = sorted(line_offers, key=lambda row: float(row.get("line", 0)))
            middle = detect_middle_opportunity(
                sorted_line_offers[0],
                sorted_line_offers[-1],
                market_identity_confidence=float(base.get("market_identity_score", 0.0)),
                stale_data_risk=bool(base.get("stale_data_risk", False)),
            )
            if middle.get("candidate_found"):
                candidates.append(
                    _build_scored_candidate(
                        {
                            **base,
                            "candidate_type": "middle_candidate",
                            "middle_width": middle.get("middle_width"),
                            "middle_zone": middle.get("middle_zone"),
                            "estimated_roi_percent": middle.get("estimated_roi_percent"),
                            "top_reasons": ["line_corridor_detected"],
                        },
                        opportunity_score=76.0,
                    )
                )
    return {
        "records_received": records_received,
        "records_valid": records_valid,
        "records_rejected": records_rejected,
        "candidates": candidates,
        "blockers": [],
    }


def _evaluate_kalshi_review_candidates(config: dict[str, Any], kalshi_snapshot: dict[str, Any] | None) -> dict[str, Any]:
    if not kalshi_snapshot:
        return {
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "candidates": [],
            "rejected_reason_counts": {"kalshi_snapshot_missing": 1},
            "flagged_low_liquidity_count": 0,
            "blockers": ["kalshi_snapshot_missing"],
        }
    source_records = list(kalshi_snapshot.get("records", []))
    now = datetime.now(timezone.utc)
    candidates: list[dict[str, Any]] = []
    rejected_reason_counts: dict[str, int] = {}
    flagged_low_liquidity_count = 0

    for row in source_records:
        if not isinstance(row, dict):
            rejected_reason_counts["malformed_record"] = rejected_reason_counts.get("malformed_record", 0) + 1
            continue

        rejection_reason: str | None = None
        if _is_kalshi_market_stale(row, now):
            rejection_reason = "stale_market"
        elif _is_kalshi_market_closed(row, now):
            rejection_reason = "closed_or_settled_market"
        elif not row.get("contract_id") or not row.get("ticker"):
            rejection_reason = "missing_ticker_or_contract_id"
        elif row.get("yes_price") is None or row.get("no_price") is None:
            rejection_reason = "missing_prices"

        if rejection_reason:
            rejected_reason_counts[rejection_reason] = rejected_reason_counts.get(rejection_reason, 0) + 1
            continue

        liquidity_score, low_liquidity = _kalshi_liquidity_metrics(row)
        if low_liquidity:
            flagged_low_liquidity_count += 1

        settlement_rule = row.get("settlement_rule")
        settlement_status = "present" if settlement_rule else "missing"
        quality = evaluate_data_quality(
            provider_id="kalshi_prediction_market",
            provider_type="prediction_market",
            payload_schema_version=kalshi_snapshot.get("schema_version"),
            validation_status="accepted",
            stale_provider_payload=False,
        )
        settlement = evaluate_settlement_liquidity_gate(
            prediction_market_resolution_match=bool(settlement_rule),
            liquidity_score=float(max(0.0, min(100.0, liquidity_score * 100.0))),
        )
        base = {
            "source": "kalshi_scheduler_review_queue_v1",
            "provider_id": "kalshi_prediction_market",
            "provider": "kalshi_prediction_market",
            "market_type": "prediction_market",
            "sport_or_symbol": "prediction_market",
            "event_id": row.get("event_id"),
            "event_name": row.get("event_title"),
            "market_id": row.get("market_id"),
            "market": row.get("market_id") or row.get("ticker"),
            "selection": row.get("contract_title") or row.get("contract_id"),
            "contract_id": row.get("contract_id"),
            "contract_title": row.get("contract_title"),
            "ticker": row.get("ticker"),
            "yes_bid": row.get("yes_bid"),
            "yes_ask": row.get("yes_ask"),
            "no_bid": row.get("no_bid"),
            "no_ask": row.get("no_ask"),
            "yes_price": row.get("yes_price"),
            "no_price": row.get("no_price"),
            "implied_probability": row.get("implied_probability"),
            "volume": row.get("volume"),
            "open_interest": row.get("open_interest"),
            "liquidity_score": round(liquidity_score, 4),
            "low_liquidity": bool(low_liquidity),
            "market_close_at": row.get("close_time"),
            "close_time": row.get("close_time"),
            "status_reason": row.get("status"),
            "settlement_rule": settlement_rule,
            "settlement_rule_status": settlement_status,
            "data_quality_status": quality.get("data_quality_result"),
            "data_quality_result": quality.get("data_quality_result"),
            "settlement_liquidity_gate_result": settlement.get("gate_result"),
            "execution_feasibility_score": settlement.get("execution_feasibility_score"),
            "settlement_rule_status_gate": settlement.get("settlement_rule_status"),
            "candidate_type": "kalshi_review_candidate",
            "recommendation_status": "review_only",
            "execution_allowed": False,
            "human_approval_required": True,
            "auto_execution_enabled": False,
            "auto_bet_enabled": False,
            "auto_trade_enabled": False,
            "stale_after_seconds": KALSHI_STALE_MARKET_SECONDS,
            "top_reasons": ["prediction_market_review_only"],
            "blockers": ["human_approval_required"] if low_liquidity else [],
        }
        candidates.append(_build_scored_candidate(base, opportunity_score=71.0 if not low_liquidity else 66.0))

    records_received = int(kalshi_snapshot.get("records_received", len(source_records)))
    records_valid = len(candidates)
    records_rejected = int(sum(rejected_reason_counts.values()))
    return {
        "records_received": records_received,
        "records_valid": records_valid,
        "records_rejected": records_rejected,
        "candidates": candidates,
        "rejected_reason_counts": rejected_reason_counts,
        "flagged_low_liquidity_count": flagged_low_liquidity_count,
        "blockers": [],
    }


def run_scheduler_once(*, injected_data: dict[str, Any] | None = None, base_data_dir: str | None = None, dry_run: bool = True, run_key: str | None = None) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("automation scheduler run-once only supports dry_run=true")
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    ctx = create_run_context(config)
    store = SnapshotStore(config)
    payload = injected_data or {}
    store.save_snapshot("scheduler_runs", ctx["run_id"], payload)
    provider_result = _collect_provider_placeholders(config)
    sharp_evaluation = _evaluate_sharp_review_candidates(config, provider_result.get("sharp_snapshot"))
    kalshi_evaluation = _evaluate_kalshi_review_candidates(config, provider_result.get("kalshi_snapshot"))
    save_snapshot("snapshots", f"sharp_snapshot_{ctx['run_id']}", provider_result.get("sharp_snapshot") or {}, config)
    save_snapshot("snapshots", f"kalshi_snapshot_{ctx['run_id']}", provider_result.get("kalshi_snapshot") or {}, config)
    new_items = 0
    watch_recheck_count = 0
    for candidate in list(sharp_evaluation["candidates"]) + list(kalshi_evaluation["candidates"]):
        item = build_review_item(candidate, config)
        if item is None:
            continue
        upsert_review_item(config, item)
        new_items += 1
        if item.get("recommended_action") == "watch_recheck":
            watch_recheck_count += 1
    queue = list_active_review_items(config)
    review_required_count = len([row for row in queue if row.get("recommended_action") in {"review_required", "urgent_review"}])
    skipped = list(payload.get("skipped_items", [])) + provider_result["skipped"]
    report = write_report(
        config,
        report_name=f"scheduler_run_{ctx['run_id']}",
        payload={
            "run_id": ctx["run_id"],
            "created_at": ctx["created_at"],
            "dry_run": True,
            "summary": {
                "review_queue_size": len(queue),
                "records_received": sharp_evaluation["records_received"] + kalshi_evaluation["records_received"],
                "records_valid": sharp_evaluation["records_valid"] + kalshi_evaluation["records_valid"],
                "records_rejected": sharp_evaluation["records_rejected"] + kalshi_evaluation["records_rejected"],
                "candidates_created": new_items,
                "review_required_count": review_required_count,
                "watch_recheck_count": watch_recheck_count,
                "kalshi_flagged_low_liquidity_count": kalshi_evaluation["flagged_low_liquidity_count"],
                "kalshi_rejected_reason_counts": kalshi_evaluation["rejected_reason_counts"],
            },
            "alerts": [],
            "review_items": queue,
            "sharp_candidates": sharp_evaluation["candidates"],
            "kalshi_candidates": kalshi_evaluation["candidates"],
            "skipped_items": skipped,
            "provider_health": provider_result["health"],
            "provider_snapshots": provider_result["snapshots"],
            "errors": [],
            "governance_status": ctx["governance_status"],
        },
    )
    write_system_health(
        config,
        {
            "last_run_id": ctx["run_id"],
            "last_run_at": datetime.now(timezone.utc).isoformat(),
            "sharp_records_received": sharp_evaluation["records_received"],
            "sharp_records_valid": sharp_evaluation["records_valid"],
            "sharp_records_rejected": sharp_evaluation["records_rejected"],
            "sharp_last_snapshot_status": (provider_result.get("sharp_snapshot") or {}).get("status"),
            "sharp_review_candidates_created": len(sharp_evaluation["candidates"]),
            "cross_book_candidates_created": len([c for c in sharp_evaluation["candidates"] if c.get("books_compared", 0) > 1]),
            "kalshi_records_received": kalshi_evaluation["records_received"],
            "kalshi_records_valid": kalshi_evaluation["records_valid"],
            "kalshi_records_rejected": kalshi_evaluation["records_rejected"],
            "kalshi_review_candidates_created": len(kalshi_evaluation["candidates"]),
            "kalshi_flagged_low_liquidity_count": kalshi_evaluation["flagged_low_liquidity_count"],
        },
    )
    return {
        "ok": True,
        "status": "dry_run_complete",
        "run_id": ctx["run_id"],
        "report_id": ctx["run_id"],
        "created_at": ctx["created_at"],
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "records_received": sharp_evaluation["records_received"] + kalshi_evaluation["records_received"],
        "records_valid": sharp_evaluation["records_valid"] + kalshi_evaluation["records_valid"],
        "records_rejected": sharp_evaluation["records_rejected"] + kalshi_evaluation["records_rejected"],
        "sharp_records_received": sharp_evaluation["records_received"],
        "sharp_records_valid": sharp_evaluation["records_valid"],
        "sharp_records_rejected": sharp_evaluation["records_rejected"],
        "kalshi_records_received": kalshi_evaluation["records_received"],
        "kalshi_records_valid": kalshi_evaluation["records_valid"],
        "kalshi_records_rejected": kalshi_evaluation["records_rejected"],
        "candidates_created": new_items,
        "kalshi_candidates_created": len(kalshi_evaluation["candidates"]),
        "kalshi_flagged_low_liquidity_count": kalshi_evaluation["flagged_low_liquidity_count"],
        "kalshi_rejected_reason_counts": kalshi_evaluation["rejected_reason_counts"],
        "review_required_count": review_required_count,
        "watch_recheck_count": watch_recheck_count,
        "skipped_items": skipped,
        "skipped_count": len(skipped),
        "report_path": report.get("path"),
        "blockers": list(sharp_evaluation.get("blockers", [])) + list(kalshi_evaluation.get("blockers", [])),
    }
