from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import AttributionSummaryContract


def _coerce_component_pairs(
    components: Mapping[str, Any] | Iterable[tuple[str, Any]],
) -> tuple[tuple[str, float], ...]:
    if isinstance(components, Mapping):
        items = components.items()
    else:
        items = components
    cleaned: list[tuple[str, float]] = []
    for name, value in items:
        name_text = str(name).strip()
        if not name_text:
            continue
        cleaned.append((name_text, float(value)))
    return tuple(cleaned)


def summarize_attribution(
    components: Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    label: str = "attribution",
    total: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> AttributionSummaryContract:
    cleaned = _coerce_component_pairs(components)
    component_total = sum(value for _, value in cleaned)
    total_value = component_total if total is None else float(total)
    residual = total_value - component_total
    return AttributionSummaryContract(
        label=str(label).strip() or "attribution",
        components=cleaned,
        total=total_value,
        residual=residual,
        metadata=dict(metadata or {}),
    )


def build_attribution_summary(
    components: Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    label: str = "attribution",
    total: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> AttributionSummaryContract:
    return summarize_attribution(components, label=label, total=total, metadata=metadata)

