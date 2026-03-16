"""Typed exceptions for Fabric API errors."""


class FabricError(Exception):
    """Base exception for all Fabric client errors."""


class FabricAPIError(FabricError):
    """HTTP error from the Fabric API."""

    def __init__(self, status_code: int, detail: str, message: str | None = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(message or f"Fabric API error {status_code}: {detail}")


class NotFoundError(FabricAPIError):
    """Resource not found (404)."""

    def __init__(self, detail: str = "not_found"):
        super().__init__(status_code=404, detail=detail)


class RateLimitError(FabricAPIError):
    """Rate limited (429)."""

    def __init__(self, detail: str = "rate_limited", retry_after: float | None = None):
        self.retry_after = retry_after
        super().__init__(status_code=429, detail=detail)


class AuthenticationError(FabricAPIError):
    """Authentication failed (401/403)."""

    def __init__(self, detail: str = "authentication_failed"):
        super().__init__(status_code=401, detail=detail)
