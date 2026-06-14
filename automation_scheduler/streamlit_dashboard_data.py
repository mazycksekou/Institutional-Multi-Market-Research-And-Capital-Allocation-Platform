"""Streamlit dashboard data helpers.

Pure Python helper layer for the local operator dashboard.

Rules:
- Streamlit UI must stay thin.
- Betting/backtest logic stays in canonical repo modules.
- This module can be tested without Streamlit installed.
- Missing dashboard files are handled safely and can be generated on demand.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
import datetime
import json
import math
import subprocess

from .historical_data_sources import get_historical_data_source_rows
from .historical_odds_sqlite import (
    connect_historical_odds_db,
    initialize_historical_odds_db,
    import_historical_odds_file_to_sqlite,
    query_historical_odds_rows,
    summarize_historical_odds_db,
    validate_sqlite_store,
)
from .historical_backtest_bridge import (
    run_sqlite_historical_backtest,
    summarize_sqlite_historical_backtest,
    get_sqlite_backtest_filter_options,
)

from .backtest_dataset_builder import (
    build_canonical_backtest_dataset,
    load_canonical_backtest_dataset,
    summarize_canonical_dataset_report,
)
from .backtest_strategy_profiles import (
    describe_regression_profiles,
    infer_strategy_profile_key_from_row,
    normalize_strategy_profile_key,
)
from .backtesting_engine import run_backtest


DEFAULT_DASHBOARD_JSON_PATH = Path("data/backtests/dashboard/latest_dashboard.json")
DEFAULT_DASHBOARD_MARKDOWN_PATH = Path("data/backtests/dashboard/latest_dashboard.md")
DEFAULT_CANONICAL_JSONL_PATH = Path("data/backtests/canonical/latest.jsonl")
DEFAULT_CANONICAL_SCHEMA_PATH = Path("data/backtests/canonical/schema_report.json")
DEFAULT_PAPER_LEDGER_PATH = Path("data/paper_ledger/latest.json")
DEFAULT_REVIEW_QUEUE_PATH = Path("data/review_queue/latest.json")
DEFAULT_REVIEW_QUEUE_FULL_PATH = Path("data/review_queue/review_queue.json")
DEFAULT_SYSTEM_HEALTH_PATH = Path("data/system_health/health.json")


DATA_LIBRARY_PATHS: dict[str, Path] = {
    "Dashboard JSON": DEFAULT_DASHBOARD_JSON_PATH,
    "Dashboard Markdown": DEFAULT_DASHBOARD_MARKDOWN_PATH,
    "Canonical Dataset JSONL": DEFAULT_CANONICAL_JSONL_PATH,
    "Canonical Schema Report": DEFAULT_CANONICAL_SCHEMA_PATH,
    "Paper Ledger Latest": DEFAULT_PAPER_LEDGER_PATH,
    "Review Queue Latest": DEFAULT_REVIEW_QUEUE_PATH,
    "Review Queue Full": DEFAULT_REVIEW_QUEUE_FULL_PATH,
    "System Health": DEFAULT_SYSTEM_HEALTH_PATH,
}

DEFAULT_HISTORICAL_SQLITE_PATH = Path("data/historical/historical_odds.db")
DEFAULT_HISTORICAL_UPLOAD_DIR = Path("data/historical/uploads")
HISTORICAL_SQLITE_UI_VERSION = "10H8"


EASY_LABELS: dict[str, str] = {
    "bankroll": "Portfolio Value",
    "bankroll_curve": "Line that shows portfolio value going up or down",
    "starting_bankroll": "Starting Portfolio",
    "ending_bankroll": "Current Portfolio",
    "current_bankroll": "Current Portfolio",
    "unit_size": "Normal bet size",
    "stake": "Bet amount",
    "profit_loss": "Net Result",
    "pnl": "Net Result",
    "bets": "Decisions",
    "no_bets": "Skipped Decisions",
    "roi_percent": "Return percent",
    "max_drawdown_percent": "Worst drop percent",
    "drawdown": "How far the portfolio dropped from the high point",
    "model_probability": "Model chance",
    "market_implied_probability": "Market chance",
    "edge": "Model advantage",
    "clv": "Closing line value",
    "closing_line": "Final market price",
    "sport": "Sport",
    "league": "League",
    "market": "Bet type",
    "odds": "Odds",
    "profile": "Model profile",
    "profile_name": "Model profile",
    "selected_profile_key": "Selected model profile",
    "features_known_at_decision_time": "Info known before the bet",
    "final_result": "Final result",
    "regression tactic": "A way to turn features into a model chance",
    "all_sports": "One model setup for every sport",
    "sport_specific": "A model setup picked for one sport",
    "feature_weights": "Numbers that tell the model what matters more",
    "intercept": "Starting chance before features move it",
    "probability_floor": "Lowest chance allowed",
    "probability_ceiling": "Highest chance allowed",
    "override_existing_probability": "Let this tactic replace the old model chance",
}


SAFE_DEFAULTS: dict[str, Any] = {
    "starting_bankroll": 1000.0,
    "unit_size": 10.0,
    "max_rows": 2000,
    "minimum_edge": 0.0,
    "minimum_model_probability": 0.0,
    "probability_floor": 0.01,
    "probability_ceiling": 0.99,
    "intercept": 0.5,
    "override_existing_probability": True,
    "require_core_fields": False,
    "force_rebuild_dataset": False,
}


RISK_PRESETS: dict[str, dict[str, Any]] = {
    "Tiny Risk Demo": {
        "unit_size_percent": 0.25,
        "max_stake_percent": 0.5,
        "max_drawdown_stop_percent": 5.0,
        "explanation": "Tiny bets. Easy to watch. Very slow swings.",
    },
    "Conservative": {
        "unit_size_percent": 1.0,
        "max_stake_percent": 2.0,
        "max_drawdown_stop_percent": 10.0,
        "explanation": "Small bets. Good for learning and paper testing.",
    },
    "Moderate": {
        "unit_size_percent": 2.0,
        "max_stake_percent": 4.0,
        "max_drawdown_stop_percent": 15.0,
        "explanation": "Bigger swings. Only for stronger evidence.",
    },
    "Aggressive paper only": {
        "unit_size_percent": 5.0,
        "max_stake_percent": 8.0,
        "max_drawdown_stop_percent": 25.0,
        "explanation": "Big swings. Paper testing only.",
    },
    "Custom": {
        "unit_size_percent": None,
        "max_stake_percent": None,
        "max_drawdown_stop_percent": None,
        "explanation": "You choose the numbers.",
    },
}


REGRESSION_TACTICS: dict[str, dict[str, Any]] = {
    "Use existing model probability": {
        "mode": "existing_probability",
        "friendly": "Use the chance already in the data.",
    },
    "All-sports regression": {
        "mode": "sport_profiles",
        "profile_scope": "all_sports",
        "friendly": "Use one simple tactic for every sport.",
    },
    "Sport-specific regression": {
        "mode": "sport_profiles",
        "profile_scope": "auto",
        "friendly": "Pick the tactic that matches the sport.",
    },
    "Custom feature weights": {
        "mode": "sport_profiles",
        "profile_scope": "custom",
        "friendly": "Let the user type feature weights.",
    },
}


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def read_text_if_exists(path: str | Path, *, max_chars: int | None = None) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""

    text = file_path.read_text(encoding="utf-8", errors="replace")
    if max_chars is not None and max_chars >= 0:
        return text[:max_chars]
    return text


def load_json_if_exists(path: str | Path, *, default: Any = None) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default

    try:
        return json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return default


def write_json(path: str | Path, payload: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl_rows(path: str | Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    file_path = Path(path)
    rows: list[dict[str, Any]] = []

    if not file_path.exists():
        return rows

    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
            if limit is not None and len(rows) >= limit:
                break

    return rows


def file_inventory() -> list[dict[str, Any]]:
    rows = []
    for label, path in DATA_LIBRARY_PATHS.items():
        exists = path.exists()
        rows.append(
            {
                "label": label,
                "path": str(path),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "kind": path.suffix.lower().lstrip("."),
            }
        )
    return rows


def flatten_preview_rows(value: Any, *, limit: int = 200) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if isinstance(value, list):
        for idx, item in enumerate(value[:limit]):
            if isinstance(item, Mapping):
                row = {"_index": idx}
                row.update(dict(item))
                rows.append(row)
            else:
                rows.append({"_index": idx, "value": item})
        return rows

    if isinstance(value, Mapping):
        for key in ("items", "rows", "decisions", "paper_decisions", "review_queue", "records", "data"):
            nested = value.get(key)
            if isinstance(nested, list):
                return flatten_preview_rows(nested, limit=limit)

        for idx, (key, item) in enumerate(list(value.items())[:limit]):
            if isinstance(item, Mapping):
                row = {"_key": key}
                row.update(dict(item))
                rows.append(row)
            else:
                rows.append({"_key": key, "value": item})
        return rows

    if value is not None:
        rows.append({"value": value})

    return rows


def preview_path(path: str | Path, *, limit: int = 200) -> dict[str, Any]:
    file_path = Path(path)

    result = {
        "path": str(file_path),
        "exists": file_path.exists(),
        "kind": file_path.suffix.lower().lstrip("."),
        "rows": [],
        "raw": None,
        "text": "",
        "warning": "",
    }

    if not file_path.exists():
        result["warning"] = "File is missing. Use Generate Latest Dashboard if this is a dashboard file."
        return result

    suffix = file_path.suffix.lower()

    if suffix == ".jsonl":
        rows = read_jsonl_rows(file_path, limit=limit)
        result["rows"] = rows
        result["raw"] = rows[: min(limit, 20)]
        return result

    if suffix == ".json":
        payload = load_json_if_exists(file_path, default={})
        result["raw"] = payload
        result["rows"] = flatten_preview_rows(payload, limit=limit)
        return result

    if suffix == ".md":
        text = read_text_if_exists(file_path, max_chars=300_000)
        result["text"] = text
        result["raw"] = {"text": text[:5000]}
        return result

    text = read_text_if_exists(file_path, max_chars=300_000)
    result["text"] = text
    result["raw"] = {"text": text[:5000]}
    return result


def compact_counts(rows: Sequence[Mapping[str, Any]], key: str, *, limit: int = 50) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if value in (None, ""):
            value = "UNKNOWN"
        counter[str(value)] += 1
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def get_available_profile_options() -> list[dict[str, Any]]:
    description = describe_regression_profiles()
    sport_profiles = dict(description.get("sport_profiles") or {})

    options = [
        {
            "label": "All sports current formation",
            "value": "all_sports",
            "scope": "all_sports",
        }
    ]

    for key, value in sorted(sport_profiles.items()):
        label = str(value.get("display_name") or value.get("profile_name") or key)
        options.append(
            {
                "label": label,
                "value": key,
                "scope": "sport_specific",
            }
        )

    return options


def parse_feature_weights(text: str | None) -> dict[str, float]:
    if not text:
        return {}

    text = text.strip()
    if not text:
        return {}

    try:
        parsed = json.loads(text)
        if isinstance(parsed, Mapping):
            return {str(key): to_float(value) for key, value in parsed.items()}
    except json.JSONDecodeError:
        pass

    weights: dict[str, float] = {}
    for chunk in text.replace("\n", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            key, value = chunk.split("=", 1)
        elif ":" in chunk:
            key, value = chunk.split(":", 1)
        else:
            continue
        key = key.strip()
        if key:
            weights[key] = to_float(value)

    return weights


def build_strategy_config(
    *,
    tactic: str,
    profile_key: str | None = None,
    intercept: float = 0.5,
    feature_weights: Mapping[str, float] | None = None,
    probability_floor: float = 0.01,
    probability_ceiling: float = 0.99,
    override_existing_probability: bool = True,
) -> dict[str, Any] | None:
    tactic_info = REGRESSION_TACTICS.get(tactic) or REGRESSION_TACTICS["Sport-specific regression"]

    if tactic_info["mode"] == "existing_probability":
        return None

    normalized_profile = normalize_strategy_profile_key(profile_key)
    weights = {str(key): to_float(value) for key, value in dict(feature_weights or {}).items()}

    base_profile = {
        "intercept": to_float(intercept, 0.5),
        "feature_weights": weights,
        "probability_floor": to_float(probability_floor, 0.01),
        "probability_ceiling": to_float(probability_ceiling, 0.99),
        "override_existing_probability": bool(override_existing_probability),
    }

    profile_scope = tactic_info.get("profile_scope", "auto")

    if profile_scope == "all_sports":
        return {
            "mode": "sport_profiles",
            "profile_scope": "all_sports",
            "all_sports_profile": dict(base_profile),
            "sport_profiles": {},
        }

    if profile_scope == "custom":
        if normalized_profile and normalized_profile != "all_sports":
            return {
                "mode": "sport_profiles",
                "profile_scope": "auto",
                "all_sports_profile": dict(base_profile),
                "sport_profiles": {normalized_profile: dict(base_profile)},
            }

        return {
            "mode": "sport_profiles",
            "profile_scope": "all_sports",
            "all_sports_profile": dict(base_profile),
            "sport_profiles": {},
        }

    return {
        "mode": "sport_profiles",
        "profile_scope": "auto",
        "all_sports_profile": dict(base_profile),
        "sport_profiles": {
            normalized_profile: dict(base_profile)
        } if normalized_profile and normalized_profile != "all_sports" else {},
    }


def ensure_canonical_dataset(
    *,
    base_dir: str | Path = ".",
    dataset_jsonl_path: str | Path = DEFAULT_CANONICAL_JSONL_PATH,
    schema_report_path: str | Path = DEFAULT_CANONICAL_SCHEMA_PATH,
    force_rebuild: bool = False,
    require_core_fields: bool = False,
) -> dict[str, Any]:
    dataset_path = Path(dataset_jsonl_path)
    schema_path = Path(schema_report_path)

    if force_rebuild or not dataset_path.exists() or not schema_path.exists():
        report = build_canonical_backtest_dataset(
            base_dir=base_dir,
            output_jsonl_path=dataset_path,
            schema_report_path=schema_path,
            require_core_fields=require_core_fields,
        )
    else:
        report = load_json_if_exists(schema_path, default={}) or {}

    try:
        return summarize_canonical_dataset_report(report)
    except Exception:
        return {
            "ok": bool(report),
            "rows_written": report.get("rows_written") if isinstance(report, Mapping) else 0,
            "summary_error": "Could not summarize canonical dataset report.",
        }


def load_canonical_rows_for_dashboard(
    *,
    dataset_jsonl_path: str | Path = DEFAULT_CANONICAL_JSONL_PATH,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    path = Path(dataset_jsonl_path)
    if not path.exists():
        return []

    try:
        rows = load_canonical_backtest_dataset(path)
    except Exception:
        rows = read_jsonl_rows(path, limit=limit)

    if limit is not None and limit >= 0:
        return rows[:limit]
    return rows


def row_matches_profile(row: Mapping[str, Any], profile_key: str | None) -> bool:
    target = normalize_strategy_profile_key(profile_key)

    if target in (None, "", "all_sports"):
        return True

    inferred = infer_strategy_profile_key_from_row(row)
    if inferred == target:
        return True

    for key in ("sport", "league", "module", "sport_profile", "provider", "source_type", "market"):
        if normalize_strategy_profile_key(row.get(key)) == target:
            return True

    return False


def filter_rows_for_profile(rows: Sequence[Mapping[str, Any]], profile_key: str | None) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if row_matches_profile(row, profile_key)]


def summarize_backtest_result(backtest_result: Mapping[str, Any] | None) -> dict[str, Any]:
    result = dict(backtest_result or {})
    strategy_summary = dict(result.get("strategy_bankroll_summary") or {})
    strategy_report = dict(result.get("strategy_bankroll_report") or {})
    leakage_report = dict(result.get("leakage_report") or {})
    replay_summary = dict(result.get("summary") or result.get("replay_summary") or {})

    decisions = list(strategy_report.get("decisions") or [])

    sport_counts: Counter[str] = Counter()
    market_counts: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    no_bet_reasons: Counter[str] = Counter()

    for decision in decisions:
        if not isinstance(decision, Mapping):
            continue

        sport_counts[str(decision.get("sport") or "UNKNOWN")] += 1
        market_counts[str(decision.get("market") or decision.get("market_type") or "UNKNOWN")] += 1

        regression_strategy = dict(decision.get("regression_strategy") or {})
        profile = dict(regression_strategy.get("profile") or {})
        profile_name = (
            decision.get("profile_name")
            or decision.get("selected_profile_key")
            or decision.get("strategy_profile")
            or profile.get("profile_name")
            or profile.get("selected_profile_key")
            or "UNKNOWN"
        )
        profile_counts[str(profile_name)] += 1

        reason = decision.get("reason") or decision.get("no_bet_reason")
        if reason:
            no_bet_reasons[str(reason)] += 1

    return {
        "bets": to_int(strategy_summary.get("bets")),
        "no_bets": to_int(strategy_summary.get("no_bets")),
        "profit_loss": to_float(strategy_summary.get("profit_loss")),
        "roi_percent": to_float(strategy_summary.get("roi_percent")),
        "max_drawdown_percent": to_float(strategy_summary.get("max_drawdown_percent")),
        "starting_bankroll": to_float(strategy_summary.get("starting_bankroll")),
        "ending_bankroll": to_float(strategy_summary.get("ending_bankroll")),
        "decision_count": len(decisions),
        "sport_counts": dict(sport_counts.most_common()),
        "market_counts": dict(market_counts.most_common()),
        "profile_counts": dict(profile_counts.most_common()),
        "no_bet_reasons": dict(no_bet_reasons.most_common()),
        "leakage_summary": leakage_report.get("summary") or leakage_report,
        "replay_summary": replay_summary,
    }


def build_bankroll_curve_rows(backtest_result: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    result = dict(backtest_result or {})
    strategy_report = dict(result.get("strategy_bankroll_report") or {})
    decisions = list(strategy_report.get("decisions") or [])

    curve: list[dict[str, Any]] = []
    fallback_bankroll = 0.0

    for idx, decision in enumerate(decisions):
        if not isinstance(decision, Mapping):
            continue

        bankroll_value = (
            decision.get("ending_bankroll")
            or decision.get("bankroll_after")
            or decision.get("current_bankroll")
            or decision.get("bankroll")
        )

        if bankroll_value in (None, ""):
            profit_loss = to_float(decision.get("profit_loss") or decision.get("pnl"))
            fallback_bankroll += profit_loss
            bankroll_value = fallback_bankroll

        regression_strategy = dict(decision.get("regression_strategy") or {})
        profile = dict(regression_strategy.get("profile") or {})

        curve.append(
            {
                "decision_index": idx,
                "event_id": decision.get("event_id") or decision.get("id") or idx,
                "sport": decision.get("sport") or "UNKNOWN",
                "market": decision.get("market") or decision.get("market_type") or "UNKNOWN",
                "profile": (
                    decision.get("profile_name")
                    or decision.get("selected_profile_key")
                    or decision.get("strategy_profile")
                    or profile.get("profile_name")
                    or profile.get("selected_profile_key")
                    or "UNKNOWN"
                ),
                "bankroll": to_float(bankroll_value),
                "profit_loss": to_float(decision.get("profit_loss") or decision.get("pnl")),
                "model_probability": decision.get("model_probability"),
                "market_implied_probability": decision.get("market_implied_probability"),
                "edge": decision.get("edge"),
                "odds": decision.get("odds") or decision.get("recommended_odds"),
            }
        )

    return curve


def calculate_dashboard_readiness(
    *,
    dataset_summary: Mapping[str, Any],
    backtest_summary: Mapping[str, Any],
) -> dict[str, Any]:
    rows_written = to_int(dataset_summary.get("rows_written") or dataset_summary.get("raw_rows_found"))
    bets = to_int(backtest_summary.get("bets"))
    roi = to_float(backtest_summary.get("roi_percent"))
    drawdown = to_float(backtest_summary.get("max_drawdown_percent"))

    failed: list[str] = []
    warnings: list[str] = []

    if rows_written < 500:
        failed.append("Need at least 500 rows before trusting a model test.")

    if bets < 100:
        failed.append("Need at least 100 bets before trusting performance.")

    if drawdown > 25:
        failed.append("Worst drop is too large.")

    if roi < 0:
        warnings.append("Return is negative in this test.")

    if failed:
        verdict = "Not ready"
        simple = "The model needs more proof before trusting it."
    elif warnings:
        verdict = "Needs review"
        simple = "The model has enough sample size but needs a human review."
    else:
        verdict = "Research candidate"
        simple = "The model passed this paper-test screen, but still needs review before live use."

    return {
        "verdict": verdict,
        "simple_explanation": simple,
        "failed_checks": failed,
        "warnings": warnings,
        "rows_written": rows_written,
        "bets": bets,
        "roi_percent": roi,
        "max_drawdown_percent": drawdown,
    }


def run_model_test(
    *,
    profile_key: str | None,
    tactic: str,
    starting_bankroll: float = 1000.0,
    unit_size: float = 10.0,
    max_rows: int = 2000,
    minimum_edge: float = 0.0,
    minimum_model_probability: float = 0.0,
    intercept: float = 0.5,
    feature_weights: Mapping[str, float] | None = None,
    probability_floor: float = 0.01,
    probability_ceiling: float = 0.99,
    override_existing_probability: bool = True,
    force_rebuild_dataset: bool = False,
    require_core_fields: bool = False,
    model_id: str = "streamlit-model-test",
    base_dir: str | Path = ".",
) -> dict[str, Any]:
    dataset_summary = ensure_canonical_dataset(
        base_dir=base_dir,
        force_rebuild=force_rebuild_dataset,
        require_core_fields=require_core_fields,
    )

    all_rows = load_canonical_rows_for_dashboard(limit=None)
    filtered_rows = filter_rows_for_profile(all_rows, profile_key)

    if max_rows is not None and max_rows >= 0:
        filtered_rows = filtered_rows[:max_rows]

    strategy_config = build_strategy_config(
        tactic=tactic,
        profile_key=profile_key,
        intercept=intercept,
        feature_weights=feature_weights,
        probability_floor=probability_floor,
        probability_ceiling=probability_ceiling,
        override_existing_probability=override_existing_probability,
    )

    backtest_kwargs: dict[str, Any] = {
        "model_id": model_id,
        "rows": filtered_rows,
        "base_data_dir": str(Path(base_dir) / "data"),
    }

    if strategy_config is not None:
        backtest_kwargs["strategy_config"] = strategy_config

    backtest_result = run_backtest(**backtest_kwargs)

    backtest_summary = summarize_backtest_result(backtest_result)
    bankroll_curve = build_bankroll_curve_rows(backtest_result)
    readiness = calculate_dashboard_readiness(
        dataset_summary=dataset_summary,
        backtest_summary=backtest_summary,
    )

    return {
        "ok": True,
        "generated_at": utc_now_iso(),
        "mode": "model_test",
        "model_id": model_id,
        "profile_key": profile_key or "all_sports",
        "tactic": tactic,
        "inputs": {
            "starting_bankroll": starting_bankroll,
            "unit_size": unit_size,
            "max_rows": max_rows,
            "minimum_edge": minimum_edge,
            "minimum_model_probability": minimum_model_probability,
            "intercept": intercept,
            "probability_floor": probability_floor,
            "probability_ceiling": probability_ceiling,
            "override_existing_probability": override_existing_probability,
        },
        "rows_available": len(all_rows),
        "rows_used": len(filtered_rows),
        "dataset_summary": dataset_summary,
        "strategy_config": strategy_config or {},
        "backtest_result": backtest_result,
        "backtest_summary": backtest_summary,
        "bankroll_curve": bankroll_curve,
        "readiness": readiness,
    }


def get_default_historical_sqlite_path() -> str:
    """Return default path for the historical‑odds SQLite database."""
    return str(DEFAULT_HISTORICAL_SQLITE_PATH)


def get_historical_import_source_options() -> list[dict]:
    """Return an operator‑friendly list of sources that can be imported.

    Only sources whose status is KEEP, KEEP_TOOL, DOWNGRADE, or EXPLORATION_ONLY
    are shown.  The list makes clear which sources have working importers.
    """
    all_sources = get_historical_data_source_rows(include_rejected=False)
    options: list[dict] = []
    for src in all_sources:
        if src["status"] in ("remove",):
            continue
        options.append(
            {
                "source_key": src["source_key"],
                "source": src["name"],
                "decision": src["status"],
                "sports": src["sport"] if src["sport"] != "*" else "any",
                "formats": src["format"],
                "next_action": (
                    "Ready" if src["projection_ready"]
                    else "Importer not built yet"
                ),
            }
        )
    return options


def save_historical_upload_for_import(
    source_key: str,
    filename: str,
    content: bytes | str,
    upload_dir: Path = DEFAULT_HISTORICAL_UPLOAD_DIR,
) -> dict:
    """Save uploaded content to a local runtime path.

    The filename is sanitised so only safe characters are kept.
    No network calls are made.
    """
    safe_name = "".join(c for c in filename if c.isalnum() or c in (".", "_", "-"))
    if not safe_name:
        safe_name = "upload"
    file_path = upload_dir / source_key / safe_name
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        file_path.write_text(content, encoding="utf-8")
    else:
        file_path.write_bytes(content)

    return {
        "ok": True,
        "path": str(file_path),
        "source_key": source_key,
        "filename": safe_name,
        "size_bytes": file_path.stat().st_size,
    }


def import_historical_file_to_sqlite_for_dashboard(
    db_path: str | Path,
    source_key: str,
    file_path: str | Path,
    source_file: str | None = None,
) -> dict:
    """Open/initialize the SQLite database, import a canonical file, and return a summary.

    The connection is closed before returning.
    After importing, also backfill line snapshots (non‑blocking).
    """
    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)

    result = import_historical_odds_file_to_sqlite(
        conn, source_key, file_path, source_file=source_file
    )
    # Also create line snapshots from the just‑imported rows
    initialize_line_movement_schema(conn)
    lm_warnings: list[str] = []
    try:
        # Re‑fetch the inserted rows to get their canonical form
        inserted_rows = result.get("rows_inserted", 0)
        if inserted_rows > 0:
            snap_rows = query_historical_odds_rows(conn, limit=inserted_rows + 100)
            if snap_rows:
                lm_result = upsert_line_snapshots_for_canonical_rows(conn, snap_rows)
                if lm_result.get("warnings"):
                    lm_warnings = lm_result["warnings"]
    except Exception as exc:
        lm_warnings.append(str(exc))

    conn.close()
    return {
        "ok": bool(result.get("ok")),
        "rows_seen": result.get("rows_seen", 0),
        "rows_inserted": result.get("rows_inserted", 0),
        "rows_rejected": result.get("rows_rejected", 0),
        "warning_total": result.get("warning_total", 0),
        "import_id": result.get("import_id", ""),
        "line_movement_warnings": lm_warnings,
    }


def get_line_movement_snapshot_for_dashboard(
    db_path: str | Path,
) -> dict:
    """Open the SQLite store, initialise line movement schema, and return summary.

    Closes the connection before returning.
    """
    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)
    result = summarize_line_movement_store(conn)
    conn.close()
    return {
        "ok": result.get("ok"),
        "total_snapshots": result.get("total_snapshots", 0),
        "opening_snapshots": result.get("opening_snapshots", 0),
        "decision_snapshots": result.get("decision_snapshots", 0),
        "current_snapshots": result.get("current_snapshots", 0),
        "closing_snapshots": result.get("closing_snapshots", 0),
        "line_movement_ready": result.get("line_movement_ready", False),
        "clv_ready": result.get("clv_ready", False),
        "warnings": result.get("warnings", []),
    }


def get_historical_sqlite_snapshot_for_dashboard(db_path: str | Path) -> dict:
    """Open the SQLite database and return table counts, summary, filter options, and validation."""
    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)

    counts: dict[str, int] = {}
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        name = row["name"]
        cnt = conn.execute(f"SELECT COUNT(*) AS c FROM [{name}]").fetchone()["c"]
        counts[name] = cnt

    db_summary = summarize_historical_odds_db(conn)
    filter_options = get_sqlite_backtest_filter_options(conn)
    validation = validate_sqlite_store(conn)
    conn.close()

    return {
        "ok": True,
        "db_path": str(db_path),
        "table_counts": counts,
        "db_summary": db_summary,
        "filter_options": filter_options,
        "validation": validation,
    }


def get_historical_sqlite_filter_options_for_dashboard(db_path: str | Path) -> dict:
    """Return only filter options (sports, leagues, etc.) from the SQLite store."""
    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)
    opts = get_sqlite_backtest_filter_options(conn)
    conn.close()
    return opts


def run_sqlite_projection_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
    model_probability: float | None = None,
    strategy_config: dict | None = None,
) -> dict:
    """Open the SQLite store, run a historical backtest, and return summary + raw result."""
    conn = connect_historical_odds_db(str(db_path))
    initialize_historical_odds_db(conn)

    bridge_result = run_sqlite_historical_backtest(
        conn,
        sport=sport,
        league=league,
        market=market,
        source_key=source_key,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        model_probability=model_probability,
        strategy_config=strategy_config,
    )
    summary = summarize_sqlite_historical_backtest(bridge_result)

    filter_opts = get_sqlite_backtest_filter_options(conn)
    conn.close()

    return {
        "ok": bool(bridge_result.get("ok")),
        "summary": summary,
        "result": bridge_result,
        "filter_options": filter_opts,
    }


def make_historical_projection_metric_rows(summary: dict) -> list[dict]:
    """Return a flat list of metric rows suitable for Streamlit data frames."""
    row = {
        "rows_loaded": summary.get("rows_loaded", 0),
        "rows_converted": summary.get("rows_converted", 0),
        "bets": summary.get("bets", 0),
        "no_bets": summary.get("no_bets", 0),
        "profit_loss": summary.get("profit_loss", 0.0),
        "roi_percent": summary.get("roi_percent", 0.0),
        "max_drawdown_percent": summary.get("max_drawdown_percent", 0.0),
        "projection_ready": summary.get("projection_ready", False),
        "reason": summary.get("reason", ""),
    }
    return [row]


def make_arrow_safe_value(value: Any) -> Any:
    """Convert a value to a stable Arrow‑compatible string.

    - str → unchanged
    - Path → string
    - list, tuple, set, dict → JSON string (sorted keys)
    - int, float, bool, None → string (display‑safe representation)
    """
    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple, set, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    # int, float, bool, None → plain string
    return str(value)


def make_arrow_safe_table_rows(rows: list[dict]) -> list[dict]:
    """Return new list where each dict's values are made Arrow‑safe.

    The input list is never mutated.
    """
    result: list[dict] = []
    for row in rows:
        new_row: dict[str, Any] = {}
        for k, v in row.items():
            new_row[k] = make_arrow_safe_value(v)
        result.append(new_row)
    return result


# ---------------------------------------------------------------------------
# Phase 10H10 – Data Explorer helpers
# ---------------------------------------------------------------------------


REQUIRED_FIELD_GROUPS: dict[str, list[str]] = {
    "core_event": [
        "sport", "league", "event_date", "home_team", "away_team",
    ],
    "line_core": [
        "market", "selection", "odds_at_decision_time",
        "market_implied_probability", "bookmaker", "line_value",
    ],
    "line_movement": [
        "opening_odds", "closing_odds", "opening_line", "closing_line",
        "current_odds", "current_line", "snapshot_time", "clv",
    ],
    "settlement": [
        "final_result", "winner", "home_score", "away_score", "profit_loss",
    ],
    "team_stats": [
        "home_team_stats", "away_team_stats", "pace",
        "offensive_rating", "defensive_rating", "rest_days", "injuries",
    ],
    "player_stats": [
        "player_name", "player_team", "player_prop_type", "player_line",
        "player_minutes", "player_usage", "recent_player_average",
        "opponent_allowed_stat",
    ],
    "projection_control": [
        "model_probability", "features_known_at_decision_time",
    ],
}


def classify_market_family(
    market: str | None,
    selection: str | None = None,
) -> str:
    """Return one of the seven market families."""
    if not market:
        return "unknown"
    lower = (
        market.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )
    if lower in ("1x2", "moneyline", "ml"):
        return "moneyline_or_1x2"
    if lower in ("runline", "spread", "pointspread"):
        return "spread_or_runline"
    if lower in ("total", "overunder", "totals", "over/under", "o/u", "ou", "gametotal", "totalpoints"):
        return "total"
    if lower.startswith("team_total") or lower in ("team total",):
        return "team_total"
    if selection and "player" in selection.lower():
        return "player_prop"
    if lower in (
        "playerpoints", "playerpointsprop", "playerprop",
        "player_points", "player_points_prop",
    ):
        return "player_prop"
    return "unknown"


def get_required_field_groups_for_market(
    market_family: str,
) -> dict[str, list[str]]:
    """Return required field groups for a given market family."""
    groups: dict[str, list[str]] = {
        "core_event": REQUIRED_FIELD_GROUPS["core_event"],
        "line_core": REQUIRED_FIELD_GROUPS["line_core"],
        "settlement": REQUIRED_FIELD_GROUPS["settlement"],
        "projection_control": REQUIRED_FIELD_GROUPS["projection_control"],
    }
    if market_family == "player_prop":
        groups["player_stats"] = REQUIRED_FIELD_GROUPS["player_stats"]
    if market_family in ("spread_or_runline", "total", "team_total"):
        groups["line_movement"] = REQUIRED_FIELD_GROUPS["line_movement"]
    return groups


def calculate_field_coverage(
    rows: list[dict[str, Any]],
    required_groups: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    """For each field, compute presence / absence counts and a status."""
    coverage: dict[str, dict[str, Any]] = {}
    total = len(rows) or 1  # avoid division by zero
    for group_name, fields in required_groups.items():
        for field in fields:
            present_count = sum(
                1 for r in rows if field in r and r[field] is not None
            )
            missing_count = len(rows) - present_count
            coverage_percent = round(present_count / total * 100, 1)
            if coverage_percent >= 99:
                status = "good"
            elif coverage_percent > 0:
                status = "partial"
            else:
                status = "missing"
            coverage[field] = {
                "present_count": present_count,
                "missing_count": missing_count,
                "coverage_percent": coverage_percent,
                "status": status,
                "group": group_name,
            }
    return coverage


def build_market_readiness_report(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate how ready the data is for projection and optional features."""
    if not rows:
        return {
            "projection_ready": False,
            "settlement_ready": False,
            "line_movement_ready": False,
            "player_prop_ready": False,
            "team_stats_ready": False,
            "critical_missing_fields": ["No rows available"],
            "warnings": [],
            "reason": "No rows available",
        }

    core_present = any(
        r.get("sport")
        and r.get("league")
        and r.get("event_date")
        and r.get("home_team")
        and r.get("away_team")
        for r in rows
    )
    line_core_present = any(
        r.get("market")
        and r.get("selection")
        and r.get("odds_at_decision_time") is not None
        and r.get("market_implied_probability") is not None
        for r in rows
    )
    settlement_ready = any(
        r.get("final_result") is not None
        or r.get("winner") is not None
        or r.get("home_score") is not None
        for r in rows
    )
    line_movement_ready = any(
        r.get("opening_odds") is not None
        or r.get("closing_odds") is not None
        or r.get("current_odds") is not None
        or r.get("opening_line") is not None
        or r.get("closing_line") is not None
        or r.get("clv") is not None
        for r in rows
    )
    player_prop_ready = any(
        r.get("player_name") is not None
        and r.get("player_prop_type") is not None
        and r.get("player_line") is not None
        for r in rows
    )
    team_stats_ready = any(
        r.get("home_team_stats") is not None
        or r.get("away_team_stats") is not None
        or r.get("pace") is not None
        for r in rows
    )

    critical_missing: list[str] = []
    if not core_present:
        critical_missing.append(
            "Core event fields (sport, league, event_date, home_team, away_team)"
        )
    if not line_core_present:
        critical_missing.append(
            "Line core fields (market, selection, odds_at_decision_time, "
            "market_implied_probability)"
        )
    if not settlement_ready:
        critical_missing.append("Settlement data (final_result, winner, scores)")
    projection_ready = core_present and line_core_present and settlement_ready

    warnings: list[str] = []
    if not line_movement_ready:
        warnings.append(
            "No line movement data (opening/closing odds). ROI may be unreliable."
        )
    if not player_prop_ready:
        warnings.append("No player prop data.")
    if not team_stats_ready:
        warnings.append("No team stats data.")

    reason = "; ".join(critical_missing) if critical_missing else (
        "Data sufficient for projection."
    )
    return {
        "projection_ready": projection_ready,
        "settlement_ready": settlement_ready,
        "line_movement_ready": line_movement_ready,
        "player_prop_ready": player_prop_ready,
        "team_stats_ready": team_stats_ready,
        "critical_missing_fields": critical_missing,
        "warnings": warnings,
        "reason": reason,
    }


def get_sqlite_data_explorer_snapshot_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    """Open the SQLite store, filter rows, and return a data‑explorer snapshot."""
    result: dict[str, Any] = {
        "ok": False,
        "db_path": str(db_path),
        "filters": {
            "sport": sport,
            "league": league,
            "market": market,
            "source_key": source_key,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        },
        "total_rows": 0,
        "filter_options": {},
        "sports": [],
        "leagues": [],
        "markets": [],
        "source_keys": [],
        "market_families": {},
        "sample_rows": [],
        "field_coverage": {},
        "missing_field_groups": [],
        "readiness": {},
        "warnings": [],
    }
    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)

        raw_rows = query_historical_odds_rows(
            conn,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        result["total_rows"] = len(raw_rows)
    except Exception as exc:
        result["warnings"].append(f"Could not open database: {exc}")
        return result

    # distribute rows
    rows = raw_rows
    sports = sorted(
        {r.get("sport") for r in rows if r.get("sport")}
    )
    leagues = sorted(
        {r.get("league") for r in rows if r.get("league")}
    )
    markets = sorted(
        {r.get("market") for r in rows if r.get("market")}
    )
    source_keys = sorted(
        {r.get("source_key") for r in rows if r.get("source_key")}
    )
    result["sports"] = sports
    result["leagues"] = leagues
    result["markets"] = markets
    result["source_keys"] = source_keys

    # market families
    families: dict[str, int] = {}
    for r in rows:
        family = classify_market_family(r.get("market"), r.get("selection"))
        families[family] = families.get(family, 0) + 1
    result["market_families"] = {
        k: v for k, v in sorted(families.items(), key=lambda x: -x[1])
    }

    # sample rows (Arrow‑safe)
    result["sample_rows"] = make_arrow_safe_table_rows(rows[: min(limit, 20)])

    # field coverage across all groups
    all_groups = dict(REQUIRED_FIELD_GROUPS)
    coverage = calculate_field_coverage(rows, all_groups)
    result["field_coverage"] = coverage

    # missing field groups
    missing_groups: list[str] = []
    for group_name, fields in all_groups.items():
        for field in fields:
            entry = coverage.get(field)
            if entry and entry["status"] == "missing":
                missing_groups.append(f"{group_name} / {field}")
    result["missing_field_groups"] = missing_groups

    readiness = build_market_readiness_report(rows)
    result["readiness"] = readiness

    # filter options
    result["filter_options"] = {
        "sports": sports,
        "leagues": leagues,
        "markets": markets,
        "source_keys": source_keys,
    }
    result["ok"] = True

    # determine any overall warnings
    if readiness.get("warnings"):
        result["warnings"].extend(readiness["warnings"])
    if missing_groups:
        result["warnings"].append(
            f"Missing field groups: {missing_groups[0]}"
            + (f" (+{len(missing_groups)-1} more)" if len(missing_groups) > 1 else "")
        )

    conn.close()
    return result


def render_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    summary = dict(dashboard.get("backtest_summary") or {})
    readiness = dict(dashboard.get("readiness") or {})
    inputs = dict(dashboard.get("inputs") or {})

    lines = [
        "# Latest Backtest Dashboard",
        "",
        f"Generated: `{dashboard.get('generated_at')}`",
        f"Model ID: `{dashboard.get('model_id')}`",
        f"Profile: `{dashboard.get('profile_key')}`",
        f"Tactic: `{dashboard.get('tactic')}`",
        "",
        "## Explain Like I'm 8",
        "",
        f"- Starting money: `{inputs.get('starting_bankroll')}`",
        f"- Normal bet size: `{inputs.get('unit_size')}`",
        f"- Money won or lost: `{summary.get('profit_loss')}`",
        f"- Return percent: `{summary.get('roi_percent')}`",
        f"- Worst drop percent: `{summary.get('max_drawdown_percent')}`",
        f"- Decision: `{readiness.get('verdict')}`",
        f"- Simple meaning: {readiness.get('simple_explanation')}",
        "",
        "## Backtest Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
        "",
        "## Readiness",
        "",
        "```json",
        json.dumps(readiness, indent=2, sort_keys=True),
        "```",
        "",
        "## Inputs",
        "",
        "```json",
        json.dumps(inputs, indent=2, sort_keys=True),
        "```",
        "",
    ]

    return "\n".join(lines) + "\n"


def generate_latest_dashboard_outputs(
    *,
    tactic: str = "Sport-specific regression",
    profile_key: str | None = "all_sports",
    starting_bankroll: float = 1000.0,
    unit_size: float = 10.0,
    max_rows: int = 2000,
    intercept: float = 0.5,
    feature_weights: Mapping[str, float] | None = None,
    probability_floor: float = 0.01,
    probability_ceiling: float = 0.99,
    override_existing_probability: bool = True,
    force_rebuild_dataset: bool = False,
    require_core_fields: bool = False,
    output_json_path: str | Path = DEFAULT_DASHBOARD_JSON_PATH,
    output_markdown_path: str | Path = DEFAULT_DASHBOARD_MARKDOWN_PATH,
) -> dict[str, Any]:
    dashboard = run_model_test(
        profile_key=profile_key,
        tactic=tactic,
        starting_bankroll=starting_bankroll,
        unit_size=unit_size,
        max_rows=max_rows,
        intercept=intercept,
        feature_weights=feature_weights,
        probability_floor=probability_floor,
        probability_ceiling=probability_ceiling,
        override_existing_probability=override_existing_probability,
        force_rebuild_dataset=force_rebuild_dataset,
        require_core_fields=require_core_fields,
        model_id="streamlit-latest-dashboard",
    )

    output_json = Path(output_json_path)
    output_md = Path(output_markdown_path)

    write_json(output_json, dashboard)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_dashboard_markdown(dashboard), encoding="utf-8")

    return {
        "ok": True,
        "output_json_path": str(output_json),
        "output_markdown_path": str(output_md),
        "summary": {
            "rows_used": dashboard.get("rows_used"),
            "bets": dashboard.get("backtest_summary", {}).get("bets"),
            "profit_loss": dashboard.get("backtest_summary", {}).get("profit_loss"),
            "roi_percent": dashboard.get("backtest_summary", {}).get("roi_percent"),
            "max_drawdown_percent": dashboard.get("backtest_summary", {}).get("max_drawdown_percent"),
            "readiness": dashboard.get("readiness", {}).get("verdict"),
        },
    }


def load_dashboard_snapshot() -> dict[str, Any]:
    dashboard = load_json_if_exists(DEFAULT_DASHBOARD_JSON_PATH, default={}) or {}
    markdown_exists = DEFAULT_DASHBOARD_MARKDOWN_PATH.exists()
    schema = load_json_if_exists(DEFAULT_CANONICAL_SCHEMA_PATH, default={}) or {}
    paper = load_json_if_exists(DEFAULT_PAPER_LEDGER_PATH, default={}) or {}
    review = load_json_if_exists(DEFAULT_REVIEW_QUEUE_PATH, default={}) or {}
    health = load_json_if_exists(DEFAULT_SYSTEM_HEALTH_PATH, default={}) or {}

    return {
        "dashboard_exists": DEFAULT_DASHBOARD_JSON_PATH.exists(),
        "dashboard_markdown_exists": markdown_exists,
        "dashboard": dashboard,
        "dashboard_summary": dashboard.get("backtest_summary", {}) if isinstance(dashboard, Mapping) else {},
        "readiness": dashboard.get("readiness", {}) if isinstance(dashboard, Mapping) else {},
        "schema": schema,
        "paper_ledger_rows": flatten_preview_rows(paper, limit=500),
        "review_queue_rows": flatten_preview_rows(review, limit=500),
        "health": health,
        "files": file_inventory(),
    }


def get_system_health_rows() -> list[dict[str, Any]]:
    files = file_inventory()

    git_status = []
    try:
        git_status = subprocess.check_output(["git", "status", "--short"], text=True).splitlines()
    except Exception:
        git_status = ["git status unavailable"]

    rows = []
    for item in files:
        rows.append(
            {
                "check": item["label"],
                "status": "OK" if item["exists"] else "MISSING",
                "detail": item["path"],
                "size_bytes": item["size_bytes"],
            }
        )

    rows.append(
        {
            "check": "Git working tree",
            "status": "CLEAN" if not git_status else "DIRTY",
            "detail": "; ".join(git_status[:10]),
            "size_bytes": 0,
        }
    )

    return rows


def simple_home_cards(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    dashboard = dict(snapshot.get("dashboard") or {})
    summary = dict(snapshot.get("dashboard_summary") or {})
    readiness = dict(snapshot.get("readiness") or {})
    inputs = dict(dashboard.get("inputs") or {})

    return {
        "Is the system safe?": "Paper/testing mode" if snapshot.get("dashboard_exists") else "Dashboard file missing",
        "How much money did the test start with?": inputs.get("starting_bankroll", "Unknown"),
        "How much money did the test end with?": summary.get("ending_bankroll", "Unknown"),
        "Did the graph go up or down?": "Up or flat" if to_float(summary.get("profit_loss")) >= 0 else "Down",
        "What sport/profile was tested?": dashboard.get("profile_key", "Unknown"),
        "Is this ready or not ready?": readiness.get("verdict", "Unknown"),
    }


# ---------------------------------------------------------------------------
# Phase 10H11 – Feature Control Lab + Dashboard Instructions
# ---------------------------------------------------------------------------

FEATURE_CONTROL_VERSION: str = "10H11"
DEFAULT_FEATURE_CONTROL_PROFILE: str = "available_baseline"


def get_feature_control_profiles() -> list[dict[str, str]]:
    """Return simple profile options for feature control."""
    return [
        {
            "value": "available_baseline",
            "label": "Available Baseline",
            "meaning": "Use the fields we currently have without pretending missing fields exist",
        },
        {
            "value": "odds_only",
            "label": "Odds Only",
            "meaning": "Test market/odds fields only",
        },
        {
            "value": "no_line_movement",
            "label": "Remove Line Movement",
            "meaning": "Ignore line movement fields when not available",
        },
        {
            "value": "settlement_check",
            "label": "Settlement Check",
            "meaning": "Focus on whether outcomes/results exist",
        },
        {
            "value": "custom",
            "label": "Custom Add/Remove",
            "meaning": "Operator chooses included/excluded fields",
        },
    ]


def get_feature_group_definitions() -> dict[str, dict[str, Any]]:
    """Return groups that match the Data Explorer coverage."""
    return {
        "core_event": {
            "label": "Core Event Fields",
            "description": "Sport, league, date, home/away team",
            "fields": REQUIRED_FIELD_GROUPS["core_event"],
        },
        "line_core": {
            "label": "Line Core Fields",
            "description": "Market, selection, odds, implied probability, bookmaker, line value",
            "fields": REQUIRED_FIELD_GROUPS["line_core"],
        },
        "line_movement": {
            "label": "Line Movement Fields",
            "description": "Opening/closing odds, CLV, snapshot time",
            "fields": REQUIRED_FIELD_GROUPS["line_movement"],
        },
        "settlement": {
            "label": "Settlement Fields",
            "description": "Final result, winner, scores, profit/loss",
            "fields": REQUIRED_FIELD_GROUPS["settlement"],
        },
        "team_stats": {
            "label": "Team Stats Fields",
            "description": "Home/away team statistics, pace, ratings, injuries",
            "fields": REQUIRED_FIELD_GROUPS["team_stats"],
        },
        "player_stats": {
            "label": "Player Stats Fields",
            "description": "Player name, prop type, line, minutes, usage",
            "fields": REQUIRED_FIELD_GROUPS["player_stats"],
        },
        "projection_control": {
            "label": "Projection Control Fields",
            "description": "Model probability, features known at decision time",
            "fields": REQUIRED_FIELD_GROUPS["projection_control"],
        },
    }


def get_never_feature_fields() -> list[str]:
    """Return fields that must never be used inside model features
    because they are leakage or grading fields."""
    return [
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


def build_feature_control_config(
    profile: str = DEFAULT_FEATURE_CONTROL_PROFILE,
    include_groups: list[str] | None = None,
    exclude_groups: list[str] | None = None,
    include_fields: list[str] | None = None,
    exclude_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Return a feature control configuration dictionary."""
    never = get_never_feature_fields()
    return {
        "profile": profile,
        "include_groups": include_groups or [],
        "exclude_groups": exclude_groups or [],
        "include_fields": include_fields or [],
        "exclude_fields": exclude_fields or [],
        "never_feature_fields": never,
        "version": FEATURE_CONTROL_VERSION,
    }


def _safe_pre_decision_fields(row: dict, never: list[str]) -> dict[str, Any]:
    """Build a safe pre-decision feature snapshot from row fields,
    excluding any never_feature_fields."""
    safe = {}
    for k, v in row.items():
        if k in never:
            continue
        if k == "features_known_at_decision_time":
            continue  # we will rebuild
        # keep the value as is (could be dict/list etc)
        safe[k] = v
    return safe


def apply_feature_control_to_row(row: dict, config: dict) -> dict:
    """Return a copy of *row* with *features_known_at_decision_time*
    filtered according to *config*.

    - Never mutate input row.
    - Never include *never_feature_fields* in the filtered snapshot.
    - If *features_known_at_decision_time* does not exist, build a safe
      pre-decision snapshot from the row fields.
    - Preserve top-level settlement fields for grading.
    """
    import copy

    never = config.get("never_feature_fields", get_never_feature_fields())
    row_copy = copy.deepcopy(row)

    # Build the initial snapshot
    existing = row_copy.get("features_known_at_decision_time")
    if existing is not None and isinstance(existing, dict):
        snapshot = dict(existing)
    else:
        snapshot = _safe_pre_decision_fields(row_copy, never)

    # Remove never fields
    for nf in never:
        snapshot.pop(nf, None)

    # Apply group includes/excludes
    groups_def = get_feature_group_definitions()
    all_group_fields = set()
    for grp, grp_data in groups_def.items():
        for f in grp_data["fields"]:
            all_group_fields.add(f)

    include_groups = set(config.get("include_groups") or [])
    exclude_groups = set(config.get("exclude_groups") or [])

    if include_groups:
        allowed_fields: set[str] = set()
        for grp in include_groups:
            if grp in groups_def:
                for f in groups_def[grp]["fields"]:
                    allowed_fields.add(f)
        snapshot = {k: v for k, v in snapshot.items() if k in allowed_fields}
    elif exclude_groups:
        blocked: set[str] = set()
        for grp in exclude_groups:
            if grp in groups_def:
                for f in groups_def[grp]["fields"]:
                    blocked.add(f)
        snapshot = {k: v for k, v in snapshot.items() if k not in blocked}

    # Apply individual field includes/excludes
    include_fields = set(config.get("include_fields") or [])
    exclude_fields = set(config.get("exclude_fields") or [])

    if include_fields:
        snapshot = {k: v for k, v in snapshot.items() if k in include_fields}
    else:
        for ex in exclude_fields:
            snapshot.pop(ex, None)

    row_copy["features_known_at_decision_time"] = snapshot
    return row_copy


def summarize_feature_control_impact(
    rows: list[dict], config: dict
) -> dict[str, Any]:
    """Analyse the impact of applying *config* to *rows*.

    Returns keys:
    - profile, rows_seen, included_groups, excluded_groups,
      included_fields, excluded_fields, never_feature_fields,
      available_feature_count, missing_feature_count,
      removed_feature_count, warnings, operator_interpretation.
    """
    never = config.get("never_feature_fields", get_never_feature_fields())
    groups_def = get_feature_group_definitions()

    available: set[str] = set()
    missing: set[str] = set()
    removed: set[str] = set()

    for row in rows:
        row_keys = set(row.keys())
        snapshot_keys = set(row.get("features_known_at_decision_time", {}).keys())
        available.update(snapshot_keys)
        missing.update(k for k in row_keys if k not in snapshot_keys and k not in never)

    # Fields that are in never set and thus removed
    removed.update(f for f in never if any(f in row for row in rows))

    include_groups = config.get("include_groups") or []
    exclude_groups = config.get("exclude_groups") or []
    include_fields = config.get("include_fields") or []
    exclude_fields = config.get("exclude_fields") or []

    warnings: list[str] = []
    if exclude_groups or exclude_fields:
        warnings.append("Some field groups or fields have been explicitly excluded.")
    if any(grp in exclude_groups for grp in ("line_movement",)):
        warnings.append("Line movement fields are missing or removed – CLV-style analysis will be limited.")
    if any(grp in exclude_groups for grp in ("player_stats",)):
        warnings.append("Player prop fields are missing – player prop projections are not ready.")

    # Interpretation
    profile_label = next(
        (p["label"] for p in get_feature_control_profiles() if p["value"] == config.get("profile")),
        config.get("profile", DEFAULT_FEATURE_CONTROL_PROFILE),
    )
    interp = f"Profile: {profile_label}. "
    if not include_groups and not exclude_groups and not include_fields and not exclude_fields:
        interp += "This profile can test a basic available-data baseline."
    else:
        interp += "Operator selected custom field controls."
    interp += " Settlement fields are top-level only and are not used as model features."

    return {
        "profile": config.get("profile", DEFAULT_FEATURE_CONTROL_PROFILE),
        "rows_seen": len(rows),
        "included_groups": include_groups,
        "excluded_groups": exclude_groups,
        "included_fields": include_fields,
        "excluded_fields": exclude_fields,
        "never_feature_fields": never,
        "available_feature_count": len(available),
        "missing_feature_count": len(missing),
        "removed_feature_count": len(removed),
        "warnings": warnings,
        "operator_interpretation": interp,
    }


def get_dashboard_tab_instructions() -> list[dict[str, str]]:
    """Return instructions for each dashboard tab."""
    return [
        {
            "tab": "Instructions",
            "purpose": "Explains how to use the dashboard",
            "how_to_use": "Start here to understand each tab and the overall testing workflow",
            "why_it_matters": "Prevents confusion and helps the operator know what to do next",
            "next_step": "Review Data Source Library, then Import Historical Data, then Data Explorer",
        },
        {
            "tab": "Operator Summary",
            "purpose": "Quick health snapshot of the latest model run.",
            "how_to_use": "Generate the dashboard or check recent metrics.",
            "why_it_matters": "Shows the most recent outcome and readiness.",
            "next_step": "Explore deeper in Data Explorer if data seems sparse.",
        },
        {
            "tab": "Data Source Library",
            "purpose": "View all registered historical data sources.",
            "how_to_use": "Check status column; only 'Ready' sources have working importers.",
            "why_it_matters": "Confirms which sources can be imported.",
            "next_step": "Pick one and import a local file.",
        },
        {
            "tab": "Import Historical Data",
            "purpose": "Upload a CSV or JSON file for a selected source.",
            "how_to_use": "Choose source, provide file path or upload, click import.",
            "why_it_matters": "Populates the SQLite store used by projections.",
            "next_step": "Visit Data Quality Check to see the new rows.",
        },
        {
            "tab": "Data Quality Check",
            "purpose": "View file inventory, schema, and SQLite snapshot.",
            "how_to_use": "Refresh the snapshot to see table counts.",
            "why_it_matters": "Validates that imported data looks correct.",
            "next_step": "Open Data Explorer to inspect field coverage.",
        },
        {
            "tab": "Data Explorer",
            "purpose": "Explore available fields, missing fields, and market families.",
            "how_to_use": "Apply filters and refresh; use the Feature Control Lab to experiment.",
            "why_it_matters": "Shows which fields are present and which groups are missing.",
            "next_step": "Choose a feature profile and run Model Projection.",
        },
        {
            "tab": "Model Projection",
            "purpose": "Run a historical backtest using SQLite rows and a feature profile.",
            "how_to_use": "Optional filters, choose feature profile, click run.",
            "why_it_matters": "Produces ROI, drawdown, and skipped decision metrics.",
            "next_step": "Review the output and compare profiles.",
        },
        {
            "tab": "Paper Bets",
            "purpose": "Browse paper‑ledger and review‑queue rows.",
            "how_to_use": "Select source and optional sport/market filters.",
            "why_it_matters": "Inspect the raw decisions and outcomes.",
            "next_step": "Use filters to isolate specific sport or market.",
        },
        {
            "tab": "Backtest Dashboard",
            "purpose": "Full dashboard of the latest generated backtest.",
            "how_to_use": "Generate or view existing dashboard JSON.",
            "why_it_matters": "Comprehensive view of the last run.",
            "next_step": "Compare with other tactics by generating again.",
        },
        {
            "tab": "Test One Sport",
            "purpose": "Run a paper backtest for a single sport/profile.",
            "how_to_use": "Pick sport, click run.",
            "why_it_matters": "Isolate performance of a specific sport.",
            "next_step": "Adjust tactic or intercept and re‑run.",
        },
        {
            "tab": "Test All Sports",
            "purpose": "Run a paper backtest across all sports.",
            "how_to_use": "Select mode, click run.",
            "why_it_matters": "See overall model performance.",
            "next_step": "Compare all‑sports vs sport‑specific results.",
        },
        {
            "tab": "Bankroll Settings",
            "purpose": "Set risk presets and testing parameters.",
            "how_to_use": "Choose preset or tweak numbers in sidebar.",
            "why_it_matters": "Controls simulated money management.",
            "next_step": "Keep conservative during early testing.",
        },
        {
            "tab": "Regression Tactics",
            "purpose": "View and adjust regression tactic and feature weights.",
            "how_to_use": "Select tactic in sidebar, see explanation here.",
            "why_it_matters": "Defines how model chance is derived.",
            "next_step": "Try All-sports vs Sport-specific for comparison.",
        },
        {
            "tab": "System Health",
            "purpose": "Check file inventory and git status.",
            "how_to_use": "Read the table; red status means missing file.",
            "why_it_matters": "Ensures all expected artifacts exist.",
            "next_step": "Generate missing dashboard files from Operator Summary.",
        },
    ]


def get_overall_operator_workflow_steps() -> list[dict[str, str]]:
    """Return ordered workflow steps for the operator."""
    return [
        {
            "step": 1,
            "action": "Pick approved data source",
            "detail": "Use Data Source Library to see which sources are ready.",
        },
        {
            "step": 2,
            "action": "Import local CSV/JSON",
            "detail": "Upload file in Import Historical Data tab.",
        },
        {
            "step": 3,
            "action": "Check data quality",
            "detail": "Open Data Quality Check to verify table counts.",
        },
        {
            "step": 4,
            "action": "Explore available fields and missing fields",
            "detail": "Use Data Explorer and the Feature Control Lab.",
        },
        {
            "step": 5,
            "action": "Choose feature profile",
            "detail": "Select a profile that matches what you want to test.",
        },
        {
            "step": 6,
            "action": "Run projection",
            "detail": "Click run in Model Projection.",
        },
        {
            "step": 7,
            "action": "Review settled count, ROI, drawdown, skipped decisions",
            "detail": "Examine the result metrics.",
        },
        {
            "step": 8,
            "action": "Adjust / remove data points",
            "detail": "Return to Feature Control Lab and refine.",
        },
        {
            "step": 9,
            "action": "Compare consistency",
            "detail": "Run the same projection with different profiles.",
        },
        {
            "step": 10,
            "action": "Add richer data later",
            "detail": "When new sources are available, re-import and repeat.",
        },
    ]
