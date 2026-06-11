from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import Depends

from src.api.schemas.bet_csv import BetLogRequest
from src.services.bet_csv_service import BETS_FILE, append_bet, summarize_bets


def register_bet_csv_routes(
    app: Any,
    *,
    require_action_key: Any,
) -> None:
    """
    Register CSV-backed bet ledger routes.

    Canonical owner: src/api/bet_csv_routes.py
    """
    @app.post("/api/bets/log", operation_id="logBetCsv", dependencies=[Depends(require_action_key)])
    async def log_bet(payload: BetLogRequest):
        row = payload.model_dump()
        row["date"] = row["date"] or date.today().isoformat()
        BETS_FILE.parent.mkdir(exist_ok=True)
        exists = BETS_FILE.exists()
        with BETS_FILE.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if not exists:
                writer.writeheader()
            writer.writerow(row)
        return {"ok": True, "message": "Bet logged.", "logbook_row": row}


    @app.get("/api/bets/summary", operation_id="getBetSummary", dependencies=[Depends(require_action_key)])
    async def get_bet_summary():
        if not BETS_FILE.exists():
            return {"ok": True, "count": 0, "summary": {"message": "No bets logged yet."}, "records": []}
        df = pd.read_csv(BETS_FILE)
        if df.empty:
            return {"ok": True, "count": 0, "summary": {"message": "No bets logged yet."}, "records": []}
        profit_col = "profit_or_loss" if "profit_or_loss" in df.columns else "profit_loss"
        df["stake"] = pd.to_numeric(df.get("stake", 0), errors="coerce").fillna(0)
        df[profit_col] = pd.to_numeric(df.get(profit_col, 0), errors="coerce").fillna(0)
        total_staked = float(df["stake"].sum())
        total_profit = float(df[profit_col].sum())
        return {
            "ok": True,
            "count": int(len(df)),
            "summary": {
                "total_bets": int(len(df)),
                "total_staked": round(total_staked, 2),
                "total_profit": round(total_profit, 2),
                "roi_percent": round((total_profit / total_staked * 100) if total_staked else 0, 2),
            },
            "records": df.tail(25).to_dict(orient="records"),
        }
