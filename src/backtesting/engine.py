from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def _as_rows(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if rows is None:
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _normalize_outcome(value: Any) -> str | None:
    if value in (None, "", "void"):
        return None
    text = str(value).strip().lower()
    if text in {"1", "win", "winner", "true", "yes"}:
        return "win"
    if text in {"0", "loss", "lose", "false", "no"}:
        return "loss"
    if text in {"push", "tie", "draw"}:
        return "push"
    return text or None


def _score_probability(row: Mapping[str, Any], strategy_config: Mapping[str, Any] | None = None) -> float:
    config = dict(strategy_config or {})
    base = float(config.get("intercept", 0.5) or 0.5)
    features = dict(row.get("features") or {})
    feature_weights = dict(config.get("feature_weights") or {})
    sport_profiles = dict(config.get("sport_profiles") or {})
    profile_scope = str(config.get("profile_scope") or "auto")
    sport_key = str(row.get("sport") or row.get("league") or "").strip().lower()
    if profile_scope != "all_sports" and sport_key in sport_profiles:
        feature_weights = dict(sport_profiles[sport_key].get("feature_weights") or feature_weights)
        base = float(sport_profiles[sport_key].get("intercept", base) or base)
    adjustment = 0.0
    for feature_name, weight in feature_weights.items():
        try:
            adjustment += float(features.get(feature_name, 0.0)) * float(weight) / 100.0
        except (TypeError, ValueError):
            continue
    probability = max(0.0, min(1.0, base + adjustment))
    return round(probability, 2)


def run_backtesting_scaffold(rows: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    row_list = _as_rows(rows)
    total = len(row_list)
    settled_rows = [row for row in row_list if _normalize_outcome(row.get("final_outcome")) is not None]
    settled_count = len(settled_rows)
    provider_counts: dict[str, int] = {}
    for row in row_list:
        provider = str(row.get("provider") or "UNKNOWN").strip() or "UNKNOWN"
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
    if total == 0 or settled_count == 0:
        status = "insufficient_data"
        metrics: dict[str, Any] = {}
        insufficient_data = True
    elif settled_count < total:
        status = "partial_calibration"
        metrics = {}
        insufficient_data = False
    else:
        status = "metrics_ready"
        wins = sum(1 for row in settled_rows if _normalize_outcome(row.get("final_outcome")) == "win")
        losses = sum(1 for row in settled_rows if _normalize_outcome(row.get("final_outcome")) == "loss")
        pushes = sum(1 for row in settled_rows if _normalize_outcome(row.get("final_outcome")) == "push")
        metrics = {
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": round((wins / settled_count) * 100.0, 2) if settled_count else 0.0,
        }
        insufficient_data = False
    return {
        "ok": True,
        "status": status,
        "insufficient_data": insufficient_data,
        "settled_count": settled_count,
        "row_count": total,
        "group_counts": {"provider": provider_counts},
        "metrics": metrics,
        "rows": row_list,
    }


def load_historical_rows(source: str | Path | Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    if source is None:
        return []
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes, Path)):
        return _as_rows(source)
    if isinstance(source, str) and source.lower().startswith(("http://", "https://")):
        raise ValueError("historical replay only accepts local files or in-memory rows")
    path = Path(source)
    if not path.exists():
        return []
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, Mapping):
                rows.append(dict(payload))
        return rows
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, Mapping)]
    if isinstance(payload, Mapping):
        return [dict(payload)]
    return []


def replay_rows(rows: Sequence[Mapping[str, Any]], model_id: str = "historical_replay") -> dict[str, Any]:
    from src.backtesting.backtesting_engine import replay_rows as _legacy_replay_rows

    return _legacy_replay_rows([dict(row) for row in _as_rows(rows)], model_id=model_id)


def run_backtest(
    *,
    model_id: str,
    rows: Sequence[Mapping[str, Any]],
    base_data_dir: str | Path | None = None,
    strategy_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from src.backtesting.backtesting_engine import run_backtest as _legacy_run_backtest

    return _legacy_run_backtest(
        model_id=model_id,
        rows=[dict(row) for row in _as_rows(rows)],
        base_data_dir=str(base_data_dir or "data"),
        strategy_config=dict(strategy_config or {}) if strategy_config is not None else None,
    )


def generate_backtest_report(
    *,
    model_id: str,
    rows: Sequence[Mapping[str, Any]],
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    from src.backtesting.backtesting_engine import (
        generate_backtest_report as _legacy_generate_backtest_report,
    )

    return _legacy_generate_backtest_report(
        model_id=model_id,
        rows=[dict(row) for row in _as_rows(rows)],
        base_data_dir=str(base_data_dir or "data"),
    )


__all__ = [
    "generate_backtest_report",
    "load_historical_rows",
    "replay_rows",
    "run_backtest",
    "run_backtesting_scaffold",
]
