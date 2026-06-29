from __future__ import annotations

import json
from collections import Counter
from typing import Any, Mapping, Sequence


_PROFILE_ALIASES = {
    "nba": "basketball_nba",
    "nfl": "americanfootball_nfl",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "soccer": "association_football",
    "kalshi": "prediction_market",
    "all_sports": "all_sports",
}


def normalize_strategy_profile_key(value: Any) -> str | None:
    from src.automation_scheduler_legacy.backtest_strategy_profiles import normalize_strategy_profile_key as _legacy_normalize_strategy_profile_key

    return _legacy_normalize_strategy_profile_key(value)


def infer_strategy_profile_key_from_row(row: Mapping[str, Any]) -> str | None:
    if not isinstance(row, Mapping):
        return None
    return normalize_strategy_profile_key(row.get("sport") or row.get("league") or row.get("market_type"))


def _profile_payload(
    *,
    profile_name: str,
    profile_scope: str,
    selection_reason: str,
    intercept: float = 0.5,
    feature_weights: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "profile_name": profile_name,
        "profile_scope": profile_scope,
        "selection_reason": selection_reason,
        "intercept": float(intercept),
        "feature_weights": dict(feature_weights or {}),
    }


def build_strategy_config_for_row(
    row: Mapping[str, Any],
    *,
    all_sports_profile: Mapping[str, Any] | None = None,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    from src.automation_scheduler_legacy.backtest_strategy_profiles import build_strategy_config_for_row as _legacy_build_strategy_config_for_row

    return _legacy_build_strategy_config_for_row(
        row,
        all_sports_profile=all_sports_profile,
        sport_profiles=sport_profiles,
    )


def describe_regression_profiles() -> dict[str, Any]:
    from src.automation_scheduler_legacy.backtest_strategy_profiles import describe_regression_profiles as _legacy_describe_regression_profiles

    return _legacy_describe_regression_profiles()


def get_regression_profile(
    *,
    sport: Any,
    profile_scope: str = "auto",
    all_sports_profile: Mapping[str, Any] | None = None,
    sport_profiles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    from src.automation_scheduler_legacy.backtest_strategy_profiles import get_regression_profile as _legacy_get_regression_profile

    return _legacy_get_regression_profile(
        sport=sport,
        profile_scope=profile_scope,
        all_sports_profile=all_sports_profile,
        sport_profiles=sport_profiles,
    )


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
    "Aggressive": {
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

LEGACY_RISK_PRESET_ALIASES: dict[str, str] = {
    "Aggressive paper only": "Aggressive",
}

SCENARIO_BACKTEST_MODES: dict[str, dict[str, str]] = {
    "Baseline / Imputed": {
        "description": "Default missing-data handling for comparison runs.",
    },
    "Strict / Complete Cases Only": {
        "description": "Only rows with complete data are eligible.",
    },
    "Stress / Adverse Missing-Data Fill": {
        "description": "Stress tests missing-data handling with adverse fill assumptions.",
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


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


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
            return {str(key): _to_float(value) for key, value in parsed.items()}
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
            weights[key] = _to_float(value)

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
    weights = {str(key): _to_float(value) for key, value in dict(feature_weights or {}).items()}

    base_profile = {
        "intercept": _to_float(intercept, 0.5),
        "feature_weights": weights,
        "probability_floor": _to_float(probability_floor, 0.01),
        "probability_ceiling": _to_float(probability_ceiling, 0.99),
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
        "bets": _to_int(strategy_summary.get("bets")),
        "no_bets": _to_int(strategy_summary.get("no_bets")),
        "profit_loss": _to_float(strategy_summary.get("profit_loss")),
        "roi_percent": _to_float(strategy_summary.get("roi_percent")),
        "max_drawdown_percent": _to_float(strategy_summary.get("max_drawdown_percent")),
        "starting_bankroll": _to_float(strategy_summary.get("starting_bankroll")),
        "ending_bankroll": _to_float(strategy_summary.get("ending_bankroll")),
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
            profit_loss = _to_float(decision.get("profit_loss") or decision.get("pnl"))
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
                "bankroll": _to_float(bankroll_value),
                "profit_loss": _to_float(decision.get("profit_loss") or decision.get("pnl")),
                "model_probability": decision.get("model_probability"),
                "market_implied_probability": decision.get("market_implied_probability"),
                "edge": decision.get("edge"),
                "odds": decision.get("odds") or decision.get("recommended_odds"),
            }
        )

    return curve


__all__ = [
    "build_strategy_config_for_row",
    "build_strategy_config",
    "build_bankroll_curve_rows",
    "compact_counts",
    "describe_regression_profiles",
    "EASY_LABELS",
    "flatten_preview_rows",
    "filter_rows_for_profile",
    "get_available_profile_options",
    "get_regression_profile",
    "LEGACY_RISK_PRESET_ALIASES",
    "parse_feature_weights",
    "infer_strategy_profile_key_from_row",
    "REGRESSION_TACTICS",
    "RISK_PRESETS",
    "SAFE_DEFAULTS",
    "SCENARIO_BACKTEST_MODES",
    "row_matches_profile",
    "summarize_backtest_result",
    "normalize_strategy_profile_key",
]
