"""Strict chronological walk-forward backtester for sports moneyline models."""
from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from src.core.calibrator import IdentityCalibrator, PlattCalibrator
from src.core.clv import price_ratio_clv_percent as clv_percent
from src.core.math_utils import edge_percent, expected_value, profit_units
from src.sports.nba_features import build_training_rows, get_feature_columns

DEFAULT_DB_PATH = Path("data") / "sports_master.db"
DEFAULT_MODEL_DIR = Path("models") / "compressed"


class SimpleLogisticModel:
    """Small dependency-free logistic model fallback."""

    model_type = "simple_logistic_fallback"

    def __init__(self, learning_rate: float = 0.05, epochs: int = 350, l2: float = 0.0005) -> None:
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2
        self.weights: list[float] = []
        self.intercept = 0.0
        self.means: list[float] = []
        self.scales: list[float] = []

    def fit(self, x_rows: Sequence[Sequence[float]], y_rows: Sequence[int]) -> "SimpleLogisticModel":
        if not x_rows:
            self.weights = []
            self.intercept = 0.0
            return self

        width = len(x_rows[0])
        self.means = []
        self.scales = []
        for index in range(width):
            values = [float(row[index]) for row in x_rows]
            mean = sum(values) / len(values)
            variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
            scale = math.sqrt(variance) or 1.0
            self.means.append(mean)
            self.scales.append(scale)

        z_rows = [self._normalize(row) for row in x_rows]
        self.weights = [0.0] * width
        positive_rate = max(1e-4, min(1.0 - 1e-4, sum(int(y) for y in y_rows) / len(y_rows)))
        self.intercept = math.log(positive_rate / (1.0 - positive_rate))

        for _epoch in range(self.epochs):
            grad_w = [0.0] * width
            grad_b = 0.0
            for features, label in zip(z_rows, y_rows):
                pred = self._sigmoid(self.intercept + sum(w * x for w, x in zip(self.weights, features)))
                error = pred - int(label)
                grad_b += error
                for index, value in enumerate(features):
                    grad_w[index] += error * value + self.l2 * self.weights[index]

            n = float(len(z_rows))
            self.intercept -= self.learning_rate * grad_b / n
            for index in range(width):
                self.weights[index] -= self.learning_rate * grad_w[index] / n

        return self

    def predict_proba(self, x_rows: Sequence[Sequence[float]]) -> list[float]:
        probabilities = []
        for row in x_rows:
            features = self._normalize(row)
            score = self.intercept + sum(w * x for w, x in zip(self.weights, features))
            probabilities.append(max(1e-6, min(1.0 - 1e-6, self._sigmoid(score))))
        return probabilities

    def _normalize(self, row: Sequence[float]) -> list[float]:
        if not self.means:
            return [float(value) for value in row]
        return [
            (float(value) - self.means[index]) / self.scales[index]
            for index, value in enumerate(row)
        ]

    @staticmethod
    def _sigmoid(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)
        z = math.exp(value)
        return z / (1.0 + z)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_sport_name(sport_key: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in sport_key)


def model_artifact_path(
    sport_key: str,
    model_version: str = "v1",
    model_dir: str | Path = DEFAULT_MODEL_DIR,
) -> Path:
    return Path(model_dir) / f"{_safe_sport_name(sport_key)}_{model_version}.joblib"


def model_metadata_path(
    sport_key: str,
    model_version: str = "v1",
    model_dir: str | Path = DEFAULT_MODEL_DIR,
) -> Path:
    return Path(model_dir) / f"{_safe_sport_name(sport_key)}_{model_version}.metadata.json"


def _feature_vector(row: dict[str, Any], feature_columns: list[str]) -> list[float]:
    features = row.get("features") or {}
    return [float(features.get(name, 0.0)) for name in feature_columns]


def _fit_model(x_rows: Sequence[Sequence[float]], y_rows: Sequence[int]):
    labels = [int(value) for value in y_rows]
    if len(set(labels)) < 2:
        return SimpleLogisticModel().fit(x_rows, labels), "simple_logistic_fallback_single_class"

    try:
        from sklearn.linear_model import LogisticRegression, SGDClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except Exception:
        return SimpleLogisticModel().fit(x_rows, labels), "simple_logistic_fallback"

    try:
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=500, solver="lbfgs"),
        )
        model.fit(x_rows, labels)
        return model, "sklearn_logistic_regression"
    except Exception:
        try:
            model = make_pipeline(
                StandardScaler(),
                SGDClassifier(loss="log_loss", max_iter=1000, tol=1e-3),
            )
            model.fit(x_rows, labels)
            return model, "sklearn_sgd_log_loss"
        except Exception:
            return SimpleLogisticModel().fit(x_rows, labels), "simple_logistic_fallback"


def _predict_positive(model: Any, x_rows: Sequence[Sequence[float]]) -> list[float]:
    if hasattr(model, "predict_proba"):
        raw = model.predict_proba(x_rows)
        if isinstance(raw, list):
            return [float(value) for value in raw]
        return [float(value) for value in raw[:, 1]]
    decision = model.decision_function(x_rows)
    return [1.0 / (1.0 + math.exp(-float(value))) for value in decision]


def _fit_model_and_calibrator(
    x_rows: Sequence[Sequence[float]],
    y_rows: Sequence[int],
    *,
    min_train_rows: int,
) -> tuple[Any, Any, str]:
    labels = [int(value) for value in y_rows]
    if len(x_rows) < min_train_rows or len(set(labels)) < 2:
        model, model_type = _fit_model(x_rows, labels)
        return model, IdentityCalibrator("insufficient_training_sample").fit([], []), model_type

    split_index = max(min_train_rows, int(len(x_rows) * 0.8))
    if split_index >= len(x_rows) or len(set(labels[:split_index])) < 2 or len(set(labels[split_index:])) < 2:
        model, model_type = _fit_model(x_rows, labels)
        return model, IdentityCalibrator("insufficient_calibration_holdout").fit([], []), model_type

    calibration_base, _cal_model_type = _fit_model(x_rows[:split_index], labels[:split_index])
    calibration_scores = _predict_positive(calibration_base, x_rows[split_index:])
    calibrator = PlattCalibrator(min_samples=20, min_positive=3, min_negative=3).fit(
        calibration_scores,
        labels[split_index:],
    )
    model, model_type = _fit_model(x_rows, labels)
    return model, calibrator, model_type


def _save_bundle(path: Path, bundle: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import joblib

        joblib.dump(bundle, path, compress=3)
        return
    except Exception:
        pass

    with gzip.open(path, "wb") as handle:
        pickle.dump(bundle, handle)


def load_model_bundle(
    sport_key: str,
    model_version: str = "v1",
    model_dir: str | Path = DEFAULT_MODEL_DIR,
) -> dict[str, Any] | None:
    path = model_artifact_path(sport_key, model_version, model_dir)
    if not path.exists():
        return None

    try:
        import joblib

        return joblib.load(path)
    except Exception:
        with gzip.open(path, "rb") as handle:
            return pickle.load(handle)


def load_model_metadata(
    sport_key: str,
    model_version: str = "v1",
    model_dir: str | Path = DEFAULT_MODEL_DIR,
) -> dict[str, Any] | None:
    path = model_metadata_path(sport_key, model_version, model_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _insert_model_run(
    conn: sqlite3.Connection,
    *,
    sport_key: str,
    market: str,
    model_version: str,
    status: str,
    started_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO model_runs (sport_key, market, model_version, started_at, status, metadata_json, summary_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (sport_key, market, model_version, started_at, status, "{}", "{}"),
    )
    return int(cursor.lastrowid)


def _update_model_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    status: str,
    metadata: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    conn.execute(
        """
        UPDATE model_runs
           SET completed_at = ?, status = ?, metadata_json = ?, summary_json = ?
         WHERE id = ?
        """,
        (_now_iso(), status, json.dumps(metadata, sort_keys=True), json.dumps(summary, sort_keys=True), run_id),
    )


def _write_prediction(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    row: dict[str, Any],
    sport_key: str,
    market: str,
    model_probability: float,
    calibrated_probability: float,
    edge: float,
    ev: float,
    stake: float,
    profit: float,
    fold: int,
    status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO model_predictions (
            run_id, event_id, sport_key, market, prediction_time, selection, selection_team,
            event_date, price_american, implied_probability, no_vig_probability,
            model_probability, calibrated_probability, edge, ev, stake, label, profit,
            closing_price_american, clv_percent, fold, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            row.get("event_id"),
            sport_key,
            market,
            _now_iso(),
            row.get("selection"),
            row.get("selection_team"),
            row.get("event_date"),
            row.get("price_american"),
            row.get("implied_probability"),
            row.get("no_vig_probability"),
            model_probability,
            calibrated_probability,
            edge,
            ev,
            stake,
            row.get("label"),
            profit,
            row.get("closing_price_american"),
            row.get("clv_percent"),
            fold,
            status,
        ),
    )


def run_walk_forward_backtest(
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    sport_key: str = "basketball_nba",
    market: str = "h2h",
    start_year: int | None = None,
    min_edge: float = 0.01,
    model_version: str = "v1",
    model_dir: str | Path = DEFAULT_MODEL_DIR,
    min_train_rows: int = 40,
    stake: float = 100.0,
) -> dict[str, Any]:
    """Run strict chronological walk-forward validation and persist artifacts."""
    db_file = Path(db_path)
    if not db_file.exists():
        return {
            "ok": False,
            "status": "INSUFFICIENT_HISTORY",
            "message": f"Sports master DB not found at {db_file}.",
            "db_path": str(db_file),
        }

    if sport_key != "basketball_nba":
        return {
            "ok": False,
            "status": "INSUFFICIENT_HISTORY",
            "message": "Only basketball_nba is wired for this v1 feature registry.",
            "sport_key": sport_key,
        }

    started_at = _now_iso()
    feature_columns = get_feature_columns()
    start_date = f"{int(start_year)}-01-01" if start_year else None
    x_train: list[list[float]] = []
    y_train: list[int] = []
    rows_seen = 0
    scored_rows = 0
    qualified_bets = 0
    staked = 0.0
    profit = 0.0
    clv_values: list[float] = []
    model_type = "unfit"
    calibrator_metadata: dict[str, Any] = {}

    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        run_id = _insert_model_run(
            conn,
            sport_key=sport_key,
            market=market,
            model_version=model_version,
            status="running",
            started_at=started_at,
        )
        conn.commit()

        for row in build_training_rows(conn, start_date=start_date, market=market):
            rows_seen += 1
            features = _feature_vector(row, feature_columns)
            label = int(row["label"])

            if len(x_train) >= min_train_rows and len(set(y_train)) >= 2:
                model, calibrator, model_type = _fit_model_and_calibrator(
                    x_train,
                    y_train,
                    min_train_rows=min_train_rows,
                )
                model_probability = _predict_positive(model, [features])[0]
                calibrated_probability = calibrator.predict_proba([model_probability])[0]
                implied = float(row.get("implied_probability") or 0.5)
                edge = calibrated_probability - implied
                ev = expected_value(row["price_american"], calibrated_probability, stake=stake)
                qualifies = edge >= float(min_edge) and ev > 0
                prediction_status = "QUALIFIED" if qualifies else "NO_BET"
                row_clv = None
                if row.get("closing_price_american") is not None:
                    try:
                        row_clv = clv_percent(row["price_american"], row["closing_price_american"])
                    except Exception:
                        row_clv = None
                row["clv_percent"] = row_clv
                bet_profit = 0.0
                if qualifies:
                    qualified_bets += 1
                    staked += stake
                    bet_profit = profit_units(row["price_american"], stake) if label == 1 else -stake
                    profit += bet_profit
                    if row_clv is not None:
                        clv_values.append(row_clv)
                _write_prediction(
                    conn,
                    run_id=run_id,
                    row=row,
                    sport_key=sport_key,
                    market=market,
                    model_probability=model_probability,
                    calibrated_probability=calibrated_probability,
                    edge=edge,
                    ev=ev,
                    stake=stake if qualifies else 0.0,
                    profit=bet_profit,
                    fold=scored_rows + 1,
                    status=prediction_status,
                )
                scored_rows += 1

            x_train.append(features)
            y_train.append(label)

        status = "backtest_complete" if scored_rows > 0 else "INSUFFICIENT_HISTORY"
        roi = (profit / staked) if staked > 0 else 0.0
        avg_clv = sum(clv_values) / len(clv_values) if clv_values else None
        artifact_path = model_artifact_path(sport_key, model_version, model_dir)
        metadata_path = model_metadata_path(sport_key, model_version, model_dir)

        saved_artifact = False
        if len(x_train) >= min_train_rows and len(set(y_train)) >= 2:
            final_model, final_calibrator, model_type = _fit_model_and_calibrator(
                x_train,
                y_train,
                min_train_rows=min_train_rows,
            )
            calibrator_metadata = final_calibrator.metadata()
            bundle = {
                "sport_key": sport_key,
                "market": market,
                "model_version": model_version,
                "model": final_model,
                "calibrator": final_calibrator,
                "feature_columns": feature_columns,
                "model_type": model_type,
                "trained_at": _now_iso(),
            }
            _save_bundle(artifact_path, bundle)
            saved_artifact = True

        summary = {
            "ok": True,
            "status": status,
            "sport_key": sport_key,
            "market": market,
            "model_version": model_version,
            "rows_seen": rows_seen,
            "scored_rows": scored_rows,
            "qualified_bets": qualified_bets,
            "staked": round(staked, 2),
            "profit": round(profit, 2),
            "roi": round(roi, 6),
            "avg_clv_percent": round(avg_clv, 6) if avg_clv is not None else None,
            "min_edge": min_edge,
            "artifact_saved": saved_artifact,
            "artifact_path": str(artifact_path) if saved_artifact else None,
            "metadata_path": str(metadata_path) if saved_artifact else None,
            "note": "Mock or local historical data is for smoke validation only and is not a profitability claim.",
        }
        metadata = {
            "sport_key": sport_key,
            "market": market,
            "model_version": model_version,
            "feature_columns": feature_columns,
            "model_type": model_type,
            "trained_at": _now_iso(),
            "training_rows": rows_seen,
            "qualified_bets": qualified_bets,
            "roi": roi,
            "avg_clv_percent": avg_clv,
            "status": status,
            "min_edge": min_edge,
            "calibrator": calibrator_metadata,
            "python": os.sys.version.split()[0],
        }
        if saved_artifact:
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

        _update_model_run(conn, run_id, status=status, metadata=metadata, summary=summary)
        conn.commit()

    return summary
