from __future__ import annotations

from typing import Any, Mapping

from ._shared import compact_list


def build_catalysts_summary(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    catalysts = data.get("catalysts")
    if catalysts is None:
        catalysts = data.get("news_catalysts") or data.get("events") or []
    return {
        "catalysts": compact_list(catalysts, limit=10),
        "catalyst_summary": "; ".join(str(item).strip() for item in compact_list(catalysts, limit=4) if str(item).strip()) or "none",
    }

