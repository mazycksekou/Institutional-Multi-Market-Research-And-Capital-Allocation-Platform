from __future__ import annotations

from typing import Any


DERIVED_FEATURE_SPECS: dict[str, dict[str, Any]] = {
    "final_margin": {"fields": ["points_for", "points_against"], "history": 1},
    "total_points": {"fields": ["points_for", "points_against"], "history": 1},
    "winner": {"fields": ["points_for", "points_against"], "history": 1},
    "rolling_points_for": {"fields": ["points_for"], "history": 3},
    "rolling_points_against": {"fields": ["points_against"], "history": 3},
    "rolling_margin": {"fields": ["points_for", "points_against"], "history": 3},
    "rolling_win_rate": {"fields": ["result"], "history": 3},
    "home_away_split": {"fields": ["home_away", "result"], "history": 3},
    "rest_days": {"fields": ["event_date", "participant"], "history": 2},
    "simple_rating": {"fields": ["rolling_margin"], "history": 3},
    "opponent_adjusted_margin": {"fields": ["margin", "opponent_strength"], "history": 3},
    "volatility": {"fields": ["margin"], "history": 5},
    "close_game_rate": {"fields": ["margin"], "history": 5},
    "market_implied_probability": {"fields": ["odds"], "history": 1},
    "prediction_market_outcome": {"fields": ["settlement_result"], "history": 1},
    "rolling_return": {"fields": ["return"], "history": 5},
    "rolling_volume": {"fields": ["volume"], "history": 5},
    "drawdown": {"fields": ["close_price"], "history": 5},
    "trend": {"fields": ["close_price"], "history": 5},
}

FIELD_EXPANSIONS = {
    "home_points": {"home_points", "points_for", "home_score"},
    "away_points": {"away_points", "points_against", "away_score"},
    "home_score": {"home_score", "points_for", "home_points"},
    "away_score": {"away_score", "points_against", "away_points"},
    "final_score": {"final_score", "points_for", "points_against", "result"},
    "final_result": {"final_result", "result", "winner"},
    "winner": {"winner", "result"},
    "moneyline": {"moneyline", "odds"},
    "spread": {"spread", "odds"},
    "total": {"total", "odds"},
    "market_price": {"market_price", "odds"},
    "prediction_market_price": {"prediction_market_price", "market_price", "odds"},
    "settlement": {"settlement", "settlement_result"},
    "final_outcome": {"final_outcome", "settlement_result", "result"},
    "close": {"close", "close_price", "price"},
    "final_price": {"final_price", "close_price", "return"},
    "historical_prices": {"historical_prices", "close_price", "return"},
    "timestamp": {"timestamp", "event_date", "date"},
    "date": {"date", "event_date"},
    "team": {"team", "participant"},
    "teams": {"teams", "participant"},
    "player": {"player", "participant"},
    "fighter": {"fighter", "participant"},
}

PLACEHOLDER_VALUES = {"", "n/a", "na", "none", "null", "unknown", "tbd", "placeholder"}


def _expand_fields(fields: set[str] | list[str] | tuple[str, ...]) -> set[str]:
    expanded: set[str] = set()
    for field in fields:
        key = str(field or "").strip()
        if not key:
            continue
        expanded.add(key)
        expanded.update(FIELD_EXPANSIONS.get(key, set()))
    return expanded


def _real_value(value: Any) -> bool:
    if value in (None, [], {}):
        return False
    if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_VALUES:
        return False
    return True


def _fields_from_history(history_rows: list[dict[str, Any]]) -> set[str]:
    fields: set[str] = set()
    for row in history_rows:
        if not isinstance(row, dict):
            continue
        for key, value in row.items():
            if _real_value(value):
                fields.add(str(key))
    return _expand_fields(fields)


def _usable_history_count(history_rows: list[dict[str, Any]], needed_fields: list[str]) -> int:
    if not history_rows:
        return 0
    count = 0
    expanded_needed = _expand_fields(needed_fields)
    for row in history_rows:
        if not isinstance(row, dict):
            continue
        row_fields = _fields_from_history([row])
        if expanded_needed.issubset(row_fields):
            count += 1
    return count


def plan_derived_features(
    *,
    available_fields: list[str] | set[str] | tuple[str, ...],
    history_rows: list[dict[str, Any]] | None = None,
    requested_features: list[str] | None = None,
    module: str | None = None,
) -> dict[str, Any]:
    rows = [row for row in (history_rows or []) if isinstance(row, dict)]
    available = _expand_fields(set(available_fields or [])) | _fields_from_history(rows)
    feature_names = list(requested_features or DERIVED_FEATURE_SPECS.keys())
    features: list[dict[str, Any]] = []

    for name in feature_names:
        spec = DERIVED_FEATURE_SPECS.get(name)
        if not spec:
            features.append(
                {
                    "feature": name,
                    "fields_needed": [],
                    "fields_available": sorted(available),
                    "required_history_length": 0,
                    "available_history_length": len(rows),
                    "derivation_status": "unknown_derived_feature",
                }
            )
            continue
        needed = list(spec["fields"])
        expanded_needed = _expand_fields(needed)
        present = sorted(expanded_needed & available)
        missing = sorted(expanded_needed - available)
        required_history = int(spec.get("history") or 1)
        usable_history = _usable_history_count(rows, needed)
        if missing:
            status = "missing_required_fields"
        elif required_history > 1 and usable_history < required_history:
            status = "insufficient_history_for_derived_feature"
        else:
            status = "derivable"
        features.append(
            {
                "feature": name,
                "fields_needed": needed,
                "fields_available": present,
                "missing_fields": missing,
                "required_history_length": required_history,
                "available_history_length": usable_history if rows else 0,
                "derivation_status": status,
            }
        )

    return {
        "ok": True,
        "status": "ok",
        "module": module,
        "features": features,
        "derived_features_available": [row["feature"] for row in features if row["derivation_status"] == "derivable"],
        "derived_features_blocked": [
            {"feature": row["feature"], "reason": row["derivation_status"]}
            for row in features
            if row["derivation_status"] != "derivable"
        ],
        "raw_payload_included": False,
        "secrets_included": False,
    }

