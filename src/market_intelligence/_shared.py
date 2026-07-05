from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Iterable, Mapping


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not isfinite(parsed):
        return default
    return parsed


def clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    number = safe_float(value, low)
    if number is None:
        number = low
    return max(low, min(high, float(number)))


def compact_list(values: Iterable[Any] | None, *, limit: int = 10) -> list[Any]:
    items = list(values or [])
    cap = max(1, min(int(limit or 10), 100))
    return items[:cap]


def normalize_text(value: Any, *, default: str = "", lower: bool = True) -> str:
    text = str(value or default).strip()
    return text.lower() if lower else text


def build_text_summary(parts: Iterable[Any], *, separator: str = "; ", default: str = "none") -> str:
    values = [str(part).strip() for part in parts if str(part).strip()]
    return separator.join(values) if values else default


def weighted_average(parts: Iterable[tuple[Any, float]]) -> float | None:
    total = 0.0
    weight = 0.0
    for value, part_weight in parts:
        number = safe_float(value)
        if number is None or part_weight <= 0:
            continue
        total += number * part_weight
        weight += part_weight
    if weight <= 0:
        return None
    return total / weight


def build_band(value: Any, *, spread: float, low_label: str = "support", high_label: str = "resistance") -> list[dict[str, Any]]:
    number = safe_float(value)
    if number is None:
        return []
    width = abs(safe_float(spread, 0.0) or 0.0)
    return [
        {"label": low_label, "value": round(number - width, 4)},
        {"label": "mid", "value": round(number, 4)},
        {"label": high_label, "value": round(number + width, 4)},
    ]


@dataclass(frozen=True, slots=True)
class FlatReport:
    data: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return dict(self.data)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]


def as_plain_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict") and callable(getattr(value, "as_dict")):
        result = value.as_dict()
        if isinstance(result, Mapping):
            return dict(result)
    if hasattr(value, "__dict__"):
        try:
            return dict(asdict(value))
        except Exception:
            return dict(value.__dict__)
    return {}
