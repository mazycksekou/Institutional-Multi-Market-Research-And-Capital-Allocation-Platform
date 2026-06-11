from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

_BOOKMAKER_ALIASES = {
    "dk": "draftkings",
    "draft kings": "draftkings",
    "fanduel sportsbook": "fanduel",
    "fd": "fanduel",
    "bet mgm": "betmgm",
    "mgm": "betmgm",
    "caesar's": "caesars",
    "caesars sportsbook": "caesars",
}

_MARKET_ALIASES = {
    "h2h": "moneyline",
    "match winner": "moneyline",
    "winner": "moneyline",
    "spread": "spread",
    "point spread": "spread",
    "handicap": "spread",
    "total": "total",
    "totals": "total",
    "over under": "total",
    "player points": "player_points",
}

_SELECTION_ALIASES = {
    "o": "over",
    "u": "under",
}


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^\w\s.+-]", " ", lowered)
    lowered = re.sub(r"\b(fc|cf|sc|club|team)\b", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def normalize_bookmaker_name(name: Any) -> str:
    canonical = _slugify(str(name or ""))
    return _BOOKMAKER_ALIASES.get(canonical, canonical.replace(" ", "_"))


def normalize_entity_name(name: Any) -> str:
    canonical = _slugify(str(name or ""))
    canonical = canonical.replace(".", "")
    return canonical


def normalize_event_name(name: Any) -> str:
    text = str(name or "")
    if re.search(r"\b(?:vs|v|at)\b|@", text, re.IGNORECASE):
        parts = [
            normalize_entity_name(part)
            for part in re.split(r"\b(?:vs|v|at)\b|@", text, flags=re.IGNORECASE)
            if str(part).strip()
        ]
        return " vs ".join(sorted(parts))
    return _slugify(text)


def normalize_market_name(name: Any) -> str:
    canonical = _slugify(str(name or ""))
    return _MARKET_ALIASES.get(canonical, canonical.replace(" ", "_"))


def normalize_selection_name(name: Any) -> str:
    canonical = _slugify(str(name or ""))
    return _SELECTION_ALIASES.get(canonical, canonical)


def normalize_odds_value(odds: Any) -> int | float | None:
    if odds in (None, ""):
        return None
    if isinstance(odds, (int, float)):
        return int(odds) if float(odds).is_integer() else float(odds)
    text = str(odds).strip().replace(",", "")
    if text.startswith("+"):
        text = text[1:]
    return normalize_line_value(text)


def normalize_line_value(value: Any) -> int | float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
    else:
        text = str(value).strip().lower().replace("pk", "0").replace("pick", "0")
        numeric = float(text)
    return int(numeric) if float(numeric).is_integer() else float(numeric)


def normalize_timestamp(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    try:
        return int(float(text))
    except ValueError:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())


def normalize_offer(offer: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(offer)
    timestamp_source = offer.get("timestamp")
    if timestamp_source in (None, ""):
        timestamp_source = offer.get("odds_timestamp")
    if timestamp_source in (None, ""):
        timestamp_source = offer.get("last_update")
    normalized["bookmaker"] = normalize_bookmaker_name(offer.get("bookmaker") or offer.get("book"))
    normalized["event_name"] = normalize_event_name(offer.get("event_name") or offer.get("event"))
    normalized["participant"] = normalize_entity_name(offer.get("participant") or offer.get("team") or offer.get("player"))
    normalized["market"] = normalize_market_name(offer.get("market"))
    normalized["selection"] = normalize_selection_name(offer.get("selection"))
    normalized["odds"] = normalize_odds_value(offer.get("odds") if "odds" in offer else offer.get("odds_american"))
    normalized["line"] = normalize_line_value(offer.get("line"))
    normalized["timestamp"] = normalize_timestamp(timestamp_source)
    confidence = 0
    for key in ("bookmaker", "event_name", "market", "selection", "odds", "timestamp"):
        if normalized.get(key) not in (None, "", "unknown"):
            confidence += 16
    if normalized.get("line") is not None:
        confidence += 4
    normalized["normalization_confidence"] = max(0, min(100, confidence))
    return normalized
