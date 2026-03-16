"""MCP test fixtures.

MCP tests manage the server/client lifecycle within each test body
(via an async context manager fixture) rather than using an async
generator fixture. This avoids a pytest-asyncio issue where fixture
teardown runs in a different asyncio Task, which breaks anyio's
cancel scope tracking inside the MCP server.
"""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import pytest

from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from fabric_mcp.server import mcp as mcp_app

# Ensure FABRIC_API_KEY is set for FabricClient in lifespan
os.environ.setdefault("FABRIC_API_KEY", "test-key-for-mcp-tests")

BASE_URL = "https://api.fabric.so/v2"


@asynccontextmanager
async def _connected_client() -> AsyncIterator[ClientSession]:
    """Create an in-process MCP client session connected to the Fabric server."""
    async with create_connected_server_and_client_session(mcp_app) as client:
        yield client


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def mcp_client():
    """Async context manager for an in-process MCP client.

    Usage in tests::

        async def test_example(mcp_client):
            async with mcp_client() as client:
                result = await client.call_tool("tool_name", {"arg": "value"})

    Returns a factory (async context manager) instead of yielding a client
    directly, so setup and teardown happen in the same asyncio Task.
    """
    return _connected_client
