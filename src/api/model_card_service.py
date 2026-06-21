from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from src.providers.provider_router import ProviderRouter


LIVE_CARD_STATUSES = {
    "NO_MODEL",
    "MODEL_METADATA_MISMATCH",
    "INSUFFICIENT_HISTORY",
    "NO_BET",
    "WATCHLIST",
    "MODEL_VALUE",
    "CONFIRMED_BACKTESTED_EDGE",
}


def _predict_model_probabilities(model: Any, matrix: list[list[float]]) -> list[float]:
    raw = model.predict_proba(matrix)
    if isinstance(raw, list):
        return [float(value) for value in raw]
    return [float(value) for value in raw[:, 1]]


class ModelCardService:
    """
    Canonical service for /model/live-card orchestration.

    The implementation below was extracted from main.py to keep the FastAPI
    route thin while preserving the existing response contract, no-model
    fallback, no-bet fallback, provider-router usage, feature construction,
    model scoring, and backtester metadata behavior.
    """

    def __init__(self, provider_router: ProviderRouter | None = None) -> None:
        self.provider_router = provider_router or ProviderRouter()

    async def assemble_live_card(
        self,
        sport: str = "basketball_nba",
        market: str = "h2h",
        min_edge: float = 0.01,
        regions: str = "us",
        odds_format: str = "american",
        limit: int = 25,
    ) -> Any:
        PROVIDER_ROUTER = self.provider_router
        from src.core.backtester import load_model_bundle, load_model_metadata
        from src.core.math_utils import edge_percent, expected_value
        from src.sports.nba_features import build_live_features_matrix, get_feature_columns

        model_version = "v1"
        bundle = load_model_bundle(sport, model_version=model_version)
        metadata = load_model_metadata(sport, model_version=model_version)
        if bundle is None or metadata is None:
            return {
                "ok": True,
                "status": "NO_MODEL",
                "sport": sport,
                "market": market,
                "message": "No local calibrated model artifact is available. Run /model/backtest first.",
            }

        expected_columns = get_feature_columns()
        mismatch_reasons = []
        if bundle.get("sport_key") != sport or metadata.get("sport_key") != sport:
            mismatch_reasons.append("sport_key")
        if bundle.get("market") != market or metadata.get("market") != market:
            mismatch_reasons.append("market")
        if list(bundle.get("feature_columns") or []) != expected_columns:
            mismatch_reasons.append("feature_columns")
        if mismatch_reasons:
            return {
                "ok": True,
                "status": "MODEL_METADATA_MISMATCH",
                "sport": sport,
                "market": market,
                "mismatch_reasons": mismatch_reasons,
            }

        if metadata.get("status") == "INSUFFICIENT_HISTORY" or int(metadata.get("training_rows") or 0) < 40:
            return {
                "ok": True,
                "status": "INSUFFICIENT_HISTORY",
                "sport": sport,
                "market": market,
                "training_rows": metadata.get("training_rows", 0),
                "message": "The model artifact exists but does not have enough historical training rows.",
            }

        payload = await PROVIDER_ROUTER.get_odds_events(
            "the_odds_api",
            sport,
            None,
            regions=regions,
            markets=market,
            odds_format=odds_format,
            limit=limit,
        )
        if not payload.get("ok"):
            if payload.get("error_type") == "PROVIDER_NOT_CONFIGURED":
                return {
                    "ok": True,
                    "status": "NO_BET",
                    "sport": sport,
                    "market": market,
                    "message": "Live odds provider is not configured.",
                }
            status_code = int(payload.get("status_code") or 500)
            content = {
                "ok": True,
                "status": "NO_BET",
                "provider": "The Odds API",
                "status_code": status_code,
                "error": str(payload.get("message") or "The Odds API provider request failed."),
            }
            if status_code >= 500:
                return JSONResponse(status_code=500, content=content)
            return JSONResponse(status_code=status_code, content=content)

        events = payload.get("raw_response") if isinstance(payload.get("raw_response"), list) else []
        if not events:
            return {
                "ok": True,
                "status": "NO_BET",
                "sport": sport,
                "market": market,
                "message": "No live odds events were returned.",
            }

        live_matrix = build_live_features_matrix(events)
        rows = live_matrix.get("rows") or []
        matrix = live_matrix.get("matrix") or []
        if not rows or not matrix:
            return {
                "ok": True,
                "status": "NO_BET",
                "sport": sport,
                "market": market,
                "events_checked": len(events),
                "cards": [],
                "message": "No live h2h rows were available for scoring.",
            }

        model = bundle["model"]
        calibrator = bundle.get("calibrator")
        model_probs = _predict_model_probabilities(model, matrix)
        calibrated_probs = calibrator.predict_proba(model_probs) if calibrator else model_probs

        qualified_bets = int(metadata.get("qualified_bets") or 0)
        historical_roi = float(metadata.get("roi") or 0.0)
        avg_clv = metadata.get("avg_clv_percent")
        avg_clv_value = float(avg_clv) if avg_clv is not None else None
        confirmation_ready = qualified_bets >= 500 and historical_roi > 0 and avg_clv_value is not None and avg_clv_value > 0

        cards = []
        for row, model_prob, calibrated_prob in zip(rows, model_probs, calibrated_probs):
            implied = float(row.get("implied_probability") or 0.5)
            edge = float(calibrated_prob) - implied
            ev = expected_value(row["price_american"], float(calibrated_prob), stake=100.0)
            if edge >= min_edge and ev > 0:
                status = "CONFIRMED_BACKTESTED_EDGE" if confirmation_ready else "MODEL_VALUE"
            elif edge > 0 or ev > 0:
                status = "WATCHLIST"
            else:
                status = "NO_BET"

            cards.append({
                "status": status,
                "event_id": row.get("event_id"),
                "event": row.get("event"),
                "market": market,
                "selection": row.get("selection"),
                "best_book": row.get("best_book"),
                "best_odds": row.get("price_american"),
                "model_probability": round(float(model_prob), 6),
                "calibrated_probability": round(float(calibrated_prob), 6),
                "implied_probability": round(implied, 6),
                "edge_percent": round(edge_percent(float(calibrated_prob), implied), 3),
                "ev_per_100": round(ev, 4),
                "confirmation_blockers": [] if status == "CONFIRMED_BACKTESTED_EDGE" else [
                    "requires_500_qualified_historical_model_bets_positive_roi_positive_avg_clv_current_positive_ev"
                ],
            })

        status_rank = {
            "CONFIRMED_BACKTESTED_EDGE": 6,
            "MODEL_VALUE": 5,
            "WATCHLIST": 4,
            "NO_BET": 3,
            "INSUFFICIENT_HISTORY": 2,
            "MODEL_METADATA_MISMATCH": 1,
            "NO_MODEL": 0,
        }
        top_status = max((card["status"] for card in cards), key=lambda value: status_rank[value]) if cards else "NO_BET"
        if top_status not in LIVE_CARD_STATUSES:
            top_status = "NO_BET"

        return {
            "ok": True,
            "status": top_status,
            "sport": sport,
            "market": market,
            "events_checked": len(events),
            "cards": sorted(cards, key=lambda item: item["ev_per_100"], reverse=True)[:50],
            "model_metadata": {
                "model_version": model_version,
                "training_rows": metadata.get("training_rows"),
                "qualified_bets": qualified_bets,
                "roi": historical_roi,
                "avg_clv_percent": avg_clv_value,
            },
            "note": "Live-card output is model research unless the status is CONFIRMED_BACKTESTED_EDGE.",
        }
