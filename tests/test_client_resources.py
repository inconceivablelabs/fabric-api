import httpx
import pytest
import respx

from fabric_client.client import FabricClient


@pytest.fixture
def client(api_key, base_url):
    return FabricClient(api_key=api_key, base_url=base_url)


@respx.mock
async def test_list_roots(client, base_url):
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
    roots = await client.list_roots()
    assert len(roots) == 2
    assert roots[0].type == "SYSTEM"
    assert roots[0].folder_name == "Inbox"
    assert roots[1].type == "SPACE"


@respx.mock
async def test_get_root(client, base_url):
    respx.get(f"{base_url}/resource-roots/root-1").mock(
        return_value=httpx.Response(
            200,
            json={
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
        )
    )
    root = await client.get_root("root-1")
    assert root.id == "root-1"
    assert root.subtype == "inbox"


@respx.mock
async def test_get_resource(client, base_url):
    respx.get(f"{base_url}/resources/res-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "res-1",
                "kind": "bookmark",
                "name": "Example",
                "url": "https://example.com",
                "tags": [],
            },
        )
    )
    resource = await client.get_resource("res-1")
    assert resource.id == "res-1"
    assert resource.kind == "bookmark"
    assert resource.url == "https://example.com"


@respx.mock
async def test_filter_resources(client, base_url):
    respx.post(f"{base_url}/resources/filter").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 1,
                "hasMore": False,
                "nextCursor": None,
                "resources": [
                    {"id": "res-1", "kind": "notepad", "name": "Note 1", "tags": []},
                ],
            },
        )
    )
    page = await client.filter_resources(kind=["notepad"], limit=10)
    assert page.total == 1
    assert page.has_more is False
    assert len(page.items) == 1
    assert page.items[0].kind == "notepad"


@respx.mock
async def test_delete_resources(client, base_url):
    route = respx.post(f"{base_url}/resources/delete").mock(
        return_value=httpx.Response(204)
    )
    await client.delete_resources(["res-1", "res-2"], archive=True)
    assert route.called
    import json

    body = json.loads(route.calls[0].request.content)
    assert body["resourceIds"] == ["res-1", "res-2"]
    assert body["archive"] is True


@respx.mock
async def test_recover_resources(client, base_url):
    route = respx.post(f"{base_url}/resources/recover").mock(
        return_value=httpx.Response(204)
    )
    await client.recover_resources(["res-1"])
    assert route.called
