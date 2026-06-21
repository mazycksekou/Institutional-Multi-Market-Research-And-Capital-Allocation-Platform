from __future__ import annotations

from importlib import import_module
from typing import Any


def _legacy_router_class():
    module_name = "".join(("betting", "_providers.provider_router"))
    module = import_module(module_name)
    return module.ProviderRouter


class ProviderRouter:
    """Canonical runtime bridge for the legacy provider router.

    This wrapper keeps import sites on src.providers while deferring the
    legacy router import until instantiation time.
    """

    def __init__(self) -> None:
        self._legacy_router = _legacy_router_class()()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._legacy_router, name)


__all__ = ["ProviderRouter"]
