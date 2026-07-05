from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI3_MODEL_MATURITY_REGISTRY_DECOUPLING.md",
    ROOT / "MODEL_MATURITY_REGISTRY_MIGRATION_MAP_AFTER_10K8ZI3.md",
    ROOT / "MODEL_MATURITY_REGISTRY_COMPATIBILITY_REPORT_AFTER_10K8ZI3.md",
    ROOT / "MODEL_MATURITY_REGISTRY_DELETE_READINESS_AFTER_10K8ZI3.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_docs_record_scheduler_decoupling_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "src.research.maturity",
        "scheduler-facing compatibility shim",
        "build_model_maturity_registry",
        "build_mdp_review_policy_scaffold",
    ]:
        assert fragment.lower() in text.lower()


def test_scheduler_registry_consumers_use_canonical_research(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    research = importlib.import_module("src.research")

    canonical = research.build_model_maturity_registry(total_labeled_outcomes=25)
    snapshot = research.build_model_maturity_registry(total_labeled_outcomes=25)
    mdp = research.build_mdp_review_policy_scaffold()

    assert snapshot["status"] == canonical["status"]
    assert snapshot["total_models"] == canonical["total_models"]
    assert mdp["model_family"] == "mdp_review_policy"
    assert mdp["execution_allowed"] is False


def test_scheduler_maturity_sources_are_safe() -> None:
    for name in [
        "src.research.maturity",
        "src.market_intelligence.feature_packs",
        "src.market_intelligence.manifold",
        "src.research.feature_control",
    ]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        assert ".model_maturity_registry" not in source, name
        for token in ["requests", "httpx", "yfinance", "playwright", "selenium", "openai", "anthropic"]:
            assert token not in source, f"{token} found in {name}"

