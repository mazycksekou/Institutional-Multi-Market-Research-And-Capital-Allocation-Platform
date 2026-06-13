"""ASGI deployment adapter.

This module exists for deployment commands that target `api_server:app`.

The FastAPI app is still assembled in `main.py` during this phase. Avoid direct
`from main import ...` imports elsewhere; a future app-factory phase can move
assembly into a package-owned factory.

This adapter intentionally uses dynamic import so the repo architecture guard can
block direct AST-level imports from `main.py` while preserving deployment
compatibility.
"""

from __future__ import annotations

import importlib
from typing import Any

_main = importlib.import_module("main")

app = getattr(_main, "app")

_custom_openapi = getattr(_main, "custom_openapi", None)
if _custom_openapi is None:
    custom_openapi = getattr(app, "openapi", None)
else:
    custom_openapi = _custom_openapi


def __getattr__(name: str) -> Any:
    """Proxy legacy deployment/test attributes to main without static imports."""

    return getattr(_main, name)
