"""NBA moneyline feature engineering.

This module intentionally avoids FastAPI, provider clients, Kelly sizing, and
schema creation. It only converts existing rows or live payloads into numeric
feature matrices.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from src.core.math_utils import american_to_implied_probability, strip_vig_two_way


FEATURE_COLUMNS = [
    "is_home",
    "rest_days",
    "elo_diff",
    "offensive_rating_diff",
    "defensive_rating_diff",
    "pace_diff",
    "efg_pct_diff",
    "turnover_pct_diff",
    "rebound_pct_diff",
    "free_throw_rate_diff",
    "injury_impact_diff",
    "travel_miles_diff",
    "form_win_pct_diff",
    "market_implied_probability",
    "book_count",
]


def _row_get(row: sqlite3.Row | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(row, sqlite3.Row):
        return row[key] if key in row.keys() else default
    return row.get(key, default)


def _float(row: sqlite3.Row | dict[str, Any], key: str, default: float = 0.0) -> float:
    value = _row_get(row, key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_feature_columns() -> list[str]:
    return list(FEATURE_COLUMNS)


def build_features_from_sql_row(row: sqlite3.Row | dict[str, Any]) -> dict[str, float]:
    """Build the canonical NBA feature dict from one SQL result row."""
    price = _row_get(row, "price_american")
    try:
        market_implied = american_to_implied_probability(price)
    except Exception:
        market_implied = _float(row, "market_implied_probability", 0.5)

    features = {
        "is_home": 1.0 if int(_float(row, "is_home", 0.0)) == 1 else 0.0,
        "rest_days": _float(row, "rest_days", 0.0),
        "elo_diff": _float(row, "elo_rating") - _float(row, "opponent_elo_rating"),
        "offensive_rating_diff": _float(row, "offensive_rating") - _float(row, "opponent_offensive_rating"),
        "defensive_rating_diff": _float(row, "opponent_defensive_rating") - _float(row, "defensive_rating"),
        "pace_diff": _float(row, "pace") - _float(row, "opponent_pace"),
        "efg_pct_diff": _float(row, "efg_pct") - _float(row, "opponent_efg_pct"),
        "turnover_pct_diff": _float(row, "opponent_turnover_pct") - _float(row, "turnover_pct"),
        "rebound_pct_diff": _float(row, "rebound_pct") - _float(row, "opponent_rebound_pct"),
        "free_throw_rate_diff": _float(row, "free_throw_rate") - _float(row, "opponent_free_throw_rate"),
        "injury_impact_diff": _float(row, "opponent_injury_impact") - _float(row, "injury_impact"),
        "travel_miles_diff": _float(row, "opponent_travel_miles") - _float(row, "travel_miles"),
        "form_win_pct_diff": _float(row, "form_win_pct") - _float(row, "opponent_form_win_pct"),
        "market_implied_probability": market_implied,
        "book_count": _float(row, "book_count", 1.0),
    }
    return {name: float(features.get(name, 0.0)) for name in FEATURE_COLUMNS}


def build_training_rows(
    conn: sqlite3.Connection,
    start_date: str | None = None,
    end_date: str | None = None,
    market: str = "h2h",
) -> Iterable[dict[str, Any]]:
    """Yield chronological NBA training rows with labels.

    The h2h label is 1 when the selected team wins the event.
    """
    conn.row_factory = sqlite3.Row
    params: list[Any] = [market, market, market]
    filters = ["e.sport_key = 'basketball_nba'", "e.status = 'final'"]
    if start_date:
        filters.append("e.event_date >= ?")
        params.append(start_date)
    if end_date:
        filters.append("e.event_date <= ?")
        params.append(end_date)

    sql = f"""
        SELECT
            e.id AS event_id,
            e.sport_key,
            e.event_date,
            e.home_team,
            e.away_team,
            e.home_score,
            e.away_score,
            tf.team AS selection_team,
            tf.opponent,
            tf.is_home,
            tf.rest_days,
            tf.elo_rating,
            tf.offensive_rating,
            tf.defensive_rating,
            tf.pace,
            tf.efg_pct,
            tf.turnover_pct,
            tf.rebound_pct,
            tf.free_throw_rate,
            tf.injury_impact,
            tf.travel_miles,
            tf.form_win_pct,
            opp.elo_rating AS opponent_elo_rating,
            opp.offensive_rating AS opponent_offensive_rating,
            opp.defensive_rating AS opponent_defensive_rating,
            opp.pace AS opponent_pace,
            opp.efg_pct AS opponent_efg_pct,
            opp.turnover_pct AS opponent_turnover_pct,
            opp.rebound_pct AS opponent_rebound_pct,
            opp.free_throw_rate AS opponent_free_throw_rate,
            opp.injury_impact AS opponent_injury_impact,
            opp.travel_miles AS opponent_travel_miles,
            opp.form_win_pct AS opponent_form_win_pct,
            oh.selection,
            oh.price_american,
            oh2.price_american AS opponent_price_american,
            close_oh.price_american AS closing_price_american,
            (
                SELECT COUNT(DISTINCT ohc.sportsbook)
                FROM odds_history ohc
                WHERE ohc.event_id = e.id
                  AND ohc.market = ?
                  AND ohc.selection_team = tf.team
                  AND ohc.is_closing = 0
            ) AS book_count
        FROM events e
        JOIN team_features tf ON tf.event_id = e.id
        JOIN team_features opp ON opp.event_id = e.id AND opp.team = tf.opponent
        JOIN odds_history oh
          ON oh.event_id = e.id
         AND oh.market = ?
         AND oh.selection_team = tf.team
         AND oh.is_closing = 0
        LEFT JOIN odds_history oh2
          ON oh2.event_id = e.id
         AND oh2.market = oh.market
         AND oh2.selection_team = tf.opponent
         AND oh2.is_closing = 0
         AND oh2.sportsbook = oh.sportsbook
        LEFT JOIN odds_history close_oh
          ON close_oh.event_id = e.id
         AND close_oh.market = ?
         AND close_oh.selection_team = tf.team
         AND close_oh.is_closing = 1
        WHERE {" AND ".join(filters)}
        ORDER BY e.event_date ASC, e.id ASC, tf.team ASC
    """

    cursor = conn.execute(sql, params)
    for row in cursor:
        team_score = row["home_score"] if row["selection_team"] == row["home_team"] else row["away_score"]
        opp_score = row["away_score"] if row["selection_team"] == row["home_team"] else row["home_score"]
        features = build_features_from_sql_row(row)

        no_vig = None
        if row["opponent_price_american"] is not None:
            try:
                side_a, _side_b = strip_vig_two_way(row["price_american"], row["opponent_price_american"])
                no_vig = side_a
            except Exception:
                no_vig = None

        yield {
            "event_id": row["event_id"],
            "sport_key": row["sport_key"],
            "event_date": row["event_date"],
            "market": market,
            "selection": row["selection"],
            "selection_team": row["selection_team"],
            "price_american": row["price_american"],
            "closing_price_american": row["closing_price_american"],
            "implied_probability": features["market_implied_probability"],
            "no_vig_probability": no_vig,
            "features": features,
            "label": 1 if team_score > opp_score else 0,
        }


def build_live_features_matrix(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a live feature matrix from The Odds API event payloads."""
    import numpy as np

    rows: list[dict[str, Any]] = []
    for event in data or []:
        h2h_prices: dict[str, list[dict[str, Any]]] = {}
        for bookmaker in event.get("bookmakers") or []:
            book_name = bookmaker.get("title") or bookmaker.get("key")
            for market in bookmaker.get("markets") or []:
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes") or []:
                    price = outcome.get("price")
                    if price is None:
                        continue
                    h2h_prices.setdefault(str(outcome.get("name")), []).append({
                        "book": book_name,
                        "price": price,
                    })

        if len(h2h_prices) < 2:
            continue

        for selection, offers in h2h_prices.items():
            best = max(offers, key=lambda item: float(item["price"]))
            try:
                market_implied = american_to_implied_probability(best["price"])
            except Exception:
                market_implied = 0.5

            features = {name: 0.0 for name in FEATURE_COLUMNS}
            features["is_home"] = 1.0 if selection == event.get("home_team") else 0.0
            features["market_implied_probability"] = market_implied
            features["book_count"] = float(len(offers))

            rows.append({
                "event_id": event.get("id"),
                "event": f"{event.get('away_team')} vs {event.get('home_team')}",
                "home_team": event.get("home_team"),
                "away_team": event.get("away_team"),
                "commence_time": event.get("commence_time"),
                "market": "h2h",
                "selection": selection,
                "selection_team": selection,
                "best_book": best.get("book"),
                "price_american": best.get("price"),
                "implied_probability": market_implied,
                "features": features,
            })

    matrix = np.asarray([[row["features"][name] for name in FEATURE_COLUMNS] for row in rows], dtype=float)
    return {
        "feature_columns": get_feature_columns(),
        "rows": rows,
        "matrix": matrix.tolist(),
    }
