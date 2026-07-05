from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.providers.policy.allowlist import classify_provider
from src.security.policy import locked_safety_flags


AUTOMATION_DATA_DIR_ENV = "AUTOMATION_DATA_DIR"
EXECUTION_ATTEMPT_BLOCKED = "execution_attempt_blocked"

_SECRET_KEYS = (
    "key",
    "secret",
    "token",
    "password",
    "auth",
    "credential",
    "signature",
    "header",
    "bearer",
    "cookie",
    "private",
)

_RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_sharp_payload",
    "raw_kalshi_payload",
    "raw_request_payload",
    "raw_response",
    "request_payload",
    "response_payload",
    "order_payload",
    "broker_order_payload",
    "sportsbook_bet_payload",
    "kalshi_order_payload",
    "crypto_trade_payload",
    "trade_payload",
    "execution_payload",
    "executable_order_payload",
    "bet_slip",
    "wager_payload",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _configured_root() -> Path | None:
    raw = os.getenv(AUTOMATION_DATA_DIR_ENV)
    if raw is None or not raw.strip():
        return None
    return Path(raw.strip()).expanduser()


def get_automation_data_dir() -> Path:
    root = _configured_root() or (_repo_root() / "data")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_base_data_dir(base_data_dir: str | Path | None = None) -> Path:
    if base_data_dir is None:
        return get_automation_data_dir()
    path = Path(base_data_dir).expanduser()
    if str(path).replace("\\", "/").rstrip("/") == "data":
        return get_automation_data_dir()
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_runtime_data_path(*parts: str | os.PathLike[str]) -> Path:
    root = get_automation_data_dir()
    path = root
    for part in parts:
        part_path = Path(part)
        if part_path.is_absolute():
            raise ValueError(f"runtime data path part must be relative: {part}")
        path = path / part_path
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    return resolved


def sanitize_filename(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
    return compact[:120] or "item"


def safe_run_id(namespace: str, seed: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{seed}").hex[:16]


def hash_payload(payload: Any) -> str:
    return hashlib.sha256(repr(redact_sensitive(payload)).encode("utf-8")).hexdigest()


def _looks_like_secret(value: str) -> bool:
    text = str(value or "")
    if not text.strip():
        return False
    lowered = text.lower()
    return any(fragment in lowered for fragment in ("sk-", "pk-", "bearer ", "token ", "private key"))


def redact_sensitive(payload: Any, *, list_limit: int = 100) -> Any:
    if isinstance(payload, Mapping):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            lower = str(key).strip().lower()
            if lower in _RAW_PAYLOAD_KEYS:
                out[str(key)] = "[omitted]"
            elif any(part in lower for part in _SECRET_KEYS):
                out[str(key)] = "[redacted]"
            else:
                out[str(key)] = redact_sensitive(value, list_limit=list_limit)
        return out
    if isinstance(payload, list):
        return [redact_sensitive(value, list_limit=list_limit) for value in payload[: max(1, int(list_limit or 100))]]
    if isinstance(payload, str) and _looks_like_secret(payload):
        return "[redacted]"
    return payload


def secret_safety_fields(*, source_payload: Any = None, redacted_payload: Any = None) -> dict[str, Any]:
    safe_payload = redacted_payload if redacted_payload is not None else redact_sensitive(source_payload)
    return {
        "secrets_detected": False,
        "raw_payload_exposed": False,
        "auth_header_exposed": False,
        "signature_exposed": False,
        "redaction_applied": True,
        "source_secret_like_content_redacted": bool(source_payload is not None and redact_sensitive(source_payload) != source_payload),
        "redacted_payload_contains_secret": bool(safe_payload is not None and safe_payload != redact_sensitive(safe_payload)),
    }


def compact_redact(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            lower = str(key).strip().lower()
            if lower in _RAW_PAYLOAD_KEYS or any(part in lower for part in _SECRET_KEYS):
                continue
            out[str(key)] = compact_redact(value)
        return out
    if isinstance(payload, list):
        return [compact_redact(item) for item in payload[:25]]
    return payload


CONTEXT_BUCKET_FIELDS = (
    "asset_type",
    "market_type",
    "provider",
    "sport",
    "league",
    "timeframe",
    "session",
    "time_of_day",
    "liquidity_tier",
    "volatility_regime",
    "manifold_cluster",
    "hidden_regime",
    "data_resolution",
    "latency_tier",
    "outcome_window",
    "catalyst_type",
    "balance_sheet_bucket",
    "incentive_bucket",
    "game_script_bucket",
)


def _norm(value: Any, default: str = "unknown") -> str:
    text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    return text or default


def context_key(bucket: Mapping[str, Any]) -> str:
    return "|".join(f"{field}={_norm(bucket.get(field))}" for field in CONTEXT_BUCKET_FIELDS)


def build_context_bucket(candidate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    candidate = compact_redact(dict(candidate or {}))
    bucket = {
        "asset_type": _norm(candidate.get("asset_type") or candidate.get("asset_class")),
        "market_type": _norm(candidate.get("market_type") or candidate.get("source_type")),
        "provider": _norm(candidate.get("provider") or candidate.get("provider_id")),
        "sport": _norm(candidate.get("sport")),
        "league": _norm(candidate.get("league")),
        "timeframe": _norm(candidate.get("timeframe")),
        "session": _norm(candidate.get("session") or candidate.get("session_time_bucket")),
        "time_of_day": _norm(candidate.get("time_of_day") or candidate.get("session_time_bucket")),
        "liquidity_tier": _norm(candidate.get("liquidity_tier")),
        "volatility_regime": _norm(candidate.get("volatility_regime")),
        "manifold_cluster": _norm(candidate.get("manifold_cluster_id") or candidate.get("manifold_cluster_name")),
        "hidden_regime": _norm(candidate.get("hidden_regime") or candidate.get("hmm_regime")),
        "data_resolution": _norm(candidate.get("data_resolution")),
        "latency_tier": _norm(candidate.get("latency_tier")),
        "outcome_window": _norm(candidate.get("outcome_window")),
        "catalyst_type": _norm(candidate.get("catalyst_type")),
        "balance_sheet_bucket": _norm(candidate.get("balance_sheet_bucket") or candidate.get("balance_sheet_risk_bucket")),
        "incentive_bucket": _norm(candidate.get("incentive_bucket")),
        "game_script_bucket": _norm(candidate.get("game_script_bucket")),
    }
    bucket["context_key"] = context_key(bucket)
    bucket.update(locked_safety_flags())
    return bucket


def normalize_event_type(event_type: str | None) -> str:
    value = str(event_type or "").strip().lower()
    return value or EXECUTION_ATTEMPT_BLOCKED


def evaluate_owner_approval(
    owner_approval: Mapping[str, Any] | None,
    *,
    requested_scope: Mapping[str, Any] | None = None,
    persist_audit: bool = False,
    base_data_dir: str | None = None,
    signing_secret: str | None = None,
    used_nonces: Sequence[str] | None = None,
    actor_type: str = "system",
) -> dict[str, Any]:
    from src.security.owner_approval_gate import evaluate_owner_approval as _canonical_evaluate_owner_approval

    return _canonical_evaluate_owner_approval(
        dict(owner_approval or {}),
        requested_scope=dict(requested_scope or {}),
        persist_audit=persist_audit,
        base_data_dir=base_data_dir,
        signing_secret=signing_secret,
        used_nonces=used_nonces,
        actor_type=actor_type,
    )


def evaluate_risk_limits(
    request: Mapping[str, Any] | None,
    *,
    risk_limits: Mapping[str, Any] | None = None,
    persist_audit: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.security.risk_limit_guard import evaluate_risk_limits as _canonical_evaluate_risk_limits

    return _canonical_evaluate_risk_limits(
        dict(request or {}),
        risk_limits=dict(risk_limits or {}),
        persist_audit=persist_audit,
        base_data_dir=base_data_dir,
    )


def _safe_num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_time_of_day(value: Any = None, *, minutes_since_midnight: int | None = None) -> dict[str, Any]:
    if minutes_since_midnight is not None:
        minutes = minutes_since_midnight
    else:
        minutes = None
        if isinstance(value, datetime):
            minutes = value.hour * 60 + value.minute
        elif isinstance(value, str) and value.strip():
            text = value.strip().replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(text)
                minutes = parsed.hour * 60 + parsed.minute
            except ValueError:
                minutes = None
    bucket = "DATA_INSUFFICIENT"
    if minutes is not None:
        market_open = 9 * 60 + 30
        if minutes < market_open:
            bucket = "PREMARKET"
        elif minutes < 10 * 60:
            bucket = "OPENING_DRIVE"
        elif minutes < 11 * 60:
            bucket = "MORNING_MOMENTUM"
        elif minutes < 14 * 60:
            bucket = "MIDDAY_CHOP"
        elif minutes < 15 * 60 + 30:
            bucket = "AFTERNOON_RECLAIM"
        elif minutes < 16 * 60:
            bucket = "POWER_HOUR"
        else:
            bucket = "AFTER_HOURS"
    base_scores = {
        "PREMARKET": 55.0,
        "OPENING_DRIVE": 92.0,
        "MORNING_MOMENTUM": 84.0,
        "MIDDAY_CHOP": 42.0,
        "AFTERNOON_RECLAIM": 62.0,
        "POWER_HOUR": 74.0,
        "AFTER_HOURS": 34.0,
        "DATA_INSUFFICIENT": 45.0,
    }
    score = base_scores[bucket]
    return {
        "session_time_bucket": bucket,
        "time_of_day_edge_score": score,
        "session_quality_score": score,
        "calibration_bucket_required": True,
    }


def evaluate_session_risk(session: Mapping[str, Any] | None) -> dict[str, Any]:
    session = dict(session or {})
    session_profit = _safe_num(session.get("session_profit"))
    peak_session_profit = _safe_num(session.get("peak_session_profit"), session_profit)
    consecutive_loss_count = int(_safe_num(session.get("consecutive_loss_count"), 0.0))
    max_consecutive_losses = int(_safe_num(session.get("max_consecutive_losses"), 3.0))
    daily_giveback_limit_percent = _safe_num(session.get("daily_giveback_limit_percent"), 20.0)
    idle_minutes = _safe_num(session.get("idle_time_without_a_quality_setup_minutes"), 0.0)
    max_idle_minutes = _safe_num(session.get("max_idle_minutes"), 60.0)
    giveback_percent = 0.0
    if peak_session_profit > 0 and session_profit < peak_session_profit:
        giveback_percent = (peak_session_profit - session_profit) / peak_session_profit * 100.0
    reasons: list[str] = []
    status = "ALLOW_REVIEW"
    kill_switch = False
    overtrading_risk = 0.0
    if giveback_percent >= daily_giveback_limit_percent:
        status = "NO_TRADE_SESSION_LOCK"
        kill_switch = True
        reasons.append("daily_giveback_limit_reached")
    if consecutive_loss_count >= max_consecutive_losses:
        status = "COOLDOWN" if not kill_switch else status
        kill_switch = True
        overtrading_risk += 35.0
        reasons.append("max_consecutive_losses_reached")
    if idle_minutes >= max_idle_minutes:
        if status == "ALLOW_REVIEW":
            status = "REDUCE_PRIORITY"
        overtrading_risk += 25.0
        reasons.append("idle_without_a_quality_setup")
    if session_profit > 0 and giveback_percent > 0:
        overtrading_risk += min(25.0, giveback_percent)
    session_risk_score = max(0.0, 100.0 - overtrading_risk - (60.0 if kill_switch else 0.0))
    return {
        "session_profit": session_profit,
        "peak_session_profit": peak_session_profit,
        "giveback_percent": round(giveback_percent, 4),
        "daily_giveback_limit_percent": daily_giveback_limit_percent,
        "consecutive_loss_count": consecutive_loss_count,
        "max_consecutive_losses": max_consecutive_losses,
        "idle_time_without_a_quality_setup_minutes": idle_minutes,
        "max_idle_minutes": max_idle_minutes,
        "profit_protection_mode": bool(peak_session_profit > 0 and session_profit < peak_session_profit),
        "overtrading_risk": round(min(100.0, overtrading_risk), 2),
        "session_kill_switch_active": kill_switch,
        "session_permission_status": status,
        "session_risk_score": round(session_risk_score, 2),
        "walk_away_reasons": sorted(set(reasons)),
    }


def calculate_float_rotation(daily_volume: Any, float_shares: Any) -> float | None:
    volume = _safe_num(daily_volume)
    float_value = _safe_num(float_shares)
    if float_value <= 0:
        return None
    return round(volume / float_value, 4)


def score_liquidity_context(row: Mapping[str, Any], asset_type: str | None = None) -> dict[str, Any]:
    row = dict(row or {})
    spread = _safe_num(row.get("spread"), 0.0)
    volume = _safe_num(row.get("volume"), 0.0)
    rotation = calculate_float_rotation(row.get("daily_volume") or volume, row.get("float_shares"))
    liquidity_score = 50.0
    if volume > 0:
        liquidity_score += min(30.0, volume / 1000.0)
    if spread:
        liquidity_score -= min(20.0, abs(spread) * 10.0)
    if rotation is not None:
        liquidity_score += min(10.0, rotation * 5.0)
    liquidity_score = max(0.0, min(100.0, liquidity_score))
    return {
        "asset_type": asset_type or row.get("asset_type"),
        "liquidity_score": round(liquidity_score, 2),
        "liquidity_tier": "high" if liquidity_score >= 70 else "medium" if liquidity_score >= 40 else "low",
        "spread_slippage_score": round(max(0.0, 100.0 - abs(spread) * 10.0), 2),
        "float_rotation": rotation,
        "liquidity_zones": [row.get("support"), row.get("resistance")],
        "liquidity_blockers": [] if liquidity_score >= 40 else ["liquidity_score_below_40"],
    }


def evaluate_balance_sheet(row: Mapping[str, Any] | None) -> dict[str, Any]:
    from src.core.balance_sheet_risk import evaluate_balance_sheet as legacy_evaluate_balance_sheet

    return legacy_evaluate_balance_sheet(dict(row or {}))


def detect_candlestick_patterns(candles: Sequence[Mapping[str, Any]] | None, context: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    from src.market_intelligence.candlestick_pattern_detector import (
        detect_candlestick_patterns as legacy_detect_candlestick_patterns,
    )

    legacy_candles = [dict(candle) for candle in candles or [] if isinstance(candle, Mapping)]
    return legacy_detect_candlestick_patterns(legacy_candles, dict(context or {}))


def build_calibration_by_asset_class(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    asset_counts: dict[str, int] = {}
    statuses: dict[str, int] = {}
    total = 0
    for record in records:
        if not isinstance(record, Mapping):
            continue
        total += 1
        asset = str(record.get("asset_class") or record.get("asset_type") or "unknown").lower()
        asset_counts[asset] = asset_counts.get(asset, 0) + 1
        status = str(record.get("calibration_status") or record.get("status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    calibration_status = "not_ready" if total < 5 else "partial_calibration" if total < 20 else "calibration_ready"
    return {
        "ok": True,
        "status": calibration_status,
        "calibration_status": calibration_status,
        "records_count": total,
        "calibration_by_asset_class": dict(sorted(asset_counts.items())),
        "calibration_status_counts": dict(sorted(statuses.items())),
    }


RISK_CATEGORIES = (
    "market_risk",
    "liquidity_risk",
    "model_risk",
    "operational_risk",
    "settlement_risk",
    "execution_risk",
    "compliance_policy_risk",
)

SUPPORTED_INSTITUTIONAL_PROVIDERS = {
    "kalshi_prediction_market",
    "sharp_sportsbook",
    "sportsbook",
    "stock_sidecar",
    "bond_sidecar",
    "major_asset_sidecar",
}

SUPPORTED_INSTITUTIONAL_ASSET_CLASSES = {"prediction_market", "stock", "bond", "major_asset", "sportsbook"}


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _risk_tier_local(score: float) -> str:
    if score >= 80.0:
        return "high_fragility"
    if score >= 60.0:
        return "elevated"
    if score >= 40.0:
        return "moderate"
    return "low"


def assess_institutional_risk(candidate: Mapping[str, Any], *, calibration_report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    candidate = dict(candidate or {})
    calibration_report = dict(calibration_report or {})
    limits = {}
    blocks: list[str] = []
    warnings: list[str] = []
    categories = {category: [] for category in RISK_CATEGORIES}

    asset_class = str(candidate.get("asset_class") or "unknown")
    provider = str(candidate.get("provider") or "unknown")

    if asset_class not in SUPPORTED_INSTITUTIONAL_ASSET_CLASSES:
        _append_unique(blocks, "unsupported_asset_class")
        categories["compliance_policy_risk"].append("unsupported_asset_class")
    if provider not in SUPPORTED_INSTITUTIONAL_PROVIDERS:
        _append_unique(blocks, "unsupported_provider")
        categories["compliance_policy_risk"].append("unsupported_provider")

    liquidity_raw = candidate.get("liquidity_score")
    pricing_raw = candidate.get("pricing_quality_score")
    structure_raw = candidate.get("market_structure_score")
    confidence_raw = candidate.get("confidence_score")
    settlement_raw = candidate.get("settlement_quality_score")
    risk_raw = candidate.get("risk_score")

    liquidity = None if liquidity_raw in (None, "") else _safe_num(liquidity_raw)
    pricing = None if pricing_raw in (None, "") else _safe_num(pricing_raw)
    structure = None if structure_raw in (None, "") else _safe_num(structure_raw)
    confidence = None if confidence_raw in (None, "") else _safe_num(confidence_raw)
    settlement = None if settlement_raw in (None, "") else _safe_num(settlement_raw)
    risk = None if risk_raw in (None, "") else _safe_num(risk_raw)

    if liquidity is None:
        _append_unique(blocks, "missing_liquidity")
        categories["liquidity_risk"].append("missing_liquidity")
    elif liquidity < float(limits.get("min_liquidity_score", 45.0)):
        _append_unique(blocks, "low_liquidity")
        categories["liquidity_risk"].append("low_liquidity")

    if pricing is None:
        _append_unique(blocks, "missing_quote")
        categories["execution_risk"].append("missing_quote")
    elif pricing < float(limits.get("min_pricing_quality_score", 45.0)):
        _append_unique(blocks, "low_pricing_quality")
        categories["execution_risk"].append("low_pricing_quality")

    if structure is None or structure < float(limits.get("min_market_structure_score", 45.0)):
        _append_unique(blocks, "weak_market_structure")
        categories["market_risk"].append("weak_market_structure")

    if confidence is None:
        _append_unique(blocks, "missing_confidence")
        categories["model_risk"].append("missing_confidence")
    elif confidence < float(limits.get("min_confidence_score", 45.0)):
        _append_unique(blocks, "low_confidence")
        categories["model_risk"].append("low_confidence")

    if settlement is None or settlement < 50.0:
        _append_unique(blocks, "missing_outcome_path")
        categories["settlement_risk"].append("missing_outcome_path")

    if risk is not None and _risk_tier_local(risk) == "high_fragility":
        _append_unique(blocks, "high_risk_tier")
        categories["market_risk"].append("high_fragility")

    for reason in candidate.get("reason_codes") or []:
        text = str(reason)
        if text in {"stale_price", "stale_line", "missing_timestamp"}:
            _append_unique(blocks, "stale_price")
            categories["operational_risk"].append(text)
        elif text in {"settlement_unknown", "ambiguous_contract"}:
            _append_unique(blocks, "settlement_ambiguity")
            categories["settlement_risk"].append(text)
        elif text in {"wide_spread", "extreme_spread", "inverted_quote"}:
            categories["execution_risk"].append(text)
            warnings.append(text)
        elif text in {"insufficient_calibration_sample", "missing_edge"}:
            categories["model_risk"].append(text)
            warnings.append(text)

    asset_calibration = None
    if calibration_report and isinstance(calibration_report.get("asset_classes"), dict):
        asset_calibration = calibration_report["asset_classes"].get(asset_class)
    elif calibration_report and calibration_report.get("asset_class") == asset_class:
        asset_calibration = calibration_report
    matched = int((asset_calibration or {}).get("matched_outcomes_count", 0) or 0)
    if matched < int(limits.get("min_calibration_sample", 30)):
        _append_unique(blocks, "insufficient_calibration_sample")
        categories["model_risk"].append("insufficient_calibration_sample")

    score_components = [
        100.0 - (liquidity if liquidity is not None else 20.0),
        100.0 - (pricing if pricing is not None else 20.0),
        100.0 - (structure if structure is not None else 45.0),
        100.0 - (confidence if confidence is not None else 30.0),
        risk if risk is not None else 70.0,
    ]
    risk_score = _clamp_score(sum(score_components) / len(score_components) + min(25.0, len(blocks) * 4.0))
    tier = _risk_tier_local(risk_score)
    return {
        "ok": not blocks,
        "status": "risk_review_pass" if not blocks else "risk_review_blocked",
        "risk_score": round(risk_score, 2),
        "risk_tier": tier,
        "risk_label": "low" if risk_score < 35 else "medium" if risk_score < 65 else "high",
        "risk_blocks": blocks,
        "risk_blockers": list(blocks),
        "risk_categories": categories,
        "execution_blocked": True,
        "block_reason": "simulation_only",
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "weighted_score": round(100.0 - (risk_score / 2.0), 2),
        "calibration_support_score": round(float(matched), 2),
        "liquidity_risk_score": round(float(liquidity or 0.0), 2),
        "trap_risk_score": round(float(0.0), 2),
        "warnings": sorted(set(warnings)),
        **locked_safety_flags(),
    }


def _pattern_queue_root(base_data_dir: str | None = None) -> Path:
    root = resolve_base_data_dir(base_data_dir) / "small_account_review" / "pattern_review_queue"
    root.mkdir(parents=True, exist_ok=True)
    return root


def calculate_review_priority_score(**scores: Any) -> float:
    total = 0.0
    weight = 0.0
    for key, factor in (
        ("pattern_quality_score", 0.16),
        ("liquidity_score", 0.16),
        ("volume_confirmation_score", 0.10),
        ("catalyst_score", 0.10),
        ("time_of_day_score", 0.10),
        ("risk_reward_score", 0.10),
        ("balance_sheet_quality_score", 0.08),
        ("historical_calibration_score", 0.05),
        ("micro_calibration_score", 0.05),
        ("trade_window_calibration_score", 0.05),
        ("spread_slippage_score", 0.03),
        ("session_risk_score", 0.02),
    ):
        value = _safe_num(scores.get(key), 50.0)
        total += value * factor
        weight += factor
    return round(max(0.0, min(100.0, total / weight if weight else 0.0)), 2)


def queue_status_for_score(score: Any) -> str:
    parsed = _safe_num(score)
    if parsed >= 85:
        return "ACTIVE_REVIEW"
    if parsed >= 70:
        return "WATCHLIST_REVIEW"
    if parsed >= 55:
        return "LOW_PRIORITY_REVIEW"
    return "NO_REVIEW"


def build_pattern_review_item(
    *,
    detection: Mapping[str, Any],
    liquidity: Mapping[str, Any],
    catalyst: Mapping[str, Any],
    time_context: Mapping[str, Any],
    risk_reward: Mapping[str, Any],
    balance_sheet: Mapping[str, Any],
    price_band: Mapping[str, Any],
    session_risk: Mapping[str, Any],
    quality: Mapping[str, Any] | None = None,
    historical_calibration_score: Any = None,
    micro_calibration_score: Any = None,
    trade_window_calibration_score: Any = None,
    special_catalyst: bool = False,
) -> dict[str, Any]:
    quality = dict(quality or {})
    liquidity_score = _safe_num(liquidity.get("liquidity_score"))
    balance_quality = _safe_num(balance_sheet.get("balance_sheet_quality_score"), 50.0)
    catalyst_score = _safe_num(catalyst.get("catalyst_quality_score"))
    priority = calculate_review_priority_score(
        pattern_quality_score=detection.get("pattern_quality_score"),
        liquidity_score=liquidity_score,
        volume_confirmation_score=detection.get("volume_confirmation_score"),
        catalyst_score=catalyst_score,
        time_of_day_score=time_context.get("time_of_day_edge_score"),
        risk_reward_score=risk_reward.get("risk_reward_score"),
        balance_sheet_quality_score=balance_quality,
        historical_calibration_score=historical_calibration_score,
        micro_calibration_score=micro_calibration_score,
        trade_window_calibration_score=trade_window_calibration_score,
        spread_slippage_score=liquidity.get("spread_slippage_score"),
        session_risk_score=session_risk.get("session_risk_score"),
    )
    no_trade_reasons: list[str] = []
    review_reasons: list[str] = []
    warnings: list[str] = []
    if detection:
        review_reasons.append("pattern_detected")
    if liquidity_score >= 40:
        review_reasons.append("liquidity_confirmed")
    if risk_reward.get("risk_reward_permission_status") in {"VALID", "REVIEW_ALLOWED_WITH_CAUTION"}:
        review_reasons.append("risk_reward_valid")
    if catalyst.get("catalyst_detected"):
        review_reasons.append("catalyst_context_present")
    if session_risk.get("session_permission_status") == "NO_TRADE_SESSION_LOCK":
        no_trade_reasons.extend(session_risk.get("walk_away_reasons") or ["session_locked"])
        status = "NO_TRADE_SESSION_LOCK"
    elif liquidity_score < 40 and not special_catalyst:
        no_trade_reasons.extend(liquidity.get("liquidity_blockers") or ["liquidity_score_below_40"])
        status = "NO_TRADE"
    else:
        status = queue_status_for_score(priority)
    if special_catalyst and liquidity_score < 40:
        warnings.append("special_catalyst_with_low_liquidity_requires_explicit_risk_review")
        priority = min(priority, 69.0)
        if status not in {"NO_TRADE_SESSION_LOCK"}:
            status = "LOW_PRIORITY_REVIEW"
    if risk_reward.get("risk_reward_permission_status") in {"BLOCKED", "DATA_INSUFFICIENT"}:
        no_trade_reasons.extend(risk_reward.get("risk_reward_blockers") or ["risk_reward_invalid"])
        if status not in {"NO_TRADE_SESSION_LOCK", "NO_TRADE"}:
            status = "DATA_INSUFFICIENT" if risk_reward.get("risk_reward_permission_status") == "DATA_INSUFFICIENT" else "NO_REVIEW"
    if balance_sheet.get("data_insufficient"):
        warnings.append("balance_sheet_data_insufficient")
    if balance_sheet.get("force_status") == "NO_REVIEW":
        no_trade_reasons.extend(balance_sheet.get("risk_blockers") or ["balance_sheet_extreme_risk"])
        if status not in {"NO_TRADE_SESSION_LOCK", "NO_TRADE"}:
            status = "NO_REVIEW"
    elif balance_sheet.get("force_status") == "HIGH_RISK_REVIEW":
        warnings.append("balance_sheet_high_risk_review")
        priority = min(priority, 69.0)
        if status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}:
            status = "LOW_PRIORITY_REVIEW"
    if price_band.get("no_review_reasons"):
        warnings.extend(price_band.get("no_review_reasons") or [])
        if price_band.get("price_band") == "below_2_caution" and status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}:
            status = "LOW_PRIORITY_REVIEW"
            priority = min(priority, 69.0)
    if time_context.get("session_time_bucket") == "MIDDAY_CHOP" and liquidity_score < 65:
        warnings.append("midday_weak_volume_watchlist_only")
        if status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}:
            status = "LOW_PRIORITY_REVIEW"
            priority = min(priority, 69.0)
    symbol = str(detection.get("asset_symbol") or "UNKNOWN").upper()
    item_id = safe_run_id("pattern_review_queue", f"{symbol}|{detection.get('detection_id')}|{detection.get('pattern_id')}|{detection.get('detected_at')}")
    return {
        "schema_version": "src.services.runtime_shared.pattern_review_queue.v1",
        "id": item_id,
        "detection_id": detection.get("detection_id"),
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "asset_symbol": symbol,
        "asset_type": detection.get("asset_type"),
        "timeframe": detection.get("timeframe"),
        "pattern_id": detection.get("pattern_id"),
        "pattern_name": detection.get("pattern_name"),
        "pattern_family": detection.get("pattern_family"),
        "direction": detection.get("direction"),
        "detected_at": detection.get("detected_at"),
        "queue_status": status,
        "review_priority_score": round(priority, 2),
        "liquidity_score": liquidity.get("liquidity_score"),
        "liquidity_tier": liquidity.get("liquidity_tier"),
        "pattern_quality_score": detection.get("pattern_quality_score"),
        "volume_confirmation_score": detection.get("volume_confirmation_score"),
        "breakout_confirmation_score": detection.get("breakout_confirmation_score"),
        "catalyst_score": catalyst_score,
        "catalyst_detected": bool(catalyst.get("catalyst_detected", False)),
        "catalyst_type": catalyst.get("catalyst_type"),
        "time_of_day_score": time_context.get("time_of_day_edge_score"),
        "session_time_bucket": time_context.get("session_time_bucket"),
        "risk_reward_score": risk_reward.get("risk_reward_score"),
        "risk_reward_ratio": risk_reward.get("reward_risk_ratio"),
        "breakeven_win_rate": risk_reward.get("breakeven_win_rate"),
        "balance_sheet_quality_score": balance_sheet.get("balance_sheet_quality_score"),
        "balance_sheet_risk_score": balance_sheet.get("fundamental_risk_score"),
        "balance_sheet_risk_bucket": balance_sheet.get("balance_sheet_risk_bucket"),
        "historical_calibration_score": historical_calibration_score,
        "micro_calibration_score": micro_calibration_score,
        "trade_window_calibration_score": trade_window_calibration_score,
        "spread_slippage_score": liquidity.get("spread_slippage_score"),
        "session_risk_score": session_risk.get("session_risk_score"),
        "entry_trigger_price": detection.get("entry_trigger_price"),
        "stop_loss_level": detection.get("stop_loss_level"),
        "target_price": detection.get("target_price"),
        "time_of_day_label": time_context.get("time_of_day_label"),
        "risk_reward_permission_status": risk_reward.get("risk_reward_permission_status"),
        "no_trade_reasons": no_trade_reasons,
        "review_reasons": review_reasons,
        "warnings": warnings,
        "special_catalyst": special_catalyst,
        "quality": quality,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        **locked_safety_flags(),
    }


def summarize_pattern_review_queue(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    from src.analytics.pattern_review_queue import (
        summarize_pattern_review_queue as legacy_summarize_pattern_review_queue,
    )

    return legacy_summarize_pattern_review_queue([dict(item) for item in items if isinstance(item, Mapping)])


def persist_pattern_review_queue(items: Sequence[Mapping[str, Any]], *, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.analytics.pattern_review_queue import (
        persist_pattern_review_queue as legacy_persist_pattern_review_queue,
    )

    return legacy_persist_pattern_review_queue(
        [dict(item) for item in items if isinstance(item, Mapping)],
        base_data_dir=base_data_dir,
    )


def get_storage_health() -> dict[str, Any]:
    root = get_automation_data_dir()
    probe = root / ".automation_data_dir_probe"
    read_ok = False
    write_ok = False
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        write_ok = True
        read_ok = probe.read_text(encoding="utf-8") == "ok"
    except Exception:
        read_ok = False
        write_ok = False
    finally:
        try:
            probe.unlink()
        except Exception:
            pass
    return {
        "env_var": AUTOMATION_DATA_DIR_ENV,
        "data_dir": str(root),
        "backend": "file",
        "configured": _configured_root() is not None,
        "render_persistent_disk_expected": False,
        "persistence_warning": None,
        "read_ok": bool(read_ok),
        "write_ok": bool(write_ok),
    }


def read_existing_outputs(*, base_data_dir: str | None = None, asset_classes: Sequence[str] | None = None, limit: int = 200) -> dict[str, Any]:
    from src.providers.institutional_cross_asset_adapters import (
        read_existing_outputs as legacy_read_existing_outputs,
    )

    return legacy_read_existing_outputs(
        base_data_dir=base_data_dir,
        asset_classes=asset_classes,
    )


__all__ = [
    "AUTOMATION_DATA_DIR_ENV",
    "EXECUTION_ATTEMPT_BLOCKED",
    "build_calibration_by_asset_class",
    "build_context_bucket",
    "build_pattern_review_item",
    "calculate_float_rotation",
    "calculate_review_priority_score",
    "classify_provider",
    "compact_redact",
    "context_key",
    "detect_candlestick_patterns",
    "evaluate_balance_sheet",
    "evaluate_owner_approval",
    "evaluate_risk_limits",
    "evaluate_session_risk",
    "get_automation_data_dir",
    "get_storage_health",
    "get_runtime_data_path",
    "hash_payload",
    "locked_safety_flags",
    "normalize_event_type",
    "persist_pattern_review_queue",
    "queue_status_for_score",
    "read_existing_outputs",
    "redact_sensitive",
    "resolve_base_data_dir",
    "safe_run_id",
    "sanitize_filename",
    "score_liquidity_context",
    "score_time_of_day",
    "secret_safety_fields",
    "summarize_pattern_review_queue",
    "utc_now_iso",
]
