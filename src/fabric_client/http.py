"""Async HTTP transport for Fabric API calls."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from fabric_client.exceptions import (
    AuthenticationError,
    FabricAPIError,
    NotFoundError,
    RateLimitError,
)

logger = logging.getLogger("fabric_client")

_DEFAULT_BASE_URL = "https://api.fabric.so/v2"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_RETRIES = 3


class FabricHTTP:
    """Low-level async HTTP client for the Fabric API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        workspace_id: str | None = None,
    ):
        headers: dict[str, str] = {"X-Api-Key": api_key}
        if workspace_id:
            headers["X-Fabric-Workspace-Id"] = workspace_id

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
        self._max_retries = max_retries

    async def close(self) -> None:
        await self._client.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def get_text(self, path: str) -> str:
        response = await self._request_raw("GET", path)
        return response.text

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def put_binary(
        self, url: str, data: bytes, headers: dict[str, str] | None = None
    ) -> None:
        """PUT binary data to an absolute URL (for presigned uploads)."""
        response = await self._client.put(url, content=data, headers=headers)
        response.raise_for_status()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = await self._request_raw(method, path, **kwargs)
        if not response.content:
            return None
        return response.json()

    async def _request_raw(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            logger.debug("%s %s (attempt %d)", method, path, attempt + 1)

            response = await self._client.request(method, path, **kwargs)
            status = response.status_code

            logger.debug("%s %s -> %d", method, path, status)

            if 200 <= status < 300:
                return response

            # Parse error body
            detail = ""
            try:
                body = response.json()
                detail = body.get("detail", "")
            except Exception:
                detail = response.text or ""

            # Non-retryable client errors
            if status == 404:
                raise NotFoundError(detail=detail or "not_found")
            if status == 429:
                retry_after = _parse_retry_after(response)
                raise RateLimitError(
                    detail=detail or "rate_limited", retry_after=retry_after
                )
            if status in (401, 403):
                raise AuthenticationError(detail=detail or "authentication_failed")
            if 400 <= status < 500:
                raise FabricAPIError(status_code=status, detail=detail)

            # 5xx -- retry with backoff
            last_error = FabricAPIError(status_code=status, detail=detail)
            if attempt < self._max_retries - 1:
                wait = 2**attempt * 0.1  # 0.1s, 0.2s, 0.4s
                logger.warning(
                    "%s %s returned %d, retrying in %.1fs", method, path, status, wait
                )
                await asyncio.sleep(wait)

        raise last_error  # type: ignore[misc]


def _parse_retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
