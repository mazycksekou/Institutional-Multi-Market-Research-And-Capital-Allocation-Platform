from __future__ import annotations

"""Canonical Phase 5.7 Research Intelligence snapshot."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.data.data_paths import get_runtime_data_path
from src.data.feature_registry import (
    DEFAULT_NFL_HISTORICAL_DATASET_ID,
)
from src.storage.local_store import LocalStorageEngine, create_local_storage_engine


RESEARCH_INTELLIGENCE_SCHEMA_VERSION = "src.market_intelligence.research_intelligence.v1"
RESEARCH_INTELLIGENCE_RUNTIME_VERSION = "phase5.7.research_intelligence.v1"
DEFAULT_RESEARCH_INTELLIGENCE_DATASET_ID = "dataset.sports.nfl.research_intelligence"
DEFAULT_RESEARCH_INTELLIGENCE_DATASET_NAME = "nfl_research_intelligence"
DEFAULT_RESEARCH_INTELLIGENCE_OWNER = "src.market_intelligence"
DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH = get_runtime_data_path(
    "baseline_backtesting",
    "canonical_data.sqlite",
)
DEFAULT_RESEARCH_INTELLIGENCE_MARKET = "sports:nfl"
DEFAULT_RESEARCH_INTELLIGENCE_MARKET_TYPE = "historical_research_intelligence"
RESEARCH_INTELLIGENCE_RUN_TABLE = "research_intelligence_runs"
RESEARCH_INTELLIGENCE_OPPORTUNITY_TABLE = "research_intelligence_opportunities"


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _normalize_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _normalize_text(value).lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return default


def _parse_iso(value: Any) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _to_iso8601_utc(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(_normalize_text(part) for part in (prefix, *parts))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _as_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, tuple):
            return list(obj)
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)

    return json.dumps(value, default=default, ensure_ascii=False, sort_keys=True)


def _load_json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): payload for key, payload in value.items()}
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return {str(key): payload for key, payload in parsed.items()}
    return {}


def _path_exists(path_value: Any) -> bool:
    path_text = _normalize_text(path_value)
    return bool(path_text) and Path(path_text).exists()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _resolve_artifact_root(storage_path: Path, artifact_root: str | Path | None) -> Path:
    if artifact_root is not None:
        root = Path(artifact_root).expanduser().resolve()
    else:
        root = storage_path.resolve().parent / "research_intelligence_artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _layer_timestamp(snapshot: Mapping[str, Any]) -> datetime | None:
    candidate_paths = (
        ("validation_timestamp",),
        ("created_at",),
        ("updated_at",),
        ("backtest_run_row", "created_at"),
        ("backtest_run_row", "updated_at"),
        ("decision_population_summary", "created_at"),
        ("signal_population_summary", "created_at"),
        ("math_engine_population_summary", "created_at"),
        ("feature_population_summary", "created_at"),
    )
    parsed: list[datetime] = []
    for path in candidate_paths:
        current: Any = snapshot
        for key in path:
            if not isinstance(current, Mapping):
                current = ""
                break
            current = current.get(key)
        value = _parse_iso(current)
        if value is not None:
            parsed.append(value)
    return max(parsed) if parsed else None


def _check(
    *,
    layer: str,
    category: str,
    check_id: str,
    ok: bool,
    expected: Any,
    actual: Any,
    details: str,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "layer": layer,
        "category": category,
        "check_id": check_id,
        "ok": bool(ok),
        "expected": expected,
        "actual": actual,
        "details": details,
        "severity": severity,
    }


def _feature_family(feature_id: str) -> str:
    text = _normalize_text(feature_id)
    prefix = "feature.sports.nfl."
    if text.startswith(prefix):
        text = text[len(prefix):]
    if "." not in text:
        return text or "unknown"
    token = text.split(".", 1)[0]
    return {
        "event": "event_context",
        "market": "market_context",
        "weather": "weather_context",
        "injury": "injury_context",
        "team_stats": "team_statistics_context",
        "data_quality": "data_quality_context",
    }.get(token, token or "unknown")


def _signal_family(signal_id: str) -> str:
    text = _normalize_text(signal_id)
    prefix = "signal.sports."
    if text.startswith(prefix):
        text = text[len(prefix):]
    if "." not in text:
        return text or "unknown"
    return text.split(".", 1)[0] or "unknown"


def _pricing_gap_bucket(pricing_gap: Any) -> str:
    gap = abs(_normalize_float(pricing_gap, 0.0))
    if gap >= 0.001:
        return "meaningful"
    if gap >= 0.00025:
        return "modest"
    if gap > 0:
        return "minimal"
    return "none"


def _feature_family_weight(family: str) -> int:
    return {
        "market_context": 4,
        "data_quality_context": 4,
        "injury_context": 2,
        "team_statistics_context": 2,
        "weather_context": 1,
        "event_context": 1,
    }.get(family, 0)


def _opportunity_sort_key(package: Mapping[str, Any]) -> tuple[float, float, float, str, str, str]:
    return (
        -_normalize_float(package.get("profit_loss_units"), 0.0),
        -_normalize_float(package.get("confidence_explanation", {}).get("confidence_score"), 0.0),
        -abs(_normalize_float(package.get("signal_agreement_summary", {}).get("pricing_gap"), 0.0)),
        _normalize_text(package.get("dataset_row_id")),
        _normalize_text(package.get("market_type")),
        _normalize_text(package.get("selection")),
    )


def _evidence_sort_key(package: Mapping[str, Any]) -> tuple[float, float, str, str, str]:
    return (
        -_normalize_float(package.get("confidence_explanation", {}).get("confidence_score"), 0.0),
        -abs(_normalize_float(package.get("signal_agreement_summary", {}).get("pricing_gap"), 0.0)),
        _normalize_text(package.get("dataset_row_id")),
        _normalize_text(package.get("market_type")),
        _normalize_text(package.get("selection")),
    )


def _summarize_bucket(bucket: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(bucket, Mapping):
        return {
            "label": "",
            "sample_size": 0,
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "profit_loss_units": 0.0,
            "roi_percent": 0.0,
        }
    return {
        "label": _normalize_text(bucket.get("label")),
        "sample_size": _normalize_int(bucket.get("sample_size"), 0),
        "wins": _normalize_int(bucket.get("wins"), 0),
        "losses": _normalize_int(bucket.get("losses"), 0),
        "pushes": _normalize_int(bucket.get("pushes"), 0),
        "profit_loss_units": _normalize_float(bucket.get("profit_loss_units"), 0.0),
        "roi_percent": _normalize_float(bucket.get("roi_percent"), 0.0),
    }


def _backtest_edge_bucket(pricing_gap: Any) -> str:
    gap = abs(_normalize_float(pricing_gap, 0.0))
    if gap < 0.01:
        return "0.000-0.010"
    if gap < 0.025:
        return "0.010-0.025"
    return "0.025+"


def _build_signal_agreement_summary(
    *,
    row: Mapping[str, Any],
    signal_values: Mapping[str, Any],
) -> dict[str, Any]:
    family_counts = Counter(_signal_family(signal_id) for signal_id in signal_values)
    confidence_score = _normalize_float(signal_values.get("signal.sports.data_quality.confidence_score"), 0.0)
    confidence_grade = _normalize_text(signal_values.get("signal.sports.data_quality.confidence_grade"))
    freshness_state = _normalize_text(signal_values.get("signal.sports.data_quality.freshness_state"), "missing")
    market_state = _normalize_text(signal_values.get("signal.sports.market.state"), "missing")
    regime_state = _normalize_text(signal_values.get("signal.sports.regime.state"), "missing")
    pricing_gap = _normalize_float(signal_values.get("signal.sports.market.pricing_gap"), 0.0)
    pricing_gap_bucket = _pricing_gap_bucket(pricing_gap)
    agreement_score = 0
    if confidence_score >= 0.72:
        agreement_score += 1
    if pricing_gap_bucket in {"modest", "meaningful"}:
        agreement_score += 1
    if market_state in {"supportive", "favorable"}:
        agreement_score += 1
    if freshness_state == "fresh":
        agreement_score += 1
    if regime_state in {"stable", "calm"}:
        agreement_score += 1
    if _normalize_text(row.get("decision_readiness_status")) != "BACKTEST_ELIGIBLE":
        agreement_state = "blocked"
    elif agreement_score >= 4:
        agreement_state = "aligned"
    elif agreement_score >= 2:
        agreement_state = "mixed"
    else:
        agreement_state = "constrained"
    notes = [
        f"confidence_grade={confidence_grade or 'missing'}",
        f"confidence_score={confidence_score:.4f}",
        f"pricing_gap_bucket={pricing_gap_bucket}",
        f"market_state={market_state or 'missing'}",
        f"regime_state={regime_state or 'missing'}",
        f"freshness_state={freshness_state}",
    ]
    return {
        "signal_count": len(signal_values),
        "family_counts": dict(sorted(family_counts.items())),
        "agreement_state": agreement_state,
        "agreement_score": agreement_score,
        "decision_readiness_status": _normalize_text(row.get("decision_readiness_status")),
        "confidence_score": confidence_score,
        "confidence_grade": confidence_grade,
        "freshness_state": freshness_state,
        "market_state": market_state,
        "regime_state": regime_state,
        "pricing_gap": pricing_gap,
        "pricing_gap_bucket": pricing_gap_bucket,
        "consensus_probability": _normalize_float(signal_values.get("signal.sports.market.consensus_probability"), 0.0),
        "fair_american_odds": _normalize_float(signal_values.get("signal.sports.market.fair_american_odds"), 0.0),
        "fair_decimal_odds": _normalize_float(signal_values.get("signal.sports.market.fair_decimal_odds"), 0.0),
        "agreement_notes": notes,
    }


def _build_feature_contribution_summary(feature_values: Mapping[str, Any]) -> dict[str, Any]:
    family_counts = Counter(_feature_family(feature_id) for feature_id in feature_values)
    freshness_seconds = {
        feature_id: _normalize_int(value, 0)
        for feature_id, value in feature_values.items()
        if feature_id.endswith("freshness_seconds")
    }
    point_in_time_safe = _normalize_bool(
        feature_values.get("feature.sports.nfl.data_quality.point_in_time_safe_flag")
    )
    predictor_outcome_separated = _normalize_bool(
        feature_values.get("feature.sports.nfl.data_quality.predictor_outcome_separated_flag")
    )
    decision_ready = _normalize_bool(
        feature_values.get("feature.sports.nfl.data_quality.decision_ready_flag")
    )
    missing_required_asset_count = _normalize_int(
        feature_values.get("feature.sports.nfl.data_quality.missing_required_asset_count"),
        0,
    )
    weighted_families = sorted(
        family_counts.items(),
        key=lambda item: (-_feature_family_weight(item[0]), -item[1], item[0]),
    )
    leading_families = [family for family, _ in weighted_families[:3]]
    if missing_required_asset_count == 0 and point_in_time_safe and predictor_outcome_separated and decision_ready:
        contribution_state = "complete"
    elif missing_required_asset_count == 0:
        contribution_state = "contextual"
    else:
        contribution_state = "partial"
    notes = [
        f"leading_families={','.join(leading_families) if leading_families else 'none'}",
        f"point_in_time_safe={point_in_time_safe}",
        f"predictor_outcome_separated={predictor_outcome_separated}",
        f"decision_ready={decision_ready}",
        f"missing_required_asset_count={missing_required_asset_count}",
    ]
    return {
        "feature_count": len(feature_values),
        "family_counts": dict(sorted(family_counts.items())),
        "leading_families": leading_families,
        "contribution_state": contribution_state,
        "point_in_time_safe_flag": point_in_time_safe,
        "predictor_outcome_separated_flag": predictor_outcome_separated,
        "decision_ready_flag": decision_ready,
        "missing_required_asset_count": missing_required_asset_count,
        "freshness_seconds": dict(sorted(freshness_seconds.items())),
        "contribution_notes": notes,
    }


def _build_confidence_explanation(
    *,
    row: Mapping[str, Any],
    signal_summary: Mapping[str, Any],
    feature_summary: Mapping[str, Any],
) -> dict[str, Any]:
    confidence_score = _normalize_float(signal_summary.get("confidence_score"), 0.0)
    confidence_grade = _normalize_text(signal_summary.get("confidence_grade"))
    freshness_state = _normalize_text(signal_summary.get("freshness_state"), "missing")
    market_state = _normalize_text(signal_summary.get("market_state"), "missing")
    regime_state = _normalize_text(signal_summary.get("regime_state"), "missing")
    pricing_gap_bucket = _normalize_text(signal_summary.get("pricing_gap_bucket"), "none")
    outcome_status = _normalize_text(row.get("outcome_status"))
    confidence_band = (
        "high"
        if confidence_score >= 0.85
        else "moderate"
        if confidence_score >= 0.70
        else "limited"
    )
    explanation = (
        f"Historical confidence was {confidence_band} because the certified signal score was "
        f"{confidence_score:.4f} (grade {confidence_grade or 'missing'}), pricing-gap evidence was "
        f"{pricing_gap_bucket}, freshness was {freshness_state}, market state was {market_state}, "
        f"and regime state was {regime_state}. The observed historical outcome was {outcome_status or 'missing'}."
    )
    factors = [
        f"confidence_band={confidence_band}",
        f"confidence_grade={confidence_grade or 'missing'}",
        f"pricing_gap_bucket={pricing_gap_bucket}",
        f"freshness_state={freshness_state}",
        f"market_state={market_state}",
        f"regime_state={regime_state}",
        f"feature_contribution_state={_normalize_text(feature_summary.get('contribution_state'), 'missing')}",
    ]
    return {
        "confidence_score": confidence_score,
        "confidence_grade": confidence_grade,
        "confidence_band": confidence_band,
        "freshness_state": freshness_state,
        "market_state": market_state,
        "regime_state": regime_state,
        "pricing_gap_bucket": pricing_gap_bucket,
        "explanation": explanation,
        "factors": factors,
    }


def _build_historical_comparison(
    *,
    row: Mapping[str, Any],
    backtest_report: Mapping[str, Any],
    benchmark_comparison: Mapping[str, Any],
) -> dict[str, Any]:
    season_key = str(_normalize_int(row.get("season"), 0))
    market_key = _normalize_text(row.get("market_type"))
    edge_key = _backtest_edge_bucket(row.get("pricing_gap"))
    market_bucket = _summarize_bucket((backtest_report.get("performance_by_market") or {}).get(market_key))
    season_bucket = _summarize_bucket((backtest_report.get("performance_by_season") or {}).get(season_key))
    edge_bucket = _summarize_bucket((backtest_report.get("performance_by_edge_bucket") or {}).get(edge_key))
    row_roi = _normalize_float(row.get("roi_percent"), 0.0)
    return {
        "market_bucket": market_bucket,
        "season_bucket": season_bucket,
        "edge_bucket": edge_bucket,
        "strategy_vs_benchmarks": dict(benchmark_comparison.get("strategy_vs_benchmarks") or {}),
        "row_vs_market_roi_delta": round(row_roi - _normalize_float(market_bucket.get("roi_percent"), 0.0), 6),
        "row_vs_edge_bucket_roi_delta": round(row_roi - _normalize_float(edge_bucket.get("roi_percent"), 0.0), 6),
    }


def _build_supporting_evidence_package(
    *,
    research_intelligence_run_id: str,
    backtest_run_id: str,
    pipeline_validation_run_id: str,
    row: Mapping[str, Any],
    certification_summary: Mapping[str, Any],
    backtest_report: Mapping[str, Any],
    benchmark_comparison: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _load_json_mapping(row.get("payload_json"))
    market_context = _load_json_mapping(payload.get("market_context"))
    decision_context = _load_json_mapping(market_context.get("decision_context"))
    signal_values = _load_json_mapping(payload.get("source_signal_values"))
    feature_values = _load_json_mapping(decision_context.get("source_feature_values"))
    math_values = _load_json_mapping(decision_context.get("source_math_values"))
    signal_summary = _build_signal_agreement_summary(row=row, signal_values=signal_values)
    feature_summary = _build_feature_contribution_summary(feature_values)
    confidence_explanation = _build_confidence_explanation(
        row=row,
        signal_summary=signal_summary,
        feature_summary=feature_summary,
    )
    historical_comparison = _build_historical_comparison(
        row=row,
        backtest_report=backtest_report,
        benchmark_comparison=benchmark_comparison,
    )
    opportunity_id = _stable_id(
        "research_opportunity",
        research_intelligence_run_id,
        row.get("backtest_row_id"),
        row.get("dataset_row_id"),
        row.get("market_type"),
        row.get("selection"),
    )
    evidence_package_id = _stable_id("research_evidence_package", opportunity_id, backtest_run_id)
    explanation = (
        f"{_normalize_text(row.get('market_type')).title()} {_normalize_text(row.get('selection'))} "
        f"finished as {_normalize_text(row.get('outcome_status'))} with "
        f"{_normalize_float(row.get('profit_loss_units'), 0.0):.2f} units. "
        f"{confidence_explanation['explanation']}"
    )
    return {
        "research_opportunity_id": opportunity_id,
        "evidence_package_id": evidence_package_id,
        "research_intelligence_run_id": research_intelligence_run_id,
        "pipeline_validation_run_id": pipeline_validation_run_id,
        "backtest_run_id": backtest_run_id,
        "decision_batch_id": _normalize_text(row.get("decision_batch_id")),
        "dataset_row_id": _normalize_text(row.get("dataset_row_id")),
        "event_id": _normalize_text(row.get("event_id")),
        "game_id": _normalize_text(row.get("game_id")),
        "season": _normalize_int(row.get("season"), 0),
        "week": _normalize_int(row.get("week"), 0),
        "market_type": _normalize_text(row.get("market_type")),
        "selection": _normalize_text(row.get("selection")),
        "book": _normalize_text(row.get("book")),
        "outcome_status": _normalize_text(row.get("outcome_status")),
        "profit_loss_units": _normalize_float(row.get("profit_loss_units"), 0.0),
        "roi_percent": _normalize_float(row.get("roi_percent"), 0.0),
        "market_implied_probability": _normalize_float(row.get("market_implied_probability"), 0.0),
        "consensus_probability": _normalize_float(row.get("consensus_probability"), 0.0),
        "pricing_gap": _normalize_float(row.get("pricing_gap"), 0.0),
        "confidence_explanation": confidence_explanation,
        "signal_agreement_summary": signal_summary,
        "feature_contribution_summary": feature_summary,
        "historical_comparison": historical_comparison,
        "supporting_evidence": {
            "source_dataset_snapshot_id": _normalize_text(row.get("source_dataset_snapshot_id")),
            "source_dataset_lineage_id": _normalize_text(row.get("source_dataset_lineage_id")),
            "source_decision_snapshot_id": _normalize_text(row.get("source_decision_snapshot_id")),
            "source_decision_context_id": _normalize_text(row.get("source_decision_context_id")),
            "source_signal_context_id": _normalize_text(row.get("source_signal_context_id")),
            "source_feature_batch_id": _normalize_text(decision_context.get("source_feature_batch_id")),
            "source_feature_population_summary_id": _normalize_text(decision_context.get("source_feature_population_summary_id")),
            "source_math_batch_id": _normalize_text(decision_context.get("source_math_batch_id")),
            "source_math_population_summary_id": _normalize_text(decision_context.get("source_math_population_summary_id")),
            "source_signal_batch_id": _normalize_text(decision_context.get("source_signal_batch_id")),
            "source_signal_population_summary_id": _normalize_text(decision_context.get("source_signal_population_summary_id")),
            "point_in_time_valid": _normalize_bool(row.get("point_in_time_valid")),
        },
        "certification_references": {
            "dataset_certification_id": _normalize_text(certification_summary.get("dataset_certification_id")),
            "feature_dataset_certification_id": _normalize_text(certification_summary.get("feature_dataset_certification_id")),
            "math_dataset_certification_id": _normalize_text(certification_summary.get("math_dataset_certification_id")),
            "signal_dataset_certification_id": _normalize_text(certification_summary.get("signal_dataset_certification_id")),
            "decision_dataset_certification_id": _normalize_text(certification_summary.get("decision_dataset_certification_id")),
            "backtest_source_decision_dataset_certification_id": _normalize_text(
                certification_summary.get("backtest_source_decision_dataset_certification_id")
            ),
        },
        "source_signal_values": dict(signal_values),
        "source_feature_values": dict(feature_values),
        "source_math_values": dict(math_values),
        "explanation": explanation,
    }


def _build_opportunity_summary(
    package: Mapping[str, Any],
    *,
    historical_rank: int,
    evidence_rank: int,
) -> dict[str, Any]:
    return {
        "research_opportunity_id": _normalize_text(package.get("research_opportunity_id")),
        "historical_rank": historical_rank,
        "evidence_rank": evidence_rank,
        "event_id": _normalize_text(package.get("event_id")),
        "game_id": _normalize_text(package.get("game_id")),
        "season": _normalize_int(package.get("season"), 0),
        "week": _normalize_int(package.get("week"), 0),
        "market_type": _normalize_text(package.get("market_type")),
        "selection": _normalize_text(package.get("selection")),
        "outcome_status": _normalize_text(package.get("outcome_status")),
        "profit_loss_units": _normalize_float(package.get("profit_loss_units"), 0.0),
        "roi_percent": _normalize_float(package.get("roi_percent"), 0.0),
        "confidence_score": _normalize_float(
            package.get("confidence_explanation", {}).get("confidence_score"),
            0.0,
        ),
        "confidence_grade": _normalize_text(
            package.get("confidence_explanation", {}).get("confidence_grade")
        ),
        "signal_agreement_state": _normalize_text(
            package.get("signal_agreement_summary", {}).get("agreement_state")
        ),
        "feature_contribution_state": _normalize_text(
            package.get("feature_contribution_summary", {}).get("contribution_state")
        ),
        "summary_text": _normalize_text(package.get("explanation")),
    }


def _build_research_summary(
    *,
    backtest_snapshot: Mapping[str, Any],
    packages: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    confidence_scores = [
        _normalize_float(package.get("confidence_explanation", {}).get("confidence_score"), 0.0)
        for package in packages
    ]
    pricing_gaps = [
        abs(_normalize_float(package.get("signal_agreement_summary", {}).get("pricing_gap"), 0.0))
        for package in packages
    ]
    summary_lines = [
        (
            f"Historical research covered {_normalize_int(backtest_snapshot.get('sample_size'), 0)} "
            f"certified opportunities with {_normalize_int(backtest_snapshot.get('wins'), 0)} wins, "
            f"{_normalize_int(backtest_snapshot.get('losses'), 0)} losses, "
            f"and {_normalize_float(backtest_snapshot.get('roi_percent'), 0.0):.1f}% ROI."
        ),
        (
            f"Average certified confidence score was "
            f"{(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0.0:.4f}, "
            f"and the largest observed pricing gap was {max(pricing_gaps) if pricing_gaps else 0.0:.6f}."
        ),
        (
            "Research Intelligence remains explanatory only: it summarizes historical evidence, "
            "does not generate new signals, and does not recommend execution."
        ),
    ]
    return {
        "sample_size": _normalize_int(backtest_snapshot.get("sample_size"), 0),
        "wins": _normalize_int(backtest_snapshot.get("wins"), 0),
        "losses": _normalize_int(backtest_snapshot.get("losses"), 0),
        "pushes": _normalize_int(backtest_snapshot.get("pushes"), 0),
        "profit_loss_units": _normalize_float(backtest_snapshot.get("profit_loss_units"), 0.0),
        "roi_percent": _normalize_float(backtest_snapshot.get("roi_percent"), 0.0),
        "average_confidence_score": round(
            (sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0.0,
            6,
        ),
        "max_pricing_gap": round(max(pricing_gaps) if pricing_gaps else 0.0, 6),
        "summary_lines": summary_lines,
    }


def _build_aggregated_signal_summary(packages: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    agreement_states = Counter(
        _normalize_text(package.get("signal_agreement_summary", {}).get("agreement_state"), "missing")
        for package in packages
    )
    market_states = Counter(
        _normalize_text(package.get("signal_agreement_summary", {}).get("market_state"), "missing")
        for package in packages
    )
    regime_states = Counter(
        _normalize_text(package.get("signal_agreement_summary", {}).get("regime_state"), "missing")
        for package in packages
    )
    freshness_states = Counter(
        _normalize_text(package.get("signal_agreement_summary", {}).get("freshness_state"), "missing")
        for package in packages
    )
    family_counts: Counter[str] = Counter()
    for package in packages:
        family_counts.update(
            {
                key: _normalize_int(value, 0)
                for key, value in (package.get("signal_agreement_summary", {}).get("family_counts") or {}).items()
            }
        )
    return {
        "agreement_state_counts": dict(sorted(agreement_states.items())),
        "market_state_counts": dict(sorted(market_states.items())),
        "regime_state_counts": dict(sorted(regime_states.items())),
        "freshness_state_counts": dict(sorted(freshness_states.items())),
        "family_counts": dict(sorted(family_counts.items())),
    }


def _build_aggregated_feature_summary(packages: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    contribution_states = Counter(
        _normalize_text(package.get("feature_contribution_summary", {}).get("contribution_state"), "missing")
        for package in packages
    )
    family_counts: Counter[str] = Counter()
    for package in packages:
        family_counts.update(
            {
                key: _normalize_int(value, 0)
                for key, value in (package.get("feature_contribution_summary", {}).get("family_counts") or {}).items()
            }
        )
    return {
        "contribution_state_counts": dict(sorted(contribution_states.items())),
        "family_counts": dict(sorted(family_counts.items())),
    }


def _build_evidence_aggregation_summary(
    *,
    packages: Sequence[Mapping[str, Any]],
    lineage_summary: Mapping[str, Any],
) -> dict[str, Any]:
    market_counts = Counter(_normalize_text(package.get("market_type"), "missing") for package in packages)
    outcome_counts = Counter(_normalize_text(package.get("outcome_status"), "missing") for package in packages)
    unique_events = sorted({_normalize_text(package.get("event_id")) for package in packages if _normalize_text(package.get("event_id"))})
    return {
        "opportunity_count": len(packages),
        "unique_event_count": len(unique_events),
        "unique_events": unique_events,
        "market_counts": dict(sorted(market_counts.items())),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "lineage_summary": dict(lineage_summary),
    }


def _build_dashboard_views(
    *,
    research_summary: Mapping[str, Any],
    opportunity_summaries: Sequence[Mapping[str, Any]],
    signal_summary: Mapping[str, Any],
    feature_summary: Mapping[str, Any],
    historical_comparison_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "summary_cards": {
            "sample_size": _normalize_int(research_summary.get("sample_size"), 0),
            "wins": _normalize_int(research_summary.get("wins"), 0),
            "losses": _normalize_int(research_summary.get("losses"), 0),
            "pushes": _normalize_int(research_summary.get("pushes"), 0),
            "profit_loss_units": _normalize_float(research_summary.get("profit_loss_units"), 0.0),
            "roi_percent": _normalize_float(research_summary.get("roi_percent"), 0.0),
            "average_confidence_score": _normalize_float(research_summary.get("average_confidence_score"), 0.0),
            "max_pricing_gap": _normalize_float(research_summary.get("max_pricing_gap"), 0.0),
        },
        "top_historical_opportunities": list(opportunity_summaries[:5]),
        "signal_agreement_breakdown": dict(signal_summary),
        "feature_contribution_breakdown": dict(feature_summary),
        "historical_comparison_summary": dict(historical_comparison_summary),
    }


def _write_artifacts(
    *,
    artifact_root: Path,
    research_intelligence_run_id: str,
    snapshot: Mapping[str, Any],
) -> dict[str, str]:
    run_root = artifact_root / research_intelligence_run_id
    run_root.mkdir(parents=True, exist_ok=True)
    report_json_path = run_root / "report.json"
    report_markdown_path = run_root / "summary.md"
    dashboard_json_path = run_root / "dashboard.json"
    report_payload = json.loads(_as_json(dict(snapshot)))
    dashboard_payload = {
        "research_intelligence_run_id": snapshot.get("research_intelligence_run_id"),
        "status": snapshot.get("status"),
        "readiness": snapshot.get("readiness"),
        "lifecycle_state": snapshot.get("lifecycle_state"),
        "validation_timestamp": snapshot.get("validation_timestamp"),
        "research_summary": snapshot.get("research_summary"),
        "dashboard_views": snapshot.get("dashboard_views"),
        "lineage_summary": snapshot.get("lineage_summary"),
        "certification_summary": snapshot.get("certification_summary"),
        "validation_summary": snapshot.get("validation_summary"),
    }
    top_opportunities = list(snapshot.get("opportunity_summaries") or [])[:3]
    markdown_lines = [
        f"# Phase 5.7 Research Intelligence `{research_intelligence_run_id}`",
        "",
        f"- Status: `{snapshot.get('status')}`",
        f"- Readiness: `{snapshot.get('readiness')}`",
        f"- Backtest run: `{snapshot.get('lineage_summary', {}).get('backtest_run_id', '')}`",
        f"- Pipeline validation run: `{snapshot.get('lineage_summary', {}).get('pipeline_validation_run_id', '')}`",
        f"- Sample size: `{snapshot.get('research_summary', {}).get('sample_size', 0)}`",
        f"- Wins / Losses / Pushes: `{snapshot.get('research_summary', {}).get('wins', 0)}` / `{snapshot.get('research_summary', {}).get('losses', 0)}` / `{snapshot.get('research_summary', {}).get('pushes', 0)}`",
        f"- ROI percent: `{snapshot.get('research_summary', {}).get('roi_percent', 0.0)}`",
        "",
        "## Summary",
    ]
    markdown_lines.extend(f"- {line}" for line in (snapshot.get("research_summary", {}).get("summary_lines") or []))
    if top_opportunities:
        markdown_lines.extend(["", "## Top Historical Opportunities"])
        for item in top_opportunities:
            markdown_lines.append(
                "- "
                f"`{item.get('market_type')}` / `{item.get('selection')}` / "
                f"`{item.get('outcome_status')}` / "
                f"`{item.get('profit_loss_units')}` units / "
                f"`{item.get('confidence_grade')}`"
            )
    _write_text(report_json_path, json.dumps(report_payload, indent=2, sort_keys=True) + "\n")
    _write_text(report_markdown_path, "\n".join(markdown_lines) + "\n")
    _write_text(dashboard_json_path, json.dumps(dashboard_payload, indent=2, sort_keys=True) + "\n")
    return {
        "artifact_root": str(run_root),
        "report_json_path": str(report_json_path),
        "report_markdown_path": str(report_markdown_path),
        "dashboard_json_path": str(dashboard_json_path),
    }


def _research_intelligence_missing_snapshot(
    *,
    storage: LocalStorageEngine,
    backtest_run_id: str,
    status: str,
    warnings: Sequence[str],
) -> dict[str, Any]:
    warning_list = [str(item) for item in warnings if str(item)]
    return {
        "ok": False,
        "status": status,
        "readiness": "blocked",
        "lifecycle_state": "missing",
        "schema_version": RESEARCH_INTELLIGENCE_SCHEMA_VERSION,
        "dataset_id": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_ID,
        "dataset_name": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_NAME,
        "research_intelligence_run_id": "",
        "research_intelligence_version": RESEARCH_INTELLIGENCE_RUNTIME_VERSION,
        "validation_timestamp": "",
        "validation_summary": {},
        "validation_checks": [],
        "lineage_summary": {
            "backtest_run_id": _normalize_text(backtest_run_id),
            "pipeline_validation_run_id": "",
        },
        "certification_summary": {},
        "evidence_aggregation_summary": {},
        "research_summary": {},
        "historical_comparison_summary": {},
        "signal_agreement_summary": {},
        "feature_contribution_summary": {},
        "confidence_explanations": [],
        "opportunity_summaries": [],
        "supporting_evidence_packages": [],
        "dashboard_views": {},
        "artifact_references": {},
        "artifact_integrity_ok": False,
        "storage": storage.health(),
        "warnings": warning_list,
        "unresolved_blockers": list(warning_list),
        "idempotent_reuse": False,
        "layer_snapshots": {},
    }


def build_research_intelligence_snapshot(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    backtest_run_id: str | None = None,
    artifact_root: str | Path | None = None,
    include_layer_snapshots: bool = True,
    persist_artifacts: bool = True,
) -> dict[str, Any]:
    from src.backtesting.baseline_backtesting import build_baseline_backtest_dashboard_snapshot
    from src.backtesting.decision_row_population import build_decision_row_population_dashboard_snapshot
    from src.backtesting.pipeline_validation import build_pipeline_validation_snapshot
    from src.data.feature_registry import build_feature_snapshot_population_dashboard_snapshot
    from src.data.historical_research_database import build_historical_dataset_population_dashboard_snapshot
    from src.data.math_engine_population import build_math_engine_population_dashboard_snapshot
    from src.market_intelligence.signal_population import get_signal_population_snapshot_for_dashboard

    storage = create_local_storage_engine(
        storage_path or DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH,
        backend=backend,
    )
    try:
        dataset_snapshot = build_historical_dataset_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            profile_id="sports:nfl",
            dataset_id=DEFAULT_NFL_HISTORICAL_DATASET_ID,
        )
        feature_snapshot = build_feature_snapshot_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            dataset_id=DEFAULT_NFL_HISTORICAL_DATASET_ID,
            include_source_dataset_snapshot=True,
        )
        math_snapshot = build_math_engine_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
        )
        signal_snapshot = get_signal_population_snapshot_for_dashboard(
            storage_path=storage.path,
            backend=backend,
        )
        decision_snapshot = build_decision_row_population_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
        )
        backtest_snapshot = build_baseline_backtest_dashboard_snapshot(
            storage_path=storage.path,
            backend=backend,
            backtest_run_id=backtest_run_id,
        )
        pipeline_validation_snapshot = build_pipeline_validation_snapshot(
            storage_path=storage.path,
            backend=backend,
            include_layer_snapshots=False,
            persist_artifacts=True,
        )
        if not backtest_snapshot.get("ok"):
            return _research_intelligence_missing_snapshot(
                storage=storage,
                backtest_run_id=_normalize_text(backtest_run_id),
                status="missing_backtest_surface",
                warnings=list(backtest_snapshot.get("warnings", [])) or ["completed baseline backtest is required"],
            )

        settled_rows = [
            dict(row)
            for row in (backtest_snapshot.get("settled_backtest_rows") or backtest_snapshot.get("backtest_rows") or [])
            if _normalize_text(row.get("outcome_status")) in {"win", "loss", "push"}
        ]
        if not settled_rows:
            return _research_intelligence_missing_snapshot(
                storage=storage,
                backtest_run_id=_normalize_text(backtest_snapshot.get("backtest_run_id")),
                status="missing_settled_backtest_rows",
                warnings=["settled baseline backtest rows are required"],
            )

        validation_timestamp = _to_iso8601_utc(
            _layer_timestamp(pipeline_validation_snapshot)
            or _layer_timestamp(backtest_snapshot)
            or _layer_timestamp(decision_snapshot)
            or _layer_timestamp(signal_snapshot)
            or _layer_timestamp(math_snapshot)
            or _layer_timestamp(feature_snapshot)
            or _layer_timestamp(dataset_snapshot)
        )
        research_intelligence_run_id = _stable_id(
            "research_intelligence",
            pipeline_validation_snapshot.get("pipeline_validation_run_id"),
            backtest_snapshot.get("backtest_run_id"),
            RESEARCH_INTELLIGENCE_RUNTIME_VERSION,
        )
        lineage_summary = {
            "dataset_batch_id": _normalize_text(dataset_snapshot.get("batch_id")),
            "feature_batch_id": _normalize_text(feature_snapshot.get("batch_id")),
            "math_batch_id": _normalize_text(math_snapshot.get("batch_id")),
            "signal_batch_id": _normalize_text(signal_snapshot.get("batch_id")),
            "decision_batch_id": _normalize_text(decision_snapshot.get("batch_id")),
            "backtest_run_id": _normalize_text(backtest_snapshot.get("backtest_run_id")),
            "pipeline_validation_run_id": _normalize_text(pipeline_validation_snapshot.get("pipeline_validation_run_id")),
        }
        certification_summary = {
            "dataset_certification_id": _normalize_text(dataset_snapshot.get("dataset_certification_id")),
            "feature_dataset_certification_id": _normalize_text(feature_snapshot.get("dataset_certification_id")),
            "math_dataset_certification_id": _normalize_text(math_snapshot.get("dataset_certification_id")),
            "signal_dataset_certification_id": _normalize_text(signal_snapshot.get("dataset_certification_id")),
            "decision_dataset_certification_id": _normalize_text(decision_snapshot.get("dataset_certification_id")),
            "backtest_source_decision_dataset_certification_id": _normalize_text(backtest_snapshot.get("dataset_certification_id")),
        }

        packages = [
            _build_supporting_evidence_package(
                research_intelligence_run_id=research_intelligence_run_id,
                backtest_run_id=_normalize_text(backtest_snapshot.get("backtest_run_id")),
                pipeline_validation_run_id=_normalize_text(pipeline_validation_snapshot.get("pipeline_validation_run_id")),
                row=row,
                certification_summary=certification_summary,
                backtest_report=dict(backtest_snapshot.get("backtest_report") or {}),
                benchmark_comparison=dict(backtest_snapshot.get("benchmark_comparison") or {}),
            )
            for row in settled_rows
        ]
        historical_sorted = sorted(packages, key=_opportunity_sort_key)
        evidence_sorted = sorted(packages, key=_evidence_sort_key)
        historical_rank_map = {
            _normalize_text(item.get("research_opportunity_id")): index
            for index, item in enumerate(historical_sorted, start=1)
        }
        evidence_rank_map = {
            _normalize_text(item.get("research_opportunity_id")): index
            for index, item in enumerate(evidence_sorted, start=1)
        }
        opportunity_summaries = [
            _build_opportunity_summary(
                package,
                historical_rank=historical_rank_map[_normalize_text(package.get("research_opportunity_id"))],
                evidence_rank=evidence_rank_map[_normalize_text(package.get("research_opportunity_id"))],
            )
            for package in historical_sorted
        ]
        research_summary = _build_research_summary(
            backtest_snapshot=backtest_snapshot,
            packages=historical_sorted,
        )
        signal_agreement_summary = _build_aggregated_signal_summary(historical_sorted)
        feature_contribution_summary = _build_aggregated_feature_summary(historical_sorted)
        confidence_explanations = [
            {
                "research_opportunity_id": _normalize_text(package.get("research_opportunity_id")),
                **dict(package.get("confidence_explanation") or {}),
            }
            for package in historical_sorted
        ]
        historical_comparison_summary = {
            "performance_by_market": dict((backtest_snapshot.get("backtest_report") or {}).get("performance_by_market") or {}),
            "performance_by_season": dict((backtest_snapshot.get("backtest_report") or {}).get("performance_by_season") or {}),
            "performance_by_edge_bucket": dict((backtest_snapshot.get("backtest_report") or {}).get("performance_by_edge_bucket") or {}),
            "benchmark_comparison": dict(backtest_snapshot.get("benchmark_comparison") or {}),
        }
        evidence_aggregation_summary = _build_evidence_aggregation_summary(
            packages=historical_sorted,
            lineage_summary=lineage_summary,
        )
        dashboard_views = _build_dashboard_views(
            research_summary=research_summary,
            opportunity_summaries=opportunity_summaries,
            signal_summary=signal_agreement_summary,
            feature_summary=feature_contribution_summary,
            historical_comparison_summary=historical_comparison_summary,
        )

        checks = [
            _check(
                layer="pipeline_validation",
                category="readiness",
                check_id="pipeline_validation_ready",
                ok=bool(pipeline_validation_snapshot.get("ok"))
                and pipeline_validation_snapshot.get("status") == "certified"
                and pipeline_validation_snapshot.get("readiness") == "research_intelligence_ready",
                expected="certified/research_intelligence_ready",
                actual=f"{pipeline_validation_snapshot.get('status')} / {pipeline_validation_snapshot.get('readiness')}",
                details="Research Intelligence requires a certified hardened pipeline.",
            ),
            _check(
                layer="dataset",
                category="status",
                check_id="dataset_ready",
                ok=dataset_snapshot.get("status") == "ready",
                expected="ready",
                actual=dataset_snapshot.get("status"),
                details="Historical dataset population must remain ready.",
            ),
            _check(
                layer="feature",
                category="status",
                check_id="feature_ready",
                ok=feature_snapshot.get("status") == "ready" and feature_snapshot.get("readiness") == "feature_ready",
                expected="ready/feature_ready",
                actual=f"{feature_snapshot.get('status')} / {feature_snapshot.get('readiness')}",
                details="Feature snapshot population must remain ready.",
            ),
            _check(
                layer="math",
                category="status",
                check_id="math_ready",
                ok=math_snapshot.get("status") == "ready" and math_snapshot.get("readiness") == "math_ready",
                expected="ready/math_ready",
                actual=f"{math_snapshot.get('status')} / {math_snapshot.get('readiness')}",
                details="Math engine population must remain ready.",
            ),
            _check(
                layer="signal",
                category="status",
                check_id="signal_certified",
                ok=signal_snapshot.get("status") == "certified" and signal_snapshot.get("readiness") == "signal_ready",
                expected="certified/signal_ready",
                actual=f"{signal_snapshot.get('status')} / {signal_snapshot.get('readiness')}",
                details="Signal population must remain certified.",
            ),
            _check(
                layer="decision",
                category="status",
                check_id="decision_certified",
                ok=decision_snapshot.get("status") == "certified" and decision_snapshot.get("readiness") == "backtest_ready",
                expected="certified/backtest_ready",
                actual=f"{decision_snapshot.get('status')} / {decision_snapshot.get('readiness')}",
                details="Decision row population must remain certified.",
            ),
            _check(
                layer="backtest",
                category="status",
                check_id="backtest_completed",
                ok=backtest_snapshot.get("status") == "completed" and backtest_snapshot.get("readiness") == "backtest_ready",
                expected="completed/backtest_ready",
                actual=f"{backtest_snapshot.get('status')} / {backtest_snapshot.get('readiness')}",
                details="Research Intelligence reads completed baseline backtests only.",
            ),
            _check(
                layer="backtest",
                category="replay",
                check_id="sample_size_matches_settled_rows",
                ok=len(settled_rows) == _normalize_int(backtest_snapshot.get("sample_size"), 0),
                expected=_normalize_int(backtest_snapshot.get("sample_size"), 0),
                actual=len(settled_rows),
                details="Settled backtest row count must equal backtest sample size.",
            ),
            _check(
                layer="backtest",
                category="replay",
                check_id="replayed_rows_only_consumed",
                ok=all(_normalize_text(row.get("replay_status")) == "replayed" for row in settled_rows),
                expected="replayed",
                actual=sorted({_normalize_text(row.get("replay_status")) for row in settled_rows}),
                details="Research Intelligence must read only replayed certified backtest rows.",
            ),
            _check(
                layer="chain",
                category="point_in_time",
                check_id="point_in_time_preserved",
                ok=all(_normalize_bool(row.get("point_in_time_valid")) for row in settled_rows),
                expected=True,
                actual=[_normalize_bool(row.get("point_in_time_valid")) for row in settled_rows],
                details="Every historical evidence package must remain point-in-time safe.",
            ),
            _check(
                layer="evidence",
                category="aggregation",
                check_id="evidence_package_count_matches_sample",
                ok=len(historical_sorted) == len(settled_rows),
                expected=len(settled_rows),
                actual=len(historical_sorted),
                details="Supporting evidence packages must cover every settled historical opportunity.",
            ),
            _check(
                layer="evidence",
                category="aggregation",
                check_id="opportunity_summary_count_matches_sample",
                ok=len(opportunity_summaries) == len(settled_rows),
                expected=len(settled_rows),
                actual=len(opportunity_summaries),
                details="Opportunity summaries must cover every settled historical opportunity.",
            ),
            _check(
                layer="evidence",
                category="provenance",
                check_id="evidence_rows_have_signal_and_feature_context",
                ok=all(
                    _normalize_int(package.get("signal_agreement_summary", {}).get("signal_count"), 0) > 0
                    and _normalize_int(package.get("feature_contribution_summary", {}).get("feature_count"), 0) > 0
                    for package in historical_sorted
                ),
                expected=True,
                actual=[
                    {
                        "research_opportunity_id": _normalize_text(package.get("research_opportunity_id")),
                        "signal_count": _normalize_int(package.get("signal_agreement_summary", {}).get("signal_count"), 0),
                        "feature_count": _normalize_int(package.get("feature_contribution_summary", {}).get("feature_count"), 0),
                    }
                    for package in historical_sorted
                ],
                details="Each evidence package must preserve signal and feature provenance.",
            ),
            _check(
                layer="dashboard",
                category="readiness",
                check_id="dashboard_view_count_matches_sample",
                ok=len(dashboard_views.get("top_historical_opportunities", [])) == len(opportunity_summaries),
                expected=len(opportunity_summaries),
                actual=len(dashboard_views.get("top_historical_opportunities", [])),
                details="Dashboard-ready opportunity view must preserve the queryable research opportunity set.",
            ),
            _check(
                layer="research_intelligence",
                category="sample",
                check_id="low_sample_warning_propagated",
                ok="low_sample_size" in list(backtest_snapshot.get("validation", {}).get("warnings", [])),
                expected=True,
                actual="low_sample_size" in list(backtest_snapshot.get("validation", {}).get("warnings", [])),
                details="Historical research output must preserve the explicit low-sample-size warning from backtesting.",
                severity="warning",
            ),
        ]

        unresolved_blockers = [
            f"{check['layer']}:{check['check_id']}"
            for check in checks
            if not check["ok"] and check["severity"] == "error"
        ]
        warnings = sorted(
            {
                str(item)
                for source in (
                    dataset_snapshot.get("warnings", []),
                    feature_snapshot.get("warnings", []),
                    math_snapshot.get("warnings", []),
                    signal_snapshot.get("warnings", []),
                    decision_snapshot.get("warnings", []),
                    backtest_snapshot.get("warnings", []),
                    pipeline_validation_snapshot.get("warnings", []),
                )
                for item in source
                if str(item)
            }
        )
        error_checks = [check for check in checks if check["severity"] == "error"]
        warning_checks = [check for check in checks if check["severity"] == "warning"]
        ok = not unresolved_blockers
        snapshot: dict[str, Any] = {
            "ok": ok,
            "status": "completed" if ok else "blocked",
            "readiness": "universal_market_framework_ready" if ok else "blocked",
            "lifecycle_state": "research_intelligence_ready" if ok else "blocked",
            "validation_state": "validated" if ok else "rejected",
            "schema_version": RESEARCH_INTELLIGENCE_SCHEMA_VERSION,
            "dataset_id": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_ID,
            "dataset_name": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_NAME,
            "research_intelligence_run_id": research_intelligence_run_id,
            "research_intelligence_version": RESEARCH_INTELLIGENCE_RUNTIME_VERSION,
            "validation_timestamp": validation_timestamp,
            "validation_summary": {
                "error_check_count": len(error_checks),
                "error_checks_passed": sum(1 for check in error_checks if check["ok"]),
                "warning_check_count": len(warning_checks),
                "warning_checks_passed": sum(1 for check in warning_checks if check["ok"]),
            },
            "validation_checks": checks,
            "lineage_summary": lineage_summary,
            "certification_summary": certification_summary,
            "evidence_aggregation_summary": evidence_aggregation_summary,
            "research_summary": research_summary,
            "historical_comparison_summary": historical_comparison_summary,
            "signal_agreement_summary": signal_agreement_summary,
            "feature_contribution_summary": feature_contribution_summary,
            "confidence_explanations": confidence_explanations,
            "opportunity_summaries": opportunity_summaries,
            "supporting_evidence_packages": historical_sorted,
            "dashboard_views": dashboard_views,
            "artifact_references": {},
            "artifact_integrity_ok": False,
            "storage": storage.health(),
            "warnings": warnings,
            "unresolved_blockers": unresolved_blockers,
            "idempotent_reuse": True,
            "layer_snapshots": {},
        }
        if include_layer_snapshots:
            snapshot["layer_snapshots"] = {
                "dataset": dataset_snapshot,
                "feature": feature_snapshot,
                "math": math_snapshot,
                "signal": signal_snapshot,
                "decision": decision_snapshot,
                "backtest": backtest_snapshot,
                "pipeline_validation": pipeline_validation_snapshot,
            }

        created_at = validation_timestamp or _normalize_text(
            backtest_snapshot.get("backtest_run_row", {}).get("created_at")
        )
        for package in historical_sorted:
            opportunity_row = {
                "research_opportunity_id": _normalize_text(package.get("research_opportunity_id")),
                "research_intelligence_run_id": research_intelligence_run_id,
                "evidence_package_id": _normalize_text(package.get("evidence_package_id")),
                "pipeline_validation_run_id": _normalize_text(lineage_summary.get("pipeline_validation_run_id")),
                "backtest_run_id": _normalize_text(lineage_summary.get("backtest_run_id")),
                "decision_batch_id": _normalize_text(package.get("decision_batch_id")),
                "dataset_id": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_ID,
                "dataset_name": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_NAME,
                "dataset_row_id": _normalize_text(package.get("dataset_row_id")),
                "event_id": _normalize_text(package.get("event_id")),
                "game_id": _normalize_text(package.get("game_id")),
                "season": _normalize_int(package.get("season"), 0),
                "week": _normalize_int(package.get("week"), 0),
                "market_type": _normalize_text(package.get("market_type")),
                "selection": _normalize_text(package.get("selection")),
                "outcome_status": _normalize_text(package.get("outcome_status")),
                "profit_loss_units": _normalize_float(package.get("profit_loss_units"), 0.0),
                "roi_percent": _normalize_float(package.get("roi_percent"), 0.0),
                "confidence_score": _normalize_float(package.get("confidence_explanation", {}).get("confidence_score"), 0.0),
                "confidence_grade": _normalize_text(package.get("confidence_explanation", {}).get("confidence_grade")),
                "signal_agreement_state": _normalize_text(package.get("signal_agreement_summary", {}).get("agreement_state")),
                "feature_contribution_state": _normalize_text(package.get("feature_contribution_summary", {}).get("contribution_state")),
                "market_implied_probability": _normalize_float(package.get("market_implied_probability"), 0.0),
                "consensus_probability": _normalize_float(package.get("consensus_probability"), 0.0),
                "pricing_gap": _normalize_float(package.get("pricing_gap"), 0.0),
                "historical_rank": historical_rank_map[_normalize_text(package.get("research_opportunity_id"))],
                "evidence_rank": evidence_rank_map[_normalize_text(package.get("research_opportunity_id"))],
                "payload_json": _as_json(package),
                "schema_version": RESEARCH_INTELLIGENCE_SCHEMA_VERSION,
                "created_at": created_at,
                "updated_at": created_at,
                "source": "baseline_backtest_rows",
                "provider": "repository",
                "market": DEFAULT_RESEARCH_INTELLIGENCE_MARKET,
                "market_type_classification": DEFAULT_RESEARCH_INTELLIGENCE_MARKET_TYPE,
                "asset_class": "research_intelligence",
                "snapshot_id": _normalize_text(package.get("research_opportunity_id")),
                "lineage_id": _stable_id(
                    "research_intelligence_opportunity_lineage",
                    research_intelligence_run_id,
                    package.get("research_opportunity_id"),
                    package.get("dataset_row_id"),
                ),
                "version_id": _stable_id(
                    "research_intelligence_opportunity_version",
                    research_intelligence_run_id,
                    package.get("research_opportunity_id"),
                    RESEARCH_INTELLIGENCE_RUNTIME_VERSION,
                ),
                "quality_score": 1.0
                if _normalize_bool(package.get("supporting_evidence", {}).get("point_in_time_valid"))
                else 0.0,
            }
            storage.upsert(RESEARCH_INTELLIGENCE_OPPORTUNITY_TABLE, opportunity_row, key_columns=("research_opportunity_id",))

        run_row = {
            "research_intelligence_run_id": research_intelligence_run_id,
            "dataset_id": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_ID,
            "dataset_name": DEFAULT_RESEARCH_INTELLIGENCE_DATASET_NAME,
            "owner": DEFAULT_RESEARCH_INTELLIGENCE_OWNER,
            "sport": "football",
            "feature_pack": "research_intelligence.sports.nfl",
            "storage_location": str(storage.path),
            "readiness": snapshot["readiness"],
            "update_frequency": "manual",
            "validation_state": snapshot["validation_state"],
            "status": snapshot["status"],
            "pipeline_validation_run_id": _normalize_text(lineage_summary.get("pipeline_validation_run_id")),
            "backtest_run_id": _normalize_text(lineage_summary.get("backtest_run_id")),
            "decision_batch_id": _normalize_text(lineage_summary.get("decision_batch_id")),
            "source_dataset_batch_id": _normalize_text(lineage_summary.get("dataset_batch_id")),
            "source_feature_batch_id": _normalize_text(lineage_summary.get("feature_batch_id")),
            "source_math_batch_id": _normalize_text(lineage_summary.get("math_batch_id")),
            "source_signal_batch_id": _normalize_text(lineage_summary.get("signal_batch_id")),
            "sample_size": _normalize_int(research_summary.get("sample_size"), 0),
            "wins": _normalize_int(research_summary.get("wins"), 0),
            "losses": _normalize_int(research_summary.get("losses"), 0),
            "pushes": _normalize_int(research_summary.get("pushes"), 0),
            "profit_loss_units": _normalize_float(research_summary.get("profit_loss_units"), 0.0),
            "roi_percent": _normalize_float(research_summary.get("roi_percent"), 0.0),
            "opportunity_count": len(opportunity_summaries),
            "results_json": _as_json(
                {
                    "research_summary": research_summary,
                    "historical_comparison_summary": historical_comparison_summary,
                    "signal_agreement_summary": signal_agreement_summary,
                    "feature_contribution_summary": feature_contribution_summary,
                    "confidence_explanations": confidence_explanations,
                    "opportunity_summaries": opportunity_summaries,
                    "supporting_evidence_packages": historical_sorted,
                    "dashboard_views": dashboard_views,
                    "validation_summary": snapshot["validation_summary"],
                    "validation_checks": checks,
                }
            ),
            "payload_json": _as_json(
                {
                    "research_intelligence_run_id": research_intelligence_run_id,
                    "validation_timestamp": validation_timestamp,
                    "lineage_summary": lineage_summary,
                    "certification_summary": certification_summary,
                    "evidence_aggregation_summary": evidence_aggregation_summary,
                }
            ),
            "schema_version": RESEARCH_INTELLIGENCE_SCHEMA_VERSION,
            "created_at": created_at,
            "updated_at": created_at,
            "source": "certified_pipeline_outputs",
            "provider": "repository",
            "market": DEFAULT_RESEARCH_INTELLIGENCE_MARKET,
            "market_type": DEFAULT_RESEARCH_INTELLIGENCE_MARKET_TYPE,
            "asset_class": "research_intelligence",
            "snapshot_id": research_intelligence_run_id,
            "lineage_id": _stable_id(
                "research_intelligence_run_lineage",
                research_intelligence_run_id,
                lineage_summary.get("pipeline_validation_run_id"),
                lineage_summary.get("backtest_run_id"),
            ),
            "version_id": _stable_id(
                "research_intelligence_run_version",
                research_intelligence_run_id,
                RESEARCH_INTELLIGENCE_RUNTIME_VERSION,
            ),
            "quality_score": 1.0 if ok else 0.0,
        }
        storage.upsert(RESEARCH_INTELLIGENCE_RUN_TABLE, run_row, key_columns=("research_intelligence_run_id",))

        if persist_artifacts:
            artifact_references = _write_artifacts(
                artifact_root=_resolve_artifact_root(storage.path, artifact_root),
                research_intelligence_run_id=research_intelligence_run_id,
                snapshot=snapshot,
            )
            snapshot["artifact_references"] = artifact_references
            snapshot["artifact_integrity_ok"] = all(
                _path_exists(path)
                for key, path in artifact_references.items()
                if key != "artifact_root"
            )
            run_row["artifact_root"] = artifact_references["artifact_root"]
            run_row["report_json_path"] = artifact_references["report_json_path"]
            run_row["report_markdown_path"] = artifact_references["report_markdown_path"]
            run_row["dashboard_json_path"] = artifact_references["dashboard_json_path"]
            run_row["results_json"] = _as_json(
                {
                    **_load_json_mapping(run_row.get("results_json")),
                    "artifact_references": artifact_references,
                }
            )
            run_row["payload_json"] = _as_json(
                {
                    **_load_json_mapping(run_row.get("payload_json")),
                    "artifact_integrity_ok": snapshot["artifact_integrity_ok"],
                }
            )
            storage.upsert(RESEARCH_INTELLIGENCE_RUN_TABLE, run_row, key_columns=("research_intelligence_run_id",))

        return snapshot
    finally:
        storage.close()


def get_research_intelligence_snapshot_for_dashboard(
    storage_path: str | Path | None = None,
    *,
    backend: str = "sqlite",
    backtest_run_id: str | None = None,
) -> dict[str, Any]:
    try:
        return build_research_intelligence_snapshot(
            storage_path=storage_path,
            backend=backend,
            backtest_run_id=backtest_run_id,
            include_layer_snapshots=True,
            persist_artifacts=True,
        )
    except Exception as exc:
        storage = create_local_storage_engine(
            storage_path or DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH,
            backend=backend,
        )
        try:
            return _research_intelligence_missing_snapshot(
                storage=storage,
                backtest_run_id=_normalize_text(backtest_run_id),
                status="research_intelligence_snapshot_error",
                warnings=[str(exc)],
            )
        finally:
            storage.close()


__all__ = [
    "DEFAULT_RESEARCH_INTELLIGENCE_DATASET_ID",
    "DEFAULT_RESEARCH_INTELLIGENCE_DATASET_NAME",
    "DEFAULT_RESEARCH_INTELLIGENCE_STORAGE_PATH",
    "RESEARCH_INTELLIGENCE_RUNTIME_VERSION",
    "RESEARCH_INTELLIGENCE_SCHEMA_VERSION",
    "build_research_intelligence_snapshot",
    "get_research_intelligence_snapshot_for_dashboard",
]
