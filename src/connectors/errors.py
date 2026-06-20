from __future__ import annotations


class ConnectorError(RuntimeError):
    """Base error for scaffold-only connector boundaries."""


class ConnectorBoundaryError(ConnectorError):
    """Raised when a scaffold-only connector boundary is violated."""


class ConnectorConfigurationError(ConnectorError):
    """Raised when a connector contract is malformed."""


class ConnectorUnavailableError(ConnectorError):
    """Raised when a connector is intentionally unavailable."""


class ConnectorResponseError(ConnectorError):
    """Raised when a connector response contract is invalid."""
