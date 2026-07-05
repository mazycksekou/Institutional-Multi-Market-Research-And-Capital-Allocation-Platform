from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZHO_RESEARCH_FOUNDATION.md",
    ROOT / "RESEARCH_FOUNDATION_OWNERSHIP_MAP_AFTER_10K8ZHO.md",
    ROOT / "RESEARCH_LANE_MIGRATION_MAP_AFTER_10K8ZHO.md",
    ROOT / "RESEARCH_VALIDATION_REPORT_AFTER_10K8ZHO.md",
]
MODULES = [
    "src.research",
    "src.research.contracts",
    "src.research.lanes",
    "src.research.experiments",
    "src.research.ablation",
]
FORBIDDEN = [
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_research_docs_capture_foundation_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for phrase in [
        "PHASE 10K8ZHO",
        "src.research",
        "research-lane descriptors",
        "experiment metadata",
        "hypothesis tracking",
        "ablation planning",
        "non-live research scaffolds",
        "no AI/LLM calls",
        "no live data pull",
        "no external writes",
    ]:
        assert phrase.lower() in text.lower()


def test_research_modules_import_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    modules = [importlib.reload(importlib.import_module(name)) for name in MODULES]
    research = modules[0]

    for symbol in [
        "ResearchLaneDescriptor",
        "HypothesisRecord",
        "ExperimentMetadata",
        "AblationPlan",
        "build_research_lane_descriptor",
        "build_experiment_metadata",
        "build_hypothesis_record",
        "build_ablation_plan",
        "describe_ablation_plan",
        "list_research_lane_tags",
    ]:
        assert hasattr(research, symbol), symbol


def test_research_descriptors_can_be_created_locally() -> None:
    from src.research import (
        build_ablation_plan,
        build_experiment_metadata,
        build_hypothesis_record,
        build_research_lane_descriptor,
        describe_ablation_plan,
        list_research_lane_tags,
    )

    lane = build_research_lane_descriptor(
        "lane-1",
        "Calibration lane",
        topic="calibration",
        tags=("local", "deterministic"),
    )
    hypothesis = build_hypothesis_record(
        "hyp-1",
        lane.lane_id,
        "Local signals should remain deterministic.",
        evidence=("docs", "tests"),
    )
    experiment = build_experiment_metadata(
        "exp-1",
        lane.lane_id,
        "Verify local research scaffolds",
        hypothesis_id=hypothesis.hypothesis_id,
        parameters={"temperature": 0.0},
    )
    plan = build_ablation_plan(
        experiment.experiment_id,
        ("feature_a", "feature_b"),
        controls=("baseline",),
        metrics=("roi", "stability"),
    )

    assert lane.as_dict()["tags"] == ["local", "deterministic"]
    assert list_research_lane_tags(lane) == ("local", "deterministic")
    assert hypothesis.expected_direction == "unknown"
    assert experiment.hypothesis_id == "hyp-1"
    assert describe_ablation_plan(plan)["component_count"] == 2


def test_research_sources_do_not_import_network_or_connector_libraries() -> None:
    for name in MODULES:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        for token in FORBIDDEN:
            assert token not in source, f"{token} found in {name}"
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name

