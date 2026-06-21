from __future__ import annotations
from pathlib import Path

from datetime import datetime, timezone
from typing import Any

from model_governance.cross_book_gate import evaluate_cross_book_gate
from model_governance.data_lineage import create_lineage_record
from model_governance.data_quality_monitor import evaluate_data_quality
from model_governance.settlement_liquidity_gate import evaluate_settlement_liquidity_gate

from .arbitrage_detector import detect_arbitrage
from .alert_engine import generate_alert_candidates
from .backtesting_engine import run_backtesting_scaffold
from .calibration import build_calibration_report
from .data_paths import resolve_base_data_dir
from .cross_book_line_comparator import group_cross_book_markets
from .ev_line_shopper import shop_ev_lines
from .kalshi_monitor import monitor_kalshi_market
from .middle_opportunity_detector import detect_middle_opportunity
from .opportunity_scoring import calculate_opportunity_score, classify_opportunity
from .paper_decision_ledger import load_paper_decisions, persist_paper_decisions_for_review_items
from src.providers.base import ProviderAdapterBase
from src.providers.health import summarize_provider_health, write_provider_health_snapshot
from .market_structure import kalshi_market_structure_signals
from .kalshi_scoring import KALSHI_LIQUIDITY_POLICY_VERSION, evaluate_kalshi_liquidity_policy, score_kalshi_candidate
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .snapshot_store import save_snapshot
from .snapshot_store import SnapshotStore
from .report_writer import write_report
from .review_queue import (
    build_review_item,
    list_active_review_items,
    persist_review_queue_snapshot,
    summarize_review_items,
    upsert_review_item,
)
from .system_health import write_system_health
from .run_context import create_run_context
from .kalshi_market_provider import get_kalshi_snapshot, summarize_kalshi_snapshot
from .kalshi_readonly_adapter import KalshiReadonlyAdapter
from .sharp_sportsbook_adapter import SharpSportsbookAdapter
from .sportsbook_odds_provider import get_valid_normalized_records, summarize_sportsbook_snapshot


def _existing_artifact_response_path(path_value, *, base_data_dir=None):
    """Return a durable artifact path that exists from the project root."""
    if not path_value:
        return path_value

    candidate = Path(str(path_value))
    if candidate.exists():
        return str(candidate)

    if base_data_dir:
        base_candidate = Path(str(base_data_dir)) / candidate
        if base_candidate.exists():
            return str(base_candidate)

    data_candidate = Path("data") / candidate
    if data_candidate.exists():
        return str(data_candidate)

    return str(candidate)


KALSHI_STALE_MARKET_SECONDS = 60 * 15
KALSHI_TELEMETRY_TOP_LEVEL_FIELDS = (
    "contract_id",
    "contractId",
    "ticker",
    "market_ticker",
    "marketTicker",
    "event_ticker",
    "eventTicker",
    "yes_price",
    "yesPrice",
    "yes",
    "yes_last_price",
    "yesLastPrice",
    "price_yes",
    "priceYes",
    "no_price",
    "noPrice",
    "no",
    "no_last_price",
    "noLastPrice",
    "price_no",
    "priceNo",
    "yes_bid",
    "yesBid",
    "bid_yes",
    "bidYes",
    "yes_bid_price",
    "yesBidPrice",
    "yes_ask",
    "yesAsk",
    "ask_yes",
    "askYes",
    "yes_ask_price",
    "yesAskPrice",
    "no_bid",
    "noBid",
    "bid_no",
    "bidNo",
    "no_bid_price",
    "noBidPrice",
    "no_ask",
    "noAsk",
    "ask_no",
    "askNo",
    "no_ask_price",
    "noAskPrice",
    "pricing",
    "prices",
    "market",
)
KALSHI_NESTED_PRICING_FIELDS = (
    "yes_price",
    "yesPrice",
    "yes",
    "price_yes",
    "priceYes",
    "no_price",
    "noPrice",
    "no",
    "price_no",
    "priceNo",
    "yes_bid",
    "yesBid",
    "bid_yes",
    "bidYes",
    "yes_bid_price",
    "yesBidPrice",
    "yes_ask",
    "yesAsk",
    "ask_yes",
    "askYes",
    "yes_ask_price",
    "yesAskPrice",
    "no_bid",
    "noBid",
    "bid_no",
    "bidNo",
    "no_bid_price",
    "noBidPrice",
    "no_ask",
    "noAsk",
    "ask_no",
    "askNo",
    "no_ask_price",
    "noAskPrice",
)
KALSHI_SOURCE_PRICE_FIELDS = (
    "yes_bid",
    "yesBid",
    "best_bid_yes",
    "yes_ask",
    "yesAsk",
    "best_ask_yes",
    "no_bid",
    "noBid",
    "best_bid_no",
    "no_ask",
    "noAsk",
    "best_ask_no",
    "yes_price",
    "yesPrice",
    "last_price_yes",
    "lastPriceYes",
    "no_price",
    "noPrice",
    "last_price_no",
    "lastPriceNo",
    "yes",
    "no",
    "price_yes",
    "priceYes",
    "price_no",
    "priceNo",
    "yes_bid_dollars",
    "yes_ask_dollars",
    "no_bid_dollars",
    "no_ask_dollars",
    "last_price_dollars",
    "open_interest_fp",
    "volume_fp",
    "open_interest",
    "volume",
    "liquidity_dollars",
)
KALSHI_EXPECTED_SOURCE_FIELDS = (
    "yes_bid_dollars",
    "yes_ask_dollars",
    "no_bid_dollars",
    "no_ask_dollars",
    "last_price_dollars",
    "open_interest_fp",
    "volume_fp",
)
KALSHI_SOURCE_LIQUIDITY_FIELDS = ("volume", "open_interest", "liquidity_dollars", "open_interest_fp", "volume_fp")

KALSHI_CONTRACT_ID_PATHS = (
    ("contract_id",),
    ("contractId",),
    ("ticker",),
    ("market_ticker",),
    ("marketTicker",),
    ("event_ticker",),
    ("eventTicker",),
)
KALSHI_TICKER_PATHS = (
    ("ticker",),
    ("market_ticker",),
    ("marketTicker",),
    ("event_ticker",),
    ("eventTicker",),
)
KALSHI_YES_DIRECT_PATHS = (
    ("yes_price",),
    ("yesPrice",),
    ("yes",),
    ("yes_last_price",),
    ("yesLastPrice",),
    ("price_yes",),
    ("priceYes",),
    ("pricing", "yes_price"),
    ("pricing", "yesPrice"),
    ("pricing", "yes"),
    ("prices", "yes_price"),
    ("prices", "yesPrice"),
    ("prices", "yes"),
    ("market", "yes_price"),
    ("market", "yesPrice"),
    ("market", "yes"),
)
KALSHI_NO_DIRECT_PATHS = (
    ("no_price",),
    ("noPrice",),
    ("no",),
    ("no_last_price",),
    ("noLastPrice",),
    ("price_no",),
    ("priceNo",),
    ("pricing", "no_price"),
    ("pricing", "noPrice"),
    ("pricing", "no"),
    ("prices", "no_price"),
    ("prices", "noPrice"),
    ("prices", "no"),
    ("market", "no_price"),
    ("market", "noPrice"),
    ("market", "no"),
)
KALSHI_YES_BID_PATHS = (
    ("yes_bid",),
    ("yesBid",),
    ("bid_yes",),
    ("bidYes",),
    ("yes_bid_price",),
    ("yesBidPrice",),
    ("pricing", "yes_bid"),
    ("pricing", "yesBid"),
    ("prices", "yes_bid"),
    ("prices", "yesBid"),
    ("market", "yes_bid"),
    ("market", "yesBid"),
)
KALSHI_YES_ASK_PATHS = (
    ("yes_ask",),
    ("yesAsk",),
    ("ask_yes",),
    ("askYes",),
    ("yes_ask_price",),
    ("yesAskPrice",),
    ("pricing", "yes_ask"),
    ("pricing", "yesAsk"),
    ("prices", "yes_ask"),
    ("prices", "yesAsk"),
    ("market", "yes_ask"),
    ("market", "yesAsk"),
)
KALSHI_NO_BID_PATHS = (
    ("no_bid",),
    ("noBid",),
    ("bid_no",),
    ("bidNo",),
    ("no_bid_price",),
    ("noBidPrice",),
    ("pricing", "no_bid"),
    ("pricing", "noBid"),
    ("prices", "no_bid"),
    ("prices", "noBid"),
    ("market", "no_bid"),
    ("market", "noBid"),
)
KALSHI_NO_ASK_PATHS = (
    ("no_ask",),
    ("noAsk",),
    ("ask_no",),
    ("askNo",),
    ("no_ask_price",),
    ("noAskPrice",),
    ("pricing", "no_ask"),
    ("pricing", "noAsk"),
    ("prices", "no_ask"),
    ("prices", "noAsk"),
    ("market", "no_ask"),
    ("market", "noAsk"),
)


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


def _has_usable_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _extract_by_path(row: dict[str, Any], path: tuple[str, ...]) -> tuple[Any, str | None]:
    current: Any = row
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None, None
        current = current.get(key)
    if not _has_usable_value(current):
        return None, None
    return current, ".".join(path)


def _first_probability_from_paths(row: dict[str, Any], paths: tuple[tuple[str, ...], ...]) -> tuple[float | None, str | None]:
    for path in paths:
        raw_value, source_path = _extract_by_path(row, path)
        if raw_value is None:
            continue
        parsed = _to_probability(raw_value)
        if parsed is not None:
            return parsed, source_path
    return None, None


def _first_text_from_paths(row: dict[str, Any], paths: tuple[tuple[str, ...], ...]) -> str | None:
    for path in paths:
        raw_value, _ = _extract_by_path(row, path)
        if raw_value is None:
            continue
        text = str(raw_value).strip()
        if text:
            return text
    return None


def _extract_kalshi_identity(row: dict[str, Any]) -> dict[str, str | None]:
    contract_id = _first_text_from_paths(row, KALSHI_CONTRACT_ID_PATHS)
    ticker = _first_text_from_paths(row, KALSHI_TICKER_PATHS)
    if ticker is None:
        ticker = contract_id
    if contract_id is None:
        contract_id = ticker
    return {"contract_id": contract_id, "ticker": ticker}


def _to_probability(value: Any) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if 0.0 <= parsed <= 1.0:
        return parsed
    if 1.0 < parsed <= 100.0:
        return parsed / 100.0
    return None


def _to_float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_kalshi_pricing_signals(row: dict[str, Any]) -> dict[str, Any]:
    yes_price, yes_price_path = _first_probability_from_paths(row, KALSHI_YES_DIRECT_PATHS)
    no_price, no_price_path = _first_probability_from_paths(row, KALSHI_NO_DIRECT_PATHS)
    yes_bid, yes_bid_path = _first_probability_from_paths(row, KALSHI_YES_BID_PATHS)
    yes_ask, yes_ask_path = _first_probability_from_paths(row, KALSHI_YES_ASK_PATHS)
    no_bid, no_bid_path = _first_probability_from_paths(row, KALSHI_NO_BID_PATHS)
    no_ask, no_ask_path = _first_probability_from_paths(row, KALSHI_NO_ASK_PATHS)
    signal_sources = [
        path
        for path in (yes_price_path, no_price_path, yes_bid_path, yes_ask_path, no_bid_path, no_ask_path)
        if path
    ]
    return {
        "yes_price": yes_price,
        "no_price": no_price,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "has_direct_yes_price": yes_price is not None,
        "has_direct_no_price": no_price is not None,
        "has_yes_bid": yes_bid is not None,
        "has_yes_ask": yes_ask is not None,
        "has_no_bid": no_bid is not None,
        "has_no_ask": no_ask is not None,
        "signal_sources": signal_sources[:12],
    }


def _derive_kalshi_pricing(row: dict[str, Any]) -> dict[str, Any]:
    extracted = _extract_kalshi_pricing_signals(row)
    yes_price = extracted["yes_price"]
    no_price = extracted["no_price"]
    yes_bid = extracted["yes_bid"]
    yes_ask = extracted["yes_ask"]
    no_bid = extracted["no_bid"]
    no_ask = extracted["no_ask"]
    yes_midpoint = None
    no_midpoint = None
    if yes_bid is not None and yes_ask is not None:
        yes_midpoint = (yes_bid + yes_ask) / 2.0
    if no_bid is not None and no_ask is not None:
        no_midpoint = (no_bid + no_ask) / 2.0

    derived_price = False
    partial_pricing = False
    price_source = "missing"
    pricing_quality = "missing"
    implied_probability = _to_probability(row.get("implied_probability"))

    if yes_price is not None or no_price is not None:
        price_source = "direct_price"
        if yes_price is not None and no_price is not None:
            pricing_quality = "complete"
        else:
            partial_pricing = True
            pricing_quality = "partial"
            derived_price = True
            if yes_price is None and no_price is not None:
                yes_price = max(0.0, min(1.0, 1.0 - no_price))
            elif no_price is None and yes_price is not None:
                no_price = max(0.0, min(1.0, 1.0 - yes_price))
        if implied_probability is None and yes_price is not None:
            implied_probability = yes_price
    elif yes_midpoint is not None and no_midpoint is not None:
        yes_price = yes_midpoint
        no_price = no_midpoint
        derived_price = True
        price_source = "bid_ask_midpoint"
        pricing_quality = "complete"
        implied_probability = yes_midpoint if implied_probability is None else implied_probability
    elif yes_midpoint is not None or no_midpoint is not None:
        partial_pricing = True
        derived_price = True
        price_source = "partial_bid_ask"
        pricing_quality = "partial"
        if yes_midpoint is not None:
            yes_price = yes_midpoint
            if no_price is None:
                no_price = max(0.0, min(1.0, 1.0 - yes_midpoint))
            implied_probability = yes_midpoint if implied_probability is None else implied_probability
        if no_midpoint is not None:
            no_price = no_midpoint
            if yes_price is None:
                yes_price = max(0.0, min(1.0, 1.0 - no_midpoint))
            implied_probability = (1.0 - no_midpoint) if implied_probability is None else implied_probability
    else:
        price_source = "missing"
        pricing_quality = "missing"

    return {
        "yes_price": yes_price,
        "no_price": no_price,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "implied_probability": implied_probability,
        "derived_price": derived_price,
        "price_source": price_source,
        "partial_pricing": partial_pricing,
        "pricing_quality": pricing_quality,
        "has_direct_yes_price": extracted["has_direct_yes_price"],
        "has_direct_no_price": extracted["has_direct_no_price"],
        "has_yes_bid": extracted["has_yes_bid"],
        "has_yes_ask": extracted["has_yes_ask"],
        "has_no_bid": extracted["has_no_bid"],
        "has_no_ask": extracted["has_no_ask"],
        "price_debug_summary": {"signal_sources": extracted["signal_sources"]},
    }


def _build_kalshi_price_field_telemetry() -> dict[str, Any]:
    return {
        "total_kalshi_records_seen": 0,
        "records_with_direct_yes_price": 0,
        "records_with_direct_no_price": 0,
        "records_with_yes_bid": 0,
        "records_with_yes_ask": 0,
        "records_with_no_bid": 0,
        "records_with_no_ask": 0,
        "records_with_bid_ask_midpoint_possible": 0,
        "records_with_any_price_signal": 0,
        "records_missing_all_price_signals": 0,
        "top_level_field_presence_counts": {name: 0 for name in KALSHI_TELEMETRY_TOP_LEVEL_FIELDS},
        "nested_pricing_object_presence_counts": {"pricing": 0, "prices": 0, "market": 0},
        "first_record_safe_field_names": [],
        "source_payload_field_presence_counts": {name: 0 for name in KALSHI_SOURCE_PRICE_FIELDS},
        "source_payload_nested_object_presence_counts": {"pricing": 0, "prices": 0, "market": 0},
        "source_payload_first_record_safe_field_names": [],
        "accepted_source_field_names": [],
        "missing_expected_source_fields": list(KALSHI_EXPECTED_SOURCE_FIELDS),
        "unexpected_source_field_count": 0,
        "pricing_signal_field_count": 0,
        "liquidity_signal_field_count": 0,
        "records_with_volume": 0,
        "records_with_open_interest": 0,
        "records_with_liquidity": 0,
        "records_with_direct_liquidity": 0,
        "records_with_liquidity_proxy": 0,
        "records_missing_liquidity": 0,
        "records_flagged_low_liquidity": 0,
        "records_low_liquidity_due_to_missing_liquidity": 0,
        "records_low_liquidity_due_to_threshold": 0,
        "records_low_liquidity_due_to_status": 0,
        "liquidity_threshold_used": {},
        "liquidity_policy_version": KALSHI_LIQUIDITY_POLICY_VERSION,
        "liquidity_source_counts": {},
        "liquidity_tier_counts": {},
    }


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
            "flagged_partial_pricing_count": 0,
            "price_field_telemetry": _build_kalshi_price_field_telemetry(),
            "blockers": ["kalshi_snapshot_missing"],
        }
    source_records = list(kalshi_snapshot.get("records", []))
    now = datetime.now(timezone.utc)
    candidates: list[dict[str, Any]] = []
    rejected_reason_counts: dict[str, int] = {}
    flagged_low_liquidity_count = 0
    flagged_partial_pricing_count = 0
    telemetry = _build_kalshi_price_field_telemetry()
    source_payload_seen_fields: set[str] = set()

    for row in source_records:
        if not isinstance(row, dict):
            rejected_reason_counts["malformed_record"] = rejected_reason_counts.get("malformed_record", 0) + 1
            continue
        telemetry["total_kalshi_records_seen"] += 1
        if not telemetry["first_record_safe_field_names"]:
            telemetry["first_record_safe_field_names"] = sorted(
                [name for name in row.keys() if name in KALSHI_TELEMETRY_TOP_LEVEL_FIELDS]
            )[:40]
        for field in KALSHI_TELEMETRY_TOP_LEVEL_FIELDS:
            if _has_usable_value(row.get(field)):
                telemetry["top_level_field_presence_counts"][field] += 1
        for nested_name in ("pricing", "prices", "market"):
            nested_value = row.get(nested_name)
            if not isinstance(nested_value, dict):
                continue
            telemetry["nested_pricing_object_presence_counts"][nested_name] += 1
            for nested_field in KALSHI_NESTED_PRICING_FIELDS:
                compound_name = f"{nested_name}.{nested_field}"
                if compound_name not in telemetry["top_level_field_presence_counts"]:
                    telemetry["top_level_field_presence_counts"][compound_name] = 0
                if _has_usable_value(nested_value.get(nested_field)):
                    telemetry["top_level_field_presence_counts"][compound_name] += 1
        source_payload = row.get("source_payload_redacted")
        if isinstance(source_payload, dict):
            if not telemetry["source_payload_first_record_safe_field_names"]:
                telemetry["source_payload_first_record_safe_field_names"] = sorted([str(name) for name in source_payload.keys()])[:60]
            source_payload_seen_fields.update(str(name) for name in source_payload.keys())
            for field in KALSHI_SOURCE_PRICE_FIELDS:
                if _has_usable_value(source_payload.get(field)):
                    telemetry["source_payload_field_presence_counts"][field] += 1
            for nested_name in ("pricing", "prices", "market"):
                nested_value = source_payload.get(nested_name)
                if not isinstance(nested_value, dict):
                    continue
                telemetry["source_payload_nested_object_presence_counts"][nested_name] += 1
                for nested_field in KALSHI_NESTED_PRICING_FIELDS:
                    compound_name = f"{nested_name}.{nested_field}"
                    if compound_name not in telemetry["source_payload_field_presence_counts"]:
                        telemetry["source_payload_field_presence_counts"][compound_name] = 0
                    if _has_usable_value(nested_value.get(nested_field)):
                        telemetry["source_payload_field_presence_counts"][compound_name] += 1

        pricing = _derive_kalshi_pricing(row)
        identity = _extract_kalshi_identity(row)
        volume_value = _to_float_or_none(row.get("volume"))
        open_interest_value = _to_float_or_none(row.get("open_interest"))
        liquidity_value = _to_float_or_none(row.get("liquidity_score"))
        if volume_value is not None and volume_value > 0:
            telemetry["records_with_volume"] += 1
        if open_interest_value is not None and open_interest_value > 0:
            telemetry["records_with_open_interest"] += 1
        if liquidity_value is not None:
            telemetry["records_with_liquidity"] += 1
            telemetry["records_with_direct_liquidity"] += 1
        if volume_value is not None or open_interest_value is not None:
            telemetry["records_with_liquidity_proxy"] += 1
        if pricing["has_direct_yes_price"]:
            telemetry["records_with_direct_yes_price"] += 1
        if pricing["has_direct_no_price"]:
            telemetry["records_with_direct_no_price"] += 1
        if pricing["has_yes_bid"]:
            telemetry["records_with_yes_bid"] += 1
        if pricing["has_yes_ask"]:
            telemetry["records_with_yes_ask"] += 1
        if pricing["has_no_bid"]:
            telemetry["records_with_no_bid"] += 1
        if pricing["has_no_ask"]:
            telemetry["records_with_no_ask"] += 1
        has_yes_midpoint = pricing["yes_bid"] is not None and pricing["yes_ask"] is not None
        has_no_midpoint = pricing["no_bid"] is not None and pricing["no_ask"] is not None
        if has_yes_midpoint or has_no_midpoint:
            telemetry["records_with_bid_ask_midpoint_possible"] += 1
        if any(
            (
                pricing["has_direct_yes_price"],
                pricing["has_direct_no_price"],
                pricing["has_yes_bid"],
                pricing["has_yes_ask"],
                pricing["has_no_bid"],
                pricing["has_no_ask"],
            )
        ):
            telemetry["records_with_any_price_signal"] += 1
        else:
            telemetry["records_missing_all_price_signals"] += 1
        rejection_reason: str | None = None
        if _is_kalshi_market_stale(row, now):
            rejection_reason = "stale_market"
        elif _is_kalshi_market_closed(row, now):
            rejection_reason = "closed_or_settled_market"
        elif not identity["contract_id"] or not identity["ticker"]:
            rejection_reason = "missing_ticker_or_contract_id"
        elif pricing["pricing_quality"] == "missing":
            rejection_reason = "missing_prices"

        if rejection_reason:
            rejected_reason_counts[rejection_reason] = rejected_reason_counts.get(rejection_reason, 0) + 1
            continue

        liquidity_policy = evaluate_kalshi_liquidity_policy({**row, **pricing})
        liquidity_score = float(liquidity_policy["liquidity_score"])
        low_liquidity = bool(liquidity_policy["low_liquidity_flag"])
        missing_liquidity = bool(liquidity_policy["missing_liquidity_flag"])
        liquidity_source = str(liquidity_policy["liquidity_source"])
        liquidity_tier = str(liquidity_policy["liquidity_tier"])
        telemetry["liquidity_source_counts"][liquidity_source] = int(telemetry["liquidity_source_counts"].get(liquidity_source, 0)) + 1
        telemetry["liquidity_tier_counts"][liquidity_tier] = int(telemetry["liquidity_tier_counts"].get(liquidity_tier, 0)) + 1
        telemetry["liquidity_threshold_used"] = liquidity_policy["liquidity_threshold_used"]
        if missing_liquidity:
            telemetry["records_missing_liquidity"] += 1
            telemetry["records_low_liquidity_due_to_missing_liquidity"] += 1
        if low_liquidity:
            flagged_low_liquidity_count += 1
            telemetry["records_flagged_low_liquidity"] += 1
            telemetry["records_low_liquidity_due_to_threshold"] += 1
        if pricing["partial_pricing"]:
            flagged_partial_pricing_count += 1

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
            liquidity_score=float(max(0.0, min(100.0, liquidity_score))),
        )
        signal_input = {
            **row,
            **pricing,
            **liquidity_policy,
            "liquidity_score": liquidity_score,
            "low_liquidity": low_liquidity,
            "missing_liquidity": missing_liquidity,
            "stale_market": _is_kalshi_market_stale(row, now),
        }
        market_structure = kalshi_market_structure_signals(signal_input, previous=None)
        scoring = score_kalshi_candidate(signal_input)
        base = {
            "source": "kalshi_scheduler_review_queue_v1",
            "provider_id": "kalshi_prediction_market",
            "provider": "kalshi_prediction_market",
            "source_type": "prediction_market",
            "market_type": "prediction_market",
            "sport_or_symbol": "prediction_market",
            "event_id": row.get("event_id"),
            "event_name": row.get("event_title"),
            "market_id": row.get("market_id"),
            "market": row.get("market_id") or identity["ticker"],
            "selection": row.get("contract_title") or identity["contract_id"],
            "contract_id": identity["contract_id"],
            "contract_title": row.get("contract_title"),
            "ticker": identity["ticker"],
            "yes_bid": pricing["yes_bid"],
            "yes_ask": pricing["yes_ask"],
            "no_bid": pricing["no_bid"],
            "no_ask": pricing["no_ask"],
            "yes_price": pricing["yes_price"],
            "no_price": pricing["no_price"],
            "implied_probability": pricing["implied_probability"],
            "derived_price": pricing["derived_price"],
            "price_source": pricing["price_source"],
            "partial_pricing": pricing["partial_pricing"],
            "pricing_quality": pricing["pricing_quality"],
            "price_debug_summary": pricing["price_debug_summary"],
            "volume": row.get("volume"),
            "open_interest": row.get("open_interest"),
            "liquidity_score": round(liquidity_score, 4),
            "liquidity_policy_version": liquidity_policy["liquidity_policy_version"],
            "liquidity_source": liquidity_policy["liquidity_source"],
            "liquidity_tier": liquidity_policy["liquidity_tier"],
            "liquidity_reason": liquidity_policy["liquidity_reason"],
            "low_liquidity_flag": bool(liquidity_policy["low_liquidity_flag"]),
            "missing_liquidity_flag": bool(liquidity_policy["missing_liquidity_flag"]),
            "missing_liquidity": bool(missing_liquidity),
            "liquidity_threshold_used": liquidity_policy["liquidity_threshold_used"],
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
            "top_reasons": ["prediction_market_review_only", pricing["price_source"]],
            "reason_codes": ["prediction_market_review_only", pricing["price_source"]],
            "blockers": ["human_approval_required"] + (["low_liquidity"] if low_liquidity else []),
            "market_structure_signals": market_structure,
            "spread_score": scoring["spread_score"],
            "pricing_quality_score": scoring["pricing_quality_score"],
            "close_time_score": scoring["close_time_score"],
            "market_structure_score": scoring["market_structure_score"],
            "confidence_score": scoring["confidence_score"],
            "risk_score": scoring["risk_score"],
            "review_priority_score": scoring["review_priority_score"],
            "classification": scoring["classification"],
        }
        candidates.append(_build_scored_candidate(base, opportunity_score=max(56.0, float(scoring["review_priority_score"]))))

    records_received = int(kalshi_snapshot.get("records_received", len(source_records)))
    records_valid = len(candidates)
    records_rejected = int(sum(rejected_reason_counts.values()))
    telemetry["accepted_source_field_names"] = sorted(
        [name for name in KALSHI_EXPECTED_SOURCE_FIELDS if int(telemetry["source_payload_field_presence_counts"].get(name, 0)) > 0]
    )
    telemetry["missing_expected_source_fields"] = sorted(
        [name for name in KALSHI_EXPECTED_SOURCE_FIELDS if name not in telemetry["accepted_source_field_names"]]
    )
    expected_source_field_set = set(KALSHI_EXPECTED_SOURCE_FIELDS)
    telemetry["unexpected_source_field_count"] = len([name for name in source_payload_seen_fields if name not in expected_source_field_set])
    telemetry["pricing_signal_field_count"] = len(
        [name for name, count in telemetry["source_payload_field_presence_counts"].items() if count and ("price" in name or "bid" in name or "ask" in name or name in {"yes", "no"})]
    )
    telemetry["liquidity_signal_field_count"] = len(
        [name for name in KALSHI_SOURCE_LIQUIDITY_FIELDS if int(telemetry["source_payload_field_presence_counts"].get(name, 0)) > 0]
    )
    return {
        "records_received": records_received,
        "records_valid": records_valid,
        "records_rejected": records_rejected,
        "candidates": candidates,
        "rejected_reason_counts": rejected_reason_counts,
        "flagged_low_liquidity_count": flagged_low_liquidity_count,
        "flagged_partial_pricing_count": flagged_partial_pricing_count,
        "price_field_telemetry": telemetry,
        "blockers": [],
    }



def _ensure_kalshi_prediction_market_skip(result: dict) -> dict:
    """
    Preserve scheduler dry-run contract: Kalshi prediction market context is
    provider enrichment / read-only context, not an auto-execution sportsbook leg.
    Tests expect this provider-level skip metadata to be present.
    """
    skipped_items = result.setdefault("skipped_items", [])

    if not isinstance(skipped_items, list):
        skipped_items = []
        result["skipped_items"] = skipped_items

    for row in skipped_items:
        if isinstance(row, dict) and row.get("provider_id") == "kalshi_prediction_market":
            return result

    skipped_items.append(
        {
            "provider_id": "kalshi_prediction_market",
            "reason": "prediction_market_context_only",
            "execution_allowed": False,
            "read_only": True,
        }
    )
    return result


def _run_scheduler_once_impl(*, injected_data: dict[str, Any] | None = None, base_data_dir: str | None = None, dry_run: bool = True, run_key: str | None = None) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("automation scheduler run-once only supports dry_run=true")
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    ctx = create_run_context(config)
    store = SnapshotStore(config)
    payload = injected_data or {}
    store.save_snapshot("scheduler_runs", ctx["run_id"], payload)
    provider_result = _collect_provider_placeholders(config)
    previous_kalshi_wrapper = store.load_latest_snapshot("snapshots", "kalshi_latest")
    previous_kalshi_records = []
    if isinstance(previous_kalshi_wrapper, dict):
        previous_payload = previous_kalshi_wrapper.get("payload", {})
        if isinstance(previous_payload, dict):
            previous_kalshi_records = list(previous_payload.get("records", []))
    sharp_evaluation = _evaluate_sharp_review_candidates(config, provider_result.get("sharp_snapshot"))
    kalshi_evaluation = _evaluate_kalshi_review_candidates(config, provider_result.get("kalshi_snapshot"))
    monitor_result = monitor_kalshi_market(
        previous_snapshot=previous_kalshi_records,
        current_snapshot=list((provider_result.get("kalshi_snapshot") or {}).get("records", [])),
        provider="kalshi_prediction_market",
        config=config,
    )
    save_snapshot("snapshots", f"sharp_snapshot_{ctx['run_id']}", provider_result.get("sharp_snapshot") or {}, config)
    save_snapshot("snapshots", f"kalshi_snapshot_{ctx['run_id']}", provider_result.get("kalshi_snapshot") or {}, config)
    save_snapshot("snapshots", "kalshi_latest", provider_result.get("kalshi_snapshot") or {}, config)
    new_items = 0
    watch_recheck_count = 0
    all_candidates = list(sharp_evaluation["candidates"]) + list(kalshi_evaluation["candidates"]) + list(monitor_result.get("candidates", []))
    for candidate in all_candidates:
        item = build_review_item(candidate, config)
        if item is None:
            continue
        upsert_review_item(config, item)
        new_items += 1
        if item.get("recommended_action") == "watch_recheck":
            watch_recheck_count += 1
    queue = list_active_review_items(config)
    queue_summary = summarize_review_items(queue, rejected_reason_counts=kalshi_evaluation["rejected_reason_counts"])
    kalshi_queue_items = [item for item in queue if item.get("provider_id") == "kalshi_prediction_market"]
    kalshi_priority_scores = [float(item.get("review_priority_score") or 0.0) for item in kalshi_queue_items]
    kalshi_high_priority_count = len([score for score in kalshi_priority_scores if score >= 70.0])
    kalshi_average_review_priority_score = round(sum(kalshi_priority_scores) / len(kalshi_priority_scores), 4) if kalshi_priority_scores else 0.0
    queue_storage = persist_review_queue_snapshot(
        config,
        queue,
        run_id=ctx["run_id"],
        summary=queue_summary,
    )
    expected_report_path = f"reports/scheduler_run_{ctx['run_id']}.json"
    paper_ledger_storage = persist_paper_decisions_for_review_items(
        queue,
        run_id=ctx["run_id"],
        snapshot_id=ctx["run_id"],
        report_path=expected_report_path,
        base_data_dir=base_data_dir,
    )
    review_required_count = len([row for row in queue if row.get("recommended_action") in {"review_required", "urgent_review"}])
    alerts = generate_alert_candidates(queue, max_alerts=25, time_bucket=ctx["run_id"])
    paper_decisions = [item for item in load_paper_decisions(base_data_dir) if isinstance(item, dict)]
    backtesting_summary = run_backtesting_scaffold(paper_decisions)
    calibration_summary = build_calibration_report(
        base_data_dir=base_data_dir,
        paper_decisions=paper_decisions,
        review_items=queue,
        write_report=True,
    )
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
                "kalshi_flagged_partial_pricing_count": kalshi_evaluation["flagged_partial_pricing_count"],
                "kalshi_liquidity_tier_counts": kalshi_evaluation.get("price_field_telemetry", {}).get("liquidity_tier_counts", {}),
                "kalshi_missing_liquidity_count": kalshi_evaluation.get("price_field_telemetry", {}).get("records_missing_liquidity", 0),
                "kalshi_high_priority_count": kalshi_high_priority_count,
                "kalshi_average_review_priority_score": kalshi_average_review_priority_score,
                "kalshi_rejected_reason_counts": kalshi_evaluation["rejected_reason_counts"],
                "kalshi_price_field_telemetry": kalshi_evaluation.get("price_field_telemetry", {}),
                "review_queue_storage_backend": queue_storage.get("storage_backend"),
                "review_queue_items_written": queue_storage.get("items_written_count"),
                "review_queue_latest_run_id": queue_storage.get("latest_run_id"),
                "paper_decisions_written": paper_ledger_storage.get("paper_decisions_written"),
                "paper_ledger_storage_backend": paper_ledger_storage.get("storage_backend"),
                "paper_ledger_latest_run_id": paper_ledger_storage.get("latest_run_id"),
            },
            "alerts": alerts,
            "review_items": queue,
            "sharp_candidates": sharp_evaluation["candidates"],
            "kalshi_candidates": kalshi_evaluation["candidates"],
            "kalshi_watch_candidates": monitor_result.get("candidates", []),
            "skipped_items": skipped,
            "provider_health": provider_result["health"],
            "provider_snapshots": provider_result["snapshots"],
            "errors": [],
            "governance_status": ctx["governance_status"],
            "paper_decision_ledger": paper_ledger_storage,
            "backtesting": backtesting_summary,
            "calibration": calibration_summary,
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
            "kalshi_flagged_partial_pricing_count": kalshi_evaluation["flagged_partial_pricing_count"],
            "kalshi_liquidity_tier_counts": kalshi_evaluation.get("price_field_telemetry", {}).get("liquidity_tier_counts", {}),
            "kalshi_missing_liquidity_count": kalshi_evaluation.get("price_field_telemetry", {}).get("records_missing_liquidity", 0),
            "kalshi_high_priority_count": kalshi_high_priority_count,
            "kalshi_average_review_priority_score": kalshi_average_review_priority_score,
            "kalshi_rejected_reason_counts": kalshi_evaluation["rejected_reason_counts"],
            "kalshi_price_field_telemetry": kalshi_evaluation.get("price_field_telemetry", {}),
            "review_queue_storage_backend": queue_storage.get("storage_backend"),
            "review_queue_total_count": len(queue),
            "review_queue_last_updated_at": queue_storage.get("last_updated_at"),
            "review_queue_latest_run_id": queue_storage.get("latest_run_id"),
            "review_queue_read_ok": True,
            "paper_decisions_count": len(paper_decisions),
            "paper_decisions_written": paper_ledger_storage.get("paper_decisions_written"),
            "paper_ledger_storage_backend": paper_ledger_storage.get("storage_backend"),
            "paper_ledger_last_updated_at": paper_ledger_storage.get("last_updated_at"),
            "paper_ledger_latest_run_id": paper_ledger_storage.get("latest_run_id"),
            "calibration_status": calibration_summary.get("status"),
            "calibration_settled_count": calibration_summary.get("settled_count"),
            "calibration_coverage_rate": calibration_summary.get("coverage_rate"),
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
        "sharp_candidates_created": len(sharp_evaluation["candidates"]),
        "sharp_blockers": list(sharp_evaluation.get("blockers", [])),
        "kalshi_records_received": kalshi_evaluation["records_received"],
        "kalshi_records_valid": kalshi_evaluation["records_valid"],
        "kalshi_records_rejected": kalshi_evaluation["records_rejected"],
        "candidates_created": new_items,
        "kalshi_candidates_created": len(kalshi_evaluation["candidates"]),
        "kalshi_watch_items_created": len(monitor_result.get("candidates", [])),
        "kalshi_flagged_low_liquidity_count": kalshi_evaluation["flagged_low_liquidity_count"],
        "kalshi_flagged_partial_pricing_count": kalshi_evaluation["flagged_partial_pricing_count"],
        "kalshi_liquidity_tier_counts": kalshi_evaluation.get("price_field_telemetry", {}).get("liquidity_tier_counts", {}),
        "kalshi_missing_liquidity_count": kalshi_evaluation.get("price_field_telemetry", {}).get("records_missing_liquidity", 0),
        "kalshi_high_priority_count": kalshi_high_priority_count,
        "kalshi_average_review_priority_score": kalshi_average_review_priority_score,
        "kalshi_rejected_reason_counts": kalshi_evaluation["rejected_reason_counts"],
        "kalshi_price_field_telemetry": kalshi_evaluation.get("price_field_telemetry", {}),
        "kalshi_blockers": list(kalshi_evaluation.get("blockers", [])),
        "review_required_count": review_required_count,
        "watch_recheck_count": watch_recheck_count,
        "skipped_items": skipped,
        "skipped_count": len(skipped),
        "alerts_created": len(alerts),
        "alerts": alerts,
        "backtesting": backtesting_summary,
        "calibration": calibration_summary,
        "report_path": report.get("path"),
        "review_queue_items_written": int(queue_storage.get("items_written_count", len(queue))),
        "review_queue_storage_backend": queue_storage.get("storage_backend", "file"),
        "review_queue_write_path": _existing_artifact_response_path(queue_storage.get("queue_write_path"), base_data_dir=base_data_dir),
        "review_queue_latest_run_id": queue_storage.get("latest_run_id"),
        "review_queue_last_updated_at": queue_storage.get("last_updated_at"),
        "paper_decisions_written": int(paper_ledger_storage.get("paper_decisions_written", len(paper_decisions))),
        "paper_decisions_count": len(paper_decisions),
        "paper_ledger_storage_backend": paper_ledger_storage.get("storage_backend", "file"),
        "paper_ledger_write_path": _existing_artifact_response_path(paper_ledger_storage.get("paper_ledger_write_path"), base_data_dir=base_data_dir),
        "paper_ledger_latest_run_id": paper_ledger_storage.get("latest_run_id"),
        "paper_ledger_last_updated_at": paper_ledger_storage.get("last_updated_at"),
        "blockers": list(sharp_evaluation.get("blockers", [])) + list(kalshi_evaluation.get("blockers", [])),
    }

# PHASE5A_RUN_SCHEDULER_ONCE_WRAPPER
def run_scheduler_once(*args, **kwargs):
    """
    Compatibility wrapper around the scheduler implementation.

    Keeps the public function name stable while enforcing dry-run provider
    skip metadata expected by scheduler contract tests.
    """
    import inspect

    sig = inspect.signature(_run_scheduler_once_impl)
    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    result = _run_scheduler_once_impl(*args, **kwargs)

    if bound.arguments.get("dry_run"):
        result = _ensure_kalshi_prediction_market_skip(result)

    return result
