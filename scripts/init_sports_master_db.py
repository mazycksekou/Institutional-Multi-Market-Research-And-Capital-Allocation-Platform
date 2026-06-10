"""Initialize the local sports master SQLite database with mock NBA smoke data."""
from __future__ import annotations

import argparse
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.math_utils import implied_probability_to_american

DEFAULT_DB_PATH = Path("data") / "sports_master.db"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    sport_key TEXT NOT NULL,
    season INTEGER NOT NULL,
    event_date TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT NOT NULL,
    neutral_site INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS team_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    is_home INTEGER NOT NULL,
    rest_days REAL NOT NULL,
    elo_rating REAL NOT NULL,
    offensive_rating REAL NOT NULL,
    defensive_rating REAL NOT NULL,
    pace REAL NOT NULL,
    efg_pct REAL NOT NULL,
    turnover_pct REAL NOT NULL,
    rebound_pct REAL NOT NULL,
    free_throw_rate REAL NOT NULL,
    injury_impact REAL NOT NULL,
    travel_miles REAL NOT NULL,
    form_win_pct REAL NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS odds_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    market TEXT NOT NULL,
    sportsbook TEXT NOT NULL,
    selection TEXT NOT NULL,
    selection_team TEXT NOT NULL,
    price_american REAL NOT NULL,
    point REAL,
    sampled_at TEXT NOT NULL,
    is_closing INTEGER NOT NULL DEFAULT 0,
    line_source TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS model_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_key TEXT NOT NULL,
    market TEXT NOT NULL,
    model_version TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    summary_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    event_id TEXT NOT NULL,
    sport_key TEXT NOT NULL,
    market TEXT NOT NULL,
    prediction_time TEXT NOT NULL,
    selection TEXT NOT NULL,
    selection_team TEXT NOT NULL,
    event_date TEXT NOT NULL,
    price_american REAL NOT NULL,
    implied_probability REAL,
    no_vig_probability REAL,
    model_probability REAL,
    calibrated_probability REAL,
    edge REAL,
    ev REAL,
    stake REAL,
    label INTEGER,
    profit REAL,
    closing_price_american REAL,
    clv_percent REAL,
    fold INTEGER,
    status TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES model_runs(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE INDEX IF NOT EXISTS idx_events_sport_date ON events(sport_key, event_date);
CREATE INDEX IF NOT EXISTS idx_team_features_event_team ON team_features(event_id, team);
CREATE INDEX IF NOT EXISTS idx_odds_history_event_market_team ON odds_history(event_id, market, selection_team, is_closing);
CREATE INDEX IF NOT EXISTS idx_model_runs_sport_market ON model_runs(sport_key, market, model_version);
CREATE INDEX IF NOT EXISTS idx_model_predictions_run ON model_predictions(run_id);
CREATE INDEX IF NOT EXISTS idx_model_predictions_sport_market_date ON model_predictions(sport_key, market, event_date);
"""


def _bounded_probability(value: float) -> float:
    return max(0.08, min(0.92, value))


def _insert_mock_nba(conn: sqlite3.Connection, games: int = 120) -> None:
    rng = random.Random(20240609)
    teams = [
        "Atlanta Hawks",
        "Boston Celtics",
        "Chicago Bulls",
        "Dallas Mavericks",
        "Denver Nuggets",
        "Golden State Warriors",
        "Los Angeles Lakers",
        "Miami Heat",
        "Milwaukee Bucks",
        "New York Knicks",
        "Phoenix Suns",
        "Seattle Stormers",
    ]
    base = {}
    for index, team in enumerate(teams):
        base[team] = {
            "elo": 1450 + index * 14 + rng.uniform(-25, 25),
            "off": 109 + (index % 5) * 1.8 + rng.uniform(-2.2, 2.2),
            "def": 112 - (index % 4) * 1.4 + rng.uniform(-2.0, 2.0),
            "pace": 97 + (index % 6) * 0.9 + rng.uniform(-1.5, 1.5),
            "efg": 0.515 + (index % 5) * 0.006 + rng.uniform(-0.008, 0.008),
            "tov": 0.116 + (index % 4) * 0.006 + rng.uniform(-0.005, 0.005),
            "reb": 0.485 + (index % 6) * 0.006 + rng.uniform(-0.01, 0.01),
            "ftr": 0.205 + (index % 5) * 0.012 + rng.uniform(-0.01, 0.01),
        }

    last_played = {team: date(2023, 12, 24) for team in teams}
    wins = {team: 0 for team in teams}
    played = {team: 0 for team in teams}
    start = date(2024, 1, 1)

    for game_index in range(games):
        event_date = start + timedelta(days=game_index)
        away = teams[(game_index * 5 + 3) % len(teams)]
        home = teams[(game_index * 7 + 1) % len(teams)]
        if away == home:
            home = teams[(teams.index(home) + 1) % len(teams)]

        event_id = f"nba_mock_{game_index + 1:04d}"
        home_rest = max(0, (event_date - last_played[home]).days - 1)
        away_rest = max(0, (event_date - last_played[away]).days - 1)
        home_form = wins[home] / played[home] if played[home] else 0.5
        away_form = wins[away] / played[away] if played[away] else 0.5
        home_injury = max(0.0, rng.gauss(1.5, 1.0))
        away_injury = max(0.0, rng.gauss(1.7, 1.1))
        home_travel = rng.uniform(0, 450)
        away_travel = rng.uniform(250, 2200)

        home_strength = (
            (base[home]["elo"] - base[away]["elo"]) / 32.0
            + (base[home]["off"] - base[away]["def"]) * 0.20
            - (base[away]["off"] - base[home]["def"]) * 0.14
            + (home_rest - away_rest) * 0.45
            + (home_form - away_form) * 5.0
            - (home_injury - away_injury) * 0.55
            + 3.1
            + rng.gauss(0, 7.5)
        )
        home_score = int(round(112 + home_strength / 2 + rng.gauss(0, 5)))
        away_score = int(round(110 - home_strength / 2 + rng.gauss(0, 5)))
        if home_score == away_score:
            home_score += 1

        market_home_prob = _bounded_probability(1.0 / (1.0 + pow(2.718281828, -home_strength / 10.5)))
        opening_home_raw = _bounded_probability(market_home_prob * 1.035)
        opening_away_raw = _bounded_probability((1.0 - market_home_prob) * 1.035)
        home_won = home_score > away_score
        closing_shift = 0.018 if home_won else -0.018
        closing_home_prob = _bounded_probability(market_home_prob + closing_shift + rng.uniform(-0.012, 0.012))
        closing_home_raw = _bounded_probability(closing_home_prob * 1.028)
        closing_away_raw = _bounded_probability((1.0 - closing_home_prob) * 1.028)

        conn.execute(
            """
            INSERT INTO events (id, sport_key, season, event_date, home_team, away_team, home_score, away_score, status, neutral_site)
            VALUES (?, 'basketball_nba', 2024, ?, ?, ?, ?, ?, 'final', 0)
            """,
            (event_id, event_date.isoformat(), home, away, home_score, away_score),
        )

        for team, opponent, is_home, rest, injury, travel, form in [
            (home, away, 1, home_rest, home_injury, home_travel, home_form),
            (away, home, 0, away_rest, away_injury, away_travel, away_form),
        ]:
            rating = base[team]
            conn.execute(
                """
                INSERT INTO team_features (
                    event_id, team, opponent, is_home, rest_days, elo_rating, offensive_rating,
                    defensive_rating, pace, efg_pct, turnover_pct, rebound_pct, free_throw_rate,
                    injury_impact, travel_miles, form_win_pct
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    team,
                    opponent,
                    is_home,
                    float(rest),
                    rating["elo"] + rng.uniform(-8, 8),
                    rating["off"] + rng.uniform(-1.2, 1.2),
                    rating["def"] + rng.uniform(-1.2, 1.2),
                    rating["pace"] + rng.uniform(-0.8, 0.8),
                    rating["efg"] + rng.uniform(-0.006, 0.006),
                    rating["tov"] + rng.uniform(-0.004, 0.004),
                    rating["reb"] + rng.uniform(-0.006, 0.006),
                    rating["ftr"] + rng.uniform(-0.008, 0.008),
                    injury,
                    travel,
                    form,
                ),
            )

        odds_rows = [
            (home, opening_home_raw, 0, "mock_open", event_date - timedelta(days=1)),
            (away, opening_away_raw, 0, "mock_open", event_date - timedelta(days=1)),
            (home, closing_home_raw, 1, "mock_close", event_date),
            (away, closing_away_raw, 1, "mock_close", event_date),
        ]
        for team, probability, is_closing, source, sampled_at in odds_rows:
            conn.execute(
                """
                INSERT INTO odds_history (
                    event_id, market, sportsbook, selection, selection_team, price_american,
                    point, sampled_at, is_closing, line_source
                )
                VALUES (?, 'h2h', 'consensus', ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    event_id,
                    team,
                    team,
                    implied_probability_to_american(probability),
                    sampled_at.isoformat(),
                    is_closing,
                    source,
                ),
            )

        for team, won in [(home, home_score > away_score), (away, away_score > home_score)]:
            played[team] += 1
            if won:
                wins[team] += 1
            last_played[team] = event_date


def initialize_database(db_path: Path, *, reset: bool = False) -> dict[str, int | str]:
    if reset and db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        existing = conn.execute("SELECT COUNT(*) FROM events WHERE sport_key = 'basketball_nba'").fetchone()[0]
        if existing == 0:
            _insert_mock_nba(conn)
        conn.commit()
        events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        team_features = conn.execute("SELECT COUNT(*) FROM team_features").fetchone()[0]
        odds = conn.execute("SELECT COUNT(*) FROM odds_history").fetchone()[0]
    return {
        "db_path": str(db_path),
        "events": int(events),
        "team_features": int(team_features),
        "odds_history": int(odds),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize sports master SQLite DB.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite DB path.")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the DB before loading mock data.")
    args = parser.parse_args()

    summary = initialize_database(Path(args.db), reset=args.reset)
    print(summary)


if __name__ == "__main__":
    main()
