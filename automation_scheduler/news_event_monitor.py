from __future__ import annotations

from typing import Any


def _severity_to_score(severity: str) -> float:
    mapping = {"low": 0.3, "medium": 0.55, "high": 0.8, "critical": 0.95}
    return mapping.get(severity, 0.4)


def monitor_news_events(
    *,
    events: list[dict[str, Any]] | None,
    provider: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    candidates = []
    for event in events or []:
        if not isinstance(event, dict):
            continue
        severity = str(event.get("event_severity") or "medium").lower()
        severity_score = _severity_to_score(severity)
        candidates.append(
            {
                "source": "news_event_monitor",
                "provider": provider,
                "market_type": "news_events",
                "sport_or_symbol": event.get("sport_or_symbol") or event.get("symbol") or event.get("sport") or "news_item",
                "market": event.get("market", "news_event"),
                "selection": event.get("selection", event.get("headline", "event")),
                "odds_or_price": event.get("odds_or_price"),
                "movement": {"event_severity": severity},
                "movement_strength": severity_score * 10,
                "edge_percent": severity_score * 12,
                "confidence": 0.5 + (severity_score / 3),
                "liquidity": float(event.get("liquidity", 0.4) or 0.4),
                "data_quality": float(event.get("data_quality", 0.7) or 0.7),
                "market_depth": 0.35,
                "timing_signal": min(1.0, severity_score + 0.1),
                "model_fit": 0.45,
                "risk_level_numeric": 0.5,
                "volatility_percent": severity_score * 20,
                "source_consensus": float(event.get("source_consensus", 0.6) or 0.6),
                "execution_feasibility": 0.4,
                "expected_roi_percent": severity_score * 8,
                "reason": str(event.get("headline") or "News or event change requires review."),
                "event_severity": severity,
            }
        )
    return {"snapshot": {"provider": provider, "event_count": len(events or [])}, "candidates": candidates}
