from __future__ import annotations


class AIExecutionDisabledError(RuntimeError):
    """Raised when code tries to activate the deferred AI boundary."""


class DisabledAIClient:
    def __init__(self, *, reason: str = "ai_llm_deferred") -> None:
        self.reason = str(reason or "ai_llm_deferred")

    def _raise(self, action: str) -> None:
        raise AIExecutionDisabledError(f"{action} is disabled: {self.reason}")

    def complete(self, *_args, **_kwargs):
        self._raise("complete")

    def chat(self, *_args, **_kwargs):
        self._raise("chat")

    def generate(self, *_args, **_kwargs):
        self._raise("generate")

    def embed(self, *_args, **_kwargs):
        self._raise("embed")

    def invoke(self, *_args, **_kwargs):
        self._raise("invoke")

    def run(self, *_args, **_kwargs):
        self._raise("run")

    def __call__(self, *_args, **_kwargs):
        self._raise("call")
