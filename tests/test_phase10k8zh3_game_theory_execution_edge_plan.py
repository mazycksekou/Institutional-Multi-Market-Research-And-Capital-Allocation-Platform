from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

PLAN_DOCS = [
    ROOT / "PHASE10K8ZH3_GAME_THEORY_EXECUTION_EDGE_PLAN.md",
    ROOT / "GAME_THEORY_EXECUTION_OWNERSHIP_MAP_AFTER_10K8ZH3.md",
    ROOT / "MARKET_IMPACT_AND_SLIPPAGE_PLAN_AFTER_10K8ZH3.md",
    ROOT / "POSITION_ACCUMULATION_PLAN_AFTER_10K8ZH3.md",
]

CONCEPT_KEYWORDS = [
    "market impact",
    "slippage",
    "signalling risk",
    "adverse selection",
    "position accumulation",
    "order splitting",
    "liquidity-adjusted Kelly",
    "stop-loss",
    "thesis break",
    "exposure-aware sizing",
    "Bayesian update",
    "war of attrition",
    "limit-order",
    "liquidity-provider",
]

FUTURE_LOCATIONS = [
    "src/core/execution.py",
    "src/core/market_impact.py",
    "src/core/game_theory.py",
    "src/core/portfolio.py",
    "src/services/decision_engine.py",
]

FUTURE_DIRECTORIES = [
    "src/brokerage",
]


def test_plan_docs_exist() -> None:
    for path in PLAN_DOCS:
        assert path.exists(), path


def test_concepts_present() -> None:
    combined = "\n".join(
        p.read_text(encoding="utf-8") for p in PLAN_DOCS if p.exists()
    )
    for keyword in CONCEPT_KEYWORDS:
        assert keyword.lower() in combined.lower(), f"{keyword} missing"


def test_ownership_map_keeps_core() -> None:
    map_text = (ROOT / "GAME_THEORY_EXECUTION_OWNERSHIP_MAP_AFTER_10K8ZH3.md").read_text(
        encoding="utf-8"
    )
    for loc in FUTURE_LOCATIONS:
        assert loc in map_text, f"{loc} not in ownership map"


def test_no_implementation_files_created() -> None:
    # Ensure the future implementation files do not exist yet.
    for loc in FUTURE_LOCATIONS:
        path = ROOT / loc
        assert not path.exists(), f"Implementation file created prematurely: {path}"


def test_future_directories_are_scaffolds_only() -> None:
    for loc in FUTURE_DIRECTORIES:
        path = ROOT / loc
        assert path.exists(), f"Expected scaffold directory to exist: {path}"
        assert path.is_dir(), f"Expected directory scaffold, not file: {path}"


def test_no_connector_ownership_contamination() -> None:
    combined = "\n".join(
        p.read_text(encoding="utf-8") for p in PLAN_DOCS if p.exists()
    )
    assert "connectors" not in combined.lower()
    assert "providers" not in combined.lower()
