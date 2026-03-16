import httpx
import respx

from fabric_client._compat import FabricSyncClient


@respx.mock
def test_sync_list_roots():
    respx.get("https://api.fabric.so/v2/resource-roots").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 1,
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
                    ]
                },
            },
        )
    )
    client = FabricSyncClient(api_key="test-key")
    roots = client.list_roots()
    assert len(roots) == 1
    assert roots[0].type == "SYSTEM"


@respx.mock
def test_sync_search():
    respx.post("https://api.fabric.so/v2/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 1,
                "hasMore": False,
                "hits": [
                    {
                        "id": "r-1",
                        "kind": "notepad",
                        "name": "Test",
                        "score": 0.8,
                        "tags": [],
                    }
                ],
            },
        )
    )
    client = FabricSyncClient(api_key="test-key")
    results = client.search("test")
    assert results.total == 1
    assert results.items[0].score == 0.8


@respx.mock
def test_sync_create_notepad():
    respx.post("https://api.fabric.so/v2/notepads").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "np-1",
                "kind": "notepad",
                "name": "Note",
                "tags": [],
            },
        )
    )
    client = FabricSyncClient(api_key="test-key")
    note = client.create_notepad(parent_id="@alias::inbox", text="content")
    assert note.id == "np-1"
