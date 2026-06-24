from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZI6_AI_LLM_BOUNDARY_AUDIT.md",
    ROOT / "AI_LLM_FILE_INVENTORY_AFTER_10K8ZI6.md",
    ROOT / "AI_LLM_CREDENTIAL_RISK_MAP_AFTER_10K8ZI6.md",
    ROOT / "AI_LLM_RUNTIME_RISK_MAP_AFTER_10K8ZI6.md",
    ROOT / "AI_LLM_DEFERRED_ACTIVATION_PLAN_AFTER_10K8ZI6.md",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_ai_inventory_docs_capture_requested_scope() -> None:
    text = "\n".join(_read(path) for path in DOCS)
    for fragment in [
        "src.ai",
        "automation_scheduler/deepseek_reviewer.py",
        "automation_scheduler/ai_provider_security.py",
        "src/api/automation_deepseek_routes.py",
        "config.py",
        "AI_CREDENTIAL_RISK",
        "AI_RUNTIME_CALL_RISK",
        "AI_PROMPT_TEMPLATE_ONLY",
        "MIGRATE_TO_SRC_AI_LATER",
        "UNSAFE_TO_TOUCH",
    ]:
        assert fragment.lower() in text.lower()


def test_src_ai_imports_without_env_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )
    for name in [
        "src.ai",
        "src.ai.contracts",
        "src.ai.prompt_policy",
        "src.ai.disabled_client",
        "src.ai.readiness",
    ]:
        module = importlib.reload(importlib.import_module(name))
        assert module is not None

    import src.ai as ai

    assert ai.build_ai_readiness()["status"] == "deferred"
    assert ai.validate_prompt_metadata({"prompt_name": "x", "purpose": "y"})["ok"] is True


def test_src_ai_sources_are_local_only() -> None:
    for name in ["src.ai", "src.ai.contracts", "src.ai.prompt_policy", "src.ai.disabled_client", "src.ai.readiness"]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        for token in ["requests", "httpx", "openai", "anthropic", "deepseek", "yfinance", "selenium", "playwright"]:
            assert token not in source, f"{token} found in {name}"

