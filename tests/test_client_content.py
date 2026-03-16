import json

import httpx
import pytest
import respx

from fabric_client.client import FabricClient
from fabric_client.models import PaginatedResponse, SearchHit


@pytest.fixture
def client(api_key, base_url):
    return FabricClient(api_key=api_key, base_url=base_url)


@respx.mock
async def test_search(client, base_url):
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
                        "name": "Note",
                        "score": 0.9,
                        "tags": [],
                    }
                ],
            },
        )
    )
    page = await client.search("my query", limit=5)
    assert isinstance(page, PaginatedResponse)
    assert page.total == 1
    assert len(page.items) == 1
    assert isinstance(page.items[0], SearchHit)
    assert page.items[0].score == 0.9


@respx.mock
async def test_search_sends_hybrid_mode(client, base_url):
    route = respx.post(f"{base_url}/search").mock(
        return_value=httpx.Response(
            200, json={"total": 0, "hasMore": False, "hits": []}
        )
    )
    await client.search("test query")
    body = json.loads(route.calls[0].request.content)
    assert body["mode"] == "hybrid"
    assert body["text"] == "test query"


@respx.mock
async def test_create_bookmark(client, base_url):
    route = respx.post(f"{base_url}/bookmarks").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "bm-1",
                "kind": "bookmark",
                "name": "Example",
                "url": "https://example.com",
                "tags": [],
            },
        )
    )
    resource = await client.create_bookmark(
        url="https://example.com",
        parent_id="@alias::inbox",
        name="Example",
        tags=[{"name": "web"}],
    )
    assert resource.id == "bm-1"
    body = json.loads(route.calls[0].request.content)
    assert body["url"] == "https://example.com"
    assert body["parentId"] == "@alias::inbox"
    assert body["tags"] == [{"name": "web"}]


@respx.mock
async def test_create_notepad(client, base_url):
    route = respx.post(f"{base_url}/notepads").mock(
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
    resource = await client.create_notepad(
        parent_id="@alias::inbox",
        name="My Note",
        text="Hello world",
    )
    assert resource.id == "np-1"
    body = json.loads(route.calls[0].request.content)
    assert body["parentId"] == "@alias::inbox"
    assert body["text"] == "Hello world"


@respx.mock
async def test_get_notepad_content(client, base_url):
    respx.get(f"{base_url}/notepads/np-1/content").mock(
        return_value=httpx.Response(
            200, text="# Title\nBody text", headers={"Content-Type": "text/plain"}
        )
    )
    content = await client.get_notepad_content("np-1")
    assert content == "# Title\nBody text"


@respx.mock
async def test_create_folder(client, base_url):
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
    resource = await client.create_folder(parent_id="root-1", name="Projects")
    assert resource.id == "fold-1"
    assert resource.kind == "folder"


@respx.mock
async def test_list_tags(client, base_url):
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
    tags = await client.list_tags()
    assert len(tags) == 2
    assert tags[0].name == "important"
