from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

import api_server as main

app = main.app
require_action_key = main.require_action_key


def _export_route_endpoints() -> None:
    for route in getattr(app, "routes", []):
        endpoint = getattr(route, "endpoint", None)
        name = getattr(endpoint, "__name__", None)
        if name and not name.startswith("_"):
            globals().setdefault(name, endpoint)


def _export_schema_models() -> None:
    try:
        import src.api.schemas as api_schemas
    except Exception:
        return

    for modinfo in pkgutil.iter_modules(api_schemas.__path__, api_schemas.__name__ + "."):
        try:
            module = importlib.import_module(modinfo.name)
        except Exception:
            continue

        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            if inspect.isclass(obj):
                globals().setdefault(name, obj)


_export_route_endpoints()
_export_schema_models()


def __getattr__(name: str) -> Any:
    _export_route_endpoints()
    _export_schema_models()

    if name in globals():
        return globals()[name]

    raise AttributeError(f"tests.support.action_imports does not expose {name!r}")
