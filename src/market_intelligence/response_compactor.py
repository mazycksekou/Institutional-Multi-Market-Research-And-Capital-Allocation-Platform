from __future__ import annotations

import importlib
from typing import Any


LEGACY_PACKAGE = "src.automation_scheduler_legacy"


def _legacy_response_module_name(name: str) -> str | None:
    if name == "redact_and_limit_payload":
        return "response_compactor"
    if name.startswith("compact_") and name.endswith("_response"):
        return "response_compactor"
    return None


def __getattr__(name: str) -> Any:
    module_name = _legacy_response_module_name(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = importlib.import_module(f"{LEGACY_PACKAGE}.{module_name}")
    try:
        attr = getattr(module, name)
    except AttributeError as exc:  # pragma: no cover - legacy compatibility guard
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    globals()[name] = attr
    return attr


__all__ = [
    "compact_baseball_impact_diagnostics_response",
    "compact_golf_impact_diagnostics_response",
    "compact_hockey_impact_diagnostics_response",
    "compact_soccer_impact_diagnostics_response",
    "compact_combat_impact_diagnostics_response",
    "compact_tennis_impact_diagnostics_response",
    "redact_and_limit_payload",
]
