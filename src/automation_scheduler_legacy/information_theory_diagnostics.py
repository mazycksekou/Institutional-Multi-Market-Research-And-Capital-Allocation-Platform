from __future__ import annotations

import math
from typing import Any, Mapping

from src.security.policy import locked_safety_flags


def _num(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _label(row: Mapping[str, Any]) -> int | None:
    value = row.get("outcome", row.get("final_outcome", row.get("label")))
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"yes", "win", "true", "1", "profitable"}:
            return 1
        if text in {"no", "loss", "false", "0", "losing"}:
            return 0
    parsed = _num(value)
    if parsed is None:
        return None
    return 1 if parsed >= 0.5 else 0


def _feature(row: Mapping[str, Any]) -> float | None:
    for key in ("signal", "score", "edge", "edge_estimate", "review_priority_score", "confidence_score", "implied_probability"):
        value = _num(row.get(key))
        if value is not None:
            return value
    return None


def _bin(value: float, cuts: list[float]) -> int:
    for index, cut in enumerate(cuts):
        if value <= cut:
            return index
    return len(cuts)


def _mutual_information(pairs: list[tuple[int, int]]) -> float:
    if not pairs:
        return 0.0
    n = len(pairs)
    px: dict[int, int] = {}
    py: dict[int, int] = {}
    pxy: dict[tuple[int, int], int] = {}
    for x, y in pairs:
        px[x] = px.get(x, 0) + 1
        py[y] = py.get(y, 0) + 1
        pxy[(x, y)] = pxy.get((x, y), 0) + 1
    mi = 0.0
    for (x, y), count in pxy.items():
        p_joint = count / n
        mi += p_joint * math.log(max(1e-12, p_joint / ((px[x] / n) * (py[y] / n))), 2)
    return max(0.0, min(1.0, mi))


def run_information_theory_diagnostics(
    *,
    records: list[Mapping[str, Any]] | None = None,
    candidate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = candidate or {}
    if candidate.get("mutual_information_score") is not None or candidate.get("transfer_entropy_score") is not None:
        mi = max(0.0, min(1.0, float(candidate.get("mutual_information_score") or 0.0)))
        te = max(0.0, min(1.0, float(candidate.get("transfer_entropy_score") or 0.0)))
    else:
        rows = [row for row in (records or []) if isinstance(row, Mapping)]
        values = [(_feature(row), _label(row)) for row in rows]
        values = [(float(x), int(y)) for x, y in values if x is not None and y is not None]
        if len(values) < 8:
            mi = 0.0
            te = 0.0
        else:
            xs = [x for x, _ in values]
            cuts = sorted(xs)[max(1, len(xs) // 3) - 1 : len(xs) : max(1, len(xs) // 3)][:2]
            mi = _mutual_information([(_bin(x, cuts), y) for x, y in values])
            lagged = [(_bin(values[i - 1][0], cuts), values[i][1]) for i in range(1, len(values))]
            te = max(0.0, min(1.0, _mutual_information(lagged) * 0.5))
    fake = mi >= 0.25 and te < 0.05
    return {
        "ok": True,
        "status": "information_theory_complete",
        "mutual_information_score": round(mi, 6),
        "transfer_entropy_score": round(te, 6),
        "redundancy_score": round(max(0.0, mi - te), 6),
        "nonlinear_dependence_detected": mi >= 0.15,
        "predictive_flow_detected": te >= 0.05,
        "fake_edge_information_risk": bool(fake),
        "information_theory_status": "static_correlation_not_predictive" if fake else "diagnostic_complete",
        "information_no_bet_reasons": ["static_correlation_not_predictive", "fake_edge_risk"] if fake else [],
        "red_team_only": True,
        **locked_safety_flags(),
    }
