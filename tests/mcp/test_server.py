"""Tests for the Fabric MCP server."""

import httpx
import respx

from fabric_mcp.server import mcp


def test_server_has_correct_name():
    """Server instance exists with expected name."""
    assert mcp.name == "Fabric"


async def test_search_returns_results(mcp_client, base_url):
    """Search tool returns formatted results."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "total": 1,
                        "hasMore": False,
                        "hits": [
                            {
                                "id": "res-1",
                                "kind": "notepad",
                                "name": "Test Note",
                                "score": 0.95,
                                "tags": [],
                            }
                        ],
                    },
                )
            )
            result = await client.call_tool("search", {"query": "test"})

    assert len(result.content) > 0
    assert "Test Note" in result.content[0].text


async def test_search_empty_results(mcp_client, base_url):
    """Search with no matches returns informative message."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "total": 0,
                        "hasMore": False,
                        "hits": [],
                    },
                )
            )
            result = await client.call_tool("search", {"query": "nonexistent"})

    assert "No results found" in result.content[0].text


# --- Task 3: Resource Browsing Tools ---


async def test_list_roots(mcp_client, base_url):
    """List roots returns formatted root names and types."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/resource-roots").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "count": 2,
                        "data": {
                            "roots": [
                                {
                                    "id": "root-1",
                                    "type": "SYSTEM",
                                    "subtype": "inbox",
                                    "isPrivate": False,
                                    "createdAt": "2026-01-01",
                                    "modifiedAt": "2026-01-01",
                                    "folder": {
                                        "id": "f-1",
                                        "name": "Inbox",
                                        "isReadonly": True,
                                        "icon": None,
                                        "childrenCount": 5,
                                        "memberCount": 1,
                                    },
                                },
                                {
                                    "id": "root-2",
                                    "type": "SPACE",
                                    "subtype": None,
                                    "isPrivate": False,
                                    "createdAt": "2026-01-01",
                                    "modifiedAt": "2026-01-01",
                                    "folder": {
                                        "id": "f-2",
                                        "name": "Projects",
                                        "isReadonly": False,
                                        "icon": None,
                                        "childrenCount": 10,
                                        "memberCount": 1,
                                    },
                                },
                            ]
                        },
                    },
                )
            )
            result = await client.call_tool("list_roots", {})

    text = result.content[0].text
    assert "Inbox" in text
    assert "Projects" in text
    assert "SYSTEM" in text
    assert "SPACE" in text
    assert "inbox" in text  # subtype
    assert "root-1" in text
    assert "root-2" in text


async def test_list_roots_empty(mcp_client, base_url):
    """List roots with no roots returns informative message."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/resource-roots").mock(
                return_value=httpx.Response(
                    200,
                    json={"count": 0, "data": {"roots": []}},
                )
            )
            result = await client.call_tool("list_roots", {})

    assert "No roots found" in result.content[0].text


async def test_get_resource(mcp_client, base_url):
    """Get resource returns formatted resource details."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/resources/res-1").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "id": "res-1",
                        "kind": "bookmark",
                        "name": "Example",
                        "url": "https://example.com",
                        "createdAt": "2026-02-01",
                        "parentId": "folder-1",
                        "tags": [{"id": "t-1", "name": "important"}],
                    },
                )
            )
            result = await client.call_tool("get_resource", {"resource_id": "res-1"})

    text = result.content[0].text
    assert "Example" in text
    assert "bookmark" in text
    assert "res-1" in text
    assert "https://example.com" in text
    assert "important" in text
    assert "2026-02-01" in text
    assert "folder-1" in text


async def test_list_resources(mcp_client, base_url):
    """List resources returns formatted resource listing."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/resources/filter").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "total": 2,
                        "hasMore": True,
                        "nextCursor": "abc",
                        "resources": [
                            {
                                "id": "res-1",
                                "kind": "notepad",
                                "name": "Note 1",
                                "tags": [],
                            },
                            {
                                "id": "res-2",
                                "kind": "bookmark",
                                "name": "Bookmark 1",
                                "url": "https://example.com",
                                "tags": [],
                            },
                        ],
                    },
                )
            )
            result = await client.call_tool(
                "list_resources", {"kind": ["notepad", "bookmark"]}
            )

    text = result.content[0].text
    assert "Note 1" in text
    assert "Bookmark 1" in text
    assert "notepad" in text
    assert "bookmark" in text
    assert "https://example.com" in text
    assert "More results available" in text


async def test_list_resources_empty(mcp_client, base_url):
    """List resources with no matches returns informative message."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/resources/filter").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "total": 0,
                        "hasMore": False,
                        "nextCursor": None,
                        "resources": [],
                    },
                )
            )
            result = await client.call_tool("list_resources", {})

    assert "No resources found" in result.content[0].text


async def test_list_tags(mcp_client, base_url):
    """List tags returns formatted tag names and IDs."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/tags").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "count": 2,
                        "data": {
                            "tags": [
                                {
                                    "id": "t-1",
                                    "userId": "u-1",
                                    "name": "important",
                                    "description": None,
                                },
                                {
                                    "id": "t-2",
                                    "userId": "u-1",
                                    "name": "project",
                                    "description": "Work projects",
                                },
                            ]
                        },
                    },
                )
            )
            result = await client.call_tool("list_tags", {})

    text = result.content[0].text
    assert "important" in text
    assert "project" in text
    assert "t-1" in text
    assert "t-2" in text


async def test_list_tags_empty(mcp_client, base_url):
    """List tags with no tags returns informative message."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/tags").mock(
                return_value=httpx.Response(
                    200,
                    json={"count": 0, "data": {"tags": []}},
                )
            )
            result = await client.call_tool("list_tags", {})

    assert "No tags found" in result.content[0].text


# --- Task 4: Notepad Content Tool ---


async def test_get_notepad_content(mcp_client, base_url):
    """Get notepad content returns the plain text content."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/notepads/note-1/content").mock(
                return_value=httpx.Response(
                    200,
                    text="# Title\nBody text here",
                    headers={"Content-Type": "text/plain"},
                )
            )
            result = await client.call_tool(
                "get_notepad_content", {"resource_id": "note-1"}
            )

    text = result.content[0].text
    assert "# Title" in text
    assert "Body text here" in text


async def test_get_notepad_content_empty(mcp_client, base_url):
    """Get notepad content for empty notepad returns placeholder."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/notepads/note-1/content").mock(
                return_value=httpx.Response(
                    200,
                    text="",
                    headers={"Content-Type": "text/plain"},
                )
            )
            result = await client.call_tool(
                "get_notepad_content", {"resource_id": "note-1"}
            )

    assert "(empty notepad)" in result.content[0].text


# --- Task 5: Content Creation Tools ---


async def test_create_bookmark(mcp_client, base_url):
    """Create bookmark returns confirmation with resource name and ID."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/bookmarks").mock(
                return_value=httpx.Response(
                    201,
                    json={
                        "id": "bm-1",
                        "kind": "bookmark",
                        "name": "Example Site",
                        "url": "https://example.com",
                        "tags": [],
                    },
                )
            )
            result = await client.call_tool(
                "create_bookmark",
                {
                    "url": "https://example.com",
                    "parent_id": "@alias::inbox",
                    "name": "Example Site",
                    "tags": ["web"],
                },
            )

    text = result.content[0].text
    assert "Bookmark created" in text
    assert "Example Site" in text
    assert "bm-1" in text


async def test_create_notepad(mcp_client, base_url):
    """Create notepad returns confirmation with resource name and ID."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/notepads").mock(
                return_value=httpx.Response(
                    201,
                    json={
                        "id": "np-1",
                        "kind": "notepad",
                        "name": "My Note",
                        "tags": [],
                    },
                )
            )
            result = await client.call_tool(
                "create_notepad",
                {
                    "parent_id": "@alias::inbox",
                    "name": "My Note",
                    "text": "Hello world",
                },
            )

    text = result.content[0].text
    assert "Notepad created" in text
    assert "My Note" in text
    assert "np-1" in text


async def test_create_folder(mcp_client, base_url):
    """Create folder returns confirmation with resource name and ID."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/folders").mock(
                return_value=httpx.Response(
                    201,
                    json={
                        "id": "fold-1",
                        "kind": "folder",
                        "name": "Projects",
                        "tags": [],
                    },
                )
            )
            result = await client.call_tool(
                "create_folder",
                {"parent_id": "root-1", "name": "Projects"},
            )

    text = result.content[0].text
    assert "Folder created" in text
    assert "Projects" in text
    assert "fold-1" in text


# --- Task 6: Delete Resources Tool ---


async def test_delete_resources(mcp_client, base_url):
    """Delete resources returns confirmation with count."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/resources/delete").mock(
                return_value=httpx.Response(204)
            )
            result = await client.call_tool(
                "delete_resources",
                {"resource_ids": ["res-1", "res-2"]},
            )

    text = result.content[0].text
    assert "Deleted" in text
    assert "2" in text


async def test_delete_resources_archive(mcp_client, base_url):
    """Archive resources returns archive-specific confirmation."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/resources/delete").mock(
                return_value=httpx.Response(204)
            )
            result = await client.call_tool(
                "delete_resources",
                {"resource_ids": ["res-1"], "archive": True},
            )

    text = result.content[0].text
    assert "Archived" in text
    assert "1" in text


# --- Task 7: Error Handling ---


async def test_get_resource_not_found(mcp_client, base_url):
    """404 from Fabric API returns helpful error, not server crash."""
    async with mcp_client() as client:
        with respx.mock:
            respx.get(f"{base_url}/resources/bad-id").mock(
                return_value=httpx.Response(404, json={"detail": "resource_not_found"})
            )
            result = await client.call_tool("get_resource", {"resource_id": "bad-id"})
    assert result.isError
    assert "not found" in result.content[0].text.lower()


async def test_search_auth_error(mcp_client, base_url):
    """401 from Fabric API returns auth error message."""
    async with mcp_client() as client:
        with respx.mock:
            respx.post(f"{base_url}/search").mock(
                return_value=httpx.Response(401, json={"detail": "unauthorized"})
            )
            result = await client.call_tool("search", {"query": "test"})
    assert result.isError
    assert "auth" in result.content[0].text.lower()
