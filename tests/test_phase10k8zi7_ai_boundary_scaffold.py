from __future__ import annotations

import importlib
import inspect
import os

import pytest


def test_disabled_client_and_readiness_are_local_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )
    ai = importlib.reload(importlib.import_module("src.ai"))
    contracts = importlib.reload(importlib.import_module("src.ai.contracts"))
    policy_mod = importlib.reload(importlib.import_module("src.ai.prompt_policy"))
    disabled_mod = importlib.reload(importlib.import_module("src.ai.disabled_client"))
    readiness_mod = importlib.reload(importlib.import_module("src.ai.readiness"))

    prompt = contracts.build_prompt_metadata("red_team_prompt", "Assess the candidate locally only", variables=("candidate",))
    request = contracts.build_ai_request_descriptor("req-1", prompt.prompt_name, metadata={"lane": "audit"})
    validation = policy_mod.validate_prompt_metadata({"prompt_name": "red_team_prompt", "purpose": "Assess the candidate locally only"})
    readiness = readiness_mod.build_ai_readiness()

    client = disabled_mod.DisabledAIClient(reason="deferred")

    assert prompt.local_only is True
    assert request.local_only is True
    assert validation["ok"] is True
    assert validation["can_execute"] is False
    assert readiness["status"] == "deferred"
    assert readiness["enabled"] is False

    for method in [client.complete, client.chat, client.generate, client.embed, client.invoke, client.run, client.__call__]:
        with pytest.raises(disabled_mod.AIExecutionDisabledError):
            method("test")

    assert ai.build_ai_readiness()["status"] == "deferred"


def test_ai_prompt_policy_source_is_local_only() -> None:
    for name in ["src.ai", "src.ai.contracts", "src.ai.prompt_policy", "src.ai.disabled_client", "src.ai.readiness"]:
        module = importlib.import_module(name)
        source = inspect.getsource(module).lower()
        assert "src.connectors" not in source, name
        assert "os.getenv" not in source, name

