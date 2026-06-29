from __future__ import annotations

def evaluate_walk_forward_gate(**kwargs):
    base = float(kwargs.get("rolling_window_performance", 0)) + float(kwargs.get("expanding_window_performance", 0)) + float(kwargs.get("regime_split_performance", 0))
    decay = float(kwargs.get("performance_decay", 0))
    sample = int(kwargs.get("sample_size", 0))
    score = max(0, min(100, (base / 3) - decay * 100 + (10 if sample >= 50 else -10)))
    return {**kwargs, "walk_forward_score": round(score, 2), "passes_gate": score >= 70}
