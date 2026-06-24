from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .contracts import PerformanceSummaryContract


def summarize_performance(
    returns: Iterable[float],
    *,
    label: str = "performance",
    metadata: dict[str, Any] | None = None,
) -> PerformanceSummaryContract:
    values = [float(value) for value in returns]
    if not values:
        raise ValueError("returns must not be empty.")

    sample_count = len(values)
    total_return = sum(values)
    average_return = total_return / sample_count
    win_count = sum(1 for value in values if value > 0)
    loss_count = sum(1 for value in values if value < 0)
    win_rate = win_count / sample_count
    return PerformanceSummaryContract(
        label=str(label).strip() or "performance",
        sample_count=sample_count,
        total_return=total_return,
        average_return=average_return,
        win_count=win_count,
        loss_count=loss_count,
        win_rate=win_rate,
        best_return=max(values),
        worst_return=min(values),
        metadata=dict(metadata or {}),
    )


def build_performance_summary(
    returns: Iterable[float],
    *,
    label: str = "performance",
    metadata: dict[str, Any] | None = None,
) -> PerformanceSummaryContract:
    return summarize_performance(returns, label=label, metadata=metadata)

