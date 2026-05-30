from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .data_paths import resolve_base_data_dir
from .institutional_cross_asset_scores import complete_institutional_scores, to_float
from .outcome_store import load_outcome_records
from .paper_decision_ledger import load_paper_decisions
from .review_queue import load_review_queue_state
from .scheduler_config import safe_run_id, utc_now_iso


ASSET_CLASSES = ("prediction_market", "stock", "bond", "major_asset", "sportsbook")
SENSITIVE_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")
RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_broker_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
    "full_provider_response",
}

NORMALIZED_RECORD_FIELDS = (
    "sidecar_id",
    "source_record_id",
    "asset_class",
    "provider",
    "market_type",
    "symbol_or_ticker",
    "contract_id",
    "event_id",
    "selection",
    "observed_at",
    "outcome_horizon",
    "observed_price",
    "bid",
    "ask",
    "mid",
    "spread",
    "volume",
    "open_interest",
    "implied_probability",
    "no_vig_probability",
    "model_probability",
    "edge",
    "quick_quality_score",
    "broad_quality_score",
    "liquidity_score",
    "pricing_quality_score",
    "market_structure_score",
    "valuation_score",
    "edge_quality_score",
    "financial_quality_score",
    "macro_quality_score",
    "settlement_quality_score",
    "calibration_readiness_score",
    "execution_readiness_score",
    "risk_score",
    "confidence_score",
    "review_priority_score",
    "quality_tier",
    "liquidity_tier",
    "risk_tier",
    "execution_readiness_tier",
    "reason_codes",
    "missing_fields",
    "outcome_status",
    "final_outcome",
    "settled_at",
    "final_price",
    "return_pct",
    "source_module",
    "paper_only",
    "review_only",
    "simulation_only",
    "execution_allowed",
)


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def compact_redact(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            key_text = str(key)
            lower = key_text.lower()
            if lower in RAW_PAYLOAD_KEYS or any(part in lower for part in SENSITIVE_KEY_PARTS):
                continue
            if isinstance(value, dict):
                out[key_text] = compact_redact(value)
            elif isinstance(value, list):
                safe_list = []
                for item in value[:25]:
                    if isinstance(item, dict):
                        safe_list.append(compact_redact(item))
                    else:
                        scalar = _safe_scalar(item)
                        if scalar is not None:
                            safe_list.append(scalar)
                out[key_text] = safe_list
            else:
                out[key_text] = _safe_scalar(value)
        return out
    if isinstance(payload, list):
        return [compact_redact(item) if isinstance(item, dict) else _safe_scalar(item) for item in payload[:25]]
    return _safe_scalar(payload)


def _sidecar_id(asset_class: str, provider: str, source_module: str, source_record_id: str) -> str:
    seed = "|".join([asset_class, provider, source_module, source_record_id])
    return f"sidecar_{safe_run_id('institutional_sidecar', seed)}"


def _source_record_id(item: dict[str, Any]) -> str:
    for key in ("sidecar_id", "decision_id", "id", "review_item_id", "outcome_id", "contract_id", "ticker", "symbol"):
        if item.get(key):
            return str(item[key])
    return safe_run_id("institutional_source", repr(compact_redact(item)))


def _mid(bid: Any, ask: Any, fallback: Any = None) -> float | None:
    b = to_float(bid)
    a = to_float(ask)
    if b is not None and a is not None and a >= b:
        return round((a + b) / 2.0, 8)
    return to_float(fallback)


def _spread(bid: Any, ask: Any, fallback: Any = None) -> float | None:
    explicit = to_float(fallback)
    if explicit is not None:
        return explicit
    b = to_float(bid)
    a = to_float(ask)
    if b is not None and a is not None:
        return round(a - b, 8)
    return None


def _base_record(
    item: dict[str, Any],
    *,
    asset_class: str,
    provider: str,
    market_type: str,
    source_module: str,
) -> dict[str, Any]:
    source_record_id = _source_record_id(item)
    observed_at = item.get("observed_at") or item.get("updated_at") or item.get("created_at") or item.get("timestamp") or utc_now_iso()
    return {
        "sidecar_id": _sidecar_id(asset_class, provider, source_module, source_record_id),
        "source_record_id": source_record_id,
        "asset_class": asset_class,
        "provider": provider,
        "market_type": market_type,
        "symbol_or_ticker": item.get("ticker") or item.get("symbol") or item.get("symbol_or_ticker"),
        "contract_id": item.get("contract_id"),
        "event_id": item.get("event_id"),
        "selection": item.get("selection") or item.get("title") or item.get("contract_title"),
        "observed_at": observed_at,
        "outcome_horizon": item.get("outcome_horizon"),
        "observed_price": item.get("observed_price"),
        "bid": item.get("bid"),
        "ask": item.get("ask"),
        "mid": item.get("mid"),
        "spread": item.get("spread"),
        "volume": item.get("volume"),
        "open_interest": item.get("open_interest"),
        "implied_probability": item.get("implied_probability"),
        "no_vig_probability": item.get("no_vig_probability"),
        "model_probability": item.get("model_probability"),
        "edge": item.get("edge") or item.get("ev_percent"),
        "quick_quality_score": item.get("quick_quality_score"),
        "broad_quality_score": item.get("broad_quality_score"),
        "liquidity_score": item.get("liquidity_score"),
        "pricing_quality_score": item.get("pricing_quality_score"),
        "market_structure_score": item.get("market_structure_score"),
        "valuation_score": item.get("valuation_score"),
        "edge_quality_score": item.get("edge_quality_score"),
        "financial_quality_score": item.get("financial_quality_score"),
        "macro_quality_score": item.get("macro_quality_score") or item.get("macro_regime_score"),
        "settlement_quality_score": item.get("settlement_quality_score"),
        "calibration_readiness_score": item.get("calibration_readiness_score"),
        "execution_readiness_score": item.get("execution_readiness_score") or item.get("execution_feasibility_score"),
        "risk_score": item.get("risk_score"),
        "confidence_score": item.get("confidence_score") or item.get("confidence"),
        "review_priority_score": item.get("review_priority_score") or item.get("opportunity_score"),
        "quality_tier": item.get("quality_tier"),
        "liquidity_tier": item.get("liquidity_tier"),
        "risk_tier": item.get("risk_tier"),
        "execution_readiness_tier": item.get("execution_readiness_tier"),
        "reason_codes": list(item.get("reason_codes") or item.get("top_reasons") or []),
        "missing_fields": list(item.get("missing_fields") or []),
        "outcome_status": item.get("outcome_status") or "pending",
        "final_outcome": item.get("final_outcome"),
        "settled_at": item.get("settled_at"),
        "final_price": item.get("final_price"),
        "return_pct": item.get("return_pct"),
        "source_module": source_module,
        "paper_only": True,
        "review_only": True,
        "simulation_only": True,
        "execution_allowed": False,
    }


def _finalize(record: dict[str, Any]) -> dict[str, Any]:
    scored = complete_institutional_scores(dict(record))
    safe = {field: scored.get(field) for field in NORMALIZED_RECORD_FIELDS}
    safe["reason_codes"] = [str(x) for x in (safe.get("reason_codes") or []) if x][:25]
    safe["missing_fields"] = [str(x) for x in (safe.get("missing_fields") or []) if x][:25]
    return safe


def normalize_prediction_market_record(item: dict[str, Any], *, source_module: str = "review_queue") -> dict[str, Any]:
    provider = str(item.get("provider") or item.get("provider_id") or "kalshi_prediction_market")
    row = _base_record(
        compact_redact(item),
        asset_class="prediction_market",
        provider=provider,
        market_type=str(item.get("market_type") or "prediction_market"),
        source_module=source_module,
    )
    yes_bid = item.get("yes_bid")
    yes_ask = item.get("yes_ask")
    observed_price = item.get("yes_price")
    if observed_price is None:
        observed_price = item.get("observed_price")
    if observed_price is None:
        observed_price = item.get("implied_probability")
    implied_probability = item.get("implied_probability")
    if implied_probability is None:
        implied_probability = item.get("yes_price")
    row.update(
        {
            "symbol_or_ticker": item.get("ticker") or item.get("market_id") or item.get("contract_id"),
            "observed_price": observed_price,
            "bid": yes_bid,
            "ask": yes_ask,
            "mid": _mid(yes_bid, yes_ask, observed_price),
            "spread": _spread(yes_bid, yes_ask, item.get("spread")),
            "implied_probability": implied_probability,
            "settlement_quality_score": item.get("settlement_quality_score"),
        }
    )
    if item.get("settlement_rule_status") in {"missing", "unknown", None}:
        row["reason_codes"].append("settlement_unknown")
    if item.get("yes_bid") is None or item.get("yes_ask") is None:
        row["reason_codes"].append("incomplete_bid_ask")
    return _finalize(row)


def normalize_sportsbook_record(item: dict[str, Any], *, source_module: str = "review_queue") -> dict[str, Any]:
    provider = str(item.get("provider") or item.get("provider_id") or item.get("book") or "sportsbook")
    odds = item.get("odds_or_price") or item.get("best_odds") or item.get("odds")
    row = _base_record(
        compact_redact(item),
        asset_class="sportsbook",
        provider=provider,
        market_type=str(item.get("market_type") or item.get("market") or "sportsbook_market"),
        source_module=source_module,
    )
    row.update(
        {
            "symbol_or_ticker": item.get("sport") or item.get("league") or item.get("event_id"),
            "observed_price": odds,
            "bid": item.get("bid"),
            "ask": item.get("ask"),
            "mid": item.get("mid") or odds,
            "spread": item.get("spread"),
            "volume": item.get("volume"),
            "book_count": item.get("book_count") or item.get("books_compared"),
            "edge": item.get("edge") or item.get("ev_percent") or item.get("estimated_roi_percent"),
        }
    )
    if not (item.get("book_count") or item.get("books_compared")):
        row["reason_codes"].append("low_book_count")
    return _finalize(row)


def normalize_stock_record(item: dict[str, Any], *, source_module: str = "stock_outputs") -> dict[str, Any]:
    provider = str(item.get("provider") or "stock_sidecar")
    bid = item.get("bid")
    ask = item.get("ask")
    observed = item.get("observed_price") or item.get("last_price") or item.get("current_price") or item.get("price")
    row = _base_record(
        compact_redact(item),
        asset_class="stock",
        provider=provider,
        market_type=str(item.get("market_type") or "equity"),
        source_module=source_module,
    )
    row.update(
        {
            "symbol_or_ticker": item.get("symbol_or_ticker") or item.get("ticker") or item.get("symbol"),
            "observed_price": observed,
            "bid": bid,
            "ask": ask,
            "mid": _mid(bid, ask, observed),
            "spread": _spread(bid, ask, item.get("spread")),
            "volume": item.get("volume") or item.get("current_volume"),
            "open_interest": item.get("open_interest"),
            "dollar_volume": item.get("dollar_volume") or item.get("average_dollar_volume"),
            "quick_ratio": item.get("quick_ratio"),
            "current_ratio": item.get("current_ratio"),
            "debt_to_cash": item.get("debt_to_cash"),
            "final_price": item.get("final_price"),
            "return_pct": item.get("return_pct"),
        }
    )
    if row.get("final_price") is not None and row.get("observed_price") is not None and row.get("return_pct") is None:
        observed_float = to_float(row["observed_price"])
        final_float = to_float(row["final_price"])
        if observed_float and final_float is not None:
            row["return_pct"] = round(((final_float - observed_float) / observed_float) * 100.0, 6)
    return _finalize(row)


def normalize_major_asset_record(
    item: dict[str, Any],
    *,
    asset_class: str = "major_asset",
    source_module: str = "major_asset_outputs",
) -> dict[str, Any]:
    if asset_class not in {"bond", "major_asset"}:
        asset_class = "major_asset"
    provider = str(item.get("provider") or f"{asset_class}_sidecar")
    bid = item.get("bid")
    ask = item.get("ask")
    observed = item.get("observed_price") or item.get("last_price") or item.get("price")
    row = _base_record(
        compact_redact(item),
        asset_class=asset_class,
        provider=provider,
        market_type=str(item.get("market_type") or asset_class),
        source_module=source_module,
    )
    row.update(
        {
            "symbol_or_ticker": item.get("symbol_or_ticker") or item.get("ticker") or item.get("symbol"),
            "observed_price": observed,
            "bid": bid,
            "ask": ask,
            "mid": _mid(bid, ask, observed),
            "spread": _spread(bid, ask, item.get("spread")),
            "volume": item.get("volume"),
            "dollar_volume": item.get("dollar_volume") or item.get("average_dollar_volume"),
            "final_price": item.get("final_price"),
            "return_pct": item.get("return_pct"),
            "risk_flags": list(item.get("risk_flags") or []),
        }
    )
    return _finalize(row)


def _outcome_index(outcomes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            continue
        for key in ("decision_id", "review_item_id", "contract_id", "ticker"):
            value = outcome.get(key)
            if value:
                indexed[f"{key}:{value}"] = outcome
    return indexed


def attach_explicit_outcome(record: dict[str, Any], outcome: dict[str, Any] | None) -> dict[str, Any]:
    if not outcome:
        return record
    status = str(outcome.get("outcome_status") or "").lower()
    final = outcome.get("final_outcome")
    if status in {"settled", "completed", "void", "cancelled"} and final is not None:
        out = dict(record)
        out["outcome_status"] = "completed" if status == "completed" else status
        out["final_outcome"] = final
        out["settled_at"] = outcome.get("settled_at")
        return out
    return record


def _matching_outcome(record: dict[str, Any], index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    candidates = (
        ("decision_id", record.get("source_record_id")),
        ("review_item_id", record.get("source_record_id")),
        ("contract_id", record.get("contract_id")),
        ("ticker", record.get("symbol_or_ticker")),
    )
    for key, value in candidates:
        if value and f"{key}:{value}" in index:
            return index[f"{key}:{value}"]
    return None


def _read_json_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [row for row in payload["items"] if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [row for row in payload["records"] if isinstance(row, dict)]
    return []


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except Exception:
        return []


def _read_optional_asset_rows(base_data_dir: str, names: tuple[str, ...]) -> list[dict[str, Any]]:
    root = resolve_base_data_dir(base_data_dir)
    rows: list[dict[str, Any]] = []
    for name in names:
        path = root / name
        if path.suffix.lower() == ".csv":
            rows.extend(_read_csv_rows(path))
        else:
            rows.extend(_read_json_rows(path))
    return rows


def read_existing_outputs(
    *,
    base_data_dir: str = "data",
    asset_classes: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    requested = {str(asset) for asset in (asset_classes or ASSET_CLASSES)}
    unknown = requested - set(ASSET_CLASSES)
    requested = requested & set(ASSET_CLASSES)
    outcomes = load_outcome_records(base_data_dir)
    outcome_by_key = _outcome_index(outcomes)
    records: list[dict[str, Any]] = []
    source_counts = {asset: 0 for asset in ASSET_CLASSES}
    unavailable: dict[str, str] = {}

    if {"prediction_market", "sportsbook"} & requested:
        queue_state = load_review_queue_state({"paths": {"review_queue": str(Path(base_data_dir) / "review_queue")}})
        source_rows: list[tuple[str, dict[str, Any]]] = []
        source_rows.extend(("review_queue", row) for row in queue_state.get("items", []) if isinstance(row, dict))
        source_rows.extend(("paper_ledger", row) for row in load_paper_decisions(base_data_dir) if isinstance(row, dict))
        for source_module, item in source_rows:
            market_type = str(item.get("market_type") or item.get("source_type") or "").lower()
            provider = str(item.get("provider") or item.get("provider_id") or "").lower()
            is_prediction = market_type == "prediction_market" or provider == "kalshi_prediction_market"
            if is_prediction and "prediction_market" in requested:
                record = normalize_prediction_market_record(item, source_module=source_module)
            elif not is_prediction and "sportsbook" in requested:
                record = normalize_sportsbook_record(item, source_module=source_module)
            else:
                continue
            record = attach_explicit_outcome(record, _matching_outcome(record, outcome_by_key))
            records.append(_finalize(record))
            source_counts[str(record["asset_class"])] += 1

    if "stock" in requested:
        stock_rows = _read_optional_asset_rows(
            base_data_dir,
            ("stock_outputs.json", "stocks.json", "stock_log.csv", "stock_outputs.csv"),
        )
        if not stock_rows:
            unavailable["stock"] = "no_stock_sidecar_outputs_found"
        for item in stock_rows:
            record = normalize_stock_record(item)
            records.append(record)
            source_counts["stock"] += 1

    if "bond" in requested or "major_asset" in requested:
        major_rows = _read_optional_asset_rows(
            base_data_dir,
            ("major_asset_outputs.json", "major_assets.json", "bond_outputs.json", "bond_assets.json"),
        )
        if not major_rows:
            if "bond" in requested:
                unavailable["bond"] = "no_bond_sidecar_outputs_found"
            if "major_asset" in requested:
                unavailable["major_asset"] = "no_major_asset_sidecar_outputs_found"
        for item in major_rows:
            asset_class = str(item.get("asset_class") or item.get("market_type") or "major_asset").lower()
            if asset_class not in {"bond", "major_asset"}:
                asset_class = "major_asset"
            if asset_class not in requested:
                continue
            record = normalize_major_asset_record(item, asset_class=asset_class)
            records.append(record)
            source_counts[asset_class] += 1

    deduped: dict[str, dict[str, Any]] = {}
    duplicate_records_skipped = 0
    for record in records:
        key = str(record.get("sidecar_id"))
        if key in deduped:
            duplicate_records_skipped += 1
            continue
        deduped[key] = record

    return {
        "records": list(deduped.values()),
        "records_read": len(records),
        "records_normalized": len(deduped),
        "duplicate_records_skipped": duplicate_records_skipped,
        "source_counts": source_counts,
        "unavailable": unavailable,
        "unknown_asset_classes": sorted(unknown),
        "outcome_records_count": len(outcomes),
    }
